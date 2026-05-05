from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_llm_threshold_bakeoff_en_es import (  # noqa: E402
    build_threshold_bakeoff_report,
    render_threshold_bakeoff_markdown,
)


class SemanticVetoLlmThresholdBakeoffTests(unittest.TestCase):
    def test_discovery_selection_is_checked_against_locked_and_stress_lanes(self) -> None:
        report = build_threshold_bakeoff_report(
            policy_payload=_policy(),
            llm_scoring_payload=_llm_scoring_payload(),
            validation_sources=[{"report_id": "stress_fixture", "report": _stress_report()}],
            shadow_lead_grid=[-0.05, 0.05],
            phrase_lead_grid=[0.0, 0.05, 0.075],
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "separate_threshold_discovery_candidate_found",
        )
        self.assertEqual(report["e2e_checks"]["llm_discovery_rows_read"], 8)
        self.assertEqual(report["e2e_checks"]["llm_locked_eval_rows_read"], 2)
        self.assertEqual(report["e2e_checks"]["manual_stress_rows_read"], 6)

        selected = report["summary"]["selected_discovery_candidate"]
        self.assertEqual(selected["shadow_lead_min"], -0.05)
        self.assertEqual(selected["llm_discovery"]["target_status"], "pass")
        self.assertEqual(selected["manual_stress_all"]["target_status"], "fail")

        self.assertIsNone(report["summary"]["best_all_lane_advisory"])

        recommendation = "\n".join(report["summary"]["recommendation"])
        self.assertIn("overblocks manual/stress positives", recommendation)

        markdown = render_threshold_bakeoff_markdown(report)
        self.assertIn("LLM Threshold Bakeoff", markdown)
        self.assertIn("Selection lane", markdown)


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "test_policy",
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _llm_scoring_payload() -> dict[str, object]:
    return {
        "case_results": [
            _case("llm_disc_pos_1", "discovery", "replace", 0.70, 0.64, 0.60),
            _case("llm_disc_pos_2", "discovery", "replace", 0.70, 0.64, 0.60),
            _case("llm_disc_pos_3", "discovery", "replace", 0.70, 0.64, 0.60),
            _case("llm_disc_pos_4", "discovery", "replace", 0.70, 0.64, 0.60),
            _case("llm_disc_pos_5", "discovery", "replace", 0.70, 0.64, 0.60),
            _case("llm_disc_neg_1", "discovery", "abstain", 0.70, 0.66, 0.60),
            _case("llm_disc_neg_2", "discovery", "abstain", 0.70, 0.66, 0.60),
            _case("llm_disc_neg_3", "discovery", "abstain", 0.55, 0.70, 0.50),
            _case("llm_lock_pos", "locked_eval", "replace", 0.70, 0.64, 0.60),
            _case("llm_lock_neg", "locked_eval", "abstain", 0.70, 0.66, 0.60),
        ]
    }


def _stress_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "fixture",
        "configured_case_results": [
            _case("stress_pos_1", "", "replace", 0.70, 0.66, 0.60),
            _case("stress_pos_2", "", "replace", 0.70, 0.66, 0.60),
            _case("stress_pos_3", "", "replace", 0.70, 0.66, 0.60),
            _case("stress_pos_4", "", "replace", 0.70, 0.66, 0.60),
            _case("stress_pos_5", "", "replace", 0.70, 0.66, 0.60),
            _case("stress_neg", "", "abstain", 0.55, 0.70, 0.50),
        ],
    }


def _case(
    case_id: str,
    split: str,
    gold_decision: str,
    active: float,
    shadow: float,
    phrase: float,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "split": split,
        "gold_decision": gold_decision,
        "active_score": active,
        "strongest_shadow_score": shadow,
        "phrase_control_score": phrase,
        "phrase_preemption_hit": False,
    }


if __name__ == "__main__":
    unittest.main()
