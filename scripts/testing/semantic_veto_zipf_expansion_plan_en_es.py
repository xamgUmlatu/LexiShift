#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    _safe_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

DEFAULT_REPRESENTATIVE_BAND_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_representative_band_performance_en_es_latest.json"
)
DEFAULT_DIFFICULTY_STRATIFICATION = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_zipf_expansion_plan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_zipf_expansion_plan_en_es_latest.md"

ZIPF_BANDS = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
)
MIN_CASES_PER_REPRESENTATIVE_BAND = 40
MIN_POSITIVES_PER_REPRESENTATIVE_BAND = 20
MIN_NEGATIVES_PER_REPRESENTATIVE_BAND = 20
MIN_TRIGGERS_PER_REPRESENTATIVE_BAND = 6


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan the next representative semantic-veto expansion around Zipf frequency "
            "bands. This is diagnostic-only and does not generate LLM rows."
        )
    )
    parser.add_argument(
        "--representative-band-json",
        type=Path,
        default=DEFAULT_REPRESENTATIVE_BAND_REPORT,
    )
    parser.add_argument(
        "--difficulty-stratification-json",
        type=Path,
        default=DEFAULT_DIFFICULTY_STRATIFICATION,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_zipf_expansion_plan_report(
        representative_band_payload=_load_json(args.representative_band_json),
        difficulty_payload=_load_json(args.difficulty_stratification_json),
        representative_band_path=args.representative_band_json,
        difficulty_path=args.difficulty_stratification_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_zipf_expansion_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_zipf_expansion_plan_report(
    *,
    representative_band_payload: Mapping[str, object],
    difficulty_payload: Mapping[str, object],
    representative_band_path: Path | None = None,
    difficulty_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    representative_rows = _zipf_breakdowns(representative_band_payload)
    difficulty_rows = {
        str(row.get("scope_id") or ""): row
        for row in _mapping_rows(difficulty_payload.get("source_zipf_breakdowns_en"))
    }
    trigger_rows = _mapping_rows(representative_band_payload.get("trigger_risk_summary"))
    issues = []
    if not representative_rows:
        issues.append("representative_band_report_has_no_zipf_breakdowns")
    expansion_rows = [
        _expansion_row(
            band=band,
            representative=_as_mapping(representative_rows.get(band)),
            overall=_as_mapping(difficulty_rows.get(band)),
            trigger_rows=trigger_rows,
        )
        for band in ZIPF_BANDS
    ]
    expansion_rows = sorted(expansion_rows, key=_expansion_sort_key)
    return {
        "schema_version": 1,
        "pair": str(
            representative_band_payload.get("pair") or difficulty_payload.get("pair") or "en-es"
        ),
        "status": "review" if issues else "ok",
        "decision": "zipf_expansion_plan_established"
        if not issues
        else "zipf_expansion_plan_incomplete",
        "generated_at": generated_at,
        "inputs": {
            "representative_band_path": _repo_path(representative_band_path),
            "representative_band_decision": str(representative_band_payload.get("decision") or ""),
            "difficulty_stratification_path": _repo_path(difficulty_path),
            "difficulty_stratification_decision": str(difficulty_payload.get("decision") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "goal": (
                "Choose the next representative rows and future LLM budget by Zipf band "
                "without using targeted stress rows as product-distribution evidence."
            ),
            "minimum_representative_targets": {
                "cases_per_band": MIN_CASES_PER_REPRESENTATIVE_BAND,
                "positive_cases_per_band": MIN_POSITIVES_PER_REPRESENTATIVE_BAND,
                "negative_cases_per_band": MIN_NEGATIVES_PER_REPRESENTATIVE_BAND,
                "triggers_per_band": MIN_TRIGGERS_PER_REPRESENTATIVE_BAND,
            },
            "priority_rule": (
                "Prioritize bands with representative shortfall, high positive abstain mass, "
                "or strong disagreement between representative and all-lane Zipf behavior."
            ),
        },
        "summary": {
            "issues": issues,
            "represented_zipf_band_count": sum(
                1 for row in expansion_rows if int(row.get("representative_case_count") or 0) > 0
            ),
            "planned_zipf_band_count": len(ZIPF_BANDS),
            "p0_band_count": sum(1 for row in expansion_rows if row.get("priority") == "P0"),
            "recommended_manual_or_observed_rows": sum(
                int(row.get("recommended_manual_or_observed_rows") or 0) for row in expansion_rows
            ),
            "recommended_llm_discovery_rows": sum(
                int(row.get("recommended_llm_discovery_rows") or 0) for row in expansion_rows
            ),
            "recommended_locked_eval_rows": sum(
                int(row.get("recommended_locked_eval_rows") or 0) for row in expansion_rows
            ),
        },
        "expansion_rows": expansion_rows,
        "limitations": [
            "zipf_band_plan_is_not_a_runtime_policy_change",
            "representative_proxy_still_needs_human_review_and_observed_context_refresh",
            "zipf_frequency_is_not_cefr_or_user_known_word_level",
            "llm_rows_should_be_generated_after_prompt_contract_review_not_from_this_report_alone",
        ],
        "next_steps": [
            "Human-review the current representative gap rows before promotion claims.",
            "Add representative observed or corpus-like rows for underrepresented Zipf bands before claiming a full curve.",
            "Use P0 very-common positive-active failures to design LLM source/evidence generation prompts.",
            "Keep generated discovery rows separate from locked evaluation rows.",
        ],
    }


def render_zipf_expansion_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Zipf Expansion Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Represented Zipf bands: `{summary.get('represented_zipf_band_count', 0)}` / `{summary.get('planned_zipf_band_count', 0)}`",
        f"- P0 bands: `{summary.get('p0_band_count', 0)}`",
        f"- Recommended manual/observed rows: `{summary.get('recommended_manual_or_observed_rows', 0)}`",
        f"- Recommended LLM discovery rows: `{summary.get('recommended_llm_discovery_rows', 0)}`",
        f"- Recommended locked-eval rows: `{summary.get('recommended_locked_eval_rows', 0)}`",
        "",
        "## Expansion Rows",
        "",
        _expansion_table(report.get("expansion_rows")),
        "",
        "## Interpretation",
        "",
        "- The very-common band is not underfilled by raw row count, but it is the clearest false-abstain problem for good replacements.",
        "- The mid and rare bands are absent from the representative-proxy lane, so they are controls for the frequency-curve hypothesis.",
        "- This plan separates row collection from LLM generation: representative rows first, generated discovery and locked-eval rows second.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _zipf_breakdowns(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("scope_id") or ""): row
        for row in _mapping_rows(
            _as_mapping(payload.get("breakdowns")).get("source_zipf_frequency_en")
        )
    }


def _expansion_row(
    *,
    band: str,
    representative: Mapping[str, object],
    overall: Mapping[str, object],
    trigger_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_count = int(representative.get("case_count") or 0)
    positive_count = int(representative.get("positive_case_count") or 0)
    negative_count = int(representative.get("negative_case_count") or 0)
    trigger_count = int(representative.get("trigger_count") or 0)
    false_abstains = int(representative.get("positive_abstain_count") or 0)
    missing_case_rows = max(0, MIN_CASES_PER_REPRESENTATIVE_BAND - case_count)
    missing_positive_rows = max(0, MIN_POSITIVES_PER_REPRESENTATIVE_BAND - positive_count)
    missing_negative_rows = max(0, MIN_NEGATIVES_PER_REPRESENTATIVE_BAND - negative_count)
    missing_trigger_rows = max(0, MIN_TRIGGERS_PER_REPRESENTATIVE_BAND - trigger_count)
    observed_issue_score = (
        1.5 * missing_case_rows
        + 2.0 * missing_positive_rows
        + 1.0 * missing_negative_rows
        + 2.0 * missing_trigger_rows
        + 1.25 * false_abstains
        + 12.0 * max(0.0, 0.8 - _safe_float(representative.get("positive_allow_rate")))
    )
    priority = "P0" if observed_issue_score >= 35 else "P1" if observed_issue_score >= 18 else "P2"
    manual_rows = max(missing_case_rows, missing_positive_rows + missing_negative_rows)
    if false_abstains and band == "zipf_5_plus_very_common":
        manual_rows = max(manual_rows, 16)
    llm_rows = 24 if priority == "P0" else 12 if priority == "P1" else 6
    locked_rows = 12 if priority == "P0" else 6 if priority == "P1" else 3
    return {
        "zipf_band": band,
        "priority": priority,
        "representative_case_count": case_count,
        "representative_trigger_count": trigger_count,
        "representative_positive_cases": positive_count,
        "representative_negative_cases": negative_count,
        "representative_positive_allow_rate": representative.get("positive_allow_rate"),
        "representative_negative_abstain_rate": representative.get("negative_abstain_rate"),
        "representative_false_abstains": false_abstains,
        "all_lane_case_count": int(overall.get("case_count") or 0),
        "all_lane_positive_allow_rate": overall.get("positive_allow_rate"),
        "all_lane_negative_abstain_rate": overall.get("negative_abstain_rate"),
        "missing_case_rows": missing_case_rows,
        "missing_positive_rows": missing_positive_rows,
        "missing_negative_rows": missing_negative_rows,
        "missing_trigger_rows": missing_trigger_rows,
        "issue_score": round(observed_issue_score, 4),
        "recommended_manual_or_observed_rows": manual_rows,
        "recommended_llm_discovery_rows": llm_rows,
        "recommended_locked_eval_rows": locked_rows,
        "example_triggers": _example_triggers(band=band, trigger_rows=trigger_rows),
        "reason": _reason(
            band=band,
            case_count=case_count,
            positive_count=positive_count,
            negative_count=negative_count,
            false_abstains=false_abstains,
        ),
    }


def _reason(
    *,
    band: str,
    case_count: int,
    positive_count: int,
    negative_count: int,
    false_abstains: int,
) -> str:
    if case_count == 0:
        return "missing_representative_control_band"
    if false_abstains and band == "zipf_5_plus_very_common":
        return "very_common_positive_false_abstain_mass"
    if positive_count < MIN_POSITIVES_PER_REPRESENTATIVE_BAND:
        return "positive_rows_underfilled"
    if negative_count < MIN_NEGATIVES_PER_REPRESENTATIVE_BAND:
        return "negative_rows_underfilled"
    return "maintain_as_curve_control"


def _example_triggers(
    *,
    band: str,
    trigger_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    examples = [
        str(row.get("scope_id") or "")
        for row in trigger_rows
        if str(row.get("source_zipf_band") or "") == band
    ]
    return examples[:8]


def _expansion_sort_key(row: Mapping[str, object]) -> tuple[int, float, str]:
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    return (
        priority_order.get(str(row.get("priority") or ""), 9),
        -_safe_float(row.get("issue_score")),
        str(row.get("zipf_band") or ""),
    )


def _expansion_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No expansion rows._"
    lines = [
        "| Priority | Zipf Band | Rep Cases | Pos Allow | Neg Abstain | False Abstain | Manual/Observed | LLM Discovery | Locked Eval | Reason | Example Triggers |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('priority') or ''))}`",
                    f"`{_escape_md(str(row.get('zipf_band') or ''))}`",
                    f"`{int(row.get('representative_case_count') or 0)}`",
                    f"`{_format_percent(row.get('representative_positive_allow_rate'))}`",
                    f"`{_format_percent(row.get('representative_negative_abstain_rate'))}`",
                    f"`{int(row.get('representative_false_abstains') or 0)}`",
                    f"`{int(row.get('recommended_manual_or_observed_rows') or 0)}`",
                    f"`{int(row.get('recommended_llm_discovery_rows') or 0)}`",
                    f"`{int(row.get('recommended_locked_eval_rows') or 0)}`",
                    f"`{_escape_md(str(row.get('reason') or ''))}`",
                    _escape_md(", ".join(str(item) for item in row.get("example_triggers", []))),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
