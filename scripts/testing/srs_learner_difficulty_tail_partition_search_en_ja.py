#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import io
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_model_family_meta_search_en_ja import (  # noqa: E402
    _expert_from_json as _family_expert_from_json,
    _model_candidate_from_row,
)
from srs_learner_difficulty_model_family_search_en_ja import (  # noqa: E402
    SIGNAL_COLUMNS,
    _calibration_detail_rows,
    _candidate_raw_scores,
    _reviewed_focus_metrics,
    _signal_arrays,
)
from srs_learner_difficulty_model_tree_search_en_ja import (  # noqa: E402
    _component_split_present,
    _component_split_values,
    _tree_from_row,
    _tree_raw_scores,
)
from srs_learner_difficulty_normalization import TARGET_CURVE_ID  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    Expert,
    _band_samples,
    _calibration_context,
    _compact_counts,
    _difficulty_metrics,
    _escape,
    _load_json,
    _mapping,
    _mapping_rows,
    _optional_float,
    _raw_scores_for_expert,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _target_curve_normalize,
    _utc_now,
)


DEFAULT_BASE_FAMILY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_family_search_en_ja_refined_kango_coverage_local_s005_latest.json"
)
DEFAULT_TAIL_TREE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_model_tree_search_en_ja_expanded_signals_s025_stump_latest.json"
)
DEFAULT_CALIBRATION_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_refined_kango_coverage_local_s005_calibration_matrix_latest.npz"
)
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_refined_kango_coverage_local_s005_component_matrix_latest.npz"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_partition_search_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_partition_search_en_ja_latest.md"
)
DEFAULT_CALIBRATION_ROWS_CSV_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_partition_calibration_rows_en_ja_latest.csv"
)
DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_partition_calibration_rows_en_ja_latest.md"
)
DEFAULT_BASE_CANDIDATE = "boost__grid_s20_cnone_008318__kango_mid_signal_t35_s05"
DEFAULT_TAIL_CANDIDATE = (
    "stump__kango_common_priority_risk<=0.9668:mr__grid_s04_c150_022123__grid_s04_c150_023187"
)
DEFAULT_TAIL_QUANTILES = (0.05, 0.08, 0.10, 0.12, 0.15, 0.20)
DEFAULT_SOFT_STRENGTHS = (0.25, 0.50, 0.75, 1.0)
FALSE_TAIL_PENALTY_WEIGHTS = (0.05, 0.075, 0.10, 0.15)
UPPER_TAIL_EXPECTED_MIN = 0.88
HIGH_TAIL_EXPECTED_MIN = 0.94
FALSE_TAIL_EXPECTED_MAX = 0.80
UPPER_TAIL_GUARD_SCORE_MIN = 0.89


@dataclass(frozen=True)
class TailCandidate:
    candidate_id: str
    mode: str
    tail_quantile: float | None
    soft_strength: float | None
    normalized: object
    segment_ids: object
    tail_mask: object


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only en-ja learner-difficulty search that treats an "
            "upper-tail expert as a latent corpus-tail selector."
        )
    )
    parser.add_argument("--base-family-json", type=Path, default=DEFAULT_BASE_FAMILY_JSON)
    parser.add_argument("--tail-tree-json", type=Path, default=DEFAULT_TAIL_TREE_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--base-candidate", default=DEFAULT_BASE_CANDIDATE)
    parser.add_argument("--tail-candidate", default=DEFAULT_TAIL_CANDIDATE)
    parser.add_argument(
        "--tail-quantiles",
        default=",".join(str(value) for value in DEFAULT_TAIL_QUANTILES),
    )
    parser.add_argument(
        "--soft-strengths",
        default=",".join(str(value) for value in DEFAULT_SOFT_STRENGTHS),
    )
    parser.add_argument("--detail-candidate-limit", type=int, default=20)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--calibration-rows-csv-out",
        type=Path,
        default=DEFAULT_CALIBRATION_ROWS_CSV_OUT,
    )
    parser.add_argument(
        "--calibration-rows-markdown-out",
        type=Path,
        default=DEFAULT_CALIBRATION_ROWS_MARKDOWN_OUT,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        base_family_json=_resolve_path(args.base_family_json),
        tail_tree_json=_resolve_path(args.tail_tree_json),
        calibration_matrix_path=_resolve_path(args.calibration_matrix),
        component_matrix_path=_resolve_path(args.component_matrix),
        base_candidate_id=str(args.base_candidate),
        tail_candidate_id=str(args.tail_candidate),
        tail_quantiles=_parse_float_csv(args.tail_quantiles),
        soft_strengths=_parse_float_csv(args.soft_strengths),
        detail_candidate_limit=max(0, int(args.detail_candidate_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    calibration_rows_csv_out = _resolve_path(args.calibration_rows_csv_out)
    calibration_rows_markdown_out = _resolve_path(args.calibration_rows_markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    calibration_rows_csv_out.parent.mkdir(parents=True, exist_ok=True)
    calibration_rows_markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    calibration_rows_csv_out.write_text(_render_calibration_rows_csv(report), encoding="utf-8")
    calibration_rows_markdown_out.write_text(
        render_calibration_rows_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    print(f"Wrote calibration rows CSV artifact to {calibration_rows_csv_out}")
    print(f"Wrote calibration rows Markdown artifact to {calibration_rows_markdown_out}")
    return 0


def build_report(
    *,
    base_family_json: Path,
    tail_tree_json: Path,
    calibration_matrix_path: Path,
    component_matrix_path: Path,
    base_candidate_id: str,
    tail_candidate_id: str,
    tail_quantiles: Sequence[float] = DEFAULT_TAIL_QUANTILES,
    soft_strengths: Sequence[float] = DEFAULT_SOFT_STRENGTHS,
    detail_candidate_limit: int = 20,
) -> dict[str, object]:
    base_family_report = _load_json(base_family_json)
    tail_tree_report = _load_json(tail_tree_json)
    calibration = np.load(calibration_matrix_path)
    component = np.load(component_matrix_path)
    calibration_ctx = _calibration_context(calibration, component)
    base_raw = _family_candidate_raw(
        base_family_report,
        component=component,
        candidate_id=base_candidate_id,
    )
    tail_raw = _tree_candidate_raw(
        tail_tree_report,
        component=component,
        candidate_id=tail_candidate_id,
    )
    target_positions = np.asarray(component["target_curve_positions"], dtype=np.float32)
    candidates = _tail_candidates(
        base_raw=base_raw,
        tail_raw=tail_raw,
        target_positions=target_positions,
        tail_quantiles=tail_quantiles,
        soft_strengths=soft_strengths,
    )
    exact_top = _evaluate_candidates(
        candidates,
        component=component,
        calibration_context=calibration_ctx,
        detail_candidate_limit=detail_candidate_limit,
    )
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "base_family_json": base_family_json,
                "tail_tree_json": tail_tree_json,
                "calibration_matrix": calibration_matrix_path,
                "component_matrix": component_matrix_path,
            },
            code_paths=_tail_partition_code_paths(),
            version_constants={
                "target_curve": TARGET_CURVE_ID,
            },
            argv=sys.argv,
        ),
        "method": {
            "model": "tail_specialist_quantile_partition",
            "tail_selector": (
                "top q fraction of the full normalization population by the "
                "tail candidate's raw score"
            ),
            "hard_partition": (
                "tail-selected rows are assigned the top q target-curve positions "
                "ordered by the tail candidate; non-tail rows are assigned the "
                "remaining positions ordered by the base candidate"
            ),
            "raw_replace": (
                "tail-selected rows use the tail raw score and all other rows use "
                "the base raw score, followed by one global target-curve normalization"
            ),
            "soft_blend": (
                "tail-selected rows use (1-strength)*base_raw + strength*tail_raw, "
                "followed by one global target-curve normalization"
            ),
            "normalization_curve_id": TARGET_CURVE_ID,
            "upper_tail_expected_min": UPPER_TAIL_EXPECTED_MIN,
            "high_tail_expected_min": HIGH_TAIL_EXPECTED_MIN,
            "false_tail_expected_max": FALSE_TAIL_EXPECTED_MAX,
        },
        "inputs": {
            "base_family_json": _repo_or_home_path(base_family_json),
            "tail_tree_json": _repo_or_home_path(tail_tree_json),
            "calibration_matrix": _repo_or_home_path(calibration_matrix_path),
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "base_candidate_id": base_candidate_id,
            "tail_candidate_id": tail_candidate_id,
            "tail_quantiles": [_rounded(value) for value in tail_quantiles],
            "soft_strengths": [_rounded(value) for value in soft_strengths],
            "normalization_population_count": int(len(component["candidate_identity_keys"])),
            "calibration_label_count": int(len(calibration["calibration_lemmas"])),
        },
        "base_reference": _reference_row(
            "base_reference",
            _target_curve_normalize(base_raw, target_positions=target_positions),
            component=component,
            calibration_context=calibration_ctx,
        ),
        "tail_reference": _reference_row(
            "tail_reference",
            _target_curve_normalize(tail_raw, target_positions=target_positions),
            component=component,
            calibration_context=calibration_ctx,
        ),
        "exact_top": exact_top,
        "leaderboards": _leaderboards(exact_top, limit=20),
        "risk_sensitivity": _risk_sensitivity(exact_top, limit=8),
        "upper_tail_guarded_risk_sensitivity": _risk_sensitivity(
            exact_top,
            limit=8,
            upper_tail_score_min=UPPER_TAIL_GUARD_SCORE_MIN,
        ),
    }


def _tail_partition_code_paths() -> dict[str, Path]:
    return {
        "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
        "difficulty_signal_sweep": (SCRIPT_DIR / "srs_learner_difficulty_signal_sweep_en_ja.py"),
        "difficulty_model_family_search": (
            SCRIPT_DIR / "srs_learner_difficulty_model_family_search_en_ja.py"
        ),
        "difficulty_model_family_meta_search": (
            SCRIPT_DIR / "srs_learner_difficulty_model_family_meta_search_en_ja.py"
        ),
        "difficulty_model_tree_search": (
            SCRIPT_DIR / "srs_learner_difficulty_model_tree_search_en_ja.py"
        ),
        "difficulty_piecewise_search": (
            SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
        ),
        "difficulty_normalization": SCRIPT_DIR / "srs_learner_difficulty_normalization.py",
    }


def _family_candidate_raw(
    report: Mapping[str, object],
    *,
    component: object,
    candidate_id: str,
) -> object:
    candidate_rows = {
        str(row.get("candidate_id") or ""): row for row in _mapping_rows(report.get("exact_top"))
    }
    row = candidate_rows.get(candidate_id)
    if row is None:
        raise ValueError(f"Family candidate not found: {candidate_id}")
    candidate = _model_candidate_from_row(row)
    experts = [_family_expert_from_json(row) for row in _mapping_rows(report.get("expert_pool"))]
    raw_by_expert = {
        expert.variant_id: _raw_scores_for_expert(expert, component) for expert in experts
    }
    signal_arrays = _signal_arrays(component)
    return _candidate_raw_scores(
        candidate,
        raw_by_expert=raw_by_expert,
        signal_arrays=signal_arrays,
    )


def _tree_candidate_raw(
    report: Mapping[str, object],
    *,
    component: object,
    candidate_id: str,
) -> object:
    candidate_rows = {
        str(row.get("candidate_id") or ""): row for row in _mapping_rows(report.get("exact_top"))
    }
    row = candidate_rows.get(candidate_id)
    if row is None:
        raise ValueError(f"Tree candidate not found: {candidate_id}")
    candidate = _tree_from_row(row)
    experts_by_id = {
        str(row.get("variant_id") or ""): Expert(
            variant_id=str(row.get("variant_id") or ""),
            weights={
                str(key): float(value)
                for key, value in _mapping(row.get("weights")).items()
                if _optional_float(value) is not None
            },
            max_shift_from_frequency=_optional_float(row.get("max_shift_from_frequency")),
            source_scores={
                str(key): float(value)
                for key, value in _mapping(row.get("source_scores")).items()
                if _optional_float(value) is not None
            },
        )
        for row in _mapping_rows(report.get("expert_pool"))
    }
    needed = set(candidate.expert_ids)
    raw_by_expert = {
        expert_id: _raw_scores_for_expert(expert, component)
        for expert_id, expert in experts_by_id.items()
        if expert_id in needed
    }
    raw, _leaf_ids = _tree_raw_scores(
        candidate,
        raw_by_expert=raw_by_expert,
        split_values=_component_split_values(component),
        split_present=_component_split_present(component),
        row_count=len(component["candidate_identity_keys"]),
    )
    return raw


def _tail_candidates(
    *,
    base_raw: object,
    tail_raw: object,
    target_positions: object,
    tail_quantiles: Sequence[float],
    soft_strengths: Sequence[float],
) -> list[TailCandidate]:
    base_values = np.asarray(base_raw, dtype=np.float32)
    tail_values = np.asarray(tail_raw, dtype=np.float32)
    candidates = [
        TailCandidate(
            candidate_id="base_reference",
            mode="reference",
            tail_quantile=None,
            soft_strength=None,
            normalized=_target_curve_normalize(base_values, target_positions=target_positions),
            segment_ids=np.zeros(len(base_values), dtype=np.int64),
            tail_mask=np.zeros(len(base_values), dtype=bool),
        ),
        TailCandidate(
            candidate_id="tail_reference",
            mode="reference",
            tail_quantile=None,
            soft_strength=None,
            normalized=_target_curve_normalize(tail_values, target_positions=target_positions),
            segment_ids=np.ones(len(base_values), dtype=np.int64),
            tail_mask=np.ones(len(base_values), dtype=bool),
        ),
    ]
    for quantile in tail_quantiles:
        q = _bounded_quantile(quantile)
        mask = _tail_mask(tail_values, q)
        qid = _quantile_id(q)
        hard = _hard_partition_normalize(
            base_values,
            tail_values,
            tail_mask=mask,
            target_positions=target_positions,
        )
        candidates.append(
            TailCandidate(
                candidate_id=f"hard_partition_q{qid}",
                mode="hard_partition",
                tail_quantile=q,
                soft_strength=None,
                normalized=hard,
                segment_ids=mask.astype(np.int64),
                tail_mask=mask,
            )
        )
        replaced = base_values.copy()
        replaced[mask] = tail_values[mask]
        candidates.append(
            TailCandidate(
                candidate_id=f"raw_replace_q{qid}",
                mode="raw_replace",
                tail_quantile=q,
                soft_strength=None,
                normalized=_target_curve_normalize(replaced, target_positions=target_positions),
                segment_ids=mask.astype(np.int64),
                tail_mask=mask,
            )
        )
        for strength in soft_strengths:
            parsed_strength = min(1.0, max(0.0, float(strength)))
            blended = base_values.copy()
            blended[mask] = ((1.0 - parsed_strength) * base_values[mask]) + (
                parsed_strength * tail_values[mask]
            )
            candidates.append(
                TailCandidate(
                    candidate_id=f"soft_blend_q{qid}_s{_strength_id(parsed_strength)}",
                    mode="soft_blend",
                    tail_quantile=q,
                    soft_strength=parsed_strength,
                    normalized=_target_curve_normalize(
                        blended,
                        target_positions=target_positions,
                    ),
                    segment_ids=mask.astype(np.int64),
                    tail_mask=mask,
                )
            )
    return candidates


def _hard_partition_normalize(
    base_raw: object,
    tail_raw: object,
    *,
    tail_mask: object,
    target_positions: object,
) -> object:
    base_values = np.asarray(base_raw, dtype=np.float32)
    tail_values = np.asarray(tail_raw, dtype=np.float32)
    mask = np.asarray(tail_mask, dtype=bool)
    positions = np.asarray(target_positions, dtype=np.float32)
    normalized = np.empty(len(base_values), dtype=np.float32)
    non_tail_indices = np.where(~mask)[0]
    tail_indices = np.where(mask)[0]
    non_tail_positions = positions[: len(non_tail_indices)]
    tail_positions = positions[len(non_tail_indices) :]
    _assign_positions_by_raw_order(
        normalized,
        indices=non_tail_indices,
        raw_values=base_values,
        positions=non_tail_positions,
    )
    _assign_positions_by_raw_order(
        normalized,
        indices=tail_indices,
        raw_values=tail_values,
        positions=tail_positions,
    )
    return normalized


def _assign_positions_by_raw_order(
    normalized: object,
    *,
    indices: object,
    raw_values: object,
    positions: object,
) -> None:
    parsed_indices = np.asarray(indices, dtype=np.int64)
    if not len(parsed_indices):
        return
    values = np.asarray(raw_values, dtype=np.float32)
    safe_values = np.nan_to_num(values[parsed_indices], nan=-np.inf)
    order = np.argsort(safe_values, kind="stable")
    np.asarray(normalized)[parsed_indices[order]] = np.asarray(positions, dtype=np.float32)


def _tail_mask(raw: object, quantile: float) -> object:
    values = np.nan_to_num(np.asarray(raw, dtype=np.float32), nan=-np.inf)
    row_count = len(values)
    tail_count = max(1, min(row_count, int(round(row_count * float(quantile)))))
    order = np.argsort(values, kind="stable")
    mask = np.zeros(row_count, dtype=bool)
    mask[order[-tail_count:]] = True
    return mask


def _evaluate_candidates(
    candidates: Sequence[TailCandidate],
    *,
    component: object,
    calibration_context: Mapping[str, object],
    detail_candidate_limit: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        rows.append(
            _candidate_row(
                candidate,
                component=component,
                calibration_context=calibration_context,
                include_details=False,
            )
        )
    ranked = _top_rows(rows, limit=len(rows))
    detail_ids = {str(row.get("candidate_id") or "") for row in ranked[:detail_candidate_limit]}
    for row in ranked:
        if str(row.get("candidate_id") or "") not in detail_ids:
            continue
        candidate = next(
            item for item in candidates if item.candidate_id == str(row.get("candidate_id"))
        )
        row.update(
            _candidate_row(
                candidate,
                component=component,
                calibration_context=calibration_context,
                include_details=True,
            )
        )
    return ranked


def _candidate_row(
    candidate: TailCandidate,
    *,
    component: object,
    calibration_context: Mapping[str, object],
    include_details: bool,
) -> dict[str, object]:
    normalized = np.asarray(candidate.normalized, dtype=np.float32)
    calibration_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    observed = np.full(len(calibration_indices), np.nan, dtype=np.float32)
    valid = calibration_indices >= 0
    observed[valid] = normalized[calibration_indices[valid]]
    metrics = _difficulty_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=observed,
        expected_bands=calibration_context["expected_bands"],
        labels=calibration_context["labels"],
    )
    reviewed_focus = _reviewed_focus_metrics(
        expected_values=calibration_context["expected_values"],
        observed_values=observed,
        labels=calibration_context["labels"],
    )
    tail_partition = _tail_partition_diagnostics(
        candidate.tail_mask,
        calibration_context=calibration_context,
    )
    scores = dict(metrics["scores"])
    scores["reviewed_focus_score"] = reviewed_focus["score"]
    for penalty in FALSE_TAIL_PENALTY_WEIGHTS:
        scores[f"false_tail_adjusted_p{_penalty_id(penalty)}_score"] = _false_tail_adjusted_score(
            scores, tail_partition, penalty
        )
    summary = dict(_summary_metrics(metrics))
    summary["reviewed_focus_mae"] = reviewed_focus["mae"]
    summary["reviewed_focus_count"] = reviewed_focus["count"]
    row = {
        "candidate_id": candidate.candidate_id,
        "mode": candidate.mode,
        "tail_quantile": _rounded(candidate.tail_quantile),
        "soft_strength": _rounded(candidate.soft_strength),
        "scores": scores,
        "metrics": summary,
        "reviewed_focus": reviewed_focus,
        "tail_partition": tail_partition,
        "wrong_pairwise_examples": metrics["pairwise_order"]["wrong_examples"],
        "difficulty_mismatches": metrics["difficulty_bucket"]["mismatches"],
        "segment_misses": {
            key: value["misses"]
            for key, value in metrics["segments"].items()
            if value.get("misses")
        },
    }
    if include_details:
        row["calibration_rows"] = _calibration_detail_rows(
            normalized,
            component=component,
            calibration_context=calibration_context,
        )
        row["band_samples"] = _band_samples(
            normalized,
            component=component,
            segment_ids=np.asarray(candidate.segment_ids, dtype=np.int64),
            expert_ids=(candidate.mode,),
            per_band=8,
        )
    return row


def _tail_partition_diagnostics(
    tail_mask: object,
    *,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    mask = np.asarray(tail_mask, dtype=bool)
    expected = np.asarray(calibration_context["expected_values"], dtype=np.float32)
    component_indices = np.asarray(calibration_context["component_indices"], dtype=np.int64)
    labels = [str(value) for value in calibration_context["labels"]]
    valid = (component_indices >= 0) & np.isfinite(expected)
    selected = np.zeros(len(component_indices), dtype=bool)
    selected[valid] = mask[component_indices[valid]]
    upper = valid & (expected >= UPPER_TAIL_EXPECTED_MIN)
    high = valid & (expected >= HIGH_TAIL_EXPECTED_MIN)
    false_tail = selected & (expected < FALSE_TAIL_EXPECTED_MAX)
    selected_count = int(selected.sum())
    upper_hit_count = int((selected & upper).sum())
    high_hit_count = int((selected & high).sum())
    rows = []
    for index in np.where(selected)[0][:30]:
        rows.append(
            {
                "label": labels[int(index)],
                "expected_value": _rounded(float(expected[int(index)])),
            }
        )
    return {
        "tail_population_count": int(mask.sum()),
        "tail_population_fraction": _rounded(float(mask.mean()) if len(mask) else None),
        "selected_calibration_count": selected_count,
        "upper_tail_label_count": int(upper.sum()),
        "upper_tail_hit_count": upper_hit_count,
        "upper_tail_recall": _rounded(_ratio(upper_hit_count, int(upper.sum()))),
        "upper_tail_precision": _rounded(_ratio(upper_hit_count, selected_count)),
        "high_tail_label_count": int(high.sum()),
        "high_tail_hit_count": high_hit_count,
        "high_tail_recall": _rounded(_ratio(high_hit_count, int(high.sum()))),
        "high_tail_precision": _rounded(_ratio(high_hit_count, selected_count)),
        "false_tail_under_0_80_count": int(false_tail.sum()),
        "false_tail_under_0_80_rate": _rounded(_ratio(int(false_tail.sum()), selected_count)),
        "selected_calibration_examples": rows,
    }


def _reference_row(
    candidate_id: str,
    normalized: object,
    *,
    component: object,
    calibration_context: Mapping[str, object],
) -> dict[str, object]:
    candidate = TailCandidate(
        candidate_id=candidate_id,
        mode="reference",
        tail_quantile=None,
        soft_strength=None,
        normalized=normalized,
        segment_ids=np.zeros(len(normalized), dtype=np.int64),
        tail_mask=np.zeros(len(normalized), dtype=bool),
    )
    return _candidate_row(
        candidate,
        component=component,
        calibration_context=calibration_context,
        include_details=False,
    )


def _top_rows(rows: Sequence[Mapping[str, object]], *, limit: int) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in sorted(
            rows,
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("upper_tail_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("bucket_accuracy_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("pairwise_order_score")) or -1.0,
            ),
            reverse=True,
        )[:limit]
    ]


def _leaderboards(
    rows: Sequence[Mapping[str, object]], *, limit: int
) -> dict[str, list[dict[str, object]]]:
    score_keys = (
        "balanced_score",
        "upper_tail_score",
        "high_tail_score",
        "bucket_accuracy_score",
        "numeric_mae_score",
        "pairwise_order_score",
        "reviewed_focus_score",
        *[
            f"false_tail_adjusted_p{_penalty_id(penalty)}_score"
            for penalty in FALSE_TAIL_PENALTY_WEIGHTS
        ],
    )
    result: dict[str, list[dict[str, object]]] = {}
    for score_key in score_keys:
        ranked = sorted(
            rows,
            key=lambda row: _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
            reverse=True,
        )
        result[score_key] = [
            {
                "candidate_id": row.get("candidate_id"),
                "mode": row.get("mode"),
                "tail_quantile": row.get("tail_quantile"),
                "soft_strength": row.get("soft_strength"),
                "score": _mapping(row.get("scores")).get(score_key),
                "balanced_score": _mapping(row.get("scores")).get("balanced_score"),
                "upper_tail_score": _mapping(row.get("scores")).get("upper_tail_score"),
                "high_tail_score": _mapping(row.get("scores")).get("high_tail_score"),
                "bucket_accuracy_score": _mapping(row.get("scores")).get("bucket_accuracy_score"),
                "pairwise_order_score": _mapping(row.get("scores")).get("pairwise_order_score"),
            }
            for row in ranked[:limit]
        ]
    return result


def _risk_sensitivity(
    rows: Sequence[Mapping[str, object]],
    *,
    limit: int,
    upper_tail_score_min: float | None = None,
) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    filtered_rows = [
        row
        for row in rows
        if (
            upper_tail_score_min is None
            or (
                (_optional_float(_mapping(row.get("scores")).get("upper_tail_score")) or -1.0)
                >= upper_tail_score_min
            )
        )
    ]
    for penalty in FALSE_TAIL_PENALTY_WEIGHTS:
        score_key = f"false_tail_adjusted_p{_penalty_id(penalty)}_score"
        ranked = sorted(
            filtered_rows,
            key=lambda row: (
                _optional_float(_mapping(row.get("scores")).get(score_key)) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("upper_tail_score")) or -1.0,
                _optional_float(_mapping(row.get("scores")).get("balanced_score")) or -1.0,
            ),
            reverse=True,
        )
        result[str(_rounded(penalty))] = [
            {
                "candidate_id": row.get("candidate_id"),
                "mode": row.get("mode"),
                "tail_quantile": row.get("tail_quantile"),
                "soft_strength": row.get("soft_strength"),
                "score": _mapping(row.get("scores")).get(score_key),
                "balanced_score": _mapping(row.get("scores")).get("balanced_score"),
                "upper_tail_score": _mapping(row.get("scores")).get("upper_tail_score"),
                "false_tail_under_0_80_rate": _mapping(row.get("tail_partition")).get(
                    "false_tail_under_0_80_rate"
                ),
            }
            for row in ranked[:limit]
        ]
    return result


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _mapping(report.get("inputs"))
    method = _mapping(report.get("method"))
    lines = [
        "# en-ja Learner Difficulty Tail-Partition Search",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Base candidate: `{_escape(inputs.get('base_candidate_id'))}`",
        f"- Tail candidate: `{_escape(inputs.get('tail_candidate_id'))}`",
        f"- Normalization population: `{_escape(inputs.get('normalization_population_count'))}`",
        f"- Calibration labels: `{_escape(inputs.get('calibration_label_count'))}`",
        "",
        "## Method",
        "",
        f"- Tail selector: {method.get('tail_selector')}",
        f"- Hard partition: {method.get('hard_partition')}",
        f"- Raw replace: {method.get('raw_replace')}",
        f"- Soft blend: {method.get('soft_blend')}",
        (
            f"- Tail diagnostics: upper tail is expected >= `{UPPER_TAIL_EXPECTED_MIN}`, "
            f"high tail is expected >= `{HIGH_TAIL_EXPECTED_MIN}`, false-tail rows are "
            f"selected calibration labels below `{FALSE_TAIL_EXPECTED_MAX}`."
        ),
        (
            "- False-tail adjusted scores are `balanced_score - penalty * "
            "false_tail_under_0_80_rate`; references with no selected tail labels "
            "use a false-tail rate of zero."
        ),
        (
            f"- Upper-tail-guarded risk sensitivity keeps only candidates with "
            f"upper-tail score >= `{UPPER_TAIL_GUARD_SCORE_MIN}` so the risk penalty "
            "does not select a model that avoids false tails by giving up the tail fix."
        ),
        "",
        "## References",
        "",
        _summary_line("Base reference", _mapping(report.get("base_reference"))),
        _summary_line("Tail reference", _mapping(report.get("tail_reference"))),
        "",
        "## Exact Top Candidates",
        "",
        (
            "| Rank | Candidate | Mode | q | Strength | Balanced | MAE | Bucket | Pairwise | "
            "Beginner | High Tail | Upper Tail | Tail Precision | False Tail |"
        ),
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(_mapping_rows(report.get("exact_top"))[:30], start=1):
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        tail = _mapping(row.get("tail_partition"))
        lines.append(
            "| "
            f"{rank} | "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('mode'))}` | "
            f"`{_escape(row.get('tail_quantile'))}` | "
            f"`{_escape(row.get('soft_strength'))}` | "
            f"`{_escape(scores.get('balanced_score'))}` | "
            f"`{_escape(metrics.get('mae'))}` | "
            f"`{_escape(scores.get('bucket_accuracy_score'))}` | "
            f"`{_escape(scores.get('pairwise_order_score'))}` | "
            f"`{_escape(scores.get('beginner_core_score'))}` | "
            f"`{_escape(scores.get('high_tail_score'))}` | "
            f"`{_escape(scores.get('upper_tail_score'))}` | "
            f"`{_escape(tail.get('upper_tail_precision'))}` | "
            f"`{_escape(tail.get('false_tail_under_0_80_rate'))}` |"
        )
    if _mapping(report.get("risk_sensitivity")):
        lines.extend(["", "## False-Tail Risk Sensitivity", ""])
        _append_risk_sensitivity_table(lines, _mapping(report.get("risk_sensitivity")))
    if _mapping(report.get("upper_tail_guarded_risk_sensitivity")):
        lines.extend(["", "## Upper-Tail-Guarded Risk Sensitivity", ""])
        _append_risk_sensitivity_table(
            lines,
            _mapping(report.get("upper_tail_guarded_risk_sensitivity")),
        )
    for row in _mapping_rows(report.get("exact_top"))[:5]:
        lines.extend(["", f"### `{_escape(row.get('candidate_id'))}`", ""])
        scores = _mapping(row.get("scores"))
        metrics = _mapping(row.get("metrics"))
        tail = _mapping(row.get("tail_partition"))
        lines.append(f"- Scores: `{_compact_counts(scores)}`")
        lines.append(f"- Metrics: `{_compact_counts(metrics)}`")
        lines.append(f"- Tail partition: `{_compact_counts(tail)}`")
        mismatches = _mapping_rows(row.get("difficulty_mismatches"))
        if mismatches:
            lines.append(
                "- Difficulty mismatches: "
                + ", ".join(
                    f"{item.get('label')} ({item.get('expected')}->{item.get('observed')})"
                    for item in mismatches[:12]
                )
            )
        if _mapping_rows(row.get("band_samples")):
            lines.extend(["", "Band samples:", ""])
            for band in _mapping_rows(row.get("band_samples")):
                samples = ", ".join(
                    f"{sample.get('lemma')}({sample.get('reading')})"
                    for sample in _mapping_rows(band.get("samples"))[:8]
                )
                lines.append(
                    f"- `{_escape(band.get('band'))}` count `{_escape(band.get('count'))}`: {samples}"
                )
    return "\n".join(lines).rstrip() + "\n"


def _append_risk_sensitivity_table(
    lines: list[str],
    sensitivity: Mapping[str, object],
) -> None:
    lines.extend(
        [
            "| Penalty | Rank | Candidate | Adjusted | Balanced | Upper Tail | False Tail |",
            "| ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for penalty, rows in sensitivity.items():
        for rank, row in enumerate(_mapping_rows(rows)[:5], start=1):
            lines.append(
                "| "
                f"`{_escape(penalty)}` | "
                f"{rank} | "
                f"`{_escape(row.get('candidate_id'))}` | "
                f"`{_escape(row.get('score'))}` | "
                f"`{_escape(row.get('balanced_score'))}` | "
                f"`{_escape(row.get('upper_tail_score'))}` | "
                f"`{_escape(row.get('false_tail_under_0_80_rate'))}` |"
            )


def _summary_line(label: str, row: Mapping[str, object]) -> str:
    scores = _mapping(row.get("scores"))
    metrics = _mapping(row.get("metrics"))
    return (
        f"- {label}: balanced `{_escape(scores.get('balanced_score'))}`, "
        f"MAE `{_escape(metrics.get('mae'))}`, "
        f"bucket `{_escape(scores.get('bucket_accuracy_score'))}`, "
        f"pairwise `{_escape(scores.get('pairwise_order_score'))}`, "
        f"high-tail `{_escape(scores.get('high_tail_score'))}`, "
        f"upper-tail `{_escape(scores.get('upper_tail_score'))}`"
    )


def render_calibration_rows_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-ja Tail-Partition Calibration Rows",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        "",
        "| Candidate | Rank | Label | Expected | Observed | Error | Direction | Freq | KangoMid | RareWagoTail | WrittenWagoTail |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in _flat_calibration_rows(report):
        lines.append(
            "| "
            f"`{_escape(row.get('candidate_id'))}` | "
            f"`{_escape(row.get('rank'))}` | "
            f"`{_escape(row.get('label'))}` | "
            f"`{_escape(row.get('expected_value'))}` | "
            f"`{_escape(row.get('observed_value'))}` | "
            f"`{_escape(row.get('absolute_error'))}` | "
            f"`{_escape(row.get('direction'))}` | "
            f"`{_escape(row.get('signal_frequency'))}` | "
            f"`{_escape(row.get('signal_kango_mid_signal'))}` | "
            f"`{_escape(row.get('signal_rare_wago_tail_risk'))}` | "
            f"`{_escape(row.get('signal_written_wago_tail_risk'))}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_calibration_rows_csv(report: Mapping[str, object]) -> str:
    rows = _flat_calibration_rows(report)
    headers = [
        "candidate_id",
        "rank",
        "label",
        "expected_band",
        "expected_value",
        "observed_value",
        "absolute_error",
        "direction",
        *[f"signal_{signal}" for signal in SIGNAL_COLUMNS],
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _flat_calibration_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(_mapping_rows(report.get("exact_top")), start=1):
        candidate_id = str(candidate.get("candidate_id") or "")
        for calibration_row in _mapping_rows(candidate.get("calibration_rows")):
            flattened = {
                "candidate_id": candidate_id,
                "rank": rank,
                "label": calibration_row.get("label"),
                "expected_band": calibration_row.get("expected_band"),
                "expected_value": calibration_row.get("expected_value"),
                "observed_value": calibration_row.get("observed_value"),
                "absolute_error": calibration_row.get("absolute_error"),
                "direction": calibration_row.get("direction"),
            }
            signals = _mapping(calibration_row.get("signals"))
            for signal in SIGNAL_COLUMNS:
                flattened[f"signal_{signal}"] = signals.get(signal)
            rows.append(flattened)
    return rows


def _parse_float_csv(value: str) -> tuple[float, ...]:
    return tuple(float(part.strip()) for part in str(value).split(",") if part.strip())


def _bounded_quantile(value: float) -> float:
    return min(0.95, max(0.01, float(value)))


def _quantile_id(value: float) -> str:
    return f"{int(round(float(value) * 100)):02d}"


def _strength_id(value: float) -> str:
    return f"{int(round(float(value) * 100)):02d}"


def _penalty_id(value: float) -> str:
    return f"{int(round(float(value) * 1000)):03d}"


def _false_tail_adjusted_score(
    scores: Mapping[str, object],
    tail_partition: Mapping[str, object],
    penalty: float,
) -> float | None:
    balanced = _optional_float(scores.get("balanced_score"))
    if balanced is None:
        return None
    false_tail_rate = _optional_float(tail_partition.get("false_tail_under_0_80_rate")) or 0.0
    return _rounded(float(balanced) - (float(penalty) * false_tail_rate))


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


if __name__ == "__main__":
    raise SystemExit(main())
