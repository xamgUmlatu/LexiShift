#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
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


DEFAULT_HEURISTIC_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_translation_ambiguity_heuristic_en_es_latest.json"
)
DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_control_pilot_plan_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_control_pilot_plan_en_es_latest.md"
)
DEFAULT_MANIFEST_OUT = TEST_INPUTS_ROOT / "semantic_veto_evidence_gap_control_pilot_plan_en_es.json"
DEFAULT_PILOT_ID = "semantic_veto_evidence_gap_control_pilot_en_es_v1"
DEFAULT_SELECTION_SCORER = "tfidf_cosine"
DEFAULT_SELECTION_FORMULA = "evidence_gap_only"
DEFAULT_ARM_SIZE = 8


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a no-spend top/middle/low control pilot plan from the latest "
            "evidence-gap heuristic bakeoff. Runtime policy and LLM spend remain unchanged."
        )
    )
    parser.add_argument("--heuristic-json", type=Path, default=DEFAULT_HEURISTIC_JSON)
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT)
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--selection-scorer", default=DEFAULT_SELECTION_SCORER)
    parser.add_argument("--selection-formula", default=DEFAULT_SELECTION_FORMULA)
    parser.add_argument("--arm-size", type=int, default=DEFAULT_ARM_SIZE)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_evidence_gap_control_pilot_plan_report(
        heuristic_payload=_load_json(args.heuristic_json),
        dataset_payload=_load_json(args.dataset_json),
        heuristic_path=args.heuristic_json,
        dataset_path=args.dataset_json,
        pilot_id=str(args.pilot_id),
        selection_scorer=str(args.selection_scorer),
        selection_formula=str(args.selection_formula),
        arm_size=int(args.arm_size),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_evidence_gap_control_pilot_plan_markdown(report), encoding="utf-8"
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


def build_evidence_gap_control_pilot_plan_report(
    *,
    heuristic_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    heuristic_path: Path | None = None,
    dataset_path: Path | None = None,
    pilot_id: str = DEFAULT_PILOT_ID,
    selection_scorer: str = DEFAULT_SELECTION_SCORER,
    selection_formula: str = DEFAULT_SELECTION_FORMULA,
    arm_size: int = DEFAULT_ARM_SIZE,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    family_metadata = _family_metadata(dataset_payload)
    selection_rows = _selection_rows(
        heuristic_payload=heuristic_payload,
        family_metadata=family_metadata,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
    )
    selected_families = _select_control_arms(selection_rows, arm_size=arm_size)
    pilot_manifest = _pilot_manifest(
        selected_families=selected_families,
        pilot_id=pilot_id,
        generated_at=generated_at,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
        heuristic_path=heuristic_path,
        dataset_path=dataset_path,
    )
    issues = _issues(
        selection_rows=selection_rows,
        selected_families=selected_families,
        dataset_payload=dataset_payload,
        arm_size=arm_size,
    )
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or heuristic_payload.get("pair") or "en-es"),
        "status": status,
        "decision": (
            "evidence_gap_control_pilot_plan_established"
            if status == "ok"
            else "evidence_gap_control_pilot_plan_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": {
            "heuristic_path": _repo_path(heuristic_path),
            "heuristic_decision": str(heuristic_payload.get("decision") or ""),
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "dataset_manual_review_state": str(dataset_payload.get("manual_review_state") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_spend": "none",
            "goal": (
                "Freeze a top/middle/low control pilot that can falsify whether "
                "evidence-gap ranking predicts benefit from better generated evidence."
            ),
            "selection_basis": (
                "Families are selected by predicted_need from the chosen pre-outcome "
                "heuristic only. Historical observed failures are attached after "
                "selection for diagnosis, not used for selecting pilot rows."
            ),
            "selection_scorer": selection_scorer,
            "selection_formula": selection_formula,
            "arm_size": int(arm_size),
            "pilot_arms": {
                "high_need": "highest predicted evidence-gap need",
                "middle_control": "families closest to the median predicted need",
                "low_control": "lowest predicted evidence-gap need",
            },
            "promotion_boundary": (
                "This manifest can drive later LLM or context generation. It cannot "
                "validate the heuristic until generated evidence is applied and top, "
                "middle, and low arms are compared."
            ),
        },
        "summary": {
            "issues": issues,
            "candidate_family_count": len(selection_rows),
            "selected_family_count": len(selected_families),
            "arm_counts": dict(Counter(row["pilot_arm"] for row in selected_families)),
            "planned_generation_slot_count": sum(
                len(_mapping_rows(row.get("planned_generation_slots"))) for row in selected_families
            ),
            "selection_need_range": _need_range(selected_families),
            "historical_observed_failure_by_arm": _observed_failure_by_arm(selected_families),
        },
        "e2e_checks": {
            "dataset_is_user_approved": str(dataset_payload.get("manual_review_state") or "")
            == "approved_by_user",
            "selection_rows_available": bool(selection_rows),
            "no_outcome_fields_used_for_selection": True,
            "all_arms_have_requested_size": all(
                count == int(arm_size)
                for count in Counter(row["pilot_arm"] for row in selected_families).values()
            )
            and len(Counter(row["pilot_arm"] for row in selected_families)) == 3,
            "selected_families_unique": len({row["family_id"] for row in selected_families})
            == len(selected_families),
            "planned_slot_count_equal_per_family": {
                len(_mapping_rows(row.get("planned_generation_slots"))) for row in selected_families
            }
            == {3},
            "manifest_generated": bool(pilot_manifest.get("pilot_families")),
        },
        "selected_families": selected_families,
        "pilot_manifest": pilot_manifest,
        "limitations": [
            "pilot_families_are_from_the_current_49_family_repaired_full_denominator",
            "historical_observed_failure_annotations_are_diagnostic_only",
            "middle_and_low_controls_are_required_to_avoid_top_rank_overfitting",
            "llm_generation_and_downstream_rescoring_are_not_done_by_this_harness",
        ],
        "next_steps": [
            "Use this manifest to generate or collect the same evidence/context slots for every arm.",
            "Apply generated evidence without changing thresholds, then compare improvement by high, middle, and low arms.",
            "Promote the heuristic only if high-need families improve more than middle and low controls.",
        ],
    }


def render_evidence_gap_control_pilot_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Control Pilot Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate families: `{summary.get('candidate_family_count', 0)}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Planned generation slots: `{summary.get('planned_generation_slot_count', 0)}`",
        "",
        "## Methodology",
        "",
        str(_as_mapping(report.get("methodology")).get("goal") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("selection_basis") or ""),
        "",
        "## Arm Summary",
        "",
        "| Arm | Families | Mean need | TF-IDF historical failure | ST historical failure |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    failure_by_arm = _as_mapping(summary.get("historical_observed_failure_by_arm"))
    arm_counts = _as_mapping(summary.get("arm_counts"))
    for arm in ("high_need", "middle_control", "low_control"):
        row = _as_mapping(failure_by_arm.get(arm))
        lines.append(
            f"| `{arm}` | {arm_counts.get(arm, 0)} | "
            f"{_number(row.get('mean_predicted_need'))} | "
            f"{_format_percent(row.get('tfidf_cosine_observed_failure_rate'))} | "
            f"{_format_percent(row.get('sentence_transformer_cosine_observed_failure_rate'))} |"
        )
    lines.extend(
        [
            "",
            "## Selected Families",
            "",
            "| Arm | Rank | Trigger | Target | Need | Slots | TF-IDF fail | ST fail |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("selected_families")):
        observed = _as_mapping(row.get("historical_observed_failure_by_scorer"))
        lines.append(
            f"| `{_escape_md(str(row.get('pilot_arm') or ''))}` | "
            f"{int(row.get('arm_rank') or 0)} | "
            f"`{_escape_md(str(row.get('trigger') or ''))}` | "
            f"`{_escape_md(str(row.get('target_lemma') or ''))}` | "
            f"{_number(row.get('predicted_need'))} | "
            f"{len(_mapping_rows(row.get('planned_generation_slots')))} | "
            f"{_format_percent(_as_mapping(observed.get('tfidf_cosine')).get('observed_failure_rate'))} | "
            f"{_format_percent(_as_mapping(observed.get('sentence_transformer_cosine')).get('observed_failure_rate'))} |"
        )
    lines.extend(["", "## Guardrails", "", "| Check | Value |", "| --- | --- |"])
    for key, value in _as_mapping(report.get("e2e_checks")).items():
        lines.append(f"| `{_escape_md(key)}` | `{value}` |")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


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


def _selection_rows(
    *,
    heuristic_payload: Mapping[str, object],
    family_metadata: Mapping[str, Mapping[str, object]],
    selection_scorer: str,
    selection_formula: str,
) -> list[dict[str, object]]:
    formula_weights = _selected_formula_weights(
        heuristic_payload=heuristic_payload,
        selection_scorer=selection_scorer,
        selection_formula=selection_formula,
    )
    observed_by_family: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    feature_rows = []
    for observation in _mapping_rows(heuristic_payload.get("observations")):
        family_id = str(observation.get("family_id") or "")
        scorer_id = str(observation.get("scorer_id") or "")
        observed_by_family[family_id][scorer_id] = {
            "observed_failure_rate": observation.get("observed_failure_rate"),
            "failure_count": observation.get("failure_count"),
            "case_count": observation.get("case_count"),
        }
        if scorer_id == selection_scorer:
            features = _as_mapping(observation.get("features"))
            predicted_need = _weighted_need(features=features, weights=formula_weights)
            metadata = _as_mapping(family_metadata.get(family_id))
            if not metadata:
                continue
            feature_rows.append(
                {
                    "family_id": family_id,
                    "trigger": str(metadata.get("trigger") or observation.get("trigger") or ""),
                    "target_lemma": str(
                        metadata.get("target_lemma") or observation.get("target_lemma") or ""
                    ),
                    "predicted_need": round(predicted_need, 4),
                    "selection_scorer": selection_scorer,
                    "selection_formula": selection_formula,
                    "selection_features": {
                        key: round(_safe_float(features.get(key)), 4) for key in sorted(features)
                    },
                    "historical_observed_failure_by_scorer": observed_by_family[family_id],
                    "active": metadata.get("active"),
                    "shadows": metadata.get("shadows"),
                }
            )
    return sorted(
        feature_rows, key=lambda row: (-_safe_float(row.get("predicted_need")), row["family_id"])
    )


def _selected_formula_weights(
    *,
    heuristic_payload: Mapping[str, object],
    selection_scorer: str,
    selection_formula: str,
) -> dict[str, float]:
    for row in _mapping_rows(heuristic_payload.get("comparison_rows")):
        if row.get("scorer_id") == selection_scorer and row.get("formula_id") == selection_formula:
            return {
                str(key): _safe_float(value)
                for key, value in _as_mapping(row.get("weights")).items()
            }
    if selection_formula == "evidence_gap_only":
        return {"evidence_gap_risk": 1.0}
    raise ValueError(
        f"Could not find formula {selection_formula!r} for scorer {selection_scorer!r}"
    )


def _select_control_arms(
    rows: Sequence[Mapping[str, object]],
    *,
    arm_size: int,
) -> list[dict[str, object]]:
    ranked = [dict(row) for row in rows]
    total = len(ranked)
    for index, row in enumerate(ranked, start=1):
        row["global_need_rank"] = index
        row["need_percentile"] = round((index - 1) / max(1, total - 1), 4)
    high = ranked[:arm_size]
    low = list(reversed(ranked[-arm_size:]))
    used = {row["family_id"] for row in [*high, *low]}
    median_rank = (total + 1) / 2.0
    middle = sorted(
        [row for row in ranked if row["family_id"] not in used],
        key=lambda row: (
            abs(_safe_float(row.get("global_need_rank")) - median_rank),
            row["family_id"],
        ),
    )[:arm_size]
    arms = [
        ("high_need", high),
        ("middle_control", sorted(middle, key=lambda row: row["global_need_rank"])),
        ("low_control", low),
    ]
    selected = []
    for arm, arm_rows in arms:
        for rank, row in enumerate(arm_rows, start=1):
            copied = dict(row)
            copied["pilot_arm"] = arm
            copied["arm_rank"] = rank
            copied["planned_generation_slots"] = _planned_generation_slots(copied)
            selected.append(copied)
    return selected


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
            "purpose": "Collect a context where no offered Spanish target should win, for guard calibration.",
        },
    ]


def _pilot_manifest(
    *,
    selected_families: Sequence[Mapping[str, object]],
    pilot_id: str,
    generated_at: str,
    selection_scorer: str,
    selection_formula: str,
    heuristic_path: Path | None,
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
            "heuristic_path": _repo_path(heuristic_path),
            "dataset_path": _repo_path(dataset_path),
            "selection_uses_observed_outcomes": False,
        },
        "generation_contract": {
            "same_contract_for_all_arms": True,
            "slot_types": [
                "active_evidence_expansion",
                "shadow_or_competitor_evidence_probe",
                "no_winner_context_probe",
            ],
            "evaluation_rule": (
                "Apply generated evidence to every arm under the same scorer and threshold "
                "settings, then compare improvement for high_need versus middle_control "
                "and low_control."
            ),
        },
        "pilot_families": list(selected_families),
    }


def _issues(
    *,
    selection_rows: Sequence[Mapping[str, object]],
    selected_families: Sequence[Mapping[str, object]],
    dataset_payload: Mapping[str, object],
    arm_size: int,
) -> list[str]:
    issues = []
    if str(dataset_payload.get("manual_review_state") or "") != "approved_by_user":
        issues.append("dataset_not_marked_approved_by_user")
    if not selection_rows:
        issues.append("no_selection_rows")
    arm_counts = Counter(row["pilot_arm"] for row in selected_families)
    for arm in ("high_need", "middle_control", "low_control"):
        if arm_counts.get(arm, 0) != arm_size:
            issues.append(f"arm_size_mismatch:{arm}")
    if len({row["family_id"] for row in selected_families}) != len(selected_families):
        issues.append("selected_family_overlap")
    return issues


def _observed_failure_by_arm(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pilot_arm") or "")].append(row)
    output = {}
    for arm, arm_rows in sorted(grouped.items()):
        scorer_values: dict[str, list[float]] = defaultdict(list)
        for row in arm_rows:
            for scorer_id, observed in _as_mapping(
                row.get("historical_observed_failure_by_scorer")
            ).items():
                scorer_values[str(scorer_id)].append(
                    _safe_float(_as_mapping(observed).get("observed_failure_rate"))
                )
        output[arm] = {
            "family_count": len(arm_rows),
            "mean_predicted_need": _mean(row.get("predicted_need") for row in arm_rows),
            **{
                f"{scorer_id}_observed_failure_rate": _mean(values)
                for scorer_id, values in sorted(scorer_values.items())
            },
        }
    return output


def _need_range(rows: Sequence[Mapping[str, object]]) -> dict[str, float | None]:
    values = [_safe_float(row.get("predicted_need")) for row in rows]
    if not values:
        return {"min": None, "max": None}
    return {"min": round(min(values), 4), "max": round(max(values), 4)}


def _evidence_text(sense: Mapping[str, object]) -> str:
    views = _as_mapping(_as_mapping(sense).get("evidence_views"))
    return str(
        views.get("all_evidence_text")
        or views.get("sense_gloss_bundle")
        or views.get("gloss_text")
        or views.get("sense_label")
        or ""
    )


def _weighted_need(*, features: Mapping[str, object], weights: Mapping[str, float]) -> float:
    return max(
        0.0,
        min(
            1.0,
            sum(
                _safe_float(features.get(feature)) * float(weight)
                for feature, weight in weights.items()
            ),
        ),
    )


def _mean(values: Sequence[object]) -> float | None:
    floats = [_safe_float(value) for value in values if value is not None]
    if not floats:
        return None
    return round(sum(floats) / len(floats), 4)


def _number(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_safe_float(value):.4f}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
