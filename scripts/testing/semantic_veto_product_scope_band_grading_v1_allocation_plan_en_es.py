#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(Path(__file__).resolve().parent),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
    _safe_float,
)
from semantic_veto_product_scope_band_grading_en_es import _assign_bands  # noqa: E402
from semantic_veto_product_scope_llm_allocation_pilot_plan_en_es import (  # noqa: E402
    SLOT_TYPE_ORDER,
    _family_metadata,
    _planned_generation_slots,
)
from semantic_veto_repaired_full_band_formula_sweep_core import _weighted_score  # noqa: E402


DEFAULT_ACCEPTANCE_AUDIT_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_band_grading_acceptance_audit_en_es_latest.json"
)
DEFAULT_BAND_FORMULA_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_formula_sweep_en_es_latest.json"
)
DEFAULT_DATASET_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_repaired_full_dataset_en_es_latest.json"
)
DEFAULT_PREVIOUS_PLAN_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json"
)
DEFAULT_PREVIOUS_ADMISSION_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_llm_allocation_generation_admission_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es_latest.md"
)
DEFAULT_MANIFEST_OUT = (
    TEST_INPUTS_ROOT / "semantic_veto_product_scope_band_grading_v1_allocation_plan_en_es.json"
)
DEFAULT_PILOT_ID = "semantic_veto_product_scope_band_grading_v1_allocation_en_es"
DEFAULT_SELECTION_SEED = "product-scope-band-grading-v1-follow-through"
DEFAULT_HIGH_SIZE = 6
DEFAULT_MIDDLE_SIZE = 6
DEFAULT_LOW_SIZE = 6
BAND_IDS = ("high_need", "middle_need", "low_need")
ARM_BY_BAND = {
    "high_need": "high_need",
    "middle_need": "middle_control",
    "low_need": "low_control",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a no-spend LLM allocation plan from accepted "
            "product_scope_band_grading_v1. Runtime policy and LLM spend remain unchanged."
        )
    )
    parser.add_argument("--acceptance-audit-json", type=Path, default=DEFAULT_ACCEPTANCE_AUDIT_JSON)
    parser.add_argument("--band-formula-json", type=Path, default=DEFAULT_BAND_FORMULA_JSON)
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--previous-plan-json", type=Path, default=DEFAULT_PREVIOUS_PLAN_JSON)
    parser.add_argument(
        "--previous-admission-json", type=Path, default=DEFAULT_PREVIOUS_ADMISSION_JSON
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT)
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--selection-seed", default=DEFAULT_SELECTION_SEED)
    parser.add_argument("--high-size", type=int, default=DEFAULT_HIGH_SIZE)
    parser.add_argument("--middle-size", type=int, default=DEFAULT_MIDDLE_SIZE)
    parser.add_argument("--low-size", type=int, default=DEFAULT_LOW_SIZE)
    parser.add_argument("--allow-previous-overlap", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    previous_plan = _load_json(args.previous_plan_json) if args.previous_plan_json.exists() else {}
    previous_admission = (
        _load_json(args.previous_admission_json) if args.previous_admission_json.exists() else {}
    )
    report = build_band_grading_v1_allocation_plan_report(
        acceptance_audit_payload=_load_json(args.acceptance_audit_json),
        band_formula_payload=_load_json(args.band_formula_json),
        dataset_payload=_load_json(args.dataset_json),
        previous_plan_payload=previous_plan,
        previous_admission_payload=previous_admission,
        acceptance_audit_path=args.acceptance_audit_json,
        band_formula_path=args.band_formula_json,
        dataset_path=args.dataset_json,
        previous_plan_path=args.previous_plan_json if args.previous_plan_json.exists() else None,
        previous_admission_path=args.previous_admission_json
        if args.previous_admission_json.exists()
        else None,
        pilot_id=str(args.pilot_id),
        selection_seed=str(args.selection_seed),
        high_size=int(args.high_size),
        middle_size=int(args.middle_size),
        low_size=int(args.low_size),
        allow_previous_overlap=bool(args.allow_previous_overlap),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_band_grading_v1_allocation_plan_markdown(report))
    args.manifest_out.write_text(
        json.dumps(report["pilot_manifest"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    print(f"Wrote pilot manifest to {args.manifest_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_band_grading_v1_allocation_plan_report(
    *,
    acceptance_audit_payload: Mapping[str, object],
    band_formula_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    previous_plan_payload: Mapping[str, object] | None = None,
    previous_admission_payload: Mapping[str, object] | None = None,
    acceptance_audit_path: Path | None = None,
    band_formula_path: Path | None = None,
    dataset_path: Path | None = None,
    previous_plan_path: Path | None = None,
    previous_admission_path: Path | None = None,
    pilot_id: str = DEFAULT_PILOT_ID,
    selection_seed: str = DEFAULT_SELECTION_SEED,
    high_size: int = DEFAULT_HIGH_SIZE,
    middle_size: int = DEFAULT_MIDDLE_SIZE,
    low_size: int = DEFAULT_LOW_SIZE,
    allow_previous_overlap: bool = False,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    candidate = _candidate(acceptance_audit_payload)
    previous = _previous_coverage(previous_plan_payload or {}, previous_admission_payload or {})
    family_metadata = _family_metadata(dataset_payload)
    band_rows = _band_family_rows(
        band_formula_payload=band_formula_payload,
        family_metadata=family_metadata,
        candidate=candidate,
        previous=previous,
    )
    selected_families = _select_follow_through_families(
        band_rows=band_rows,
        requested_sizes={
            "high_need": high_size,
            "middle_need": middle_size,
            "low_need": low_size,
        },
        selection_seed=selection_seed,
        allow_previous_overlap=allow_previous_overlap,
    )
    pilot_manifest = _pilot_manifest(
        selected_families=selected_families,
        pilot_id=pilot_id,
        generated_at=generated_at,
        candidate=candidate,
        selection_seed=selection_seed,
        allow_previous_overlap=allow_previous_overlap,
        acceptance_audit_path=acceptance_audit_path,
        band_formula_path=band_formula_path,
        dataset_path=dataset_path,
        previous_plan_path=previous_plan_path,
    )
    issues = _issues(
        acceptance_audit_payload=acceptance_audit_payload,
        dataset_payload=dataset_payload,
        candidate=candidate,
        band_rows=band_rows,
        selected_families=selected_families,
        requested_sizes={
            "high_need": high_size,
            "middle_need": middle_size,
            "low_need": low_size,
        },
        allow_previous_overlap=allow_previous_overlap,
    )
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or band_formula_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "product_scope_band_grading_v1_allocation_plan_established"
            if status == "ok"
            else "product_scope_band_grading_v1_allocation_plan_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "acceptance_audit_path": _repo_path(acceptance_audit_path),
            "acceptance_audit_decision": str(acceptance_audit_payload.get("decision") or ""),
            "band_formula_path": _repo_path(band_formula_path),
            "band_formula_decision": str(band_formula_payload.get("decision") or ""),
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "dataset_manual_review_state": str(dataset_payload.get("manual_review_state") or ""),
            "previous_plan_path": _repo_path(previous_plan_path),
            "previous_admission_path": _repo_path(previous_admission_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_spend": "none",
            "candidate_id": "product_scope_band_grading_v1",
            "goal": (
                "Freeze the smallest useful new-family follow-through batch for the "
                "accepted v1 band heuristic, while preserving high/middle/low controls."
            ),
            "selection_basis": (
                "Families are banded by the accepted formula and sampled deterministically "
                "within each band. Previous paid-pilot families are excluded by default "
                "so the next spend increases coverage instead of duplicating rows."
            ),
            "selection_seed": selection_seed,
            "allow_previous_overlap": allow_previous_overlap,
            "requested_arm_sizes": {
                "high_need": high_size,
                "middle_control": middle_size,
                "low_control": low_size,
            },
            "candidate": candidate,
            "selection_uses_observed_outcomes": False,
        },
        "summary": {
            "issues": issues,
            "candidate_family_count": len(band_rows),
            "band_counts": _band_counts(band_rows),
            "previous_overlap_by_band": _previous_overlap_by_band(band_rows),
            "selected_family_count": len(selected_families),
            "selected_arm_counts": dict(Counter(row["pilot_arm"] for row in selected_families)),
            "selected_previous_overlap_count": sum(
                1 for row in selected_families if row.get("previous_pilot_overlap")
            ),
            "planned_generation_slot_count": sum(
                len(_mapping_rows(row.get("planned_generation_slots"))) for row in selected_families
            ),
            "expected_generated_item_count": sum(
                sum(
                    int(slot.get("requested_items") or 0)
                    for slot in _mapping_rows(row.get("planned_generation_slots"))
                )
                for row in selected_families
            ),
            "historical_observed_failure_by_arm": _observed_failure_by_arm(selected_families),
        },
        "e2e_checks": {
            "acceptance_audit_ok": str(acceptance_audit_payload.get("status") or "") == "ok",
            "acceptance_decision_is_carry_forward": str(
                acceptance_audit_payload.get("decision") or ""
            )
            == "accept_band_grading_v1_for_next_research_stage",
            "dataset_is_user_approved": str(dataset_payload.get("manual_review_state") or "")
            == "approved_by_user",
            "band_rows_available": bool(band_rows),
            "band_rows_unique": len({row["family_id"] for row in band_rows}) == len(band_rows),
            "selected_families_unique": len({row["family_id"] for row in selected_families})
            == len(selected_families),
            "no_previous_overlap_selected": not any(
                row.get("previous_pilot_overlap") for row in selected_families
            ),
            "no_outcome_fields_used_for_selection": True,
            "all_requested_arm_sizes_available": _arm_counts_match(
                selected_families,
                {
                    "high_need": high_size,
                    "middle_control": middle_size,
                    "low_control": low_size,
                },
            ),
            "generation_contract_compatible_with_existing_request_renderer": tuple(
                _as_mapping(pilot_manifest.get("generation_contract")).get("slot_types") or ()
            )
            == SLOT_TYPE_ORDER,
            "manifest_generated": bool(pilot_manifest.get("pilot_families")),
        },
        "band_family_rows": band_rows,
        "selected_families": selected_families,
        "pilot_manifest": pilot_manifest,
        "limitations": [
            "this_is_a_no_spend_plan_not_generated_data",
            "selection_is_for_sentence_transformer_product_lane_not_backend_agnostic",
            "historical_failure_fields_are_diagnostic_only_and_not_used_for_selection",
            "the_plan_expands_beyond_previous_pilot_families_but_still_uses_the_49_family_denominator",
        ],
        "next_steps": [
            "Render the generation request packet from this manifest.",
            "Inspect selected families and prompt packet before any paid generation.",
            "Generate the same slot contract for all arms if approved.",
            "Admit outputs and compare improvement by arm before broad language-wide spending.",
        ],
    }


def render_band_grading_v1_allocation_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    methodology = _as_mapping(report.get("methodology"))
    lines = [
        "# en-es Semantic Veto Product-Scope Band-Grading v1 Allocation Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate families: `{summary.get('candidate_family_count', 0)}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Planned generation slots: `{summary.get('planned_generation_slot_count', 0)}`",
        f"- Expected generated items: `{summary.get('expected_generated_item_count', 0)}`",
        f"- Previous-overlap selected: `{summary.get('selected_previous_overlap_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(methodology.get("goal") or ""),
        "",
        str(methodology.get("selection_basis") or ""),
        "",
        "## Candidate",
        "",
        _candidate_table(_as_mapping(methodology.get("candidate"))),
        "",
        "## Band Availability",
        "",
        "| Band | Families | Previous pilot overlap | New families |",
        "| --- | ---: | ---: | ---: |",
    ]
    overlap = _as_mapping(summary.get("previous_overlap_by_band"))
    for band_id, row_obj in _as_mapping(summary.get("band_counts")).items():
        row = _as_mapping(row_obj)
        overlap_row = _as_mapping(overlap.get(band_id))
        lines.append(
            f"| `{_escape_md(str(band_id))}` | {row.get('family_count', 0)} | "
            f"{overlap_row.get('previous_pilot_overlap_count', 0)} | "
            f"{overlap_row.get('new_family_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Arm Summary",
            "",
            "| Arm | Families | Mean need | Historical failure | Harmful share | False abstains |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    failure_by_arm = _as_mapping(summary.get("historical_observed_failure_by_arm"))
    for arm in ("high_need", "middle_control", "low_control"):
        row = _as_mapping(failure_by_arm.get(arm))
        lines.append(
            f"| `{arm}` | {row.get('family_count', 0)} | "
            f"{_number(row.get('mean_predicted_need'))} | "
            f"{_format_percent(row.get('observed_failure_rate'))} | "
            f"{_format_percent(row.get('harmful_replace_rate'))} | "
            f"{int(row.get('false_abstain_count') or 0)} |"
        )
    lines.extend(
        [
            "",
            "## Selected Families",
            "",
            "| Arm | Rank | Trigger | Target | Need | Prev pilot | Slots | Historical fail |",
            "| --- | ---: | --- | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("selected_families")):
        lines.append(
            f"| `{_escape_md(str(row.get('pilot_arm') or ''))}` | "
            f"{int(row.get('arm_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('target_lemma') or ''))}` | "
            f"{_number(row.get('predicted_need'))} | "
            f"`{str(bool(row.get('previous_pilot_overlap'))).lower()}` | "
            f"{len(_mapping_rows(row.get('planned_generation_slots')))} | "
            f"{_format_percent(row.get('observed_failure_rate'))} |"
        )
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(str(key))}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _candidate(payload: Mapping[str, object]) -> dict[str, object]:
    candidate = dict(_as_mapping(_as_mapping(payload.get("summary")).get("candidate")))
    return {
        "candidate_id": "product_scope_band_grading_v1",
        "scorer_id": str(candidate.get("scorer_id") or ""),
        "formula_id": str(candidate.get("formula_id") or ""),
        "formula_family": str(candidate.get("formula_family") or ""),
        "weights": {
            str(key): _safe_float(value)
            for key, value in _as_mapping(candidate.get("weights")).items()
        },
        "primary_grade_score": candidate.get("primary_grade_score"),
        "primary_normalized_high_low_failure_delta": candidate.get(
            "primary_normalized_high_low_failure_delta"
        ),
        "primary_normalized_order_score": candidate.get("primary_normalized_order_score"),
        "raw_high_low_failure_delta": candidate.get("raw_high_low_failure_delta"),
    }


def _band_family_rows(
    *,
    band_formula_payload: Mapping[str, object],
    family_metadata: Mapping[str, Mapping[str, object]],
    candidate: Mapping[str, object],
    previous: Mapping[str, set[str]],
) -> list[dict[str, object]]:
    scorer_id = str(candidate.get("scorer_id") or "")
    weights = _as_mapping(candidate.get("weights"))
    scored = []
    observations_by_family = {}
    for observation in _mapping_rows(band_formula_payload.get("observations")):
        if str(observation.get("scorer_id") or "") != scorer_id:
            continue
        family_id = str(observation.get("family_id") or "")
        metadata = _as_mapping(family_metadata.get(family_id))
        if not metadata:
            continue
        predicted_need = _weighted_score(_as_mapping(observation.get("features")), weights)
        scored.append({"family_id": family_id, "predicted_need": predicted_need})
        observations_by_family[family_id] = observation
    bands = _assign_bands(scored)
    rows = []
    previous_plan_ids = previous.get("previous_plan_family_ids", set())
    previous_admitted_ids = previous.get("previous_admitted_family_ids", set())
    for band_id in BAND_IDS:
        family_ids = bands.get(band_id, [])
        ranked = _stable_rank(family_ids, seed=f"band-row:{band_id}")
        for band_rank, family_id in enumerate(ranked, start=1):
            observation = _as_mapping(observations_by_family.get(family_id))
            metadata = _as_mapping(family_metadata.get(family_id))
            rows.append(
                {
                    "family_id": family_id,
                    "trigger": str(metadata.get("trigger") or observation.get("trigger") or ""),
                    "target_lemma": str(
                        metadata.get("target_lemma") or observation.get("target_lemma") or ""
                    ),
                    "band_id": band_id,
                    "pilot_arm": ARM_BY_BAND[band_id],
                    "band_rank": band_rank,
                    "predicted_need": round(
                        _weighted_score(_as_mapping(observation.get("features")), weights), 4
                    ),
                    "selection_scorer": scorer_id,
                    "selection_formula": str(candidate.get("formula_id") or ""),
                    "selection_features": {
                        key: round(_safe_float(value), 4)
                        for key, value in sorted(_as_mapping(observation.get("features")).items())
                    },
                    "feature_context": dict(_as_mapping(observation.get("feature_context"))),
                    "previous_pilot_overlap": family_id in previous_plan_ids,
                    "previous_admitted_overlap": family_id in previous_admitted_ids,
                    "observed_failure_rate": observation.get("observed_failure_rate"),
                    "failure_count": int(observation.get("failure_count") or 0),
                    "case_count": int(observation.get("case_count") or 0),
                    "harmful_replace_count": int(observation.get("harmful_replace_count") or 0),
                    "false_abstain_count": int(observation.get("false_abstain_count") or 0),
                    "active": metadata.get("active"),
                    "shadows": metadata.get("shadows"),
                    "shadow_count": len(_mapping_rows(metadata.get("shadows"))),
                }
            )
    return sorted(rows, key=lambda row: (BAND_IDS.index(row["band_id"]), row["band_rank"]))


def _select_follow_through_families(
    *,
    band_rows: Sequence[Mapping[str, object]],
    requested_sizes: Mapping[str, int],
    selection_seed: str,
    allow_previous_overlap: bool,
) -> list[dict[str, object]]:
    selected = []
    for band_id in BAND_IDS:
        rows = [row for row in band_rows if row.get("band_id") == band_id]
        if not allow_previous_overlap:
            rows = [row for row in rows if not row.get("previous_pilot_overlap")]
        rows = _stable_sample(
            rows, size=int(requested_sizes.get(band_id) or 0), seed=selection_seed
        )
        rows = sorted(rows, key=lambda row: int(row.get("band_rank") or 0))
        for arm_rank, row in enumerate(rows, start=1):
            copied = dict(row)
            copied["arm_rank"] = arm_rank
            copied["global_need_rank"] = _global_need_rank(row, band_rows)
            copied["planned_generation_slots"] = _planned_generation_slots(copied)
            selected.append(copied)
    return selected


def _pilot_manifest(
    *,
    selected_families: Sequence[Mapping[str, object]],
    pilot_id: str,
    generated_at: str,
    candidate: Mapping[str, object],
    selection_seed: str,
    allow_previous_overlap: bool,
    acceptance_audit_path: Path | None,
    band_formula_path: Path | None,
    dataset_path: Path | None,
    previous_plan_path: Path | None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pilot_id": pilot_id,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "no_spend_manifest_only",
        "selection": {
            "candidate_id": str(candidate.get("candidate_id") or ""),
            "selection_scorer": str(candidate.get("scorer_id") or ""),
            "selection_formula": str(candidate.get("formula_id") or ""),
            "selection_formula_weights": dict(_as_mapping(candidate.get("weights"))),
            "selection_seed": selection_seed,
            "allow_previous_overlap": allow_previous_overlap,
            "acceptance_audit_path": _repo_path(acceptance_audit_path),
            "band_formula_path": _repo_path(band_formula_path),
            "dataset_path": _repo_path(dataset_path),
            "previous_plan_path": _repo_path(previous_plan_path),
            "selection_uses_observed_outcomes": False,
        },
        "generation_contract": {
            "same_contract_for_all_arms": True,
            "slot_types": list(SLOT_TYPE_ORDER),
            "evaluation_rule": (
                "Apply generated evidence to every arm under the same selected candidate "
                "policies, then compare improvement for high_need versus middle_control "
                "and low_control. Do not tune thresholds from the generated rows."
            ),
        },
        "pilot_families": list(selected_families),
    }


def _previous_coverage(
    previous_plan_payload: Mapping[str, object],
    previous_admission_payload: Mapping[str, object],
) -> dict[str, set[str]]:
    return {
        "previous_plan_family_ids": {
            str(row.get("family_id") or "")
            for row in _mapping_rows(previous_plan_payload.get("pilot_families"))
            if str(row.get("family_id") or "")
        },
        "previous_admitted_family_ids": {
            str(row.get("family_id") or "")
            for row in _mapping_rows(previous_admission_payload.get("admitted_items"))
            if str(row.get("family_id") or "")
        },
    }


def _issues(
    *,
    acceptance_audit_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    candidate: Mapping[str, object],
    band_rows: Sequence[Mapping[str, object]],
    selected_families: Sequence[Mapping[str, object]],
    requested_sizes: Mapping[str, int],
    allow_previous_overlap: bool,
) -> list[str]:
    issues = []
    if str(acceptance_audit_payload.get("status") or "") != "ok":
        issues.append("acceptance_audit_not_ok")
    if (
        str(acceptance_audit_payload.get("decision") or "")
        != "accept_band_grading_v1_for_next_research_stage"
    ):
        issues.append("acceptance_decision_not_carry_forward")
    if str(dataset_payload.get("manual_review_state") or "") != "approved_by_user":
        issues.append("dataset_not_marked_approved_by_user")
    if not _as_mapping(candidate.get("weights")):
        issues.append("candidate_weights_missing")
    if len({row["family_id"] for row in band_rows}) != len(band_rows):
        issues.append("duplicate_band_family_rows")
    if len({row["family_id"] for row in selected_families}) != len(selected_families):
        issues.append("duplicate_selected_families")
    selected_counts = Counter(str(row.get("band_id") or "") for row in selected_families)
    for band_id, requested in requested_sizes.items():
        if selected_counts.get(band_id, 0) != int(requested):
            issues.append(
                f"{band_id}_selected_count_{selected_counts.get(band_id, 0)}_expected_{requested}"
            )
    if not allow_previous_overlap and any(
        row.get("previous_pilot_overlap") for row in selected_families
    ):
        issues.append("previous_pilot_overlap_selected")
    if any(
        tuple(
            str(slot.get("slot_type") or "")
            for slot in _mapping_rows(row.get("planned_generation_slots"))
        )
        != SLOT_TYPE_ORDER
        for row in selected_families
    ):
        issues.append("invalid_generation_slot_order")
    return issues


def _previous_overlap_by_band(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    output = {}
    for band_id in BAND_IDS:
        band_rows = [row for row in rows if row.get("band_id") == band_id]
        previous = sum(1 for row in band_rows if row.get("previous_pilot_overlap"))
        output[band_id] = {
            "family_count": len(band_rows),
            "previous_pilot_overlap_count": previous,
            "previous_admitted_overlap_count": sum(
                1 for row in band_rows if row.get("previous_admitted_overlap")
            ),
            "new_family_count": len(band_rows) - previous,
        }
    return output


def _band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    output = {}
    for band_id in BAND_IDS:
        band_rows = [row for row in rows if row.get("band_id") == band_id]
        output[band_id] = {
            "family_count": len(band_rows),
            "mean_predicted_need": _mean(band_rows, "predicted_need"),
            "min_predicted_need": min(
                (_safe_float(row.get("predicted_need")) for row in band_rows), default=0.0
            ),
            "max_predicted_need": max(
                (_safe_float(row.get("predicted_need")) for row in band_rows), default=0.0
            ),
        }
    return output


def _observed_failure_by_arm(
    selected_families: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    summary = {}
    for arm in ("high_need", "middle_control", "low_control"):
        rows = [row for row in selected_families if row.get("pilot_arm") == arm]
        cases = sum(int(row.get("case_count") or 0) for row in rows)
        failures = sum(int(row.get("failure_count") or 0) for row in rows)
        harmful = sum(int(row.get("harmful_replace_count") or 0) for row in rows)
        false_abstain = sum(int(row.get("false_abstain_count") or 0) for row in rows)
        summary[arm] = {
            "family_count": len(rows),
            "mean_predicted_need": _mean(rows, "predicted_need"),
            "case_count": cases,
            "failure_count": failures,
            "observed_failure_rate": failures / cases if cases else 0.0,
            "harmful_replace_count": harmful,
            "harmful_replace_rate": harmful / cases if cases else 0.0,
            "false_abstain_count": false_abstain,
        }
    return summary


def _stable_rank(family_ids: Sequence[str], *, seed: str) -> list[str]:
    return sorted(
        family_ids,
        key=lambda family_id: (
            hashlib.sha256(f"{seed}:{family_id}".encode("utf-8")).hexdigest(),
            family_id,
        ),
    )


def _stable_sample(
    rows: Sequence[Mapping[str, object]],
    *,
    size: int,
    seed: str,
) -> list[Mapping[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            hashlib.sha256(
                f"{seed}:{row.get('band_id')}:{row.get('family_id')}".encode("utf-8")
            ).hexdigest(),
            str(row.get("family_id") or ""),
        ),
    )
    return ranked[:size]


def _global_need_rank(row: Mapping[str, object], rows: Sequence[Mapping[str, object]]) -> int:
    ranked = sorted(
        rows,
        key=lambda item: (
            -_safe_float(item.get("predicted_need")),
            BAND_IDS.index(str(item.get("band_id") or "low_need")),
            str(item.get("family_id") or ""),
        ),
    )
    family_id = str(row.get("family_id") or "")
    for index, candidate in enumerate(ranked, start=1):
        if str(candidate.get("family_id") or "") == family_id:
            return index
    return 0


def _arm_counts_match(
    selected_families: Sequence[Mapping[str, object]],
    expected: Mapping[str, int],
) -> bool:
    counts = Counter(row["pilot_arm"] for row in selected_families)
    return all(counts.get(arm, 0) == int(size) for arm, size in expected.items())


def _candidate_table(candidate: Mapping[str, object]) -> str:
    weights = _as_mapping(candidate.get("weights"))
    return "\n".join(
        [
            f"- Scorer/config: `{_escape_md(str(candidate.get('scorer_id') or ''))}`",
            f"- Formula: `{_escape_md(str(candidate.get('formula_id') or ''))}`",
            f"- Primary grade: `{_number(candidate.get('primary_grade_score'))}`",
            f"- Base SRS high-low delta: `{_format_signed_percent(candidate.get('primary_normalized_high_low_failure_delta'))}`",
            "- Weights: `"
            + _escape_md(json.dumps(weights, sort_keys=True, separators=(",", ":")))
            + "`",
        ]
    )


def _mean(rows: Sequence[Mapping[str, object]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(_safe_float(row.get(key)) for row in rows) / len(rows), 4)


def _format_signed_percent(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{100 * _safe_float(value):+.1f}%"


def _number(value: object) -> str:
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
