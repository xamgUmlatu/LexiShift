#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(PROJECT_ROOT / "core"), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prototype_admission_probe_en_es import (  # noqa: E402
    ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR,
)


DEFAULT_ACTIVE_REPORT = TEST_OUTPUTS_ROOT / (
    "semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_heldout_"
    "margin000_phrase002_validation_latest.json"
)
DEFAULT_PHRASE_REPORT = TEST_OUTPUTS_ROOT / (
    "semantic_source_non_v10_wave6_alt_phrase_semantic_surface_pos_phrase_"
    "margin000_phrase002_validation_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay semantic phrase-prototype plus surface-POS traces while sweeping "
            "general rescue gates. This does not rescore evidence; it keeps the score "
            "surface fixed and only varies when a syntax rescue may override abstain."
        )
    )
    parser.add_argument("--active-report-json", type=Path, default=DEFAULT_ACTIVE_REPORT)
    parser.add_argument("--phrase-report-json", type=Path, default=DEFAULT_PHRASE_REPORT)
    parser.add_argument("--min-margin-grid", default="0")
    parser.add_argument("--phrase-prototype-margin-grid", default="0.02")
    parser.add_argument("--rescue-min-active-grid", default="0,0.5,0.52,0.55,0.58")
    parser.add_argument("--noun-max-phrase-lead-grid", default="none")
    parser.add_argument("--modifier-max-phrase-lead-grid", default="none,0.02,0.03,0.04,0.05")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when no replayed policy passes all supplied suites.",
    )
    return parser.parse_args()


def build_surface_pos_rescue_policy_sweep_report(
    *,
    active_report: Mapping[str, object],
    phrase_report: Mapping[str, object],
    active_report_path: Path | None = None,
    phrase_report_path: Path | None = None,
    min_margins: Sequence[float] = (0.0,),
    phrase_prototype_margins: Sequence[float] = (0.02,),
    rescue_min_active_scores: Sequence[float] = (0.0, 0.5, 0.52, 0.55, 0.58),
    noun_max_phrase_leads: Sequence[float | None] = (None,),
    modifier_max_phrase_leads: Sequence[float | None] = (None, 0.02, 0.03, 0.04, 0.05),
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    suites = [
        _suite_payload("active_shadow", active_report, active_report_path),
        _suite_payload("phrase_no_winner", phrase_report, phrase_report_path),
    ]
    policies = _policy_grid(
        min_margins=min_margins,
        phrase_prototype_margins=phrase_prototype_margins,
        rescue_min_active_scores=rescue_min_active_scores,
        noun_max_phrase_leads=noun_max_phrase_leads,
        modifier_max_phrase_leads=modifier_max_phrase_leads,
    )
    rows: list[dict[str, object]] = []
    for policy in policies:
        for suite in suites:
            summary = _replay_suite(suite["case_results"], policy=policy)
            rows.append(_policy_suite_row(policy=policy, suite=suite, summary=summary))

    recommendation = _build_recommendation(rows, policies)
    status = "ok" if recommendation.get("recommended_policy") else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "rescue_policy_candidate_found" if status == "ok" else "rescue_policy_review",
        "generated_at": generated_at,
        "score_surface": {
            "active_report": _report_ref(active_report, active_report_path),
            "phrase_report": _report_ref(phrase_report, phrase_report_path),
        },
        "grid": {
            "min_margins": [float(value) for value in min_margins],
            "phrase_prototype_margins": [float(value) for value in phrase_prototype_margins],
            "rescue_min_active_scores": [float(value) for value in rescue_min_active_scores],
            "noun_max_phrase_leads": [_optional_float(value) for value in noun_max_phrase_leads],
            "modifier_max_phrase_leads": [
                _optional_float(value) for value in modifier_max_phrase_leads
            ],
        },
        "summary": {
            "suite_count": len(suites),
            "policy_count": len(policies),
            "row_count": len(rows),
            "passing_policy_count": len(recommendation.get("passing_policies") or ()),
            "recommended_policy": recommendation.get("recommended_policy"),
        },
        "recommendation": recommendation,
        "rows": rows,
        "limitations": [
            "replay_only_not_runtime_policy",
            "uses_fixed_score_traces_from_supplied_reports",
            "bounded_wave6_active_and_phrase_suites_only",
        ],
    }


def render_surface_pos_rescue_policy_sweep_markdown(report: Mapping[str, object]) -> str:
    recommendation = _as_mapping(report.get("recommendation"))
    lines = [
        "# en-es Surface-POS Rescue Policy Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Recommended policy: `{_format_policy(recommendation.get('recommended_policy'))}`",
        f"- Passing policies: `{len(recommendation.get('passing_policies') or ())}`",
        "",
        "## Recommendation",
        "",
        f"- Reason: `{recommendation.get('reason', '')}`",
        f"- Next step: {recommendation.get('next_step', '')}",
        "",
        "## Best Rows",
        "",
        _row_table(recommendation.get("best_rows", ())),
        "",
        "## Passing Policies",
        "",
        _policy_table(recommendation.get("passing_policies", ())),
        "",
        "## Blockers",
        "",
        _blocker_table(recommendation.get("blockers_by_policy")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _suite_payload(
    suite_id: str,
    report: Mapping[str, object],
    path: Path | None,
) -> dict[str, object]:
    return {
        "suite_id": suite_id,
        "path": str(path or ""),
        "path_sha256": _sha256(path) if path else "",
        "heldout_dataset_id": str(report.get("heldout_dataset_id") or "").strip(),
        "case_scope": str(report.get("heldout_case_scope") or "").strip(),
        "case_results": [
            dict(row)
            for row in report.get("configured_case_results", ())
            if isinstance(row, Mapping)
        ],
    }


def _policy_grid(
    *,
    min_margins: Sequence[float],
    phrase_prototype_margins: Sequence[float],
    rescue_min_active_scores: Sequence[float],
    noun_max_phrase_leads: Sequence[float | None],
    modifier_max_phrase_leads: Sequence[float | None],
) -> list[dict[str, object]]:
    policies: list[dict[str, object]] = []
    for min_margin in _dedupe_floats(min_margins):
        for phrase_margin in _dedupe_floats(phrase_prototype_margins):
            for rescue_min_active in _dedupe_floats(rescue_min_active_scores):
                for noun_ceiling in _dedupe_optional_floats(noun_max_phrase_leads):
                    for modifier_ceiling in _dedupe_optional_floats(modifier_max_phrase_leads):
                        policies.append(
                            {
                                "min_margin": float(min_margin),
                                "phrase_prototype_margin": float(phrase_margin),
                                "rescue_min_active_score": float(rescue_min_active),
                                "noun_max_phrase_lead": _optional_float(noun_ceiling),
                                "modifier_max_phrase_lead": _optional_float(modifier_ceiling),
                            }
                        )
    return policies


def _replay_suite(
    case_results: object,
    *,
    policy: Mapping[str, object],
) -> dict[str, object]:
    rows = [row for row in case_results or () if isinstance(row, Mapping)]
    case_count = len(rows)
    gold_replace = 0
    gold_abstain = 0
    true_replace = 0
    correct = 0
    harmful_ids: list[str] = []
    false_ids: list[str] = []
    rescue_ids: list[str] = []
    block_reasons: dict[str, int] = {}
    for row in rows:
        gold = str(row.get("gold_decision") or "").strip()
        if gold == "replace":
            gold_replace += 1
        else:
            gold_abstain += 1
        decision, trace = _replay_decision(row, policy=policy)
        if decision == gold:
            correct += 1
        if decision == "replace" and gold == "replace":
            true_replace += 1
        if decision == "replace" and gold != "replace":
            harmful_ids.append(str(row.get("case_id") or "").strip())
        if decision != "replace" and gold == "replace":
            false_ids.append(str(row.get("case_id") or "").strip())
        if trace.get("active_rescue_applied"):
            rescue_ids.append(str(row.get("case_id") or "").strip())
        reason = str(trace.get("surface_pos_rescue_blocked_reason") or "").strip()
        if reason:
            block_reasons[reason] = block_reasons.get(reason, 0) + 1
    return {
        "case_count": case_count,
        "gold_replace_cases": gold_replace,
        "gold_abstain_cases": gold_abstain,
        "harmful_replace_count": len(harmful_ids),
        "false_abstain_count": len(false_ids),
        "harmful_replace_case_ids": harmful_ids,
        "false_abstain_case_ids": false_ids,
        "replace_recall": _round_float(true_replace / gold_replace) if gold_replace else 0.0,
        "decision_accuracy": _round_float(correct / case_count) if case_count else 0.0,
        "active_rescue_applied_count": len(rescue_ids),
        "active_rescue_case_ids": rescue_ids,
        "surface_pos_rescue_blocked_reasons": block_reasons,
    }


def _replay_decision(
    row: Mapping[str, object],
    *,
    policy: Mapping[str, object],
) -> tuple[str, dict[str, object]]:
    active_score = float(row.get("active_score") or 0.0)
    shadow_score = float(row.get("strongest_shadow_score") or 0.0)
    phrase_score = float(row.get("phrase_control_score") or 0.0)
    margin = active_score - shadow_score
    phrase_lead = phrase_score - max(active_score, shadow_score)
    min_margin = float(policy.get("min_margin") or 0.0)
    phrase_margin = float(policy.get("phrase_prototype_margin") or 0.0)
    has_active_evidence = bool(str(row.get("active_evidence_text") or "").strip())
    has_phrase_evidence = bool(str(row.get("phrase_control_evidence_text") or "").strip())
    decision = "replace" if has_active_evidence and margin >= min_margin else "abstain"
    if has_phrase_evidence and phrase_score >= max(active_score, shadow_score) + phrase_margin:
        decision = "abstain"
    if bool(row.get("phrase_preemption_hit")):
        decision = "abstain"

    signal = str(row.get("surface_pos_signal") or "").strip()
    trace: dict[str, object] = {
        "active_rescue_applied": False,
        "surface_pos_rescue_blocked_reason": "",
    }
    if signal in {"active_noun_frame", "active_modifier_frame"} and decision != "replace":
        block_reason = _surface_rescue_block_reason(
            row,
            signal=signal,
            active_score=active_score,
            margin=margin,
            phrase_lead=phrase_lead,
            policy=policy,
        )
        if block_reason:
            trace["surface_pos_rescue_blocked_reason"] = block_reason
        else:
            decision = "replace"
            trace["active_rescue_applied"] = True
    elif signal in {"non_active_nominal_frame", "shadow_verb_frame"} and decision == "replace":
        decision = "abstain"
    return decision, trace


def _surface_rescue_block_reason(
    row: Mapping[str, object],
    *,
    signal: str,
    active_score: float,
    margin: float,
    phrase_lead: float,
    policy: Mapping[str, object],
) -> str:
    if not str(row.get("active_evidence_text") or "").strip():
        return "missing_active_examples"
    rescue_min_active = float(policy.get("rescue_min_active_score") or 0.0)
    if active_score < rescue_min_active:
        return "surface_pos_active_score_below_floor"
    if signal == "active_noun_frame" and not _noun_shadow_is_verb_like(row):
        return "strongest_shadow_not_verb_like"
    if signal == "active_modifier_frame" and margin < ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR:
        return "active_modifier_margin_below_floor"
    noun_ceiling = policy.get("noun_max_phrase_lead")
    if signal == "active_noun_frame" and noun_ceiling is not None:
        if phrase_lead >= float(noun_ceiling):
            return "surface_pos_noun_phrase_lead_above_ceiling"
    modifier_ceiling = policy.get("modifier_max_phrase_lead")
    if signal == "active_modifier_frame" and modifier_ceiling is not None:
        if phrase_lead >= float(modifier_ceiling):
            return "surface_pos_modifier_phrase_lead_above_ceiling"
    return ""


def _noun_shadow_is_verb_like(row: Mapping[str, object]) -> bool:
    explicit = row.get("surface_pos_noun_shadow_verb_like")
    if isinstance(explicit, bool):
        return explicit
    if str(row.get("surface_pos_rescue_blocked_reason") or "").strip() == (
        "strongest_shadow_not_verb_like"
    ):
        return False
    return True


def _policy_suite_row(
    *,
    policy: Mapping[str, object],
    suite: Mapping[str, object],
    summary: Mapping[str, object],
) -> dict[str, object]:
    passes = (
        int(summary.get("harmful_replace_count") or 0) == 0
        and int(summary.get("false_abstain_count") or 0) == 0
    )
    return {
        "policy_id": _policy_id(policy),
        "suite_id": str(suite.get("suite_id") or "").strip(),
        "dataset_id": str(suite.get("heldout_dataset_id") or "").strip(),
        "case_scope": str(suite.get("case_scope") or "").strip(),
        "passes": passes,
        **dict(policy),
        **dict(summary),
    }


def _build_recommendation(
    rows: Sequence[Mapping[str, object]],
    policies: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    suite_ids = sorted({str(row.get("suite_id") or "") for row in rows if row.get("suite_id")})
    passing_policies: list[dict[str, object]] = []
    blockers_by_policy: dict[str, list[dict[str, object]]] = {}
    for policy in policies:
        policy_id = _policy_id(policy)
        policy_rows = [row for row in rows if str(row.get("policy_id") or "") == policy_id]
        present_suite_ids = {str(row.get("suite_id") or "") for row in policy_rows}
        blockers = [row for row in policy_rows if not bool(row.get("passes"))]
        missing_suite_ids = [
            suite_id for suite_id in suite_ids if suite_id not in present_suite_ids
        ]
        if not blockers and not missing_suite_ids and suite_ids:
            passing_policies.append(dict(policy))
        blockers_by_policy[policy_id] = [
            {
                "suite_id": str(row.get("suite_id") or ""),
                "harmful_replace_count": int(row.get("harmful_replace_count") or 0),
                "false_abstain_count": int(row.get("false_abstain_count") or 0),
                "harmful_replace_case_ids": list(row.get("harmful_replace_case_ids") or ()),
                "false_abstain_case_ids": list(row.get("false_abstain_case_ids") or ()),
            }
            for row in blockers
        ] + [
            {
                "suite_id": suite_id,
                "harmful_replace_count": 0,
                "false_abstain_count": 0,
                "harmful_replace_case_ids": [],
                "false_abstain_case_ids": [],
                "reason": "suite_result_missing",
            }
            for suite_id in missing_suite_ids
        ]
    best_rows = sorted(rows, key=_row_rank_key)[:12]
    recommended = min(passing_policies, key=_policy_rank_key, default=None)
    return {
        "reason": "passing_policy_found" if recommended else "no_policy_passed",
        "recommended_policy": recommended,
        "passing_policies": passing_policies,
        "best_rows": [dict(row) for row in best_rows],
        "blockers_by_policy": {
            policy_id: blockers for policy_id, blockers in blockers_by_policy.items() if blockers
        },
        "next_step": (
            "run the recommended rescue policy through the scorer-backed held-out harness"
            if recommended
            else "add a new rescue gate or source signal; current replayed gates did not pass"
        ),
    }


def _row_rank_key(row: Mapping[str, object]) -> tuple[int, int, float, float, str, str]:
    return (
        int(row.get("harmful_replace_count") or 0),
        int(row.get("false_abstain_count") or 0),
        -float(row.get("decision_accuracy") or 0.0),
        -float(row.get("replace_recall") or 0.0),
        str(row.get("policy_id") or ""),
        str(row.get("suite_id") or ""),
    )


def _policy_rank_key(policy: Mapping[str, object]) -> tuple[float, float, float, str, str]:
    noun_ceiling = policy.get("noun_max_phrase_lead")
    modifier_ceiling = policy.get("modifier_max_phrase_lead")
    return (
        float(policy.get("rescue_min_active_score") or 0.0),
        999.0 if noun_ceiling is None else float(noun_ceiling),
        999.0 if modifier_ceiling is None else float(modifier_ceiling),
        str(policy.get("min_margin") or ""),
        str(policy.get("phrase_prototype_margin") or ""),
    )


def _row_table(rows: object) -> str:
    materialized = [row for row in rows or () if isinstance(row, Mapping)]
    if not materialized:
        return "No rows."
    lines = [
        "| Suite | Policy | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('suite_id', '')}`",
                    f"`{row.get('policy_id', '')}`",
                    f"`{str(bool(row.get('passes'))).lower()}`",
                    str(row.get("case_count", 0)),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                    _pct(row.get("replace_recall")),
                    _pct(row.get("decision_accuracy")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _policy_table(policies: object) -> str:
    materialized = [policy for policy in policies or () if isinstance(policy, Mapping)]
    if not materialized:
        return "No passing policies."
    lines = [
        "| Policy | Min Margin | Phrase Margin | Rescue Active Floor | Noun Phrase Ceiling | Modifier Phrase Ceiling |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_policy_id(policy)}`",
                    str(policy.get("min_margin", 0.0)),
                    str(policy.get("phrase_prototype_margin", 0.0)),
                    str(policy.get("rescue_min_active_score", 0.0)),
                    _format_optional(policy.get("noun_max_phrase_lead")),
                    _format_optional(policy.get("modifier_max_phrase_lead")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _blocker_table(blockers_by_policy: object) -> str:
    if not isinstance(blockers_by_policy, Mapping) or not blockers_by_policy:
        return "No blockers."
    lines = [
        "| Policy | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for policy_id, blockers in blockers_by_policy.items():
        if not isinstance(blockers, Sequence) or isinstance(blockers, (str, bytes)):
            continue
        for blocker in blockers:
            if not isinstance(blocker, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{policy_id}`",
                        f"`{blocker.get('suite_id', '')}`",
                        str(blocker.get("harmful_replace_count", 0)),
                        str(blocker.get("false_abstain_count", 0)),
                        _case_ids(blocker.get("harmful_replace_case_ids")),
                        _case_ids(blocker.get("false_abstain_case_ids")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) if len(lines) > 2 else "No blockers."


def _policy_id(policy: Mapping[str, object]) -> str:
    return (
        f"m={_fmt(policy.get('min_margin'))};"
        f"p={_fmt(policy.get('phrase_prototype_margin'))};"
        f"rescue_active={_fmt(policy.get('rescue_min_active_score'))};"
        f"noun_lead={_format_optional(policy.get('noun_max_phrase_lead'))};"
        f"modifier_lead={_format_optional(policy.get('modifier_max_phrase_lead'))}"
    )


def _format_policy(value: object) -> str:
    return _policy_id(value) if isinstance(value, Mapping) else "none"


def _report_ref(report: Mapping[str, object], path: Path | None) -> dict[str, object]:
    return {
        "path": str(path or ""),
        "sha256": _sha256(path) if path else "",
        "status": str(report.get("status") or ""),
        "heldout_dataset_id": str(report.get("heldout_dataset_id") or ""),
        "case_scope": str(report.get("heldout_case_scope") or ""),
    }


def _parse_float_grid(value: str) -> list[float]:
    return [float(item) for item in _parse_string_grid(value)]


def _parse_optional_float_grid(value: str) -> list[float | None]:
    values: list[float | None] = []
    for item in _parse_string_grid(value):
        if item.lower() in {"none", "null", "off"}:
            values.append(None)
        else:
            values.append(float(item))
    return values


def _parse_string_grid(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _dedupe_floats(values: Sequence[float]) -> list[float]:
    seen: set[float] = set()
    out: list[float] = []
    for value in values:
        item = float(value)
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _dedupe_optional_floats(values: Sequence[float | None]) -> list[float | None]:
    seen: set[float | None] = set()
    out: list[float | None] = []
    for value in values:
        item = _optional_float(value)
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _case_ids(value: object) -> str:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return "`none`"
    text = ", ".join(str(item) for item in value if str(item))
    return f"`{text or 'none'}`"


def _format_optional(value: object) -> str:
    return "none" if value is None else _fmt(value)


def _fmt(value: object) -> str:
    return f"{float(value or 0.0):.3f}".rstrip("0").rstrip(".")


def _pct(value: object) -> str:
    return f"{float(value or 0.0) * 100:.1f}%"


def _round_float(value: float) -> float:
    return round(float(value), 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    active_report = _load_json(args.active_report_json)
    phrase_report = _load_json(args.phrase_report_json)
    report = build_surface_pos_rescue_policy_sweep_report(
        active_report=active_report,
        phrase_report=phrase_report,
        active_report_path=args.active_report_json,
        phrase_report_path=args.phrase_report_json,
        min_margins=_parse_float_grid(args.min_margin_grid),
        phrase_prototype_margins=_parse_float_grid(args.phrase_prototype_margin_grid),
        rescue_min_active_scores=_parse_float_grid(args.rescue_min_active_grid),
        noun_max_phrase_leads=_parse_optional_float_grid(args.noun_max_phrase_lead_grid),
        modifier_max_phrase_leads=_parse_optional_float_grid(args.modifier_max_phrase_lead_grid),
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_surface_pos_rescue_policy_sweep_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
