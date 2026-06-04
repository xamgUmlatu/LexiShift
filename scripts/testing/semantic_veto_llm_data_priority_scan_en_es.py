#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from math import log1p
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _repo_path,
    _resolve_repo_path,
    _safe_float,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_DIFFICULTY_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_scan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_data_priority_scan_en_es_latest.md"

ERROR_OUTCOMES = {"positive_abstain", "negative_allow"}
FORBIDDEN_RANKING_FIELDS = (
    "manual_case_type",
    "gold_decision",
    "gold_winner_type",
    "predicted_decision",
    "predicted_winner_type",
    "product_outcome",
    "error_type",
    "veto_reason",
)
PROGRAMMATIC_FEATURE_FIELDS = (
    "source_rank_risk",
    "source_rank_missing",
    "target_rank_value",
    "wordnet_sense_risk",
    "wordnet_pos_risk",
    "translation_fanout_risk",
    "shadow_presence_risk",
    "ambiguity_risk",
    "active_evidence_gap",
    "shadow_evidence_gap",
    "phrase_evidence_gap",
    "metadata_gap_rate",
    "coverage_gap",
    "active_low_rate",
    "near_tie_rate",
    "phrase_near_best_rate",
    "phrase_surface_pattern_rate",
    "decision_uncertainty",
    "expected_fixability",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rank en-es semantic-veto trigger/target pairs by LLM data need using "
            "programmatic metadata and scorer surfaces only."
        )
    )
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_llm_data_priority_scan_report(
    *,
    difficulty_payload: Mapping[str, object],
    difficulty_json_path: Path | None = None,
    top_n: int = 25,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_rows = _mapping_rows(difficulty_payload.get("case_traces"))
    groups = _group_candidate_rows(source_rows)
    scan_rows = [_scan_row(group_key=group_key, rows=rows) for group_key, rows in groups.items()]
    scan_rows.sort(
        key=lambda row: (
            -_safe_float(row.get("scored_context_llm_data_need")),
            -_safe_float(row.get("static_llm_data_need")),
            str(row.get("trigger") or ""),
            str(row.get("target_lemma") or ""),
        )
    )
    for index, row in enumerate(scan_rows, start=1):
        row["priority_rank"] = index
        row["in_top_n"] = index <= int(top_n)

    issues = _issues(scan_rows)
    status = "review" if issues else "ok"
    summary = _summary(scan_rows=scan_rows, top_n=top_n, issues=issues)
    report = {
        "schema_version": 1,
        "pair": str(difficulty_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "llm_data_priority_scan_established"
            if status == "ok"
            else "llm_data_priority_scan_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "difficulty_json": _repo_path(difficulty_json_path),
            "difficulty_decision": str(difficulty_payload.get("decision") or ""),
            "difficulty_case_count": len(source_rows),
        },
        "methodology": {
            "purpose": (
                "Allocate LLM generation budget to trigger/target pairs where more "
                "active, shadow, or phrase/no-winner evidence is most likely to improve "
                "semantic-veto quality."
            ),
            "ranking_scope": (
                "Programmatic-feature scan over currently measured/scored candidate "
                "rows. It can rank a wider inventory once the same metadata fields are "
                "available for that inventory."
            ),
            "forbidden_ranking_fields": list(FORBIDDEN_RANKING_FIELDS),
            "programmatic_feature_fields": list(PROGRAMMATIC_FEATURE_FIELDS),
            "score_formula": {
                "static_llm_data_need": (
                    "exposure_value * (0.25 + 0.75 * ambiguity_risk) * (0.25 + 0.75 * coverage_gap)"
                ),
                "scored_context_llm_data_need": (
                    "static_llm_data_need * (0.65 + 0.35 * decision_uncertainty) * "
                    "(0.70 + 0.30 * expected_fixability)"
                ),
            },
            "label_policy": (
                "Gold labels, product outcomes, and manual case-type labels may be "
                "used only in validation_shadow fields; they are not ranking inputs."
            ),
        },
        "summary": summary,
        "e2e_checks": {
            "forbidden_fields_absent_from_programmatic_features": all(
                set(_as_mapping(row.get("programmatic_features"))).isdisjoint(
                    FORBIDDEN_RANKING_FIELDS
                )
                for row in scan_rows
            ),
            "all_programmatic_features_declared": all(
                set(_as_mapping(row.get("programmatic_features"))).issubset(
                    PROGRAMMATIC_FEATURE_FIELDS
                )
                for row in scan_rows
            ),
            "rows_sorted_by_scored_context_need": _is_sorted_by_need(scan_rows),
            "validation_shadow_kept_separate": all(
                "validation_shadow" in row and "product_outcome" not in row for row in scan_rows
            ),
        },
        "priority_rows": scan_rows,
        "top_priority_rows": scan_rows[: int(top_n)],
        "limitations": [
            "current_scan_reads_measured_scored_contexts_not_full_database_inventory",
            "english_source_rank_and_spanish_target_rank_coverage_are_incomplete",
            "wordnet_and_translation_metadata_are_not_available_for_every_candidate",
            "score_surface_features_require_observed_or_generated_contexts",
            "ranking_is_for_data_spend_allocation_not_runtime_policy_promotion",
        ],
        "next_steps": [
            "Run this scanner after every difficulty-stratification refresh.",
            "Use top rows to request LLM active/shadow/phrase evidence packets.",
            "Add a wider inventory input once rulegen can emit the same programmatic metadata for all candidate rules.",
            "Evaluate rank quality with labels only after the priority list is frozen.",
        ],
    }
    return report


def render_llm_data_priority_scan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Data Priority Scan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate pairs: `{summary.get('candidate_pair_count', 0)}`",
        f"- Top N: `{summary.get('top_n', 0)}`",
        f"- Forbidden feature fields: `{summary.get('forbidden_feature_field_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        "Ranking uses programmatic metadata and raw scorer surfaces only. Gold labels, "
        "manual case labels, and product outcomes are kept out of the ranking feature vector.",
        "",
        "## Score Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| top static need | {float(summary.get('top_static_llm_data_need') or 0.0):.4f} |",
        f"| top scored-context need | {float(summary.get('top_scored_context_llm_data_need') or 0.0):.4f} |",
        f"| source rank known rate | {_format_percent(summary.get('source_rank_known_rate'))} |",
        f"| target rank known rate | {_format_percent(summary.get('target_rank_known_rate'))} |",
        f"| WordNet sense known rate | {_format_percent(summary.get('wordnet_sense_known_rate'))} |",
        f"| translation count known rate | {_format_percent(summary.get('translation_count_known_rate'))} |",
        "",
        "## Recommended LLM Packets",
        "",
        "| Rank | Trigger | Target | Need | Static | Active | Shadow | Phrase | Locked | Reasons | Validation shadow |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in _mapping_rows(report.get("top_priority_rows")):
        packet = _as_mapping(row.get("recommended_llm_packet"))
        validation = _as_mapping(row.get("validation_shadow"))
        lines.append(
            " | ".join(
                [
                    f"| {int(row.get('priority_rank') or 0)}",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('target_lemma') or ''))}`",
                    f"{float(row.get('scored_context_llm_data_need') or 0.0):.4f}",
                    f"{float(row.get('static_llm_data_need') or 0.0):.4f}",
                    str(packet.get("active_rows") or 0),
                    str(packet.get("shadow_rows") or 0),
                    str(packet.get("phrase_rows") or 0),
                    str(packet.get("locked_eval_rows") or 0),
                    _escape_md(", ".join(str(item) for item in row.get("priority_reasons", []))),
                    (
                        f"{validation.get('observed_failure_count', 0)} / "
                        f"{validation.get('observed_case_count', 0)}"
                    ),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Feature Guardrails",
            "",
            "| Check | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", []))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", []))
    return "\n".join(lines) + "\n"


def _group_candidate_rows(
    rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], list[Mapping[str, object]]]:
    groups: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        trigger = str(row.get("trigger") or "").strip()
        target = str(row.get("target_lemma") or "").strip()
        if not trigger or not target:
            continue
        groups[(trigger.lower(), target.lower())].append(row)
    return dict(groups)


def _scan_row(
    *, group_key: tuple[str, str], rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    trigger, target = group_key
    features = _programmatic_features(rows)
    exposure_value = max(
        _safe_float(features.get("source_rank_risk")),
        0.35 * _safe_float(features.get("source_rank_missing")),
        0.20 * _safe_float(features.get("target_rank_value")),
    )
    static_need = _clamp(
        exposure_value
        * (0.25 + 0.75 * _safe_float(features.get("ambiguity_risk")))
        * (0.25 + 0.75 * _safe_float(features.get("coverage_gap")))
    )
    scored_need = _clamp(
        static_need
        * (0.65 + 0.35 * _safe_float(features.get("decision_uncertainty")))
        * (0.70 + 0.30 * _safe_float(features.get("expected_fixability")))
    )
    active_need = _clamp(
        exposure_value
        * (
            0.45 * _safe_float(features.get("active_evidence_gap"))
            + 0.35 * _safe_float(features.get("active_low_rate"))
            + 0.20 * _safe_float(features.get("near_tie_rate"))
        )
    )
    shadow_need = _clamp(
        exposure_value
        * (
            0.35 * _safe_float(features.get("shadow_evidence_gap"))
            + 0.35 * _safe_float(features.get("ambiguity_risk"))
            + 0.30 * _safe_float(features.get("near_tie_rate"))
        )
    )
    phrase_need = _clamp(
        exposure_value
        * (
            0.45 * _safe_float(features.get("phrase_evidence_gap"))
            + 0.25 * _safe_float(features.get("phrase_surface_pattern_rate"))
            + 0.30 * _safe_float(features.get("phrase_near_best_rate"))
        )
    )
    packet = _recommended_packet(
        active_need=active_need,
        shadow_need=shadow_need,
        phrase_need=phrase_need,
    )
    return {
        "trigger": trigger,
        "target_lemma": target,
        "candidate_key": f"{trigger}::{target}",
        "family_ids": sorted(
            {str(row.get("family_id") or "") for row in rows if row.get("family_id")}
        ),
        "source_ids": sorted(
            {str(row.get("source_id") or "") for row in rows if row.get("source_id")}
        ),
        "lane_types": dict(
            sorted(Counter(str(row.get("lane_type") or "") for row in rows).items())
        ),
        "case_count": len(rows),
        "static_llm_data_need": _round4(static_need),
        "scored_context_llm_data_need": _round4(scored_need),
        "priority_band": _priority_band(scored_need),
        "programmatic_features": features,
        "recommended_llm_packet": packet,
        "priority_reasons": _priority_reasons(features=features, packet=packet),
        "validation_shadow": _validation_shadow(rows),
    }


def _programmatic_features(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    source_ranks = _number_values(rows, "source_trigger_rank_en")
    target_ranks = _number_values(rows, "target_lemma_rank_es")
    sense_counts = _number_values(rows, "wordnet_sense_count")
    pos_counts = _number_values(rows, "wordnet_pos_count")
    translation_counts = _number_values(rows, "translation_candidate_count")
    active_counts = _number_values(rows, "active_evidence_count")
    shadow_counts = _number_values(rows, "shadow_evidence_count")
    phrase_counts = _number_values(rows, "phrase_control_evidence_count")
    admitted_shadow_counts = _number_values(rows, "admitted_shadow_count")
    active_scores = _number_values(rows, "active_score")
    shadow_scores = _number_values(rows, "strongest_shadow_score")
    phrase_scores = _number_values(rows, "phrase_control_score")

    source_rank = min(source_ranks) if source_ranks else None
    target_rank = min(target_ranks) if target_ranks else None
    source_rank_missing = 0.0 if source_rank is not None else 1.0
    target_rank_value = _rank_risk_score(target_rank) if target_rank is not None else 0.0
    source_rank_risk = _rank_risk_score(source_rank) if source_rank is not None else 0.0
    sense_risk = _sense_risk(max(sense_counts) if sense_counts else None)
    pos_risk = _pos_risk(max(pos_counts) if pos_counts else None)
    translation_risk = _translation_risk(max(translation_counts) if translation_counts else None)
    shadow_presence = _clamp(
        max(
            max(admitted_shadow_counts) if admitted_shadow_counts else 0.0,
            (max(shadow_counts) / 4.0) if shadow_counts else 0.0,
        )
    )
    ambiguity_risk = _clamp(
        0.35 * sense_risk + 0.18 * pos_risk + 0.22 * translation_risk + 0.25 * shadow_presence
    )

    active_gap = _evidence_gap(max(active_counts) if active_counts else None, target=4)
    shadow_gap = _evidence_gap(max(shadow_counts) if shadow_counts else None, target=4)
    phrase_gap = _evidence_gap(max(phrase_counts) if phrase_counts else None, target=4)
    metadata_gap = _ratio(
        sum(
            1
            for value in (
                source_rank,
                target_rank,
                max(sense_counts) if sense_counts else None,
                max(translation_counts) if translation_counts else None,
            )
            if value is None
        ),
        4,
    )
    coverage_gap = _clamp(
        0.30 * active_gap + 0.25 * shadow_gap + 0.25 * phrase_gap + 0.20 * metadata_gap
    )

    margins = [
        active - shadow
        for active, shadow in zip(active_scores, shadow_scores)
        if active is not None and shadow is not None
    ]
    low_active_rate = _ratio(sum(1 for value in active_scores if value < 0.05), len(active_scores))
    near_tie_rate = _ratio(sum(1 for value in margins if abs(value) < 0.02), len(margins))
    phrase_near_best_rate = _phrase_near_best_rate(
        active_scores=active_scores,
        shadow_scores=shadow_scores,
        phrase_scores=phrase_scores,
    )
    phrase_surface_rate = _ratio(
        sum(1 for row in rows if _has_phrase_surface_pattern(row)), len(rows)
    )
    decision_uncertainty = _clamp(
        0.35 * near_tie_rate
        + 0.25 * low_active_rate
        + 0.25 * phrase_near_best_rate
        + 0.15 * coverage_gap
    )
    expected_fixability = _clamp(
        0.45 * coverage_gap + 0.35 * decision_uncertainty + 0.20 * ambiguity_risk
    )

    features = {
        "source_rank_risk": _round4(source_rank_risk),
        "source_rank_missing": _round4(source_rank_missing),
        "target_rank_value": _round4(target_rank_value),
        "wordnet_sense_risk": _round4(sense_risk),
        "wordnet_pos_risk": _round4(pos_risk),
        "translation_fanout_risk": _round4(translation_risk),
        "shadow_presence_risk": _round4(shadow_presence),
        "ambiguity_risk": _round4(ambiguity_risk),
        "active_evidence_gap": _round4(active_gap),
        "shadow_evidence_gap": _round4(shadow_gap),
        "phrase_evidence_gap": _round4(phrase_gap),
        "metadata_gap_rate": _round4(metadata_gap),
        "coverage_gap": _round4(coverage_gap),
        "active_low_rate": _round4(low_active_rate),
        "near_tie_rate": _round4(near_tie_rate),
        "phrase_near_best_rate": _round4(phrase_near_best_rate),
        "phrase_surface_pattern_rate": _round4(phrase_surface_rate),
        "decision_uncertainty": _round4(decision_uncertainty),
        "expected_fixability": _round4(expected_fixability),
    }
    forbidden = set(features).intersection(FORBIDDEN_RANKING_FIELDS)
    if forbidden:
        raise ValueError(f"Forbidden ranking fields leaked into features: {sorted(forbidden)}")
    return features


def _validation_shadow(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    outcomes = Counter(str(row.get("product_outcome") or "") for row in rows)
    failures = sum(outcomes.get(item, 0) for item in ERROR_OUTCOMES)
    return {
        "observed_case_count": len(rows),
        "observed_failure_count": failures,
        "observed_failure_rate": _round4(_ratio(failures, len(rows))),
        "outcome_counts": dict(sorted(outcomes.items())),
        "note": "Evaluation labels are not ranking inputs.",
    }


def _summary(
    *,
    scan_rows: Sequence[Mapping[str, object]],
    top_n: int,
    issues: Sequence[str],
) -> dict[str, object]:
    top_rows = list(scan_rows[: int(top_n)])
    source_known = sum(
        1
        for row in scan_rows
        if _safe_float(_as_mapping(row.get("programmatic_features")).get("source_rank_missing"))
        == 0.0
    )
    target_known = sum(
        1
        for row in scan_rows
        if _safe_float(_as_mapping(row.get("programmatic_features")).get("target_rank_value")) > 0.0
    )
    sense_known = sum(
        1
        for row in scan_rows
        if _safe_float(_as_mapping(row.get("programmatic_features")).get("wordnet_sense_risk"))
        > 0.0
    )
    translation_known = sum(
        1
        for row in scan_rows
        if _safe_float(_as_mapping(row.get("programmatic_features")).get("translation_fanout_risk"))
        > 0.0
    )
    return {
        "candidate_pair_count": len(scan_rows),
        "top_n": int(top_n),
        "issues": list(issues),
        "forbidden_feature_field_count": len(FORBIDDEN_RANKING_FIELDS),
        "programmatic_feature_field_count": len(PROGRAMMATIC_FEATURE_FIELDS),
        "top_static_llm_data_need": _round4(
            max((_safe_float(row.get("static_llm_data_need")) for row in scan_rows), default=0.0)
        ),
        "top_scored_context_llm_data_need": _round4(
            max(
                (_safe_float(row.get("scored_context_llm_data_need")) for row in scan_rows),
                default=0.0,
            )
        ),
        "source_rank_known_rate": _round4(_ratio(source_known, len(scan_rows))),
        "target_rank_known_rate": _round4(_ratio(target_known, len(scan_rows))),
        "wordnet_sense_known_rate": _round4(_ratio(sense_known, len(scan_rows))),
        "translation_count_known_rate": _round4(_ratio(translation_known, len(scan_rows))),
        "priority_band_counts": dict(
            sorted(Counter(str(row.get("priority_band") or "") for row in scan_rows).items())
        ),
        "recommended_llm_rows_top_n": {
            "active_rows": sum(
                int(_as_mapping(row.get("recommended_llm_packet")).get("active_rows") or 0)
                for row in top_rows
            ),
            "shadow_rows": sum(
                int(_as_mapping(row.get("recommended_llm_packet")).get("shadow_rows") or 0)
                for row in top_rows
            ),
            "phrase_rows": sum(
                int(_as_mapping(row.get("recommended_llm_packet")).get("phrase_rows") or 0)
                for row in top_rows
            ),
            "locked_eval_rows": sum(
                int(_as_mapping(row.get("recommended_llm_packet")).get("locked_eval_rows") or 0)
                for row in top_rows
            ),
        },
    }


def _issues(scan_rows: Sequence[Mapping[str, object]]) -> list[str]:
    issues = []
    if not scan_rows:
        issues.append("no_candidate_pairs")
    if any(
        not set(_as_mapping(row.get("programmatic_features"))).isdisjoint(FORBIDDEN_RANKING_FIELDS)
        for row in scan_rows
    ):
        issues.append("forbidden_ranking_field_leak")
    if not _is_sorted_by_need(scan_rows):
        issues.append("priority_rows_not_sorted")
    return issues


def _recommended_packet(
    *,
    active_need: float,
    shadow_need: float,
    phrase_need: float,
) -> dict[str, object]:
    active_rows = _budget_rows(active_need)
    shadow_rows = _budget_rows(shadow_need)
    phrase_rows = _budget_rows(phrase_need)
    total = active_rows + shadow_rows + phrase_rows
    return {
        "active_rows": active_rows,
        "shadow_rows": shadow_rows,
        "phrase_rows": phrase_rows,
        "locked_eval_rows": max(0, _budget_rows(total / 36.0, low=2, mid=4, high=6)),
        "score_components": {
            "active_need": _round4(active_need),
            "shadow_need": _round4(shadow_need),
            "phrase_need": _round4(phrase_need),
        },
    }


def _priority_reasons(
    *,
    features: Mapping[str, object],
    packet: Mapping[str, object],
) -> list[str]:
    reasons = []
    if _safe_float(features.get("source_rank_risk")) >= 0.85:
        reasons.append("high_source_exposure")
    if _safe_float(features.get("source_rank_missing")) > 0.0:
        reasons.append("missing_source_rank")
    if _safe_float(features.get("ambiguity_risk")) >= 0.55:
        reasons.append("high_programmatic_ambiguity")
    if _safe_float(features.get("coverage_gap")) >= 0.50:
        reasons.append("coverage_gap")
    if _safe_float(features.get("decision_uncertainty")) >= 0.35:
        reasons.append("score_surface_uncertainty")
    if int(packet.get("active_rows") or 0):
        reasons.append("generate_active_rows")
    if int(packet.get("shadow_rows") or 0):
        reasons.append("generate_shadow_rows")
    if int(packet.get("phrase_rows") or 0):
        reasons.append("generate_phrase_rows")
    return reasons or ["low_priority_monitor"]


def _priority_band(score: float) -> str:
    if score >= 0.45:
        return "P0"
    if score >= 0.30:
        return "P1"
    if score >= 0.18:
        return "P2"
    return "P3"


def _budget_rows(score: float, *, low: int = 4, mid: int = 8, high: int = 12) -> int:
    if score >= 0.65:
        return high
    if score >= 0.40:
        return mid
    if score >= 0.20:
        return low
    return 0


def _rank_risk_score(rank: float | None) -> float:
    if rank is None:
        return 0.0
    if rank <= 500:
        return 1.0
    if rank <= 1000:
        return 0.85
    if rank <= 2000:
        return 0.65
    if rank <= 5000:
        return 0.45
    return 0.25


def _sense_risk(count: float | None) -> float:
    if count is None:
        return 0.0
    return _clamp(log1p(max(0.0, count)) / log1p(40.0))


def _pos_risk(count: float | None) -> float:
    if count is None:
        return 0.0
    return _clamp((max(0.0, count) - 1.0) / 3.0)


def _translation_risk(count: float | None) -> float:
    if count is None:
        return 0.0
    return _clamp(max(0.0, count) / 20.0)


def _evidence_gap(count: float | None, *, target: int) -> float:
    if count is None:
        return 1.0
    return _clamp(1.0 - max(0.0, count) / float(target))


def _phrase_near_best_rate(
    *,
    active_scores: Sequence[float],
    shadow_scores: Sequence[float],
    phrase_scores: Sequence[float],
) -> float:
    count = min(len(active_scores), len(shadow_scores), len(phrase_scores))
    if count <= 0:
        return 0.0
    near = 0
    for index in range(count):
        phrase = phrase_scores[index]
        best = max(active_scores[index], shadow_scores[index])
        if phrase >= best - 0.02:
            near += 1
    return _ratio(near, count)


def _has_phrase_surface_pattern(row: Mapping[str, object]) -> bool:
    sentence = str(row.get("sentence") or "").strip().lower()
    trigger = str(row.get("trigger") or "").strip().lower()
    if not sentence or not trigger:
        return False
    return (
        sentence.startswith(f"{trigger},")
        or sentence.startswith(f"{trigger}!")
        or f"{trigger}," in sentence
        or f"{trigger}!" in sentence
        or f'"{trigger}"' in sentence
        or bool(row.get("phrase_preemption_hit"))
    )


def _number_values(rows: Sequence[Mapping[str, object]], key: str) -> list[float]:
    result = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            result.append(float(value))
    return result


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _is_sorted_by_need(rows: Sequence[Mapping[str, object]]) -> bool:
    values = [_safe_float(row.get("scored_context_llm_data_need")) for row in rows]
    return values == sorted(values, reverse=True)


def write_report(
    report: Mapping[str, object],
    *,
    json_out: Path,
    markdown_out: Path,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_llm_data_priority_scan_markdown(report), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    difficulty_path = _resolve_repo_path(args.difficulty_json)
    report = build_llm_data_priority_scan_report(
        difficulty_payload=_load_json(difficulty_path),
        difficulty_json_path=difficulty_path,
        top_n=int(args.top_n),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    write_report(report, json_out=json_out, markdown_out=markdown_out)
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
