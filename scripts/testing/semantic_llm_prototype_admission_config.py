#!/usr/bin/env python3
from __future__ import annotations

DEFAULT_PHRASE_PROTOTYPE_MARGIN = 0.0
ACTIVE_MODIFIER_RESCUE_MARGIN_FLOOR = -0.05
STRONG_ACTIVE_PHRASE_PREEMPTION_MARGIN_FLOOR = 0.10
PROTOTYPE_CONFIGS: tuple[tuple[str, str, str, bool, bool, bool], ...] = (
    (
        "prototype_reviewed_examples_family_guard",
        "Prototype reviewed examples, family phrase guard",
        "family_all",
        False,
        False,
        False,
    ),
    (
        "prototype_reviewed_examples_active_guard",
        "Prototype reviewed examples, active phrase guard",
        "active_only",
        False,
        False,
        False,
    ),
    (
        "prototype_reviewed_examples_phrase_containment_guard",
        "Prototype reviewed examples, phrase-control containment guard",
        "active_only",
        False,
        True,
        False,
    ),
    (
        "prototype_reviewed_examples_surface_pos_rescue_guard",
        "Prototype reviewed examples, surface-POS rescue guard",
        "active_only",
        False,
        True,
        True,
    ),
    (
        "prototype_reviewed_examples_phrase_prototype_guard",
        "Prototype reviewed examples, phrase-control prototype guard",
        "active_only",
        True,
        False,
        False,
    ),
    (
        "prototype_reviewed_examples_phrase_prototype_surface_pos_guard",
        "Prototype reviewed examples, phrase-control prototype plus surface-POS guard",
        "active_only",
        True,
        False,
        True,
    ),
)


def phrase_preemption_should_apply(
    *,
    phrase_preemption_hit: bool,
    decision_before_phrase_preemption: str,
    active_score: float,
    strongest_shadow_score: float,
    phrase_control_score: float,
    phrase_prototype_margin: float,
    strong_active_margin_floor: float = STRONG_ACTIVE_PHRASE_PREEMPTION_MARGIN_FLOOR,
) -> bool:
    if not phrase_preemption_hit:
        return False
    if str(decision_before_phrase_preemption or "").strip() != "replace":
        return True
    active_margin = float(active_score) - float(strongest_shadow_score)
    phrase_lead = float(phrase_control_score) - max(
        float(active_score),
        float(strongest_shadow_score),
    )
    if active_margin >= float(strong_active_margin_floor) and phrase_lead < float(
        phrase_prototype_margin
    ):
        return False
    return True
