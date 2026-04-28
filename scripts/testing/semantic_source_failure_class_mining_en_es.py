#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping, Sequence

from semantic_source_failure_class_mining_rendering import (
    render_source_failure_class_mining_markdown,
)
from semantic_source_failure_class_mining_support import (
    _as_mapping,
    _as_sequence,
    _best_comparator,
    _family_token,
    _heldout_family_ids,
    _item_at,
    _label_at,
    _load_json,
    _load_optional_json,
    _reason_count_ids,
    _safe_ratio,
    _sense_sidecar_for,
    _utc_now,
    _write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"

DEFAULT_PRIMARY_ADMISSION_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_source_admission_cycle_wordnet_def_source_non_v10_probe_v1_latest.json"
)
DEFAULT_PRIMARY_HELDOUT_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_source_non_v10_heldout_v1_margin005_validation_latest.json"
)
DEFAULT_COMPARATOR_ADMISSION_JSONS = (
    TEST_OUTPUTS_ROOT
    / "semantic_source_admission_cycle_wordnet_source_non_v10_probe_v1_latest.json",
)
DEFAULT_SOURCE_REPORT_JSONS = (
    TEST_OUTPUTS_ROOT / "semantic_wordnet_def_source_non_v10_probe_v1_latest.json",
    TEST_OUTPUTS_ROOT / "semantic_wordnet_source_non_v10_probe_v1_latest.json",
)
DEFAULT_MARGIN_SWEEP_JSON = TEST_OUTPUTS_ROOT / "semantic_source_margin_policy_sweep_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_failure_class_mining_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_failure_class_mining_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Mine semantic-source artifacts for reusable failure classes and overfit risk. "
            "This is a no-spend harness: it reads existing admission, held-out, source, and "
            "margin-sweep artifacts."
        )
    )
    parser.add_argument(
        "--primary-admission-json", type=Path, default=DEFAULT_PRIMARY_ADMISSION_JSON
    )
    parser.add_argument("--primary-heldout-json", type=Path, default=DEFAULT_PRIMARY_HELDOUT_JSON)
    parser.add_argument(
        "--additional-heldout-json",
        action="append",
        default=None,
        type=Path,
        help=(
            "Optional additional held-out validation report. Use this when active/shadow "
            "and phrase/no-winner suites are validated separately."
        ),
    )
    parser.add_argument(
        "--comparator-admission-json",
        action="append",
        default=None,
        type=Path,
        help=(
            "Optional comparator admission report. Defaults to the WordNet example-preferred "
            "non-v10 report when the option is omitted."
        ),
    )
    parser.add_argument(
        "--source-report-json",
        action="append",
        default=None,
        type=Path,
        help=(
            "Optional source extraction report. Defaults to the WordNet definition- and "
            "example-preferred non-v10 reports when the option is omitted."
        ),
    )
    parser.add_argument("--margin-sweep-json", type=Path, default=DEFAULT_MARGIN_SWEEP_JSON)
    parser.add_argument("--min-broad-family-count", type=int, default=50)
    parser.add_argument("--min-broad-case-count", type=int, default=200)
    parser.add_argument(
        "--policy-delta-count",
        type=int,
        default=0,
        help=(
            "Optional manually supplied count of broad policy/code deltas in the slice. "
            "The default stays zero so leverage is not overstated from artifacts alone."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when promotion readiness is still review.",
    )
    return parser.parse_args()


def build_source_failure_class_mining_report(
    *,
    primary_admission_payload: Mapping[str, object],
    primary_heldout_payload: Mapping[str, object],
    comparator_admission_payloads: Sequence[Mapping[str, object]] = (),
    source_report_payloads: Sequence[Mapping[str, object]] = (),
    margin_sweep_payload: Mapping[str, object] | None = None,
    additional_heldout_payloads: Sequence[Mapping[str, object]] = (),
    primary_admission_label: str = "primary_admission",
    primary_heldout_label: str = "primary_heldout",
    additional_heldout_labels: Sequence[str] = (),
    comparator_admission_labels: Sequence[str] = (),
    source_report_labels: Sequence[str] = (),
    primary_sense_payload: Mapping[str, object] | None = None,
    comparator_sense_payloads: Sequence[Mapping[str, object] | None] = (),
    min_broad_family_count: int = 50,
    min_broad_case_count: int = 200,
    policy_delta_count: int = 0,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    primary_admission = _admission_row(
        label=primary_admission_label,
        role="primary",
        payload=primary_admission_payload,
        sense_payload=primary_sense_payload,
    )
    primary_heldout = _heldout_row(label=primary_heldout_label, payload=primary_heldout_payload)
    additional_heldout_rows = [
        _heldout_row(
            label=_label_at(additional_heldout_labels, index, f"additional_heldout_{index + 1}"),
            payload=payload,
        )
        for index, payload in enumerate(additional_heldout_payloads)
    ]
    comparator_rows = [
        _admission_row(
            label=_label_at(comparator_admission_labels, index, f"comparator_{index + 1}"),
            role="comparator",
            payload=payload,
            sense_payload=_item_at(comparator_sense_payloads, index),
        )
        for index, payload in enumerate(comparator_admission_payloads)
    ]
    source_rows = [
        _source_report_row(
            label=_label_at(source_report_labels, index, f"source_{index + 1}"),
            payload=payload,
        )
        for index, payload in enumerate(source_report_payloads)
    ]
    margin_row = (
        _margin_sweep_row(margin_sweep_payload) if isinstance(margin_sweep_payload, Mapping) else {}
    )
    failure_classes = _build_failure_classes(
        primary_admission=primary_admission,
        primary_heldout=primary_heldout,
        additional_heldouts=additional_heldout_rows,
        comparator_admissions=comparator_rows,
        source_reports=source_rows,
        margin_sweep=margin_row,
    )
    leverage = _build_leverage_summary(
        primary_admission=primary_admission,
        primary_heldout=primary_heldout,
        additional_heldouts=additional_heldout_rows,
        source_reports=source_rows,
        comparator_admissions=comparator_rows,
        min_broad_family_count=min_broad_family_count,
        min_broad_case_count=min_broad_case_count,
        policy_delta_count=policy_delta_count,
    )
    quality_gate = _build_quality_gate_distance(
        primary_admission=primary_admission,
        primary_heldout=primary_heldout,
        additional_heldouts=additional_heldout_rows,
        leverage=leverage,
    )
    decision = _decision_from_gate_and_leverage(quality_gate=quality_gate, leverage=leverage)
    status = (
        "ok"
        if quality_gate["distance"] == "breadth_only" and leverage["manual_overfit_risk"] == "low"
        else "review"
    )
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "generated_at": generated_at,
        "summary": {
            "primary_admission_label": primary_admission["label"],
            "primary_heldout_label": primary_heldout["label"],
            "heldout_suite_count": 1 + len(additional_heldout_rows),
            "failure_class_count": len(failure_classes),
            "blocking_failure_class_count": sum(
                1 for row in failure_classes if bool(row.get("blocks_semantic_promotion"))
            ),
            "tracked_residual_class_count": sum(
                1 for row in failure_classes if bool(row.get("tracked_residual"))
            ),
            "manual_overfit_risk": leverage["manual_overfit_risk"],
            "promotion_readiness": quality_gate["promotion_readiness"],
            "quality_gate_distance": quality_gate["distance"],
        },
        "primary_admission": primary_admission,
        "primary_heldout": primary_heldout,
        "additional_heldouts": additional_heldout_rows,
        "comparator_admissions": comparator_rows,
        "source_reports": source_rows,
        "margin_sweep": margin_row,
        "failure_classes": failure_classes,
        "leverage": leverage,
        "quality_gate": quality_gate,
        "next_steps": _next_steps(decision=decision, quality_gate=quality_gate, leverage=leverage),
    }


def _admission_row(
    *,
    label: str,
    role: str,
    payload: Mapping[str, object],
    sense_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    summary = _as_mapping(payload.get("summary"))
    residuals = _as_mapping(payload.get("residuals"))
    best = _as_mapping(summary.get("best_ablation_row"))
    heldout = _as_mapping(summary.get("heldout_validation"))
    sense_summary = (
        _as_mapping(sense_payload.get("summary")) if isinstance(sense_payload, Mapping) else {}
    )
    rejection_reason_counts = _as_mapping(sense_summary.get("rejection_reason_counts"))
    sense_rejected = int(
        summary.get("sense_rejected_row_count")
        or sense_summary.get("semantic_rejected_row_count")
        or 0
    )
    return {
        "label": str(label or "").strip(),
        "role": str(role or "").strip(),
        "status": str(payload.get("status") or "").strip(),
        "decision": str(payload.get("decision") or "").strip(),
        "leakage_rejected_row_count": int(summary.get("leakage_rejected_row_count") or 0),
        "sense_rejected_row_count": sense_rejected,
        "sense_rejection_reason_counts": dict(rejection_reason_counts),
        "final_admitted_row_count": int(summary.get("final_admitted_row_count") or 0),
        "families_total": int(summary.get("families_total") or 0),
        "semantic_contract_complete_family_count": int(
            summary.get("semantic_contract_complete_family_count") or 0
        ),
        "phrase_contract_complete_family_count": int(
            summary.get("phrase_contract_complete_family_count") or 0
        ),
        "semantic_gap_family_keys": list(_as_sequence(residuals.get("semantic_gap_family_keys"))),
        "phrase_gap_family_keys": list(
            _as_sequence(residuals.get("phrase_containment_gap_family_keys"))
        ),
        "seed_harmful_replace_count": int(best.get("harmful_replace_count") or 0),
        "seed_false_abstain_count": int(best.get("false_abstain_count") or 0),
        "seed_harmful_replace_case_ids": list(_as_sequence(best.get("harmful_replace_case_ids"))),
        "seed_false_abstain_case_ids": list(_as_sequence(best.get("false_abstain_case_ids"))),
        "seed_decision_accuracy": float(best.get("decision_accuracy") or 0.0),
        "seed_replace_recall": float(best.get("replace_recall") or 0.0),
        "heldout_validation": dict(heldout),
    }


def _heldout_row(*, label: str, payload: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(payload.get("summary"))
    delta = _as_mapping(summary.get("delta_vs_empty_baseline"))
    family_ids = _heldout_family_ids(payload)
    return {
        "label": str(label or "").strip(),
        "status": str(payload.get("status") or summary.get("status") or "").strip(),
        "decision": str(payload.get("decision") or summary.get("decision") or "").strip(),
        "heldout_dataset_id": str(payload.get("heldout_dataset_id") or "").strip(),
        "heldout_case_scope": str(payload.get("heldout_case_scope") or "").strip(),
        "case_count": int(summary.get("case_count") or 0),
        "family_count": int(summary.get("family_count") or 0),
        "family_ids": family_ids,
        "gold_replace_cases": int(summary.get("gold_replace_cases") or 0),
        "gold_abstain_cases": int(summary.get("gold_abstain_cases") or 0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "harmful_replace_case_ids": list(_as_sequence(summary.get("harmful_replace_case_ids"))),
        "false_abstain_case_ids": list(_as_sequence(summary.get("false_abstain_case_ids"))),
        "replace_recall": float(summary.get("replace_recall") or 0.0),
        "decision_accuracy": float(summary.get("decision_accuracy") or 0.0),
        "delta_vs_empty_baseline": dict(delta),
    }


def _source_report_row(*, label: str, payload: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(payload.get("summary"))
    source_family_count = int(
        summary.get("source_family_count")
        or summary.get("materialized_family_count")
        or summary.get("selected_family_count")
        or 0
    )
    target_family_count = int(
        summary.get("target_family_count")
        or summary.get("selected_family_count")
        or summary.get("materialized_family_count")
        or 0
    )
    row_count = int(
        summary.get("row_count")
        or summary.get("final_admitted_row_count")
        or summary.get("candidate_row_count")
        or 0
    )
    semantic_complete_count = int(summary.get("semantic_contract_complete_family_count") or 0)
    phrase_complete_count = int(summary.get("phrase_contract_complete_family_count") or 0)
    return {
        "label": str(label or "").strip(),
        "evidence_mode": str(summary.get("evidence_mode") or payload.get("decision") or "").strip(),
        "source_family_count": source_family_count,
        "target_family_count": target_family_count,
        "row_count": row_count,
        "families_with_active_wordnet": int(
            summary.get("families_with_active_wordnet") or semantic_complete_count
        ),
        "families_with_shadow_wordnet": int(
            summary.get("families_with_shadow_wordnet") or semantic_complete_count
        ),
        "target_families_with_active_wordnet": int(
            summary.get("target_families_with_active_wordnet") or semantic_complete_count
        ),
        "target_families_with_shadow_wordnet": int(
            summary.get("target_families_with_shadow_wordnet") or semantic_complete_count
        ),
        "missing_active_family_keys": list(_as_sequence(summary.get("missing_active_family_keys"))),
        "missing_shadow_family_keys": list(_as_sequence(summary.get("missing_shadow_family_keys"))),
        "families_with_phrase_control_examples": int(
            summary.get("families_with_phrase_control_examples") or phrase_complete_count
        ),
    }


def _margin_sweep_row(payload: Mapping[str, object]) -> dict[str, object]:
    summary = _as_mapping(payload.get("summary"))
    recommendation = _as_mapping(payload.get("recommendation"))
    return {
        "status": str(payload.get("status") or "").strip(),
        "decision": str(payload.get("decision") or "").strip(),
        "suite_count": int(summary.get("suite_count") or 0),
        "row_count": int(summary.get("row_count") or 0),
        "recommended_min_margin": summary.get("recommended_min_margin"),
        "passing_margins": list(_as_sequence(recommendation.get("passing_margins"))),
        "blockers_by_margin": dict(_as_mapping(recommendation.get("blockers_by_margin"))),
    }


def _build_failure_classes(
    *,
    primary_admission: Mapping[str, object],
    primary_heldout: Mapping[str, object],
    additional_heldouts: Sequence[Mapping[str, object]],
    comparator_admissions: Sequence[Mapping[str, object]],
    source_reports: Sequence[Mapping[str, object]],
    margin_sweep: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(_heldout_failure_classes(primary_heldout))
    for index, heldout in enumerate(additional_heldouts, start=1):
        rows.extend(
            _heldout_failure_classes(
                heldout,
                class_prefix=f"additional_heldout_{index}",
            )
        )
    rows.extend(_admission_failure_classes(primary_admission, comparator=False))
    for comparator in comparator_admissions:
        rows.extend(_admission_failure_classes(comparator, comparator=True))
    rows.extend(_source_failure_classes(source_reports))
    rows.extend(_margin_failure_classes(margin_sweep))
    return [row for row in rows if int(row.get("count") or 0) > 0]


def _heldout_failure_classes(
    heldout: Mapping[str, object],
    *,
    class_prefix: str = "heldout",
) -> list[dict[str, object]]:
    return [
        _failure_class(
            class_id=f"{class_prefix}_harmful_replace",
            label="Held-out harmful replacement",
            count=int(heldout.get("harmful_replace_count") or 0),
            artifact=str(heldout.get("label") or ""),
            ids=_as_sequence(heldout.get("harmful_replace_case_ids")),
            blocks=True,
        ),
        _failure_class(
            class_id=f"{class_prefix}_false_abstain",
            label="Held-out false abstain",
            count=int(heldout.get("false_abstain_count") or 0),
            artifact=str(heldout.get("label") or ""),
            ids=_as_sequence(heldout.get("false_abstain_case_ids")),
            tracked=True,
        ),
    ]


def _admission_failure_classes(
    admission: Mapping[str, object], *, comparator: bool
) -> list[dict[str, object]]:
    role_prefix = "comparator" if comparator else "primary"
    tracked = True
    rows = [
        _failure_class(
            class_id=f"{role_prefix}_sense_reject",
            label=f"{role_prefix} sense rejected rows",
            count=int(admission.get("sense_rejected_row_count") or 0),
            artifact=str(admission.get("label") or ""),
            ids=_reason_count_ids(_as_mapping(admission.get("sense_rejection_reason_counts"))),
            tracked=tracked,
        ),
        _failure_class(
            class_id=f"{role_prefix}_semantic_contract_gap",
            label=f"{role_prefix} semantic contract gap",
            count=len(_as_sequence(admission.get("semantic_gap_family_keys"))),
            artifact=str(admission.get("label") or ""),
            ids=_as_sequence(admission.get("semantic_gap_family_keys")),
            blocks=not comparator,
            tracked=comparator,
        ),
        _failure_class(
            class_id=f"{role_prefix}_seed_harmful_replace",
            label=f"{role_prefix} seed ablation harmful replacement",
            count=int(admission.get("seed_harmful_replace_count") or 0),
            artifact=str(admission.get("label") or ""),
            ids=_as_sequence(admission.get("seed_harmful_replace_case_ids")),
            blocks=not comparator,
            tracked=comparator,
        ),
        _failure_class(
            class_id=f"{role_prefix}_seed_false_abstain",
            label=f"{role_prefix} seed ablation false abstain",
            count=int(admission.get("seed_false_abstain_count") or 0),
            artifact=str(admission.get("label") or ""),
            ids=_as_sequence(admission.get("seed_false_abstain_case_ids")),
            tracked=True,
        ),
        _failure_class(
            class_id=f"{role_prefix}_phrase_contract_gap",
            label=f"{role_prefix} phrase contract gap",
            count=len(_as_sequence(admission.get("phrase_gap_family_keys"))),
            artifact=str(admission.get("label") or ""),
            ids=_as_sequence(admission.get("phrase_gap_family_keys")),
            tracked=True,
        ),
    ]
    return rows


def _source_failure_classes(
    source_reports: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in source_reports:
        label = str(source.get("label") or "")
        rows.extend(
            [
                _failure_class(
                    class_id=f"source_missing_active:{label}",
                    label="source active coverage gap",
                    count=len(_as_sequence(source.get("missing_active_family_keys"))),
                    artifact=label,
                    ids=_as_sequence(source.get("missing_active_family_keys")),
                    blocks=False,
                    tracked=True,
                ),
                _failure_class(
                    class_id=f"source_missing_shadow:{label}",
                    label="source shadow coverage gap",
                    count=len(_as_sequence(source.get("missing_shadow_family_keys"))),
                    artifact=label,
                    ids=_as_sequence(source.get("missing_shadow_family_keys")),
                    blocks=False,
                    tracked=True,
                ),
            ]
        )
    return rows


def _margin_failure_classes(margin_sweep: Mapping[str, object]) -> list[dict[str, object]]:
    blockers = _as_mapping(margin_sweep.get("blockers_by_margin"))
    if not blockers:
        return []
    margin_ids: list[str] = []
    for margin, blocker_rows in blockers.items():
        materialized = _as_sequence(blocker_rows)
        if not materialized:
            margin_ids.append(str(margin))
            continue
        for blocker in materialized:
            if not isinstance(blocker, Mapping):
                margin_ids.append(f"{margin}:{blocker}")
                continue
            suite_id = str(blocker.get("suite_id") or "unknown_suite")
            harmful_ids = _as_sequence(blocker.get("harmful_replace_case_ids"))
            false_abstain_ids = _as_sequence(blocker.get("false_abstain_case_ids"))
            for case_id in harmful_ids:
                margin_ids.append(f"{margin}:{suite_id}:harmful:{case_id}")
            for case_id in false_abstain_ids:
                margin_ids.append(f"{margin}:{suite_id}:false_abstain:{case_id}")
            if not harmful_ids and not false_abstain_ids:
                margin_ids.append(f"{margin}:{suite_id}:blocked")
    return [
        _failure_class(
            class_id="margin_policy_blockers",
            label="margin policy blocker",
            count=len(margin_ids),
            artifact="semantic_source_margin_policy_sweep",
            ids=margin_ids,
            tracked=True,
        )
    ]


def _failure_class(
    *,
    class_id: str,
    label: str,
    count: int,
    artifact: str,
    ids: Sequence[object],
    blocks: bool = False,
    tracked: bool = False,
) -> dict[str, object]:
    identifiers = [str(item) for item in ids if str(item or "").strip()]
    return {
        "class_id": class_id,
        "label": label,
        "count": int(count),
        "artifact": artifact,
        "ids": identifiers,
        "family_tokens": sorted({_family_token(identifier) for identifier in identifiers}),
        "blocks_semantic_promotion": bool(blocks),
        "tracked_residual": bool(tracked),
    }


def _build_leverage_summary(
    *,
    primary_admission: Mapping[str, object],
    primary_heldout: Mapping[str, object],
    additional_heldouts: Sequence[Mapping[str, object]],
    source_reports: Sequence[Mapping[str, object]],
    comparator_admissions: Sequence[Mapping[str, object]],
    min_broad_family_count: int,
    min_broad_case_count: int,
    policy_delta_count: int,
) -> dict[str, object]:
    source_row_count = max((int(row.get("row_count") or 0) for row in source_reports), default=0)
    source_family_count = max(
        (int(row.get("source_family_count") or 0) for row in source_reports), default=0
    )
    admitted_rows = int(primary_admission.get("final_admitted_row_count") or 0)
    all_heldouts = (primary_heldout, *additional_heldouts)
    heldout_cases = sum(int(row.get("case_count") or 0) for row in all_heldouts)
    heldout_harmful_count = sum(int(row.get("harmful_replace_count") or 0) for row in all_heldouts)
    heldout_false_abstain_count = sum(
        int(row.get("false_abstain_count") or 0) for row in all_heldouts
    )
    heldout_family_ids = {
        str(family_id)
        for row in all_heldouts
        for family_id in _as_sequence(row.get("family_ids"))
        if str(family_id or "").strip()
    }
    heldout_families = (
        len(heldout_family_ids)
        if heldout_family_ids
        else max((int(row.get("family_count") or 0) for row in all_heldouts), default=0)
    )
    best_comparator = _best_comparator(comparator_admissions)
    false_abstain_delta = 0
    sense_reject_delta = 0
    if best_comparator:
        false_abstain_delta = int(primary_admission.get("seed_false_abstain_count") or 0) - int(
            best_comparator.get("seed_false_abstain_count") or 0
        )
        sense_reject_delta = int(primary_admission.get("sense_rejected_row_count") or 0) - int(
            best_comparator.get("sense_rejected_row_count") or 0
        )
    family_gap = max(int(min_broad_family_count) - heldout_families, 0)
    case_gap = max(int(min_broad_case_count) - heldout_cases, 0)
    overfit_risk = _manual_overfit_risk(
        family_gap=family_gap,
        case_gap=case_gap,
        heldout={
            "harmful_replace_count": heldout_harmful_count,
            "false_abstain_count": heldout_false_abstain_count,
        },
        primary_admission=primary_admission,
        false_abstain_delta=false_abstain_delta,
        sense_reject_delta=sense_reject_delta,
    )
    return {
        "source_row_count": source_row_count,
        "source_family_count": source_family_count,
        "primary_admitted_row_count": admitted_rows,
        "heldout_suite_count": len(all_heldouts),
        "heldout_case_count": heldout_cases,
        "heldout_family_count": heldout_families,
        "heldout_harmful_replace_count": heldout_harmful_count,
        "heldout_false_abstain_count": heldout_false_abstain_count,
        "heldout_cases_per_admitted_row": _safe_ratio(heldout_cases, admitted_rows),
        "source_rows_per_family": _safe_ratio(source_row_count, source_family_count),
        "family_breadth_target": int(min_broad_family_count),
        "case_breadth_target": int(min_broad_case_count),
        "family_breadth_gap": family_gap,
        "case_breadth_gap": case_gap,
        "policy_delta_count": int(policy_delta_count),
        "heldout_cases_per_policy_delta": _safe_ratio(heldout_cases, int(policy_delta_count)),
        "best_comparator_label": str(best_comparator.get("label") or "") if best_comparator else "",
        "best_comparator_false_abstain_delta": false_abstain_delta,
        "best_comparator_sense_reject_delta": sense_reject_delta,
        "manual_overfit_risk": overfit_risk["risk"],
        "manual_overfit_reasons": overfit_risk["reasons"],
        "generalization_signals": overfit_risk["signals"],
    }


def _build_quality_gate_distance(
    *,
    primary_admission: Mapping[str, object],
    primary_heldout: Mapping[str, object],
    additional_heldouts: Sequence[Mapping[str, object]],
    leverage: Mapping[str, object],
) -> dict[str, object]:
    blockers: list[str] = []
    tracked: list[str] = []
    all_heldouts = (primary_heldout, *additional_heldouts)
    if len(_as_sequence(primary_admission.get("semantic_gap_family_keys"))) > 0:
        blockers.append("semantic_contract_gap")
    if any(int(row.get("harmful_replace_count") or 0) > 0 for row in all_heldouts):
        blockers.append("heldout_harmful_replace")
    if int(primary_admission.get("seed_harmful_replace_count") or 0) > 0:
        blockers.append("seed_harmful_replace")
    if any(int(row.get("false_abstain_count") or 0) > 0 for row in all_heldouts):
        tracked.append("heldout_false_abstain")
    if int(primary_admission.get("seed_false_abstain_count") or 0) > 0:
        tracked.append("seed_ablation_false_abstain")
    if int(primary_admission.get("sense_rejected_row_count") or 0) > 0:
        tracked.append("sense_filter_rejects")
    if len(_as_sequence(primary_admission.get("phrase_gap_family_keys"))) > 0:
        tracked.append("phrase_contract_gap")
    if int(leverage.get("family_breadth_gap") or 0) > 0:
        tracked.append("insufficient_family_breadth")
    if int(leverage.get("case_breadth_gap") or 0) > 0:
        tracked.append("insufficient_case_breadth")
    heldout_clean = all(
        str(row.get("status") or "") == "ok"
        and str(row.get("decision") or "") == "heldout_pass"
        and int(row.get("harmful_replace_count") or 0) == 0
        and int(row.get("false_abstain_count") or 0) == 0
        for row in all_heldouts
    )
    if blockers:
        readiness = "blocked"
        distance = "semantic_risk_blockers"
    elif not heldout_clean:
        readiness = "needs_heldout_cleanup"
        distance = "heldout_residuals"
    elif tracked:
        readiness = "ready_for_broader_breadth"
        distance = "breadth_and_residual_tracking"
    else:
        readiness = "ready_for_broader_breadth"
        distance = "breadth_only"
    return {
        "promotion_readiness": readiness,
        "distance": distance,
        "blockers": blockers,
        "tracked_residuals": tracked,
        "heldout_clean": heldout_clean,
    }


def _decision_from_gate_and_leverage(
    *, quality_gate: Mapping[str, object], leverage: Mapping[str, object]
) -> str:
    if _as_sequence(quality_gate.get("blockers")):
        return "fix_blocking_failure_classes"
    if not bool(quality_gate.get("heldout_clean")):
        return "mine_heldout_failure_clusters"
    if str(leverage.get("manual_overfit_risk") or "") in {"medium", "high"}:
        return "seed_pass_expand_inventory"
    return "scale_candidate"


def _next_steps(
    *, decision: str, quality_gate: Mapping[str, object], leverage: Mapping[str, object]
) -> list[str]:
    if decision == "fix_blocking_failure_classes":
        return [
            "resolve blocking semantic-risk classes before claiming source expansion",
            "rerun admission, held-out validation, margin sweep, and this mining harness",
            "only expand breadth after harmful replacements and semantic contract gaps are clean",
        ]
    if decision == "mine_heldout_failure_clusters":
        return [
            "cluster held-out failures by family token, relation type, and source evidence mode",
            "test a no-spend source-mode or margin-policy sweep before adding manual cases",
            "promote only rules that improve multiple cases or families without adding harmful replacements",
        ]
    if decision == "seed_pass_expand_inventory":
        return [
            "build automatic non-v10 inventory candidate generation instead of tuning this small slice further",
            "run WordNet definition-preferred extraction across the expanded inventory and rerun admission",
            "use this mining report to separate reusable failure clusters from one-off manual cases",
            "keep phrase containment as a tracked residual lane until source data or policy exists for it",
        ]
    return [
        "promote the candidate to the next breadth tier",
        "freeze the current evidence manifest and compare future deltas against it",
        "raise broad-family and broad-case thresholds before considering runtime publication",
    ]


def _manual_overfit_risk(
    *,
    family_gap: int,
    case_gap: int,
    heldout: Mapping[str, object],
    primary_admission: Mapping[str, object],
    false_abstain_delta: int,
    sense_reject_delta: int,
) -> dict[str, object]:
    reasons: list[str] = []
    signals: list[str] = []
    risk = "low"
    if family_gap > 0:
        reasons.append("family_inventory_below_broad_threshold")
        risk = "medium"
    if case_gap > 0:
        reasons.append("heldout_cases_below_broad_threshold")
        risk = "medium"
    if int(primary_admission.get("seed_false_abstain_count") or 0) > 0:
        reasons.append("seed_ablation_false_abstains_remain")
    if len(_as_sequence(primary_admission.get("phrase_gap_family_keys"))) > 0:
        reasons.append("phrase_contract_not_yet_sourced")
    if int(heldout.get("harmful_replace_count") or 0) == 0:
        signals.append("no_heldout_harmful_replacements")
    if int(heldout.get("false_abstain_count") or 0) == 0:
        signals.append("no_heldout_false_abstains")
    if false_abstain_delta < 0:
        signals.append("source_mode_reduced_seed_false_abstains")
    if sense_reject_delta < 0:
        signals.append("source_mode_reduced_sense_rejects")
    if not signals and reasons:
        risk = "high"
    return {"risk": risk, "reasons": reasons, "signals": signals}


def main() -> int:
    args = _parse_args()
    comparator_paths = (
        tuple(args.comparator_admission_json)
        if args.comparator_admission_json is not None
        else DEFAULT_COMPARATOR_ADMISSION_JSONS
    )
    source_paths = (
        tuple(args.source_report_json)
        if args.source_report_json is not None
        else DEFAULT_SOURCE_REPORT_JSONS
    )
    primary_admission = _load_json(args.primary_admission_json)
    primary_heldout = _load_json(args.primary_heldout_json)
    additional_heldout_paths = tuple(args.additional_heldout_json or ())
    additional_heldouts = [_load_json(path) for path in additional_heldout_paths]
    primary_sense = _load_optional_json(_sense_sidecar_for(args.primary_admission_json))
    comparator_payloads = [_load_json(path) for path in comparator_paths]
    comparator_senses = [_load_optional_json(_sense_sidecar_for(path)) for path in comparator_paths]
    source_payloads = [_load_json(path) for path in source_paths]
    margin_sweep = _load_optional_json(args.margin_sweep_json)
    report = build_source_failure_class_mining_report(
        primary_admission_payload=primary_admission,
        primary_heldout_payload=primary_heldout,
        comparator_admission_payloads=comparator_payloads,
        source_report_payloads=source_payloads,
        margin_sweep_payload=margin_sweep,
        additional_heldout_payloads=additional_heldouts,
        primary_admission_label=args.primary_admission_json.stem,
        primary_heldout_label=args.primary_heldout_json.stem,
        additional_heldout_labels=[path.stem for path in additional_heldout_paths],
        comparator_admission_labels=[path.stem for path in comparator_paths],
        source_report_labels=[path.stem for path in source_paths],
        primary_sense_payload=primary_sense,
        comparator_sense_payloads=comparator_senses,
        min_broad_family_count=args.min_broad_family_count,
        min_broad_case_count=args.min_broad_case_count,
        policy_delta_count=args.policy_delta_count,
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_source_failure_class_mining_markdown(report), encoding="utf-8"
    )
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
