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

from semantic_veto_heuristic_group_case_authoring_en_es import (  # noqa: E402
    build_heuristic_group_case_authoring_report,
    render_case_authoring_markdown,
)


class SemanticVetoHeuristicGroupCaseAuthoringTests(unittest.TestCase):
    def test_case_authoring_materializes_dataset_and_keeps_low_poly_contract(self) -> None:
        report, dataset = build_heuristic_group_case_authoring_report(
            pilot_payload={
                "pilot_id": "semantic_veto_heuristic_group_pilot_en_es_v1",
                "input_fingerprint": "abc123",
                "manual_review_packet": [
                    {
                        "group_id": "core_high_polysemy",
                        "trigger": "man",
                        "source_rank": 95,
                        "source_rank_bin": "1-500",
                        "wordnet_sense_count": 12,
                        "wordnet_pos_count": 2,
                    },
                    {
                        "group_id": "core_low_polysemy_control",
                        "trigger": "yes",
                        "source_rank": 175,
                        "source_rank_bin": "1-500",
                        "wordnet_sense_count": 1,
                        "wordnet_pos_count": 1,
                    },
                ],
            },
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "heuristic_group_case_authoring_dataset_ready_for_scoring",
        )
        self.assertEqual(dataset["dataset_id"], "en_es_heuristic_group_pilot_v1")
        self.assertEqual(len(dataset["families"]), 2)
        self.assertEqual(report["summary"]["dataset_case_count"], 8)
        self.assertEqual(report["summary"]["shadow_contract_counts"]["full"], 1)
        self.assertEqual(report["summary"]["shadow_contract_counts"]["not_applicable"], 1)

        by_trigger = {family["trigger"]: family for family in dataset["families"]}
        self.assertEqual(len(by_trigger["man"]["shadows"]), 2)
        self.assertEqual(len(by_trigger["yes"]["shadows"]), 0)
        yes_case_types = {
            case["slice_dimensions"]["manual_case_type"][0] for case in by_trigger["yes"]["cases"]
        }
        self.assertEqual(yes_case_types, {"positive_active", "phrase_no_winner"})

        markdown = render_case_authoring_markdown(report)
        self.assertIn("Low-polysemy controls", markdown)
        self.assertIn("core_high_polysemy", markdown)

    def test_case_authoring_flags_unimplemented_frozen_triggers(self) -> None:
        report, dataset = build_heuristic_group_case_authoring_report(
            pilot_payload={
                "manual_review_packet": [
                    {
                        "group_id": "future_group",
                        "trigger": "futuretrigger",
                        "source_rank_bin": "missing",
                        "wordnet_sense_count": 1,
                    }
                ]
            },
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(dataset["families"], [])
        self.assertEqual(report["summary"]["missing_authoring_specs"], ["futuretrigger"])


if __name__ == "__main__":
    unittest.main()
