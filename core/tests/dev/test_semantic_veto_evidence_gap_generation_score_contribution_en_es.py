from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_evidence_gap_generation_score_contribution_en_es import (  # noqa: E402
    build_evidence_gap_score_contribution_report,
    render_evidence_gap_score_contribution_markdown,
)


class SemanticVetoEvidenceGapGenerationScoreContributionTests(unittest.TestCase):
    def test_scores_generated_evidence_without_using_no_winner_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_evidence_gap_score_contribution_report(
                dataset_payload=_dataset_payload(),
                admission_payload=_admission_payload(),
                augmented_dir=Path(tmp),
                generated_at="2026-05-09T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["selected_family_count"], 1)
        self.assertEqual(report["summary"]["admitted_item_count"], 3)
        self.assertEqual(
            report["application_summary"]["generated_existing_shadows"]["active_items_applied"],
            1,
        )
        self.assertEqual(
            report["application_summary"]["generated_existing_shadows"]["new_shadow_items_ignored"],
            1,
        )
        self.assertEqual(
            report["application_summary"]["generated_synthetic_shadows"][
                "synthetic_shadow_items_applied"
            ],
            1,
        )
        self.assertEqual(
            report["application_summary"]["generated_synthetic_shadows"]["no_winner_items_ignored"],
            1,
        )
        self.assertGreater(report["summary"]["policy_sweep_row_count"], 0)
        self.assertEqual(report["methodology"]["min_active_score"], 0.05)
        self.assertEqual(report["methodology"]["min_margin"], 0.0)
        self.assertIn("0", report["best_by_harmful_budget"])
        self.assertEqual(
            {
                row["active_rescue_mode"]
                for row in report["policy_sweep_rows"]
                if row["application_mode"] == "generated_active_only"
            },
            {"off", "sense_label_near_tie_active_rescue"},
        )
        self.assertEqual(
            {
                row["phrase_control_mode"]
                for row in report["policy_sweep_rows"]
                if row["application_mode"] == "generated_active_only"
            },
            {"off", "noun_family_frame_guard"},
        )

        markdown = render_evidence_gap_score_contribution_markdown(report)
        self.assertIn("Score Contribution", markdown)
        self.assertIn("generated_synthetic_shadows", markdown)
        self.assertIn("Policy Sweep Best By Harmful Budget", markdown)

    def test_custom_decision_thresholds_and_skip_policy_sweep_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_evidence_gap_score_contribution_report(
                dataset_payload=_dataset_payload(),
                admission_payload=_admission_payload(),
                augmented_dir=Path(tmp),
                min_active_score=0.0,
                min_margin=0.015,
                include_policy_sweep=False,
                generated_at="2026-05-09T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["methodology"]["min_active_score"], 0.0)
        self.assertEqual(report["methodology"]["min_margin"], 0.015)
        self.assertFalse(report["methodology"]["include_policy_sweep"])
        self.assertEqual(report["summary"]["policy_sweep_row_count"], 0)
        self.assertEqual(report["policy_sweep_rows"], [])
        self.assertEqual(report["best_by_harmful_budget"], {})

    def test_missing_admitted_items_is_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_evidence_gap_score_contribution_report(
                dataset_payload=_dataset_payload(),
                admission_payload={"admitted_items": []},
                augmented_dir=Path(tmp),
                generated_at="2026-05-09T00:00:00Z",
            )

        self.assertEqual(report["status"], "review")
        self.assertIn("no_admitted_items_to_score", report["summary"]["issues"])


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "dataset_id": "tiny",
        "pair": "en-es",
        "families": [
            {
                "family_id": "family:bank:banco",
                "trigger": "bank",
                "active": {
                    "sense_id": "family:bank:banco:active",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "bank -> banco | financial institution",
                        "sense_label": "bank -> banco",
                    },
                },
                "shadows": [],
                "cases": [
                    {
                        "case_id": "case:active",
                        "sentence": "The bank approved the loan.",
                        "source_phrase": "bank",
                        "gold_decision": "replace",
                        "gold_winner": "family:bank:banco:active",
                    },
                    {
                        "case_id": "case:none",
                        "sentence": "The page title said Bank Tools.",
                        "source_phrase": "bank",
                        "gold_decision": "abstain",
                        "gold_winner": "none",
                    },
                ],
            }
        ],
    }


def _admission_payload() -> dict[str, object]:
    return {
        "summary": {"coverage_waived_item_count": 0},
        "admitted_items": [
            {
                "item_id": "item:active",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "slot_type": "active_evidence_expansion",
                "source_phrase": "bank",
                "target_lemma": "banco",
                "sentence": "The bank reviewed the mortgage.",
                "evidence_note": "Financial institution sense.",
            },
            {
                "item_id": "item:shadow",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "source_phrase": "bank",
                "proposed_competitor_target_lemma": "orilla",
                "sentence": "The river bank eroded.",
                "evidence_note": "Land beside water sense.",
            },
            {
                "item_id": "item:no-winner",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "slot_type": "no_winner_context_probe",
                "source_phrase": "bank",
                "sentence": "Search results for bank",
                "no_winner_reason": "Literal search query.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
