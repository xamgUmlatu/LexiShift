from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_evidence_gap_generation_admission_en_es import ACTIVE_SLOT
from semantic_veto_product_quality_en_es import _as_mapping


def _next_steps(
    *,
    comparisons: Mapping[str, object],
    issues: Sequence[str],
    admitted_items_by_slot_type: Mapping[str, int] | None = None,
) -> list[str]:
    if issues:
        return [
            "Repair score-contribution inputs before interpreting generated-data lift.",
            "Do not run the full generation pilot until the contribution probe is scoreable.",
        ]
    slot_counts = dict(admitted_items_by_slot_type or {})
    active_only_batch = bool(slot_counts) and set(slot_counts) == {ACTIVE_SLOT}
    synthetic = _as_mapping(comparisons.get("generated_synthetic_shadows"))
    existing = _as_mapping(comparisons.get("generated_existing_shadows"))
    if (
        int(existing.get("false_abstain_delta") or 0) < 0
        or int(synthetic.get("false_abstain_delta") or 0) < 0
    ):
        if active_only_batch:
            return [
                "Treat this as the one-shot active-only PoC follow-through reading.",
                "If the harmful-replace budget is acceptable, package the active-only generated-evidence direction instead of running another veto research loop.",
                "Keep shadow and no-winner generation paused unless a later product decision requires a broader semantic-veto batch.",
            ]
        return [
            "Inspect the family-level deltas and review queued non-active generated rows.",
            "If review does not find role pollution, run the full 72-request pilot.",
        ]
    return [
        "The selected generated evidence did not show immediate score lift on frozen manual cases.",
        "Before full spend, inspect whether thresholds are too conservative or whether generated evidence is not being applied in the right representation.",
    ]
