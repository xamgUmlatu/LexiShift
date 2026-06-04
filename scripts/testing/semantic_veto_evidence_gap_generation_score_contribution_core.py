from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"
for candidate in (str(SCRIPT_ROOT), str(PROJECT_ROOT / "core")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import (  # noqa: E402
    build_sentence_veto_report,
)
from semantic_veto_evidence_gap_generation_admission_en_es import (  # noqa: E402
    ACTIVE_SLOT,
    NO_WINNER_SLOT,
    SHADOW_SLOT,
)
from semantic_veto_product_quality_en_es import _repo_path  # noqa: E402
from semantic_veto_evidence_gap_generation_score_contribution_summary import _next_steps  # noqa: E402
from semantic_veto_evidence_gap_generation_score_contribution_utils import (  # noqa: E402
    _application_summary,
    _as_mapping,
    _as_sequence as _as_sequence,
    _count_by,
    _delta,
    _fmt as _fmt,
    _load_json as _load_json,
    _mapping_rows,
    _normalize_target,
    _report_modes,
    _slug,
    _utc_now,
    _write_dataset,
)


DEFAULT_SCORER_ID = "tfidf_cosine"
DEFAULT_CONTEXT_VIEW = "masked_sentence"
DEFAULT_EVIDENCE_VIEW = "all_evidence_text"
AUGMENTED_DATASET_FAMILY = (
    "docs/test_outputs/experiments/semantic_veto_evidence_gap_augmented_datasets"
)
DEFAULT_AUGMENTED_DIR = PROJECT_ROOT / AUGMENTED_DATASET_FAMILY
POLICY_SWEEP_MIN_ACTIVE_SCORES = (0.05, 0.075, 0.1, 0.125)
POLICY_SWEEP_MIN_MARGINS = (0.0, 0.02, 0.05)
POLICY_SWEEP_PHRASE_CONTROL_MODES = ("off", "noun_family_frame_guard")
POLICY_SWEEP_ACTIVE_RESCUE_MODES = ("off", "sense_label_near_tie_active_rescue")
POLICY_SWEEP_HARMFUL_BUDGETS = (0, 1, 2)


def build_evidence_gap_score_contribution_report(
    *,
    dataset_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    selected_family_ids: Sequence[str] | None = None,
    dataset_path: Path | None = None,
    admission_path: Path | None = None,
    augmented_dir: Path = DEFAULT_AUGMENTED_DIR,
    scorer_id: str = DEFAULT_SCORER_ID,
    context_view: str = DEFAULT_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_EVIDENCE_VIEW,
    min_active_score: float = 0.05,
    min_margin: float = 0.0,
    phrase_control_mode: str = "off",
    active_rescue_mode: str = "off",
    include_policy_sweep: bool = True,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    admitted_items = _mapping_rows(admission_payload.get("admitted_items"))
    selected_family_ids = sorted(selected_family_ids or [])
    if not selected_family_ids:
        selected_family_ids = sorted(
            {
                str(item.get("family_id") or "")
                for item in admitted_items
                if str(item.get("family_id") or "")
            }
        )
    selected_family_ids = sorted(
        {str(family_id) for family_id in selected_family_ids if str(family_id)}
    )
    issues: list[str] = []
    if not selected_family_ids:
        issues.append("no_admitted_items_to_score")
    selected_dataset = _selected_dataset(dataset_payload, selected_family_ids)
    if not _mapping_rows(selected_dataset.get("families")):
        issues.append("no_matching_families_in_dataset")
    if issues:
        return {
            "schema_version": 1,
            "status": "review",
            "decision": "score_contribution_inputs_need_repair",
            "generated_at": generated_at,
            "pair": str(dataset_payload.get("pair") or admission_payload.get("pair") or "en-es"),
            "inputs": {
                "dataset_path": _repo_path(dataset_path),
                "admission_path": _repo_path(admission_path),
            },
            "methodology": _methodology(
                scorer_id=scorer_id,
                context_view=context_view,
                evidence_view=evidence_view,
                min_active_score=min_active_score,
                min_margin=min_margin,
                phrase_control_mode=phrase_control_mode,
                active_rescue_mode=active_rescue_mode,
                include_policy_sweep=include_policy_sweep,
            ),
            "artifacts": {},
            "summary": {
                "issues": issues,
                "selected_family_count": len(selected_family_ids),
                "admitted_item_count": len(admitted_items),
                "admitted_items_by_slot_type": _count_by(admitted_items, "slot_type"),
                "waived_item_count": int(
                    _as_mapping(admission_payload.get("summary")).get("coverage_waived_item_count")
                    or 0
                ),
            },
            "application_summary": {},
            "comparisons": {},
            "family_comparisons": {},
            "application_rows": {},
            "limitations": [
                "offline score-contribution probe only",
                "inputs were not scoreable",
            ],
            "next_steps": _next_steps(comparisons={}, issues=issues),
        }

    dataset_slug = _slug(str(_as_mapping(admission_payload.get("pilot")).get("pilot_id") or "run"))
    base_dataset_path = augmented_dir / f"{dataset_slug}_base_selected.json"
    existing_dataset_path = augmented_dir / f"{dataset_slug}_generated_existing_shadows.json"
    synthetic_dataset_path = augmented_dir / f"{dataset_slug}_generated_synthetic_shadows.json"
    augmented_dir.mkdir(parents=True, exist_ok=True)

    active_only_dataset, active_only_applications = _augment_dataset(
        selected_dataset,
        admitted_items=admitted_items,
        apply_active=True,
        apply_shadow=False,
        synthetic_shadows=False,
    )
    shadow_existing_only_dataset, shadow_existing_only_applications = _augment_dataset(
        selected_dataset,
        admitted_items=admitted_items,
        apply_active=False,
        apply_shadow=True,
        synthetic_shadows=False,
    )
    shadow_synthetic_only_dataset, shadow_synthetic_only_applications = _augment_dataset(
        selected_dataset,
        admitted_items=admitted_items,
        apply_active=False,
        apply_shadow=True,
        synthetic_shadows=True,
    )
    existing_dataset, existing_applications = _augment_dataset(
        selected_dataset,
        admitted_items=admitted_items,
        apply_active=True,
        apply_shadow=True,
        synthetic_shadows=False,
    )
    synthetic_dataset, synthetic_applications = _augment_dataset(
        selected_dataset,
        admitted_items=admitted_items,
        apply_active=True,
        apply_shadow=True,
        synthetic_shadows=True,
    )
    active_only_dataset_path = augmented_dir / f"{dataset_slug}_generated_active_only.json"
    shadow_existing_only_dataset_path = (
        augmented_dir / f"{dataset_slug}_generated_shadow_existing_only.json"
    )
    shadow_synthetic_only_dataset_path = (
        augmented_dir / f"{dataset_slug}_generated_shadow_synthetic_only.json"
    )
    _write_dataset(base_dataset_path, selected_dataset)
    _write_dataset(active_only_dataset_path, active_only_dataset)
    _write_dataset(shadow_existing_only_dataset_path, shadow_existing_only_dataset)
    _write_dataset(shadow_synthetic_only_dataset_path, shadow_synthetic_only_dataset)
    _write_dataset(existing_dataset_path, existing_dataset)
    _write_dataset(synthetic_dataset_path, synthetic_dataset)

    reports = {
        "base": _sentence_report(
            base_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
        "generated_active_only": _sentence_report(
            active_only_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
        "generated_shadow_existing_only": _sentence_report(
            shadow_existing_only_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
        "generated_shadow_synthetic_only": _sentence_report(
            shadow_synthetic_only_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
        "generated_existing_shadows": _sentence_report(
            existing_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
        "generated_synthetic_shadows": _sentence_report(
            synthetic_dataset_path,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
        ),
    }
    application_dataset_paths = {
        "generated_active_only": active_only_dataset_path,
        "generated_shadow_existing_only": shadow_existing_only_dataset_path,
        "generated_shadow_synthetic_only": shadow_synthetic_only_dataset_path,
        "generated_existing_shadows": existing_dataset_path,
        "generated_synthetic_shadows": synthetic_dataset_path,
    }
    comparisons = {
        mode: _compare_reports(reports["base"], report)
        for mode, report in reports.items()
        if mode != "base"
    }
    policy_sweep_rows = (
        _build_policy_sweep_rows(
            base_dataset_path=base_dataset_path,
            application_dataset_paths=application_dataset_paths,
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
        )
        if include_policy_sweep
        else []
    )
    best_by_harmful_budget = (
        _best_policy_rows_by_harmful_budget(policy_sweep_rows) if include_policy_sweep else {}
    )
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "score_contribution_ready_for_interpretation"
            if status == "ok"
            else "score_contribution_inputs_need_repair"
        ),
        "generated_at": generated_at,
        "pair": str(dataset_payload.get("pair") or admission_payload.get("pair") or "en-es"),
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "admission_path": _repo_path(admission_path),
        },
        "methodology": _methodology(
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            min_active_score=min_active_score,
            min_margin=min_margin,
            phrase_control_mode=phrase_control_mode,
            active_rescue_mode=active_rescue_mode,
            include_policy_sweep=include_policy_sweep,
        ),
        "artifacts": {
            "base_selected_dataset": _repo_path(base_dataset_path),
            "generated_active_only_dataset": _repo_path(active_only_dataset_path),
            "generated_shadow_existing_only_dataset": _repo_path(shadow_existing_only_dataset_path),
            "generated_shadow_synthetic_only_dataset": _repo_path(
                shadow_synthetic_only_dataset_path
            ),
            "generated_existing_shadows_dataset": _repo_path(existing_dataset_path),
            "generated_synthetic_shadows_dataset": _repo_path(synthetic_dataset_path),
        },
        "summary": {
            "issues": issues,
            "selected_family_count": len(selected_family_ids),
            "admitted_item_count": len(admitted_items),
            "admitted_items_by_slot_type": _count_by(admitted_items, "slot_type"),
            "waived_item_count": int(
                _as_mapping(admission_payload.get("summary")).get("coverage_waived_item_count") or 0
            ),
            "base": _summary_slice(reports["base"]),
            "generated_active_only": _summary_slice(reports["generated_active_only"]),
            "generated_shadow_existing_only": _summary_slice(
                reports["generated_shadow_existing_only"]
            ),
            "generated_shadow_synthetic_only": _summary_slice(
                reports["generated_shadow_synthetic_only"]
            ),
            "generated_existing_shadows": _summary_slice(reports["generated_existing_shadows"]),
            "generated_synthetic_shadows": _summary_slice(reports["generated_synthetic_shadows"]),
            "policy_sweep_row_count": len(policy_sweep_rows),
        },
        "application_summary": {
            "generated_active_only": _application_summary(active_only_applications),
            "generated_shadow_existing_only": _application_summary(
                shadow_existing_only_applications
            ),
            "generated_shadow_synthetic_only": _application_summary(
                shadow_synthetic_only_applications
            ),
            "generated_existing_shadows": _application_summary(existing_applications),
            "generated_synthetic_shadows": _application_summary(synthetic_applications),
        },
        "comparisons": comparisons,
        "family_comparisons": {
            mode: _family_comparison_rows(reports["base"], report)
            for mode, report in reports.items()
            if mode != "base"
        },
        "case_deltas": {
            mode: _case_delta_rows(reports["base"], report)
            for mode, report in reports.items()
            if mode != "base"
        },
        "policy_sweep_rows": policy_sweep_rows,
        "best_by_harmful_budget": best_by_harmful_budget,
        "application_rows": {
            "generated_active_only": active_only_applications,
            "generated_shadow_existing_only": shadow_existing_only_applications,
            "generated_shadow_synthetic_only": shadow_synthetic_only_applications,
            "generated_existing_shadows": existing_applications,
            "generated_synthetic_shadows": synthetic_applications,
        },
        "limitations": [
            "offline score-contribution probe only",
            "generated no-winner contexts are not used as runtime evidence in this probe",
            "synthetic shadow mode is diagnostic until new competitor targets are reviewed",
            "policy sweep reuses the same generated evidence batch and is not promotion evidence by itself",
            "selected batch is not broad enough to prove the full en-es heuristic curve",
        ],
        "next_steps": _next_steps(
            comparisons=comparisons,
            issues=issues,
            admitted_items_by_slot_type=_count_by(admitted_items, "slot_type"),
        ),
    }


def _selected_dataset(
    dataset_payload: Mapping[str, object],
    selected_family_ids: Sequence[str],
) -> dict[str, object]:
    selected = set(selected_family_ids)
    payload = deepcopy(dict(dataset_payload))
    payload["dataset_id"] = f"{dataset_payload.get('dataset_id', 'dataset')}:selected"
    payload["families"] = [
        deepcopy(family)
        for family in _mapping_rows(dataset_payload.get("families"))
        if str(family.get("family_id") or "") in selected
    ]
    return payload


def _methodology(
    *,
    scorer_id: str,
    context_view: str,
    evidence_view: str,
    min_active_score: float,
    min_margin: float,
    phrase_control_mode: str,
    active_rescue_mode: str,
    include_policy_sweep: bool,
) -> dict[str, object]:
    return {
        "runtime_policy_change": "none",
        "llm_call": "none",
        "threshold_tuning": "none",
        "scorer_id": scorer_id,
        "context_view": context_view,
        "evidence_view": evidence_view,
        "min_active_score": float(min_active_score),
        "min_margin": float(min_margin),
        "phrase_control_mode": phrase_control_mode,
        "active_rescue_mode": active_rescue_mode,
        "include_policy_sweep": bool(include_policy_sweep),
        "base_dataset_role": "frozen_manual_eval_cases",
        "generated_active_items": "appended_to_active_all_evidence_text",
        "generated_shadow_existing_mode": "append_only_when_target_matches_existing_shadow",
        "generated_shadow_synthetic_mode": "adds_generated_shadow_senses_for_new_targets",
        "application_bakeoff_modes": list(_report_modes()),
        "generated_no_winner_items": "not_used_as_evidence_in_this_probe",
    }


def _augment_dataset(
    dataset_payload: Mapping[str, object],
    *,
    admitted_items: Sequence[Mapping[str, object]],
    apply_active: bool,
    apply_shadow: bool,
    synthetic_shadows: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = deepcopy(dict(dataset_payload))
    families = _mapping_rows(payload.get("families"))
    families_by_id = {str(family.get("family_id") or ""): family for family in families}
    applications: list[dict[str, object]] = []
    for item in admitted_items:
        family = families_by_id.get(str(item.get("family_id") or ""))
        if family is None:
            continue
        slot_type = str(item.get("slot_type") or "")
        if slot_type == ACTIVE_SLOT:
            if apply_active:
                _append_evidence(
                    _as_mapping(family.get("active")),
                    _item_evidence_text(item),
                )
                applications.append(_application_row(item, "active_evidence_appended"))
            else:
                applications.append(_application_row(item, "active_evidence_ignored"))
        elif slot_type == SHADOW_SLOT:
            if not apply_shadow:
                applications.append(_application_row(item, "shadow_evidence_ignored"))
                continue
            shadow = _matching_shadow(family, item)
            if shadow is not None:
                _append_evidence(shadow, _item_evidence_text(item))
                applications.append(_application_row(item, "existing_shadow_evidence_appended"))
            elif synthetic_shadows:
                shadow = _synthetic_shadow(family, item)
                family.setdefault("shadows", []).append(shadow)
                applications.append(_application_row(item, "synthetic_shadow_created"))
            else:
                applications.append(_application_row(item, "new_shadow_target_ignored"))
        elif slot_type == NO_WINNER_SLOT:
            applications.append(_application_row(item, "no_winner_context_not_runtime_evidence"))
    return payload, applications


def _append_evidence(sense: Mapping[str, object], evidence_text: str) -> None:
    if not evidence_text:
        return
    evidence_views = sense.setdefault("evidence_views", {})
    if not isinstance(evidence_views, dict):
        return
    existing = str(evidence_views.get(DEFAULT_EVIDENCE_VIEW) or "").strip()
    evidence_views[DEFAULT_EVIDENCE_VIEW] = (
        f"{existing} | generated evidence: {evidence_text}" if existing else evidence_text
    )


def _matching_shadow(
    family: Mapping[str, object],
    item: Mapping[str, object],
) -> Mapping[str, object] | None:
    target = _normalize_target(
        str(item.get("target_lemma") or item.get("proposed_competitor_target_lemma") or "")
    )
    if not target:
        return None
    for shadow in _mapping_rows(family.get("shadows")):
        if _normalize_target(str(shadow.get("target_lemma") or "")) == target:
            return shadow
    return None


def _synthetic_shadow(
    family: Mapping[str, object], item: Mapping[str, object]
) -> dict[str, object]:
    target = str(item.get("target_lemma") or item.get("proposed_competitor_target_lemma") or "")
    family_id = str(family.get("family_id") or "")
    source = str(item.get("source_phrase") or family.get("trigger") or "")
    label = str(item.get("competitor_sense_label") or target or "generated competitor")
    evidence = _item_evidence_text(item)
    active = _as_mapping(family.get("active"))
    return {
        "sense_id": f"{family_id}:generated_shadow:{_slug(target or label)}",
        "target_lemma": target,
        "canonical_pos": str(active.get("canonical_pos") or ""),
        "evidence_views": {
            "sense_label": f"{source} -> {target}",
            "gloss_text": label,
            "sense_gloss_bundle": f"{source} -> {target} | {label}",
            DEFAULT_EVIDENCE_VIEW: f"{source} -> {target} | {label} | generated evidence: {evidence}",
        },
    }


def _item_evidence_text(item: Mapping[str, object]) -> str:
    parts = [
        str(item.get("sentence") or ""),
        str(item.get("evidence_note") or ""),
    ]
    return " ; ".join(part.strip() for part in parts if part and part.strip())


def _application_row(item: Mapping[str, object], action: str) -> dict[str, object]:
    return {
        "item_id": str(item.get("item_id") or ""),
        "family_id": str(item.get("family_id") or ""),
        "pilot_arm": str(item.get("pilot_arm") or ""),
        "slot_type": str(item.get("slot_type") or ""),
        "target_lemma": str(item.get("target_lemma") or ""),
        "proposed_competitor_target_lemma": str(item.get("proposed_competitor_target_lemma") or ""),
        "action": action,
    }


def _sentence_report(
    dataset_path: Path,
    *,
    scorer_id: str,
    context_view: str,
    evidence_view: str,
    min_active_score: float = 0.05,
    min_margin: float = 0.0,
    phrase_control_mode: str = "off",
    active_rescue_mode: str = "off",
) -> Mapping[str, object]:
    return build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=scorer_id,
        context_view=context_view,
        evidence_view=evidence_view,
        min_active_score=float(min_active_score),
        min_margin=float(min_margin),
        phrase_control_mode=phrase_control_mode,
        active_rescue_mode=active_rescue_mode,
    )


def _build_policy_sweep_rows(
    *,
    base_dataset_path: Path,
    application_dataset_paths: Mapping[str, Path],
    scorer_id: str,
    context_view: str,
    evidence_view: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for min_active_score in POLICY_SWEEP_MIN_ACTIVE_SCORES:
        for min_margin in POLICY_SWEEP_MIN_MARGINS:
            for phrase_control_mode in POLICY_SWEEP_PHRASE_CONTROL_MODES:
                for active_rescue_mode in POLICY_SWEEP_ACTIVE_RESCUE_MODES:
                    base_report = _sentence_report(
                        base_dataset_path,
                        scorer_id=scorer_id,
                        context_view=context_view,
                        evidence_view=evidence_view,
                        min_active_score=min_active_score,
                        min_margin=min_margin,
                        phrase_control_mode=phrase_control_mode,
                        active_rescue_mode=active_rescue_mode,
                    )
                    for application_mode, dataset_path in application_dataset_paths.items():
                        candidate_report = _sentence_report(
                            dataset_path,
                            scorer_id=scorer_id,
                            context_view=context_view,
                            evidence_view=evidence_view,
                            min_active_score=min_active_score,
                            min_margin=min_margin,
                            phrase_control_mode=phrase_control_mode,
                            active_rescue_mode=active_rescue_mode,
                        )
                        candidate = _summary_slice(candidate_report)
                        comparison = _compare_reports(base_report, candidate_report)
                        rows.append(
                            {
                                "application_mode": application_mode,
                                "scorer_id": scorer_id,
                                "context_view": context_view,
                                "evidence_view": evidence_view,
                                "min_active_score": float(min_active_score),
                                "min_margin": float(min_margin),
                                "phrase_control_mode": phrase_control_mode,
                                "active_rescue_mode": active_rescue_mode,
                                "decision_accuracy": candidate.get("decision_accuracy"),
                                "replace_recall": candidate.get("replace_recall"),
                                "harmful_replace_count": candidate.get("harmful_replace_count"),
                                "false_abstain_count": candidate.get("false_abstain_count"),
                                "winner_accuracy": candidate.get("winner_accuracy"),
                                "predicted_replace_cases": candidate.get("predicted_replace_cases"),
                                "active_rescue_applied_count": _active_rescue_applied_count(
                                    candidate_report
                                ),
                                **comparison,
                            }
                        )
    return sorted(rows, key=_policy_sweep_sort_key)


def _best_policy_rows_by_harmful_budget(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    best: dict[str, dict[str, object]] = {}
    for budget in POLICY_SWEEP_HARMFUL_BUDGETS:
        candidates = [
            dict(row) for row in rows if int(row.get("harmful_replace_count") or 0) <= int(budget)
        ]
        if not candidates:
            best[str(budget)] = {}
            continue
        best[str(budget)] = sorted(candidates, key=_best_policy_sort_key)[0]
    return best


def _best_policy_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        -float(row.get("decision_accuracy") or 0.0),
        int(row.get("false_abstain_count") or 0),
        -float(row.get("replace_recall") or 0.0),
        int(row.get("harmful_replace_count") or 0),
        -float(row.get("winner_accuracy") or 0.0),
        _policy_complexity(row),
        str(row.get("application_mode") or ""),
    )


def _policy_sweep_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("application_mode") or ""),
        float(row.get("min_active_score") or 0.0),
        float(row.get("min_margin") or 0.0),
        str(row.get("phrase_control_mode") or ""),
        str(row.get("active_rescue_mode") or ""),
    )


def _policy_complexity(row: Mapping[str, object]) -> int:
    score = 0
    if str(row.get("phrase_control_mode") or "") != "off":
        score += 1
    if str(row.get("active_rescue_mode") or "") != "off":
        score += 1
    if "synthetic" in str(row.get("application_mode") or ""):
        score += 1
    return score


def _active_rescue_applied_count(report: Mapping[str, object]) -> int:
    return sum(
        1 for row in _mapping_rows(report.get("row_results")) if row.get("active_rescue_applied")
    )


def _compare_reports(
    base_report: Mapping[str, object],
    candidate_report: Mapping[str, object],
) -> dict[str, object]:
    base = _as_mapping(base_report.get("summary"))
    candidate = _as_mapping(candidate_report.get("summary"))
    return {
        "decision_accuracy_delta": _delta(candidate, base, "decision_accuracy"),
        "replace_recall_delta": _delta(candidate, base, "replace_recall"),
        "winner_accuracy_delta": _delta(candidate, base, "winner_accuracy"),
        "harmful_replace_delta": int(candidate.get("harmful_replace_count") or 0)
        - int(base.get("harmful_replace_count") or 0),
        "false_abstain_delta": int(candidate.get("false_abstain_count") or 0)
        - int(base.get("false_abstain_count") or 0),
        "predicted_replace_delta": int(candidate.get("predicted_replace_cases") or 0)
        - int(base.get("predicted_replace_cases") or 0),
    }


def _family_comparison_rows(
    base_report: Mapping[str, object],
    candidate_report: Mapping[str, object],
) -> list[dict[str, object]]:
    base_rows = {
        str(row.get("family_id") or ""): row
        for row in _mapping_rows(base_report.get("family_breakdown"))
    }
    rows = []
    for row in _mapping_rows(candidate_report.get("family_breakdown")):
        family_id = str(row.get("family_id") or "")
        base = _as_mapping(_as_mapping(base_rows.get(family_id)).get("summary"))
        candidate = _as_mapping(row.get("summary"))
        rows.append(
            {
                "family_id": family_id,
                "trigger": str(row.get("trigger") or ""),
                "base_false_abstain_count": int(base.get("false_abstain_count") or 0),
                "candidate_false_abstain_count": int(candidate.get("false_abstain_count") or 0),
                "false_abstain_delta": int(candidate.get("false_abstain_count") or 0)
                - int(base.get("false_abstain_count") or 0),
                "base_harmful_replace_count": int(base.get("harmful_replace_count") or 0),
                "candidate_harmful_replace_count": int(candidate.get("harmful_replace_count") or 0),
                "harmful_replace_delta": int(candidate.get("harmful_replace_count") or 0)
                - int(base.get("harmful_replace_count") or 0),
            }
        )
    return rows


def _case_delta_rows(
    base_report: Mapping[str, object],
    candidate_report: Mapping[str, object],
) -> list[dict[str, object]]:
    base_rows = {
        str(row.get("case_id") or ""): row for row in _mapping_rows(base_report.get("row_results"))
    }
    rows = []
    for candidate in _mapping_rows(candidate_report.get("row_results")):
        case_id = str(candidate.get("case_id") or "")
        base = _as_mapping(base_rows.get(case_id))
        if not base:
            continue
        rows.append(
            {
                "case_id": case_id,
                "family_id": str(candidate.get("family_id") or ""),
                "trigger": str(candidate.get("trigger") or ""),
                "sentence": str(candidate.get("sentence") or ""),
                "gold_decision": str(candidate.get("gold_decision") or ""),
                "gold_winner_type": str(candidate.get("gold_winner_type") or ""),
                "base_predicted_decision": str(base.get("predicted_decision") or ""),
                "candidate_predicted_decision": str(candidate.get("predicted_decision") or ""),
                "base_predicted_winner_type": str(base.get("predicted_winner_type") or ""),
                "candidate_predicted_winner_type": str(
                    candidate.get("predicted_winner_type") or ""
                ),
                "decision_changed": str(base.get("predicted_decision") or "")
                != str(candidate.get("predicted_decision") or ""),
                "winner_changed": str(base.get("predicted_winner") or "")
                != str(candidate.get("predicted_winner") or ""),
                "base_active_score": base.get("active_score"),
                "candidate_active_score": candidate.get("active_score"),
                "active_score_delta": _delta(candidate, base, "active_score"),
                "base_strongest_shadow_score": base.get("strongest_shadow_score"),
                "candidate_strongest_shadow_score": candidate.get("strongest_shadow_score"),
                "strongest_shadow_score_delta": _delta(candidate, base, "strongest_shadow_score"),
            }
        )
    return rows


def _summary_slice(report: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(report.get("summary"))
    keys = (
        "cases_total",
        "decision_accuracy",
        "replace_recall",
        "harmful_replace_count",
        "false_abstain_count",
        "winner_accuracy",
        "predicted_replace_cases",
    )
    return {key: summary.get(key) for key in keys}
