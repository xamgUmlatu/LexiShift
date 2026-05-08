#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _utility_weights,
    score_product_outcome_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_POLICY = TEST_INPUTS_ROOT / "semantic_veto_product_quality_policy_en_es.json"
DEFAULT_DIFFICULTY_STRATIFICATION = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_band_performance_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_band_performance_en_es_latest.md"
)
DEFAULT_REPRESENTATIVE_LANE_ID = "sampling_stage1_representative_proxy"

SOURCE_RANK_ORDER = ("1-500", "501-1000", "1001-2000", "2001-5000", ">5000", "missing")
SOURCE_ZIPF_ORDER = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)
GOLD_WINNER_ORDER = ("active", "shadow", "none", "missing")
AMBIGUITY_ORDER = ("low", "medium", "high", "missing")
METADATA_PROFILE_ORDER = (
    "source_rank_known",
    "source_rank_missing",
    "target_rank_known",
    "target_rank_missing",
    "wordnet_known",
    "wordnet_missing",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Slice the filled Stage 1 representative semantic-veto lane by "
            "frequency and heuristic bands. This is a diagnostic report only."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--difficulty-stratification-json",
        type=Path,
        default=DEFAULT_DIFFICULTY_STRATIFICATION,
    )
    parser.add_argument("--lane-id", default=DEFAULT_REPRESENTATIVE_LANE_ID)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_representative_band_performance_report(
        policy_payload=_load_json(args.policy_json),
        difficulty_payload=_load_json(args.difficulty_stratification_json),
        policy_path=args.policy_json,
        difficulty_path=args.difficulty_stratification_json,
        representative_lane_id=args.lane_id,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_representative_band_performance_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_representative_band_performance_report(
    *,
    policy_payload: Mapping[str, object],
    difficulty_payload: Mapping[str, object],
    representative_lane_id: str = DEFAULT_REPRESENTATIVE_LANE_ID,
    source_zipf_by_trigger: Mapping[str, float] | None = None,
    policy_path: Path | None = None,
    difficulty_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    weights = _utility_weights(policy_payload)
    acceptance = _as_mapping(policy_payload.get("acceptance"))
    rows = [
        _normalized_row(row)
        for row in _mapping_rows(difficulty_payload.get("case_traces"))
        if str(row.get("lane_id") or "") == representative_lane_id
    ]
    zipf_lookup, zipf_status = _source_zipf_lookup(
        rows=rows,
        source_zipf_by_trigger=source_zipf_by_trigger,
    )
    rows = [_row_with_zipf(row=row, zipf_lookup=zipf_lookup) for row in rows]
    issues = []
    if not rows:
        issues.append("representative_lane_has_no_case_traces")

    overall = _metrics_for_rows(rows=rows, weights=weights, acceptance=acceptance)
    source_rank = _breakdown(
        rows=rows,
        key="source_trigger_rank_bin_en",
        weights=weights,
        acceptance=acceptance,
        preferred_order=SOURCE_RANK_ORDER,
    )
    source_zipf = _breakdown(
        rows=rows,
        key="source_zipf_band_en",
        weights=weights,
        acceptance=acceptance,
        preferred_order=SOURCE_ZIPF_ORDER,
    )
    gold_winner = _breakdown(
        rows=rows,
        key="gold_winner_type",
        weights=weights,
        acceptance=acceptance,
        preferred_order=GOLD_WINNER_ORDER,
    )
    source_rank_by_winner = _cross_breakdown(
        rows=rows,
        left_key="source_trigger_rank_bin_en",
        right_key="gold_winner_type",
        weights=weights,
        acceptance=acceptance,
        left_order=SOURCE_RANK_ORDER,
        right_order=GOLD_WINNER_ORDER,
    )
    declared_ambiguity = _breakdown(
        rows=rows,
        key="declared_ambiguity_class",
        weights=weights,
        acceptance=acceptance,
        preferred_order=AMBIGUITY_ORDER,
    )
    context_source = _breakdown(
        rows=rows,
        key="context_source",
        weights=weights,
        acceptance=acceptance,
    )
    metadata_profile = _metadata_profile_breakdown(
        rows=rows,
        weights=weights,
        acceptance=acceptance,
    )
    trigger_risk = _trigger_risk(rows=rows, weights=weights, acceptance=acceptance)
    sample_warnings = _sample_warnings(
        rows=rows,
        source_rank=source_rank,
        declared_ambiguity=declared_ambiguity,
    )
    return {
        "schema_version": 1,
        "pair": str(policy_payload.get("pair") or difficulty_payload.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "representative_band_performance_established"
            if not issues
            else "representative_band_performance_incomplete"
        ),
        "generated_at": generated_at,
        "inputs": {
            "policy_path": _repo_path(policy_path),
            "difficulty_stratification_path": _repo_path(difficulty_path),
            "difficulty_stratification_decision": str(difficulty_payload.get("decision") or ""),
            "representative_lane_id": representative_lane_id,
        },
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_or_scorer_change": "none",
            "scored_rows_source": "difficulty_stratification_case_traces",
            "wordfreq_zipf_source": zipf_status,
            "primary_question": (
                "Within the filled representative-proxy lane, do frequency or "
                "heuristic bands explain current allow/abstain behavior?"
            ),
            "promotion_rule": (
                "This report is diagnostic only. It cannot promote a formula because "
                "the representative lane still has sparse source-rank coverage and "
                "agent-draft rows that need review."
            ),
        },
        "summary": {
            "issues": issues,
            "case_count": len(rows),
            "family_count": len({str(row.get("family_id") or "") for row in rows}),
            "trigger_count": len({str(row.get("trigger") or "") for row in rows}),
            "source_rank_known_rows": sum(
                1 for row in rows if str(row.get("source_trigger_rank_bin_en") or "") != "missing"
            ),
            "source_zipf_known_rows": sum(
                1 for row in rows if str(row.get("source_zipf_band_en") or "") != "missing"
            ),
            "target_rank_known_rows": sum(
                1 for row in rows if str(row.get("target_lemma_rank_bin_es") or "") != "missing"
            ),
            "wordnet_known_rows": sum(
                1 for row in rows if str(row.get("wordnet_sense_count_bin") or "") != "missing"
            ),
            "overall": overall,
        },
        "breakdowns": {
            "source_trigger_rank_en": source_rank,
            "source_zipf_frequency_en": source_zipf,
            "gold_winner_type": gold_winner,
            "source_trigger_rank_en_by_gold_winner_type": source_rank_by_winner,
            "declared_ambiguity_class": declared_ambiguity,
            "context_source": context_source,
            "metadata_profile": metadata_profile,
        },
        "trigger_risk_summary": trigger_risk,
        "sample_warnings": sample_warnings,
        "answer_to_band_question": _answer_to_band_question(
            rows=rows,
            overall=overall,
            source_rank=source_rank,
            source_zipf=source_zipf,
            sample_warnings=sample_warnings,
        ),
        "limitations": [
            "representative_proxy_is_not_final_browser_distribution",
            "source_rank_known_rows_are_sparse",
            "wordfreq_zipf_is_a_frequency_proxy_not_a_corpus_rank_or_cefr_level",
            "wordnet_and_target_rank_are_missing_for_the_current_representative_proxy",
            "agent_curated_gap_rows_need_human_review_before_promotion_claims",
            "current_policy_is_so_conservative_that_negative_bands_saturate_at_abstain",
        ],
        "next_steps": [
            "Use this report to separate real product behavior from old authored stress-lane behavior.",
            "Improve metadata coverage for the representative lane before claiming a beginner/intermediate/advanced curve.",
            "Rerun formula and threshold bakeoffs on representative case traces, but keep source-rank-known and source-rank-missing rows separate.",
            "Add observed browser contexts or reviewed LLM rows where representative bands are sparse or metadata-missing.",
        ],
    }


def render_representative_band_performance_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    breakdowns = _as_mapping(report.get("breakdowns"))
    answer = _as_mapping(report.get("answer_to_band_question"))
    lines = [
        "# en-es Semantic Veto Representative Band Performance",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Representative cases: `{summary.get('case_count', 0)}`",
        f"- Families / triggers: `{summary.get('family_count', 0)}` / `{summary.get('trigger_count', 0)}`",
        f"- Source-rank known rows: `{summary.get('source_rank_known_rows', 0)}`",
        f"- Source Zipf-known rows: `{summary.get('source_zipf_known_rows', 0)}`",
        f"- Target-rank known rows: `{summary.get('target_rank_known_rows', 0)}`",
        f"- WordNet-known rows: `{summary.get('wordnet_known_rows', 0)}`",
        "",
        "## Answer To The Band Question",
        "",
        f"- Same-band-performance claim: `{answer.get('same_band_performance_claim', '')}`",
        f"- Main read: {answer.get('main_read', '')}",
        f"- Product read: {answer.get('product_read', '')}",
        f"- LLM-data read: {answer.get('llm_data_read', '')}",
        "",
        "## Overall Representative Proxy",
        "",
        _metric_table([_as_mapping(summary.get("overall"))]),
        "",
        "## Source Trigger Rank",
        "",
        _metric_table(breakdowns.get("source_trigger_rank_en")),
        "",
        "## Source Zipf Frequency",
        "",
        _metric_table(breakdowns.get("source_zipf_frequency_en")),
        "",
        "## Source Rank By Gold Winner Type",
        "",
        _cross_metric_table(breakdowns.get("source_trigger_rank_en_by_gold_winner_type")),
        "",
        "## Declared Ambiguity",
        "",
        _metric_table(breakdowns.get("declared_ambiguity_class")),
        "",
        "## Context Source",
        "",
        _metric_table(breakdowns.get("context_source")),
        "",
        "## Metadata Profile",
        "",
        _metric_table(breakdowns.get("metadata_profile")),
        "",
        "## Trigger Risk Summary",
        "",
        _trigger_table(report.get("trigger_risk_summary")),
        "",
        "## Sample Warnings",
        "",
    ]
    warnings = _mapping_rows(report.get("sample_warnings"))
    if not warnings:
        lines.append("_No sample warnings._")
    else:
        for warning in warnings:
            lines.append(
                f"- `{_escape_md(str(warning.get('warning_id') or ''))}`: {warning.get('message', '')}"
            )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _normalized_row(row: Mapping[str, object]) -> dict[str, object]:
    payload = dict(row)
    payload["product_outcome"] = str(payload.get("product_outcome") or "").strip()
    payload["source_trigger_rank_bin_en"] = _nonempty(
        payload.get("source_trigger_rank_bin_en"), "missing"
    )
    payload["target_lemma_rank_bin_es"] = _nonempty(
        payload.get("target_lemma_rank_bin_es"), "missing"
    )
    payload["wordnet_sense_count_bin"] = _nonempty(
        payload.get("wordnet_sense_count_bin"), "missing"
    )
    payload["declared_ambiguity_class"] = _nonempty(
        payload.get("declared_ambiguity_class"), "missing"
    )
    payload["gold_winner_type"] = _nonempty(payload.get("gold_winner_type"), "missing")
    payload["context_source"] = _nonempty(payload.get("context_source"), "missing")
    return payload


def _source_zipf_lookup(
    *,
    rows: Sequence[Mapping[str, object]],
    source_zipf_by_trigger: Mapping[str, float] | None,
) -> tuple[dict[str, float], str]:
    triggers = sorted({str(row.get("trigger") or "").strip() for row in rows if row.get("trigger")})
    if source_zipf_by_trigger is not None:
        return {
            trigger: float(source_zipf_by_trigger.get(trigger) or 0.0) for trigger in triggers
        }, "injected"
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return {}, "wordfreq_package_unavailable"
    return {trigger: float(zipf_frequency(trigger, "en")) for trigger in triggers}, "wordfreq"


def _row_with_zipf(
    *,
    row: Mapping[str, object],
    zipf_lookup: Mapping[str, float],
) -> dict[str, object]:
    payload = dict(row)
    trigger = str(payload.get("trigger") or "").strip()
    zipf = float(zipf_lookup.get(trigger) or 0.0)
    payload["source_zipf_frequency_en"] = round(zipf, 4) if zipf > 0 else None
    payload["source_zipf_band_en"] = _source_zipf_band(zipf)
    return payload


def _source_zipf_band(zipf: float) -> str:
    if zipf >= 5.0:
        return "zipf_5_plus_very_common"
    if zipf >= 4.0:
        return "zipf_4_to_5_common"
    if zipf >= 3.0:
        return "zipf_3_to_4_mid"
    if zipf > 0:
        return "zipf_below_3_rare"
    return "missing"


def _metrics_for_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
    scope_id: str = "overall",
) -> dict[str, object]:
    outcome_counts = Counter(str(row.get("product_outcome") or "") for row in rows)
    metrics = score_product_outcome_counts(
        outcome_counts=outcome_counts,
        weights=weights,
        acceptance=acceptance,
    )
    metrics["scope_id"] = scope_id
    metrics["family_count"] = len({str(row.get("family_id") or "") for row in rows})
    metrics["trigger_count"] = len({str(row.get("trigger") or "") for row in rows})
    metrics["source_rank_known_rate"] = _optional_ratio(
        sum(1 for row in rows if str(row.get("source_trigger_rank_bin_en") or "") != "missing"),
        len(rows),
    )
    return metrics


def _breakdown(
    *,
    rows: Sequence[Mapping[str, object]],
    key: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
    preferred_order: Sequence[str] = (),
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[_nonempty(row.get(key), "missing")].append(row)
    return [
        _metrics_for_rows(
            rows=grouped[scope_id],
            weights=weights,
            acceptance=acceptance,
            scope_id=scope_id,
        )
        for scope_id in _ordered_keys(grouped, preferred_order)
    ]


def _cross_breakdown(
    *,
    rows: Sequence[Mapping[str, object]],
    left_key: str,
    right_key: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
    left_order: Sequence[str] = (),
    right_order: Sequence[str] = (),
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        left = _nonempty(row.get(left_key), "missing")
        right = _nonempty(row.get(right_key), "missing")
        grouped[(left, right)].append(row)
    rows_out = []
    left_keys = _ordered_keys({left: [] for left, _ in grouped}, left_order)
    for left in left_keys:
        right_keys = _ordered_keys(
            {right: [] for group_left, right in grouped if group_left == left},
            right_order,
        )
        for right in right_keys:
            metrics = _metrics_for_rows(
                rows=grouped[(left, right)],
                weights=weights,
                acceptance=acceptance,
                scope_id=f"{left}::{right}",
            )
            metrics["left_scope_id"] = left
            metrics["right_scope_id"] = right
            rows_out.append(metrics)
    return rows_out


def _metadata_profile_breakdown(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[
            "source_rank_known"
            if str(row.get("source_trigger_rank_bin_en") or "") != "missing"
            else "source_rank_missing"
        ].append(row)
        grouped[
            "target_rank_known"
            if str(row.get("target_lemma_rank_bin_es") or "") != "missing"
            else "target_rank_missing"
        ].append(row)
        grouped[
            "wordnet_known"
            if str(row.get("wordnet_sense_count_bin") or "") != "missing"
            else "wordnet_missing"
        ].append(row)
    return [
        _metrics_for_rows(
            rows=grouped[scope_id],
            weights=weights,
            acceptance=acceptance,
            scope_id=scope_id,
        )
        for scope_id in _ordered_keys(grouped, METADATA_PROFILE_ORDER)
    ]


def _trigger_risk(
    *,
    rows: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("trigger") or "")].append(row)
    result = []
    for trigger, trigger_rows in grouped.items():
        metrics = _metrics_for_rows(
            rows=trigger_rows,
            weights=weights,
            acceptance=acceptance,
            scope_id=trigger,
        )
        metrics["failure_count"] = int(metrics.get("positive_abstain_count") or 0) + int(
            metrics.get("negative_allow_count") or 0
        )
        metrics["source_rank_bin"] = _first_distinct(
            trigger_rows,
            "source_trigger_rank_bin_en",
            default="missing",
        )
        metrics["source_zipf_band"] = _first_distinct(
            trigger_rows,
            "source_zipf_band_en",
            default="missing",
        )
        metrics["declared_ambiguity_class"] = _first_distinct(
            trigger_rows,
            "declared_ambiguity_class",
            default="missing",
        )
        result.append(metrics)
    return sorted(
        result,
        key=lambda row: (
            -int(row.get("failure_count") or 0),
            -int(row.get("case_count") or 0),
            str(row.get("scope_id") or ""),
        ),
    )[:15]


def _sample_warnings(
    *,
    rows: Sequence[Mapping[str, object]],
    source_rank: Sequence[Mapping[str, object]],
    declared_ambiguity: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    warnings = []
    missing_rank_count = sum(
        1 for row in rows if str(row.get("source_trigger_rank_bin_en") or "") == "missing"
    )
    if rows and missing_rank_count / len(rows) > 0.5:
        warnings.append(
            {
                "warning_id": "source_rank_mostly_missing",
                "message": (
                    f"{missing_rank_count} of {len(rows)} representative rows lack source-rank "
                    "metadata, so frequency-band curves are still fragile."
                ),
            }
        )
    for label, breakdown in (
        ("source_rank", source_rank),
        ("declared_ambiguity", declared_ambiguity),
    ):
        small = [
            str(row.get("scope_id") or "")
            for row in breakdown
            if int(row.get("case_count") or 0) < 10 and str(row.get("scope_id") or "") != "missing"
        ]
        if small:
            warnings.append(
                {
                    "warning_id": f"{label}_small_cells",
                    "message": (
                        f"Some {label} cells have fewer than 10 cases: "
                        + ", ".join(sorted(small))
                        + ". Treat their rates as directional only."
                    ),
                }
            )
    return warnings


def _answer_to_band_question(
    *,
    rows: Sequence[Mapping[str, object]],
    overall: Mapping[str, object],
    source_rank: Sequence[Mapping[str, object]],
    source_zipf: Sequence[Mapping[str, object]],
    sample_warnings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    known_rank_rows = [
        row for row in rows if str(row.get("source_trigger_rank_bin_en") or "") != "missing"
    ]
    positive_rates = {
        str(row.get("scope_id") or ""): row.get("positive_allow_rate")
        for row in source_rank
        if row.get("positive_allow_rate") is not None
    }
    rate_values = [float(value) for value in positive_rates.values()]
    if rate_values:
        spread = round(max(rate_values) - min(rate_values), 4)
    else:
        spread = 0.0
    zipf_rates = {
        str(row.get("scope_id") or ""): row.get("positive_allow_rate")
        for row in source_zipf
        if row.get("positive_allow_rate") is not None
    }
    zipf_rate_values = [float(value) for value in zipf_rates.values()]
    zipf_spread = (
        round(max(zipf_rate_values) - min(zipf_rate_values), 4) if zipf_rate_values else 0.0
    )
    return {
        "same_band_performance_claim": "not_supported",
        "known_rank_rows": len(known_rank_rows),
        "positive_allow_rate_spread_among_reported_rank_bands": spread,
        "source_zipf_positive_allow_rate_spread": zipf_spread,
        "main_read": (
            "The representative-proxy lane does not prove that bands perform the same. "
            "It shows low positive allow across most source-rank bands, while the denser "
            "Zipf fallback suggests very common triggers may be especially abstain-heavy. "
            "That is a promising clue, not yet a stable curve."
        ),
        "product_read": (
            "Current browser-like behavior is conservative: negative rows are all abstained, "
            f"while positive allow is {_format_percent(overall.get('positive_allow_rate'))}. "
            "That is safer than over-replacing, but it misses many good replacements."
        ),
        "llm_data_read": (
            "The immediate LLM-data need is not proven to be one rank band. The stronger "
            "finding is that we should add denser, programmatic frequency metadata and then "
            "test whether very-common trigger abstention persists before using a top-N "
            "difficulty formula confidently."
        ),
        "sample_warning_count": len(sample_warnings),
    }


def _metric_table(rows: object) -> str:
    metric_rows = _mapping_rows(rows)
    if not metric_rows:
        return "_None._"
    lines = [
        "| Scope | Cases | Positives | Negatives | Pos allow | Neg abstain | Pos abstain | Neg allow | Utility | Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in metric_rows:
        checks = _as_mapping(row.get("target_checks"))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('scope_id') or ''))}`",
                    f"`{int(row.get('case_count') or 0)}`",
                    f"`{int(row.get('positive_case_count') or 0)}`",
                    f"`{int(row.get('negative_case_count') or 0)}`",
                    f"`{_format_percent(row.get('positive_allow_rate'))}`",
                    f"`{_format_percent(row.get('negative_abstain_rate'))}`",
                    f"`{int(row.get('positive_abstain_count') or 0)}`",
                    f"`{int(row.get('negative_allow_count') or 0)}`",
                    f"`{row.get('utility_score')}`",
                    f"`{_escape_md(str(checks.get('target_status') or ''))}`",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _cross_metric_table(rows: object) -> str:
    metric_rows = _mapping_rows(rows)
    if not metric_rows:
        return "_None._"
    lines = [
        "| Source Rank | Winner Type | Cases | Pos allow | Neg abstain | Pos abstain | Neg allow |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metric_rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('left_scope_id') or ''))}`",
                    f"`{_escape_md(str(row.get('right_scope_id') or ''))}`",
                    f"`{int(row.get('case_count') or 0)}`",
                    f"`{_format_percent(row.get('positive_allow_rate'))}`",
                    f"`{_format_percent(row.get('negative_abstain_rate'))}`",
                    f"`{int(row.get('positive_abstain_count') or 0)}`",
                    f"`{int(row.get('negative_allow_count') or 0)}`",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _trigger_table(rows: object) -> str:
    trigger_rows = _mapping_rows(rows)
    if not trigger_rows:
        return "_None._"
    lines = [
        "| Trigger | Cases | Failures | Source Rank | Zipf Band | Ambiguity | Pos allow | Neg abstain |",
        "| --- | ---: | ---: | --- | --- | --- | ---: | ---: |",
    ]
    for row in trigger_rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('scope_id') or ''))}`",
                    f"`{int(row.get('case_count') or 0)}`",
                    f"`{int(row.get('failure_count') or 0)}`",
                    f"`{_escape_md(str(row.get('source_rank_bin') or ''))}`",
                    f"`{_escape_md(str(row.get('source_zipf_band') or ''))}`",
                    f"`{_escape_md(str(row.get('declared_ambiguity_class') or ''))}`",
                    f"`{_format_percent(row.get('positive_allow_rate'))}`",
                    f"`{_format_percent(row.get('negative_abstain_rate'))}`",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _ordered_keys(grouped: Mapping[str, object], preferred_order: Sequence[str]) -> list[str]:
    seen = set()
    ordered = []
    for key in preferred_order:
        if key in grouped:
            ordered.append(key)
            seen.add(key)
    ordered.extend(sorted(key for key in grouped if key not in seen))
    return ordered


def _nonempty(value: object, default: str) -> str:
    text = str(value or "").strip()
    return text if text else default


def _optional_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _first_distinct(
    rows: Sequence[Mapping[str, object]],
    key: str,
    *,
    default: str,
) -> str:
    values = sorted({_nonempty(row.get(key), default) for row in rows})
    return values[0] if len(values) == 1 else "mixed"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
