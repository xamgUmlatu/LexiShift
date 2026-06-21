#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402


DEFAULT_TRACE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_trace_latest.json"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_extended_freq_factor_s010_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_component_matrix_latest.npz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_piecewise_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_piecewise_search_en_ja_latest.md"
)
SCORE_KEYS = (
    "balanced_score",
    "numeric_mae_score",
    "bucket_accuracy_score",
    "pairwise_order_score",
    "rank_correlation_score",
    "beginner_core_score",
    "beginner_broad_score",
    "upper_tail_score",
    "high_tail_score",
    "tail_separation_score",
)
PAIRWISE_MIN_EXPECTED_GAP = 0.03
PAIRWISE_TIE_TOLERANCE = 0.01
BEGINNER_CORE_MAX = 0.20
BEGINNER_CORE_OBSERVED_CEILING = 0.25
BEGINNER_BROAD_MAX = 0.40
BEGINNER_BROAD_OBSERVED_CEILING = 0.50
UPPER_TAIL_MIN = 0.88
UPPER_TAIL_OBSERVED_FLOOR = 0.80
HIGH_TAIL_MIN = 0.94
HIGH_TAIL_OBSERVED_FLOOR = 0.88
VOCAB_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})


@dataclass(frozen=True)
class Expert:
    variant_id: str
    weights: Mapping[str, float]
    max_shift_from_frequency: float | None
    source_scores: Mapping[str, float]


@dataclass(frozen=True)
class PiecewiseCandidate:
    candidate_id: str
    boundaries: tuple[float, ...]
    expert_ids: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Post-process en-ja learner-difficulty sweep outputs into simple "
            "frequency-anchored piecewise candidates."
        )
    )
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE_JSON)
    parser.add_argument(
        "--calibration-matrix",
        type=Path,
        default=DEFAULT_CALIBRATION_MATRIX,
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--expert-pool-size", type=int, default=20)
    parser.add_argument("--top-per-metric", type=int, default=8)
    parser.add_argument(
        "--two-segment-boundaries",
        default="0.25,0.35,0.45,0.55,0.65,0.75",
    )
    parser.add_argument(
        "--three-segment-boundaries",
        default="0.25:0.55,0.25:0.65,0.25:0.75,0.35:0.60,0.35:0.70,0.35:0.80,0.45:0.65,0.45:0.75,0.45:0.85",
    )
    parser.add_argument("--approximate-retain-limit", type=int, default=500)
    parser.add_argument("--exact-limit", type=int, default=80)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        trace_json=_resolve_path(args.trace_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        expert_pool_size=max(1, int(args.expert_pool_size)),
        top_per_metric=max(1, int(args.top_per_metric)),
        two_segment_boundaries=_parse_float_csv(args.two_segment_boundaries),
        three_segment_boundaries=_parse_boundary_pairs(args.three_segment_boundaries),
        approximate_retain_limit=max(1, int(args.approximate_retain_limit)),
        exact_limit=max(1, int(args.exact_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    trace_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    expert_pool_size: int = 20,
    top_per_metric: int = 8,
    two_segment_boundaries: Sequence[float] = (0.25, 0.35, 0.45, 0.55, 0.65, 0.75),
    three_segment_boundaries: Sequence[tuple[float, float]] = (
        (0.25, 0.55),
        (0.25, 0.65),
        (0.25, 0.75),
        (0.35, 0.60),
        (0.35, 0.70),
        (0.35, 0.80),
        (0.45, 0.65),
        (0.45, 0.75),
        (0.45, 0.85),
    ),
    approximate_retain_limit: int = 500,
    exact_limit: int = 80,
) -> dict[str, object]:
    trace = _load_json(trace_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    experts = _select_experts(
        trace.get("variant_records", ()),
        pool_size=expert_pool_size,
        top_per_metric=top_per_metric,
    )
    expert_ids = [expert.variant_id for expert in experts]
    variant_ids = [str(value) for value in calibration["variant_ids"]]
    variant_index = {variant_id: index for index, variant_id in enumerate(variant_ids)}
    missing_experts = [
        expert.variant_id for expert in experts if expert.variant_id not in variant_index
    ]
    if missing_experts:
        raise ValueError(f"Missing experts in calibration matrix: {missing_experts[:5]}")

    calibration_context = _calibration_context(calibration, component)
    approximate_candidates = _approximate_search(
        candidates=_iter_piecewise_candidates(
            expert_ids,
            two_segment_boundaries=two_segment_boundaries,
            three_segment_boundaries=three_segment_boundaries,
        ),
        calibration_matrix=calibration,
        variant_index=variant_index,
        calibration_frequency=calibration_context["frequency"],
        expected_values=calibration_context["expected_values"],
        expected_bands=calibration_context["expected_bands"],
        expected_candidate_states=calibration_context["expected_candidate_states"],
        observed_candidate_states=calibration_context["observed_candidate_states"],
        labels=calibration_context["labels"],
        retain_limit=approximate_retain_limit,
    )

    exact_candidates = _exact_evaluate_candidates(
        approximate_candidates[:exact_limit],
        experts_by_id={expert.variant_id: expert for expert in experts},
        component=component,
        calibration_context=calibration_context,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "trace_json": trace_json,
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
            },
            code_paths=_piecewise_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "search_anchor": "frequency",
            "transition": "hard_piecewise",
            "approximate_stage": (
                "uses individual expert target-curve calibration predictions only "
                "to preselect candidates"
            ),
            "exact_stage": (
                "recomputes raw full-corpus piecewise scores and applies global "
                "target-curve normalization"
            ),
            "normalization_curve_id": TARGET_CURVE_ID,
        },
        "inputs": {
            "trace_json": _repo_or_home_path(trace_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "trace_variant_count": len(trace.get("variant_records", ())),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "component_names": [str(value) for value in component["component_names"]],
            "expert_pool_size": len(experts),
            "top_per_metric": top_per_metric,
            "two_segment_boundaries": [round(float(value), 4) for value in two_segment_boundaries],
            "three_segment_boundaries": [
                [round(float(left), 4), round(float(right), 4)]
                for left, right in three_segment_boundaries
            ],
            "approximate_retain_limit": approximate_retain_limit,
            "exact_limit": exact_limit,
        },
        "expert_pool": [_expert_json(expert) for expert in experts],
        "approximate_top": approximate_candidates[:50],
        "exact_top": exact_candidates,
    }


def _piecewise_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_signal_sweep": (SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _select_experts(
    records: object,
    *,
    pool_size: int,
    top_per_metric: int,
) -> list[Expert]:
    rows = [row for row in _mapping_rows(records) if _mapping(row.get("weights"))]
    selected: list[Expert] = []
    seen: set[str] = set()
    for score_key in SCORE_KEYS:
        ranked = sorted(
            rows,
            key=lambda row: _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
            reverse=True,
        )
        for row in ranked[:top_per_metric]:
            variant_id = str(row.get("variant_id") or "")
            if not variant_id or variant_id in seen:
                continue
            seen.add(variant_id)
            selected.append(_expert_from_record(row))
            if len(selected) >= pool_size:
                return selected
    if len(selected) >= pool_size:
        return selected
    ranked_balanced = sorted(
        rows,
        key=lambda row: _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
        reverse=True,
    )
    for row in ranked_balanced:
        variant_id = str(row.get("variant_id") or "")
        if not variant_id or variant_id in seen:
            continue
        seen.add(variant_id)
        selected.append(_expert_from_record(row))
        if len(selected) >= pool_size:
            break
    return selected


def _expert_from_record(row: Mapping[str, object]) -> Expert:
    cap = _optional_float(row.get("max_shift_from_frequency"))
    return Expert(
        variant_id=str(row.get("variant_id") or ""),
        weights={
            str(key): float(value)
            for key, value in _mapping(row.get("weights")).items()
            if _optional_float(value) is not None
        },
        max_shift_from_frequency=cap,
        source_scores={
            str(key): float(value)
            for key, value in _mapping(row.get("scores")).items()
            if _optional_float(value) is not None
        },
    )


def _iter_piecewise_candidates(
    expert_ids: Sequence[str],
    *,
    two_segment_boundaries: Sequence[float],
    three_segment_boundaries: Sequence[tuple[float, float]],
) -> Iterable[PiecewiseCandidate]:
    for expert_id in expert_ids:
        yield PiecewiseCandidate(
            candidate_id=f"linear__{expert_id}",
            boundaries=(),
            expert_ids=(expert_id,),
        )
    for boundary in two_segment_boundaries:
        for left in expert_ids:
            for right in expert_ids:
                if left == right:
                    continue
                yield PiecewiseCandidate(
                    candidate_id=f"pw2_b{_boundary_label(boundary)}__{left}__{right}",
                    boundaries=(round(float(boundary), 4),),
                    expert_ids=(left, right),
                )
    for left_boundary, right_boundary in three_segment_boundaries:
        if left_boundary >= right_boundary:
            continue
        for early in expert_ids:
            for middle in expert_ids:
                for late in expert_ids:
                    if len({early, middle, late}) == 1:
                        continue
                    yield PiecewiseCandidate(
                        candidate_id=(
                            f"pw3_b{_boundary_label(left_boundary)}_"
                            f"{_boundary_label(right_boundary)}__{early}__{middle}__{late}"
                        ),
                        boundaries=(
                            round(float(left_boundary), 4),
                            round(float(right_boundary), 4),
                        ),
                        expert_ids=(early, middle, late),
                    )


def _approximate_search(
    *,
    candidates: Iterable[PiecewiseCandidate],
    calibration_matrix: object,
    variant_index: Mapping[str, int],
    calibration_frequency: object,
    expected_values: object,
    expected_bands: Sequence[str],
    expected_candidate_states: object | None,
    observed_candidate_states: object | None,
    labels: Sequence[str],
    retain_limit: int,
) -> list[dict[str, object]]:
    observed_matrix = calibration_matrix["observed_values"]
    retained: list[dict[str, object]] = []
    for candidate in candidates:
        observed = _approximate_candidate_values(
            candidate,
            observed_matrix=observed_matrix,
            variant_index=variant_index,
            calibration_frequency=calibration_frequency,
        )
        metrics = _difficulty_metrics(
            expected_values=expected_values,
            observed_values=observed,
            expected_bands=expected_bands,
            expected_candidate_states=expected_candidate_states,
            observed_candidate_states=observed_candidate_states,
            labels=labels,
        )
        retained.append(
            {
                "candidate_id": candidate.candidate_id,
                "boundaries": list(candidate.boundaries),
                "expert_ids": list(candidate.expert_ids),
                "stage": "approximate",
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
            }
        )
        if len(retained) > retain_limit * 4:
            retained = _top_candidates(retained, limit=retain_limit)
    return _top_candidates(retained, limit=retain_limit)


def _approximate_candidate_values(
    candidate: PiecewiseCandidate,
    *,
    observed_matrix: object,
    variant_index: Mapping[str, int],
    calibration_frequency: object,
) -> object:
    values = np.full(len(calibration_frequency), np.nan, dtype=np.float32)
    expert_indices = [variant_index[expert_id] for expert_id in candidate.expert_ids]
    if len(expert_indices) == 1:
        return np.asarray(observed_matrix[expert_indices[0]], dtype=np.float32)
    segment_ids = _segment_ids(calibration_frequency, candidate.boundaries)
    for segment_index, expert_index in enumerate(expert_indices):
        mask = segment_ids == segment_index
        values[mask] = observed_matrix[expert_index, mask]
    return values


def _exact_evaluate_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    experts_by_id: Mapping[str, Expert],
    component: object,
    calibration_context: Mapping[str, object],
) -> list[dict[str, object]]:
    needed_expert_ids = sorted(
        {
            str(expert_id)
            for candidate in candidates
            for expert_id in _sequence_values(candidate.get("expert_ids"))
        }
    )
    raw_by_expert = {
        expert_id: _raw_scores_for_expert(experts_by_id[expert_id], component)
        for expert_id in needed_expert_ids
    }
    results: list[dict[str, object]] = []
    frequency = np.asarray(component["frequency_values"], dtype=np.float32)
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    expected_values = calibration_context["expected_values"]
    expected_bands = calibration_context["expected_bands"]
    labels = calibration_context["labels"]
    for candidate_row in candidates:
        candidate = PiecewiseCandidate(
            candidate_id=str(candidate_row.get("candidate_id") or ""),
            boundaries=tuple(
                float(value) for value in _sequence_values(candidate_row.get("boundaries"))
            ),
            expert_ids=tuple(
                str(value) for value in _sequence_values(candidate_row.get("expert_ids"))
            ),
        )
        raw = _piecewise_raw_scores(
            candidate,
            raw_by_expert=raw_by_expert,
            frequency=frequency,
        )
        normalized = _target_curve_normalize(raw, target_positions=target_positions)
        segment_ids = _segment_ids(frequency, candidate.boundaries)
        observed = np.full(len(calibration_indices), np.nan, dtype=np.float32)
        valid = calibration_indices >= 0
        observed[valid] = normalized[calibration_indices[valid]]
        metrics = _difficulty_metrics(
            expected_values=expected_values,
            observed_values=observed,
            expected_bands=expected_bands,
            expected_candidate_states=calibration_context["expected_candidate_states"],
            observed_candidate_states=calibration_context["observed_candidate_states"],
            labels=labels,
        )
        results.append(
            {
                "candidate_id": candidate.candidate_id,
                "boundaries": list(candidate.boundaries),
                "expert_ids": list(candidate.expert_ids),
                "stage": "exact",
                "scores": metrics["scores"],
                "metrics": _summary_metrics(metrics),
                "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
                "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
                "band_samples": _band_samples(
                    normalized,
                    component=component,
                    segment_ids=segment_ids,
                    expert_ids=candidate.expert_ids,
                    per_band=8,
                ),
                "segment_misses": {
                    key: value["misses"]
                    for key, value in metrics["segments"].items()
                    if value.get("misses")
                },
                "approximate_scores": candidate_row.get("scores"),
            }
        )
    return _top_candidates(results, limit=len(results))


def _raw_scores_for_expert(expert: Expert, component: object) -> object:
    names = [str(value) for value in component["component_names"]]
    name_to_index = {name: index for index, name in enumerate(names)}
    values = np.asarray(component["component_values"], dtype=np.float32)
    present = np.asarray(component["component_present"], dtype=bool)
    frequency = np.asarray(component["frequency_values"], dtype=np.float32)
    active_indices: list[int] = []
    active_weights: list[float] = []
    for component_name, weight in expert.weights.items():
        if weight <= 0.0 or component_name not in name_to_index:
            continue
        active_indices.append(name_to_index[component_name])
        active_weights.append(float(weight))
    if not active_indices:
        return np.nan_to_num(frequency, nan=0.0).astype(np.float32)
    selected_values = values[:, active_indices]
    selected_present = present[:, active_indices]
    weight_vector = np.asarray(active_weights, dtype=np.float32)
    numerator = (selected_values * selected_present * weight_vector).sum(axis=1)
    denominator = (selected_present * weight_vector).sum(axis=1)
    raw = np.nan_to_num(frequency, nan=0.0).astype(np.float32)
    np.divide(numerator, denominator, out=raw, where=denominator > 0.0)
    if expert.max_shift_from_frequency is not None:
        cap = max(0.0, float(expert.max_shift_from_frequency))
        capped = np.minimum(frequency + cap, np.maximum(frequency - cap, raw))
        raw = np.where(np.isnan(frequency), raw, capped)
    return np.clip(raw, 0.0, 1.0).astype(np.float32)


def _piecewise_raw_scores(
    candidate: PiecewiseCandidate,
    *,
    raw_by_expert: Mapping[str, object],
    frequency: object,
) -> object:
    if len(candidate.expert_ids) == 1:
        return np.asarray(raw_by_expert[candidate.expert_ids[0]], dtype=np.float32)
    segment_ids = _segment_ids(frequency, candidate.boundaries)
    raw = np.empty(len(frequency), dtype=np.float32)
    for segment_index, expert_id in enumerate(candidate.expert_ids):
        mask = segment_ids == segment_index
        raw[mask] = raw_by_expert[expert_id][mask]
    return raw


def _target_curve_normalize(raw: object, *, target_positions: object) -> object:
    order = np.argsort(raw, kind="stable")
    normalized = np.empty_like(raw, dtype=np.float32)
    normalized[order] = target_positions
    return normalized


def _band_samples(
    normalized: object,
    *,
    component: object,
    segment_ids: object,
    expert_ids: Sequence[str],
    per_band: int,
) -> list[dict[str, object]]:
    values = np.asarray(normalized, dtype=np.float32)
    frequency = np.asarray(component["frequency_values"], dtype=np.float32)
    segments = np.asarray(segment_ids, dtype=np.int64)
    lemmas = component["lemmas"]
    readings = component["readings"]
    identities = component["candidate_identity_keys"]
    bands: list[dict[str, object]] = []
    for band_index in range(20):
        start = band_index * 0.05
        end = (band_index + 1) * 0.05
        if band_index == 19:
            mask = (values >= start) & (values <= end)
        else:
            mask = (values >= start) & (values < end)
        indices = np.where(mask)[0]
        if len(indices) == 0:
            bands.append(
                {
                    "band": f"{start:.2f}-{end:.2f}",
                    "count": 0,
                    "samples": [],
                }
            )
            continue
        ordered = indices[np.argsort(values[indices], kind="stable")]
        sample_offsets = np.linspace(
            0,
            len(ordered) - 1,
            num=min(max(1, per_band), len(ordered)),
            dtype=int,
        )
        samples = []
        for row_index in ordered[sample_offsets]:
            segment_index = int(segments[row_index])
            expert_id = expert_ids[segment_index] if 0 <= segment_index < len(expert_ids) else ""
            samples.append(
                {
                    "lemma": str(lemmas[row_index]),
                    "reading": str(readings[row_index]),
                    "difficulty": _rounded(float(values[row_index])),
                    "frequency_anchor": _rounded(float(frequency[row_index])),
                    "expert_id": expert_id,
                    "candidate_identity_key": str(identities[row_index]),
                }
            )
        bands.append(
            {
                "band": f"{start:.2f}-{end:.2f}",
                "count": int(len(indices)),
                "samples": samples,
            }
        )
    return bands


def _calibration_context(calibration: object, component: object) -> dict[str, object]:
    component_by_identity = {
        str(identity): index
        for index, identity in enumerate(component["candidate_identity_keys"])
        if str(identity)
    }
    component_by_lemma_reading = {
        (str(lemma), str(reading)): index
        for index, (lemma, reading) in enumerate(zip(component["lemmas"], component["readings"]))
    }
    indices: list[int] = []
    for identity, lemma, reading in zip(
        calibration["calibration_identity_keys"],
        calibration["calibration_lemmas"],
        calibration["calibration_readings"],
    ):
        index = component_by_identity.get(str(identity))
        if index is None:
            index = component_by_lemma_reading.get((str(lemma), str(reading)))
        indices.append(-1 if index is None else int(index))
    component_indices = np.asarray(indices, dtype=np.int64)
    frequency = np.full(len(indices), np.nan, dtype=np.float32)
    component_candidate_states = np.full(len(indices), "", dtype="<U64")
    component_problem_classes = np.full(len(indices), "", dtype="<U64")
    valid = component_indices >= 0
    frequency[valid] = component["frequency_values"][component_indices[valid]]
    if _npz_has_key(component, "candidate_states"):
        component_candidate_states[valid] = component["candidate_states"][component_indices[valid]]
    if _npz_has_key(component, "problem_classes"):
        component_problem_classes[valid] = component["problem_classes"][component_indices[valid]]
    labels = [
        f"{lemma}/{reading}" if str(reading) else str(lemma)
        for lemma, reading in zip(
            calibration["calibration_lemmas"],
            calibration["calibration_readings"],
        )
    ]
    return {
        "component_indices": component_indices,
        "frequency": frequency,
        "expected_values": calibration["expected_values"],
        "expected_bands": [str(value) for value in calibration["expected_bands"]],
        "expected_candidate_states": _optional_np_string_values(
            calibration,
            "expected_candidate_states",
            len(indices),
        ),
        "expected_presentation_modes": _optional_np_string_values(
            calibration,
            "expected_presentation_modes",
            len(indices),
        ),
        "expected_problem_classes": _optional_np_string_values(
            calibration,
            "expected_problem_classes",
            len(indices),
        ),
        "observed_candidate_states": _optional_np_string_values(
            calibration,
            "observed_candidate_states",
            len(indices),
            fallback=component_candidate_states,
        ),
        "observed_presentation_modes": _optional_np_string_values(
            calibration,
            "observed_presentation_modes",
            len(indices),
        ),
        "observed_problem_classes": _optional_np_string_values(
            calibration,
            "observed_problem_classes",
            len(indices),
            fallback=component_problem_classes,
        ),
        "labels": labels,
    }


def _optional_np_string_values(
    source: object,
    key: str,
    count: int,
    *,
    fallback: object | None = None,
) -> object:
    if _npz_has_key(source, key):
        return np.asarray(source[key], dtype=str)
    if fallback is not None:
        return np.asarray(fallback, dtype=str)
    return np.full(count, "", dtype="<U64")


def _npz_has_key(source: object, key: str) -> bool:
    files = getattr(source, "files", ())
    return key in files


def _segment_ids(values: object, boundaries: Sequence[float]) -> object:
    parsed = np.asarray(values, dtype=np.float32)
    safe_values = np.nan_to_num(parsed, nan=0.5)
    return np.digitize(safe_values, np.asarray(boundaries, dtype=np.float32), right=False)


def _difficulty_metrics(
    *,
    expected_values: object,
    observed_values: object,
    expected_bands: Sequence[str],
    labels: Sequence[str],
    expected_candidate_states: object | None = None,
    observed_candidate_states: object | None = None,
) -> dict[str, object]:
    expected = np.asarray(expected_values, dtype=np.float32)
    observed = np.asarray(observed_values, dtype=np.float32)
    finite = np.isfinite(expected) & np.isfinite(observed)
    errors = np.abs(observed[finite] - expected[finite])
    difficulty_value = {
        "evaluated_count": int(finite.sum()),
        "mae": _rounded(float(errors.mean())) if len(errors) else None,
        "rmse": _rounded(float(np.sqrt(np.mean(errors * errors)))) if len(errors) else None,
        "within_0_10": int((errors <= 0.10).sum()) if len(errors) else 0,
    }
    observed_bands = [_difficulty_band(value) for value in observed]
    band_rows = [
        index
        for index, band in enumerate(expected_bands)
        if str(band).strip() and np.isfinite(observed[index])
    ]
    band_matches = [index for index in band_rows if expected_bands[index] == observed_bands[index]]
    mismatches = [
        {
            "label": labels[index],
            "expected": expected_bands[index],
            "observed": observed_bands[index],
            "expected_value": _rounded(float(expected[index]))
            if np.isfinite(expected[index])
            else None,
            "observed_value": _rounded(float(observed[index])),
        }
        for index in band_rows
        if expected_bands[index] != observed_bands[index]
    ][:20]
    difficulty_bucket = {
        "evaluated_count": len(band_rows),
        "match_count": len(band_matches),
        "mismatch_count": len(band_rows) - len(band_matches),
        "accuracy": _rounded(_ratio_or_none(len(band_matches), len(band_rows))),
        "mismatches": mismatches,
    }
    pairwise_order = _pairwise_metrics(expected, observed, labels)
    rank_correlation = _rank_correlation(expected, observed)
    segments = {
        "beginner_core": _segment_threshold_metrics(
            expected,
            observed,
            labels,
            expected_max=BEGINNER_CORE_MAX,
            observed_ceiling=BEGINNER_CORE_OBSERVED_CEILING,
        ),
        "beginner_broad": _segment_threshold_metrics(
            expected,
            observed,
            labels,
            expected_max=BEGINNER_BROAD_MAX,
            observed_ceiling=BEGINNER_BROAD_OBSERVED_CEILING,
        ),
        "upper_tail": _segment_threshold_metrics(
            expected,
            observed,
            labels,
            expected_min=UPPER_TAIL_MIN,
            observed_floor=UPPER_TAIL_OBSERVED_FLOOR,
        ),
        "high_tail": _segment_threshold_metrics(
            expected,
            observed,
            labels,
            expected_min=HIGH_TAIL_MIN,
            observed_floor=HIGH_TAIL_OBSERVED_FLOOR,
        ),
    }
    separation = _tail_separation(expected, observed)
    default_decision = _default_vocab_decision_metrics(
        expected_candidate_states=expected_candidate_states,
        observed_candidate_states=observed_candidate_states,
        labels=labels,
    )
    scores = _score_summary(
        difficulty_value=difficulty_value,
        difficulty_bucket=difficulty_bucket,
        pairwise_order=pairwise_order,
        rank_correlation=rank_correlation,
        segments=segments,
        separation=separation,
        default_decision=default_decision,
    )
    return {
        "difficulty_value": difficulty_value,
        "difficulty_bucket": difficulty_bucket,
        "pairwise_order": pairwise_order,
        "rank_correlation": rank_correlation,
        "segments": segments,
        "separation": separation,
        "default_vocab_decision": default_decision,
        "scores": scores,
    }


def _default_vocab_decision_metrics(
    *,
    expected_candidate_states: object | None,
    observed_candidate_states: object | None,
    labels: Sequence[str],
) -> dict[str, object]:
    if expected_candidate_states is None or observed_candidate_states is None:
        return {
            "evaluated_count": 0,
            "accuracy": None,
            "unavailable_reason": "candidate_state_arrays_missing",
        }
    expected = np.asarray(expected_candidate_states, dtype=str)
    observed = np.asarray(observed_candidate_states, dtype=str)
    count = min(len(expected), len(observed), len(labels))
    true_default_accept = 0
    true_default_block = 0
    false_default_admit = 0
    false_default_suppress = 0
    mismatches = []
    for index in range(count):
        expected_state = str(expected[index]).strip()
        observed_state = str(observed[index]).strip()
        if not expected_state or not observed_state:
            continue
        expected_default = expected_state in VOCAB_STATES
        observed_default = observed_state in VOCAB_STATES
        if expected_default and observed_default:
            true_default_accept += 1
        elif expected_default and not observed_default:
            false_default_suppress += 1
        elif not expected_default and observed_default:
            false_default_admit += 1
        else:
            true_default_block += 1
        if expected_default != observed_default and len(mismatches) < 20:
            mismatches.append(
                {
                    "label": labels[index],
                    "expected_candidate_state": expected_state,
                    "observed_candidate_state": observed_state,
                    "expected_default": expected_default,
                    "observed_default": observed_default,
                }
            )
    evaluated_count = (
        true_default_accept + true_default_block + false_default_admit + false_default_suppress
    )
    correct = true_default_accept + true_default_block
    return {
        "evaluated_count": evaluated_count,
        "true_default_accept": true_default_accept,
        "true_default_block": true_default_block,
        "false_default_admit": false_default_admit,
        "false_default_suppress": false_default_suppress,
        "accuracy": _rounded(_ratio_or_none(correct, evaluated_count)),
        "mismatches": mismatches,
    }


def _pairwise_metrics(
    expected: object,
    observed: object,
    labels: Sequence[str],
) -> dict[str, object]:
    expected_array = np.asarray(expected, dtype=np.float32)
    observed_array = np.asarray(observed, dtype=np.float32)
    wrong_examples: list[dict[str, object]] = []
    finite = np.isfinite(expected_array) & np.isfinite(observed_array)
    indices = np.where(finite)[0]
    if len(indices) < 2:
        return {
            "comparable_count": 0,
            "correct_count": 0,
            "tie_count": 0,
            "wrong_count": 0,
            "accuracy": None,
            "strict_accuracy": None,
            "wrong_examples": [],
        }
    left_offsets, right_offsets = np.triu_indices(len(indices), k=1)
    left_indices = indices[left_offsets]
    right_indices = indices[right_offsets]
    expected_gaps = expected_array[right_indices] - expected_array[left_indices]
    comparable = np.abs(expected_gaps) >= PAIRWISE_MIN_EXPECTED_GAP
    if not bool(comparable.any()):
        return {
            "comparable_count": 0,
            "correct_count": 0,
            "tie_count": 0,
            "wrong_count": 0,
            "accuracy": None,
            "strict_accuracy": None,
            "wrong_examples": [],
        }
    left_indices = left_indices[comparable]
    right_indices = right_indices[comparable]
    expected_gaps = expected_gaps[comparable]
    observed_gaps = observed_array[right_indices] - observed_array[left_indices]
    ties = np.abs(observed_gaps) <= PAIRWISE_TIE_TOLERANCE
    correct = (~ties) & (np.sign(expected_gaps) == np.sign(observed_gaps))
    wrong = (~ties) & (~correct)
    comparable_count = int(len(expected_gaps))
    correct_count = int(correct.sum())
    tie_count = int(ties.sum())
    wrong_count = int(wrong.sum())
    wrong_positions = np.where(wrong)[0][:20]
    for position in wrong_positions:
        left_index = int(left_indices[position])
        right_index = int(right_indices[position])
        expected_gap = float(expected_gaps[position])
        easier_index = left_index if expected_gap > 0 else right_index
        harder_index = right_index if expected_gap > 0 else left_index
        wrong_examples.append(
            {
                "expected_easier": labels[easier_index],
                "expected_harder": labels[harder_index],
                "expected_gap": _rounded(abs(expected_gap)),
                "observed_gap": _rounded(
                    float(observed_array[harder_index] - observed_array[easier_index])
                ),
            }
        )
    return {
        "comparable_count": comparable_count,
        "correct_count": correct_count,
        "tie_count": tie_count,
        "wrong_count": wrong_count,
        "accuracy": _rounded(_ratio_or_none(correct_count + (0.5 * tie_count), comparable_count)),
        "strict_accuracy": _rounded(_ratio_or_none(correct_count, comparable_count)),
        "wrong_examples": wrong_examples,
    }


def _rank_correlation(expected: object, observed: object) -> dict[str, object]:
    finite = np.isfinite(expected) & np.isfinite(observed)
    left = np.asarray(expected[finite], dtype=np.float64)
    right = np.asarray(observed[finite], dtype=np.float64)
    return {
        "evaluated_count": int(len(left)),
        "spearman": _rounded(_pearson(_ranks(left), _ranks(right))),
        "pearson": _rounded(_pearson(left, right)),
    }


def _segment_threshold_metrics(
    expected: object,
    observed: object,
    labels: Sequence[str],
    *,
    expected_min: float | None = None,
    expected_max: float | None = None,
    observed_floor: float | None = None,
    observed_ceiling: float | None = None,
) -> dict[str, object]:
    mask = np.isfinite(expected) & np.isfinite(observed)
    if expected_min is not None:
        mask &= expected >= expected_min
    if expected_max is not None:
        mask &= expected <= expected_max
    indices = [int(index) for index in np.where(mask)[0]]
    pass_count = 0
    misses: list[dict[str, object]] = []
    values = []
    errors = []
    for index in indices:
        value = float(observed[index])
        values.append(value)
        errors.append(abs(value - float(expected[index])))
        floor_ok = observed_floor is None or value >= observed_floor
        ceiling_ok = observed_ceiling is None or value <= observed_ceiling
        if floor_ok and ceiling_ok:
            pass_count += 1
        elif len(misses) < 20:
            misses.append(
                {
                    "label": labels[index],
                    "expected": _rounded(float(expected[index])),
                    "observed": _rounded(value),
                }
            )
    return {
        "count": len(indices),
        "pass_count": pass_count,
        "pass_rate": _rounded(_ratio_or_none(pass_count, len(indices))),
        "mae": _rounded(float(np.mean(errors))) if errors else None,
        "observed_min": _rounded(min(values)) if values else None,
        "observed_max": _rounded(max(values)) if values else None,
        "observed_avg": _rounded(float(np.mean(values))) if values else None,
        "misses": misses,
    }


def _tail_separation(expected: object, observed: object) -> dict[str, object]:
    finite = np.isfinite(expected) & np.isfinite(observed)
    beginner = observed[finite & (expected <= BEGINNER_CORE_MAX)]
    high_tail = observed[finite & (expected >= HIGH_TAIL_MIN)]
    beginner_avg = float(beginner.mean()) if len(beginner) else None
    high_tail_avg = float(high_tail.mean()) if len(high_tail) else None
    return {
        "beginner_count": int(len(beginner)),
        "high_tail_count": int(len(high_tail)),
        "beginner_observed_avg": _rounded(beginner_avg),
        "high_tail_observed_avg": _rounded(high_tail_avg),
        "mean_gap": _rounded(
            high_tail_avg - beginner_avg
            if high_tail_avg is not None and beginner_avg is not None
            else None
        ),
        "minmax_gap": _rounded(
            float(high_tail.min() - beginner.max()) if len(high_tail) and len(beginner) else None
        ),
    }


def _score_summary(
    *,
    difficulty_value: Mapping[str, object],
    difficulty_bucket: Mapping[str, object],
    pairwise_order: Mapping[str, object],
    rank_correlation: Mapping[str, object],
    segments: Mapping[str, Mapping[str, object]],
    separation: Mapping[str, object],
    default_decision: Mapping[str, object] | None = None,
) -> dict[str, object]:
    numeric_mae = _optional_float(difficulty_value.get("mae"))
    rank_score = _correlation_to_score(_optional_float(rank_correlation.get("spearman")))
    separation_gap = _optional_float(separation.get("mean_gap"))
    scores = {
        "numeric_mae_score": _rounded(1.0 - numeric_mae if numeric_mae is not None else None),
        "bucket_accuracy_score": _rounded(difficulty_bucket.get("accuracy")),
        "pairwise_order_score": _rounded(pairwise_order.get("accuracy")),
        "rank_correlation_score": _rounded(rank_score),
        "beginner_core_score": _rounded(_mapping(segments.get("beginner_core")).get("pass_rate")),
        "beginner_broad_score": _rounded(_mapping(segments.get("beginner_broad")).get("pass_rate")),
        "upper_tail_score": _rounded(_mapping(segments.get("upper_tail")).get("pass_rate")),
        "high_tail_score": _rounded(_mapping(segments.get("high_tail")).get("pass_rate")),
        "tail_separation_score": _rounded(
            min(1.0, max(0.0, separation_gap / 0.70)) if separation_gap is not None else None
        ),
        "default_decision_score": _rounded(_mapping(default_decision).get("accuracy")),
    }
    scores["balanced_score"] = _rounded(
        _weighted_average(
            (
                (scores["numeric_mae_score"], 0.16),
                (scores["bucket_accuracy_score"], 0.12),
                (scores["pairwise_order_score"], 0.20),
                (scores["rank_correlation_score"], 0.10),
                (scores["beginner_core_score"], 0.12),
                (scores["beginner_broad_score"], 0.08),
                (scores["upper_tail_score"], 0.10),
                (scores["high_tail_score"], 0.06),
                (scores["tail_separation_score"], 0.03),
                (scores["default_decision_score"], 0.03),
            )
        )
    )
    return scores


def _summary_metrics(metrics: Mapping[str, object]) -> dict[str, object]:
    difficulty_value = _mapping(metrics.get("difficulty_value"))
    difficulty_bucket = _mapping(metrics.get("difficulty_bucket"))
    pairwise = _mapping(metrics.get("pairwise_order"))
    rank = _mapping(metrics.get("rank_correlation"))
    segments = _mapping(metrics.get("segments"))
    beginner_core = _mapping(segments.get("beginner_core"))
    high_tail = _mapping(segments.get("high_tail"))
    return {
        "mae": difficulty_value.get("mae"),
        "bucket_accuracy": difficulty_bucket.get("accuracy"),
        "bucket_mismatch_count": difficulty_bucket.get("mismatch_count"),
        "pairwise_accuracy": pairwise.get("accuracy"),
        "pairwise_wrong_count": pairwise.get("wrong_count"),
        "spearman": rank.get("spearman"),
        "beginner_core_pass_rate": beginner_core.get("pass_rate"),
        "high_tail_pass_rate": high_tail.get("pass_rate"),
    }


def _top_candidates(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(
            rows,
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("numeric_mae_score")) or -1.0,
            ),
            reverse=True,
        )[:limit]
    ]


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Learner Difficulty Piecewise Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Trace variants: `{_escape(inputs.get('trace_variant_count'))}`",
        f"- Expert pool size: `{_escape(inputs.get('expert_pool_size'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        f"- Approximate retained: `{_escape(inputs.get('approximate_retain_limit'))}`",
        f"- Exact evaluated: `{_escape(inputs.get('exact_limit'))}`",
        "",
        "## Method",
        "",
        (
            "Approximate search combines individual expert normalized calibration "
            "predictions only to select candidates. Exact search recomputes raw "
            "piecewise scores over the full component matrix, then re-applies the "
            "global target curve."
        ),
        "",
        "## Exact Top Candidates",
        "",
        (
            "| Rank | Candidate | Balanced | MAE | Bucket | Pairwise | Spearman | "
            "Beginner | High tail | Boundaries | Experts |"
        ),
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for index, row in enumerate(_mapping_rows(report.get("exact_top"))[:20], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        lines.append(
            "| "
            f"{index} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(metrics.get('bucket_accuracy'))}` | "
            f"`{_escape(metrics.get('pairwise_accuracy'))}` | "
            f"`{_escape(metrics.get('spearman'))}` | "
            f"`{_escape(metrics.get('beginner_core_pass_rate'))}` | "
            f"`{_escape(metrics.get('high_tail_pass_rate'))}` | "
            f"`{_escape(row.get('boundaries'))}` | "
            f"`{_escape(', '.join(str(value) for value in _sequence_values(row.get('expert_ids'))))}` |"
        )
    lines.extend(["", "## Expert Pool", ""])
    lines.extend(
        [
            "| Expert | Balanced | MAE | Bucket | Pairwise | Beginner | High tail | Weights | Cap |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for expert in _mapping_rows(report.get("expert_pool")):
        scores = _mapping(expert.get("source_scores"))
        lines.append(
            "| "
            f"`{_escape(expert.get('variant_id'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(1 - float(scores.get('numeric_mae_score')) if scores.get('numeric_mae_score') is not None else '')}` | "
            f"`{_escape(scores.get('bucket_accuracy_score'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_compact_counts(expert.get('weights'))}` | "
            f"`{_escape(expert.get('max_shift_from_frequency'))}` |"
        )
    lines.extend(["", "## Top Candidate Details", ""])
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        metrics = _mapping(row.get("metrics"))
        lines.extend(
            [
                f"### `{_escape(row.get('candidate_id'))}`",
                "",
                f"- Boundaries: `{_escape(row.get('boundaries'))}`",
                f"- Experts: `{_escape(', '.join(str(value) for value in _sequence_values(row.get('expert_ids'))))}`",
                f"- Scores: `{_compact_counts(row.get('scores'))}`",
                f"- Metrics: `{_compact_counts(metrics)}`",
            ]
        )
        mismatches = _mapping_rows(row.get("difficulty_mismatches"))
        if mismatches:
            text = ", ".join(
                f"{item.get('label')} ({item.get('expected')}->{item.get('observed')})"
                for item in mismatches[:12]
            )
            lines.append(f"- Difficulty mismatches: {text}")
        wrong = _mapping_rows(row.get("wrong_pairwise_examples"))
        if wrong:
            text = ", ".join(
                f"{item.get('expected_easier')} < {item.get('expected_harder')} obs_gap={item.get('observed_gap')}"
                for item in wrong[:8]
            )
            lines.append(f"- Pairwise misses: {text}")
        lines.extend(["", "Band samples:", ""])
        for band in _mapping_rows(row.get("band_samples")):
            samples = ", ".join(
                f"{sample.get('lemma')}({sample.get('reading')})"
                for sample in _mapping_rows(band.get("samples"))[:8]
            )
            lines.append(
                f"- `{_escape(band.get('band'))}` count `{_escape(band.get('count'))}`: {samples}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _expert_json(expert: Expert) -> dict[str, object]:
    return {
        "variant_id": expert.variant_id,
        "weights": dict(expert.weights),
        "max_shift_from_frequency": expert.max_shift_from_frequency,
        "source_scores": dict(expert.source_scores),
    }


def _parse_float_csv(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in str(value or "").split(",") if item.strip())


def _parse_boundary_pairs(value: str) -> tuple[tuple[float, float], ...]:
    pairs: list[tuple[float, float]] = []
    for item in str(value or "").split(","):
        item = item.strip()
        if not item:
            continue
        left, sep, right = item.partition(":")
        if not sep:
            raise ValueError(f"Expected boundary pair as left:right, got {item!r}")
        pairs.append((float(left), float(right)))
    return tuple(pairs)


def _boundary_label(value: float) -> str:
    return f"{int(round(float(value) * 100)):02d}"


def _difficulty_band(value: object) -> str:
    parsed = _optional_float(value)
    if parsed is None:
        return ""
    if parsed < 0.55:
        return "beginner"
    if parsed < 0.80:
        return "intermediate"
    return "advanced"


def _ranks(values: object) -> object:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="stable")
    ranks = np.empty(len(array), dtype=np.float64)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and array[order[end]] == array[order[cursor]]:
            end += 1
        average_rank = ((cursor + 1) + end) / 2.0
        ranks[order[cursor:end]] = average_rank
        cursor = end
    return ranks


def _pearson(left: object, right: object) -> float | None:
    left_values = np.asarray(left, dtype=np.float64)
    right_values = np.asarray(right, dtype=np.float64)
    if len(left_values) != len(right_values) or len(left_values) < 2:
        return None
    left_centered = left_values - left_values.mean()
    right_centered = right_values - right_values.mean()
    denominator = np.sqrt((left_centered * left_centered).sum()) * np.sqrt(
        (right_centered * right_centered).sum()
    )
    if denominator <= 0.0:
        return None
    return float((left_centered * right_centered).sum() / denominator)


def _weighted_average(values_and_weights: Sequence[tuple[object, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values_and_weights:
        parsed = _optional_float(value)
        if parsed is None or weight <= 0.0:
            continue
        numerator += parsed * weight
        denominator += weight
    if denominator <= 0.0:
        return None
    return numerator / denominator


def _correlation_to_score(value: float | None) -> float | None:
    if value is None:
        return None
    return min(1.0, max(0.0, (value + 1.0) / 2.0))


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _repo_or_home_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        home = Path.home()
        try:
            return "~/" + str(path.relative_to(home))
        except ValueError:
            return str(path)


def _optional_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _rounded(value: object) -> float | None:
    parsed = _optional_float(value)
    if parsed is None:
        return None
    return round(parsed, 6)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence_values(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _compact_counts(value: object) -> str:
    mapping = _mapping(value)
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
