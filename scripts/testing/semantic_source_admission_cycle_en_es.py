#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_example_frame_batch_merge_en_es import (  # noqa: E402
    DEFAULT_BASE_BATCH_JSON,
    build_merged_example_frame_batch_report,
    render_merged_example_frame_batch_markdown,
)
from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
    render_example_frame_contract_markdown,
)
from semantic_llm_example_frame_leakage_audit_en_es import (  # noqa: E402
    build_example_frame_leakage_audit_report,
    render_example_frame_leakage_audit_markdown,
)
from semantic_llm_example_frame_sense_discrimination_audit_en_es import (  # noqa: E402
    build_example_frame_sense_discrimination_audit_report,
    render_example_frame_sense_discrimination_audit_markdown,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_llm_prototype_ablation_matrix_en_es import (  # noqa: E402
    build_prototype_ablation_matrix_report,
)
from semantic_llm_prototype_ablation_matrix_rendering import (  # noqa: E402
    render_prototype_ablation_matrix_markdown,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_CANDIDATE_BATCH_JSON = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-balanced-plus-source-coverage-filtered-safe-v2-20260425a_normalized_evidence.json"
)
DEFAULT_PREFIX = "semantic_source_admission_cycle_latest"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / f"{DEFAULT_PREFIX}.md"
DEFAULT_FILTERED_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-source-admission-cycle-filtered-latest_normalized_evidence.json"
)
DEFAULT_SENSE_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-source-admission-cycle-sense-admitted-latest_normalized_evidence.json"
)
DEFAULT_MERGED_BATCH_OUT = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-source-admission-cycle-merged-latest_normalized_evidence.json"
)
DEFAULT_SCORERS = ("sentence_transformer_cosine",)
DEFAULT_SENSE_MIN_INTENDED_SCORE = 0.5
DEFAULT_SENSE_MIN_MARGIN = 0.0
DEFAULT_BATCH_ID = "en-es:example-frame-composite:source-admission-cycle-latest"
DEFAULT_SOURCE_ID = "source_admission_cycle_candidate"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the no-spend source-admission cycle for an existing candidate evidence batch: "
            "leakage/duplicate audit, merge, final-composite sense-discrimination audit, "
            "split contract, and optional ablation matrix."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--required-family-json", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--base-batch-json", type=Path, default=DEFAULT_BASE_BATCH_JSON)
    parser.add_argument(
        "--empty-base",
        action="store_true",
        help="Use an empty internal base batch so the candidate source is admitted by itself.",
    )
    parser.add_argument("--candidate-batch-json", type=Path, default=DEFAULT_CANDIDATE_BATCH_JSON)
    parser.add_argument(
        "--prior-batch-json",
        action="append",
        default=[],
        type=Path,
        help=(
            "Optional prior source batch for duplicate admission checks. The base batch is "
            "always included as a prior source before these extras."
        ),
    )
    parser.add_argument(
        "--heldout-validation-json",
        type=Path,
        default=None,
        help=(
            "Optional semantic-source held-out validation artifact. When supplied, a "
            "failing held-out artifact blocks offline promotion status; a passing seed "
            "artifact moves the runtime blocker to broader held-out breadth."
        ),
    )
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--sense-scorers", default=",".join(DEFAULT_SCORERS))
    parser.add_argument(
        "--sense-min-intended-score", type=float, default=DEFAULT_SENSE_MIN_INTENDED_SCORE
    )
    parser.add_argument("--sense-min-margin", type=float, default=DEFAULT_SENSE_MIN_MARGIN)
    parser.add_argument("--skip-ablation", action="store_true")
    parser.add_argument("--ablation-scorers", default="sentence_transformer_cosine")
    parser.add_argument("--ablation-scopes", default="all_dataset_families")
    parser.add_argument("--ablation-context-views", default="masked_sentence")
    parser.add_argument("--ablation-min-active-grid", default="0.0,0.35")
    parser.add_argument("--ablation-min-margin-grid", default="0.0,0.05")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--filtered-batch-out", type=Path, default=DEFAULT_FILTERED_BATCH_OUT)
    parser.add_argument("--sense-batch-out", type=Path, default=DEFAULT_SENSE_BATCH_OUT)
    parser.add_argument("--merged-batch-out", type=Path, default=DEFAULT_MERGED_BATCH_OUT)
    parser.add_argument(
        "--candidate-admitted-batch-out",
        type=Path,
        default=None,
        help=(
            "Optional normalized batch containing only candidate rows that survived "
            "the leakage/duplicate filter and final sense-discrimination audit."
        ),
    )
    return parser.parse_args()


def build_source_admission_cycle_bundle(
    *,
    dataset_payload: Mapping[str, object],
    queue_payload: Mapping[str, object],
    required_family_payload: Mapping[str, object],
    base_batch_payload: Mapping[str, object],
    candidate_batch_payload: Mapping[str, object],
    prior_batch_payloads: Sequence[Mapping[str, object]] = (),
    heldout_validation_payload: Mapping[str, object] | None = None,
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = DEFAULT_SOURCE_ID,
    sense_scorers: Sequence[str] = DEFAULT_SCORERS,
    sense_min_intended_score: float = DEFAULT_SENSE_MIN_INTENDED_SCORE,
    sense_min_margin: float = DEFAULT_SENSE_MIN_MARGIN,
    run_ablation: bool = True,
    ablation_scorers: Sequence[str] = DEFAULT_SCORERS,
    ablation_scopes: Sequence[str] = ("all_dataset_families",),
    ablation_context_views: Sequence[str] = ("masked_sentence",),
    ablation_min_active_scores: Sequence[float] = (0.0, 0.35),
    ablation_min_margins: Sequence[float] = (0.0, 0.05),
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    leakage_report = build_example_frame_leakage_audit_report(
        dataset_payload=dataset_payload,
        batch_payload=candidate_batch_payload,
        prior_batch_payloads=(base_batch_payload, *prior_batch_payloads),
        generated_at=generated_at,
    )
    filtered_batch = leakage_report["filtered_batch"]
    merge_report = build_merged_example_frame_batch_report(
        base_batch_payload=base_batch_payload,
        add_batch_payloads=[filtered_batch],
        batch_id=batch_id,
        source_id=source_id,
        generated_at=generated_at,
    )
    pre_sense_merged_batch = merge_report["merged_batch"]
    sense_report = build_example_frame_sense_discrimination_audit_report(
        dataset_payload=dataset_payload,
        batch_payload=pre_sense_merged_batch,
        scorers=sense_scorers,
        min_intended_score=sense_min_intended_score,
        min_margin=sense_min_margin,
        generated_at=generated_at,
    )
    merged_batch = sense_report["admitted_batch"]
    candidate_admitted_batch = _build_candidate_admitted_batch(
        candidate_batch_payload=candidate_batch_payload,
        filtered_candidate_batch=filtered_batch,
        admitted_batch=merged_batch,
        source_cycle_batch_id=batch_id,
        generated_at=generated_at,
    )
    contract_report = build_example_frame_contract_report(
        merged_batch,
        required_family_keys=_required_family_keys(required_family_payload),
        generated_at=generated_at,
    )
    ablation_report = (
        build_prototype_ablation_matrix_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            source_modes=("cycle_merged",),
            scopes=ablation_scopes,
            scorers=ablation_scorers,
            context_views=ablation_context_views,
            min_active_scores=ablation_min_active_scores,
            min_margins=ablation_min_margins,
            source_payload_overrides={"cycle_merged": merged_batch},
            generated_at=generated_at,
        )
        if run_ablation
        else None
    )
    report = _build_cycle_report(
        generated_at=generated_at,
        leakage_report=leakage_report,
        sense_report=sense_report,
        merge_report=merge_report,
        contract_report=contract_report,
        ablation_report=ablation_report,
        heldout_validation_report=heldout_validation_payload,
    )
    return {
        "report": report,
        "leakage_report": leakage_report,
        "filtered_batch": filtered_batch,
        "sense_report": sense_report,
        "sense_batch": merged_batch,
        "candidate_admitted_batch": candidate_admitted_batch,
        "merge_report": merge_report,
        "merged_batch": merged_batch,
        "contract_report": contract_report,
        "ablation_report": ablation_report,
    }


def write_source_admission_cycle_bundle(
    *,
    bundle: Mapping[str, object],
    json_out: Path,
    markdown_out: Path,
    filtered_batch_out: Path,
    sense_batch_out: Path,
    merged_batch_out: Path,
    candidate_admitted_batch_out: Path | None = None,
) -> None:
    _write_json(filtered_batch_out, _as_mapping(bundle["filtered_batch"]))
    _write_json(sense_batch_out, _as_mapping(bundle["sense_batch"]))
    _write_json(merged_batch_out, _as_mapping(bundle["merged_batch"]))
    _write_sidecar_artifacts(json_out, bundle)
    if candidate_admitted_batch_out is not None:
        _write_json(candidate_admitted_batch_out, _as_mapping(bundle["candidate_admitted_batch"]))
        report = bundle.get("report")
        if isinstance(report, dict):
            report["artifacts"] = {
                **_as_mapping(report.get("artifacts")),
                "candidate_admitted_batch_json": str(candidate_admitted_batch_out),
            }
    _write_json(json_out, _as_mapping(bundle["report"]))
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_source_admission_cycle_markdown(bundle), encoding="utf-8")


def render_source_admission_cycle_markdown(bundle: Mapping[str, object]) -> str:
    report = _as_mapping(bundle["report"])
    summary = _as_mapping(report.get("summary"))
    best = _as_mapping(summary.get("best_ablation_row"))
    residuals = _as_mapping(report.get("residuals"))
    policy = _as_mapping(report.get("policy"))
    heldout = _as_mapping(summary.get("heldout_validation"))
    runtime_blockers = _as_sequence(policy.get("runtime_publication_blockers"))
    lines = [
        "# en-es Semantic Source Admission Cycle",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "",
        "## Gate Summary",
        "",
        f"- Leakage rejected rows: `{summary.get('leakage_rejected_row_count', 0)}`",
        f"- Sense rejected rows: `{summary.get('sense_rejected_row_count', 0)}`",
        f"- Pre-sense merged rows: `{summary.get('pre_sense_merged_row_count', 0)}`",
        f"- Final admitted rows: `{summary.get('final_admitted_row_count', 0)}`",
        f"- Semantic contract: `{summary.get('semantic_contract_complete_family_count', 0)}` / `{summary.get('families_total', 0)}`",
        f"- Phrase contract: `{summary.get('phrase_contract_complete_family_count', 0)}` / `{summary.get('families_total', 0)}`",
        f"- Combined contract status: `{summary.get('contract_status', '')}`",
        f"- Held-out validation: `{heldout.get('status', 'not_provided')}` / `{heldout.get('decision', '')}`",
        f"- Held-out cases: `{heldout.get('case_count', 0)}`",
        f"- Held-out harmful / false abstain: `{heldout.get('harmful_replace_count', 0)}` / `{heldout.get('false_abstain_count', 0)}`",
        f"- Offline lane: `{policy.get('offline_promotion_lane', '')}` / `{policy.get('offline_semantic_lane_status', '')}`",
        f"- Runtime publication: `{policy.get('runtime_publication_status', '')}`",
    ]
    if runtime_blockers:
        lines.append(
            "- Runtime blockers: " + ", ".join(f"`{str(blocker)}`" for blocker in runtime_blockers)
        )
    lines.extend(["", "## Best Ablation", ""])
    if best:
        lines.extend(
            [
                f"- Source: `{best.get('source_mode', '')}`",
                f"- Shape: `{best.get('decision_shape', '')}`",
                f"- Metrics: `{_pct(best.get('decision_accuracy'))}` accuracy / `{_pct(best.get('replace_recall'))}` recall / `{best.get('harmful_replace_count', 0)}` harmful / `{best.get('false_abstain_count', 0)}` false abstains",
            ]
        )
    else:
        lines.append("- Ablation was skipped or produced no candidate-source row.")
    lines.extend(
        [
            "",
            "## Residuals",
            "",
            f"- Semantic gap families: `{len(_as_sequence(residuals.get('semantic_gap_family_keys')))}`",
            f"- Phrase gap families: `{len(_as_sequence(residuals.get('phrase_containment_gap_family_keys')))}`",
            f"- Harmful ablation cases: `{len(_as_sequence(residuals.get('harmful_replace_case_ids')))}`",
            f"- False-abstain ablation cases: `{len(_as_sequence(residuals.get('false_abstain_case_ids')))}`",
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, path in _as_mapping(report.get("artifacts")).items():
        lines.append(f"- {label}: `{path}`")
    return "\n".join(lines) + "\n"


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _build_candidate_admitted_batch(
    *,
    candidate_batch_payload: Mapping[str, object],
    filtered_candidate_batch: Mapping[str, object],
    admitted_batch: Mapping[str, object],
    source_cycle_batch_id: str,
    generated_at: str,
) -> dict[str, object]:
    filtered_candidate_keys = {
        _row_key(row)
        for row in filtered_candidate_batch.get("rows", ())
        if isinstance(row, Mapping)
    }
    rows = [
        dict(row)
        for row in admitted_batch.get("rows", ())
        if isinstance(row, Mapping) and _row_key(row) in filtered_candidate_keys
    ]
    batch_id = str(candidate_batch_payload.get("batch_id") or "").strip()
    source_id = str(candidate_batch_payload.get("source_id") or "").strip()
    payload = dict(candidate_batch_payload)
    payload.update(
        {
            "batch_id": f"{batch_id}:candidate-admitted" if batch_id else "candidate-admitted",
            "source_id": (f"{source_id}_candidate_admitted" if source_id else "candidate_admitted"),
            "generated_at": generated_at,
            "ingested_at": generated_at,
            "review_state": "admitted_by_semantic_source_cycle",
            "row_count": len(rows),
            "rows": rows,
        }
    )
    provenance = _as_mapping(payload.get("provenance"))
    provenance["admission_cycle"] = {
        "source_cycle_batch_id": source_cycle_batch_id,
        "filtered_candidate_row_count": len(filtered_candidate_keys),
        "admitted_candidate_row_count": len(rows),
    }
    payload["provenance"] = provenance
    return payload


def _row_key(row: Mapping[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("source_id") or "").strip(),
        str(row.get("row_id") or "").strip(),
        str(row.get("relation_type") or "").strip(),
        str(row.get("evidence_text") or "").strip(),
    )


def _build_cycle_report(
    *,
    generated_at: str,
    leakage_report: Mapping[str, object],
    sense_report: Mapping[str, object],
    merge_report: Mapping[str, object],
    contract_report: Mapping[str, object],
    ablation_report: Mapping[str, object] | None,
    heldout_validation_report: Mapping[str, object] | None = None,
) -> dict[str, object]:
    leakage_summary = _as_mapping(leakage_report.get("summary"))
    sense_summary = _as_mapping(sense_report.get("summary"))
    merge_summary = _as_mapping(merge_report.get("summary"))
    contract_summary = _as_mapping(contract_report.get("summary"))
    best = (
        _as_mapping(ablation_report.get("best_candidate_source_row"))
        if isinstance(ablation_report, Mapping)
        else {}
    )
    harmful = int(best.get("harmful_replace_count") or 0) if best else 0
    false_abstain = int(best.get("false_abstain_count") or 0) if best else 0
    semantic_complete = bool(contract_summary.get("semantic_contract_complete"))
    phrase_complete = bool(contract_summary.get("phrase_containment_contract_complete"))
    combined_complete = bool(contract_summary.get("contract_complete"))
    heldout_summary = _build_heldout_validation_summary(heldout_validation_report)
    gate_clean = (
        int(leakage_summary.get("rejected_row_count") or 0) == 0
        and semantic_complete
        and (not best or harmful == 0)
        and not bool(heldout_summary.get("blocks_offline_semantic_promotion"))
    )
    decision = (
        "promotion_candidate" if gate_clean and best and false_abstain == 0 else "analysis_only"
    )
    residuals = _build_residuals(contract_summary=contract_summary, best_ablation_row=best)
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok" if gate_clean else "review",
        "decision": decision,
        "policy": _build_policy_summary(
            decision=decision,
            semantic_complete=semantic_complete,
            phrase_complete=phrase_complete,
            combined_complete=combined_complete,
            heldout_validation=heldout_summary,
        ),
        "summary": {
            "leakage_status": str(leakage_report.get("status") or "").strip(),
            "leakage_rejected_row_count": int(leakage_summary.get("rejected_row_count") or 0),
            "sense_status": str(sense_report.get("status") or "").strip(),
            "sense_rejected_row_count": int(sense_summary.get("semantic_rejected_row_count") or 0),
            "pre_sense_merged_row_count": int(merge_summary.get("row_count") or 0),
            "final_admitted_row_count": int(sense_summary.get("admitted_row_count") or 0),
            "contract_status": str(contract_report.get("status") or "").strip(),
            "semantic_gate_status": "ok" if semantic_complete else "review",
            "phrase_contract_status": "ok" if phrase_complete else "review",
            "combined_contract_status": "ok" if combined_complete else "review",
            "families_total": int(contract_summary.get("families_total") or 0),
            "semantic_contract_complete_family_count": int(
                contract_summary.get("semantic_contract_complete_family_count") or 0
            ),
            "phrase_contract_complete_family_count": int(
                contract_summary.get("phrase_containment_contract_complete_family_count") or 0
            ),
            "heldout_validation": heldout_summary,
            "best_ablation_row": best,
        },
        "residuals": residuals,
        "artifacts": {},
    }


def _build_policy_summary(
    *,
    decision: str,
    semantic_complete: bool,
    phrase_complete: bool,
    combined_complete: bool,
    heldout_validation: Mapping[str, object],
) -> dict[str, object]:
    runtime_blockers = []
    if decision == "promotion_candidate":
        if not phrase_complete:
            runtime_blockers.append("runtime_phrase_source_policy")
        if not heldout_validation.get("provided"):
            runtime_blockers.append("held_out_non_benchmark_validation")
        elif heldout_validation.get("passed"):
            runtime_blockers.append("broader_heldout_breadth")
        else:
            runtime_blockers.append("held_out_non_benchmark_validation_failed")
        runtime_blockers.append("runtime_packaging_feasibility")
    return {
        "offline_promotion_lane": "semantic_active_shadow",
        "offline_semantic_lane_status": decision,
        "runtime_publication_status": "blocked" if runtime_blockers else "not_assessed",
        "runtime_publication_blockers": runtime_blockers,
        "contract_lanes": {
            "semantic_active_shadow": {
                "status": "ok" if semantic_complete else "review",
                "blocks_offline_semantic_promotion": not semantic_complete,
            },
            "phrase_containment": {
                "status": "ok" if phrase_complete else "review",
                "blocks_offline_semantic_promotion": False,
                "blocks_runtime_publication_until_policy_decision": not phrase_complete,
            },
            "combined_legacy_contract": {
                "status": "ok" if combined_complete else "review",
                "blocks_offline_semantic_promotion": False,
            },
            "held_out_seed_validation": {
                "status": str(heldout_validation.get("status") or "not_provided"),
                "decision": str(heldout_validation.get("decision") or ""),
                "blocks_offline_semantic_promotion": bool(
                    heldout_validation.get("blocks_offline_semantic_promotion")
                ),
                "blocks_runtime_publication_until_broader_breadth": bool(
                    heldout_validation.get("passed")
                ),
            },
        },
    }


def _build_heldout_validation_summary(
    payload: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {
            "provided": False,
            "passed": False,
            "status": "not_provided",
            "decision": "not_provided",
            "case_count": 0,
            "family_count": 0,
            "harmful_replace_count": 0,
            "false_abstain_count": 0,
            "replace_recall": 0.0,
            "decision_accuracy": 0.0,
            "blocks_offline_semantic_promotion": False,
        }
    summary = _as_mapping(payload.get("summary"))
    status = str(payload.get("status") or summary.get("status") or "").strip()
    decision = str(payload.get("decision") or summary.get("decision") or "").strip()
    harmful = int(summary.get("harmful_replace_count") or 0)
    false_abstain = int(summary.get("false_abstain_count") or 0)
    passed = status == "ok" and decision == "heldout_pass" and harmful == 0 and false_abstain == 0
    return {
        "provided": True,
        "passed": passed,
        "status": status or "unknown",
        "decision": decision or "unknown",
        "case_count": int(summary.get("case_count") or 0),
        "family_count": int(summary.get("family_count") or 0),
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "replace_recall": float(summary.get("replace_recall") or 0.0),
        "decision_accuracy": float(summary.get("decision_accuracy") or 0.0),
        "blocks_offline_semantic_promotion": not passed,
    }


def _build_residuals(
    *,
    contract_summary: Mapping[str, object],
    best_ablation_row: Mapping[str, object],
) -> dict[str, object]:
    return {
        "semantic_gap_family_keys": list(
            _as_sequence(contract_summary.get("semantic_gap_family_keys"))
        ),
        "phrase_containment_gap_family_keys": list(
            _as_sequence(contract_summary.get("phrase_containment_gap_family_keys"))
        ),
        "harmful_replace_case_ids": list(
            _as_sequence(best_ablation_row.get("harmful_replace_case_ids"))
        ),
        "false_abstain_case_ids": list(
            _as_sequence(best_ablation_row.get("false_abstain_case_ids"))
        ),
    }


def _write_sidecar_artifacts(json_out: Path, bundle: Mapping[str, object]) -> None:
    prefix = json_out.with_suffix("")
    sidecars = [
        ("leakage", "leakage_report", render_example_frame_leakage_audit_markdown),
        ("sense", "sense_report", render_example_frame_sense_discrimination_audit_markdown),
        ("merge", "merge_report", render_merged_example_frame_batch_markdown),
        ("contract", "contract_report", render_example_frame_contract_markdown),
    ]
    report = bundle.get("report")
    artifacts: dict[str, str] = (
        _as_mapping(report.get("artifacts")) if isinstance(report, Mapping) else {}
    )
    for suffix, key, renderer in sidecars:
        payload = _as_mapping(bundle[key])
        json_path = prefix.parent / f"{prefix.name}_{suffix}.json"
        md_path = prefix.parent / f"{prefix.name}_{suffix}.md"
        _write_json(
            json_path,
            {
                item_key: value
                for item_key, value in payload.items()
                if item_key not in _embedded_keys(key)
            },
        )
        md_path.write_text(renderer(payload), encoding="utf-8")
        artifacts[f"{suffix}_json"] = str(json_path)
        artifacts[f"{suffix}_markdown"] = str(md_path)
    ablation = bundle.get("ablation_report")
    if isinstance(ablation, Mapping):
        json_path = prefix.parent / f"{prefix.name}_ablation.json"
        md_path = prefix.parent / f"{prefix.name}_ablation.md"
        _write_json(json_path, ablation)
        md_path.write_text(render_prototype_ablation_matrix_markdown(ablation), encoding="utf-8")
        artifacts["ablation_json"] = str(json_path)
        artifacts["ablation_markdown"] = str(md_path)
    if isinstance(report, dict):
        report["artifacts"] = artifacts


def _embedded_keys(key: str) -> set[str]:
    if key == "leakage_report":
        return {"filtered_batch"}
    if key == "sense_report":
        return {"admitted_batch"}
    if key == "merge_report":
        return {"merged_batch"}
    return set()


def _required_family_keys(payload: Mapping[str, object]) -> list[str]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("required-family payload must contain a `families` array.")
    return [
        str(family.get("family_id") or "").strip()
        for family in families
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    ]


def _normalize_strings(value: Sequence[str] | str) -> list[str]:
    values = value.split(",") if isinstance(value, str) else value
    return [str(item or "").strip() for item in values if str(item or "").strip()]


def _normalize_floats(value: str) -> list[float]:
    return [float(item) for item in _normalize_strings(value)]


def _empty_base_batch(*, generated_at: str | None = None) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "en-es:example-frame-empty-base",
        "pair": "en-es",
        "source_type": "internal",
        "source_id": "empty_source_admission_base",
        "source_family": "internal_rulegen_artifact",
        "roles": ["discrimination"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "not_applicable",
        "prompt_version": "empty-source-admission-base-v1",
        "row_count": 0,
        "rows": [],
        "provenance": {
            "source_note": "synthetic empty base for source-admission cycle isolation",
        },
    }


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    bundle = build_source_admission_cycle_bundle(
        dataset_payload=dataset_payload,
        queue_payload=_load_json(args.queue_json),
        required_family_payload=_load_json(args.required_family_json),
        base_batch_payload=_empty_base_batch()
        if args.empty_base
        else _load_json(args.base_batch_json),
        candidate_batch_payload=_load_json(args.candidate_batch_json),
        prior_batch_payloads=[_load_json(path) for path in args.prior_batch_json],
        heldout_validation_payload=_load_json(args.heldout_validation_json)
        if args.heldout_validation_json
        else None,
        batch_id=str(args.batch_id or "").strip() or DEFAULT_BATCH_ID,
        source_id=str(args.source_id or "").strip() or DEFAULT_SOURCE_ID,
        sense_scorers=_normalize_strings(str(args.sense_scorers or "")),
        sense_min_intended_score=float(args.sense_min_intended_score),
        sense_min_margin=float(args.sense_min_margin),
        run_ablation=not bool(args.skip_ablation),
        ablation_scorers=_normalize_strings(str(args.ablation_scorers or "")),
        ablation_scopes=_normalize_strings(str(args.ablation_scopes or "")),
        ablation_context_views=_normalize_strings(str(args.ablation_context_views or "")),
        ablation_min_active_scores=_normalize_floats(str(args.ablation_min_active_grid or "")),
        ablation_min_margins=_normalize_floats(str(args.ablation_min_margin_grid or "")),
    )
    if args.heldout_validation_json:
        report = bundle.get("report")
        if isinstance(report, dict):
            report["artifacts"] = {
                **_as_mapping(report.get("artifacts")),
                "heldout_validation_json": str(args.heldout_validation_json),
            }
    write_source_admission_cycle_bundle(
        bundle=bundle,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
        filtered_batch_out=args.filtered_batch_out,
        sense_batch_out=args.sense_batch_out,
        merged_batch_out=args.merged_batch_out,
        candidate_admitted_batch_out=args.candidate_admitted_batch_out,
    )
    report = _as_mapping(bundle["report"])
    print(f"Wrote source-admission cycle JSON to {args.json_out}")
    print(f"Wrote source-admission cycle Markdown to {args.markdown_out}")
    print(f"Source-admission cycle status: {report.get('status')}")
    return 0 if report.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
