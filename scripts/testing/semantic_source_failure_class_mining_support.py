#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _heldout_family_ids(payload: Mapping[str, object]) -> list[str]:
    rows = _as_sequence(payload.get("heldout_families"))
    family_ids = [
        str(row.get("family_id") or "").strip()
        for row in rows
        if isinstance(row, Mapping) and str(row.get("family_id") or "").strip()
    ]
    return sorted(set(family_ids))


def _sense_sidecar_for(admission_path: Path) -> Path:
    prefix = admission_path.with_suffix("")
    return prefix.parent / f"{prefix.name}_sense.json"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _best_comparator(comparator_admissions: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    if not comparator_admissions:
        return {}
    return min(
        comparator_admissions,
        key=lambda row: (
            int(row.get("sense_rejected_row_count") or 0),
            int(row.get("seed_harmful_replace_count") or 0),
            int(row.get("seed_false_abstain_count") or 0),
        ),
    )


def _label_at(labels: Sequence[str], index: int, default: str) -> str:
    if index < len(labels) and str(labels[index] or "").strip():
        return str(labels[index]).strip()
    return default


def _item_at(
    values: Sequence[Mapping[str, object] | None], index: int
) -> Mapping[str, object] | None:
    if index < len(values):
        return values[index]
    return None


def _family_token(identifier: str) -> str:
    parts = [part for part in str(identifier or "").split(":") if part]
    if not parts:
        return "unknown"
    if parts[-1].isdigit() and len(parts) >= 2:
        return parts[-2]
    if len(parts) >= 3 and parts[0] == "en-es":
        return parts[-2]
    return parts[-1]


def _reason_count_ids(reason_counts: Mapping[str, object]) -> list[str]:
    ids: list[str] = []
    for reason, count in reason_counts.items():
        ids.append(f"{reason}:{int(count or 0)}")
    return ids


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
