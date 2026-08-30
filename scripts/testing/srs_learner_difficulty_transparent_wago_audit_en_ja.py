#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_cleaned_lane_eval_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PAIR_JSON,
    component_lookup,
    row_component_index,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _mapping,
    _optional_float,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _utc_now,
)
from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    MatrixView,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    DEFAULT_COMPONENT_MATRIX,
    family_parts,
)
from srs_learner_difficulty_stitch_validation_eval_en_ja import (  # noqa: E402
    DEFAULT_CAP_REPORT,
    DEFAULT_STITCHED_REPORT,
    DEFAULT_V1_REPORT,
    score_arrays_for_models,
)


PAIR = "en-ja"
ANCHOR_MODEL = "ordinary_cap"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_transparent_wago_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_transparent_wago_audit_en_ja_latest.md"
)
DATASET_ORDER = ("calibration", "holdout", "stitch_validation")
ROW_SIGNALS = (
    "frequency",
    "frequency_tail80",
    "frequency_unranked_risk",
    "bccwj_domain_rank_coverage",
    "jlpt_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "jmdict_priority",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
    "jmdict_reading_form_marked_risk",
    "jmdict_reading_restricted_risk",
    "non_standard_reading_risk",
    "rare_non_standard_reading_risk",
    "rare_wago_non_standard_reading_risk",
    "wtype_wago_ease",
    "wtype_kango_risk",
    "wtype_gairaigo_risk",
    "max_written_form_burden",
    "max_kanji_burden",
    "rare_wago_risk",
    "rare_wago_tail_risk",
    "rare_wago_obscure_written_risk",
    "rare_wago_max_written_burden",
    "rare_wago_max_kanji_burden",
    "rare_wago_marked_usage_risk",
    "rare_wago_missing_curriculum_risk",
    "rare_wago_missing_curriculum_shape_risk",
    "written_wago_tail_risk",
    "named_entity_risk",
    "candidate_deprioritized_vocab_risk",
)


@dataclass(frozen=True)
class WagoCeilingSpec:
    spec_id: str
    family: str
    ceiling: float
    tail_min: float
    written_max: float
    rank_max: float
    obscure_max: float
    protect_beginner_core: bool
    protect_source_pair_review: bool
    entity_max: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit transparent rare-wago overplacement and probe bounded "
            "sidecar downshift ceilings without changing runtime behavior."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--source-pair-json", type=Path, default=DEFAULT_SOURCE_PAIR_JSON)
    parser.add_argument("--v1-report", type=Path, default=DEFAULT_V1_REPORT)
    parser.add_argument("--cap-report", type=Path, default=DEFAULT_CAP_REPORT)
    parser.add_argument("--stitched-report", type=Path, default=DEFAULT_STITCHED_REPORT)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--leaderboard-limit", type=int, default=30)
    parser.add_argument("--detail-limit", type=int, default=24)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        source_pair_json_path=_resolve_path(args.source_pair_json),
        v1_report_path=_resolve_path(args.v1_report),
        cap_report_path=_resolve_path(args.cap_report),
        stitched_report_path=_resolve_path(args.stitched_report),
        anchor_model=str(args.anchor_model),
        leaderboard_limit=max(1, int(args.leaderboard_limit)),
        detail_limit=max(1, int(args.detail_limit)),
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
    component_matrix_path: Path,
    source_pair_json_path: Path,
    v1_report_path: Path,
    cap_report_path: Path,
    stitched_report_path: Path,
    anchor_model: str,
    leaderboard_limit: int,
    detail_limit: int,
) -> dict[str, object]:
    component_payload = np.load(component_matrix_path)
    component_view = ComponentView.from_npz(component_payload)
    matrix_view = MatrixView.from_npz(np.load(component_matrix_path))
    score_arrays, resolved_ids = score_arrays_for_models(
        view=component_view,
        parts=family_parts(component_view),
        v1_report_path=v1_report_path,
        cap_report_path=cap_report_path,
        stitched_report_path=stitched_report_path,
        v1_candidate_id=None,
        cap_candidate_id=None,
        stitch_candidate_id=None,
    )
    if anchor_model not in score_arrays:
        raise ValueError(f"Unknown anchor model: {anchor_model}")
    source_pair = _load_json(source_pair_json_path)
    lookup = component_lookup(component_payload)
    scalar_rows = [
        row
        for row in source_pair.get("rows", ())
        if isinstance(row, Mapping) and row.get("target") == "scalar_vocab"
    ]
    anchor_scores = np.asarray(score_arrays[anchor_model], dtype=np.float32)
    rows = rows_with_signals(
        scalar_rows,
        lookup=lookup,
        matrix=matrix_view,
        anchor_scores=anchor_scores,
    )
    segment_rows = {
        segment_id: [row for row in rows if segment_id in row.get("segments", ())]
        for segment_id in segment_definitions()
    }
    candidates = [candidate_report(rows, spec) for spec in wago_ceiling_specs()]
    ranked = sorted(candidates, key=candidate_rank_key, reverse=True)
    best = next((row for row in ranked if row.get("passes_guardrails")), ranked[0])
    best_spec = spec_from_payload(_mapping(best.get("spec")))
    best_rows = adjusted_rows_for_spec(rows, best_spec)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": True,
        "method": {
            "purpose": (
                "Test whether existing signals can safely identify rare but "
                "transparent wago/native rows that the anchor places too late."
            ),
            "anchor_model": anchor_model,
            "guardrail_policy": (
                "Promising candidates must improve stitch-validation transparent "
                "wago rows, avoid negative all-row MAE on all labeled splits, and "
                "produce no changed-row or success-row regressions."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "source_pair_json": _repo_or_home_path(source_pair_json_path),
            "v1_report": _repo_or_home_path(v1_report_path),
            "cap_report": _repo_or_home_path(cap_report_path),
            "stitched_report": _repo_or_home_path(stitched_report_path),
            "anchor_model": anchor_model,
            "rows": len(rows),
            **resolved_ids,
        },
        "segment_definitions": segment_definitions(),
        "dataset_summary": dataset_summary(rows),
        "segment_summary": {
            segment_id: segment_report(segment_id, segment_rows[segment_id])
            for segment_id in segment_definitions()
        },
        "candidate_space": candidate_space_summary(),
        "summary": {
            "candidate_count": len(candidates),
            "best_candidate_id": best.get("candidate_id"),
            "best_passes_guardrails": best.get("passes_guardrails"),
            "best": best,
            "interpretation": interpretation(best, segment_rows),
        },
        "leaderboard": ranked[:leaderboard_limit],
        "best_changed_rows": changed_rows_by_dataset(best_rows, detail_limit=detail_limit),
        "best_regression_rows": regression_rows_by_dataset(
            best_rows,
            detail_limit=detail_limit,
        ),
        "best_full_matrix_review": full_matrix_review_pack(
            matrix_view,
            best_spec,
            anchor_scores=anchor_scores,
            detail_limit=detail_limit,
        ),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "source_pair_json": source_pair_json_path,
                "v1_report": v1_report_path,
                "cap_report": cap_report_path,
                "stitched_report": stitched_report_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "transparent_wago_audit": Path(__file__),
                "cleaned_lane_eval": SCRIPT_DIR
                / "srs_learner_difficulty_cleaned_lane_eval_en_ja.py",
                "stitch_validation_eval": SCRIPT_DIR
                / "srs_learner_difficulty_stitch_validation_eval_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def rows_with_signals(
    rows: Sequence[Mapping[str, object]],
    *,
    lookup: Mapping[tuple[str, str], int],
    matrix: MatrixView,
    anchor_scores: np.ndarray,
) -> list[dict[str, object]]:
    result = []
    for row in rows:
        value = _optional_float(row.get("expected_learner_difficulty"))
        index = row_component_index(row, lookup)
        if value is None or index is None:
            continue
        observed = float(anchor_scores[index])
        signals = signal_snapshot(index, matrix=matrix)
        payload = {
            "dataset_id": row.get("dataset_id"),
            "label": row.get("label") or f"{row.get('lemma')}/{row.get('reading')}",
            "lemma": row.get("lemma"),
            "reading": row.get("reading"),
            "expected": _rounded(value),
            "expected_band": _difficulty_band(value),
            "anchor_observed": _rounded(observed),
            "anchor_abs_error": _rounded(abs(float(value) - observed)),
            "anchor_direction": "too_low" if observed < float(value) else "too_high",
            "candidate_state": matrix.candidate_states[index],
            "problem_class": matrix.problem_classes[index],
            "core_rank": _rounded(float(matrix.core_ranks[index])),
            "primary_pair_status": row.get("primary_pair_status"),
            "signals": signals,
            "surface_features": surface_features(str(row.get("lemma") or "")),
        }
        payload["segments"] = segment_memberships(payload)
        result.append(payload)
    return result


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    snapshot: dict[str, object] = {}
    for signal in ROW_SIGNALS:
        column = component_index.get(signal)
        snapshot[signal] = (
            None if column is None else _rounded(float(matrix.component_values[index, column]))
        )
    return snapshot


def surface_features(lemma: str) -> dict[str, object]:
    kanji = sum(1 for char in lemma if is_kanji(char))
    hiragana = sum(1 for char in lemma if is_hiragana(char))
    katakana = sum(1 for char in lemma if is_katakana(char))
    return {
        "length": len(lemma),
        "kanji_count": kanji,
        "hiragana_count": hiragana,
        "katakana_count": katakana,
        "has_hiragana": hiragana > 0,
        "has_katakana": katakana > 0,
        "mixed_kanji_hiragana": kanji > 0 and hiragana > 0,
        "kanji_only": kanji > 0 and hiragana == 0 and katakana == 0,
    }


def is_kanji(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff" or "\u3400" <= char <= "\u4dbf"


def is_hiragana(char: str) -> bool:
    return "\u3040" <= char <= "\u309f"


def is_katakana(char: str) -> bool:
    return "\u30a0" <= char <= "\u30ff"


def segment_definitions() -> dict[str, str]:
    return {
        "wago_tail_any": "Wago/native row with rare-wago tail pressure.",
        "transparent_wago_failure": (
            "Labeled wago-tail row where the anchor is too late by at least 0.12."
        ),
        "mixed_kanji_hiragana_tail": (
            "Wago-tail row whose surface has kanji plus hiragana morphology."
        ),
        "low_written_tail": "Wago-tail row with comparatively low written burden.",
        "ranked_tail": "Wago-tail row with a finite BCCWJ/core rank.",
        "obscure_written_tail": ("Wago-tail row with high obscure-written composite pressure."),
        "source_pair_review": "Scalar row is not JMDict-exact for the lemma/reading pair.",
        "transparent_proxy_candidate": (
            "Narrow existing-signal proxy for possible transparent wago downshift."
        ),
    }


def segment_memberships(row: Mapping[str, object]) -> list[str]:
    signals = _mapping(row.get("signals"))
    features = _mapping(row.get("surface_features"))
    segments: list[str] = []
    if wago_tail(row):
        segments.append("wago_tail_any")
    if transparent_wago_failure(row):
        segments.append("transparent_wago_failure")
    if wago_tail(row) and bool(features.get("mixed_kanji_hiragana")):
        segments.append("mixed_kanji_hiragana_tail")
    if wago_tail(row) and _float_signal(signals, "max_written_form_burden") <= 0.55:
        segments.append("low_written_tail")
    if wago_tail(row) and _optional_float(row.get("core_rank")) is not None:
        segments.append("ranked_tail")
    if wago_tail(row) and _float_signal(signals, "rare_wago_obscure_written_risk") >= 0.75:
        segments.append("obscure_written_tail")
    if source_pair_review(row):
        segments.append("source_pair_review")
    if transparent_proxy_candidate(row):
        segments.append("transparent_proxy_candidate")
    return segments


def wago_tail(row: Mapping[str, object]) -> bool:
    signals = _mapping(row.get("signals"))
    return (
        _float_signal(signals, "wtype_wago_ease") >= 0.75
        and _float_signal(signals, "rare_wago_tail_risk") >= 0.5
    )


def transparent_wago_failure(row: Mapping[str, object]) -> bool:
    return (
        wago_tail(row)
        and row.get("anchor_direction") == "too_high"
        and float(row.get("anchor_abs_error") or 0.0) >= 0.12
    )


def source_pair_review(row: Mapping[str, object]) -> bool:
    status = row.get("primary_pair_status")
    return status is not None and status != "jmdict_exact"


def common_protected(row: Mapping[str, object], *, spec: WagoCeilingSpec) -> bool:
    signals = _mapping(row.get("signals"))
    beginner_core = max(
        _float_signal(signals, "jlpt_vocab_beginner_core"),
        _float_signal(signals, "lesson_vocab_beginner_core"),
    )
    return spec.protect_beginner_core and beginner_core >= 0.1


def transparent_proxy_candidate(row: Mapping[str, object]) -> bool:
    spec = WagoCeilingSpec(
        spec_id="default_transparent_proxy_candidate",
        family="hybrid",
        ceiling=0.62,
        tail_min=0.75,
        written_max=0.55,
        rank_max=25000.0,
        obscure_max=0.95,
        protect_beginner_core=True,
        protect_source_pair_review=True,
        entity_max=0.95,
    )
    return policy_matches(row, spec)


def wago_ceiling_specs() -> list[WagoCeilingSpec]:
    specs: list[WagoCeilingSpec] = []
    for family in (
        "low_written",
        "mixed_surface",
        "ranked_tail",
        "low_obscure",
        "hybrid",
    ):
        for ceiling in (0.48, 0.54, 0.62, 0.68, 0.74):
            for tail_min in (0.5, 0.7, 0.85):
                for written_max in (0.45, 0.55, 0.65):
                    for obscure_max in (0.75, 0.9, 0.98):
                        specs.append(
                            WagoCeilingSpec(
                                spec_id=spec_id(
                                    family=family,
                                    ceiling=ceiling,
                                    tail_min=tail_min,
                                    written_max=written_max,
                                    obscure_max=obscure_max,
                                ),
                                family=family,
                                ceiling=ceiling,
                                tail_min=tail_min,
                                written_max=written_max,
                                rank_max=25000.0,
                                obscure_max=obscure_max,
                                protect_beginner_core=True,
                                protect_source_pair_review=True,
                                entity_max=0.95,
                            )
                        )
    return specs


def spec_id(
    *,
    family: str,
    ceiling: float,
    tail_min: float,
    written_max: float,
    obscure_max: float,
) -> str:
    return (
        f"wago_{family}_c{id_float(ceiling)}_t{id_float(tail_min)}"
        f"_w{id_float(written_max)}_o{id_float(obscure_max)}"
    )


def id_float(value: float) -> str:
    return f"{value:.2f}".replace("0.", "").replace(".", "p")


def adjusted_rows_for_spec(
    rows: Sequence[Mapping[str, object]],
    spec: WagoCeilingSpec,
) -> list[dict[str, object]]:
    return [dict(row) | adjusted_payload(row, spec) for row in rows]


def adjusted_payload(row: Mapping[str, object], spec: WagoCeilingSpec) -> dict[str, object]:
    observed = _float_or_nan(row.get("anchor_observed"))
    expected = _float_or_nan(row.get("expected"))
    ceiling = spec.ceiling if policy_matches(row, spec) else None
    adjusted = observed if ceiling is None else min(observed, ceiling)
    return {
        "adjusted_observed": _rounded(adjusted),
        "adjusted_abs_error": _rounded(abs(expected - adjusted)),
        "adjusted_band": _difficulty_band(adjusted),
        "changed": ceiling is not None and adjusted < observed - 1e-9,
        "policy_ceiling": ceiling,
        "policy_reason": "transparent_wago_ceiling" if ceiling is not None else "not_matched",
    }


def policy_matches(row: Mapping[str, object], spec: WagoCeilingSpec) -> bool:
    if not wago_tail(row):
        return False
    if source_pair_review(row) and spec.protect_source_pair_review:
        return False
    if common_protected(row, spec=spec):
        return False
    signals = _mapping(row.get("signals"))
    if _float_signal(signals, "rare_wago_tail_risk") < spec.tail_min:
        return False
    if _float_signal(signals, "named_entity_risk") > spec.entity_max:
        return False
    return raw_family_matches(row, spec)


def raw_family_matches(row: Mapping[str, object], spec: WagoCeilingSpec) -> bool:
    signals = _mapping(row.get("signals"))
    features = _mapping(row.get("surface_features"))
    written = _float_signal(signals, "max_written_form_burden")
    obscure = _float_signal(signals, "rare_wago_obscure_written_risk")
    rank = _optional_float(row.get("core_rank"))
    low_written = written <= spec.written_max
    mixed_surface = bool(features.get("mixed_kanji_hiragana"))
    ranked_tail = rank is not None and rank <= spec.rank_max
    low_obscure = obscure <= spec.obscure_max
    if spec.family == "low_written":
        return low_written
    if spec.family == "mixed_surface":
        return mixed_surface
    if spec.family == "ranked_tail":
        return ranked_tail
    if spec.family == "low_obscure":
        return low_obscure
    if spec.family == "hybrid":
        return low_written or mixed_surface or ranked_tail or low_obscure
    raise ValueError(f"Unknown wago ceiling family: {spec.family}")


def candidate_report(
    rows: Sequence[Mapping[str, object]],
    spec: WagoCeilingSpec,
) -> dict[str, object]:
    adjusted = adjusted_rows_for_spec(rows, spec)
    datasets = {
        dataset_id: curve_result([row for row in adjusted if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    return {
        "candidate_id": spec.spec_id,
        "spec": spec_payload(spec),
        "passes_guardrails": passes_guardrails(datasets),
        "datasets": datasets,
        "summary": candidate_summary(datasets),
    }


def curve_result(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    wago_rows = [row for row in rows if "wago_tail_any" in row.get("segments", ())]
    transparent_failures = [
        row for row in rows if "transparent_wago_failure" in row.get("segments", ())
    ]
    changed_rows = [row for row in rows if row.get("changed")]
    regressions = [
        row
        for row in changed_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    success_regressions = [
        row
        for row in changed_rows
        if float(row.get("anchor_abs_error") or 0.0) <= 0.08
        and float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    return {
        "row_count": len(rows),
        "wago_tail_count": len(wago_rows),
        "transparent_failure_count": len(transparent_failures),
        "changed_count": len(changed_rows),
        "changed_regressions": len(regressions),
        "success_regressions": len(success_regressions),
        "all_rows": metrics_for_rows(rows),
        "wago_tail_rows": metrics_for_rows(wago_rows),
        "transparent_failure_rows": metrics_for_rows(transparent_failures),
        "changed_rows": metrics_for_rows(changed_rows),
    }


def metrics_for_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    expected = np.asarray([_float_or_nan(row.get("expected")) for row in rows], dtype=np.float32)
    anchor = np.asarray(
        [_float_or_nan(row.get("anchor_observed")) for row in rows],
        dtype=np.float32,
    )
    adjusted = np.asarray(
        [_float_or_nan(row.get("adjusted_observed", row.get("anchor_observed"))) for row in rows],
        dtype=np.float32,
    )
    labels = [str(row.get("label")) for row in rows]
    expected_bands = [str(row.get("expected_band")) for row in rows]
    anchor_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=anchor,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    adjusted_summary = _summary_metrics(
        _difficulty_metrics(
            expected_values=expected,
            observed_values=adjusted,
            expected_bands=expected_bands,
            labels=labels,
        )
    )
    return {
        "count": len(rows),
        "anchor": anchor_summary,
        "adjusted": adjusted_summary,
        "delta": {
            "mae_reduction": _rounded(
                float(anchor_summary.get("mae") or 0.0) - float(adjusted_summary.get("mae") or 0.0)
            ),
            "bucket_delta": _rounded(
                float(adjusted_summary.get("bucket_accuracy") or 0.0)
                - float(anchor_summary.get("bucket_accuracy") or 0.0)
            ),
            "pairwise_delta": _rounded(
                float(adjusted_summary.get("pairwise_accuracy") or 0.0)
                - float(anchor_summary.get("pairwise_accuracy") or 0.0)
            ),
        },
    }


def passes_guardrails(datasets: Mapping[str, Mapping[str, object]]) -> bool:
    validation = _mapping(datasets.get("stitch_validation"))
    if metric_delta(validation, "transparent_failure_rows", "mae_reduction") <= 0.0:
        return False
    for dataset_id in DATASET_ORDER:
        dataset = _mapping(datasets.get(dataset_id))
        if int(dataset.get("changed_regressions") or 0) > 0:
            return False
        if int(dataset.get("success_regressions") or 0) > 0:
            return False
        if metric_delta(dataset, "all_rows", "mae_reduction") < -0.000001:
            return False
    return True


def candidate_summary(datasets: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        dataset_id: {
            "all_mae_reduction": metric_delta(dataset, "all_rows", "mae_reduction"),
            "wago_tail_mae_reduction": metric_delta(
                dataset,
                "wago_tail_rows",
                "mae_reduction",
            ),
            "transparent_failure_mae_reduction": metric_delta(
                dataset,
                "transparent_failure_rows",
                "mae_reduction",
            ),
            "changed_count": _mapping(dataset).get("changed_count"),
            "changed_regressions": _mapping(dataset).get("changed_regressions"),
            "success_regressions": _mapping(dataset).get("success_regressions"),
        }
        for dataset_id, dataset in datasets.items()
    }


def candidate_rank_key(candidate: Mapping[str, object]) -> tuple[float, ...]:
    datasets = _mapping(candidate.get("datasets"))
    validation = _mapping(datasets.get("stitch_validation"))
    holdout = _mapping(datasets.get("holdout"))
    calibration = _mapping(datasets.get("calibration"))
    return (
        1.0 if candidate.get("passes_guardrails") else 0.0,
        metric_delta(validation, "transparent_failure_rows", "mae_reduction"),
        metric_delta(validation, "all_rows", "mae_reduction"),
        metric_delta(holdout, "all_rows", "mae_reduction"),
        metric_delta(calibration, "all_rows", "mae_reduction"),
        -float(_mapping(validation).get("changed_regressions") or 0.0),
        -float(_mapping(holdout).get("changed_regressions") or 0.0),
    )


def metric_delta(dataset: Mapping[str, object], scope: str, key: str) -> float:
    metrics = _mapping(dataset.get(scope))
    return float(_mapping(metrics.get("delta")).get(key) or 0.0)


def dataset_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        dataset_id: segment_report(
            "all_scalar",
            [row for row in rows if row.get("dataset_id") == dataset_id],
        )
        for dataset_id in DATASET_ORDER
    }


def segment_report(segment_id: str, rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_dataset = {
        dataset_id: base_row_stats([row for row in rows if row.get("dataset_id") == dataset_id])
        for dataset_id in DATASET_ORDER
    }
    return {
        "segment_id": segment_id,
        "count": len(rows),
        "by_dataset": by_dataset,
        "overall": base_row_stats(rows),
    }


def base_row_stats(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "count": 0,
            "mae": None,
            "mean_observed_minus_expected": None,
            "too_low": 0,
            "too_high": 0,
        }
    errors = [
        float(row.get("anchor_observed") or 0.0) - float(row.get("expected") or 0.0) for row in rows
    ]
    return {
        "count": len(rows),
        "mae": _rounded(
            sum(abs(float(row.get("anchor_abs_error") or 0.0)) for row in rows) / len(rows)
        ),
        "mean_observed_minus_expected": _rounded(sum(errors) / len(errors)),
        "too_low": len([row for row in rows if row.get("anchor_direction") == "too_low"]),
        "too_high": len([row for row in rows if row.get("anchor_direction") == "too_high"]),
    }


def changed_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [row for row in rows if row.get("dataset_id") == dataset_id and row.get("changed")],
            key=lambda row: float(row.get("anchor_abs_error") or 0.0),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def regression_rows_by_dataset(
    rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> dict[str, object]:
    return {
        dataset_id: sorted(
            [
                row
                for row in rows
                if row.get("dataset_id") == dataset_id
                and row.get("changed")
                and float(row.get("adjusted_abs_error") or 0.0)
                > float(row.get("anchor_abs_error") or 0.0) + 1e-9
            ],
            key=lambda row: (
                float(row.get("adjusted_abs_error") or 0.0)
                - float(row.get("anchor_abs_error") or 0.0)
            ),
            reverse=True,
        )[:detail_limit]
        for dataset_id in DATASET_ORDER
    }


def full_matrix_review_pack(
    matrix: MatrixView,
    spec: WagoCeilingSpec,
    *,
    anchor_scores: np.ndarray,
    detail_limit: int,
) -> dict[str, object]:
    would_match: list[dict[str, object]] = []
    would_change: list[dict[str, object]] = []
    for index, lemma in enumerate(matrix.lemmas):
        if matrix.candidate_states[index] != "normal_vocab":
            continue
        row = matrix_review_row(index, matrix=matrix, anchor_scores=anchor_scores)
        if policy_matches(row, spec):
            would_match.append(review_pack_row(row, spec, reason="would_match"))
            if float(row.get("anchor_observed") or 0.0) > spec.ceiling:
                would_change.append(review_pack_row(row, spec, reason="would_change"))
    would_match.sort(key=review_pack_sort_key, reverse=True)
    would_change.sort(key=review_pack_sort_key, reverse=True)
    return {
        "candidate_id": spec.spec_id,
        "would_match_count": len(would_match),
        "would_change_count": len(would_change),
        "would_match_examples": would_match[:detail_limit],
        "would_change_examples": would_change[:detail_limit],
    }


def matrix_review_row(
    index: int,
    *,
    matrix: MatrixView,
    anchor_scores: np.ndarray,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "dataset_id": "full_matrix",
        "label": f"{matrix.lemmas[index]}/{matrix.readings[index]}",
        "lemma": matrix.lemmas[index],
        "reading": matrix.readings[index],
        "anchor_observed": _rounded(float(anchor_scores[index])),
        "candidate_state": matrix.candidate_states[index],
        "problem_class": matrix.problem_classes[index],
        "core_rank": _rounded(float(matrix.core_ranks[index])),
        "primary_pair_status": None,
        "signals": signal_snapshot(index, matrix=matrix),
        "surface_features": surface_features(matrix.lemmas[index]),
    }
    payload["segments"] = segment_memberships(payload)
    return payload


def review_pack_row(
    row: Mapping[str, object],
    spec: WagoCeilingSpec,
    *,
    reason: str,
) -> dict[str, object]:
    return {
        "label": row.get("label"),
        "lemma": row.get("lemma"),
        "reading": row.get("reading"),
        "anchor_observed": row.get("anchor_observed"),
        "candidate_state": row.get("candidate_state"),
        "problem_class": row.get("problem_class"),
        "core_rank": row.get("core_rank"),
        "policy_ceiling": spec.ceiling,
        "would_change": float(row.get("anchor_observed") or 0.0) > spec.ceiling,
        "review_reason": reason,
        "reason_flags": reason_flags(row),
        "segments": row.get("segments"),
        "signals": row.get("signals"),
        "surface_features": row.get("surface_features"),
    }


def reason_flags(row: Mapping[str, object]) -> list[str]:
    signals = _mapping(row.get("signals"))
    features = _mapping(row.get("surface_features"))
    flags = []
    if bool(features.get("mixed_kanji_hiragana")):
        flags.append("mixed_surface")
    if _float_signal(signals, "max_written_form_burden") <= 0.55:
        flags.append("low_written")
    if _optional_float(row.get("core_rank")) is not None:
        flags.append("ranked_tail")
    if _float_signal(signals, "rare_wago_obscure_written_risk") <= 0.9:
        flags.append("low_obscure")
    if _float_signal(signals, "named_entity_risk") >= 0.5:
        flags.append("entity_overlap")
    return flags


def review_pack_sort_key(row: Mapping[str, object]) -> tuple[float, ...]:
    signals = _mapping(row.get("signals"))
    return (
        _float_signal(signals, "rare_wago_tail_risk"),
        _float_signal(signals, "frequency"),
        -_float_signal(signals, "max_written_form_burden"),
    )


def candidate_space_summary() -> dict[str, object]:
    return {
        "families": [
            "low_written",
            "mixed_surface",
            "ranked_tail",
            "low_obscure",
            "hybrid",
        ],
        "ceilings": [0.48, 0.54, 0.62, 0.68, 0.74],
        "tail_thresholds": [0.5, 0.7, 0.85],
        "written_max": [0.45, 0.55, 0.65],
        "obscure_max": [0.75, 0.9, 0.98],
        "candidate_count": len(wago_ceiling_specs()),
    }


def interpretation(
    best: Mapping[str, object],
    segment_rows: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    best_summary = _mapping(best.get("summary"))
    validation = _mapping(best_summary.get("stitch_validation"))
    holdout = _mapping(best_summary.get("holdout"))
    transparent_failures = segment_report(
        "transparent_wago_failure",
        segment_rows.get("transparent_wago_failure", ()),
    )
    return {
        "best_passes_guardrails": bool(best.get("passes_guardrails")),
        "promotion_readiness": (
            "review_only_candidate_not_runtime_promotable"
            if best.get("passes_guardrails")
            else "not_promotable_from_current_probe"
        ),
        "validation_transparent_failure_delta": validation.get("transparent_failure_mae_reduction"),
        "holdout_all_delta": holdout.get("all_mae_reduction"),
        "transparent_failure_count": transparent_failures.get("count"),
        "main_caveat": (
            "Existing signals approximate transparency only indirectly through "
            "surface script, written burden, rank, and obscure-written composites. "
            "If the full-matrix would-change set is broad or semantically mixed, "
            "this should become a new constituent/transparency signal rather than "
            "a runtime scalar correction."
        ),
    }


def spec_payload(spec: WagoCeilingSpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "family": spec.family,
        "ceiling": spec.ceiling,
        "tail_min": spec.tail_min,
        "written_max": spec.written_max,
        "rank_max": spec.rank_max,
        "obscure_max": spec.obscure_max,
        "protect_beginner_core": spec.protect_beginner_core,
        "protect_source_pair_review": spec.protect_source_pair_review,
        "entity_max": spec.entity_max,
    }


def spec_from_payload(payload: Mapping[str, object]) -> WagoCeilingSpec:
    return WagoCeilingSpec(
        spec_id=str(payload.get("spec_id") or ""),
        family=str(payload.get("family") or "hybrid"),
        ceiling=float(payload.get("ceiling") or 0.62),
        tail_min=float(payload.get("tail_min") or 0.75),
        written_max=float(payload.get("written_max") or 0.55),
        rank_max=float(payload.get("rank_max") or 25000.0),
        obscure_max=float(payload.get("obscure_max") or 0.9),
        protect_beginner_core=bool(payload.get("protect_beginner_core")),
        protect_source_pair_review=bool(payload.get("protect_source_pair_review")),
        entity_max=float(payload.get("entity_max") or 0.95),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Transparent Wago Tail Audit",
        "",
        "Status: generated sidecar diagnostic",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        f"Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        "",
        "## Interpretation",
        "",
    ]
    for key, value in _mapping(summary.get("interpretation")).items():
        lines.append(f"- `{_escape(key)}`: `{_escape(display_value(value))}`")
    lines.extend(["", "## Dataset Summary", ""])
    lines.extend(dataset_summary_table(_mapping(report.get("dataset_summary"))))
    lines.extend(["", "## Segment Summary", ""])
    lines.extend(segment_summary_table(_mapping(report.get("segment_summary"))))
    lines.extend(["", "## Candidate Space", ""])
    lines.extend(candidate_space_lines(_mapping(report.get("candidate_space"))))
    lines.extend(["", "## Probe Leaderboard", ""])
    lines.extend(leaderboard_table(_rows(report.get("leaderboard"))))
    lines.extend(["", "## Best Candidate Changed Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_changed_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    lines.extend(["## Best Candidate Regression Rows", ""])
    for dataset_id, rows in _mapping(report.get("best_regression_rows")).items():
        lines.extend([f"### `{_escape(dataset_id)}`", ""])
        lines.extend(row_table(_rows(rows)))
        lines.append("")
    full_matrix = _mapping(report.get("best_full_matrix_review"))
    lines.extend(["## Full-Matrix Would-Change Review", ""])
    lines.append(f"- Candidate: `{_escape(full_matrix.get('candidate_id'))}`")
    lines.append(f"- Would-match count: `{_escape(full_matrix.get('would_match_count'))}`")
    lines.append(f"- Would-change count: `{_escape(full_matrix.get('would_change_count'))}`")
    lines.extend(["", "### Would-Change Examples", ""])
    lines.extend(review_pack_table(_rows(full_matrix.get("would_change_examples"))))
    lines.extend(["", "### Would-Match Examples", ""])
    lines.extend(review_pack_table(_rows(full_matrix.get("would_match_examples"))))
    return "\n".join(lines).rstrip() + "\n"


def dataset_summary_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Dataset | Rows | MAE | Bias obs-exp | Too low | Too high |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_id, row in summary.items():
        parsed = _mapping(_mapping(row).get("overall"))
        lines.append(
            f"| `{_escape(dataset_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(parsed.get('mae'))} | "
            f"{_escape(parsed.get('mean_observed_minus_expected'))} | "
            f"{_escape(parsed.get('too_low'))} | "
            f"{_escape(parsed.get('too_high'))} |"
        )
    return lines


def segment_summary_table(summary: Mapping[str, object]) -> list[str]:
    lines = [
        "| Segment | Count | Overall MAE | Bias obs-exp | Calib | Holdout | Validation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for segment_id, row in summary.items():
        parsed = _mapping(row)
        overall = _mapping(parsed.get("overall"))
        by_dataset = _mapping(parsed.get("by_dataset"))
        lines.append(
            f"| `{_escape(segment_id)}` | "
            f"{_escape(parsed.get('count'))} | "
            f"{_escape(overall.get('mae'))} | "
            f"{_escape(overall.get('mean_observed_minus_expected'))} | "
            f"{_escape(_mapping(by_dataset.get('calibration')).get('count'))} | "
            f"{_escape(_mapping(by_dataset.get('holdout')).get('count'))} | "
            f"{_escape(_mapping(by_dataset.get('stitch_validation')).get('count'))} |"
        )
    return lines


def candidate_space_lines(space: Mapping[str, object]) -> list[str]:
    return [
        f"- Candidate count: `{_escape(space.get('candidate_count'))}`",
        f"- Families: `{_escape(', '.join(str(item) for item in _sequence(space.get('families'))))}`",
        f"- Ceilings: `{_escape(_sequence(space.get('ceilings')))}`",
        f"- Tail thresholds: `{_escape(_sequence(space.get('tail_thresholds')))}`",
        f"- Written max thresholds: `{_escape(_sequence(space.get('written_max')))}`",
    ]


def leaderboard_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Candidate | Pass | Val transparent ΔMAE | Val all ΔMAE | Holdout all ΔMAE | Calib all ΔMAE | Val regressions | Holdout regressions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        summary = _mapping(row.get("summary"))
        validation = _mapping(summary.get("stitch_validation"))
        holdout = _mapping(summary.get("holdout"))
        calibration = _mapping(summary.get("calibration"))
        lines.append(
            f"| `{_escape(row.get('candidate_id'))}` | "
            f"{_escape(row.get('passes_guardrails'))} | "
            f"{_escape(validation.get('transparent_failure_mae_reduction'))} | "
            f"{_escape(validation.get('all_mae_reduction'))} | "
            f"{_escape(holdout.get('all_mae_reduction'))} | "
            f"{_escape(calibration.get('all_mae_reduction'))} | "
            f"{_escape(validation.get('changed_regressions'))} | "
            f"{_escape(holdout.get('changed_regressions'))} |"
        )
    return lines


def row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Expected | Anchor | Adjusted | Anchor Err | Adj Err | Status | Segments | Freq | WagoTail | Written |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"{_escape(row.get('expected'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('adjusted_observed'))} | "
            f"{_escape(row.get('anchor_abs_error'))} | "
            f"{_escape(row.get('adjusted_abs_error'))} | "
            f"`{_escape(row.get('primary_pair_status'))}` | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('segments'))))} | "
            f"{_escape(signals.get('frequency'))} | "
            f"{_escape(signals.get('rare_wago_tail_risk'))} | "
            f"{_escape(signals.get('max_written_form_burden'))} |"
        )
    return lines


def review_pack_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = [
        "| Label | Anchor | Ceiling | Rank | Flags | Segments | Freq | Tail | Written | Entity |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        lines.append(
            f"| {_escape(row.get('label'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('policy_ceiling'))} | "
            f"{_escape(row.get('core_rank'))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('reason_flags'))))} | "
            f"{_escape(', '.join(str(item) for item in _sequence(row.get('segments'))))} | "
            f"{_escape(signals.get('frequency'))} | "
            f"{_escape(signals.get('rare_wago_tail_risk'))} | "
            f"{_escape(signals.get('max_written_form_burden'))} | "
            f"{_escape(signals.get('named_entity_risk'))} |"
        )
    return lines


def display_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = _optional_float(signals.get(signal))
    return 0.0 if value is None else float(value)


def _float_or_nan(value: object) -> float:
    parsed = _optional_float(value)
    return float("nan") if parsed is None else float(parsed)


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


if __name__ == "__main__":
    raise SystemExit(main())
