#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_trusted_seed_v2_band_performance_rendering import (
    render_trusted_seed_v2_band_performance_markdown as render_trusted_seed_v2_band_performance_markdown,
)
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_TFIDF_REPORT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_full_family_trusted_eval_seed_v2_sentence_veto_tfidf_en_es_latest.json"
)
DEFAULT_ST_REPORT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_full_family_trusted_eval_seed_v2_sentence_veto_st_en_es_latest.json"
)
DEFAULT_PRIOR_SURFACE = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_score_surface_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_trusted_seed_v2_band_performance_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_trusted_seed_v2_band_performance_en_es_latest.md"
)

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
            "Slice the approved trusted eval seed v2 by frequency band, case type, "
            "review source, and scorer. This is a diagnostic report only."
        )
    )
    parser.add_argument("--tfidf-report-json", type=Path, default=DEFAULT_TFIDF_REPORT)
    parser.add_argument("--sentence-transformer-report-json", type=Path, default=DEFAULT_ST_REPORT)
    parser.add_argument("--prior-surface-json", type=Path, default=DEFAULT_PRIOR_SURFACE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    prior_surface = _load_optional_json(args.prior_surface_json)
    report = build_trusted_seed_v2_band_performance_report(
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
        prior_surface=prior_surface,
        prior_surface_path=args.prior_surface_json if prior_surface else None,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_trusted_seed_v2_band_performance_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_trusted_seed_v2_band_performance_report(
    *,
    score_sources: Sequence[Mapping[str, object]],
    prior_surface: Mapping[str, object] | None = None,
    prior_surface_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    rows: list[dict[str, object]] = []
    issues: list[str] = []
    source_summaries = []
    dataset_ids = set()
    for source in score_sources:
        source_id = str(source.get("source_id") or "").strip()
        source_path = source.get("path") if isinstance(source.get("path"), Path) else None
        report = _as_mapping(source.get("report"))
        source_rows = _score_rows(report=report, source_id=source_id, source_path=source_path)
        rows.extend(source_rows)
        dataset_ids.add(str(report.get("dataset_id") or ""))
        config = _as_mapping(report.get("config"))
        summary = _as_mapping(report.get("summary"))
        source_summaries.append(
            {
                "source_id": source_id,
                "path": _repo_path(source_path),
                "scorer_id": str(config.get("scorer_id") or source_id),
                "case_rows": len(source_rows),
                "report_status": str(report.get("status") or ""),
                "decision_accuracy": _optional_float(summary.get("decision_accuracy")),
                "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
                "false_abstain_count": int(summary.get("false_abstain_count") or 0),
            }
        )
        if not source_rows:
            issues.append(f"no_rows_for_score_source:{source_id}")
    if not rows:
        issues.append("no_score_rows_available")
    if len({row["case_id"] for row in rows}) * max(len(score_sources), 1) != len(rows):
        issues.append("case_rows_not_balanced_across_scorers")

    breakdowns = {
        "scorer": _breakdown(rows, ("scorer_id",)),
        "scorer_x_source_band": _breakdown(rows, ("scorer_id", "source_zipf_band_en")),
        "scorer_x_source_band_x_case_type": _breakdown(
            rows, ("scorer_id", "source_zipf_band_en", "manual_case_type")
        ),
        "scorer_x_case_type": _breakdown(rows, ("scorer_id", "manual_case_type")),
        "scorer_x_target_band": _breakdown(rows, ("scorer_id", "target_zipf_band_es")),
        "scorer_x_polysemy": _breakdown(rows, ("scorer_id", "polysemy_band")),
        "scorer_x_pos_shape": _breakdown(rows, ("scorer_id", "pos_shape")),
        "scorer_x_approval": _breakdown(rows, ("scorer_id", "approval_id")),
        "scorer_x_trusted_seed_v2_status": _breakdown(
            rows, ("scorer_id", "trusted_seed_v2_status")
        ),
        "scorer_x_no_winner_subtype": _breakdown(rows, ("scorer_id", "no_winner_subtype")),
    }
    prior_comparison = _prior_comparison(
        current_overall=breakdowns["scorer"],
        current_source_band=breakdowns["scorer_x_source_band"],
        prior_surface=prior_surface,
        prior_surface_path=prior_surface_path,
    )
    sample_warnings = _sample_warnings(rows)
    return {
        "schema_version": 1,
        "pair": _pair_from_sources(score_sources),
        "status": "review" if issues else "ok",
        "decision": (
            "trusted_seed_v2_band_performance_established"
            if not issues
            else "trusted_seed_v2_band_performance_incomplete"
        ),
        "generated_at": generated_at,
        "inputs": {
            "score_sources": source_summaries,
            "prior_surface_path": _repo_path(prior_surface_path),
            "dataset_ids": sorted(dataset_id for dataset_id in dataset_ids if dataset_id),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_or_scorer_change": "none",
            "row_scope": "approved_trusted_eval_seed_v2",
            "primary_question": (
                "After repairing and approving the deferred rows, what do the "
                "current scorers do by source band, case type, and approval source?"
            ),
            "promotion_boundary": (
                "This is a trusted-seed diagnostic. It is stronger than the old "
                "draft score surface, but it is still small and not an untouched "
                "locked-eval split."
            ),
        },
        "summary": {
            "issues": issues,
            "case_count_per_scorer": _case_count_per_scorer(rows),
            "unique_case_count": len({row["case_id"] for row in rows}),
            "unique_family_count": len({row["family_id"] for row in rows}),
            "source_band_case_counts": _dimension_counts(rows, "source_zipf_band_en"),
            "case_type_counts": _dimension_counts(rows, "manual_case_type"),
            "approval_case_counts": _dimension_counts(rows, "approval_id"),
            "overall_by_scorer": breakdowns["scorer"],
            "sample_warnings": sample_warnings,
        },
        "breakdowns": breakdowns,
        "failure_concentration": _failure_concentration(rows),
        "prior_comparison": prior_comparison,
        "answer_to_band_question": _answer_to_band_question(
            breakdowns=breakdowns,
            sample_warnings=sample_warnings,
            prior_comparison=prior_comparison,
        ),
        "row_results": rows,
        "limitations": [
            "trusted_seed_v2_has_only_42_rows",
            "per_band_positive_shadow_phrase_counts_are_small",
            "not_an_untouched_locked_eval_split",
            "source_zipf_band_is_not_a_full_srs_or_browser_distribution",
            "sentence_transformer_phrase_no_winner_leakage_requires_separate_guard_or_policy_tests",
        ],
        "next_steps": [
            "Use this trusted v2 report as the first reviewed band denominator.",
            "Run scorer bakeoffs or threshold sweeps on this seed as diagnostics only.",
            "Expand representative locked data before making a production acceptance claim.",
        ],
    }


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
        normalized.append(
            {
                "case_id": str(row.get("case_id") or ""),
                "family_id": str(row.get("family_id") or ""),
                "trigger": str(row.get("trigger") or row.get("source_phrase") or ""),
                "source_id": source_id,
                "source_report": _repo_path(source_path),
                "scorer_id": scorer_id,
                "gold_decision": gold_decision,
                "predicted_decision": predicted_decision,
                "gold_winner_type": str(row.get("gold_winner_type") or ""),
                "predicted_winner_type": str(row.get("predicted_winner_type") or ""),
                "manual_case_type": manual_case_type,
                "source_zipf_band_en": _first_dim(dims, "source_zipf_band_en") or "missing",
                "target_zipf_band_es": _first_dim(dims, "target_zipf_band_es") or "missing",
                "polysemy_band": _first_dim(dims, "polysemy_band") or "missing",
                "pos_shape": _first_dim(dims, "pos_shape") or "missing",
                "approval_id": _first_dim(dims, "approval_id")
                or str(row.get("approval_id") or "missing"),
                "trusted_seed_v2_status": _first_dim(dims, "trusted_seed_v2_status") or "missing",
                "family_repair_status": _first_dim(dims, "family_repair_status") or "missing",
                "no_winner_subtype": _first_dim(dims, "no_winner_subtype") or "missing",
                "context_source": _first_dim(dims, "context_source") or "missing",
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
    predicted_replace = sum(1 for row in rows if row.get("predicted_decision") == "replace")
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
        "predicted_replace_cases": predicted_replace,
        "decision_accuracy": _rate(true_replace + true_abstain, cases),
        "replace_precision": _rate(true_replace, predicted_replace),
        "replace_recall": _rate(true_replace, gold_replace),
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
        "negative_abstain_rate": _rate(true_abstain, gold_abstain),
        "harmful_replace_rate": _rate(harmful_replace, gold_abstain),
        "false_abstain_rate": _rate(false_abstain, gold_replace),
        "harmful_replace_count": harmful_replace,
        "false_abstain_count": false_abstain,
        "positive_active_count": len(positive_active),
        "shadow_negative_count": len(shadow_negative),
        "phrase_no_winner_count": len(phrase_no_winner),
    }


def _prior_comparison(
    *,
    current_overall: Sequence[Mapping[str, object]],
    current_source_band: Sequence[Mapping[str, object]],
    prior_surface: Mapping[str, object] | None,
    prior_surface_path: Path | None,
) -> dict[str, object]:
    if not prior_surface:
        return {
            "available": False,
            "path": _repo_path(prior_surface_path),
        }
    prior_breakdowns = _as_mapping(prior_surface.get("breakdowns"))
    prior_summary = _as_mapping(prior_surface.get("summary"))
    prior_overall = _mapping_rows(prior_summary.get("overall_by_scorer"))
    prior_source_band = _mapping_rows(prior_breakdowns.get("scorer_x_source_band"))
    return {
        "available": True,
        "path": _repo_path(prior_surface_path),
        "prior_row_scope": str(
            _as_mapping(prior_surface.get("methodology")).get("row_scope") or ""
        ),
        "prior_review_state": str(prior_summary.get("review_state") or ""),
        "overall_deltas": _metric_deltas(
            current_rows=current_overall,
            prior_rows=prior_overall,
            key_fields=("scorer_id",),
        ),
        "source_band_deltas": _metric_deltas(
            current_rows=current_source_band,
            prior_rows=prior_source_band,
            key_fields=("scorer_id", "source_zipf_band_en"),
        ),
        "comparison_boundary": (
            "The prior surface used a 206-row agent-draft packet. Deltas show how "
            "the trusted v2 denominator differs, not a clean algorithm regression."
        ),
    }


def _metric_deltas(
    *,
    current_rows: Sequence[Mapping[str, object]],
    prior_rows: Sequence[Mapping[str, object]],
    key_fields: Sequence[str],
) -> list[dict[str, object]]:
    prior_by_key = {_key(row, key_fields): row for row in prior_rows}
    output = []
    for current in current_rows:
        key = _key(current, key_fields)
        prior = prior_by_key.get(key)
        if prior is None:
            continue
        row = {field: str(current.get(field) or "") for field in key_fields}
        row.update(
            {
                "current_cases": int(current.get("cases") or 0),
                "prior_cases": int(prior.get("cases") or 0),
                "decision_accuracy_delta": _delta(current, prior, "decision_accuracy"),
                "positive_allow_rate_delta": _delta(current, prior, "positive_allow_rate"),
                "shadow_negative_abstain_rate_delta": _delta(
                    current, prior, "shadow_negative_abstain_rate"
                ),
                "phrase_no_winner_abstain_rate_delta": _delta(
                    current, prior, "phrase_no_winner_abstain_rate"
                ),
                "harmful_replace_count_delta": int(current.get("harmful_replace_count") or 0)
                - int(prior.get("harmful_replace_count") or 0),
                "false_abstain_count_delta": int(current.get("false_abstain_count") or 0)
                - int(prior.get("false_abstain_count") or 0),
            }
        )
        output.append(row)
    return sorted(output, key=_comparison_sort_key)


def _failure_concentration(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    dimensions = (
        "source_zipf_band_en",
        "manual_case_type",
        "approval_id",
        "trusted_seed_v2_status",
        "no_winner_subtype",
        "family_repair_status",
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


def _answer_to_band_question(
    *,
    breakdowns: Mapping[str, object],
    sample_warnings: Sequence[str],
    prior_comparison: Mapping[str, object],
) -> dict[str, object]:
    st_case_rows = [
        row
        for row in _mapping_rows(breakdowns.get("scorer_x_case_type"))
        if row.get("scorer_id") == "sentence_transformer_cosine"
    ]
    phrase_row = next(
        (row for row in st_case_rows if row.get("manual_case_type") == "phrase_no_winner"),
        {},
    )
    tfidf_case_rows = [
        row
        for row in _mapping_rows(breakdowns.get("scorer_x_case_type"))
        if row.get("scorer_id") == "tfidf_cosine"
    ]
    positive_tfidf = next(
        (row for row in tfidf_case_rows if row.get("manual_case_type") == "positive_active"),
        {},
    )
    claim_strength = "diagnostic_trusted_seed_only"
    if sample_warnings:
        claim_strength = "directional_underpowered"
    return {
        "claim_strength": claim_strength,
        "main_signal": (
            "The trusted v2 bands preserve the broad scorer tradeoff: TF-IDF is "
            f"safe but allows only {_format_percent(positive_tfidf.get('positive_allow_rate'))} "
            "of positives, while sentence-transformer recovers active/shadow rows "
            f"but abstains on only {_format_percent(phrase_row.get('phrase_no_winner_abstain_rate'))} "
            "of phrase/no-winner rows."
        ),
        "main_caution": (
            "Band-level rows are now trusted, but the seed has only 42 cases and "
            "several source-band x case-type cells are tiny."
        ),
        "prior_comparison_available": bool(prior_comparison.get("available")),
    }


def _sample_warnings(rows: Sequence[Mapping[str, object]]) -> list[str]:
    warnings: list[str] = []
    unique_rows = _dedupe_case_rows(rows)
    source_counts = _dimension_counts(unique_rows, "source_zipf_band_en")
    for band, count in source_counts.items():
        if count < 10:
            warnings.append(f"small_source_band:{band}:{count}")
    cross_counts = defaultdict(int)
    for row in unique_rows:
        cross_counts[
            (
                str(row.get("source_zipf_band_en") or "missing"),
                str(row.get("manual_case_type") or "missing"),
            )
        ] += 1
    for (band, case_type), count in sorted(cross_counts.items()):
        if count < 3:
            warnings.append(f"tiny_source_band_case_type_cell:{band}:{case_type}:{count}")
    return warnings


def _breakdown_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _scorer_sort(str(row.get("scorer_id") or "")),
        SOURCE_BAND_ORDER.get(str(row.get("source_zipf_band_en") or ""), 99),
        TARGET_BAND_ORDER.get(str(row.get("target_zipf_band_es") or ""), 99),
        CASE_TYPE_ORDER.get(str(row.get("manual_case_type") or ""), 99),
        str(row.get("approval_id") or ""),
        str(row.get("trusted_seed_v2_status") or ""),
        str(row.get("polysemy_band") or ""),
        str(row.get("pos_shape") or ""),
        str(row.get("slice_id") or ""),
    )


def _comparison_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _scorer_sort(str(row.get("scorer_id") or "")),
        SOURCE_BAND_ORDER.get(str(row.get("source_zipf_band_en") or ""), 99),
        str(row.get("source_zipf_band_en") or ""),
    )


def _pair_from_sources(score_sources: Sequence[Mapping[str, object]]) -> str:
    for source in score_sources:
        pair = str(_as_mapping(source.get("report")).get("pair") or "")
        if pair:
            return pair
    return "en-es"


def _case_count_per_scorer(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts = defaultdict(set)
    for row in rows:
        counts[str(row.get("scorer_id") or "missing")].add(str(row.get("case_id") or ""))
    return {key: len(value) for key, value in sorted(counts.items())}


def _dimension_counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts = defaultdict(set)
    for row in rows:
        counts[str(row.get(key) or "missing")].add(str(row.get("case_id") or ""))
    return {name: len(case_ids) for name, case_ids in sorted(counts.items())}


def _dedupe_case_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    by_case = {}
    for row in rows:
        by_case.setdefault(str(row.get("case_id") or ""), row)
    return list(by_case.values())


def _key(row: Mapping[str, object], fields: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(row.get(field) or "") for field in fields)


def _delta(current: Mapping[str, object], prior: Mapping[str, object], key: str) -> float | None:
    current_value = _optional_float(current.get(key))
    prior_value = _optional_float(prior.get(key))
    if current_value is None or prior_value is None:
        return None
    return current_value - prior_value


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


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
