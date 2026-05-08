from __future__ import annotations

from collections import Counter, defaultdict
from typing import Mapping, Sequence

from semantic_veto_difficulty_stratification_common import (
    OUTCOME_FAILURES,
    _optional_int,
    _optional_ratio,
)
from semantic_veto_difficulty_stratification_frequency import FrequencyLookup, _source_zipf_band
from semantic_veto_difficulty_stratification_rows import _positive_allow_rate, _rank_bin
from semantic_veto_product_quality_en_es import (
    _format_percent,
    _safe_float,
    score_product_outcome_counts,
)


def _metrics(
    rows: Sequence[Mapping[str, object]],
    *,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
) -> dict[str, object]:
    outcome_counts = Counter(str(row.get("product_outcome") or "") for row in rows)
    metrics = score_product_outcome_counts(
        outcome_counts=outcome_counts,
        weights=weights,
        acceptance=acceptance,
    )
    metrics["case_count"] = len(rows)
    metrics["family_count"] = len({row.get("family_id") for row in rows if row.get("family_id")})
    metrics["source_rank_known_rate"] = _optional_ratio(
        sum(1 for row in rows if row.get("source_trigger_rank_en") is not None),
        len(rows),
    )
    metrics["source_zipf_known_rate"] = _optional_ratio(
        sum(1 for row in rows if row.get("source_zipf_frequency_en") is not None),
        len(rows),
    )
    metrics["target_rank_known_rate"] = _optional_ratio(
        sum(1 for row in rows if row.get("target_lemma_rank_es") is not None),
        len(rows),
    )
    return metrics


def _breakdowns(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
    weights: Mapping[str, float],
    acceptance: Mapping[str, object],
    order: Sequence[str] = (),
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        value = str(row.get(key) or "missing").strip() or "missing"
        grouped[value].append(row)
    result = []
    for scope_id, group in grouped.items():
        metrics = _metrics(group, weights=weights, acceptance=acceptance)
        metrics["scope_id"] = scope_id
        result.append(metrics)
    if order:
        order_index = {value: index for index, value in enumerate(order)}
        return sorted(
            result,
            key=lambda item: (order_index.get(str(item["scope_id"]), 999), str(item["scope_id"])),
        )
    return sorted(result, key=lambda item: str(item["scope_id"]))


def _metadata_diagnostics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    source_match_counts = Counter(
        str(row.get("source_trigger_frequency_match_kind") or "missing") for row in rows
    )
    source_zipf_match_counts = Counter(
        str(row.get("source_zipf_match_kind") or "missing") for row in rows
    )
    target_match_counts = Counter(
        str(row.get("target_lemma_frequency_match_kind") or "missing") for row in rows
    )
    missing_source_triggers = sorted(
        {
            str(row.get("trigger") or "")
            for row in rows
            if row.get("source_trigger_rank_en") is None and row.get("trigger")
        }
    )
    missing_source_zipf_triggers = sorted(
        {
            str(row.get("trigger") or "")
            for row in rows
            if row.get("source_zipf_frequency_en") is None and row.get("trigger")
        }
    )
    missing_targets = sorted(
        {
            str(row.get("target_lemma") or "")
            for row in rows
            if row.get("target_lemma_rank_es") is None and row.get("target_lemma")
        }
    )
    source_known = sum(1 for row in rows if row.get("source_trigger_rank_en") is not None)
    source_zipf_known = sum(1 for row in rows if row.get("source_zipf_frequency_en") is not None)
    target_known = sum(1 for row in rows if row.get("target_lemma_rank_es") is not None)
    return {
        "case_count": len(rows),
        "source_rank_known_rows": source_known,
        "source_rank_known_rate": _optional_ratio(source_known, len(rows)),
        "source_zipf_known_rows": source_zipf_known,
        "source_zipf_known_rate": _optional_ratio(source_zipf_known, len(rows)),
        "target_rank_known_rows": target_known,
        "target_rank_known_rate": _optional_ratio(target_known, len(rows)),
        "source_frequency_match_counts": dict(sorted(source_match_counts.items())),
        "source_zipf_match_counts": dict(sorted(source_zipf_match_counts.items())),
        "target_frequency_match_counts": dict(sorted(target_match_counts.items())),
        "missing_source_rank_trigger_count": len(missing_source_triggers),
        "missing_source_rank_triggers": missing_source_triggers,
        "missing_source_zipf_trigger_count": len(missing_source_zipf_triggers),
        "missing_source_zipf_triggers": missing_source_zipf_triggers,
        "missing_target_rank_candidate_count": len(missing_targets),
        "missing_target_rank_candidates": missing_targets,
        "wordnet_sense_count_known_rows": sum(
            1 for row in rows if row.get("wordnet_sense_count") is not None
        ),
        "translation_candidate_count_known_rows": sum(
            1 for row in rows if row.get("translation_candidate_count") is not None
        ),
    }


def _key_findings(
    *,
    rows: Sequence[Mapping[str, object]],
    overall: Mapping[str, object],
    diagnostics: Mapping[str, object],
) -> list[str]:
    findings = [
        (
            "Overall measured lanes are "
            f"{_format_percent(overall.get('positive_allow_rate'))} positive allow and "
            f"{_format_percent(overall.get('negative_abstain_rate'))} negative abstain."
        ),
        (
            "English source-trigger rank coverage is "
            f"{_format_percent(diagnostics.get('source_rank_known_rate'))}; missing rank remains "
            "a first-class metadata gap rather than a reason to drop rows."
        ),
        (
            "English source-trigger Zipf coverage is "
            f"{_format_percent(diagnostics.get('source_zipf_known_rate'))}; use it as a denser "
            "frequency proxy while keeping corpus rank and learner level separate."
        ),
        (
            "Spanish target-rank coverage is "
            f"{_format_percent(diagnostics.get('target_rank_known_rate'))}; this is too sparse "
            "to use as a standalone learner-difficulty proof."
        ),
    ]
    beginner_rows = [
        row
        for row in rows
        if str(row.get("source_trigger_rank_bin_en") or "") in {"1-500", "501-1000"}
    ]
    if beginner_rows:
        beginner_failures = sum(
            1 for row in beginner_rows if str(row.get("product_outcome") or "") in OUTCOME_FAILURES
        )
        findings.append(
            f"Known top-1000 English trigger rows have {beginner_failures} product failures "
            f"over {len(beginner_rows)} measured cases."
        )
    else:
        findings.append(
            "The installed English frequency pack does not cover enough current triggers to "
            "estimate a top-1000 trigger curve yet."
        )
    very_common_rows = [
        row
        for row in rows
        if str(row.get("source_zipf_band_en") or "") == "zipf_5_plus_very_common"
    ]
    common_rows = [
        row for row in rows if str(row.get("source_zipf_band_en") or "") == "zipf_4_to_5_common"
    ]
    if very_common_rows and common_rows:
        findings.append(
            "Zipf frequency fallback separates very-common and common triggers at "
            f"{_format_percent(_positive_allow_rate(very_common_rows))} versus "
            f"{_format_percent(_positive_allow_rate(common_rows))} positive allow."
        )
    high_sense_rows = [
        row for row in rows if (_optional_int(row.get("wordnet_sense_count")) or 0) >= 10
    ]
    if high_sense_rows:
        high_sense_failures = sum(
            1
            for row in high_sense_rows
            if str(row.get("product_outcome") or "") in OUTCOME_FAILURES
        )
        findings.append(
            f"Rows with 10+ WordNet senses have {high_sense_failures} failures over "
            f"{len(high_sense_rows)} cases in the measured lanes."
        )
    return findings


def _trigger_risk_summary(
    rows: Sequence[Mapping[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        trigger = str(row.get("trigger") or "").strip()
        if trigger:
            grouped[trigger].append(row)
    summaries = []
    for trigger, group in grouped.items():
        outcomes = Counter(str(row.get("product_outcome") or "") for row in group)
        source_ranks = [
            _safe_float(row.get("source_trigger_rank_en"))
            for row in group
            if row.get("source_trigger_rank_en") is not None
        ]
        zipf_values = [
            _safe_float(row.get("source_zipf_frequency_en"))
            for row in group
            if row.get("source_zipf_frequency_en") is not None
        ]
        wordnet_counts = [
            _optional_int(row.get("wordnet_sense_count")) or 0
            for row in group
            if row.get("wordnet_sense_count") is not None
        ]
        summaries.append(
            {
                "trigger": trigger,
                "case_count": len(group),
                "family_count": len(
                    {row.get("family_id") for row in group if row.get("family_id")}
                ),
                "positive_abstain_count": outcomes["positive_abstain"],
                "negative_allow_count": outcomes["negative_allow"],
                "failure_count": outcomes["positive_abstain"] + outcomes["negative_allow"],
                "source_trigger_best_rank_en": min(source_ranks) if source_ranks else None,
                "source_trigger_rank_bin_en": _rank_bin(
                    min(source_ranks) if source_ranks else None
                ),
                "source_zipf_frequency_en": max(zipf_values) if zipf_values else None,
                "source_zipf_band_en": _source_zipf_band(max(zipf_values) if zipf_values else None),
                "max_wordnet_sense_count": max(wordnet_counts) if wordnet_counts else None,
                "lanes": sorted({str(row.get("lane_id") or "") for row in group}),
            }
        )
    return sorted(
        summaries,
        key=lambda item: (
            -int(item["negative_allow_count"]),
            -int(item["failure_count"]),
            _safe_float(item.get("source_trigger_best_rank_en")) or 999999.0,
            -_safe_float(item.get("source_zipf_frequency_en")),
            str(item["trigger"]),
        ),
    )[: max(1, int(top_n))]


def _failure_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    failures = [row for row in rows if str(row.get("product_outcome") or "") in OUTCOME_FAILURES]
    failures = sorted(
        failures,
        key=lambda row: (
            0 if row.get("product_outcome") == "negative_allow" else 1,
            _safe_float(row.get("source_trigger_rank_en")) or 999999.0,
            -(_optional_int(row.get("wordnet_sense_count")) or 0),
            str(row.get("case_id") or ""),
        ),
    )
    return [
        {
            "case_id": str(row.get("case_id") or ""),
            "lane_id": str(row.get("lane_id") or ""),
            "suite_id": str(row.get("suite_id") or ""),
            "trigger": str(row.get("trigger") or ""),
            "target_lemma": str(row.get("target_lemma") or ""),
            "product_outcome": str(row.get("product_outcome") or ""),
            "source_trigger_rank_bin_en": str(row.get("source_trigger_rank_bin_en") or ""),
            "source_zipf_band_en": str(row.get("source_zipf_band_en") or ""),
            "target_lemma_rank_bin_es": str(row.get("target_lemma_rank_bin_es") or ""),
            "wordnet_sense_count": row.get("wordnet_sense_count"),
            "shadow_lead": row.get("shadow_lead"),
            "phrase_lead_to_best": row.get("phrase_lead_to_best"),
            "sentence": str(row.get("sentence") or ""),
        }
        for row in failures[: max(1, int(top_n))]
    ]


def _limitations(
    *,
    source_frequency: FrequencyLookup,
    target_frequency: FrequencyLookup,
    diagnostics: Mapping[str, object],
) -> list[str]:
    limitations = [
        "difficulty_report_is_diagnostic_only",
        "stress_llm_and_representative_proxy_lanes_are_reported_together_but_not_promotion_equivalent",
        "frequency_rank_is_a_proxy_not_a_cefr_or_user-known-word_model",
        "source_zipf_frequency_is_a_package_proxy_not_a_corpus_rank_or_cefr_level",
        "target_lemma_rank_can_be_sparse_when_spanish_replacements_are_inflected_or_absent",
    ]
    if source_frequency.status != "ok":
        limitations.append(f"source_frequency_lookup_status_{source_frequency.status}")
    if target_frequency.status != "ok":
        limitations.append(f"target_frequency_lookup_status_{target_frequency.status}")
    if _safe_float(diagnostics.get("source_rank_known_rate")) < 0.5:
        limitations.append("source_rank_coverage_below_50_percent")
    if _safe_float(diagnostics.get("source_zipf_known_rate")) < 0.5:
        limitations.append("source_zipf_coverage_below_50_percent")
    if _safe_float(diagnostics.get("target_rank_known_rate")) < 0.5:
        limitations.append("target_rank_coverage_below_50_percent")
    return limitations


def _next_steps(diagnostics: Mapping[str, object]) -> list[str]:
    steps = [
        "Use this report to choose the first frequency/ambiguity strata for expanded LLM evaluation rows.",
        "Improve target-lemma normalization or target-frequency coverage before using Spanish rank as an SRS difficulty gate.",
        "Keep source-trigger rank, source Zipf frequency, target rank, and ambiguity proxies separate in future acceptance claims.",
    ]
    if _safe_float(diagnostics.get("source_rank_known_rate")) < 0.5:
        steps.append(
            "Add or configure a denser English source frequency list before claiming a beginner-trigger accuracy curve."
        )
    if _safe_float(diagnostics.get("source_zipf_known_rate")) >= 0.5:
        steps.append(
            "Use Zipf bands as the next no-spend expansion axis, then verify the very-common false-abstain signal with more representative rows."
        )
    if _safe_float(diagnostics.get("target_rank_known_rate")) < 0.5:
        steps.append(
            "Add exact lemma normalization for Spanish replacements before estimating learner difficulty at scale."
        )
    return steps


def _decision(
    *,
    row_count: int,
    source_frequency: FrequencyLookup,
    target_frequency: FrequencyLookup,
) -> dict[str, str]:
    if row_count <= 0:
        return {
            "status": "review",
            "decision": "no_case_rows_available_for_stratification",
        }
    if source_frequency.status != "ok" and target_frequency.status != "ok":
        return {
            "status": "review",
            "decision": "case_rows_available_but_frequency_metadata_unavailable",
        }
    return {
        "status": "ok",
        "decision": "difficulty_stratification_baseline_established",
    }
