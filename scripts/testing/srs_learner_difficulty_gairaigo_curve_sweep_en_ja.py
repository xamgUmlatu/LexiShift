#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_acceptance_review_pack_en_ja import (  # noqa: E402
    DEFAULT_VALIDATION_EVAL_JSON,
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
    DEFAULT_COMPONENT_MATRIX,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_curve_sweep_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_curve_sweep_en_ja_latest.md"
)
ANCHOR_MODEL = "ordinary_cap"
CURRENT_SPEC_ID = "gcur_t80_linear_b34_s28_c48_u40_ld52"
ROW_SIGNALS = (
    "frequency",
    "frequency_tail65",
    "frequency_tail80",
    "frequency_tail90",
    "frequency_unranked_risk",
    "bccwj_domain_rank_coverage",
    "jlpt_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "jmdict_priority",
    "jmdict_loanword_source_risk",
    "jmdict_foreign_priority_risk",
    "jmdict_field_marked_risk",
    "jmdict_news_or_policy_domain_risk",
    "wtype_gairaigo_risk",
)


@dataclass(frozen=True)
class CurveSpec:
    spec_id: str
    tail_lower: float
    tail_shape: str
    ranked_base: float
    ranked_slope: float
    ranked_cap: float
    unranked_floor: float
    unranked_low_domain_floor: float
    protection_frequency_max: float = 0.75
    protection_rank_max: float = 10000.0
    low_domain_coverage_max: float = 0.45


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep protected gairaigo floor curves against fresh en-ja "
            "validation rows without changing runtime behavior."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--validation-eval-json", type=Path, default=DEFAULT_VALIDATION_EVAL_JSON)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--leaderboard-limit", type=int, default=40)
    parser.add_argument("--detail-limit", type=int, default=30)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        validation_eval_json_path=_resolve_path(args.validation_eval_json),
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
    validation_eval_json_path: Path,
    anchor_model: str,
    leaderboard_limit: int = 40,
    detail_limit: int = 30,
) -> dict[str, object]:
    matrix = MatrixView.from_npz(np.load(component_matrix_path))
    validation_eval = _load_json(validation_eval_json_path)
    rows = validation_rows(validation_eval, matrix=matrix, anchor_model=anchor_model)
    candidates = [evaluate_curve(rows, spec) for spec in curve_specs()]
    ranked = sorted(candidates, key=_rank_key, reverse=True)
    best = next((row for row in ranked if row.get("passes_guardrails")), ranked[0])
    current = next(
        (row for row in candidates if row.get("spec_id") == CURRENT_SPEC_ID),
        evaluate_curve(rows, current_curve_spec()),
    )
    best_spec = spec_from_summary(_mapping(best.get("spec")))
    adjusted_best_rows = adjusted_rows_for_spec(rows, best_spec)
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "sweeps_run": True,
        "method": {
            "purpose": (
                "Search the gairaigo-specific floor curve while keeping common "
                "loanword protection fixed."
            ),
            "anchor_model": anchor_model,
            "guardrail_policy": (
                "Prefer curves with no changed-row regressions, no success-row "
                "regressions, positive gairaigo improvement, and non-negative "
                "overall validation MAE impact."
            ),
            "why_curve_only": (
                "This isolates the frequency relationship after the previous "
                "audit showed the protection predicate was necessary."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "validation_eval_json": _repo_or_home_path(validation_eval_json_path),
            "anchor_model": anchor_model,
            "validation_rows": len(rows),
            "gairaigo_rows": len([row for row in rows if row.get("is_gairaigo")]),
        },
        "curve_space": curve_space_description(),
        "summary": {
            "candidate_count": len(candidates),
            "current_spec_id": CURRENT_SPEC_ID,
            "best_spec_id": best.get("spec_id"),
            "current": current,
            "best": best,
            "best_vs_current": compare_candidates(best, current),
        },
        "leaderboard": ranked[:leaderboard_limit],
        "best_changed_rows": sorted(
            [row for row in adjusted_best_rows if row.get("changed")],
            key=lambda row: float(row.get("anchor_abs_error") or 0.0),
            reverse=True,
        )[:detail_limit],
        "best_gairaigo_failures": [
            row
            for row in adjusted_best_rows
            if row.get("is_gairaigo") and float(row.get("anchor_abs_error") or 0.0) >= 0.15
        ][:detail_limit],
        "best_gairaigo_successes": [
            row
            for row in adjusted_best_rows
            if row.get("is_gairaigo") and float(row.get("anchor_abs_error") or 0.0) <= 0.08
        ][:detail_limit],
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "validation_eval_json": validation_eval_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "gairaigo_curve_sweep": Path(__file__),
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
                "qualitative_failure_hypotheses": SCRIPT_DIR
                / "srs_learner_difficulty_qualitative_failure_hypotheses_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def curve_specs() -> list[CurveSpec]:
    specs = [current_curve_spec()]
    for tail_lower, tail_shape, base, slope, cap, unranked, low_domain in itertools.product(
        (0.65, 0.75, 0.80, 0.90),
        ("linear", "square", "sqrt", "step"),
        (0.30, 0.34, 0.38, 0.42),
        (0.20, 0.28, 0.36, 0.44),
        (0.46, 0.48, 0.50, 0.54, 0.58, 0.62),
        (0.40, 0.46, 0.52),
        (0.52, 0.58, 0.64, 0.70),
    ):
        spec = CurveSpec(
            spec_id=_spec_id(
                tail_lower=tail_lower,
                tail_shape=tail_shape,
                base=base,
                slope=slope,
                cap=cap,
                unranked=unranked,
                low_domain=low_domain,
            ),
            tail_lower=tail_lower,
            tail_shape=tail_shape,
            ranked_base=base,
            ranked_slope=slope,
            ranked_cap=cap,
            unranked_floor=unranked,
            unranked_low_domain_floor=low_domain,
        )
        if spec.spec_id != CURRENT_SPEC_ID:
            specs.append(spec)
    return specs


def current_curve_spec() -> CurveSpec:
    return CurveSpec(
        spec_id=CURRENT_SPEC_ID,
        tail_lower=0.80,
        tail_shape="linear",
        ranked_base=0.34,
        ranked_slope=0.28,
        ranked_cap=0.48,
        unranked_floor=0.40,
        unranked_low_domain_floor=0.52,
    )


def evaluate_curve(
    rows: Sequence[Mapping[str, object]],
    spec: CurveSpec,
) -> dict[str, object]:
    adjusted_rows = adjusted_rows_for_spec(rows, spec)
    gairaigo_rows = [row for row in adjusted_rows if row.get("is_gairaigo")]
    changed_rows = [row for row in adjusted_rows if row.get("changed")]
    failure_rows = [
        row for row in gairaigo_rows if float(row.get("anchor_abs_error") or 0.0) >= 0.15
    ]
    success_rows = [
        row for row in gairaigo_rows if float(row.get("anchor_abs_error") or 0.0) <= 0.08
    ]
    counts = curve_counts(gairaigo_rows, changed_rows, success_rows)
    metrics = {
        "all_validation": metrics_for_rows(adjusted_rows),
        "gairaigo_subset": metrics_for_rows(gairaigo_rows),
        "failure_subset": metrics_for_rows(failure_rows),
        "success_subset": metrics_for_rows(success_rows),
        "changed_subset": metrics_for_rows(changed_rows),
    }
    return {
        "spec_id": spec.spec_id,
        "spec": spec_summary(spec),
        "passes_guardrails": passes_guardrails(metrics, counts),
        "counts": counts,
        "metrics": metrics,
    }


def adjusted_rows_for_spec(
    rows: Sequence[Mapping[str, object]],
    spec: CurveSpec,
) -> list[dict[str, object]]:
    return [dict(row) | guarded_gairaigo_curve(row, spec) for row in rows]


def guarded_gairaigo_curve(row: Mapping[str, object], spec: CurveSpec) -> dict[str, object]:
    expected = _float_or_nan(row.get("expected"))
    observed = _float_or_nan(row.get("anchor_observed"))
    if not bool(row.get("is_gairaigo")):
        return adjusted_payload(
            observed=observed,
            expected=expected,
            changed=False,
            floor=None,
            policy_reason="not_gairaigo",
            tail_value=None,
        )
    signals = _mapping(row.get("signals"))
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    domain_coverage = _float_signal(signals, "bccwj_domain_rank_coverage")
    unranked_low_coverage = unranked >= 0.5 and domain_coverage <= spec.low_domain_coverage_max
    if protected_common_loanword(row, spec=spec):
        return adjusted_payload(
            observed=observed,
            expected=expected,
            changed=False,
            floor=None,
            policy_reason="protected_common_loanword",
            tail_value=None,
        )
    if unranked_low_coverage:
        floor = spec.unranked_low_domain_floor
        reason = "unranked_low_domain_coverage_floor"
        tail_value = None
    elif unranked >= 0.5:
        floor = spec.unranked_floor
        reason = "unranked_general_floor"
        tail_value = None
    else:
        tail_value = shaped_tail_value(frequency, lower=spec.tail_lower, shape=spec.tail_shape)
        floor = min(spec.ranked_cap, spec.ranked_base + spec.ranked_slope * tail_value)
        reason = "ranked_tail_floor"
    adjusted = max(observed, floor)
    return adjusted_payload(
        observed=adjusted,
        expected=expected,
        changed=adjusted > observed + 1e-9,
        floor=floor,
        policy_reason=reason,
        tail_value=tail_value,
    )


def protected_common_loanword(row: Mapping[str, object], *, spec: CurveSpec) -> bool:
    signals = _mapping(row.get("signals"))
    frequency = _float_signal(signals, "frequency")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    domain_coverage = _float_signal(signals, "bccwj_domain_rank_coverage")
    jlpt = _float_signal(signals, "jlpt_vocab_difficulty")
    jlpt_core = _float_signal(signals, "jlpt_vocab_beginner_core")
    lesson_core = _float_signal(signals, "lesson_vocab_beginner_core")
    rank = _optional_float(row.get("core_rank"))
    unranked_low_coverage = unranked >= 0.5 and domain_coverage <= spec.low_domain_coverage_max
    return (
        frequency <= spec.protection_frequency_max
        or (rank is not None and rank <= spec.protection_rank_max)
        or jlpt_core >= 0.1
        or lesson_core >= 0.1
        or (jlpt >= 0.65 and not unranked_low_coverage)
    )


def shaped_tail_value(frequency: float, *, lower: float, shape: str) -> float:
    if lower >= 1.0:
        raise ValueError("tail lower must be less than 1.0")
    tail = _clamp01((frequency - lower) / (1.0 - lower))
    if shape == "linear":
        return tail
    if shape == "square":
        return tail * tail
    if shape == "sqrt":
        return math.sqrt(tail)
    if shape == "step":
        if tail <= 0.0:
            return 0.0
        return 0.5 if tail < 0.5 else 1.0
    raise ValueError(f"Unknown tail shape: {shape}")


def adjusted_payload(
    *,
    observed: float,
    expected: float,
    changed: bool,
    floor: float | None,
    policy_reason: str,
    tail_value: float | None,
) -> dict[str, object]:
    return {
        "adjusted_observed": _rounded(observed),
        "adjusted_abs_error": _rounded(abs(expected - observed)),
        "adjusted_band": _difficulty_band(observed),
        "changed": changed,
        "policy_floor": _rounded(floor),
        "policy_reason": policy_reason,
        "policy_tail_value": _rounded(tail_value),
    }


def curve_counts(
    gairaigo_rows: Sequence[Mapping[str, object]],
    changed_rows: Sequence[Mapping[str, object]],
    success_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    changed_regressions = [
        row
        for row in changed_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    success_regressions = [
        row
        for row in success_rows
        if float(row.get("adjusted_abs_error") or 0.0)
        > float(row.get("anchor_abs_error") or 0.0) + 1e-9
    ]
    return {
        "gairaigo_rows": len(gairaigo_rows),
        "changed_rows": len(changed_rows),
        "protected_gairaigo_rows": len(
            [
                row
                for row in gairaigo_rows
                if row.get("policy_reason") == "protected_common_loanword"
            ]
        ),
        "changed_regressions": len(changed_regressions),
        "success_rows": len(success_rows),
        "changed_success_rows": len([row for row in success_rows if row.get("changed")]),
        "success_regressions": len(success_regressions),
    }


def passes_guardrails(
    metrics: Mapping[str, object],
    counts: Mapping[str, object],
) -> bool:
    all_delta = _mapping(_mapping(metrics.get("all_validation")).get("delta"))
    gairaigo_delta = _mapping(_mapping(metrics.get("gairaigo_subset")).get("delta"))
    failure_delta = _mapping(_mapping(metrics.get("failure_subset")).get("delta"))
    return (
        int(counts.get("changed_regressions") or 0) == 0
        and int(counts.get("success_regressions") or 0) == 0
        and float(all_delta.get("mae_reduction") or 0.0) >= 0.0
        and float(gairaigo_delta.get("mae_reduction") or 0.0) > 0.0
        and float(failure_delta.get("mae_reduction") or 0.0) > 0.0
    )


def metrics_for_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    expected = np.asarray([_float_or_nan(row.get("expected")) for row in rows], dtype=np.float32)
    anchor = np.asarray(
        [_float_or_nan(row.get("anchor_observed")) for row in rows],
        dtype=np.float32,
    )
    adjusted = np.asarray(
        [_float_or_nan(row.get("adjusted_observed")) for row in rows],
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


def validation_rows(
    validation_eval: Mapping[str, object],
    *,
    matrix: MatrixView,
    anchor_model: str,
) -> list[dict[str, object]]:
    pair_to_index = matrix.row_index_by_pair()
    rows: list[dict[str, object]] = []
    for row in _rows(_mapping(validation_eval.get("row_comparison")).get("all_rows")):
        label = str(row.get("label", ""))
        if "/" not in label:
            continue
        lemma, reading = label.split("/", 1)
        matrix_index = pair_to_index.get((lemma, reading))
        if matrix_index is None:
            continue
        model = _mapping(_mapping(row.get("models")).get(anchor_model))
        observed = _optional_float(model.get("observed"))
        expected = _optional_float(row.get("expected"))
        if observed is None or expected is None:
            continue
        signals = signal_snapshot(matrix_index, matrix=matrix)
        rows.append(
            {
                "label": label,
                "lemma": lemma,
                "reading": reading,
                "expected": _rounded(expected),
                "expected_band": _difficulty_band(expected),
                "anchor_observed": _rounded(observed),
                "anchor_abs_error": _rounded(abs(expected - observed)),
                "anchor_direction": "too_low" if observed < expected else "too_high",
                "candidate_state": matrix.candidate_states[matrix_index],
                "problem_class": matrix.problem_classes[matrix_index],
                "core_rank": _rounded(float(matrix.core_ranks[matrix_index])),
                "is_gairaigo": _float_signal(signals, "wtype_gairaigo_risk") >= 0.75,
                "signals": signals,
            }
        )
    return rows


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    snapshot: dict[str, object] = {}
    for signal in ROW_SIGNALS:
        column = component_index.get(signal)
        snapshot[signal] = (
            None if column is None else _rounded(float(matrix.component_values[index, column]))
        )
    return snapshot


def compare_candidates(
    best: Mapping[str, object], current: Mapping[str, object]
) -> dict[str, object]:
    return {
        "best_spec_id": best.get("spec_id"),
        "current_spec_id": current.get("spec_id"),
        "gairaigo_mae_reduction_delta": _rounded(
            metric_delta(best, "gairaigo_subset", "mae_reduction")
            - metric_delta(current, "gairaigo_subset", "mae_reduction")
        ),
        "failure_mae_reduction_delta": _rounded(
            metric_delta(best, "failure_subset", "mae_reduction")
            - metric_delta(current, "failure_subset", "mae_reduction")
        ),
        "overall_mae_reduction_delta": _rounded(
            metric_delta(best, "all_validation", "mae_reduction")
            - metric_delta(current, "all_validation", "mae_reduction")
        ),
    }


def metric_delta(candidate: Mapping[str, object], scope: str, key: str) -> float:
    metrics = _mapping(candidate.get("metrics"))
    return float(_mapping(_mapping(metrics.get(scope)).get("delta")).get(key) or 0.0)


def _rank_key(candidate: Mapping[str, object]) -> tuple[float, ...]:
    counts = _mapping(candidate.get("counts"))
    return (
        1.0 if candidate.get("passes_guardrails") else 0.0,
        -float(counts.get("success_regressions") or 0.0),
        -float(counts.get("changed_regressions") or 0.0),
        metric_delta(candidate, "failure_subset", "mae_reduction"),
        metric_delta(candidate, "gairaigo_subset", "mae_reduction"),
        metric_delta(candidate, "gairaigo_subset", "pairwise_delta"),
        metric_delta(candidate, "all_validation", "mae_reduction"),
    )


def curve_space_description() -> dict[str, object]:
    return {
        "protected_predicate": (
            "frequency <= 0.75 OR core_rank <= 10000 OR "
            "jlpt_vocab_beginner_core >= 0.1 OR lesson_vocab_beginner_core >= 0.1 "
            "OR jlpt_vocab_difficulty >= 0.65 unless unranked with low domain coverage"
        ),
        "ranked_floor": "min(cap, base + slope * shaped_tail(frequency))",
        "tail_lowers": [0.65, 0.75, 0.80, 0.90],
        "tail_shapes": ["linear", "square", "sqrt", "step"],
        "ranked_bases": [0.30, 0.34, 0.38, 0.42],
        "ranked_slopes": [0.20, 0.28, 0.36, 0.44],
        "ranked_caps": [0.46, 0.48, 0.50, 0.54, 0.58, 0.62],
        "unranked_floors": [0.40, 0.46, 0.52],
        "unranked_low_domain_floors": [0.52, 0.58, 0.64, 0.70],
        "current_spec_id": CURRENT_SPEC_ID,
    }


def spec_summary(spec: CurveSpec) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "tail_lower": spec.tail_lower,
        "tail_shape": spec.tail_shape,
        "ranked_base": spec.ranked_base,
        "ranked_slope": spec.ranked_slope,
        "ranked_cap": spec.ranked_cap,
        "unranked_floor": spec.unranked_floor,
        "unranked_low_domain_floor": spec.unranked_low_domain_floor,
        "protection_frequency_max": spec.protection_frequency_max,
        "protection_rank_max": spec.protection_rank_max,
        "low_domain_coverage_max": spec.low_domain_coverage_max,
    }


def spec_from_summary(summary: Mapping[str, object]) -> CurveSpec:
    return CurveSpec(
        spec_id=str(summary.get("spec_id") or ""),
        tail_lower=float(summary.get("tail_lower") or 0.80),
        tail_shape=str(summary.get("tail_shape") or "linear"),
        ranked_base=float(summary.get("ranked_base") or 0.34),
        ranked_slope=float(summary.get("ranked_slope") or 0.28),
        ranked_cap=float(summary.get("ranked_cap") or 0.48),
        unranked_floor=float(summary.get("unranked_floor") or 0.40),
        unranked_low_domain_floor=float(summary.get("unranked_low_domain_floor") or 0.52),
        protection_frequency_max=float(summary.get("protection_frequency_max") or 0.75),
        protection_rank_max=float(summary.get("protection_rank_max") or 10000.0),
        low_domain_coverage_max=float(summary.get("low_domain_coverage_max") or 0.45),
    )


def _spec_id(
    *,
    tail_lower: float,
    tail_shape: str,
    base: float,
    slope: float,
    cap: float,
    unranked: float,
    low_domain: float,
) -> str:
    return (
        f"gcur_t{_id_float(tail_lower)}_{tail_shape}"
        f"_b{_id_float(base)}_s{_id_float(slope)}_c{_id_float(cap)}"
        f"_u{_id_float(unranked)}_ld{_id_float(low_domain)}"
    )


def _id_float(value: float) -> str:
    return f"{value:.2f}".replace("0.", "").replace(".", "p")


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    inputs = _mapping(report.get("inputs"))
    lines = [
        "# en-ja Gairaigo Curve Sweep",
        "",
        "Status: generated sidecar experiment",
        f"Generated: `{_escape(report.get('generated_at'))}`",
        f"Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        "",
        "## Scope",
        "",
        f"- Anchor model: `{_escape(inputs.get('anchor_model'))}`",
        f"- Validation rows: `{_escape(inputs.get('validation_rows'))}`",
        f"- Gairaigo rows: `{_escape(inputs.get('gairaigo_rows'))}`",
        f"- Candidate curves: `{_escape(summary.get('candidate_count'))}`",
        "",
        "## Best Vs Current",
        "",
    ]
    lines.extend(_candidate_compare_table(summary))
    lines.extend(["", "## Leaderboard", ""])
    lines.extend(_leaderboard_table(_rows(report.get("leaderboard"))))
    lines.extend(["", "## Best Changed Rows", ""])
    lines.extend(_row_table(_rows(report.get("best_changed_rows"))))
    lines.extend(["", "## Best Gairaigo Failures", ""])
    lines.extend(_row_table(_rows(report.get("best_gairaigo_failures"))))
    lines.extend(["", "## Best Gairaigo Successes / Near Successes", ""])
    lines.extend(_row_table(_rows(report.get("best_gairaigo_successes"))))
    return "\n".join(lines).rstrip() + "\n"


def _candidate_compare_table(summary: Mapping[str, object]) -> list[str]:
    rows = [
        ("Current", _mapping(summary.get("current"))),
        ("Best", _mapping(summary.get("best"))),
    ]
    lines = [
        "| View | Spec | Pass | Changed | Regressions | Success regressions | Overall MAE reduction | Gairaigo MAE reduction | Failure MAE reduction |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, candidate in rows:
        counts = _mapping(candidate.get("counts"))
        metrics = _mapping(candidate.get("metrics"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(label),
                    f"`{_escape(candidate.get('spec_id'))}`",
                    _escape(candidate.get("passes_guardrails")),
                    _escape(counts.get("changed_rows")),
                    _escape(counts.get("changed_regressions")),
                    _escape(counts.get("success_regressions")),
                    _escape(metric_delta_from_metrics(metrics, "all_validation", "mae_reduction")),
                    _escape(metric_delta_from_metrics(metrics, "gairaigo_subset", "mae_reduction")),
                    _escape(metric_delta_from_metrics(metrics, "failure_subset", "mae_reduction")),
                ]
            )
            + " |"
        )
    return lines


def _leaderboard_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Rank | Spec | Pass | Changed | Regressions | Success regressions | Gairaigo MAE reduction | Failure MAE reduction | Pairwise delta | Params |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        counts = _mapping(row.get("counts"))
        metrics = _mapping(row.get("metrics"))
        spec = _mapping(row.get("spec"))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{_escape(row.get('spec_id'))}`",
                    _escape(row.get("passes_guardrails")),
                    _escape(counts.get("changed_rows")),
                    _escape(counts.get("changed_regressions")),
                    _escape(counts.get("success_regressions")),
                    _escape(metric_delta_from_metrics(metrics, "gairaigo_subset", "mae_reduction")),
                    _escape(metric_delta_from_metrics(metrics, "failure_subset", "mae_reduction")),
                    _escape(
                        metric_delta_from_metrics(metrics, "gairaigo_subset", "pairwise_delta")
                    ),
                    _escape(_compact_spec(spec)),
                ]
            )
            + " |"
        )
    return lines


def _row_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Label | Expected | Anchor | Adjusted | Anchor Err | Adj Err | Rank | Freq | Reason | Floor | Tail | Changed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(row.get("label")),
                    _escape(row.get("expected")),
                    _escape(row.get("anchor_observed")),
                    _escape(row.get("adjusted_observed")),
                    _escape(row.get("anchor_abs_error")),
                    _escape(row.get("adjusted_abs_error")),
                    _escape(row.get("core_rank")),
                    _escape(signals.get("frequency")),
                    f"`{_escape(row.get('policy_reason'))}`",
                    _escape(row.get("policy_floor")),
                    _escape(row.get("policy_tail_value")),
                    _escape(row.get("changed")),
                ]
            )
            + " |"
        )
    return lines


def metric_delta_from_metrics(metrics: Mapping[str, object], scope: str, key: str) -> object:
    return _mapping(_mapping(metrics.get(scope)).get("delta")).get(key)


def _compact_spec(spec: Mapping[str, object]) -> str:
    return (
        f"tail={spec.get('tail_lower')}/{spec.get('tail_shape')}, "
        f"base={spec.get('ranked_base')}, slope={spec.get('ranked_slope')}, "
        f"cap={spec.get('ranked_cap')}, u={spec.get('unranked_floor')}, "
        f"ld={spec.get('unranked_low_domain_floor')}"
    )


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = _optional_float(signals.get(signal))
    return 0.0 if value is None else float(value)


def _float_or_nan(value: object) -> float:
    parsed = _optional_float(value)
    return float("nan") if parsed is None else float(parsed)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
