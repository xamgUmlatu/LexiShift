#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_sampling_stage1_materialization_rendering import (
    render_sampling_stage1_markdown as render_sampling_stage1_markdown,
)

from semantic_veto_formula_shape_bakeoff_en_es import (
    _load_json,
    _mapping_rows,
    _sequence,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_SAMPLING_DESIGN = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_expansion_design_en_es_latest.json"
)
DEFAULT_CURVE_PLAN = (
    TEST_OUTPUTS_ROOT / "semantic_veto_curve_guided_expansion_plan_en_es_latest.json"
)
DEFAULT_DIFFICULTY_STRATIFICATION = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_REPRESENTATIVE_GAP_ROWS = (
    TEST_INPUTS_ROOT / "semantic_veto_representative_gap_rows_en_es.json"
)
DEFAULT_P0_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_sampling_stage1_p0_manual_v1.json"
)
DEFAULT_REPRESENTATIVE_FRAME_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_frame_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_materialization_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_materialization_en_es_latest.md"
)
DEFAULT_TRIGGER_SPECS_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_sampling_stage1_trigger_specs_en_es.json"
)
DATASET_ID = "en_es_sampling_stage1_p0_manual_v1"
MANUAL_REVIEW_STATE = "agent_draft_human_review_pending"


@dataclass(frozen=True)
class SenseSpec:
    sense_id_suffix: str
    target_lemma: str
    canonical_pos: str
    sense_label: str
    gloss_text: str
    examples: tuple[str, ...]


@dataclass(frozen=True)
class ManualCaseSpec:
    cell_key: str
    sentence: str
    gold_decision: str
    gold_winner_kind: str
    note: str


@dataclass(frozen=True)
class TriggerSpec:
    trigger: str
    target_lemma: str
    active: SenseSpec
    shadows: tuple[SenseSpec, ...]
    cases: tuple[ManualCaseSpec, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize semantic-veto sampling Stage 1: representative sampling "
            "frame plus P0 manual discovery packet. No runtime policy changes."
        )
    )
    parser.add_argument("--sampling-design", type=Path, default=DEFAULT_SAMPLING_DESIGN)
    parser.add_argument("--curve-plan", type=Path, default=DEFAULT_CURVE_PLAN)
    parser.add_argument(
        "--difficulty-stratification",
        type=Path,
        default=DEFAULT_DIFFICULTY_STRATIFICATION,
    )
    parser.add_argument(
        "--representative-gap-rows",
        type=Path,
        default=DEFAULT_REPRESENTATIVE_GAP_ROWS,
    )
    parser.add_argument("--p0-dataset-out", type=Path, default=DEFAULT_P0_DATASET_OUT)
    parser.add_argument(
        "--representative-frame-out",
        type=Path,
        default=DEFAULT_REPRESENTATIVE_FRAME_OUT,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report, p0_dataset, representative_frame = build_sampling_stage1_materialization_report(
        sampling_design_payload=_load_json(args.sampling_design),
        curve_plan_payload=_load_json(args.curve_plan),
        difficulty_payload=_load_json(args.difficulty_stratification),
        representative_gap_payload=_load_optional_json(args.representative_gap_rows),
        sampling_design_path=args.sampling_design,
        curve_plan_path=args.curve_plan,
        difficulty_path=args.difficulty_stratification,
        representative_gap_path=args.representative_gap_rows,
        p0_dataset_path=args.p0_dataset_out,
        representative_frame_path=args.representative_frame_out,
    )
    args.p0_dataset_out.parent.mkdir(parents=True, exist_ok=True)
    args.representative_frame_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.p0_dataset_out.write_text(
        json.dumps(p0_dataset, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.representative_frame_out.write_text(
        json.dumps(representative_frame, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_sampling_stage1_markdown(report), encoding="utf-8")
    print(f"Wrote P0 dataset artifact to {args.p0_dataset_out}")
    print(f"Wrote representative frame artifact to {args.representative_frame_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_sampling_stage1_materialization_report(
    *,
    sampling_design_payload: Mapping[str, object],
    curve_plan_payload: Mapping[str, object],
    difficulty_payload: Mapping[str, object],
    representative_gap_payload: Mapping[str, object] | None = None,
    sampling_design_path: Path | None = None,
    curve_plan_path: Path | None = None,
    difficulty_path: Path | None = None,
    representative_gap_path: Path | None = None,
    p0_dataset_path: Path | None = None,
    representative_frame_path: Path | None = None,
    trigger_specs: Mapping[str, TriggerSpec] | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if generated_at is None:
        generated_at = _utc_now()
    specs = dict(trigger_specs or TRIGGER_SPECS)
    issues: list[str] = []
    lanes = _mapping_rows(sampling_design_payload.get("lane_reports"))
    representative_lane = _lane_by_type(lanes, "representative_random")
    targeted_lane = _lane_by_type(lanes, "targeted_curve_expansion")
    if not representative_lane:
        issues.append("missing_representative_lane")
    if not targeted_lane:
        issues.append("missing_targeted_curve_lane")
    p0_cells = [
        row
        for row in _mapping_rows(curve_plan_payload.get("expansion_queue"))
        if str(row.get("priority") or "") == "P0"
    ]
    if not p0_cells:
        issues.append("curve_plan_has_no_p0_cells")
    representative_frame = _representative_frame_payload(
        difficulty_payload=difficulty_payload,
        representative_gap_payload=representative_gap_payload or {},
        representative_lane=representative_lane,
        random_seed=str(
            _as_mapping(sampling_design_payload.get("methodology")).get("random_seed") or ""
        ),
        generated_at=generated_at,
    )
    p0_dataset, authored_rows = _p0_dataset(
        p0_cells=p0_cells,
        trigger_specs=specs,
    )
    missing_specs = sorted(
        {
            str(trigger)
            for cell in p0_cells
            for trigger in _sequence(cell.get("triggers"))
            if str(trigger) not in specs
        }
    )
    if missing_specs:
        issues.append("missing_p0_trigger_specs:" + ",".join(missing_specs))
    representative_summary = _as_mapping(representative_frame.get("summary"))
    p0_summary = {
        "p0_curve_cell_count": len(p0_cells),
        "p0_trigger_count": len({str(row.get("trigger") or "") for row in authored_rows}),
        "p0_manual_case_count": sum(
            len(_sequence(family.get("cases"))) for family in _sequence(p0_dataset.get("families"))
        ),
        "p0_case_type_counts": dict(
            sorted(Counter(str(row.get("manual_case_type") or "") for row in authored_rows).items())
        ),
        "p0_scorer_cell_counts": dict(
            sorted(Counter(str(row.get("scorer_id") or "") for row in authored_rows).items())
        ),
        "p0_trigger_case_counts": dict(
            sorted(Counter(str(row.get("trigger") or "") for row in authored_rows).items())
        ),
        "p0_dataset_fingerprint": _fingerprint(p0_dataset),
    }
    decision = (
        "sampling_stage1_materialized_with_representative_shortfall"
        if int(representative_summary.get("remaining_representative_rows_needed") or 0) > 0
        else "sampling_stage1_materialized"
    )
    report = {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": "sampling_stage1_incomplete" if issues else decision,
        "generated_at": generated_at,
        "pair": str(curve_plan_payload.get("pair") or difficulty_payload.get("pair") or "en-es"),
        "inputs": {
            "sampling_design_path": _repo_path(sampling_design_path),
            "curve_plan_path": _repo_path(curve_plan_path),
            "difficulty_stratification_path": _repo_path(difficulty_path),
            "representative_gap_rows_path": _repo_path(representative_gap_path),
            "sampling_design_decision": str(sampling_design_payload.get("decision") or ""),
            "curve_plan_decision": str(curve_plan_payload.get("decision") or ""),
            "difficulty_stratification_decision": str(difficulty_payload.get("decision") or ""),
            "representative_gap_dataset_id": str(
                (representative_gap_payload or {}).get("dataset_id") or ""
            ),
        },
        "outputs": {
            "p0_dataset_path": _repo_path(p0_dataset_path),
            "p0_dataset_id": p0_dataset.get("dataset_id"),
            "p0_dataset_fingerprint": p0_summary["p0_dataset_fingerprint"],
            "representative_frame_path": _repo_path(representative_frame_path),
            "representative_frame_id": representative_frame.get("frame_id"),
            "representative_frame_fingerprint": representative_summary.get("frame_fingerprint"),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_or_scorer_change": "none",
            "llm_generation": "none",
            "representative_frame_selection": (
                "stable seeded random order over existing representative-proxy rows "
                "plus reviewed primary representative-gap rows; selection excludes "
                "predicted decisions, product outcomes, errors, and scores"
            ),
            "p0_manual_packet_scope": (
                "P0 targeted curve cells only; all rows are discovery manual draft rows "
                "and cannot estimate real-world frequency"
            ),
            "manual_review_state": MANUAL_REVIEW_STATE,
        },
        "summary": {
            "issues": issues,
            **dict(representative_summary),
            **p0_summary,
        },
        "representative_frame_preview": _sequence(representative_frame.get("rows"))[:12],
        "p0_authored_rows": authored_rows,
        "bias_controls": [
            "representative_selection_does_not_use_scores_or_outcomes",
            "representative_shortfall_is_reported_not_backfilled_with_targeted_rows",
            "representative_gap_rows_are_corpus_like_primary_proxy_not_targeted_p0",
            "p0_rows_are_discovery_only",
            "p0_rows_are_not_representative_frequency_evidence",
            "llm_generation_waits_for_manual_contract_review",
        ],
        "limitations": [
            "representative_frame_uses_existing_v10_proxy_and_corpus_like_gap_proxy_not_final_browsing_distribution",
            "representative_gap_rows_are_agent_draft_human_review_pending",
            "p0_manual_rows_are_agent_draft_human_review_pending",
            "duplicate_trigger_p0_cells_are_preserved_because_current_curve_queue_is_scorer_cell_based",
        ],
        "next_steps": [
            "Human-review the P0 manual rows before LLM expansion.",
            "Human-review the 25 representative gap rows before using them for promotion claims.",
            "Prefer observed browser/runtime contexts for the next representative refresh when logs are available.",
            "Run leakage/control prompt checks before generating LLM discovery rows.",
            "Score the P0 manual packet as a discovery lane, then rerun the curve and sampling reports before expanding P1.",
        ],
    }
    return report, p0_dataset, representative_frame


def _representative_frame_payload(
    *,
    difficulty_payload: Mapping[str, object],
    representative_gap_payload: Mapping[str, object],
    representative_lane: Mapping[str, object],
    random_seed: str,
    generated_at: str,
) -> dict[str, object]:
    target = int(representative_lane.get("locked_eval_rows") or 0)
    rows = [
        row
        for row in _mapping_rows(difficulty_payload.get("case_traces"))
        if str(row.get("lane_type") or "") == "representative"
        and _counts_as_base_representative_row(row)
    ]
    frame_rows = [_representative_frame_row(row, random_seed=random_seed) for row in rows]
    gap_rows = _representative_gap_frame_rows(
        representative_gap_payload=representative_gap_payload,
        random_seed=random_seed,
    )
    frame_rows.extend(gap_rows)
    frame_rows.sort(key=lambda row: str(row.get("stable_random_key") or ""))
    for index, row in enumerate(frame_rows, start=1):
        row["selection_rank"] = index
        row["selected_for_locked_eval"] = index <= target
    payload = {
        "schema_version": 1,
        "frame_id": "semantic_veto_sampling_stage1_representative_frame_en_es_v1",
        "generated_at": generated_at,
        "pair": str(difficulty_payload.get("pair") or "en-es"),
        "selection_policy": {
            "lane_id": representative_lane.get("lane_id"),
            "target_locked_eval_rows": target,
            "selection_method": "stable_seeded_random_order",
            "random_seed": random_seed,
            "selection_excludes_fields": [
                "predicted_decision",
                "product_outcome",
                "error_type",
                "active_score",
                "strongest_shadow_score",
                "phrase_control_score",
            ],
            "primary_gap_rows_dataset_id": str(representative_gap_payload.get("dataset_id") or ""),
        },
        "rows": frame_rows,
    }
    payload["summary"] = {
        "target_locked_eval_rows": target,
        "available_representative_rows": len(frame_rows),
        "base_representative_rows": len(rows),
        "representative_gap_rows_added": len(gap_rows),
        "selected_locked_eval_rows": sum(
            1 for row in frame_rows if row.get("selected_for_locked_eval")
        ),
        "remaining_representative_rows_needed": max(0, target - len(frame_rows)),
        "trigger_count": len({str(row.get("trigger") or "") for row in frame_rows}),
        "context_source_counts": dict(
            sorted(Counter(str(row.get("context_source") or "") for row in frame_rows).items())
        ),
        "frame_fingerprint": _fingerprint(
            {
                "frame_id": payload["frame_id"],
                "pair": payload["pair"],
                "selection_policy": payload["selection_policy"],
                "rows": payload["rows"],
            }
        ),
    }
    return payload


def _representative_gap_frame_rows(
    *,
    representative_gap_payload: Mapping[str, object],
    random_seed: str,
) -> list[dict[str, object]]:
    source_id = str(
        representative_gap_payload.get("source_id") or "corpus_sampled_app_candidate_contexts"
    )
    source_class = str(representative_gap_payload.get("source_class") or "primary_corpus_proxy")
    context_source = str(
        representative_gap_payload.get("context_source")
        or "agent_curated_corpus_like_app_candidate_contexts"
    )
    review_state = str(
        representative_gap_payload.get("review_state") or "agent_draft_human_review_pending"
    )
    rows = []
    for row in _mapping_rows(representative_gap_payload.get("rows")):
        row_id = str(row.get("row_id") or "").strip()
        trigger = str(row.get("trigger") or "").strip()
        target = str(row.get("target_lemma") or "").strip()
        sentence = str(row.get("sentence") or "").strip()
        if not row_id or not trigger or not target or not sentence:
            continue
        stable_key = _stable_hash(
            "semantic_veto_sampling_stage1_representative_gap:"
            + "|".join([random_seed, row_id, trigger, target, sentence])
        )
        rows.append(
            {
                "frame_row_id": f"en-es:stage1-representative-gap:{stable_key[:12]}",
                "source_case_id": row_id,
                "slot_id": str(row.get("slot_id") or ""),
                "context_source": context_source,
                "source_class": source_class,
                "review_state": review_state,
                "counts_toward_primary_representative_target": bool(
                    representative_gap_payload.get(
                        "counts_toward_primary_representative_target",
                        True,
                    )
                ),
                "family_id": str(row.get("family_id") or ""),
                "lane_id": "representative_random_product_lane",
                "source_id": source_id,
                "split": "locked_eval",
                "suite_id": "representative_gap_primary_v1",
                "trigger": trigger,
                "target_lemma": target,
                "sentence": sentence,
                "gold_decision": str(row.get("gold_decision") or ""),
                "gold_winner": str(row.get("gold_winner") or ""),
                "gold_winner_type": str(row.get("gold_winner_type") or ""),
                "source_trigger_rank_en": row.get("source_trigger_rank_en"),
                "source_trigger_rank_bin_en": str(row.get("source_trigger_rank_bin_en") or ""),
                "target_lemma_rank_es": row.get("target_lemma_rank_es"),
                "target_lemma_rank_bin_es": str(row.get("target_lemma_rank_bin_es") or ""),
                "metadata_gap_flags": [
                    str(item) for item in _sequence(row.get("metadata_gap_flags"))
                ],
                "slice_tags": [str(item) for item in _sequence(row.get("slice_tags"))],
                "stable_random_key": stable_key,
                "selection_used_scoring_fields": False,
            }
        )
    return rows


def _counts_as_base_representative_row(row: Mapping[str, object]) -> bool:
    context_source = str(row.get("context_source") or "").strip()
    return context_source != "agent_curated_corpus_like_app_candidate_contexts"


def _representative_frame_row(row: Mapping[str, object], *, random_seed: str) -> dict[str, object]:
    case_id = str(row.get("case_id") or "")
    trigger = str(row.get("trigger") or "")
    target = str(row.get("target_lemma") or "")
    sentence = str(row.get("sentence") or "")
    stable_key = _stable_hash(
        "semantic_veto_sampling_stage1_representative_frame:"
        + "|".join([random_seed, case_id, trigger, target, sentence])
    )
    return {
        "frame_row_id": f"en-es:stage1-representative-frame:{stable_key[:12]}",
        "source_case_id": case_id,
        "context_source": "existing_sentence_veto_v10_representative_proxy",
        "family_id": str(row.get("family_id") or ""),
        "lane_id": str(row.get("lane_id") or ""),
        "source_id": str(row.get("source_id") or ""),
        "split": "locked_eval",
        "suite_id": str(row.get("suite_id") or ""),
        "trigger": trigger,
        "target_lemma": target,
        "sentence": sentence,
        "gold_decision": str(row.get("gold_decision") or ""),
        "gold_winner_type": str(row.get("gold_winner_type") or ""),
        "source_trigger_rank_en": row.get("source_trigger_rank_en"),
        "source_trigger_rank_bin_en": str(row.get("source_trigger_rank_bin_en") or ""),
        "target_lemma_rank_es": row.get("target_lemma_rank_es"),
        "target_lemma_rank_bin_es": str(row.get("target_lemma_rank_bin_es") or ""),
        "metadata_gap_flags": [str(item) for item in _sequence(row.get("metadata_gap_flags"))],
        "slice_tags": [str(item) for item in _sequence(row.get("slice_tags"))],
        "stable_random_key": stable_key,
        "selection_used_scoring_fields": False,
    }


def _p0_dataset(
    *,
    p0_cells: Sequence[Mapping[str, object]],
    trigger_specs: Mapping[str, TriggerSpec],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    families_by_trigger: dict[str, dict[str, object]] = {}
    authored_rows = []
    for cell_index, cell in enumerate(p0_cells, start=1):
        trigger = str((_sequence(cell.get("triggers")) or [""])[0])
        spec = trigger_specs.get(trigger)
        if spec is None:
            continue
        family = families_by_trigger.setdefault(trigger, _family_from_spec(spec))
        cell_key = _cell_key(cell=cell)
        matching_cases = [case for case in spec.cases if case.cell_key == cell_key]
        for local_index, case_spec in enumerate(matching_cases, start=1):
            case_id = f"en-es:sampling-stage1-p0:{trigger}:{cell_index:02d}:{local_index:03d}"
            case = _case_from_spec(
                case_id=case_id,
                trigger_spec=spec,
                cell=cell,
                case_spec=case_spec,
            )
            family["cases"].append(case)
            authored_rows.append(
                {
                    "case_id": case_id,
                    "trigger": spec.trigger,
                    "target_lemma": spec.target_lemma,
                    "manual_case_type": str(cell.get("manual_case_type") or ""),
                    "scorer_id": str(cell.get("scorer_id") or ""),
                    "heuristic_group": str(cell.get("heuristic_group") or ""),
                    "source_rank_bin": str(cell.get("source_rank_bin") or ""),
                    "polysemy_band": str(cell.get("polysemy_band") or ""),
                    "gold_decision": case_spec.gold_decision,
                    "sentence": case_spec.sentence,
                    "notes": case_spec.note,
                }
            )
    dataset = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": DATASET_ID,
        "description": (
            "Stage 1 P0 manual discovery rows for the scientific sampling expansion "
            "plan. Agent draft; human review required before LLM generation or locked-eval claims."
        ),
        "sampling_lane": "targeted_curve_mechanism_lane",
        "manual_review_state": MANUAL_REVIEW_STATE,
        "families": list(families_by_trigger.values()),
    }
    return dataset, authored_rows


def _family_from_spec(spec: TriggerSpec) -> dict[str, object]:
    active_id = _sense_id(spec=spec, sense=spec.active, kind="active")
    return {
        "family_id": f"en-es:sampling-stage1-p0:{spec.trigger}:{spec.target_lemma}",
        "trigger": spec.trigger,
        "active": _sense_payload(sense_id=active_id, sense=spec.active),
        "shadows": [
            _sense_payload(sense_id=_sense_id(spec=spec, sense=shadow, kind="shadow"), sense=shadow)
            for shadow in spec.shadows
        ],
        "cases": [],
    }


def _case_from_spec(
    *,
    case_id: str,
    trigger_spec: TriggerSpec,
    cell: Mapping[str, object],
    case_spec: ManualCaseSpec,
) -> dict[str, object]:
    manual_case_type = str(cell.get("manual_case_type") or "")
    winner = (
        _sense_id(spec=trigger_spec, sense=trigger_spec.active, kind="active")
        if case_spec.gold_winner_kind == "active"
        else "none"
    )
    return {
        "case_id": case_id,
        "sentence": case_spec.sentence,
        "source_phrase": trigger_spec.trigger,
        "gold_winner": winner,
        "gold_decision": case_spec.gold_decision,
        "slice_tags": [
            DATASET_ID,
            "manual_draft_v1",
            "targeted_curve_mechanism_lane",
            "discovery",
            "curve_priority:P0",
            str(cell.get("heuristic_group") or ""),
            "pre_outcome",
            f"rank_bin:{cell.get('source_rank_bin') or ''}",
            f"polysemy:{cell.get('polysemy_band') or ''}",
            manual_case_type,
            f"shadow_contract:{cell.get('shadow_contract') or ''}",
            f"scorer:{cell.get('scorer_id') or ''}",
        ],
        "slice_dimensions": {
            "sampling_lane": ["targeted_curve_mechanism_lane"],
            "split": ["discovery"],
            "curve_priority": ["P0"],
            "curve_cell_id": [str(cell.get("cell_id") or "")],
            "scorer_id": [str(cell.get("scorer_id") or "")],
            "heuristic_group": [str(cell.get("heuristic_group") or "")],
            "selection_mode": ["pre_outcome"],
            "source_rank_bin": [str(cell.get("source_rank_bin") or "")],
            "polysemy_band": [str(cell.get("polysemy_band") or "")],
            "manual_case_type": [manual_case_type],
            "shadow_contract": [str(cell.get("shadow_contract") or "")],
            "manual_review_state": [MANUAL_REVIEW_STATE],
        },
        "notes": case_spec.note,
    }


def _sense_payload(*, sense_id: str, sense: SenseSpec) -> dict[str, object]:
    evidence = " | ".join([sense.sense_label, sense.gloss_text, *sense.examples])
    return {
        "sense_id": sense_id,
        "target_lemma": sense.target_lemma,
        "canonical_pos": sense.canonical_pos,
        "evidence_views": {
            "sense_label": sense.sense_label,
            "gloss_text": sense.gloss_text,
            "sense_gloss_bundle": f"{sense.sense_label} | {sense.gloss_text}",
            "all_evidence_text": evidence,
        },
    }


def _cell_key(cell: Mapping[str, object]) -> str:
    return "::".join(
        [
            str(cell.get("manual_case_type") or ""),
            str(cell.get("scorer_id") or ""),
            str(cell.get("trigger") or ""),
        ]
    )


def _sense_id(*, spec: TriggerSpec, sense: SenseSpec, kind: str) -> str:
    return f"en-es:sampling-stage1-p0:{spec.trigger}:{spec.target_lemma}:{sense.sense_id_suffix}:{kind}"


def _lane_by_type(lanes: Sequence[Mapping[str, object]], lane_type: str) -> Mapping[str, object]:
    for lane in lanes:
        if str(lane.get("lane_type") or "") == lane_type:
            return lane
    return {}


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_optional_json(path: Path) -> dict[str, object]:
    candidate = Path(path)
    if not candidate.exists():
        return {}
    return _load_json(candidate)


def _fingerprint(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sense_spec_from_payload(payload: Mapping[str, object]) -> SenseSpec:
    return SenseSpec(
        sense_id_suffix=str(payload.get("sense_id_suffix") or ""),
        target_lemma=str(payload.get("target_lemma") or ""),
        canonical_pos=str(payload.get("canonical_pos") or ""),
        sense_label=str(payload.get("sense_label") or ""),
        gloss_text=str(payload.get("gloss_text") or ""),
        examples=tuple(str(item) for item in _sequence(payload.get("examples"))),
    )


def _manual_case_spec_from_payload(payload: Mapping[str, object]) -> ManualCaseSpec:
    return ManualCaseSpec(
        cell_key=str(payload.get("cell_key") or ""),
        sentence=str(payload.get("sentence") or ""),
        gold_decision=str(payload.get("gold_decision") or ""),
        gold_winner_kind=str(payload.get("gold_winner_kind") or ""),
        note=str(payload.get("note") or ""),
    )


def _trigger_spec_from_payload(payload: Mapping[str, object]) -> TriggerSpec:
    return TriggerSpec(
        trigger=str(payload.get("trigger") or ""),
        target_lemma=str(payload.get("target_lemma") or ""),
        active=_sense_spec_from_payload(_as_mapping(payload.get("active"))),
        shadows=tuple(
            _sense_spec_from_payload(_as_mapping(item))
            for item in _sequence(payload.get("shadows"))
        ),
        cases=tuple(
            _manual_case_spec_from_payload(_as_mapping(item))
            for item in _sequence(payload.get("cases"))
        ),
    )


def _load_trigger_specs(path: Path = DEFAULT_TRIGGER_SPECS_JSON) -> dict[str, TriggerSpec]:
    payload = _load_json(path)
    rows = _as_mapping(payload.get("trigger_specs"))
    return {
        str(trigger): _trigger_spec_from_payload(_as_mapping(spec_payload))
        for trigger, spec_payload in rows.items()
    }


TRIGGER_SPECS = _load_trigger_specs()
