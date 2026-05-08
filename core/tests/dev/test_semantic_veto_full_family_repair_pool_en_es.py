from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_repair_pool_en_es import (  # noqa: E402
    build_full_family_repair_pool_report,
    render_full_family_repair_pool_markdown,
)


class SemanticVetoFullFamilyRepairPoolTests(unittest.TestCase):
    def test_materializes_every_repair_pool_family_as_user_approved_rows(self) -> None:
        report, dataset = build_full_family_repair_pool_report(
            agent_review_payload=_agent_review(),
            repair_specs=[
                {
                    "source": "change",
                    "target": "cambio",
                    "pos": "noun",
                    "positive": ("The policy change surprised everyone.",),
                    "shadows": (
                        ("monedas", "coins or small money", "The cashier gave me change."),
                    ),
                    "no_winner": "The dashboard listed Change as an internal project code.",
                }
            ],
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "full_family_repair_pool_user_approved_for_exploratory_sweeps",
        )
        self.assertEqual(report["summary"]["repaired_family_count"], 1)
        self.assertEqual(report["summary"]["excluded_family_count"], 1)
        self.assertEqual(report["summary"]["trusted_case_count"], 3)
        self.assertEqual(
            report["summary"]["case_type_counts"],
            {"phrase_no_winner": 1, "positive_active": 1, "shadow_negative": 1},
        )
        self.assertTrue(all(report["e2e_checks"].values()))
        self.assertEqual(dataset["manual_review_state"], "approved_by_user")
        self.assertTrue(dataset["provenance"]["trusted_now"])
        self.assertEqual(len(dataset["families"]), 1)
        self.assertEqual(len(dataset["excluded_families"]), 1)
        for family in dataset["families"]:
            for case in family["cases"]:
                self.assertEqual(case["human_review_status"], "approved_by_user")
                self.assertEqual(case["row_quality_status"], "trusted")
                self.assertEqual(
                    case["approval_id"], "user_approved_full_repaired_dataset_2026_05_08"
                )

        markdown = render_full_family_repair_pool_markdown(report)
        self.assertIn("Full-Family Repair Pool", markdown)
        self.assertIn("change", markdown)

    def test_fails_if_a_repair_pool_family_is_not_specified(self) -> None:
        report, _dataset = build_full_family_repair_pool_report(
            agent_review_payload=_agent_review(),
            repair_specs=[],
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("missing_repair_spec:change->cambio", report["issues"])
        self.assertFalse(report["e2e_checks"]["all_expected_repair_families_materialized"])


def _agent_review() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "full_family_agent_review_complete_user_approval_required",
        "review_authority": "unit_test",
        "family_reviews": [
            {
                "family_id": "fam:change:cambio",
                "trigger": "change",
                "target_lemma": "cambio",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "target_zipf_band_es": "zipf_4_to_5_common",
                "polysemy_band": "high_10_plus",
                "pos_shape": "same_pos_polysemy",
                "active_sense_status": "aligned",
                "family_disposition": "aligned_mapping_rewrite_contexts",
                "scoring_action": "repair_pool",
                "corrected_active_gloss": "an act or result of becoming different",
            },
            {
                "family_id": "fam:bad:deducción",
                "trigger": "bad",
                "target_lemma": "deducción",
                "source_zipf_band_en": "zipf_4_to_5_common",
                "target_zipf_band_es": "zipf_4_to_5_common",
                "polysemy_band": "low_1_to_3",
                "pos_shape": "single_sense",
                "active_sense_status": "source_target_mapping_rejected",
                "family_disposition": "source_target_mapping_rejected",
                "scoring_action": "exclude_from_trusted_eval",
                "notes": "unit rejected mapping",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
