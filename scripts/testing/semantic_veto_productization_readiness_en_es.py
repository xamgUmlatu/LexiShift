#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_evidence import (  # noqa: E402
    SEMANTIC_EVIDENCE_NORMALIZATION_VERSION,
)
from lexishift_core.rulegen.semantic_publication import (  # noqa: E402
    build_semantic_inventory_from_results,
)
from lexishift_core.rulegen.semantic_routing_runtime_policy import (  # noqa: E402
    resolve_semantic_decision_policy,
)


DEFAULT_PROMPT_BAKEOFF = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es_latest.json"
)
DEFAULT_ADMISSION = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_admission_active_only_poc_en_es_latest.json"
)
DEFAULT_POSTPROCESS = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_postprocess_active_only_poc_en_es_latest.json"
)
DEFAULT_SCORE_CONTRIBUTION = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_score_contribution_active_only_poc_en_es_latest.json"
)
DEFAULT_SOURCE_PACKAGING = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_source_packaging_en_es_latest.json"
)
DEFAULT_INVENTORY_REPLAY = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_inventory_replay_en_es_latest.json"
)
DEFAULT_HELPER_RUNTIME_SMOKE = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_helper_runtime_smoke_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_productization_readiness_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_productization_readiness_en_es_latest.md"

RECOMMENDED_PROMPT_VARIANT = "v5_refresh_control"
RECOMMENDED_APPLICATION_MODE = "generated_active_only"
RECOMMENDED_POSTPROCESS_VIEW = "no_high_eval_overlap_sentence_only"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize whether the current en-es semantic-veto active-only LLM "
            "candidate is ready for production packaging."
        )
    )
    parser.add_argument("--prompt-bakeoff", type=Path, default=DEFAULT_PROMPT_BAKEOFF)
    parser.add_argument("--admission", type=Path, default=DEFAULT_ADMISSION)
    parser.add_argument("--postprocess", type=Path, default=DEFAULT_POSTPROCESS)
    parser.add_argument("--score-contribution", type=Path, default=DEFAULT_SCORE_CONTRIBUTION)
    parser.add_argument("--source-packaging", type=Path, default=DEFAULT_SOURCE_PACKAGING)
    parser.add_argument("--inventory-replay", type=Path, default=DEFAULT_INVENTORY_REPLAY)
    parser.add_argument("--helper-runtime-smoke", type=Path, default=DEFAULT_HELPER_RUNTIME_SMOKE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_productization_readiness_report(
        prompt_bakeoff_payload=_load_json(args.prompt_bakeoff),
        admission_payload=_load_json(args.admission),
        postprocess_payload=_load_json(args.postprocess),
        score_contribution_payload=_load_json(args.score_contribution),
        source_packaging_payload=_load_json_if_exists(args.source_packaging),
        inventory_replay_payload=_load_json_if_exists(args.inventory_replay),
        helper_runtime_smoke_payload=_load_json_if_exists(args.helper_runtime_smoke),
        prompt_bakeoff_path=args.prompt_bakeoff,
        admission_path=args.admission,
        postprocess_path=args.postprocess,
        score_contribution_path=args.score_contribution,
        source_packaging_path=args.source_packaging,
        inventory_replay_path=args.inventory_replay,
        helper_runtime_smoke_path=args.helper_runtime_smoke,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_productization_readiness_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_productization_readiness_report(
    *,
    prompt_bakeoff_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    score_contribution_payload: Mapping[str, object],
    source_packaging_payload: Mapping[str, object] | None = None,
    inventory_replay_payload: Mapping[str, object] | None = None,
    helper_runtime_smoke_payload: Mapping[str, object] | None = None,
    prompt_bakeoff_path: Path | None = None,
    admission_path: Path | None = None,
    postprocess_path: Path | None = None,
    score_contribution_path: Path | None = None,
    source_packaging_path: Path | None = None,
    inventory_replay_path: Path | None = None,
    helper_runtime_smoke_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    policy = resolve_semantic_decision_policy(pair="en-es")
    candidate = _candidate_summary(
        prompt_bakeoff_payload=prompt_bakeoff_payload,
        admission_payload=admission_payload,
        postprocess_payload=postprocess_payload,
        score_contribution_payload=score_contribution_payload,
    )
    source_packaging_ready = (
        isinstance(source_packaging_payload, Mapping)
        and str(source_packaging_payload.get("status") or "") == "ok"
    )
    inventory_replay_ready = (
        isinstance(inventory_replay_payload, Mapping)
        and str(inventory_replay_payload.get("status") or "") == "ok"
    )
    helper_runtime_smoke_ready = (
        isinstance(helper_runtime_smoke_payload, Mapping)
        and str(helper_runtime_smoke_payload.get("status") or "") == "ok"
    )
    readiness_checks = _readiness_checks(
        prompt_bakeoff_payload=prompt_bakeoff_payload,
        admission_payload=admission_payload,
        score_contribution_payload=score_contribution_payload,
        candidate=candidate,
        source_packaging_payload=source_packaging_payload,
        inventory_replay_payload=inventory_replay_payload,
        helper_runtime_smoke_payload=helper_runtime_smoke_payload,
    )
    issue_count = sum(1 for check in readiness_checks if check["result"] == "fail")
    block_count = sum(1 for check in readiness_checks if check["result"] == "block")
    status = "ok" if issue_count == 0 else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            (
                "active_only_candidate_ready_for_manual_testing"
                if helper_runtime_smoke_ready
                else "active_only_candidate_ready_for_inventory_compile"
                if source_packaging_ready and not inventory_replay_ready
                else "active_only_candidate_ready_for_runtime_smoke"
                if inventory_replay_ready
                else "active_only_candidate_ready_for_source_packaging"
            )
            if status == "ok"
            else "active_only_candidate_inputs_need_review"
        ),
        "runtime_publication_status": (
            "manual_testing_ready"
            if helper_runtime_smoke_ready
            else "inventory_compile_required"
            if source_packaging_ready and not inventory_replay_ready
            else "runtime_smoke_required"
            if inventory_replay_ready
            else ("source_packaging_required" if block_count else "runtime_packaging_unblocked")
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "product_stance": {
            "mode": "soft_assist",
            "harmful_replacements_allowed": True,
            "runtime_ux": "binary_replace_or_do_not_replace",
            "threshold_change_requested": False,
            "runtime_policy_change_requested": False,
        },
        "inputs": {
            "prompt_bakeoff_path": _repo_path(prompt_bakeoff_path),
            "admission_path": _repo_path(admission_path),
            "postprocess_path": _repo_path(postprocess_path),
            "score_contribution_path": _repo_path(score_contribution_path),
            "source_packaging_path": _repo_path(source_packaging_path),
            "inventory_replay_path": _repo_path(inventory_replay_path),
            "helper_runtime_smoke_path": _repo_path(helper_runtime_smoke_path),
        },
        "current_runtime_policy": {
            "policy_id": policy.policy_id,
            "scorer_id": policy.scorer_id,
            "context_view": policy.context_view,
            "evidence_view": policy.evidence_view,
            "min_active_score": policy.min_active_score,
            "min_margin": policy.min_margin,
            "phrase_control_mode": policy.phrase_control_mode,
            "active_rescue_mode": policy.active_rescue_mode,
        },
        "source_to_runtime_seams": {
            "semantic_evidence_normalization_version": SEMANTIC_EVIDENCE_NORMALIZATION_VERSION,
            "semantic_evidence_normalizer_available": True,
            "semantic_inventory_publication_available": callable(
                build_semantic_inventory_from_results
            ),
            "canonical_source_packaging_available": source_packaging_ready,
            "inventory_shaped_replay_available": inventory_replay_ready,
            "helper_runtime_smoke_available": helper_runtime_smoke_ready,
            "packaged_canonical_row_count": int(
                _as_mapping(_as_mapping(source_packaging_payload).get("summary")).get(
                    "packaged_row_count"
                )
                or 0
            ),
            "inventory_replay_case_count": int(
                _as_mapping(_as_mapping(inventory_replay_payload).get("summary")).get("case_count")
                or 0
            ),
            "helper_runtime_smoke_case_count": int(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "case_count"
                )
                or 0
            ),
            "helper_runtime_smoke_fallback_decision_count": int(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "fallback_decision_count"
                )
                or 0
            ),
            "helper_runtime_smoke_decision_accuracy": float(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "decision_accuracy"
                )
                or 0.0
            ),
            "helper_runtime_smoke_replace_recall": float(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "replace_recall"
                )
                or 0.0
            ),
            "helper_runtime_smoke_harmful_replace_count": int(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "harmful_replace_count"
                )
                or 0
            ),
            "helper_runtime_smoke_false_abstain_count": int(
                _as_mapping(_as_mapping(helper_runtime_smoke_payload).get("summary")).get(
                    "false_abstain_count"
                )
                or 0
            ),
            "generated_rows_are_research_admission_rows": True,
            "llm_rows_compiled_into_runtime_inventory": helper_runtime_smoke_ready,
        },
        "candidate": candidate,
        "readiness_checks": readiness_checks,
        "blocking_next_work": _blocking_next_work(
            source_packaging_ready=source_packaging_ready,
            inventory_replay_ready=inventory_replay_ready,
            helper_runtime_smoke_ready=helper_runtime_smoke_ready,
        ),
        "non_goals_for_this_slice": [
            "do not tune runtime thresholds",
            "do not promote v6 prompt wording",
            "do not use generated shadows or no-winner rows for production",
            "do not claim full en-es product accuracy from the 24-family PoC denominator",
        ],
    }


def render_productization_readiness_markdown(report: Mapping[str, object]) -> str:
    candidate = _as_mapping(report.get("candidate"))
    metrics = _as_mapping(candidate.get("score_metrics"))
    delta = _as_mapping(candidate.get("score_delta"))
    policy = _as_mapping(report.get("current_runtime_policy"))
    seams = _as_mapping(report.get("source_to_runtime_seams"))
    lines = [
        "# en-es Semantic Veto Productization Readiness",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Runtime publication status: `{report.get('runtime_publication_status', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "",
        "## Candidate",
        "",
        f"- Prompt variant: `{candidate.get('prompt_variant_id', '')}`",
        f"- Application mode: `{candidate.get('application_mode', '')}`",
        f"- Postprocess view: `{candidate.get('postprocess_view_id', '')}`",
        f"- Admitted active evidence items: `{candidate.get('admitted_item_count', 0)}`",
        f"- Rejected generated items: `{candidate.get('rejected_item_count', 0)}`",
        f"- Score cases: `{metrics.get('cases_total', 0)}`",
        f"- Decision accuracy: `{_fmt(metrics.get('decision_accuracy'))}` "
        f"(`{_fmt_delta(delta.get('decision_accuracy_delta'))}`)",
        f"- Replace recall: `{_fmt(metrics.get('replace_recall'))}` "
        f"(`{_fmt_delta(delta.get('replace_recall_delta'))}`)",
        f"- False abstains: `{metrics.get('false_abstain_count', 0)}` "
        f"(`{_fmt_int_delta(delta.get('false_abstain_delta'))}`)",
        f"- Harmful replaces: `{metrics.get('harmful_replace_count', 0)}` "
        f"(`{_fmt_int_delta(delta.get('harmful_replace_delta'))}`)",
        "",
        "## Runtime State",
        "",
        f"- Current policy: `{policy.get('policy_id', '')}`",
        f"- Scorer/evidence: `{policy.get('scorer_id', '')}` / `{policy.get('evidence_view', '')}`",
        f"- Thresholds: min active `{policy.get('min_active_score', '')}`, "
        f"min margin `{policy.get('min_margin', '')}`",
        f"- LLM rows compiled into runtime inventory: `{seams.get('llm_rows_compiled_into_runtime_inventory')}`",
        f"- Canonical source packaging available: `{seams.get('canonical_source_packaging_available')}`",
        f"- Packaged canonical rows: `{seams.get('packaged_canonical_row_count', 0)}`",
        f"- Inventory-shaped replay available: `{seams.get('inventory_shaped_replay_available')}`",
        f"- Inventory replay cases: `{seams.get('inventory_replay_case_count', 0)}`",
        f"- Helper runtime smoke available: `{seams.get('helper_runtime_smoke_available')}`",
        f"- Helper runtime smoke cases: `{seams.get('helper_runtime_smoke_case_count', 0)}`",
        f"- Helper runtime fallback decisions: "
        f"`{seams.get('helper_runtime_smoke_fallback_decision_count', 0)}`",
        f"- Helper runtime accuracy/recall: "
        f"`{_fmt(seams.get('helper_runtime_smoke_decision_accuracy'))}` / "
        f"`{_fmt(seams.get('helper_runtime_smoke_replace_recall'))}`",
        f"- Helper runtime harmful/false abstain: "
        f"`{seams.get('helper_runtime_smoke_harmful_replace_count', 0)}` / "
        f"`{seams.get('helper_runtime_smoke_false_abstain_count', 0)}`",
        "",
        "## Readiness Checks",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for check in _mapping_rows(report.get("readiness_checks")):
        lines.append(
            f"| `{check.get('check_id', '')}` | `{check.get('result', '')}` | "
            f"{check.get('detail', '')} |"
        )
    lines.extend(["", "## Blocking Next Work", ""])
    lines.extend(f"- {item}" for item in report.get("blocking_next_work", ()))
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- `{item}`" for item in report.get("non_goals_for_this_slice", ()))
    return "\n".join(lines) + "\n"


def _candidate_summary(
    *,
    prompt_bakeoff_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    score_contribution_payload: Mapping[str, object],
) -> dict[str, object]:
    prompt_summary = _as_mapping(prompt_bakeoff_payload.get("summary"))
    admission_summary = _as_mapping(admission_payload.get("summary"))
    postprocess_summary = _as_mapping(postprocess_payload.get("summary"))
    score_summary = _as_mapping(score_contribution_payload.get("summary"))
    comparisons = _as_mapping(score_contribution_payload.get("comparisons"))
    base_metrics = _as_mapping(score_summary.get("base"))
    primary_postprocess_view = _view_by_id(
        _mapping_rows(postprocess_payload.get("view_scores")),
        RECOMMENDED_POSTPROCESS_VIEW,
    )
    generated_metrics = _as_mapping(
        primary_postprocess_view.get(RECOMMENDED_APPLICATION_MODE)
        or score_summary.get(RECOMMENDED_APPLICATION_MODE)
    )
    generated_comparison = _as_mapping(
        primary_postprocess_view.get("comparison") or comparisons.get(RECOMMENDED_APPLICATION_MODE)
    )
    return {
        "prompt_variant_id": str(
            prompt_summary.get("best_primary_variant_id") or RECOMMENDED_PROMPT_VARIANT
        ),
        "application_mode": RECOMMENDED_APPLICATION_MODE,
        "postprocess_view_id": str(
            prompt_bakeoff_payload.get("primary_view_id") or RECOMMENDED_POSTPROCESS_VIEW
        ),
        "prompt_bakeoff_status": str(prompt_bakeoff_payload.get("status") or ""),
        "admission_status": str(admission_payload.get("status") or ""),
        "postprocess_status": str(postprocess_payload.get("status") or ""),
        "score_contribution_status": str(score_contribution_payload.get("status") or ""),
        "admitted_item_count": int(admission_summary.get("admitted_item_count") or 0),
        "rejected_item_count": int(admission_summary.get("rejected_item_count") or 0),
        "coverage_shortfall_count": int(admission_summary.get("coverage_shortfall_count") or 0),
        "postprocess_flags": {
            "high_eval_overlap_count": int(postprocess_summary.get("high_eval_overlap_count") or 0),
            "medium_eval_overlap_count": int(
                postprocess_summary.get("medium_eval_overlap_count") or 0
            ),
            "definition_like_count": int(postprocess_summary.get("definition_like_count") or 0),
            "pos_weak_count": int(postprocess_summary.get("pos_weak_count") or 0),
            "target_lemma_in_note_count": int(
                postprocess_summary.get("target_lemma_in_note_count") or 0
            ),
        },
        "base_metrics": base_metrics,
        "score_metrics": generated_metrics,
        "score_delta": {
            "decision_accuracy_delta": _float_delta(
                generated_comparison,
                "decision_accuracy_delta",
                generated_metrics,
                base_metrics,
                "decision_accuracy",
            ),
            "replace_recall_delta": _float_delta(
                generated_comparison,
                "replace_recall_delta",
                generated_metrics,
                base_metrics,
                "replace_recall",
            ),
            "winner_accuracy_delta": _float_delta(
                generated_comparison,
                "winner_accuracy_delta",
                generated_metrics,
                base_metrics,
                "winner_accuracy",
            ),
            "false_abstain_delta": _int_delta(
                generated_comparison,
                "false_abstain_delta",
                generated_metrics,
                base_metrics,
                "false_abstain_count",
            ),
            "harmful_replace_delta": _int_delta(
                generated_comparison,
                "harmful_replace_delta",
                generated_metrics,
                base_metrics,
                "harmful_replace_count",
            ),
        },
    }


def _readiness_checks(
    *,
    prompt_bakeoff_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    score_contribution_payload: Mapping[str, object],
    candidate: Mapping[str, object],
    source_packaging_payload: Mapping[str, object] | None,
    inventory_replay_payload: Mapping[str, object] | None,
    helper_runtime_smoke_payload: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    metrics = _as_mapping(candidate.get("score_metrics"))
    delta = _as_mapping(candidate.get("score_delta"))
    checks = [
        _check(
            "prompt_candidate_selected",
            str(candidate.get("prompt_bakeoff_status") or "") == "ok"
            and str(candidate.get("prompt_variant_id") or "") == RECOMMENDED_PROMPT_VARIANT,
            (
                f"best primary prompt is {candidate.get('prompt_variant_id', '')}; "
                f"expected {RECOMMENDED_PROMPT_VARIANT}"
            ),
        ),
        _check(
            "admission_clean",
            str(candidate.get("admission_status") or "") == "ok"
            and int(candidate.get("admitted_item_count") or 0) > 0
            and int(candidate.get("rejected_item_count") or 0) == 0
            and int(candidate.get("coverage_shortfall_count") or 0) == 0,
            (
                f"{candidate.get('admitted_item_count', 0)} admitted; "
                f"{candidate.get('rejected_item_count', 0)} rejected; "
                f"{candidate.get('coverage_shortfall_count', 0)} shortfall"
            ),
        ),
        _check(
            "offline_lift_observed",
            float(delta.get("decision_accuracy_delta") or 0.0) > 0.0
            and int(delta.get("false_abstain_delta") or 0) < 0,
            (
                f"accuracy delta {_fmt_delta(delta.get('decision_accuracy_delta'))}; "
                f"false abstain delta {_fmt_int_delta(delta.get('false_abstain_delta'))}"
            ),
        ),
        _check(
            "soft_assist_harm_budget_preserved",
            int(delta.get("harmful_replace_delta") or 0) <= 0
            and int(metrics.get("harmful_replace_count") or 0) <= 1,
            (
                f"harmful replaces {metrics.get('harmful_replace_count', 0)}; "
                f"delta {_fmt_int_delta(delta.get('harmful_replace_delta'))}"
            ),
        ),
        _check(
            "same_denominator_confirmed",
            _score_status_ok(prompt_bakeoff_payload, admission_payload, score_contribution_payload),
            "prompt, admission, and score artifacts are all status ok",
        ),
    ]
    inventory_replay_ready = (
        isinstance(inventory_replay_payload, Mapping)
        and str(inventory_replay_payload.get("status") or "") == "ok"
    )
    helper_runtime_smoke_ready = (
        isinstance(helper_runtime_smoke_payload, Mapping)
        and str(helper_runtime_smoke_payload.get("status") or "") == "ok"
    )
    if (
        isinstance(source_packaging_payload, Mapping)
        and str(source_packaging_payload.get("status") or "") == "ok"
    ):
        summary = _as_mapping(source_packaging_payload.get("summary"))
        checks.append(
            _check(
                "source_packaging_done",
                int(summary.get("packaged_row_count") or 0) > 0
                and int(summary.get("runtime_publishable_row_count") or 0) == 0,
                (
                    f"{summary.get('packaged_row_count', 0)} canonical rows; "
                    f"{summary.get('runtime_publishable_row_count', 0)} runtime-publishable rows"
                ),
            )
        )
        if inventory_replay_ready:
            replay_summary = _as_mapping(inventory_replay_payload.get("summary"))
            replay_comparison = _as_mapping(replay_summary.get("comparison"))
            checks.append(
                _check(
                    "inventory_replay_done",
                    int(replay_summary.get("case_count") or 0) > 0
                    and int(replay_summary.get("unapplied_row_count") or 0) == 0,
                    (
                        f"{replay_summary.get('case_count', 0)} cases; "
                        f"{replay_summary.get('applied_row_count', 0)} applied rows; "
                        f"accuracy delta {_fmt_delta(replay_comparison.get('decision_accuracy_delta'))}"
                    ),
                )
            )
            if helper_runtime_smoke_ready:
                smoke_summary = _as_mapping(helper_runtime_smoke_payload.get("summary"))
                checks.append(
                    _check(
                        "helper_runtime_smoke_done",
                        int(smoke_summary.get("case_count") or 0) > 0
                        and int(smoke_summary.get("fallback_decision_count") or 0) == 0,
                        (
                            f"{smoke_summary.get('case_count', 0)} cases; "
                            f"{smoke_summary.get('fallback_decision_count', 0)} fallback decisions; "
                            f"accuracy {_fmt(smoke_summary.get('decision_accuracy'))}; "
                            f"recall {_fmt(smoke_summary.get('replace_recall'))}; "
                            f"harmful {smoke_summary.get('harmful_replace_count', 0)}"
                        ),
                    )
                )
            else:
                checks.append(
                    {
                        "check_id": "runtime_smoke_required",
                        "result": "block",
                        "detail": (
                            "inventory-shaped replay passed; the next step must use the actual "
                            "helper publication family and browser/helper semantic-admission path"
                        ),
                    }
                )
        else:
            checks.append(
                {
                    "check_id": "inventory_compile_required",
                    "result": "block",
                    "detail": (
                        "canonical source evidence exists; the next compiler still has to append it "
                        "to ready active-sense evidence_views in a semantic inventory candidate"
                    ),
                }
            )
    else:
        checks.append(
            {
                "check_id": "source_packaging_required",
                "result": "block",
                "detail": (
                    "candidate rows are admitted research evidence; source packaging must turn "
                    "them into canonical semantic evidence before runtime inventory compilation"
                ),
            }
        )
    return checks


def _blocking_next_work(
    *,
    source_packaging_ready: bool,
    inventory_replay_ready: bool,
    helper_runtime_smoke_ready: bool,
) -> list[str]:
    if helper_runtime_smoke_ready:
        return [
            "Use the isolated helper fixture for manual browser/helper testing before mutating any real profile data.",
            "If manual behavior is acceptable, package a bounded real helper candidate or stop the veto lane as a soft-assist PoC.",
            "Keep broader paid generation blocked until the manual smoke confirms the user-facing replace-or-abstain behavior is acceptable.",
        ]
    if inventory_replay_ready:
        return [
            "Build a helper-publication smoke fixture that writes a generation-aligned ruleset, snapshot, semantic inventory, and manifest for the active-only candidate without changing default user data.",
            "Call the helper semantic-admission path against that fixture and verify the browser-facing decision payload remains binary replace-or-abstain.",
            "Only after that smoke passes, decide whether to package a bounded real helper generation or stop before broader paid generation.",
        ]
    if source_packaging_ready:
        return [
            "Compile the canonical active-only anchor cues into semantic inventory evidence views for matching ready active senses.",
            "Replay the frozen 91-case denominator through the inventory-shaped runtime path and compare it to the research augmentation score.",
            "Only after inventory replay matches expectations, republish a generation-aligned ruleset, snapshot, semantic inventory, and manifest, then run helper/runtime semantic-admission smoke tests.",
        ]
    return [
        "Define the source-packaging step that turns admitted active-only evidence rows into canonical semantic evidence records.",
        "Compile those canonical records into the semantic inventory evidence views for matching ready senses without mutating published runtime artifacts by hand.",
        "Republish a generation-aligned ruleset, snapshot, semantic inventory, and manifest, then run helper/runtime semantic-admission smoke tests.",
    ]


def _check(check_id: str, condition: bool, detail: str) -> dict[str, object]:
    return {
        "check_id": check_id,
        "result": "pass" if condition else "fail",
        "detail": detail,
    }


def _score_status_ok(*payloads: Mapping[str, object]) -> bool:
    return all(str(payload.get("status") or "") == "ok" for payload in payloads)


def _float_delta(
    comparison: Mapping[str, object],
    comparison_key: str,
    generated: Mapping[str, object],
    base: Mapping[str, object],
    metric_key: str,
) -> float:
    if comparison_key in comparison:
        return float(comparison.get(comparison_key) or 0.0)
    return float(generated.get(metric_key) or 0.0) - float(base.get(metric_key) or 0.0)


def _int_delta(
    comparison: Mapping[str, object],
    comparison_key: str,
    generated: Mapping[str, object],
    base: Mapping[str, object],
    metric_key: str,
) -> int:
    if comparison_key in comparison:
        return int(comparison.get(comparison_key) or 0)
    return int(generated.get(metric_key) or 0) - int(base.get(metric_key) or 0)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_if_exists(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _view_by_id(
    view_rows: Sequence[Mapping[str, object]],
    view_id: str,
) -> Mapping[str, object]:
    for row in view_rows:
        if str(row.get("view_id") or "") == view_id:
            return row
    return {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _fmt(value: object) -> str:
    return f"{float(value or 0.0):.4f}"


def _fmt_delta(value: object) -> str:
    number = float(value or 0.0)
    return f"{number:+.4f}"


def _fmt_int_delta(value: object) -> str:
    number = int(value or 0)
    return f"{number:+d}"


if __name__ == "__main__":
    raise SystemExit(main())
