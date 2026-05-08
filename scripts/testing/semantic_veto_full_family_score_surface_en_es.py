#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_AUTHORING_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_manual_packet_authoring_en_es_latest.json"
)
DEFAULT_TFIDF_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_manual_sentence_veto_tfidf_en_es_latest.json"
)
DEFAULT_ST_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_manual_sentence_veto_st_en_es_latest.json"
)
DEFAULT_STAGE1_REFERENCE = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_scoring_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_score_surface_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_score_surface_en_es_latest.md"

SOURCE_BAND_ORDER = {
    "zipf_5_plus_very_common": 0,
    "zipf_4_to_5_common": 1,
    "zipf_3_to_4_mid": 2,
    "zipf_below_3_rare": 3,
    "missing": 4,
}
TARGET_BAND_ORDER = dict(SOURCE_BAND_ORDER)
CASE_TYPE_ORDER = {
    "positive_active": 0,
    "shadow_negative": 1,
    "phrase_no_winner": 2,
    "missing": 3,
}
SCORER_ORDER = {
    "tfidf_cosine": 0,
    "sentence_transformer_cosine": 1,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize the full-family representative draft manual packet by scorer, "
            "source band, target band, polysemy, POS shape, and case type. "
            "This report changes no runtime policy."
        )
    )
    parser.add_argument("--authoring-json", type=Path, default=DEFAULT_AUTHORING_JSON)
    parser.add_argument("--tfidf-report-json", type=Path, default=DEFAULT_TFIDF_REPORT)
    parser.add_argument("--sentence-transformer-report-json", type=Path, default=DEFAULT_ST_REPORT)
    parser.add_argument("--stage1-reference-json", type=Path, default=DEFAULT_STAGE1_REFERENCE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_full_family_score_surface_report(
        authoring_payload=_load_json(args.authoring_json),
        score_sources=[
            {
                "source_id": "tfidf_cosine",
                "path": args.tfidf_report_json,
                "report": _load_json(args.tfidf_report_json),
            },
            {
                "source_id": "sentence_transformer_cosine",
                "path": args.sentence_transformer_report_json,
                "report": _load_json(args.sentence_transformer_report_json),
            },
        ],
        authoring_path=args.authoring_json,
        stage1_reference=_load_optional_json(args.stage1_reference_json),
        stage1_reference_path=args.stage1_reference_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_full_family_score_surface_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_full_family_score_surface_report(
    *,
    authoring_payload: Mapping[str, object],
    score_sources: Sequence[Mapping[str, object]],
    authoring_path: Path | None = None,
    stage1_reference: Mapping[str, object] | None = None,
    stage1_reference_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()

    rows: list[dict[str, object]] = []
    score_source_summaries = []
    issues: list[str] = []
    for source in score_sources:
        source_id = str(source.get("source_id") or "").strip()
        report = _as_mapping(source.get("report"))
        source_path = source.get("path") if isinstance(source.get("path"), Path) else None
        source_rows = _score_rows(report=report, source_id=source_id, source_path=source_path)
        rows.extend(source_rows)
        config = _as_mapping(report.get("config"))
        score_source_summaries.append(
            {
                "source_id": source_id,
                "path": _repo_path(source_path),
                "scorer_id": str(config.get("scorer_id") or source_id),
                "case_rows": len(source_rows),
                "report_status": str(report.get("status") or ""),
            }
        )
        if not source_rows:
            issues.append(f"no_rows_for_score_source:{source_id}")

    if not rows:
        issues.append("no_score_rows_available")

    authoring_summary = _as_mapping(authoring_payload.get("summary"))
    dataset_family_count = _first_int(
        authoring_summary,
        ("dataset_family_count", "repaired_family_count", "trusted_family_count"),
    )
    dataset_case_count = _first_int(
        authoring_summary,
        ("dataset_case_count", "repaired_case_count", "trusted_case_count"),
    )
    review_state = (
        str(authoring_summary.get("draft_review_state") or "")
        or str(authoring_summary.get("manual_review_state") or "")
        or str(authoring_payload.get("manual_review_state") or "")
    )
    row_scope = _row_scope(authoring_payload)
    breakdowns = {
        "scorer": _breakdown(rows, ("scorer_id",)),
        "scorer_x_source_band": _breakdown(rows, ("scorer_id", "source_zipf_band_en")),
        "scorer_x_target_band": _breakdown(rows, ("scorer_id", "target_zipf_band_es")),
        "scorer_x_polysemy": _breakdown(rows, ("scorer_id", "polysemy_band")),
        "scorer_x_pos_shape": _breakdown(rows, ("scorer_id", "pos_shape")),
        "scorer_x_case_type": _breakdown(rows, ("scorer_id", "manual_case_type")),
        "scorer_x_source_band_x_case_type": _breakdown(
            rows, ("scorer_id", "source_zipf_band_en", "manual_case_type")
        ),
        "scorer_x_source_band_x_polysemy": _breakdown(
            rows, ("scorer_id", "source_zipf_band_en", "polysemy_band")
        ),
    }
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_score_surface_established"
            if not issues
            else "full_family_score_surface_incomplete"
        ),
        "generated_at": generated_at,
        "pair": str(authoring_payload.get("pair") or "en-es"),
        "inputs": {
            "authoring_path": _repo_path(authoring_path),
            "score_sources": score_source_summaries,
            "stage1_reference_path": _repo_path(stage1_reference_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "row_scope": row_scope,
            "comparison_boundary": (
                "Stage 1 reference is shown only for orientation because it uses a "
                "different dataset mix and current-policy phrase/rescue settings."
            ),
            "promotion_boundary": (
                "approved_for_exploratory_sweeps_not_locked_eval_or_runtime_promotion"
                if row_scope == "user_approved_repaired_full_candidate"
                else "not_locked_eval_and_not_runtime_promotion_evidence"
            ),
        },
        "summary": {
            "issues": issues,
            "authoring_decision": str(authoring_payload.get("decision") or ""),
            "dataset_family_count": dataset_family_count,
            "dataset_case_count": dataset_case_count,
            "review_state": review_state,
            "source_band_case_counts": dict(
                sorted(_as_mapping(authoring_summary.get("source_band_case_counts")).items())
            ),
            "case_type_counts": dict(
                sorted(_as_mapping(authoring_summary.get("case_type_counts")).items())
            ),
            "overall_by_scorer": breakdowns["scorer"],
            "stage1_reference": _stage1_reference_summary(
                stage1_reference, path=stage1_reference_path
            ),
        },
        "breakdowns": breakdowns,
        "failure_concentration": _failure_concentration(rows),
        "row_results": rows,
        "limitations": [
            "approved_rows_are_still_not_final_locked_eval",
            "tfidf_score_can_be_optimistic_under_template_and_definition_overlap",
            "sentence_transformer_phrase_no_winner_failures_are_diagnostic_until_locked_eval",
            "source_band_curves_are_directional_not_causal_on_this_packet",
            "runtime_policy_remains_unchanged",
        ],
        "next_steps": [
            "Review the high-failure source-band and case-type cells before interpreting the curve.",
            "Rerun formula and boundary sweeps on this approved repaired denominator.",
            "Use the resulting ranking only for LLM evidence allocation until locked-eval confirms it.",
        ],
    }


def render_full_family_score_surface_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    breakdowns = _as_mapping(report.get("breakdowns"))
    lines = [
        "# en-es Semantic Veto Full-Family Score Surface",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Families: `{summary.get('dataset_family_count', 0)}`",
        f"- Cases: `{summary.get('dataset_case_count', 0)}`",
        f"- Review state: `{summary.get('review_state', '')}`",
        "",
        "## Methodology",
        "",
        "This report summarizes the full-family packet by scorer and by measurable "
        "source/target features. It does not change runtime policy and it does not "
        "promote these rows as locked eval.",
        "",
        "## Overall By Scorer",
        "",
        _metrics_table(summary.get("overall_by_scorer")),
        "",
        "## Source Band",
        "",
        _metrics_table(breakdowns.get("scorer_x_source_band")),
        "",
        "## Case Type",
        "",
        _metrics_table(breakdowns.get("scorer_x_case_type")),
        "",
        "## Source Band By Case Type",
        "",
        _metrics_table(breakdowns.get("scorer_x_source_band_x_case_type")),
        "",
        "## Target Band",
        "",
        _metrics_table(breakdowns.get("scorer_x_target_band")),
        "",
        "## Polysemy",
        "",
        _metrics_table(breakdowns.get("scorer_x_polysemy")),
        "",
        "## POS Shape",
        "",
        _metrics_table(breakdowns.get("scorer_x_pos_shape")),
        "",
        "## Prior Reference",
        "",
        _prior_reference_table(summary.get("stage1_reference")),
        "",
        "## Failure Concentration",
        "",
        _failure_table(report.get("failure_concentration")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _score_rows(
    *,
    report: Mapping[str, object],
    source_id: str,
    source_path: Path | None,
) -> list[dict[str, object]]:
    config = _as_mapping(report.get("config"))
    scorer_id = str(config.get("scorer_id") or source_id).strip()
    normalized: list[dict[str, object]] = []
    for row in _mapping_rows(report.get("row_results")):
        dims = _normalize_slice_dimensions(row.get("slice_dimensions"))
        gold_decision = _decision(row.get("gold_decision"))
        predicted_decision = _decision(row.get("predicted_decision"))
        manual_case_type = _first_dim(dims, "manual_case_type") or _case_type_from_row(row)
        gold_winner_type = str(row.get("gold_winner_type") or "")
        normalized.append(
            {
                "case_id": str(row.get("case_id") or ""),
                "family_id": str(row.get("family_id") or ""),
                "trigger": str(row.get("trigger") or row.get("source_phrase") or ""),
                "sentence": str(row.get("sentence") or ""),
                "source_id": source_id,
                "source_report": _repo_path(source_path),
                "scorer_id": scorer_id,
                "gold_decision": gold_decision,
                "predicted_decision": predicted_decision,
                "decision_correct": gold_decision == predicted_decision,
                "gold_winner_type": gold_winner_type,
                "predicted_winner_type": str(row.get("predicted_winner_type") or ""),
                "manual_case_type": manual_case_type,
                "source_zipf_band_en": _first_dim(dims, "source_zipf_band_en") or "missing",
                "target_zipf_band_es": _first_dim(dims, "target_zipf_band_es") or "missing",
                "polysemy_band": _first_dim(dims, "polysemy_band") or "missing",
                "pos_shape": _first_dim(dims, "pos_shape") or "missing",
                "shadow_contract": _first_dim(dims, "shadow_contract") or "missing",
                "manual_review_state": _first_dim(dims, "manual_review_state") or "missing",
                "active_score": _round4(_optional_float(row.get("active_score"))),
                "strongest_shadow_score": _round4(
                    _optional_float(row.get("strongest_shadow_score"))
                ),
                "margin": _round4(_optional_float(row.get("margin"))),
                "error_type": _error_type(gold_decision, predicted_decision),
            }
        )
    return normalized


def _breakdown(
    rows: Sequence[Mapping[str, object]], dimensions: Sequence[str]
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(dimension) or "missing") for dimension in dimensions)
        grouped[key].append(row)
    output = []
    for key, bucket_rows in grouped.items():
        metrics = _metrics(bucket_rows)
        for dimension, value in zip(dimensions, key, strict=True):
            metrics[dimension] = value
        metrics["slice_id"] = "::".join(
            f"{dimension}={value}" for dimension, value in zip(dimensions, key, strict=True)
        )
        output.append(metrics)
    return sorted(output, key=_breakdown_sort_key)


def _metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    cases = len(rows)
    gold_replace = sum(1 for row in rows if row.get("gold_decision") == "replace")
    gold_abstain = sum(1 for row in rows if row.get("gold_decision") == "abstain")
    true_replace = sum(
        1
        for row in rows
        if row.get("gold_decision") == "replace" and row.get("predicted_decision") == "replace"
    )
    true_abstain = sum(
        1
        for row in rows
        if row.get("gold_decision") == "abstain" and row.get("predicted_decision") == "abstain"
    )
    false_abstain = sum(
        1
        for row in rows
        if row.get("gold_decision") == "replace" and row.get("predicted_decision") == "abstain"
    )
    harmful_replace = sum(
        1
        for row in rows
        if row.get("gold_decision") == "abstain" and row.get("predicted_decision") == "replace"
    )
    positive_active = [row for row in rows if row.get("manual_case_type") == "positive_active"]
    shadow_negative = [row for row in rows if row.get("manual_case_type") == "shadow_negative"]
    phrase_no_winner = [row for row in rows if row.get("manual_case_type") == "phrase_no_winner"]
    return {
        "cases": cases,
        "gold_replace_cases": gold_replace,
        "gold_abstain_cases": gold_abstain,
        "decision_accuracy": _rate(true_replace + true_abstain, cases),
        "positive_allow_rate": _rate(
            sum(1 for row in positive_active if row.get("predicted_decision") == "replace"),
            len(positive_active),
        ),
        "shadow_negative_abstain_rate": _rate(
            sum(1 for row in shadow_negative if row.get("predicted_decision") == "abstain"),
            len(shadow_negative),
        ),
        "phrase_no_winner_abstain_rate": _rate(
            sum(1 for row in phrase_no_winner if row.get("predicted_decision") == "abstain"),
            len(phrase_no_winner),
        ),
        "replace_recall": _rate(true_replace, gold_replace),
        "negative_abstain_rate": _rate(true_abstain, gold_abstain),
        "harmful_replace_rate": _rate(harmful_replace, gold_abstain),
        "false_abstain_rate": _rate(false_abstain, gold_replace),
        "harmful_replace_count": harmful_replace,
        "false_abstain_count": false_abstain,
        "positive_active_count": len(positive_active),
        "shadow_negative_count": len(shadow_negative),
        "phrase_no_winner_count": len(phrase_no_winner),
    }


def _failure_concentration(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    dimensions = (
        "source_zipf_band_en",
        "target_zipf_band_es",
        "polysemy_band",
        "pos_shape",
        "manual_case_type",
        "shadow_contract",
    )
    rows_by_scorer = defaultdict(list)
    for row in rows:
        rows_by_scorer[str(row.get("scorer_id") or "missing")].append(row)
    concentration = []
    for scorer_id, scorer_rows in rows_by_scorer.items():
        for dimension in dimensions:
            for metric in _breakdown(scorer_rows, (dimension,)):
                errors = int(metric["harmful_replace_count"]) + int(metric["false_abstain_count"])
                if errors <= 0:
                    continue
                concentration.append(
                    {
                        "scorer_id": scorer_id,
                        "dimension": dimension,
                        "value": str(metric.get(dimension) or "missing"),
                        "cases": int(metric["cases"]),
                        "error_count": errors,
                        "error_rate": _rate(errors, int(metric["cases"])),
                        "harmful_replace_count": int(metric["harmful_replace_count"]),
                        "false_abstain_count": int(metric["false_abstain_count"]),
                    }
                )
    return sorted(
        concentration,
        key=lambda row: (
            -float(row.get("error_count") or 0),
            -float(row.get("error_rate") or 0),
            _scorer_sort(str(row.get("scorer_id") or "")),
            str(row.get("dimension") or ""),
            str(row.get("value") or ""),
        ),
    )[:30]


def _stage1_reference_summary(
    stage1_reference: Mapping[str, object] | None, *, path: Path | None
) -> dict[str, object]:
    if not stage1_reference:
        return {
            "available": False,
            "path": _repo_path(path),
        }
    summary = _as_mapping(stage1_reference.get("summary"))
    config = _as_mapping(stage1_reference.get("config"))
    return {
        "available": True,
        "path": _repo_path(path),
        "decision": str(stage1_reference.get("decision") or ""),
        "dataset_path": str(stage1_reference.get("dataset_path") or ""),
        "scorer_id": str(config.get("scorer_id") or ""),
        "phrase_control_mode": str(config.get("phrase_control_mode") or ""),
        "active_rescue_mode": str(config.get("active_rescue_mode") or ""),
        "cases_total": int(summary.get("cases_total") or 0),
        "decision_accuracy": _optional_float(summary.get("decision_accuracy")),
        "replace_recall": _optional_float(summary.get("replace_recall")),
        "harmful_replace_rate": _optional_float(summary.get("harmful_replace_rate")),
        "false_abstain_rate": _optional_float(summary.get("false_abstain_rate")),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "comparison_note": "orientation_only_different_dataset_and_policy_modes",
    }


def _first_int(summary: Mapping[str, object], keys: Sequence[str]) -> int:
    for key in keys:
        value = summary.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _row_scope(authoring_payload: Mapping[str, object]) -> str:
    decision = str(authoring_payload.get("decision") or "")
    manual_review_state = str(authoring_payload.get("manual_review_state") or "")
    if (
        decision == "full_family_repair_pool_user_approved_for_exploratory_sweeps"
        or manual_review_state == "approved_by_user"
    ):
        return "user_approved_repaired_full_candidate"
    return "agent_draft_human_review_pending_full_family_representative_packet"


def _metrics_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No rows._"
    dimension_keys = [
        key
        for key in (
            "scorer_id",
            "source_zipf_band_en",
            "target_zipf_band_es",
            "polysemy_band",
            "pos_shape",
            "manual_case_type",
        )
        if any(key in row for row in rows)
    ]
    headers = [
        *dimension_keys,
        "cases",
        "decision",
        "positive allow",
        "shadow abstain",
        "phrase abstain",
        "harmful",
        "false abstain",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [
            *[str(row.get(key) or "") for key in dimension_keys],
            str(row.get("cases") or 0),
            _format_percent(row.get("decision_accuracy")),
            _format_percent(row.get("positive_allow_rate")),
            _format_percent(row.get("shadow_negative_abstain_rate")),
            _format_percent(row.get("phrase_no_winner_abstain_rate")),
            f"{_format_percent(row.get('harmful_replace_rate'))} ({row.get('harmful_replace_count', 0)})",
            f"{_format_percent(row.get('false_abstain_rate'))} ({row.get('false_abstain_count', 0)})",
        ]
        lines.append("| " + " | ".join(_escape_md(value) for value in values) + " |")
    return "\n".join(lines)


def _prior_reference_table(reference_obj: object) -> str:
    reference = _as_mapping(reference_obj)
    if not bool(reference.get("available")):
        return "_No prior reference report found._"
    headers = [
        "scope",
        "cases",
        "scorer",
        "phrase mode",
        "rescue mode",
        "decision",
        "positive recall",
        "harmful",
        "false abstain",
    ]
    values = [
        "stage1_representative_reference",
        str(reference.get("cases_total") or 0),
        str(reference.get("scorer_id") or ""),
        str(reference.get("phrase_control_mode") or ""),
        str(reference.get("active_rescue_mode") or ""),
        _format_percent(reference.get("decision_accuracy")),
        _format_percent(reference.get("replace_recall")),
        f"{_format_percent(reference.get('harmful_replace_rate'))} ({reference.get('harmful_replace_count', 0)})",
        f"{_format_percent(reference.get('false_abstain_rate'))} ({reference.get('false_abstain_count', 0)})",
    ]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            "| " + " | ".join(_escape_md(value) for value in values) + " |",
            "",
            "`stage1_representative_reference` is orientation only; it uses a different "
            "dataset mix and current-policy phrase/rescue settings.",
        ]
    )


def _failure_table(rows_obj: object) -> str:
    rows = _mapping_rows(rows_obj)
    if not rows:
        return "_No failures._"
    headers = [
        "scorer",
        "dimension",
        "value",
        "cases",
        "errors",
        "error rate",
        "harmful",
        "false abstain",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [
            str(row.get("scorer_id") or ""),
            str(row.get("dimension") or ""),
            str(row.get("value") or ""),
            str(row.get("cases") or 0),
            str(row.get("error_count") or 0),
            _format_percent(row.get("error_rate")),
            str(row.get("harmful_replace_count") or 0),
            str(row.get("false_abstain_count") or 0),
        ]
        lines.append("| " + " | ".join(_escape_md(value) for value in values) + " |")
    return "\n".join(lines)


def _breakdown_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _scorer_sort(str(row.get("scorer_id") or "")),
        SOURCE_BAND_ORDER.get(str(row.get("source_zipf_band_en") or ""), 99),
        TARGET_BAND_ORDER.get(str(row.get("target_zipf_band_es") or ""), 99),
        CASE_TYPE_ORDER.get(str(row.get("manual_case_type") or ""), 99),
        str(row.get("polysemy_band") or ""),
        str(row.get("pos_shape") or ""),
        str(row.get("slice_id") or ""),
    )


def _case_type_from_row(row: Mapping[str, object]) -> str:
    winner_type = str(row.get("gold_winner_type") or "")
    if winner_type == "active":
        return "positive_active"
    if winner_type == "shadow":
        return "shadow_negative"
    if winner_type == "none":
        return "phrase_no_winner"
    return "missing"


def _error_type(gold: str, predicted: str) -> str:
    if gold == "replace" and predicted == "abstain":
        return "false_abstain"
    if gold == "abstain" and predicted == "replace":
        return "harmful_replace"
    return "correct"


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for key, raw in _as_mapping(value).items():
        output[str(key)] = [str(item) for item in _sequence(raw) if str(item)]
    return output


def _first_dim(dimensions: Mapping[str, Sequence[str]], key: str) -> str:
    values = dimensions.get(key) or []
    return str(values[0]) if values else ""


def _decision(value: object) -> str:
    text = str(value or "").strip()
    if text in {"replace", "abstain"}:
        return text
    return ""


def _scorer_sort(value: str) -> int:
    return SCORER_ORDER.get(value, 99)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_percent(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.1f}%"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return [value]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
