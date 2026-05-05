from __future__ import annotations

from typing import Mapping, Sequence

from semantic_veto_product_quality_en_es import _as_mapping


def limitations() -> list[str]:
    return [
        "llm_pilot_is_not_representative_browsing",
        "source_evidence_is_independent_but_still_silver_llm_reviewed_fixture",
        "candidate_thresholds_are_frozen_not_tuned_on_locked_eval",
        "scoring_does_not_promote_runtime_policy_or_source_evidence",
    ]


def next_steps(
    *,
    status: str,
    metrics: Mapping[str, object],
    unscored_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    if unscored_rows:
        return [
            "Fill independent active, shadow, and phrase source evidence for unscored families before claiming pilot accuracy.",
            "Rerun this scoring harness after source coverage is complete.",
        ]
    target_status = str(_as_mapping(metrics.get("target_checks")).get("target_status") or "")
    if status == "ok" and target_status == "pass":
        return [
            "Inspect failure rows by split and gold type before expanding the LLM pilot.",
            "Run a larger locked eval lane with the same source/evaluation separation.",
            "Keep thresholds frozen until discovery-only diagnostics justify a separate candidate.",
        ]
    return [
        "Use failure rows to decide whether the next improvement is source evidence, scoring shape, or threshold policy.",
        "Do not tune on locked_eval rows; tune only on discovery if a candidate change is proposed.",
    ]
