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

from lexishift_core.resources.dict_loaders import TranslationGlossRecord  # noqa: E402
from semantic_reverse_aux_text_pilot_en_es import (  # noqa: E402
    augment_queue_dataset_with_reverse_aux_views,
    build_queue_subset_dataset,
    select_reverse_aux_candidate_config,
)


class SemanticReverseAuxTextPilotTests(unittest.TestCase):
    def test_augment_queue_dataset_adds_reverse_aux_views(self) -> None:
        dataset_payload = {
            "schema_version": 1,
            "pair": "en-es",
            "dataset_id": "synthetic",
            "families": [
                {
                    "family_id": "family:order",
                    "trigger": "order",
                    "active": {
                        "sense_id": "active:pedido",
                        "target_lemma": "pedido",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "food order",
                            "all_evidence_text": "food order | request",
                        },
                    },
                    "shadows": [
                        {
                            "sense_id": "shadow:ordenar",
                            "target_lemma": "ordenar",
                            "canonical_pos": "verb",
                            "evidence_views": {
                                "sense_label": "command",
                                "all_evidence_text": "command | instruct",
                            },
                        }
                    ],
                    "cases": [],
                },
                {
                    "family_id": "family:play",
                    "trigger": "play",
                    "active": {
                        "sense_id": "active:obra",
                        "target_lemma": "obra",
                        "canonical_pos": "noun",
                        "evidence_views": {"sense_label": "theatrical work"},
                    },
                    "shadows": [],
                    "cases": [],
                },
            ],
        }
        queue_payload = {
            "families": [
                {"family_id": "family:order", "role": "target"},
                {"family_id": "family:play", "role": "negative_control"},
            ]
        }
        subset_dataset, family_roles = build_queue_subset_dataset(dataset_payload, queue_payload)
        augmented_dataset, coverage_rows = augment_queue_dataset_with_reverse_aux_views(
            subset_dataset,
            family_roles=family_roles,
            reverse_records_by_trigger={
                "order": (
                    TranslationGlossRecord(
                        translation="pedido",
                        pos_raw="noun",
                        metadata={"translation_sense_text": "request for some product or service"},
                    ),
                    TranslationGlossRecord(
                        translation="ordenar",
                        pos_raw="verb",
                        metadata={"translation_sense_text": "to command"},
                    ),
                ),
                "play": (),
            },
        )

        families = {
            family["family_id"]: family
            for family in augmented_dataset["families"]
            if isinstance(family, dict)
        }
        order_active_views = families["family:order"]["active"]["evidence_views"]
        self.assertEqual(
            order_active_views["reverse_aux_text"],
            "request for some product or service",
        )
        self.assertEqual(
            order_active_views["reverse_aux_plus_sense_label"],
            "food order | request for some product or service",
        )
        self.assertEqual(
            order_active_views["reverse_aux_plus_all_evidence"],
            "food order | request | request for some product or service",
        )

        order_shadow_views = families["family:order"]["shadows"][0]["evidence_views"]
        self.assertEqual(order_shadow_views["reverse_aux_text"], "to command")

        coverage_by_family = {
            row["family_id"]: row for row in coverage_rows if isinstance(row, dict)
        }
        self.assertTrue(bool(coverage_by_family["family:order"]["active_aux_ready"]))
        self.assertEqual(int(coverage_by_family["family:order"]["shadow_aux_count"]), 1)
        self.assertFalse(bool(coverage_by_family["family:play"]["active_aux_ready"]))

    def test_select_reverse_aux_candidate_prefers_same_harm_lower_false_abstain(self) -> None:
        selected = select_reverse_aux_candidate_config(
            [
                {
                    "config_id": "current_default",
                    "summary": {"harmful_replace_count": 1, "false_abstain_count": 8},
                },
                {
                    "config_id": "reverse_aux_text_primary",
                    "summary": {"harmful_replace_count": 4, "false_abstain_count": 8},
                },
                {
                    "config_id": "reverse_aux_plus_sense_label",
                    "summary": {"harmful_replace_count": 3, "false_abstain_count": 7},
                },
                {
                    "config_id": "reverse_aux_plus_all_evidence",
                    "summary": {"harmful_replace_count": 1, "false_abstain_count": 6},
                },
            ]
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected["config_id"], "reverse_aux_plus_all_evidence")


if __name__ == "__main__":
    unittest.main()
