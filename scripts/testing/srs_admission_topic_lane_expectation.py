#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.profile_bootstrap import DEFAULT_PROFILE_BOOTSTRAP_POLICY  # noqa: E402


def with_topic_lane_expectations(
    topic_lane_rows: Sequence[Mapping[str, Any]],
    topic_lane_window_preview: Mapping[str, Any],
) -> list[dict[str, Any]]:
    window_scenarios = {
        str(scenario.get("name") or ""): scenario
        for scenario in topic_lane_window_preview.get("scenarios", ())
        if isinstance(scenario, Mapping)
    }
    return [
        _with_topic_lane_expectation(row, window_scenarios.get(str(row.get("name") or "")))
        for row in topic_lane_rows
    ]


def _with_topic_lane_expectation(
    row: Mapping[str, Any],
    window_scenario: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result = dict(row)
    expectation = _topic_lane_policy_expectation(row, window_scenario)
    result["topic_lane_policy_expectation"] = expectation
    result["expected_topic_count"] = expectation["expected_topic_count"]
    result["expected_topic_share"] = expectation["expected_topic_share"]
    result["topic_lane_expectation_status"] = expectation["status"]
    return result


def _topic_lane_policy_expectation(
    row: Mapping[str, Any],
    window_scenario: Mapping[str, Any] | None,
) -> dict[str, Any]:
    active_topics = [str(topic) for topic in row.get("active_topics", ()) if str(topic).strip()]
    selected_count = int(row.get("selected_count") or 0)
    selected_topic_count = int(row.get("selected_topic_count") or 0)
    window_words = _window_words(window_scenario)
    preferred_window_words = [word for word in window_words if _is_topic_mover(word, active_topics)]
    total_candidates = _topic_support_total_candidates(window_scenario)
    full_topic_candidates = _topic_support_candidate_count(window_scenario, active_topics)
    full_general_candidates = max(0, total_candidates - full_topic_candidates)
    max_topic_strength = max(
        (_safe_float(word.get("topic_affinity")) for word in preferred_window_words),
        default=0.0,
    )
    lane_max_share = DEFAULT_PROFILE_BOOTSTRAP_POLICY.selector_config.topic_lane_max_share
    topic_budget = _topic_lane_budget(
        selected_count=selected_count,
        max_topic_strength=max_topic_strength,
        topic_lane_max_share=lane_max_share,
    )
    window_topic_candidates = len(preferred_window_words)
    first_pass_topic_count = min(topic_budget, window_topic_candidates, selected_count)
    general_fill_count = min(
        max(0, selected_count - first_pass_topic_count),
        full_general_candidates,
    )
    fallback_topic_count = min(
        max(0, selected_count - first_pass_topic_count - general_fill_count),
        max(0, full_topic_candidates - first_pass_topic_count),
    )
    expected_topic_count = first_pass_topic_count + fallback_topic_count
    status = _expectation_status(
        selected_topic_count=selected_topic_count,
        expected_topic_count=expected_topic_count,
    )
    return {
        "status": status,
        "selected_topic_count": selected_topic_count,
        "expected_topic_count": expected_topic_count,
        "expected_topic_share": _ratio(expected_topic_count, selected_count),
        "selected_count": selected_count,
        "topic_budget": topic_budget,
        "topic_lane_max_share": _rounded(lane_max_share),
        "max_topic_strength_in_window": _rounded(max_topic_strength),
        "window_size": len(window_words),
        "window_topic_candidates": window_topic_candidates,
        "window_general_candidates": max(0, len(window_words) - window_topic_candidates),
        "full_topic_candidates": full_topic_candidates,
        "full_general_candidates": full_general_candidates,
        "full_candidate_count": total_candidates,
        "source_limited": 0 < topic_budget and window_topic_candidates < topic_budget,
        "general_limited": full_general_candidates
        < max(0, selected_count - first_pass_topic_count),
    }


def _window_words(window_scenario: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(window_scenario, Mapping):
        return []
    return [
        dict(word)
        for word in window_scenario.get("admitted_words", ())
        if isinstance(word, Mapping)
    ]


def _expectation_status(*, selected_topic_count: int, expected_topic_count: int) -> str:
    if selected_topic_count < expected_topic_count:
        return "below_expected"
    if selected_topic_count > expected_topic_count:
        return "above_expected_topic_fill"
    return "matches"


def _topic_support_total_candidates(window_scenario: Mapping[str, Any] | None) -> int:
    if not isinstance(window_scenario, Mapping):
        return 0
    support = window_scenario.get("active_topic_support")
    if not isinstance(support, Mapping):
        return 0
    return max(0, int(support.get("total_candidates") or 0))


def _topic_support_candidate_count(
    window_scenario: Mapping[str, Any] | None,
    active_topics: Sequence[str],
) -> int:
    if not isinstance(window_scenario, Mapping) or not active_topics:
        return 0
    support = window_scenario.get("active_topic_support")
    if not isinstance(support, Mapping):
        return 0
    active_set = {str(topic).strip() for topic in active_topics if str(topic).strip()}
    total_candidates = _topic_support_total_candidates(window_scenario)
    topic_count = 0
    for entry in support.get("topics", ()):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("topic") or "").strip() not in active_set:
            continue
        topic_count += max(0, int(entry.get("candidate_count") or 0))
    return min(total_candidates, topic_count)


def _topic_lane_budget(
    *,
    selected_count: int,
    max_topic_strength: float,
    topic_lane_max_share: float,
) -> int:
    if selected_count <= 0 or max_topic_strength <= 0.0:
        return 0
    return min(
        selected_count,
        int(
            math.ceil(
                selected_count
                * max(0.0, min(1.0, max_topic_strength))
                * max(0.0, min(1.0, topic_lane_max_share))
            )
        ),
    )


def _is_topic_mover(row: Mapping[str, Any], active_topics: Sequence[str]) -> bool:
    if not active_topics:
        return False
    source = str(row.get("topic_affinity_source") or "")
    if not source:
        return False
    return any(topic in source for topic in active_topics)


def _ratio(numerator: int, denominator: int) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed == parsed else 0.0


def _rounded(value: object) -> float:
    return round(_safe_float(value), 6)
