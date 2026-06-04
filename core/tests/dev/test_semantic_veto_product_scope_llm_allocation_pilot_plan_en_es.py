from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_product_scope_llm_allocation_pilot_plan_en_es import (  # noqa: E402
    build_product_scope_llm_allocation_pilot_plan_report,
    render_product_scope_llm_allocation_pilot_plan_markdown,
)


class SemanticVetoProductScopeLlmAllocationPilotPlanTests(unittest.TestCase):
    def test_selects_seeded_high_middle_low_bands_without_outcomes(self) -> None:
        report = build_product_scope_llm_allocation_pilot_plan_report(
            band_formula_payload=_band_formula_payload(),
            dataset_payload=_dataset_payload(),
            generated_at="2026-05-09T00:00:00Z",
            selection_seed="fixture-seed",
            high_size=2,
            middle_size=2,
            low_size=2,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "product_scope_llm_allocation_pilot_plan_established")
        self.assertEqual(
            report["summary"]["arm_counts"],
            {
                "high_need": 2,
                "low_control": 2,
                "middle_control": 2,
            },
        )
        self.assertTrue(report["e2e_checks"]["no_outcome_fields_used_for_selection"])
        self.assertTrue(
            report["e2e_checks"]["generation_contract_compatible_with_existing_request_renderer"]
        )
        self.assertTrue(
            all(len(row["planned_generation_slots"]) == 3 for row in report["selected_families"])
        )

        high = [row for row in report["selected_families"] if row["pilot_arm"] == "high_need"]
        middle = [
            row for row in report["selected_families"] if row["pilot_arm"] == "middle_control"
        ]
        low = [row for row in report["selected_families"] if row["pilot_arm"] == "low_control"]
        self.assertTrue(all(row["predicted_need"] == 0.85 for row in high))
        self.assertTrue(all(row["predicted_need"] == 0.65 for row in middle))
        self.assertTrue(all(row["predicted_need"] == 0.3 for row in low))

        manifest = report["pilot_manifest"]
        self.assertFalse(manifest["selection"]["selection_uses_observed_outcomes"])
        self.assertEqual(
            tuple(manifest["generation_contract"]["slot_types"]),
            (
                "active_evidence_expansion",
                "shadow_or_competitor_evidence_probe",
                "no_winner_context_probe",
            ),
        )
        markdown = render_product_scope_llm_allocation_pilot_plan_markdown(report)
        self.assertIn("Product-Scope LLM Allocation Pilot Plan", markdown)


def _band_formula_payload() -> dict[str, object]:
    observations = []
    rows = [
        ("high0", 0.85, 2),
        ("high1", 0.85, 2),
        ("high2", 0.85, 2),
        ("mid0", 0.65, 1),
        ("mid1", 0.65, 1),
        ("mid2", 0.65, 1),
        ("low0", 0.3, 0),
        ("low1", 0.3, 0),
        ("low2", 0.3, 0),
    ]
    for index, (name, need, shadow_count) in enumerate(rows):
        observations.append(
            {
                "family_id": f"family:{name}",
                "scorer_id": "best_product_rank_sentence_transformer_a0000_mneg0025",
                "trigger": name,
                "target_lemma": f"target-{name}",
                "features": {"shadow_coverage_risk": need},
                "feature_context": {"shadow_count": shadow_count},
                "observed_failure_rate": 1.0 if index == 0 else 0.0,
                "failure_count": 3 if index == 0 else 0,
                "harmful_replace_count": 2 if index == 0 else 0,
                "false_abstain_count": 1 if index == 0 else 0,
                "case_count": 3,
            }
        )
    return {
        "pair": "en-es",
        "decision": "repaired_full_band_formula_sweep_established",
        "comparison_rows": [
            {
                "scorer_id": "best_product_rank_sentence_transformer_a0000_mneg0025",
                "formula_id": "shadow_coverage_only",
                "weights": {"shadow_coverage_risk": 1.0},
            }
        ],
        "observations": observations,
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "fixture_product_scope",
        "manual_review_state": "approved_by_user",
        "families": [
            _family(name)
            for name in (
                "high0",
                "high1",
                "high2",
                "mid0",
                "mid1",
                "mid2",
                "low0",
                "low1",
                "low2",
            )
        ],
    }


def _family(name: str) -> dict[str, object]:
    return {
        "family_id": f"family:{name}",
        "trigger": name,
        "active": {
            "sense_id": f"family:{name}:active",
            "target_lemma": f"target-{name}",
            "canonical_pos": "noun",
            "evidence_views": {"all_evidence_text": f"{name} active evidence"},
        },
        "shadows": [
            {
                "sense_id": f"family:{name}:shadow",
                "target_lemma": f"shadow-{name}",
                "canonical_pos": "noun",
                "evidence_views": {"all_evidence_text": f"{name} shadow evidence"},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
