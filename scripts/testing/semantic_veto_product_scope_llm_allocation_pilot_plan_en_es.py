#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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


DEFAULT_BAND_FORMULA_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_band_formula_sweep_en_es_latest.json"
)
DEFAULT_DATASET_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_repaired_full_dataset_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_llm_allocation_pilot_plan_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_product_scope_llm_allocation_pilot_plan_en_es_latest.md"
)
DEFAULT_MANIFEST_OUT = (
    TEST_INPUTS_ROOT / "semantic_veto_product_scope_llm_allocation_pilot_plan_en_es.json"
)
DEFAULT_PILOT_ID = "semantic_veto_product_scope_llm_allocation_pilot_en_es_v1"
DEFAULT_SELECTION_SCORER = "best_product_rank_sentence_transformer_a0000_mneg0025"
DEFAULT_SELECTION_FORMULA = "shadow_coverage_only"
DEFAULT_SELECTION_SEED = "product-scope-shadow-coverage-v1"
DEFAULT_HIGH_SIZE = 8
DEFAULT_MIDDLE_SIZE = 4
DEFAULT_LOW_SIZE = 8
SLOT_TYPE_ORDER = (
    "active_evidence_expansion",
    "shadow_or_competitor_evidence_probe",
    "no_winner_context_probe",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a no-spend LLM-allocation pilot from the corrected product-scope "
            "band/formula sweep. Runtime policy and LLM spend remain unchanged."
        )
    )
    parser.add_argument("--band-formula-json", type=Path, default=DEFAULT_BAND_FORMULA_JSON)
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT)
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--selection-scorer", default=DEFAULT_SELECTION_SCORER)
    parser.add_argument("--selection-formula", default=DEFAULT_SELECTION_FORMULA)
    parser.add_argument("--selection-seed", default=DEFAULT_SELECTION_SEED)
    parser.add_argument("--high-size", type=int, default=DEFAULT_HIGH_SIZE)
    parser.add_argument("--middle-size", type=int, default=DEFAULT_MIDDLE_SIZE)
    parser.add_argument("--low-size", type=int, default=DEFAULT_LOW_SIZE)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_product_scope_llm_allocation_pilot_plan_report(
        band_formula_payload=_load_json(args.band_formula_json),
        dataset_payload=_load_json(args.dataset_json),
        band_formula_path=args.band_formula_json,
        dataset_path=args.dataset_json,
        pilot_id=str(args.pilot_id),
        selection_scorer=str(args.selection_scorer),
        selection_formula=str(args.selection_formula),
        selection_seed=str(args.selection_seed),
        high_size=int(args.high_size),
        middle_size=int(args.middle_size),
        low_size=int(args.low_size),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_product_scope_llm_allocation_pilot_plan_markdown(report), encoding="utf-8"
    )
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


def build_product_scope_llm_allocation_pilot_plan_report(
    *,
    band_formula_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    band_formula_path: Path | None = None,
    dataset_path: Path | None = None,
    pilot_id: str = DEFAULT_PILOT_ID,
    selection_scorer: str = DEFAULT_SELECTION_SCORER,
    selection_formula: str = DEFAULT_SELECTION_FORMULA,
    selection_seed: str = DEFAULT_SELECTION_SEED,
    high_size: int = DEFAULT_HIGH_SIZE,
    middle_size: int = DEFAULT_MIDDLE_SIZE,
    low_size: int = DEFAULT_LOW_SIZE,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    family_metadata = _family_metadata(dataset_payload)
    observations = _selection_observations(
        band_formula_payload=band_formula_payload,
        family_metadata=family_metadata,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
    )
    selected_families = _select_band_arms(
        observations,
        high_size=high_size,
        middle_size=middle_size,
        low_size=low_size,
        selection_seed=selection_seed,
    )
    pilot_manifest = _pilot_manifest(
        selected_families=selected_families,
        pilot_id=pilot_id,
        generated_at=generated_at,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
        selection_seed=selection_seed,
        band_formula_path=band_formula_path,
        dataset_path=dataset_path,
    )
    issues = _issues(
        observations=observations,
        selected_families=selected_families,
        dataset_payload=dataset_payload,
        high_size=high_size,
        middle_size=middle_size,
        low_size=low_size,
    )
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or band_formula_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "product_scope_llm_allocation_pilot_plan_established"
            if status == "ok"
            else "product_scope_llm_allocation_pilot_plan_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "band_formula_path": _repo_path(band_formula_path),
            "band_formula_decision": str(band_formula_payload.get("decision") or ""),
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "dataset_manual_review_state": str(dataset_payload.get("manual_review_state") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_spend": "none",
            "goal": (
                "Choose a smallest meaningful high/middle/low family batch to test whether "
                "the corrected shadow-coverage band actually predicts where generated "
                "semantic evidence improves veto quality."
            ),
            "selection_basis": (
                "Families are assigned to bands by the selected formula's predicted need. "
                "Within tied bands, selection uses a deterministic seed hash over family_id. "
                "Observed failures are attached after selection for diagnosis only."
            ),
            "selection_scorer": selection_scorer,
            "selection_formula": selection_formula,
            "selection_seed": selection_seed,
            "requested_arm_sizes": {
                "high_need": int(high_size),
                "middle_control": int(middle_size),
                "low_control": int(low_size),
            },
            "pilot_arms": {
                "high_need": "highest shadow-coverage need band",
                "middle_control": "middle shadow-coverage need band",
                "low_control": "lowest shadow-coverage need band",
            },
            "promotion_boundary": (
                "The heuristic is useful only if generated evidence improves high_need "
                "families more than middle and low controls under the same carried-forward "
                "candidate policies."
            ),
        },
        "summary": {
            "issues": issues,
            "candidate_family_count": len(observations),
            "selected_family_count": len(selected_families),
            "arm_counts": dict(Counter(row["pilot_arm"] for row in selected_families)),
            "band_counts": _band_counts(observations),
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
            "dataset_is_user_approved": str(dataset_payload.get("manual_review_state") or "")
            == "approved_by_user",
            "selection_rows_available": bool(observations),
            "selection_formula_is_shadow_coverage_only": selection_formula
            == "shadow_coverage_only",
            "no_outcome_fields_used_for_selection": True,
            "selected_families_unique": len({row["family_id"] for row in selected_families})
            == len(selected_families),
            "all_requested_arm_sizes_available": _arm_counts_match(
                selected_families,
                {
                    "high_need": high_size,
                    "middle_control": middle_size,
                    "low_control": low_size,
                },
            ),
            "planned_slot_count_equal_per_family": {
                len(_mapping_rows(row.get("planned_generation_slots"))) for row in selected_families
            }
            == {len(SLOT_TYPE_ORDER)},
            "generation_contract_compatible_with_existing_request_renderer": tuple(
                _as_mapping(pilot_manifest.get("generation_contract")).get("slot_types") or ()
            )
            == SLOT_TYPE_ORDER,
            "manifest_generated": bool(pilot_manifest.get("pilot_families")),
        },
        "selected_families": selected_families,
        "pilot_manifest": pilot_manifest,
        "limitations": [
            "pilot_families_are_from_the_current_49_family_product_scope_denominator",
            "shadow_coverage_is_a_current_best_cheap_signal_not_a_final_language_wide_policy",
            "historical_observed_failure_annotations_are_diagnostic_only",
            "the_middle_band_has_only_four_available_families_in_this_denominator",
            "llm_generation_and_downstream_rescoring_are_not_done_by_this_harness",
        ],
        "next_steps": [
            "Render the generation request packet from this manifest before spending.",
            "Run identical generation slots for high, middle, and low arms.",
            "Admit generated outputs, then rescore the same five carried-forward candidate policies.",
            "Prioritize full production generation by band only if high_need improves more than controls.",
        ],
    }


def render_product_scope_llm_allocation_pilot_plan_markdown(
    report: Mapping[str, object],
) -> str:
    summary = _as_mapping(report.get("summary"))
    methodology = _as_mapping(report.get("methodology"))
    lines = [
        "# en-es Semantic Veto Product-Scope LLM Allocation Pilot Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate families: `{summary.get('candidate_family_count', 0)}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Planned generation slots: `{summary.get('planned_generation_slot_count', 0)}`",
        f"- Expected generated items: `{summary.get('expected_generated_item_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(methodology.get("goal") or ""),
        "",
        str(methodology.get("selection_basis") or ""),
        "",
        "## Band Availability",
        "",
        "| Band | Predicted need | Available families |",
        "| --- | ---: | ---: |",
    ]
    for band, row in _as_mapping(summary.get("band_counts")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(band))}` | {_number(row_map.get('predicted_need'))} | "
            f"{row_map.get('family_count', 0)} |"
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
    arm_counts = _as_mapping(summary.get("arm_counts"))
    for arm in ("high_need", "middle_control", "low_control"):
        row = _as_mapping(failure_by_arm.get(arm))
        lines.append(
            f"| `{arm}` | {arm_counts.get(arm, 0)} | "
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
            "| Arm | Rank | Trigger | Target | Need | Shadow count | Slots | Historical fail |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("selected_families")):
        lines.append(
            f"| `{_escape_md(str(row.get('pilot_arm') or ''))}` | "
            f"{int(row.get('arm_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('target_lemma') or ''))}` | "
            f"{_number(row.get('predicted_need'))} | "
            f"{int(row.get('shadow_count') or 0)} | "
            f"{len(_mapping_rows(row.get('planned_generation_slots')))} | "
            f"{_format_percent(row.get('observed_failure_rate'))} |"
        )
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _selection_observations(
    *,
    band_formula_payload: Mapping[str, object],
    family_metadata: Mapping[str, Mapping[str, object]],
    selection_scorer: str,
    selection_formula: str,
) -> list[dict[str, object]]:
    formula_weights = _selected_formula_weights(
        band_formula_payload=band_formula_payload,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
    )
    observed_by_family: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for observation in _mapping_rows(band_formula_payload.get("observations")):
        observed_by_family[str(observation.get("family_id") or "")].append(observation)

    rows = []
    for observation in _mapping_rows(band_formula_payload.get("observations")):
        if str(observation.get("scorer_id") or "") != selection_scorer:
            continue
        family_id = str(observation.get("family_id") or "")
        metadata = _as_mapping(family_metadata.get(family_id))
        if not metadata:
            continue
        features = _as_mapping(observation.get("features"))
        predicted_need = _weighted_need(features=features, weights=formula_weights)
        shadow_count = int(_as_mapping(observation.get("feature_context")).get("shadow_count") or 0)
        observed_summary = _family_observed_summary(observed_by_family[family_id])
        rows.append(
            {
                "family_id": family_id,
                "trigger": str(metadata.get("trigger") or observation.get("trigger") or ""),
                "target_lemma": str(
                    metadata.get("target_lemma") or observation.get("target_lemma") or ""
                ),
                "predicted_need": round(predicted_need, 4),
                "selection_scorer": selection_scorer,
                "selection_formula": selection_formula,
                "shadow_count": shadow_count,
                "selection_features": {
                    key: round(_safe_float(features.get(key)), 4) for key in sorted(features)
                },
                "feature_context": dict(_as_mapping(observation.get("feature_context"))),
                "observed_failure_rate": observed_summary["observed_failure_rate"],
                "failure_count": observed_summary["failure_count"],
                "case_count": observed_summary["case_count"],
                "harmful_replace_count": observed_summary["harmful_replace_count"],
                "false_abstain_count": observed_summary["false_abstain_count"],
                "active": metadata.get("active"),
                "shadows": metadata.get("shadows"),
            }
        )
    return sorted(rows, key=lambda row: (-_safe_float(row.get("predicted_need")), row["family_id"]))


def _selected_formula_weights(
    *,
    band_formula_payload: Mapping[str, object],
    selection_scorer: str,
    selection_formula: str,
) -> dict[str, float]:
    for row in _mapping_rows(band_formula_payload.get("comparison_rows")):
        if row.get("scorer_id") == selection_scorer and row.get("formula_id") == selection_formula:
            return {
                str(key): _safe_float(value)
                for key, value in _as_mapping(row.get("weights")).items()
            }
    if selection_formula == "shadow_coverage_only":
        return {"shadow_coverage_risk": 1.0}
    raise ValueError(
        f"Could not find formula {selection_formula!r} for scorer {selection_scorer!r}"
    )


def _weighted_need(*, features: Mapping[str, object], weights: Mapping[str, float]) -> float:
    score = 0.0
    for feature, weight in weights.items():
        score += float(weight) * _safe_float(features.get(feature))
    return max(0.0, min(1.0, score))


def _select_band_arms(
    rows: Sequence[Mapping[str, object]],
    *,
    high_size: int,
    middle_size: int,
    low_size: int,
    selection_seed: str,
) -> list[dict[str, object]]:
    grouped: dict[float, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[round(_safe_float(row.get("predicted_need")), 4)].append(row)
    needs = sorted(grouped, reverse=True)
    if not needs:
        return []
    high_need = needs[0]
    low_need = needs[-1]
    middle_need = min(needs, key=lambda need: (abs(need - 0.5), -need))
    arms = [
        ("high_need", high_need, high_size),
        ("middle_control", middle_need, middle_size),
        ("low_control", low_need, low_size),
    ]
    selected = []
    global_rank_by_family = _global_ranks(rows)
    for arm, need, size in arms:
        sampled = _stable_sample(grouped[need], size=size, seed=f"{selection_seed}:{arm}:{need}")
        sampled = sorted(sampled, key=lambda row: global_rank_by_family[str(row["family_id"])])
        for arm_rank, row in enumerate(sampled, start=1):
            copied = dict(row)
            copied["pilot_arm"] = arm
            copied["arm_rank"] = arm_rank
            copied["global_need_rank"] = global_rank_by_family[str(row["family_id"])]
            copied["band_predicted_need"] = need
            copied["planned_generation_slots"] = _planned_generation_slots(copied)
            selected.append(copied)
    return selected


def _stable_sample(
    rows: Sequence[Mapping[str, object]],
    *,
    size: int,
    seed: str,
) -> list[Mapping[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            hashlib.sha256(f"{seed}:{row.get('family_id')}".encode("utf-8")).hexdigest(),
            str(row.get("family_id") or ""),
        ),
    )
    return ranked[:size]


def _global_ranks(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -_safe_float(row.get("predicted_need")),
            int(row.get("shadow_count") or 0) * -1,
            str(row.get("family_id") or ""),
        ),
    )
    return {str(row.get("family_id") or ""): index for index, row in enumerate(ranked, start=1)}


def _family_metadata(dataset_payload: Mapping[str, object]) -> dict[str, dict[str, object]]:
    metadata = {}
    for family in _mapping_rows(dataset_payload.get("families")):
        family_id = str(family.get("family_id") or "")
        active = _as_mapping(family.get("active"))
        shadows = _mapping_rows(family.get("shadows"))
        metadata[family_id] = {
            "family_id": family_id,
            "trigger": str(family.get("trigger") or ""),
            "target_lemma": str(active.get("target_lemma") or ""),
            "active": {
                "sense_id": str(active.get("sense_id") or ""),
                "target_lemma": str(active.get("target_lemma") or ""),
                "canonical_pos": str(active.get("canonical_pos") or ""),
                "evidence_text": _evidence_text(active),
            },
            "shadows": [
                {
                    "sense_id": str(shadow.get("sense_id") or ""),
                    "target_lemma": str(shadow.get("target_lemma") or ""),
                    "canonical_pos": str(shadow.get("canonical_pos") or ""),
                    "evidence_text": _evidence_text(shadow),
                }
                for shadow in shadows
            ],
        }
    return metadata


def _family_observed_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    failure = sum(int(row.get("failure_count") or 0) for row in rows)
    cases = sum(int(row.get("case_count") or 0) for row in rows)
    harmful = sum(int(row.get("harmful_replace_count") or 0) for row in rows)
    false_abstain = sum(int(row.get("false_abstain_count") or 0) for row in rows)
    return {
        "failure_count": failure,
        "case_count": cases,
        "observed_failure_rate": failure / cases if cases else 0.0,
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
    }


def _planned_generation_slots(row: Mapping[str, object]) -> list[dict[str, object]]:
    family_id = str(row.get("family_id") or "")
    trigger = str(row.get("trigger") or "")
    target = str(row.get("target_lemma") or "")
    shadows = _mapping_rows(row.get("shadows"))
    primary_shadow = _as_mapping(shadows[0] if shadows else {})
    return [
        {
            "slot_id": f"{family_id}:active_evidence_expansion",
            "slot_type": "active_evidence_expansion",
            "source_phrase": trigger,
            "target_lemma": target,
            "requested_items": 2,
            "purpose": "Improve active-sense examples without changing decision thresholds.",
        },
        {
            "slot_id": f"{family_id}:shadow_or_competitor_evidence_probe",
            "slot_type": "shadow_or_competitor_evidence_probe",
            "source_phrase": trigger,
            "target_lemma": str(primary_shadow.get("target_lemma") or ""),
            "requested_items": 2,
            "purpose": (
                "Improve an existing competitor sense when present; otherwise discover "
                "one plausible competing sense before evidence generation."
            ),
        },
        {
            "slot_id": f"{family_id}:no_winner_context_probe",
            "slot_type": "no_winner_context_probe",
            "source_phrase": trigger,
            "target_lemma": "",
            "requested_items": 1,
            "purpose": (
                "Collect a runtime-like context where no offered Spanish target should win, "
                "for guard calibration."
            ),
        },
    ]


def _pilot_manifest(
    *,
    selected_families: Sequence[Mapping[str, object]],
    pilot_id: str,
    generated_at: str,
    selection_scorer: str,
    selection_formula: str,
    selection_seed: str,
    band_formula_path: Path | None,
    dataset_path: Path | None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pilot_id": pilot_id,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "no_spend_manifest_only",
        "selection": {
            "selection_scorer": selection_scorer,
            "selection_formula": selection_formula,
            "selection_seed": selection_seed,
            "band_formula_path": _repo_path(band_formula_path),
            "dataset_path": _repo_path(dataset_path),
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


def _issues(
    *,
    observations: Sequence[Mapping[str, object]],
    selected_families: Sequence[Mapping[str, object]],
    dataset_payload: Mapping[str, object],
    high_size: int,
    middle_size: int,
    low_size: int,
) -> list[str]:
    issues = []
    if str(dataset_payload.get("manual_review_state") or "") != "approved_by_user":
        issues.append("dataset_not_marked_approved_by_user")
    if not observations:
        issues.append("no_selection_observations")
    expected = {
        "high_need": int(high_size),
        "middle_control": int(middle_size),
        "low_control": int(low_size),
    }
    counts = Counter(row["pilot_arm"] for row in selected_families)
    for arm, size in expected.items():
        if counts.get(arm, 0) != size:
            issues.append(f"{arm}_selected_count_{counts.get(arm, 0)}_expected_{size}")
    if len({row["family_id"] for row in selected_families}) != len(selected_families):
        issues.append("duplicate_selected_families")
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


def _arm_counts_match(
    selected_families: Sequence[Mapping[str, object]],
    expected: Mapping[str, int],
) -> bool:
    counts = Counter(row["pilot_arm"] for row in selected_families)
    return all(counts.get(arm, 0) == int(size) for arm, size in expected.items())


def _band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[float, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[round(_safe_float(row.get("predicted_need")), 4)].append(row)
    needs = sorted(grouped, reverse=True)
    if not needs:
        return {}
    middle_need = min(needs, key=lambda need: (abs(need - 0.5), -need))
    labels = {
        needs[0]: "high_need",
        middle_need: "middle_control",
        needs[-1]: "low_control",
    }
    return {
        labels[need]: {
            "predicted_need": need,
            "family_count": len(grouped[need]),
        }
        for need in needs
        if need in labels
    }


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
        predicted_need = (
            sum(_safe_float(row.get("predicted_need")) for row in rows) / len(rows) if rows else 0.0
        )
        summary[arm] = {
            "family_count": len(rows),
            "mean_predicted_need": round(predicted_need, 4),
            "case_count": cases,
            "failure_count": failures,
            "observed_failure_rate": failures / cases if cases else 0.0,
            "harmful_replace_count": harmful,
            "harmful_replace_rate": harmful / cases if cases else 0.0,
            "false_abstain_count": false_abstain,
        }
    return summary


def _evidence_text(sense: Mapping[str, object]) -> str:
    evidence = _as_mapping(sense.get("evidence_views"))
    for key in ("all_evidence_text", "sense_gloss_bundle", "gloss_text", "sense_label"):
        value = str(evidence.get(key) or "").strip()
        if value:
            return value
    return str(sense.get("target_lemma") or "")


def _number(value: object) -> str:
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
