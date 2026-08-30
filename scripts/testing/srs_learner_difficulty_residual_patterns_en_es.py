#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_SWEEP_JSON,
    _candidate_by_id,
    _score_formula,
    generate_candidates,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_metrics,
    _summary_metrics,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_patterns_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_residual_patterns_en_es_latest.md"
)
BASELINE_VARIANT_ID = "learner_source_zipf_medium"
PRIMARY_STATE = "normal_vocab"
DEFAULT_ERROR_THRESHOLD = 0.12
DEFAULT_CHANGE_THRESHOLD = 0.03


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Join reviewed en-es learner-difficulty labels to the current fixed "
            "baseline and selected formula-sweep candidate, then group residuals "
            "by computable signal patterns. This is a diagnostic sidecar only."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id", default=None)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--error-threshold", type=float, default=DEFAULT_ERROR_THRESHOLD)
    parser.add_argument("--change-threshold", type=float, default=DEFAULT_CHANGE_THRESHOLD)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    sweep_payload = _load_optional_json(Path(args.formula_sweep_json).expanduser())
    report = build_report(
        formula_report=formula_report,
        sweep_payload=sweep_payload,
        calibration_payload=_load_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_json(Path(args.holdout_json).expanduser()),
        candidate_id=args.candidate_id,
        error_threshold=max(0.01, float(args.error_threshold)),
        change_threshold=max(0.0, float(args.change_threshold)),
        detail_limit=max(1, int(args.detail_limit)),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
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


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    sweep_payload: Mapping[str, object] | None,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
    candidate_id: str | None = None,
    error_threshold: float = DEFAULT_ERROR_THRESHOLD,
    change_threshold: float = DEFAULT_CHANGE_THRESHOLD,
    detail_limit: int = 20,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    rows_by_lemma = {str(row.get("lemma") or "").lower(): row for row in formula_rows}
    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
    candidate = _candidate_by_id(generate_candidates(), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")

    calibration_labels = [
        _as_mapping(row) for row in _as_sequence(calibration_payload.get("labels"))
    ]
    holdout_labels = [_as_mapping(row) for row in _as_sequence(holdout_payload.get("labels"))]
    labeled_rows = _labeled_rows(
        rows_by_lemma=rows_by_lemma,
        calibration_labels=calibration_labels,
        holdout_labels=holdout_labels,
        candidate=candidate,
        error_threshold=error_threshold,
    )
    primary_rows = [
        row for row in labeled_rows if row.get("expected_candidate_state") == PRIMARY_STATE
    ]
    residual_rows = [
        row
        for row in primary_rows
        if (_safe_float(row.get("candidate_abs_error")) or 0.0) >= error_threshold
    ]
    family_reports = _family_reports(residual_rows, detail_limit=detail_limit)
    route_reports = _route_reports(
        primary_rows,
        error_threshold=error_threshold,
        detail_limit=detail_limit,
    )
    changes = _change_reports(
        primary_rows,
        change_threshold=change_threshold,
        detail_limit=detail_limit,
    )
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_residual_patterns_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Diagnostic working set for moving from broad formula sweeps to "
                "specific en-es residual hypotheses."
            ),
            "baseline_variant_id": BASELINE_VARIANT_ID,
            "candidate_id": selected_candidate_id,
            "error_threshold": _round_float(error_threshold),
            "change_threshold": _round_float(change_threshold),
            "primary_state": PRIMARY_STATE,
            "score_source": "formula probe rows plus formula sweep candidate math",
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "calibration_id": calibration_payload.get("calibration_id"),
            "holdout_id": holdout_payload.get("holdout_id"),
            "calibration_count": len(calibration_labels),
            "holdout_count": len(holdout_labels),
            "labeled_rows_joined": len(labeled_rows),
            "primary_rows": len(primary_rows),
        },
        "summary": {
            "baseline_primary": _metrics(primary_rows, score_key="baseline_score"),
            "candidate_primary": _metrics(primary_rows, score_key="candidate_score"),
            "residual_count": len(residual_rows),
            "residual_threshold": _round_float(error_threshold),
            "residual_direction_counts": _direction_counts(residual_rows),
            "largest_candidate_errors": _largest_rows(
                residual_rows,
                sort_key="candidate_abs_error",
                detail_limit=detail_limit,
            ),
            "family_count": len(family_reports),
            "component_route_count": len(route_reports),
            "improvement_count": changes["improvement_count"],
            "regression_count": changes["regression_count"],
        },
        "candidate_vs_baseline_changes": changes,
        "residual_families": family_reports,
        "component_problem_routes": route_reports,
        "residual_rows": sorted(
            residual_rows,
            key=lambda row: _safe_float(row.get("candidate_abs_error")) or 0.0,
            reverse=True,
        ),
        "limitations": [
            "Residual tags are computable diagnostics, not gold linguistic labels.",
            "The calibration and holdout labels are still small; use this report to choose next hypotheses, not to promote a new runtime model by itself.",
            "Manual corrections and admission restrictions remain separate from scalar difficulty ranking.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    inputs = _as_mapping(report.get("inputs"))
    summary = _as_mapping(report.get("summary"))
    baseline = _as_mapping(summary.get("baseline_primary"))
    candidate = _as_mapping(summary.get("candidate_primary"))
    lines = [
        "# en-es Learner Difficulty Residual Patterns",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Inputs",
        "",
        f"- Formula probe: `{inputs.get('formula_probe_decision')}`",
        f"- Formula sweep: `{inputs.get('formula_sweep_decision')}`",
        f"- Calibration labels: `{inputs.get('calibration_count')}`",
        f"- Holdout labels: `{inputs.get('holdout_count')}`",
        f"- Joined labeled rows: `{inputs.get('labeled_rows_joined')}`",
        f"- Primary rows: `{inputs.get('primary_rows')}`",
        "",
        "## Score Baseline",
        "",
        f"- Baseline variant: `{method.get('baseline_variant_id')}`",
        f"- Candidate: `{method.get('candidate_id')}`",
        f"- Residual threshold: `{method.get('error_threshold')}`",
        "",
        "| Model | Rows | Balanced | MAE | Bucket | Pairwise | High Tail |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        _metric_row("baseline", baseline),
        _metric_row("candidate", candidate),
        "",
        "## Summary",
        "",
        f"- Residual rows at threshold: `{summary.get('residual_count')}`",
        f"- Residual directions: `{_json_inline(summary.get('residual_direction_counts'))}`",
        f"- Candidate improvements vs baseline: `{summary.get('improvement_count')}`",
        f"- Candidate regressions vs baseline: `{summary.get('regression_count')}`",
        "",
        "## Residual Families",
        "",
        "| Family | Count | Too Hard | Too Easy | Mean Error | Examples |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for raw in _as_sequence(report.get("residual_families")):
        item = _as_mapping(raw)
        examples = ", ".join(
            f"`{_escape(row.get('lemma'))}`" for row in _as_sequence(item.get("examples"))[:6]
        )
        lines.append(
            f"| `{_escape(item.get('family'))}` | {item.get('count')} | "
            f"{item.get('too_hard_count')} | {item.get('too_easy_count')} | "
            f"{_fmt(item.get('mean_abs_error'))} | {examples or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Component Problem Routes",
            "",
            "| Route | Rows | Residuals | Counterexamples | Too Hard | Too Easy | Need | Examples |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for raw in _as_sequence(report.get("component_problem_routes")):
        item = _as_mapping(raw)
        examples = ", ".join(
            f"`{_escape(row.get('lemma'))}`"
            for row in _as_sequence(item.get("residual_examples"))[:5]
        )
        if not examples:
            examples = ", ".join(
                f"`{_escape(row.get('lemma'))}`"
                for row in _as_sequence(item.get("counterexamples"))[:5]
            )
        lines.append(
            f"| `{_escape(item.get('route'))}` | {item.get('row_count')} | "
            f"{item.get('residual_count')} | {item.get('counterexample_count')} | "
            f"{item.get('too_hard_count')} | {item.get('too_easy_count')} | "
            f"{_escape(item.get('recommended_next_signal'))} | {examples or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Largest Residual Rows",
            "",
            "| Split | Lemma | Expected | Candidate | Baseline | Error | Delta vs Baseline | Tags |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for raw in _as_sequence(summary.get("largest_candidate_errors")):
        item = _as_mapping(raw)
        lines.append(_row_line(item))
    changes = _as_mapping(report.get("candidate_vs_baseline_changes"))
    for key, title in (
        ("largest_improvements", "Largest Improvements vs Baseline"),
        ("largest_regressions", "Largest Regressions vs Baseline"),
    ):
        rows = _as_sequence(changes.get(key))
        if not rows:
            continue
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                "| Split | Lemma | Expected | Candidate | Baseline | Error | Delta vs Baseline | Tags |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for raw in rows:
            lines.append(_row_line(_as_mapping(raw)))
    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["", "## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return "spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard"


def _labeled_rows(
    *,
    rows_by_lemma: Mapping[str, Mapping[str, object]],
    calibration_labels: Sequence[Mapping[str, object]],
    holdout_labels: Sequence[Mapping[str, object]],
    candidate: object,
    error_threshold: float,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for split, labels in (("calibration", calibration_labels), ("holdout", holdout_labels)):
        for label in labels:
            expected = _safe_float(label.get("expected_learner_difficulty"))
            if expected is None:
                continue
            lemma = str(label.get("lemma") or "")
            row = rows_by_lemma.get(lemma.lower())
            if row is None:
                continue
            baseline = _safe_float(_as_mapping(row.get("variant_scores")).get(BASELINE_VARIANT_ID))
            if baseline is None:
                continue
            candidate_score = _score_formula(candidate, row)
            baseline_error = abs(baseline - expected)
            candidate_error = abs(candidate_score - expected)
            score_delta = candidate_score - baseline
            error_delta = candidate_error - baseline_error
            tags = _residual_tags(row=row, label=label, expected=expected, observed=candidate_score)
            problem_routes = _problem_routes(
                row=row,
                label=label,
                expected=expected,
                observed=candidate_score,
                abs_error=candidate_error,
                error_threshold=error_threshold,
            )
            dictionary = _as_mapping(row.get("dictionary"))
            result.append(
                {
                    "split": split,
                    "lemma": lemma,
                    "expected": _round_float(expected),
                    "baseline_score": _round_float(baseline),
                    "candidate_score": _round_float(candidate_score),
                    "baseline_abs_error": _round_float(baseline_error),
                    "candidate_abs_error": _round_float(candidate_error),
                    "score_delta_vs_baseline": _round_float(score_delta),
                    "error_delta_vs_baseline": _round_float(error_delta),
                    "direction": "too_hard" if candidate_score > expected else "too_easy",
                    "expected_candidate_state": label.get("expected_candidate_state"),
                    "expected_problem_class": label.get("expected_problem_class"),
                    "expected_difficulty_band": label.get("expected_difficulty_band"),
                    "review_flags": list(_as_sequence(label.get("review_flags"))),
                    "review_confidence": label.get("review_confidence"),
                    "rationale": label.get("rationale"),
                    "pos": row.get("pos"),
                    "pos_bucket": row.get("pos_bucket"),
                    "spalex_rank": row.get("spalex_rank"),
                    "learner_source_count": len(_as_sequence(row.get("learner_source"))),
                    "broad_learner_known": bool(
                        _as_mapping(row.get("learner_source_context")).get("broad_source_known")
                    ),
                    "dictionary_entry_count": dictionary.get("entry_count"),
                    "dictionary_marked_terms": list(_as_sequence(dictionary.get("marked_terms"))),
                    "dictionary_topics": list(_as_sequence(dictionary.get("topics"))),
                    "translations": list(_as_sequence(row.get("translations")))[:4],
                    "tags": tags,
                    "problem_routes": problem_routes,
                    "salient_signals": _salient_signals(_as_mapping(row.get("components"))),
                }
            )
    return result


def _residual_tags(
    *,
    row: Mapping[str, object],
    label: Mapping[str, object],
    expected: float,
    observed: float,
) -> list[str]:
    components = _as_mapping(row.get("components"))
    context = _as_mapping(row.get("learner_source_context"))
    review_flags = {str(flag) for flag in _as_sequence(label.get("review_flags"))}
    tags: list[str] = []
    if context.get("broad_source_known"):
        tags.append("broad_learner_known")
    elif context.get("broad_source_available"):
        tags.append("broad_learner_absent")
    if _as_sequence(row.get("learner_source")):
        tags.append("any_learner_source")
    if observed > expected:
        tags.append("too_hard")
    else:
        tags.append("too_easy")
    if (
        _component(components, "learner_core_gap_blend_confident") >= 0.18
        or _component(components, "learner_core_gap_zipf_confident") >= 0.18
    ):
        tags.append("learner_rescue_active")
    if _component(components, "cognate_rescue") >= 0.25:
        tags.append("cognate_rescue_active")
    if _component(components, "rare_cognate_tail_rescue") >= 0.05:
        tags.append("rare_cognate_tail_rescue")
    if _component(components, "wordfreq_source_rescue") >= 0.04:
        tags.append("wordfreq_rescue_available")
    if _component(components, "wordfreq_tail_rescue") >= 0.04:
        tags.append("wordfreq_tail_rescue_available")
    if _component(components, "wordfreq_source_caution") >= 0.04:
        tags.append("wordfreq_caution_available")
    if _component(components, "lexcom_learner_rescue") >= 0.04:
        tags.append("lexcom_rescue_available")
    if _component(components, "lexcom_learner_caution") >= 0.04:
        tags.append("lexcom_caution_available")
    if (
        _component(components, "gated_dict_marked_usage_risk") >= 0.30
        or _component(components, "dict_variant_risk") >= 0.20
        or _component(components, "tail_dict_ambiguity") >= 0.20
    ):
        tags.append("dictionary_marked_or_variant")
    if (
        _component(components, "pos_function_risk") >= 0.50
        or _component(components, "pos_other_risk") >= 0.50
    ):
        tags.append("function_or_other_pos")
    if _component(components, "unsupported_ease65") >= 0.05:
        tags.append("unsupported_ease_signal")
    if _component(components, "unsupported_ease_marked") >= 0.05:
        tags.append("unsupported_ease_marked")
    if _component(components, "unsupported_ease_usage") >= 0.05:
        tags.append("unsupported_ease_usage")
    if _component(components, "unsupported_ease_structural") >= 0.05:
        tags.append("unsupported_ease_structural")
    if "marked_rare_or_regional" in review_flags:
        tags.append("review_marked_rare_or_regional")
    if "domain_or_register_specific" in review_flags:
        tags.append("review_domain_or_register_specific")
    if "cognate_easy_for_english_speaker" in review_flags:
        tags.append("review_cognate_easy_for_english_speaker")
    if "foreign_or_borrowed_form" in review_flags:
        tags.append("review_foreign_or_borrowed_form")
    if "grammar_or_function_word" in review_flags:
        tags.append("review_grammar_or_function_word")
    if _safe_float(row.get("spalex_rank")) is None:
        tags.append("no_spalex_rank")
    return tags


def _problem_routes(
    *,
    row: Mapping[str, object],
    label: Mapping[str, object],
    expected: float,
    observed: float,
    abs_error: float,
    error_threshold: float,
) -> list[str]:
    components = _as_mapping(row.get("components"))
    context = _as_mapping(row.get("learner_source_context"))
    dictionary = _as_mapping(row.get("dictionary"))
    flags = {str(flag) for flag in _as_sequence(label.get("review_flags"))}
    marked_terms = {str(term).lower() for term in _as_sequence(dictionary.get("marked_terms"))}
    pos_bucket = str(row.get("pos_bucket") or "")
    translations = " ".join(str(item).lower() for item in _as_sequence(row.get("translations")))
    too_hard = observed > expected
    too_easy = observed < expected
    broad_absent = bool(context.get("broad_source_absent"))
    broad_known = bool(context.get("broad_source_known"))
    review_marked = "marked_rare_or_regional" in flags
    review_domain = "domain_or_register_specific" in flags
    review_cognate = "cognate_easy_for_english_speaker" in flags
    residual = abs_error >= error_threshold
    routes: list[str] = []
    if residual and too_hard and broad_absent:
        routes.append("source_void_too_hard")
    if residual and too_hard and _component(components, "wordfreq_tail_rescue") >= 0.04:
        routes.append("wordfreq_commonness_gap")
    if residual and too_hard and _component(components, "lexcom_learner_rescue") >= 0.04:
        routes.append("lexcom_learner_complexity_gap")
    if residual and too_easy and _component(components, "lexcom_learner_caution") >= 0.04:
        routes.append("lexcom_learner_complexity_caution")
    if (
        residual
        and too_hard
        and review_marked
        and expected <= 0.70
        and marked_terms & {"slang", "vulgar", "colloquial", "regional", "dialectal"}
    ):
        routes.append("spoken_regional_commonness_gap")
    if review_marked and (
        "vulgar" in marked_terms
        or any(term in translations for term in ("fuck", "asshole", "cunt", "vagina", "sex"))
    ):
        routes.append("vulgar_register_policy_split")
    if (
        residual
        and too_hard
        and (
            review_domain
            or (
                review_marked
                and pos_bucket == "noun"
                and (_safe_float(dictionary.get("entry_count")) or 0.0) == 0.0
            )
        )
    ):
        routes.append("domain_concrete_register_gap")
    if residual and too_hard and review_cognate:
        routes.append("transparent_cognate_morphology_gap")
    if (
        residual
        and too_easy
        and (
            broad_known
            or _component(components, "learner_core_gap_blend_confident") >= 0.18
            or _component(components, "cognate_rescue") >= 0.25
        )
    ):
        routes.append("learner_cognate_over_rescue")
    if review_marked and not residual:
        routes.append("marked_regional_counterexample_keep_current_shape")
    return routes


def _family_reports(
    residual_rows: Sequence[Mapping[str, object]],
    *,
    detail_limit: int,
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in residual_rows:
        for tag in _as_sequence(row.get("tags")):
            grouped[str(tag)].append(row)
    reports = []
    for family, rows in grouped.items():
        errors = [_safe_float(row.get("candidate_abs_error")) or 0.0 for row in rows]
        reports.append(
            {
                "family": family,
                "count": len(rows),
                "too_hard_count": sum(str(row.get("direction")) == "too_hard" for row in rows),
                "too_easy_count": sum(str(row.get("direction")) == "too_easy" for row in rows),
                "mean_abs_error": _round_float(sum(errors) / len(errors)) if errors else None,
                "examples": _largest_rows(
                    rows, sort_key="candidate_abs_error", detail_limit=detail_limit
                ),
            }
        )
    return sorted(
        reports,
        key=lambda item: (
            int(item.get("count") or 0),
            _safe_float(item.get("mean_abs_error")) or 0.0,
        ),
        reverse=True,
    )


def _route_reports(
    rows: Sequence[Mapping[str, object]],
    *,
    error_threshold: float,
    detail_limit: int,
) -> list[dict[str, object]]:
    descriptions = {
        "source_void_too_hard": (
            "Independent positive evidence; broad learner absence is not enough to distinguish useful tail words from obscure tail words."
        ),
        "spoken_regional_commonness_gap": (
            "Modern spoken/subtitle or region-aware frequency support, ideally gated by vulgar/register policy."
        ),
        "wordfreq_commonness_gap": (
            "Multi-source wordfreq evidence already says this tail row is more common than SPALEX implies; sweep a bounded rescue."
        ),
        "lexcom_learner_complexity_gap": (
            "Direct LexComSpaL2 learner-complexity evidence says this row is easier than the current model; sweep a bounded rescue."
        ),
        "lexcom_learner_complexity_caution": (
            "Direct LexComSpaL2 learner-complexity evidence says this row is harder than the current model; sweep a bounded caution."
        ),
        "vulgar_register_policy_split": (
            "Separate scalar difficulty from product admission/display policy for vulgar or sensitive words."
        ),
        "domain_concrete_register_gap": (
            "Domain, register, or concrete-noun commonness support; do not solve with a broad regional rescue."
        ),
        "transparent_cognate_morphology_gap": (
            "Stronger English-speaker transparency signal from cognates, prefixes, suffixes, or translation alignment."
        ),
        "learner_cognate_over_rescue": (
            "Dampener for short/polysemous/domain-specific rows where learner/cognate evidence over-lowers the score."
        ),
        "marked_regional_counterexample_keep_current_shape": (
            "Regression guard set: marked/regional rows that should stay roughly where the current model puts them."
        ),
    }
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        for route in _as_sequence(row.get("problem_routes")):
            grouped[str(route)].append(row)
    reports = []
    for route, route_rows in grouped.items():
        residuals = [
            row
            for row in route_rows
            if (_safe_float(row.get("candidate_abs_error")) or 0.0) >= error_threshold
        ]
        counterexamples = [
            row
            for row in route_rows
            if (_safe_float(row.get("candidate_abs_error")) or 0.0) < error_threshold
        ]
        reports.append(
            {
                "route": route,
                "row_count": len(route_rows),
                "residual_count": len(residuals),
                "counterexample_count": len(counterexamples),
                "too_hard_count": sum(
                    str(row.get("direction")) == "too_hard" for row in route_rows
                ),
                "too_easy_count": sum(
                    str(row.get("direction")) == "too_easy" for row in route_rows
                ),
                "recommended_next_signal": descriptions.get(route, ""),
                "residual_examples": _largest_rows(
                    residuals,
                    sort_key="candidate_abs_error",
                    detail_limit=detail_limit,
                ),
                "counterexamples": _largest_rows(
                    counterexamples,
                    sort_key="candidate_abs_error",
                    detail_limit=detail_limit,
                ),
            }
        )
    route_order = {
        "spoken_regional_commonness_gap": 0,
        "wordfreq_commonness_gap": 1,
        "lexcom_learner_complexity_gap": 2,
        "lexcom_learner_complexity_caution": 3,
        "vulgar_register_policy_split": 4,
        "domain_concrete_register_gap": 5,
        "transparent_cognate_morphology_gap": 6,
        "learner_cognate_over_rescue": 7,
        "source_void_too_hard": 8,
        "marked_regional_counterexample_keep_current_shape": 9,
    }
    return sorted(
        reports,
        key=lambda item: (
            route_order.get(str(item.get("route")), 99),
            -int(item.get("residual_count") or 0),
            -int(item.get("row_count") or 0),
        ),
    )


def _change_reports(
    rows: Sequence[Mapping[str, object]],
    *,
    change_threshold: float,
    detail_limit: int,
) -> dict[str, object]:
    improvements = [
        row
        for row in rows
        if (_safe_float(row.get("error_delta_vs_baseline")) or 0.0) <= -change_threshold
    ]
    regressions = [
        row
        for row in rows
        if (_safe_float(row.get("error_delta_vs_baseline")) or 0.0) >= change_threshold
    ]
    return {
        "change_threshold": _round_float(change_threshold),
        "improvement_count": len(improvements),
        "regression_count": len(regressions),
        "largest_improvements": sorted(
            improvements,
            key=lambda row: _safe_float(row.get("error_delta_vs_baseline")) or 0.0,
        )[:detail_limit],
        "largest_regressions": sorted(
            regressions,
            key=lambda row: _safe_float(row.get("error_delta_vs_baseline")) or 0.0,
            reverse=True,
        )[:detail_limit],
    }


def _metrics(rows: Sequence[Mapping[str, object]], *, score_key: str) -> dict[str, object]:
    expected = []
    observed = []
    bands = []
    labels = []
    expected_states = []
    observed_states = []
    for row in rows:
        expected_value = _safe_float(row.get("expected"))
        observed_value = _safe_float(row.get(score_key))
        if expected_value is None or observed_value is None:
            continue
        expected.append(expected_value)
        observed.append(observed_value)
        bands.append(str(row.get("expected_difficulty_band") or ""))
        labels.append(str(row.get("lemma") or ""))
        expected_states.append(str(row.get("expected_candidate_state") or ""))
        observed_states.append(PRIMARY_STATE)
    if not expected:
        return {"count": 0}
    metrics = _difficulty_metrics(
        expected_values=np.asarray(expected, dtype=np.float32),
        observed_values=np.asarray(observed, dtype=np.float32),
        expected_bands=bands,
        labels=labels,
        expected_candidate_states=np.asarray(expected_states, dtype="<U64"),
        observed_candidate_states=np.asarray(observed_states, dtype="<U64"),
    )
    scores = _as_mapping(metrics.get("scores"))
    summary = _summary_metrics(metrics)
    return {
        "count": len(expected),
        "balanced_score": scores.get("balanced_score"),
        "mae": summary.get("mae"),
        "bucket_accuracy": summary.get("bucket_accuracy"),
        "pairwise_accuracy": summary.get("pairwise_accuracy"),
        "high_tail_score": scores.get("high_tail_score"),
        "raw_scores": scores,
        "raw_metrics": summary,
    }


def _direction_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts = Counter(str(row.get("direction") or "") for row in rows)
    return {key: counts[key] for key in sorted(counts) if key}


def _largest_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    sort_key: str,
    detail_limit: int,
) -> list[dict[str, object]]:
    fields = (
        "split",
        "lemma",
        "expected",
        "candidate_score",
        "baseline_score",
        "candidate_abs_error",
        "baseline_abs_error",
        "score_delta_vs_baseline",
        "error_delta_vs_baseline",
        "direction",
        "spalex_rank",
        "pos",
        "pos_bucket",
        "tags",
        "salient_signals",
        "translations",
        "rationale",
    )
    selected = sorted(
        rows,
        key=lambda row: _safe_float(row.get(sort_key)) or 0.0,
        reverse=True,
    )[:detail_limit]
    return [{field: row.get(field) for field in fields if field in row} for row in selected]


def _salient_signals(components: Mapping[str, object]) -> list[dict[str, object]]:
    signal_order = (
        "zipf_base",
        "spalex_blend",
        "learner_core_confidence",
        "learner_core_gap_blend_confident",
        "learner_core_gap_zipf_confident",
        "cognate_rescue",
        "rare_cognate_tail_rescue",
        "wordfreq_commonness",
        "wordfreq_source_rescue",
        "wordfreq_tail_rescue",
        "wordfreq_regional_rescue",
        "wordfreq_source_caution",
        "wordfreq_tail_caution",
        "lexcom_complexity",
        "lexcom_learner_rescue",
        "lexcom_rescue_after020",
        "lexcom_rescue_after030",
        "lexcom_rescue_after040",
        "lexcom_tail_rescue",
        "lexcom_learner_caution",
        "lexcom_tail_caution",
        "learner_broad_absence_tail50",
        "learner_broad_absence_tail65",
        "learner_broad_absence_tail80",
        "positive_ease_support",
        "unsupported_ease50",
        "unsupported_ease65",
        "unsupported_ease_content",
        "unsupported_ease_marked",
        "unsupported_ease_usage",
        "unsupported_ease_structural",
        "unsupported_ease_floor040",
        "unsupported_ease_floor050",
        "unsupported_ease_content_floor050",
        "unsupported_ease_marked_floor060",
        "unsupported_ease_usage_floor060",
        "unsupported_ease_structural_floor060",
        "gated_dict_marked_usage_risk",
        "dict_region_tag_count_score",
        "dict_domain_topic_count_score",
        "dict_register_colloquial_score",
        "dict_register_sensitive_score",
        "dict_register_rare_dated_score",
        "regional_colloquial_gate",
        "tail_domain_specificity",
        "tail_rare_dated_register",
        "dict_variant_risk",
        "tail_dict_ambiguity",
        "pos_function_risk",
        "pos_other_risk",
        "admission_suitability_risk",
    )
    result = []
    for component in signal_order:
        value = _safe_float(components.get(component))
        if value is not None and abs(value) > 1e-6:
            result.append({"component": component, "value": _round_float(value)})
    return result


def _metric_row(label: str, row: Mapping[str, object]) -> str:
    return (
        f"| {label} | {row.get('count', '')} | {_fmt(row.get('balanced_score'))} | "
        f"{_fmt(row.get('mae'))} | {_fmt(row.get('bucket_accuracy'))} | "
        f"{_fmt(row.get('pairwise_accuracy'))} | {_fmt(row.get('high_tail_score'))} |"
    )


def _row_line(item: Mapping[str, object]) -> str:
    tags = ", ".join(f"`{_escape(tag)}`" for tag in _as_sequence(item.get("tags"))[:5])
    return (
        f"| {item.get('split')} | `{_escape(item.get('lemma'))}` | "
        f"{_fmt(item.get('expected'))} | {_fmt(item.get('candidate_score'))} | "
        f"{_fmt(item.get('baseline_score'))} | {_fmt(item.get('candidate_abs_error'))} | "
        f"{_fmt_signed(item.get('score_delta_vs_baseline'))} | {tags or '-'} |"
    )


def _component(components: Mapping[str, object], key: str) -> float:
    return _safe_float(components.get(key)) or 0.0


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    return _load_json(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _round_float(value: float | None, digits: int = 6) -> float | None:
    return round(float(value), digits) if value is not None and np.isfinite(value) else None


def _fmt(value: object) -> str:
    number = _safe_float(value)
    return "" if number is None else f"{number:.3f}"


def _fmt_signed(value: object) -> str:
    number = _safe_float(value)
    return "" if number is None else f"{number:+.3f}"


def _json_inline(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
