from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_active_only_inventory_replay_en_es import (  # noqa: E402
    build_active_only_inventory_replay_bundle,
    render_active_only_inventory_replay_markdown,
)


class SemanticVetoActiveOnlyInventoryReplayTests(unittest.TestCase):
    def test_appends_packaged_anchor_cues_to_inventory_active_sense(self) -> None:
        bundle = build_active_only_inventory_replay_bundle(
            dataset_payload=_dataset_payload(),
            normalized_evidence_payload=_normalized_evidence_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )

        report = bundle["report"]
        inventory = bundle["candidate_inventory"]
        active = inventory["senses"]["family:bank:active"]

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["family_count"], 1)
        self.assertEqual(report["summary"]["case_count"], 2)
        self.assertEqual(report["summary"]["packaged_row_count"], 1)
        self.assertEqual(report["summary"]["applied_row_count"], 1)
        self.assertIn(
            "The teller approved the loan",
            active["evidence_views"]["all_evidence_text"],
        )

        markdown = render_active_only_inventory_replay_markdown(report)
        self.assertIn("Inventory Replay", markdown)
        self.assertIn("active_only_inventory_replay_tfidf_v1", markdown)


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "families": [
            {
                "family_id": "family:bank",
                "trigger": "bank",
                "active": {
                    "sense_id": "family:bank:active",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "bank -> banco",
                        "all_evidence_text": "bank -> banco | financial institution",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "family:bank:shadow:1",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "bank -> orilla",
                            "all_evidence_text": "bank -> orilla | river shore",
                        },
                    }
                ],
                "cases": [
                    {
                        "case_id": "case:bank:1",
                        "sentence": "The bank approved the loan.",
                        "gold_decision": "replace",
                        "gold_winner": "family:bank:active",
                    },
                    {
                        "case_id": "case:bank:2",
                        "sentence": "The river bank was muddy.",
                        "gold_decision": "abstain",
                        "gold_winner": "family:bank:shadow:1",
                    },
                ],
            }
        ],
    }


def _normalized_evidence_payload() -> dict[str, object]:
    return {
        "rows": [
            {
                "evidence_id": "evidence:bank:1",
                "relation_type": "anchor_cue",
                "trigger": "bank",
                "active_target": "banco",
                "evidence_text": "The teller approved the loan at the bank.",
                "metadata": {
                    "family_id": "family:bank",
                },
            }
        ]
    }


if __name__ == "__main__":
    unittest.main()
