#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from semantic_veto_llm_pilot_failure_review_en_es import _failure_class
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _escape_md,
    _load_json,
    _repo_path,
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_SCORING_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_MANUAL_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_sentence_veto_v10.json"
)
DEFAULT_MANUAL_MATRIX_JSON = TEST_OUTPUTS_ROOT / "semantic_decision_rule_matrix_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_data_comparison_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_data_comparison_en_es_latest.md"
DEFAULT_CONFIG_ID = "control_st_masked_all_margin_phrase_override"
TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")
ARTICLE_TOKENS = {"a", "an", "the"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare failed LLM pilot rows with same-family manual v10 cases and "
            "the source evidence that scored each failed row."
        )
    )
    parser.add_argument("--scoring-json", type=Path, default=DEFAULT_SCORING_JSON)
    parser.add_argument("--manual-dataset-json", type=Path, default=DEFAULT_MANUAL_DATASET_JSON)
    parser.add_argument("--manual-matrix-json", type=Path, default=DEFAULT_MANUAL_MATRIX_JSON)
    parser.add_argument("--config-id", default=DEFAULT_CONFIG_ID)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_data_comparison_report(
        scoring_payload=_load_json(args.scoring_json),
        manual_dataset_payload=_load_json(args.manual_dataset_json),
        manual_matrix_payload=_load_json(args.manual_matrix_json),
        scoring_path=args.scoring_json,
        manual_dataset_path=args.manual_dataset_json,
        manual_matrix_path=args.manual_matrix_json,
        config_id=args.config_id,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_data_comparison_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_data_comparison_report(
    *,
    scoring_payload: Mapping[str, object],
    manual_dataset_payload: Mapping[str, object],
    manual_matrix_payload: Mapping[str, object],
    scoring_path: Path | None = None,
    manual_dataset_path: Path | None = None,
    manual_matrix_path: Path | None = None,
    config_id: str = DEFAULT_CONFIG_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    manual_families = {
        str(family.get("family_id") or ""): family
        for family in _mapping_rows(manual_dataset_payload.get("families"))
    }
    manual_results = {
        str(row.get("case_id") or ""): row
        for row in _mapping_rows(manual_matrix_payload.get("case_results"))
        if str(row.get("config_id") or "") == config_id
    }
    failures = [
        row
        for row in _mapping_rows(scoring_payload.get("case_results"))
        if str(row.get("product_outcome") or "") in {"positive_abstain", "negative_allow"}
    ]
    comparisons = [
        _comparison_row(
            failure=row,
            manual_family=_as_mapping(manual_families.get(str(row.get("family_id") or ""))),
            manual_results=manual_results,
        )
        for row in failures
    ]
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "llm_manual_failed_case_data_comparison_complete",
        "generated_at": generated_at,
        "inputs": {
            "scoring_path": _repo_path(scoring_path),
            "manual_dataset_path": _repo_path(manual_dataset_path),
            "manual_matrix_path": _repo_path(manual_matrix_path),
            "config_id": config_id,
        },
        "summary": _summary(comparisons),
        "comparison_rows": comparisons,
        "interpretation": _interpretation(comparisons),
    }


def _comparison_row(
    *,
    failure: Mapping[str, object],
    manual_family: Mapping[str, object],
    manual_results: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    manual_cases = _manual_case_rows(
        manual_family=manual_family,
        manual_results=manual_results,
        llm_gold_type=str(failure.get("gold_type") or ""),
    )
    source_overlap = _source_surface_overlap(failure)
    nearest = _nearest_manual_case(
        llm_sentence=str(failure.get("sentence") or failure.get("context_text") or ""),
        trigger=str(failure.get("trigger") or ""),
        manual_cases=manual_cases,
    )
    return {
        "case_id": str(failure.get("case_id") or ""),
        "family_id": str(failure.get("family_id") or ""),
        "trigger": str(failure.get("trigger") or ""),
        "gold_type": str(failure.get("gold_type") or ""),
        "product_outcome": str(failure.get("product_outcome") or ""),
        "failure_class": _failure_class(failure),
        "llm_sentence": str(failure.get("sentence") or ""),
        "llm_context": str(failure.get("context_text") or ""),
        "llm_scores": {
            "active": failure.get("active_score"),
            "shadow": failure.get("strongest_shadow_score"),
            "phrase": failure.get("phrase_control_score"),
            "shadow_lead": failure.get("shadow_lead"),
            "phrase_lead_to_best": failure.get("phrase_lead_to_best"),
            "veto_reason": str(failure.get("veto_reason") or ""),
        },
        "source_evidence_used": {
            "active": str(failure.get("active_evidence_text") or ""),
            "shadow": str(failure.get("strongest_shadow_evidence_text") or ""),
            "phrase": str(failure.get("phrase_control_evidence_text") or ""),
        },
        "source_overlap": source_overlap,
        "manual_matching_cases": manual_cases,
        "manual_matching_summary": _manual_matching_summary(manual_cases),
        "nearest_manual_matching_case": nearest,
        "data_difference": _data_difference(
            failure=failure,
            manual_cases=manual_cases,
            nearest=nearest,
            source_overlap=source_overlap,
        ),
    }


def _manual_case_rows(
    *,
    manual_family: Mapping[str, object],
    manual_results: Mapping[str, Mapping[str, object]],
    llm_gold_type: str,
) -> list[dict[str, object]]:
    rows = []
    for case in _mapping_rows(manual_family.get("cases")):
        result = _as_mapping(manual_results.get(str(case.get("case_id") or "")))
        winner_type = str(result.get("gold_winner_type") or _manual_gold_type(case, manual_family))
        if not _manual_case_matches_llm_gold_type(
            winner_type, str(case.get("slice_tags") or ""), llm_gold_type
        ):
            continue
        rows.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "sentence": str(case.get("sentence") or ""),
                "gold_winner_type": winner_type,
                "gold_decision": str(
                    result.get("gold_decision") or case.get("gold_decision") or ""
                ),
                "predicted_decision": str(result.get("predicted_decision") or ""),
                "product_outcome": _product_outcome(
                    gold=str(result.get("gold_decision") or case.get("gold_decision") or ""),
                    predicted=str(result.get("predicted_decision") or ""),
                ),
                "active_score": result.get("active_score"),
                "strongest_shadow_score": result.get("strongest_shadow_score"),
                "phrase_preemption_hit": bool(result.get("phrase_preemption_hit")),
                "context_text": str(result.get("context_text") or ""),
                "slice_tags": [str(tag) for tag in _as_sequence(case.get("slice_tags"))],
            }
        )
    return rows


def _manual_case_matches_llm_gold_type(
    winner_type: str,
    slice_tags_text: str,
    llm_gold_type: str,
) -> bool:
    if llm_gold_type == "positive_active":
        return winner_type == "active"
    if llm_gold_type == "shadow_negative":
        return winner_type == "shadow"
    if llm_gold_type == "phrase_no_winner":
        return winner_type == "none" or "phrase_control" in slice_tags_text
    return False


def _manual_gold_type(case: Mapping[str, object], family: Mapping[str, object]) -> str:
    gold = str(case.get("gold_winner") or "")
    active = _as_mapping(family.get("active"))
    if gold == str(active.get("sense_id") or ""):
        return "active"
    if gold == "none":
        return "none"
    return "shadow"


def _manual_matching_summary(manual_cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    outcomes = Counter(str(row.get("product_outcome") or "") for row in manual_cases)
    return {
        "case_count": len(manual_cases),
        "manual_predicted_replace_count": sum(
            1 for row in manual_cases if str(row.get("predicted_decision") or "") == "replace"
        ),
        "manual_predicted_abstain_count": sum(
            1 for row in manual_cases if str(row.get("predicted_decision") or "") == "abstain"
        ),
        "manual_failure_count": outcomes.get("positive_abstain", 0)
        + outcomes.get("negative_allow", 0),
        "manual_outcome_counts": dict(sorted(outcomes.items())),
    }


def _nearest_manual_case(
    *,
    llm_sentence: str,
    trigger: str,
    manual_cases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    if not manual_cases:
        return {}
    scored = [
        (
            _surface_similarity(llm_sentence, str(row.get("sentence") or ""), trigger),
            row,
        )
        for row in manual_cases
    ]
    surface, row = sorted(
        scored,
        key=lambda item: (
            -_safe_float(item[0].get("composite_similarity")),
            str(item[1].get("case_id") or ""),
        ),
    )[0]
    return {
        "case_id": str(row.get("case_id") or ""),
        "sentence": str(row.get("sentence") or ""),
        "composite_similarity": surface.get("composite_similarity"),
        "token_jaccard": surface.get("token_jaccard"),
        "ordered_bigram_jaccard": surface.get("ordered_bigram_jaccard"),
        "trigger_neighbor_overlap": surface.get("trigger_neighbor_overlap"),
        "trigger_window_llm": surface.get("left_trigger_window"),
        "trigger_window_manual": surface.get("right_trigger_window"),
        "predicted_decision": str(row.get("predicted_decision") or ""),
        "product_outcome": str(row.get("product_outcome") or ""),
        "active_score": row.get("active_score"),
        "strongest_shadow_score": row.get("strongest_shadow_score"),
    }


def _source_surface_overlap(failure: Mapping[str, object]) -> dict[str, object]:
    sentence = str(failure.get("sentence") or failure.get("context_text") or "")
    trigger = str(failure.get("trigger") or "")
    overlaps = {
        "active": _surface_similarity(
            sentence, str(failure.get("active_evidence_text") or ""), trigger
        ),
        "shadow": _surface_similarity(
            sentence, str(failure.get("strongest_shadow_evidence_text") or ""), trigger
        ),
        "phrase": _surface_similarity(
            sentence, str(failure.get("phrase_control_evidence_text") or ""), trigger
        ),
    }
    largest = max(
        overlaps,
        key=lambda key: _safe_float(_as_mapping(overlaps[key]).get("composite_similarity")),
    )
    return {
        "active": overlaps["active"],
        "shadow": overlaps["shadow"],
        "phrase": overlaps["phrase"],
        "largest_surface_overlap": largest,
        "score_winner": _best_score_source(failure),
    }


def _data_difference(
    *,
    failure: Mapping[str, object],
    manual_cases: Sequence[Mapping[str, object]],
    nearest: Mapping[str, object],
    source_overlap: Mapping[str, object],
) -> dict[str, object]:
    failure_class = _failure_class(failure)
    manual_summary = _manual_matching_summary(manual_cases)
    notes = []
    if manual_summary["manual_failure_count"] == 0 and manual_summary["case_count"]:
        notes.append("same_family_manual_matching_rows_passed_under_control")
    elif manual_summary["manual_failure_count"]:
        notes.append("same_family_manual_matching_rows_also_have_failures")
    score_winner = str(source_overlap.get("score_winner") or "")
    surface_winner = str(source_overlap.get("largest_surface_overlap") or "")
    if score_winner == "active" and str(failure.get("product_outcome") or "") == "negative_allow":
        notes.append("scorer_chose_active_evidence_over_blocker")
    if surface_winner and score_winner and surface_winner != score_winner:
        notes.append("surface_pattern_points_to_different_source_than_score_winner")
    if failure_class == "shadow_negative_active_score_dominated":
        notes.append("shadow_negative_was_scored_as_active_like")
    if failure_class == "phrase_no_winner_phrase_score_not_dominant":
        notes.append("phrase_prototype_did_not_cover_this_expression_strongly_enough")
        if surface_winner == "phrase":
            notes.append("phrase_surface_pattern_visible_but_not_weighted_enough")
    if failure_class == "positive_overblocked_by_phrase_prototype":
        notes.append("positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win")
    if failure_class == "positive_overblocked_by_shadow_score":
        notes.append("positive_sentence_was_generic_enough_for_shadow_evidence_to_win")
    nearest_score = _safe_float(nearest.get("composite_similarity"))
    if manual_cases and nearest_score < 0.08:
        notes.append("llm_sentence_is_lexically_far_from_manual_same_class_examples")
    confidence = _diagnosis_confidence(notes)
    return {
        "obvious_from_data": confidence in {"high", "medium"},
        "diagnosis_confidence": confidence,
        "notes": notes,
        "short_read": _short_read(notes),
    }


def _short_read(notes: Sequence[str]) -> str:
    if not notes:
        return "No obvious data-level difference was detected by the automatic comparison."
    if "phrase_surface_pattern_visible_but_not_weighted_enough" in notes:
        return "The phrase shape is visible in the words, but the semantic score still did not let phrase evidence win."
    if "scorer_chose_active_evidence_over_blocker" in notes:
        return "The scorer chose active evidence over the intended blocker evidence."
    if "phrase_prototype_did_not_cover_this_expression_strongly_enough" in notes:
        return "The LLM phrase/no-winner expression is not well covered by the available phrase prototype."
    if "same_family_manual_matching_rows_also_have_failures" in notes:
        return "The manual same-class rows already expose a similar weakness, so this is not purely an LLM-data regression."
    if "positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win" in notes:
        return "The LLM positive row is short or generic enough that phrase evidence beats it."
    if "positive_sentence_was_generic_enough_for_shadow_evidence_to_win" in notes:
        return "The LLM positive row is generic enough that shadow evidence beats it."
    return "The same-family manual examples look easier or more directly aligned with the available evidence."


def _diagnosis_confidence(notes: Sequence[str]) -> str:
    strong = {
        "scorer_chose_active_evidence_over_blocker",
        "phrase_surface_pattern_visible_but_not_weighted_enough",
        "positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win",
        "positive_sentence_was_generic_enough_for_shadow_evidence_to_win",
    }
    if any(note in strong for note in notes):
        return "high"
    if notes:
        return "medium"
    return "low"


def _surface_similarity(left: str, right: str, trigger: str) -> dict[str, object]:
    left_tokens = _ordered_tokens(_normalize_trigger_blanks(left, trigger))
    right_tokens = _ordered_tokens(_normalize_trigger_blanks(right, trigger))
    token_jaccard = _set_jaccard(_content_token_set(left_tokens), _content_token_set(right_tokens))
    bigram_jaccard = _set_jaccard(set(_ngrams(left_tokens, 2)), set(_ngrams(right_tokens, 2)))
    left_window = _trigger_window(left_tokens, trigger)
    right_window = _trigger_window(right_tokens, trigger)
    neighbor_overlap = _set_jaccard(
        set(_as_sequence(left_window.get("left")) + _as_sequence(left_window.get("right"))),
        set(_as_sequence(right_window.get("left")) + _as_sequence(right_window.get("right"))),
    )
    composite = (token_jaccard + (2 * bigram_jaccard) + neighbor_overlap) / 4
    return {
        "composite_similarity": round(composite, 4),
        "token_jaccard": round(token_jaccard, 4),
        "ordered_bigram_jaccard": round(bigram_jaccard, 4),
        "trigger_neighbor_overlap": round(neighbor_overlap, 4),
        "left_trigger_window": left_window,
        "right_trigger_window": right_window,
    }


def _normalize_trigger_blanks(value: str, trigger: str) -> str:
    normalized = str(value or "")
    if trigger:
        normalized = normalized.replace("___", trigger)
    return normalized


def _ordered_tokens(value: str) -> list[str]:
    return [token.casefold() for token in TOKEN_RE.findall(str(value or ""))]


def _content_token_set(tokens: Sequence[str]) -> set[str]:
    return {token for token in tokens if token not in ARTICLE_TOKENS}


def _ngrams(tokens: Sequence[str], size: int) -> list[tuple[str, ...]]:
    if size <= 0 or len(tokens) < size:
        return []
    return [tuple(tokens[index : index + size]) for index in range(0, len(tokens) - size + 1)]


def _trigger_window(tokens: Sequence[str], trigger: str) -> dict[str, object]:
    normalized_trigger = str(trigger or "").casefold()
    if not normalized_trigger:
        return {"left": [], "right": []}
    try:
        index = list(tokens).index(normalized_trigger)
    except ValueError:
        return {"left": [], "right": []}
    return {
        "left": list(tokens[max(0, index - 2) : index]),
        "right": list(tokens[index + 1 : index + 3]),
    }


def _set_jaccard(left: set[object], right: set[object]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _best_score_source(failure: Mapping[str, object]) -> str:
    scores = {
        "active": _safe_float(failure.get("active_score")),
        "shadow": _safe_float(failure.get("strongest_shadow_score")),
        "phrase": _safe_float(failure.get("phrase_control_score")),
    }
    return max(scores, key=lambda key: (scores[key], key))


def render_data_comparison_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM vs Manual Failed-Case Data Comparison",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Failed LLM rows compared: `{summary.get('failed_llm_case_count', 0)}`",
        f"- Manual rows referenced: `{summary.get('manual_matching_case_count', 0)}`",
        f"- Obvious data-difference rows: `{summary.get('obvious_data_difference_count', 0)}`",
        "",
        "## Summary",
        "",
        _summary_table(summary),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("interpretation")))
    lines.extend(["", "## Case Comparisons", ""])
    for row in _mapping_rows(report.get("comparison_rows")):
        lines.extend(_case_section(row))
    return "\n".join(lines) + "\n"


def _case_section(row: Mapping[str, object]) -> list[str]:
    data_diff = _as_mapping(row.get("data_difference"))
    scores = _as_mapping(row.get("llm_scores"))
    evidence = _as_mapping(row.get("source_evidence_used"))
    source_overlap = _as_mapping(row.get("source_overlap"))
    nearest = _as_mapping(row.get("nearest_manual_matching_case"))
    manual_summary = _as_mapping(row.get("manual_matching_summary"))
    return [
        f"### `{row.get('case_id', '')}`",
        "",
        f"- Trigger/gold/outcome: `{row.get('trigger', '')}` / `{row.get('gold_type', '')}` / `{row.get('product_outcome', '')}`",
        f"- Failure class: `{row.get('failure_class', '')}`",
        f"- Diagnosis confidence: `{data_diff.get('diagnosis_confidence', '')}`",
        f"- Short read: {data_diff.get('short_read', '')}",
        f"- Notes: `{', '.join(str(v) for v in _as_sequence(data_diff.get('notes'))) or 'none'}`",
        f"- LLM sentence: {_escape_md(str(row.get('llm_sentence') or ''))}",
        f"- LLM context: `{_escape_md(str(row.get('llm_context') or ''))}`",
        f"- Scores: active `{scores.get('active', '')}`, shadow `{scores.get('shadow', '')}`, phrase `{scores.get('phrase', '')}`, shadow lead `{scores.get('shadow_lead', '')}`, phrase lead `{scores.get('phrase_lead_to_best', '')}`",
        f"- Score winner vs surface-pattern winner: `{source_overlap.get('score_winner', '')}` / `{source_overlap.get('largest_surface_overlap', '')}`",
        f"- Source active: `{_escape_md(str(evidence.get('active') or ''))}`",
        f"- Source shadow: `{_escape_md(str(evidence.get('shadow') or ''))}`",
        f"- Source phrase: `{_escape_md(str(evidence.get('phrase') or ''))}`",
        "- Nearest manual same-class row: "
        f"`{nearest.get('case_id', '')}` composite `{nearest.get('composite_similarity', '')}`, "
        f"bigram `{nearest.get('ordered_bigram_jaccard', '')}`, "
        f"neighbor `{nearest.get('trigger_neighbor_overlap', '')}` - "
        f"{_escape_md(str(nearest.get('sentence') or ''))}",
        "- Manual same-class summary: "
        f"`{manual_summary.get('case_count', 0)}` rows, "
        f"`{manual_summary.get('manual_failure_count', 0)}` manual failures under control",
        "",
        _manual_table(row.get("manual_matching_cases")),
        "",
    ]


def _manual_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No matching manual rows._"
    lines = [
        "| Manual case | Gold | Predicted | Active | Shadow | Sentence |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("gold_winner_type") or "")),
                    _escape_md(str(row.get("predicted_decision") or "")),
                    str(row.get("active_score") or ""),
                    str(row.get("strongest_shadow_score") or ""),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _summary(comparisons: Sequence[Mapping[str, object]]) -> dict[str, object]:
    class_counts = Counter(str(row.get("failure_class") or "") for row in comparisons)
    confidence_counts = Counter(
        str(_as_mapping(row.get("data_difference")).get("diagnosis_confidence") or "")
        for row in comparisons
    )
    note_counts = Counter(
        str(note)
        for row in comparisons
        for note in _as_sequence(_as_mapping(row.get("data_difference")).get("notes"))
    )
    return {
        "failed_llm_case_count": len(comparisons),
        "manual_matching_case_count": sum(
            len(_mapping_rows(row.get("manual_matching_cases"))) for row in comparisons
        ),
        "obvious_data_difference_count": sum(
            1
            for row in comparisons
            if _as_mapping(row.get("data_difference")).get("obvious_from_data")
        ),
        "diagnosis_confidence_counts": dict(sorted(confidence_counts.items())),
        "failure_class_counts": dict(sorted(class_counts.items())),
        "data_difference_note_counts": dict(sorted(note_counts.items())),
    }


def _summary_table(summary: Mapping[str, object]) -> str:
    lines = ["| Item | Value |", "| --- | --- |"]
    for key in (
        "failed_llm_case_count",
        "manual_matching_case_count",
        "obvious_data_difference_count",
    ):
        lines.append(f"| `{key}` | `{summary.get(key, '')}` |")
    lines.append(
        f"| `failure_class_counts` | `{_counter_text(summary.get('failure_class_counts'))}` |"
    )
    lines.append(
        "| `diagnosis_confidence_counts` | "
        f"`{_counter_text(summary.get('diagnosis_confidence_counts'))}` |"
    )
    lines.append(
        f"| `data_difference_note_counts` | `{_counter_text(summary.get('data_difference_note_counts'))}` |"
    )
    return "\n".join(lines)


def _interpretation(comparisons: Sequence[Mapping[str, object]]) -> list[str]:
    obvious_count = sum(
        1 for row in comparisons if _as_mapping(row.get("data_difference")).get("obvious_from_data")
    )
    class_counts = Counter(str(row.get("failure_class") or "") for row in comparisons)
    confidence_counts = Counter(
        str(_as_mapping(row.get("data_difference")).get("diagnosis_confidence") or "")
        for row in comparisons
    )
    return [
        f"The automatic comparison found medium/high-confidence data explanations for {obvious_count} / {len(comparisons)} failed LLM rows.",
        f"Diagnosis confidence counts: {_counter_text(dict(sorted(confidence_counts.items())))}.",
        "The repeated pattern is that LLM-generated negative rows often leave the narrow manual/source evidence lane or expose phrase shapes whose word order is visible but whose semantic score is not dominant enough.",
        "Several LLM rows are not simply harder examples; they expose source-coverage or label-scope questions, especially for `plant`, `check`, `order`, `match`, and phrase/no-winner rows.",
        f"Largest failure classes: {_counter_text(dict(sorted(class_counts.items())))}.",
    ]


def _product_outcome(*, gold: str, predicted: str) -> str:
    normalized_gold = str(gold or "").strip()
    normalized_predicted = str(predicted or "").strip()
    if not normalized_predicted:
        return ""
    product_class = "positive" if normalized_gold == "replace" else "negative"
    user_outcome = "allow" if normalized_predicted == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _counter_text(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}:{mapping[key]}" for key in sorted(mapping)) or "none"


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
