from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_active_only_full_pack_builder_en_es import (  # noqa: E402
    build_active_only_full_pack_report,
)


class SemanticVetoActiveOnlyFullPackBuilderTests(unittest.TestCase):
    def test_adds_new_active_only_families_without_dropping_existing_shadows(self) -> None:
        report = build_active_only_full_pack_report(
            base_inventory_payload=_base_inventory(),
            base_normalized_payload=_base_normalized_evidence(),
            add_normalized_payloads=[_add_normalized_evidence()],
            pack_id="test-pack",
            generated_at="2026-05-12T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        summary = report["summary"]
        self.assertEqual(summary["base_normalized_row_count"], 1)
        self.assertEqual(summary["add_normalized_row_count"], 2)
        self.assertEqual(summary["combined_normalized_row_count"], 3)
        self.assertEqual(summary["new_family_count"], 1)
        self.assertEqual(summary["existing_family_append_count"], 1)
        self.assertEqual(summary["competition_set_count"], 2)

        inventory = report["semantic_inventory"]
        competition_sets = inventory["competition_sets"]
        self.assertEqual(
            competition_sets["family:bank:competition"]["shadow_sense_ids"],
            ["family:bank:shadow:1"],
        )
        self.assertEqual(
            competition_sets["family:away:competition:active-only-pack"]["shadow_sense_ids"],
            [],
        )
        bank_evidence = inventory["senses"]["family:bank:active"]["evidence_views"][
            "all_evidence_text"
        ]
        self.assertIn("The bank approved the loan.", bank_evidence)
        away_evidence = inventory["senses"]["family:away:active"]["evidence_views"][
            "all_evidence_text"
        ]
        self.assertIn("The cabin is far away.", away_evidence)


def _base_inventory() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "profile_id": "base",
        "generated_at": "2026-05-12T00:00:00Z",
        "capability": {},
        "triggers": {
            "family:bank:trigger": {
                "trigger_id": "family:bank:trigger",
                "source_phrase": "bank",
                "normalized_source_phrase": "bank",
                "token_count": 1,
            }
        },
        "senses": {
            "family:bank:active": {
                "sense_id": "family:bank:active",
                "target_lemma": "banco",
                "evidence_views": {
                    "sense_label": "bank -> banco",
                    "all_evidence_text": "bank -> banco",
                },
            },
            "family:bank:shadow:1": {
                "sense_id": "family:bank:shadow:1",
                "target_lemma": "orilla",
            },
        },
        "competition_sets": {
            "family:bank:competition": {
                "competition_set_id": "family:bank:competition",
                "trigger_id": "family:bank:trigger",
                "active_sense_id": "family:bank:active",
                "shadow_sense_ids": ["family:bank:shadow:1"],
                "status": "ready",
            }
        },
        "phrase_sets": {},
    }


def _base_normalized_evidence() -> dict[str, object]:
    return {
        "schema_version": 1,
        "batch_id": "base",
        "source_id": "base",
        "source_type": "internal",
        "source_family": "internal",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "bank",
                "active_target": "banco",
                "candidate_target": "banco",
                "evidence_text": "The bank manages deposits.",
                "roles": ["cue_generation"],
                "metadata": {"family_id": "family:bank"},
            }
        ],
    }


def _add_normalized_evidence() -> dict[str, object]:
    return {
        "schema_version": 1,
        "batch_id": "add",
        "source_id": "add",
        "source_type": "llm",
        "source_family": "silver_llm_generation",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "away",
                "active_target": "lejos",
                "candidate_target": "lejos",
                "active_sense_hint": {"sense_label": "away -> lejos"},
                "evidence_text": "The cabin is far away.",
                "roles": ["cue_generation"],
                "metadata": {"family_id": "family:away"},
            },
            {
                "relation_type": "anchor_cue",
                "trigger": "bank",
                "active_target": "banco",
                "candidate_target": "banco",
                "evidence_text": "The bank approved the loan.",
                "roles": ["cue_generation"],
                "metadata": {"family_id": "family:bank"},
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
