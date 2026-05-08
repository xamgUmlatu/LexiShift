from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_evidence_gap_control_pilot_plan_en_es import (  # noqa: E402
    build_evidence_gap_control_pilot_plan_report,
    render_evidence_gap_control_pilot_plan_markdown,
)


class SemanticVetoEvidenceGapControlPilotPlanTests(unittest.TestCase):
    def test_selects_top_middle_low_controls_without_outcome_selection(self) -> None:
        report = build_evidence_gap_control_pilot_plan_report(
            heuristic_payload=_heuristic_payload(),
            dataset_payload=_dataset_payload(),
            generated_at="2026-05-08T00:00:00Z",
            arm_size=2,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "evidence_gap_control_pilot_plan_established")
        self.assertEqual(
            report["summary"]["arm_counts"],
            {
                "high_need": 2,
                "low_control": 2,
                "middle_control": 2,
            },
        )
        self.assertTrue(report["e2e_checks"]["no_outcome_fields_used_for_selection"])
        self.assertTrue(report["e2e_checks"]["planned_slot_count_equal_per_family"])

        selected = report["selected_families"]
        high = [row["trigger"] for row in selected if row["pilot_arm"] == "high_need"]
        low = [row["trigger"] for row in selected if row["pilot_arm"] == "low_control"]
        self.assertEqual(high, ["source0", "source1"])
        self.assertEqual(low, ["source5", "source4"])
        self.assertTrue(all(len(row["planned_generation_slots"]) == 3 for row in selected))

        manifest = report["pilot_manifest"]
        self.assertFalse(manifest["selection"]["selection_uses_observed_outcomes"])
        markdown = render_evidence_gap_control_pilot_plan_markdown(report)
        self.assertIn("Evidence-Gap Control Pilot Plan", markdown)


def _heuristic_payload() -> dict[str, object]:
    observations = []
    needs = [0.9, 0.8, 0.55, 0.45, 0.2, 0.1]
    for index, need in enumerate(needs):
        observations.append(
            {
                "family_id": f"family:{index}",
                "scorer_id": "tfidf_cosine",
                "trigger": f"source{index}",
                "target_lemma": f"target{index}",
                "features": {"evidence_gap_risk": need},
                "observed_failure_rate": 0.0 if index < 2 else 1.0,
                "failure_count": 0 if index < 2 else 1,
                "case_count": 1,
            }
        )
    return {
        "pair": "en-es",
        "decision": "translation_ambiguity_heuristic_bakeoff_established",
        "comparison_rows": [
            {
                "scorer_id": "tfidf_cosine",
                "formula_id": "evidence_gap_only",
                "weights": {"evidence_gap_risk": 1.0},
            }
        ],
        "observations": observations,
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "fixture",
        "manual_review_state": "approved_by_user",
        "families": [_family(index) for index in range(6)],
    }


def _family(index: int) -> dict[str, object]:
    return {
        "family_id": f"family:{index}",
        "trigger": f"source{index}",
        "active": {
            "sense_id": f"family:{index}:active",
            "target_lemma": f"target{index}",
            "canonical_pos": "noun",
            "evidence_views": {"all_evidence_text": f"source{index} active evidence"},
        },
        "shadows": [
            {
                "sense_id": f"family:{index}:shadow",
                "target_lemma": f"shadow{index}",
                "canonical_pos": "noun",
                "evidence_views": {"all_evidence_text": f"source{index} shadow evidence"},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
