#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping


def limitations_for_margin_recommendation(recommendation: Mapping[str, object]) -> list[str]:
    recommended = recommendation.get("recommended_min_margin")
    margin_limitation = (
        "margin_candidate_requires_non_v10_stress_before_runtime_default"
        if recommended is not None
        else "no_scalar_margin_policy_passed_current_suites"
    )
    return [
        "bounded_current_suite_not_full_en_es_proof",
        margin_limitation,
        "does_not_replace_phrase_source_or_pattern_provenance",
    ]
