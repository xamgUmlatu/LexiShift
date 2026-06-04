#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
DEFAULT_CASE_ROOT = DOCS_ROOT / "test_inputs" / "semantic_routing_cases"
for candidate in (str(PROJECT_ROOT / "core"), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_source_heldout_validation_en_es import (  # noqa: E402
    build_source_heldout_validation_report,
)
from semantic_surface_pos_rescue_policy_sweep_en_es import (  # noqa: E402
    _policy_id,
    _replay_decision,
)


DEFAULT_BASE_DATASET = (
    DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json"
)
DEFAULT_ACTIVE_HELDOUT_CASES = (
    DEFAULT_CASE_ROOT / "en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1.json"
)
DEFAULT_PHRASE_HELDOUT_CASES = (
    DEFAULT_CASE_ROOT / "en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1.json"
)
DEFAULT_AUTH_FRAME_EVIDENCE = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-authorization-frame-non-v10-wave6-wiktextract-supported-v1-latest_"
    "cycle_sense_admitted_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_"
    "raw_sentence_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md"
)
DEFAULT_DECISION_SHAPE = "active_shadow_phrase_semantic_surface_pos"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the recommended surface-POS rescue policy over freshly scored "
            "active/shadow and phrase/no-winner held-out rows. This is scorer-backed "
            "offline confirmation, not a runtime policy change."
        )
    )
    parser.add_argument("--base-dataset", type=Path, default=DEFAULT_BASE_DATASET)
    parser.add_argument("--active-heldout-cases", type=Path, default=DEFAULT_ACTIVE_HELDOUT_CASES)
    parser.add_argument("--phrase-heldout-cases", type=Path, default=DEFAULT_PHRASE_HELDOUT_CASES)
    parser.add_argument("--evidence-batch-json", type=Path, default=DEFAULT_AUTH_FRAME_EVIDENCE)
    parser.add_argument("--scorer-id", default="sentence_transformer_cosine")
    parser.add_argument("--context-view", default="raw_sentence")
    parser.add_argument("--min-active-score", type=float, default=0.0)
    parser.add_argument("--min-margin", type=float, default=0.0)
    parser.add_argument("--phrase-prototype-margin", type=float, default=0.02)
    parser.add_argument("--decision-shape", default=DEFAULT_DECISION_SHAPE)
    parser.add_argument("--rescue-min-active-score", type=float, default=0.52)
    parser.add_argument("--noun-max-phrase-lead", default="none")
    parser.add_argument("--modifier-max-phrase-lead", default="0.02")
    parser.add_argument("--max-harmful", type=int, default=0)
    parser.add_argument("--max-false-abstain", type=int, default=0)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when the policy misses the configured suite thresholds.",
    )
    return parser.parse_args()


def build_scorer_backed_surface_pos_rescue_policy_validation_report(
    *,
    base_dataset_payload: Mapping[str, object],
    active_heldout_case_payload: Mapping[str, object],
    phrase_heldout_case_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    scorer_id: str = "sentence_transformer_cosine",
    context_view: str = "raw_sentence",
    min_active_score: float = 0.0,
    min_margin: float = 0.0,
    phrase_prototype_margin: float = 0.02,
    decision_shape: str = DEFAULT_DECISION_SHAPE,
    rescue_min_active_score: float = 0.52,
    noun_max_phrase_lead: float | None = None,
    modifier_max_phrase_lead: float | None = 0.02,
    max_harmful: int = 0,
    max_false_abstain: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    active_report = build_source_heldout_validation_report(
        base_dataset_payload=base_dataset_payload,
        heldout_case_payload=active_heldout_case_payload,
        evidence_batch_payload=evidence_batch_payload,
        scorer_id=scorer_id,
        context_view=context_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_prototype_margin=phrase_prototype_margin,
        decision_shape=decision_shape,
        max_harmful=max_harmful,
        max_false_abstain=max_false_abstain,
        generated_at=generated_at,
    )
    phrase_report = build_source_heldout_validation_report(
        base_dataset_payload=base_dataset_payload,
        heldout_case_payload=phrase_heldout_case_payload,
        evidence_batch_payload=evidence_batch_payload,
        scorer_id=scorer_id,
        context_view=context_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        phrase_prototype_margin=phrase_prototype_margin,
        decision_shape=decision_shape,
        max_harmful=max_harmful,
        max_false_abstain=max_false_abstain,
        generated_at=generated_at,
    )
    return build_surface_pos_rescue_policy_validation_report(
        active_validation_report=active_report,
        phrase_validation_report=phrase_report,
        min_margin=min_margin,
        phrase_prototype_margin=phrase_prototype_margin,
        rescue_min_active_score=rescue_min_active_score,
        noun_max_phrase_lead=noun_max_phrase_lead,
        modifier_max_phrase_lead=modifier_max_phrase_lead,
        max_harmful=max_harmful,
        max_false_abstain=max_false_abstain,
        generated_at=generated_at,
    )


def build_surface_pos_rescue_policy_validation_report(
    *,
    active_validation_report: Mapping[str, object],
    phrase_validation_report: Mapping[str, object],
    min_margin: float = 0.0,
    phrase_prototype_margin: float = 0.02,
    rescue_min_active_score: float = 0.52,
    noun_max_phrase_lead: float | None = None,
    modifier_max_phrase_lead: float | None = 0.02,
    max_harmful: int = 0,
    max_false_abstain: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    policy = {
        "min_margin": float(min_margin),
        "phrase_prototype_margin": float(phrase_prototype_margin),
        "rescue_min_active_score": float(rescue_min_active_score),
        "noun_max_phrase_lead": _optional_float(noun_max_phrase_lead),
        "modifier_max_phrase_lead": _optional_float(modifier_max_phrase_lead),
    }
    suites = [
        _validate_suite("active_shadow", active_validation_report, policy=policy),
        _validate_suite("phrase_no_winner", phrase_validation_report, policy=policy),
    ]
    policy_summaries = [
        _as_mapping(suite.get("policy_summary")) for suite in suites if isinstance(suite, Mapping)
    ]
    harmful_count = sum(
        int(summary.get("harmful_replace_count") or 0) for summary in policy_summaries
    )
    false_abstain_count = sum(
        int(summary.get("false_abstain_count") or 0) for summary in policy_summaries
    )
    passes = all(bool(suite.get("passes")) for suite in suites)
    return {
        "schema_version": 1,
        "status": "ok" if passes else "review",
        "decision": "scorer_backed_policy_pass" if passes else "scorer_backed_policy_review",
        "generated_at": generated_at,
        "policy": policy,
        "policy_id": _policy_id(policy),
        "summary": {
            "suite_count": len(suites),
            "case_count": sum(int(summary.get("case_count") or 0) for summary in policy_summaries),
            "gold_replace_cases": sum(
                int(summary.get("gold_replace_cases") or 0) for summary in policy_summaries
            ),
            "gold_abstain_cases": sum(
                int(summary.get("gold_abstain_cases") or 0) for summary in policy_summaries
            ),
            "max_harmful": int(max_harmful),
            "max_false_abstain": int(max_false_abstain),
            "harmful_replace_count": harmful_count,
            "false_abstain_count": false_abstain_count,
            "harmful_replace_case_ids": _case_ids_from_summaries(
                policy_summaries, "harmful_replace_case_ids"
            ),
            "false_abstain_case_ids": _case_ids_from_summaries(
                policy_summaries, "false_abstain_case_ids"
            ),
            "active_rescue_applied_count": sum(
                int(summary.get("active_rescue_applied_count") or 0) for summary in policy_summaries
            ),
            "active_rescue_case_ids": _case_ids_from_summaries(
                policy_summaries, "active_rescue_case_ids"
            ),
        },
        "suite_results": suites,
        "limitations": [
            "offline_scorer_backed_validation_not_runtime_policy",
            "policy_applied_after_fresh_harness_scoring",
            "bounded_wave6_active_and_phrase_suites_only",
        ],
        "next_steps": (
            [
                "keep the candidate research-only until broader semantic-class breadth is tested",
                "do not change runtime policy without implementation and runtime-path tests",
            ]
            if passes
            else [
                "inspect policy failure cases before changing gates",
                "rerun the fixed-trace sweep only after scorer-backed misses are understood",
            ]
        ),
    }


def render_surface_pos_rescue_policy_validation_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Surface-POS Rescue Policy Validation",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Policy: `{report.get('policy_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Suites: `{summary.get('suite_count', 0)}`",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Harmful replacements: `{summary.get('harmful_replace_count', 0)}` / max `{summary.get('max_harmful', 0)}`",
        f"- False abstains: `{summary.get('false_abstain_count', 0)}` / max `{summary.get('max_false_abstain', 0)}`",
        f"- Active rescues applied: `{summary.get('active_rescue_applied_count', 0)}`",
        f"- Harmful cases: `{', '.join(summary.get('harmful_replace_case_ids', ())) or 'none'}`",
        f"- False abstain cases: `{', '.join(summary.get('false_abstain_case_ids', ())) or 'none'}`",
        "",
        "## Suites",
        "",
        _suite_table(report.get("suite_results", ())),
        "",
        "## Rescue Applications",
        "",
        _case_table(report.get("suite_results", ()), failures_only=False),
        "",
        "## Failure Cases",
        "",
        _case_table(report.get("suite_results", ()), failures_only=True),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _validate_suite(
    suite_id: str,
    validation_report: Mapping[str, object],
    *,
    policy: Mapping[str, object],
) -> dict[str, object]:
    rows = [
        row
        for row in validation_report.get("configured_case_results", ())
        if isinstance(row, Mapping)
    ]
    case_results = [_policy_case_result(suite_id, row, policy=policy) for row in rows]
    summary = _summary(case_results)
    max_harmful = int(_as_mapping(validation_report.get("summary")).get("max_harmful") or 0)
    max_false_abstain = int(
        _as_mapping(validation_report.get("summary")).get("max_false_abstain") or 0
    )
    passes = (
        int(summary.get("harmful_replace_count") or 0) <= max_harmful
        and int(summary.get("false_abstain_count") or 0) <= max_false_abstain
    )
    return {
        "suite_id": suite_id,
        "passes": passes,
        "source_validation": _source_validation_ref(validation_report),
        "policy_summary": summary,
        "policy_case_results": case_results,
    }


def _policy_case_result(
    suite_id: str,
    row: Mapping[str, object],
    *,
    policy: Mapping[str, object],
) -> dict[str, object]:
    predicted_decision, trace = _replay_decision(row, policy=policy)
    gold = str(row.get("gold_decision") or "").strip()
    active_score = float(row.get("active_score") or 0.0)
    shadow_score = float(row.get("strongest_shadow_score") or 0.0)
    phrase_score = float(row.get("phrase_control_score") or 0.0)
    result = {
        "suite_id": suite_id,
        "case_id": str(row.get("case_id") or "").strip(),
        "family_id": str(row.get("family_id") or "").strip(),
        "trigger": str(row.get("trigger") or "").strip(),
        "sentence": str(row.get("sentence") or "").strip(),
        "gold_decision": gold,
        "predicted_decision_before_policy": str(row.get("predicted_decision") or "").strip(),
        "predicted_decision": predicted_decision,
        "policy_correct": predicted_decision == gold,
        "harmful_replace": predicted_decision == "replace" and gold != "replace",
        "false_abstain": predicted_decision != "replace" and gold == "replace",
        "active_score": _round(active_score),
        "strongest_shadow_score": _round(shadow_score),
        "phrase_control_score": _round(phrase_score),
        "margin": _round(active_score - shadow_score),
        "phrase_lead": _round(phrase_score - max(active_score, shadow_score)),
        "surface_pos_signal": str(row.get("surface_pos_signal") or "").strip(),
        "surface_pos_noun_shadow_verb_like": row.get("surface_pos_noun_shadow_verb_like"),
        "active_rescue_applied": bool(trace.get("active_rescue_applied")),
        "surface_pos_rescue_blocked_reason": str(
            trace.get("surface_pos_rescue_blocked_reason") or ""
        ).strip(),
        "active_evidence_text": str(row.get("active_evidence_text") or "").strip(),
        "strongest_shadow_evidence_text": str(
            row.get("strongest_shadow_evidence_text") or ""
        ).strip(),
        "phrase_control_evidence_text": str(row.get("phrase_control_evidence_text") or "").strip(),
    }
    return result


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    case_count = len(rows)
    gold_replace = [row for row in rows if row.get("gold_decision") == "replace"]
    harmful = [row for row in rows if row.get("harmful_replace")]
    false = [row for row in rows if row.get("false_abstain")]
    correct = [row for row in rows if row.get("policy_correct")]
    true_replace = [
        row
        for row in rows
        if row.get("predicted_decision") == "replace" and row.get("gold_decision") == "replace"
    ]
    return {
        "case_count": case_count,
        "gold_replace_cases": len(gold_replace),
        "gold_abstain_cases": case_count - len(gold_replace),
        "harmful_replace_count": len(harmful),
        "false_abstain_count": len(false),
        "harmful_replace_case_ids": [str(row.get("case_id") or "") for row in harmful],
        "false_abstain_case_ids": [str(row.get("case_id") or "") for row in false],
        "replace_recall": _round(len(true_replace) / len(gold_replace)) if gold_replace else 0.0,
        "decision_accuracy": _round(len(correct) / case_count) if case_count else 0.0,
        "active_rescue_applied_count": sum(
            1 for row in rows if bool(row.get("active_rescue_applied"))
        ),
        "active_rescue_case_ids": [
            str(row.get("case_id") or "") for row in rows if bool(row.get("active_rescue_applied"))
        ],
    }


def _source_validation_ref(report: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(report.get("summary"))
    return {
        "status": str(report.get("status") or "").strip(),
        "decision": str(report.get("decision") or "").strip(),
        "heldout_dataset_id": str(report.get("heldout_dataset_id") or "").strip(),
        "heldout_case_scope": str(report.get("heldout_case_scope") or "").strip(),
        "evidence_batch_id": str(report.get("evidence_batch_id") or "").strip(),
        "configured_lane": dict(_as_mapping(report.get("configured_lane"))),
        "summary": {
            "case_count": int(summary.get("case_count") or 0),
            "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
            "false_abstain_count": int(summary.get("false_abstain_count") or 0),
            "replace_recall": summary.get("replace_recall"),
            "decision_accuracy": summary.get("decision_accuracy"),
        },
    }


def _suite_table(suites: object) -> str:
    materialized = [suite for suite in suites or () if isinstance(suite, Mapping)]
    if not materialized:
        return "No suite rows."
    lines = [
        "| Suite | Pass | Cases | Harmful | False Abstain | Recall | Accuracy | Active Rescues | Source Validation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for suite in materialized:
        summary = _as_mapping(suite.get("policy_summary"))
        source = _as_mapping(suite.get("source_validation"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{suite.get('suite_id', '')}`",
                    f"`{str(bool(suite.get('passes'))).lower()}`",
                    str(summary.get("case_count", 0)),
                    str(summary.get("harmful_replace_count", 0)),
                    str(summary.get("false_abstain_count", 0)),
                    _pct(summary.get("replace_recall")),
                    _pct(summary.get("decision_accuracy")),
                    str(summary.get("active_rescue_applied_count", 0)),
                    f"`{source.get('status', '')}` / `{source.get('decision', '')}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_table(suites: object, *, failures_only: bool) -> str:
    rows = [
        row
        for suite in suites or ()
        if isinstance(suite, Mapping)
        for row in suite.get("policy_case_results", ())
        if isinstance(row, Mapping)
        and (
            bool(row.get("harmful_replace"))
            or bool(row.get("false_abstain"))
            or (not failures_only and bool(row.get("active_rescue_applied")))
        )
    ]
    if failures_only:
        rows = [row for row in rows if row.get("harmful_replace") or row.get("false_abstain")]
    if not rows:
        return "No failure cases." if failures_only else "No rescue applications."
    lines = [
        "| Suite | Case | Gold | Before | After | Active | Shadow | Phrase | Phrase Lead | Surface Signal | Trace |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        trace = ", ".join(
            item
            for item in (
                "rescue" if row.get("active_rescue_applied") else "",
                str(row.get("surface_pos_rescue_blocked_reason") or "").strip(),
            )
            if item
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('suite_id', '')}`",
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('gold_decision', '')}`",
                    f"`{row.get('predicted_decision_before_policy', '')}`",
                    f"`{row.get('predicted_decision', '')}`",
                    str(row.get("active_score", "")),
                    str(row.get("strongest_shadow_score", "")),
                    str(row.get("phrase_control_score", "")),
                    str(row.get("phrase_lead", "")),
                    f"`{row.get('surface_pos_signal', '')}`",
                    _md_text(trace or "none"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _case_ids_from_summaries(
    summaries: Sequence[Mapping[str, object]],
    key: str,
) -> list[str]:
    return [
        str(case_id) for summary in summaries for case_id in summary.get(key, ()) if str(case_id)
    ]


def _parse_optional_float(value: str) -> float | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "none", "null", "off"}:
        return None
    return float(normalized)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _round(value: float) -> float:
    return round(float(value), 4)


def _pct(value: object) -> str:
    return f"{float(value or 0.0) * 100:.1f}%"


def _md_text(value: object) -> str:
    text = str(value or "").strip()
    return (text or "`none`").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    base_dataset = load_sentence_veto_dataset(args.base_dataset)
    report = build_scorer_backed_surface_pos_rescue_policy_validation_report(
        base_dataset_payload=base_dataset,
        active_heldout_case_payload=_load_json(args.active_heldout_cases),
        phrase_heldout_case_payload=_load_json(args.phrase_heldout_cases),
        evidence_batch_payload=_load_json(args.evidence_batch_json),
        scorer_id=args.scorer_id,
        context_view=args.context_view,
        min_active_score=args.min_active_score,
        min_margin=args.min_margin,
        phrase_prototype_margin=args.phrase_prototype_margin,
        decision_shape=args.decision_shape,
        rescue_min_active_score=args.rescue_min_active_score,
        noun_max_phrase_lead=_parse_optional_float(args.noun_max_phrase_lead),
        modifier_max_phrase_lead=_parse_optional_float(args.modifier_max_phrase_lead),
        max_harmful=max(0, int(args.max_harmful)),
        max_false_abstain=max(0, int(args.max_false_abstain)),
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_surface_pos_rescue_policy_validation_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
