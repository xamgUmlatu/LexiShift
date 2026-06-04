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
    _repo_path,
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_SCORING_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_MANUAL_VALIDATION_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_veto_only_validation_en_es_latest.json"
)
DEFAULT_PRODUCT_QUALITY_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_product_quality_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_failure_review_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_failure_review_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review how admitted LLM pilot scoring failures differ from the current "
            "manual/stress semantic-veto lanes and product expectations."
        )
    )
    parser.add_argument("--scoring-json", type=Path, default=DEFAULT_SCORING_JSON)
    parser.add_argument(
        "--manual-validation-json", type=Path, default=DEFAULT_MANUAL_VALIDATION_JSON
    )
    parser.add_argument("--product-quality-json", type=Path, default=DEFAULT_PRODUCT_QUALITY_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_failure_review_report(
        scoring_payload=_load_json(args.scoring_json),
        manual_validation_payload=_load_json(args.manual_validation_json),
        product_quality_payload=_load_json(args.product_quality_json)
        if args.product_quality_json.exists()
        else {},
        scoring_path=args.scoring_json,
        manual_validation_path=args.manual_validation_json,
        product_quality_path=args.product_quality_json
        if args.product_quality_json.exists()
        else None,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_failure_review_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_failure_review_report(
    *,
    scoring_payload: Mapping[str, object],
    manual_validation_payload: Mapping[str, object],
    product_quality_payload: Mapping[str, object] | None = None,
    scoring_path: Path | None = None,
    manual_validation_path: Path | None = None,
    product_quality_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    failure_cases = [
        row
        for row in _mapping_rows(scoring_payload.get("case_results"))
        if str(row.get("product_outcome") or "") in {"positive_abstain", "negative_allow"}
    ]
    class_rows = _failure_class_rows(failure_cases)
    comparison_rows = _comparison_rows(
        scoring_payload=scoring_payload,
        manual_validation_payload=manual_validation_payload,
        product_quality_payload=product_quality_payload or {},
    )
    expectation_rows = _expectation_rows(
        scoring_payload=scoring_payload,
        manual_validation_payload=manual_validation_payload,
    )
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "llm_pilot_failure_review_complete",
        "generated_at": generated_at,
        "inputs": {
            "scoring_path": _repo_path(scoring_path),
            "manual_validation_path": _repo_path(manual_validation_path),
            "product_quality_path": _repo_path(product_quality_path),
        },
        "summary": {
            "failure_count": len(failure_cases),
            "failure_outcome_counts": dict(
                sorted(
                    Counter(str(row.get("product_outcome") or "") for row in failure_cases).items()
                )
            ),
            "failure_gold_type_counts": dict(
                sorted(Counter(str(row.get("gold_type") or "") for row in failure_cases).items())
            ),
            "main_read": _main_read(expectation_rows=expectation_rows, class_rows=class_rows),
        },
        "expectation_rows": expectation_rows,
        "comparison_rows": comparison_rows,
        "failure_class_rows": class_rows,
        "trigger_failure_rows": _trigger_failure_rows(failure_cases),
        "failure_samples": _failure_samples(failure_cases),
        "interpretation": _interpretation(expectation_rows=expectation_rows, class_rows=class_rows),
        "next_steps": _next_steps(),
    }


def _comparison_rows(
    *,
    scoring_payload: Mapping[str, object],
    manual_validation_payload: Mapping[str, object],
    product_quality_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = []
    overall = _as_mapping(_as_mapping(scoring_payload.get("summary")).get("overall"))
    rows.append(_metric_row("llm_pilot_overall", overall, "LLM pilot, all admitted rows"))
    for row in _mapping_rows(scoring_payload.get("split_breakdowns")):
        rows.append(_metric_row(f"llm_pilot_split:{row.get('scope_id')}", row, "LLM pilot split"))
    for row in _mapping_rows(scoring_payload.get("gold_type_breakdowns")):
        rows.append(
            _metric_row(f"llm_pilot_gold:{row.get('scope_id')}", row, "LLM pilot gold type")
        )

    best_manual = _as_mapping(
        _as_mapping(manual_validation_payload.get("summary")).get("best_product_rank_row")
    )
    if best_manual:
        rows.append(
            _metric_row(
                "manual_stress_best_veto_only", best_manual, "Current manual/stress best row"
            )
        )
        for source in _mapping_rows(best_manual.get("source_breakdowns")):
            source_id = str(source.get("report_id") or "")
            rows.append(
                _metric_row(
                    f"manual_stress_source:{source_id}", source, "Manual/stress source breakdown"
                )
            )

    product_overall = _as_mapping(
        _as_mapping(product_quality_payload.get("summary")).get("overall")
    )
    if product_overall:
        rows.append(
            _metric_row(
                "product_quality_current_overall",
                product_overall,
                "Current product-quality aggregate",
            )
        )
    return rows


def _expectation_rows(
    *,
    scoring_payload: Mapping[str, object],
    manual_validation_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = []
    metrics_by_id = {
        str(row.get("scope_id") or ""): row
        for row in _mapping_rows(scoring_payload.get("gold_type_breakdowns"))
    }
    overall = _as_mapping(_as_mapping(scoring_payload.get("summary")).get("overall"))
    manual_best = _as_mapping(
        _as_mapping(manual_validation_payload.get("summary")).get("best_product_rank_row")
    )
    manual_sources = {
        str(row.get("report_id") or ""): row
        for row in _mapping_rows(manual_best.get("source_breakdowns"))
    }
    active_shadow_manual = _first_source_containing(manual_sources, "heldout")
    phrase_manual = _first_source_containing(manual_sources, "phrase")
    rows.append(
        _expectation(
            "positive_allow",
            "Good replacements should usually stay visible.",
            actual=_safe_float(overall.get("positive_allow_rate")),
            target=0.8,
            comparator=_optional_float(manual_best.get("positive_allow_rate")),
        )
    )
    rows.append(
        _expectation(
            "negative_abstain_overall",
            "Clearly bad replacements should be blocked at least half the time.",
            actual=_safe_float(overall.get("negative_abstain_rate")),
            target=0.5,
            comparator=_optional_float(manual_best.get("negative_abstain_rate")),
        )
    )
    rows.append(
        _expectation(
            "shadow_negative_abstain",
            "Alternate-sense negatives should often be caught by shadow evidence.",
            actual=_safe_float(
                metrics_by_id.get("shadow_negative", {}).get("negative_abstain_rate")
            ),
            target=0.5,
            comparator=_optional_float(active_shadow_manual.get("negative_abstain_rate")),
        )
    )
    rows.append(
        _expectation(
            "phrase_no_winner_abstain",
            "Phrase/no-winner rows should remain visible as their own safety class.",
            actual=_safe_float(
                metrics_by_id.get("phrase_no_winner", {}).get("negative_abstain_rate")
            ),
            target=0.5,
            comparator=_optional_float(phrase_manual.get("negative_abstain_rate")),
        )
    )
    return rows


def _failure_class_rows(failure_cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in failure_cases:
        grouped[_failure_class(row)].append(row)
    output = []
    for class_id, rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        output.append(
            {
                "failure_class": class_id,
                "case_count": len(rows),
                "gold_type_counts": dict(
                    sorted(Counter(str(row.get("gold_type") or "") for row in rows).items())
                ),
                "trigger_counts": dict(
                    sorted(Counter(str(row.get("trigger") or "") for row in rows).items())
                ),
                "median_shadow_lead": _median(_safe_float(row.get("shadow_lead")) for row in rows),
                "median_phrase_lead_to_best": _median(
                    _safe_float(row.get("phrase_lead_to_best")) for row in rows
                ),
                "sample_case_ids": [str(row.get("case_id") or "") for row in rows[:6]],
            }
        )
    return output


def _failure_class(row: Mapping[str, object]) -> str:
    outcome = str(row.get("product_outcome") or "")
    gold_type = str(row.get("gold_type") or "")
    reason = str(row.get("veto_reason") or "")
    shadow_lead = _safe_float(row.get("shadow_lead"))
    phrase_lead = _safe_float(row.get("phrase_lead_to_best"))
    if outcome == "positive_abstain":
        if reason == "phrase_score_lead":
            return "positive_overblocked_by_phrase_prototype"
        if reason == "shadow_lead":
            return "positive_overblocked_by_shadow_score"
        return "positive_overblocked_other"
    if gold_type == "phrase_no_winner":
        if phrase_lead < 0:
            return "phrase_no_winner_phrase_score_not_dominant"
        return "phrase_no_winner_phrase_threshold_missed"
    if gold_type == "shadow_negative":
        if shadow_lead < 0:
            return "shadow_negative_active_score_dominated"
        if shadow_lead < 0.05:
            return "shadow_negative_shadow_lead_below_threshold"
        return "shadow_negative_policy_threshold_missed"
    return "negative_allow_other"


def _trigger_failure_rows(failure_cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in failure_cases:
        grouped[str(row.get("trigger") or "")].append(row)
    return [
        {
            "trigger": trigger,
            "failure_count": len(rows),
            "outcome_counts": dict(
                sorted(Counter(str(row.get("product_outcome") or "") for row in rows).items())
            ),
            "gold_type_counts": dict(
                sorted(Counter(str(row.get("gold_type") or "") for row in rows).items())
            ),
            "sample_case_ids": [str(row.get("case_id") or "") for row in rows[:4]],
        }
        for trigger, rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def _failure_samples(failure_cases: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "case_id": str(row.get("case_id") or ""),
            "split": str(row.get("split") or ""),
            "gold_type": str(row.get("gold_type") or ""),
            "trigger": str(row.get("trigger") or ""),
            "product_outcome": str(row.get("product_outcome") or ""),
            "failure_class": _failure_class(row),
            "veto_reason": str(row.get("veto_reason") or ""),
            "active_score": row.get("active_score"),
            "strongest_shadow_score": row.get("strongest_shadow_score"),
            "phrase_control_score": row.get("phrase_control_score"),
            "shadow_lead": row.get("shadow_lead"),
            "phrase_lead_to_best": row.get("phrase_lead_to_best"),
            "sentence": str(row.get("sentence") or ""),
        }
        for row in failure_cases
    ]


def render_failure_review_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto LLM Pilot Failure Review",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Failure count: `{summary.get('failure_count', 0)}`",
        f"- Main read: {summary.get('main_read', '')}",
        "",
        "## Expectation Check",
        "",
        _expectation_table(report.get("expectation_rows")),
        "",
        "## Comparison Rows",
        "",
        _comparison_table(report.get("comparison_rows")),
        "",
        "## Failure Classes",
        "",
        _class_table(report.get("failure_class_rows")),
        "",
        "## Trigger Failures",
        "",
        _trigger_table(report.get("trigger_failure_rows")),
        "",
        "## Samples",
        "",
        _sample_table(report.get("failure_samples")),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in _as_sequence(report.get("interpretation")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _main_read(
    *,
    expectation_rows: Sequence[Mapping[str, object]],
    class_rows: Sequence[Mapping[str, object]],
) -> str:
    weak = [
        str(row.get("expectation_id") or "")
        for row in expectation_rows
        if str(row.get("status") or "") in {"below_target", "below_manual_comparator"}
    ]
    largest_class = class_rows[0]["failure_class"] if class_rows else "none"
    return (
        "The LLM pilot keeps positive replacements visible, but negative blocking is weaker "
        f"than manual/stress comparators; the largest failure class is `{largest_class}`. "
        f"Weak expectations: {', '.join(weak) or 'none'}."
    )


def _interpretation(
    *,
    expectation_rows: Sequence[Mapping[str, object]],
    class_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    rows_by_id = {str(row.get("expectation_id") or ""): row for row in expectation_rows}
    interpretation = [
        "The pilot is not lower in every way: positive allow beats the 80% target and the current manual/stress comparator.",
        "The worrying gap is negative blocking. Overall negative abstain barely clears the 50% target and is well below the manual/stress best row.",
    ]
    phrase = rows_by_id.get("phrase_no_winner_abstain", {})
    if str(phrase.get("status") or "") != "meets_target_and_comparator":
        interpretation.append(
            "Phrase/no-winner is the clearest miss: its abstain rate is below target and below the manual phrase-source comparator."
        )
    shadow = rows_by_id.get("shadow_negative_abstain", {})
    if str(shadow.get("status") or "") != "meets_target_and_comparator":
        interpretation.append(
            "Shadow-negative rows pass the minimum target but lag the manual active/shadow comparator, so the issue is not only phrase handling."
        )
    if class_rows:
        interpretation.append(
            "Most failures are no-veto negative allows, meaning the active/shadow/phrase scores did not produce a strong enough blocker rather than a blocker firing incorrectly."
        )
    return interpretation


def _next_steps() -> list[str]:
    return [
        "Review the no-veto negative-allow rows first; they show whether source evidence, context representation, or threshold shape is the limiting factor.",
        "Keep phrase/no-winner separate from shadow-negative rows; the phrase class is below target even while the aggregate passes.",
        "Do not interpret the small locked-eval pass as enough to justify full-scale generation; expand only after the discovered failure classes are understood.",
    ]


def _expectation(
    expectation_id: str,
    description: str,
    *,
    actual: float,
    target: float,
    comparator: float | None,
) -> dict[str, object]:
    target_delta = None if actual is None else round(actual - target, 4)
    comparator_delta = None if comparator is None else round(actual - comparator, 4)
    if actual < target:
        status = "below_target"
    elif comparator is not None and actual < comparator:
        status = "below_manual_comparator"
    else:
        status = "meets_target_and_comparator"
    return {
        "expectation_id": expectation_id,
        "description": description,
        "actual_rate": round(actual, 4),
        "target_rate": target,
        "target_delta": target_delta,
        "manual_comparator_rate": comparator,
        "manual_comparator_delta": comparator_delta,
        "status": status,
    }


def _metric_row(scope_id: str, metrics: Mapping[str, object], note: str) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "note": note,
        "case_count": metrics.get("case_count"),
        "positive_allow_count": metrics.get("positive_allow_count"),
        "positive_abstain_count": metrics.get("positive_abstain_count"),
        "negative_abstain_count": metrics.get("negative_abstain_count"),
        "negative_allow_count": metrics.get("negative_allow_count"),
        "positive_allow_rate": metrics.get("positive_allow_rate"),
        "negative_abstain_rate": metrics.get("negative_abstain_rate"),
        "utility_score": metrics.get("utility_score"),
        "target_status": str(
            _as_mapping(metrics.get("target_checks")).get("target_status")
            or metrics.get("target_status")
            or ""
        ),
    }


def _expectation_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Expectation | Actual | Target | Manual comparator | Delta vs target | Delta vs manual | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("expectation_id") or "")),
                    _format_percent(row.get("actual_rate")),
                    _format_percent(row.get("target_rate")),
                    _format_percent(row.get("manual_comparator_rate")),
                    _format_signed_rate(row.get("target_delta")),
                    _format_signed_rate(row.get("manual_comparator_delta")),
                    _escape_md(str(row.get("status") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _comparison_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No rows._"
    lines = [
        "| Scope | Cases | Pos allow | Neg abstain | Utility | Target | Note |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("scope_id") or "")),
                    str(row.get("case_count") or ""),
                    _format_percent(row.get("positive_allow_rate")),
                    _format_percent(row.get("negative_abstain_rate")),
                    str(row.get("utility_score") or ""),
                    _escape_md(str(row.get("target_status") or "")),
                    _escape_md(str(row.get("note") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _class_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No classes._"
    lines = [
        "| Class | Cases | Gold types | Triggers | Median shadow lead | Median phrase lead | Samples |",
        "| --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("failure_class") or "")),
                    str(row.get("case_count") or 0),
                    _escape_md(_counter_text(row.get("gold_type_counts"))),
                    _escape_md(_counter_text(row.get("trigger_counts"))),
                    str(row.get("median_shadow_lead")),
                    str(row.get("median_phrase_lead_to_best")),
                    _escape_md(", ".join(str(v) for v in _as_sequence(row.get("sample_case_ids")))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _trigger_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No trigger failures._"
    lines = [
        "| Trigger | Failures | Outcomes | Gold types | Samples |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("trigger") or "")),
                    str(row.get("failure_count") or 0),
                    _escape_md(_counter_text(row.get("outcome_counts"))),
                    _escape_md(_counter_text(row.get("gold_type_counts"))),
                    _escape_md(", ".join(str(v) for v in _as_sequence(row.get("sample_case_ids")))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sample_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No samples._"
    lines = [
        "| Case | Gold | Trigger | Outcome | Class | Active | Shadow | Phrase | Sentence |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:30]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md(str(row.get("case_id") or "")),
                    _escape_md(str(row.get("gold_type") or "")),
                    _escape_md(str(row.get("trigger") or "")),
                    _escape_md(str(row.get("product_outcome") or "")),
                    _escape_md(str(row.get("failure_class") or "")),
                    str(row.get("active_score") or ""),
                    str(row.get("strongest_shadow_score") or ""),
                    str(row.get("phrase_control_score") or ""),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _first_source_containing(
    manual_sources: Mapping[str, Mapping[str, object]],
    text: str,
) -> Mapping[str, object]:
    if text == "phrase":
        for key, row in sorted(manual_sources.items()):
            if key.endswith("_phrase") or key.endswith("_phrase_validation"):
                return row
    for key, row in sorted(manual_sources.items()):
        if text in key:
            return row
    return {}


def _counter_text(value: object) -> str:
    mapping = _as_mapping(value)
    return ", ".join(f"{key}:{mapping[key]}" for key in sorted(mapping))


def _format_signed_rate(value: object) -> str:
    if value is None:
        return "n/a"
    numeric = _safe_float(value)
    sign = "+" if numeric >= 0 else ""
    return f"{sign}{numeric * 100:.1f}pp"


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return _safe_float(value)


def _median(values: Sequence[float]) -> float:
    materialized = sorted(float(value) for value in values)
    if not materialized:
        return 0.0
    middle = len(materialized) // 2
    if len(materialized) % 2:
        return round(materialized[middle], 4)
    return round((materialized[middle - 1] + materialized[middle]) / 2, 4)


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
