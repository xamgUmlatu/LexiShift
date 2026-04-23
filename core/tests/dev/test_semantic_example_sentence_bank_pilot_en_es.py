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
from semantic_example_sentence_bank_pilot_en_es import (  # noqa: E402
    build_example_sentence_bank_pilot_report,
    render_example_sentence_bank_pilot_markdown,
)


class SemanticExampleSentenceBankPilotTests(unittest.TestCase):
    def test_pilot_distinguishes_example_ready_aux_only_and_guardrail_rows(self) -> None:
        queue_payload = {
            "queue_id": "semantic_prompt_bakeoff_en_es_v10",
            "dataset_id": "en_es_sentence_veto_v10",
            "families": [
                {
                    "family_id": "family:order",
                    "trigger": "order",
                    "role": "target",
                    "likely_bucket": "needs_cue_data",
                    "primary_prompt_slot": "cue_cross_pos_frame_v1",
                },
                {
                    "family_id": "family:check",
                    "trigger": "check",
                    "role": "target",
                    "likely_bucket": "needs_cue_data",
                    "primary_prompt_slot": "cue_cross_pos_frame_v1",
                },
                {
                    "family_id": "family:play",
                    "trigger": "play",
                    "role": "negative_control",
                    "likely_bucket": "needs_phrase_parsing_fix",
                    "primary_prompt_slot": "",
                },
            ],
        }
        inventory_payload = {
            "inventory_id": "semantic_family_inventory_en_es_v10",
            "families": [
                {
                    "family_id": "family:order",
                    "active_target": "pedido",
                    "metadata": {"split_id": "held_out"},
                },
                {
                    "family_id": "family:check",
                    "active_target": "cheque",
                    "metadata": {"split_id": "held_out"},
                },
                {
                    "family_id": "family:play",
                    "active_target": "obra",
                    "metadata": {"split_id": "held_out"},
                },
            ],
        }
        forward_records_by_target = {
            "pedido": (
                TranslationGlossRecord(
                    translation="order",
                    pos_raw="noun",
                    metadata={
                        "sense_examples": [
                            {"text": "We placed an order for lunch."},
                        ]
                    },
                ),
            ),
            "cheque": (
                TranslationGlossRecord(
                    translation="check",
                    pos_raw="noun",
                    metadata={},
                ),
            ),
        }
        reverse_records_by_trigger = {
            "order": (
                TranslationGlossRecord(
                    translation="pedido",
                    pos_raw="noun",
                    metadata={"translation_sense_text": "request for some product or service"},
                ),
            ),
            "check": (
                TranslationGlossRecord(
                    translation="cheque",
                    pos_raw="noun",
                    metadata={"translation_sense_text": "written payment instruction"},
                ),
            ),
            "play": (),
        }

        report = build_example_sentence_bank_pilot_report(
            queue_payload=queue_payload,
            inventory_payload=inventory_payload,
            forward_records_by_target=forward_records_by_target,
            reverse_records_by_trigger=reverse_records_by_trigger,
            data_root=REPO_ROOT,
            forward_pack=None,
            reverse_pack=None,
            generated_at="2026-04-24T12:00:00Z",
        )

        self.assertEqual(report["status"], "missing_resources")
        self.assertIn("forward_translation_pack", report["resource_status"]["missing_resources"])

        report = build_example_sentence_bank_pilot_report(
            queue_payload=queue_payload,
            inventory_payload=inventory_payload,
            forward_records_by_target=forward_records_by_target,
            reverse_records_by_trigger=reverse_records_by_trigger,
            data_root=REPO_ROOT,
            forward_pack=self._pack("/tmp/fwd.sqlite"),
            reverse_pack=self._pack("/tmp/rev.sqlite"),
            generated_at="2026-04-24T12:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(summary["target_family_count"], 2)
        self.assertEqual(summary["negative_control_family_count"], 1)
        self.assertEqual(summary["target_families_with_any_examples"], 1)
        self.assertEqual(summary["target_families_with_trigger_matched_examples"], 1)
        self.assertEqual(summary["target_families_with_reverse_aux_text"], 2)
        self.assertEqual(summary["target_families_aux_only"], 1)
        self.assertTrue(bool(summary["example_source_ready_on_current_packs"]))

        families = {
            str(family["family_id"]): family
            for family in report["families"]
            if isinstance(family, dict)
        }
        order_family = families["family:order"]
        self.assertEqual(order_family["status"], "example_ready")
        self.assertTrue(bool(order_family["trigger_matched_example_ready"]))
        self.assertIn("We placed an order for lunch.", order_family["sample_forward_examples"])

        check_family = families["family:check"]
        self.assertEqual(check_family["status"], "no_examples_but_aux_text_available")
        self.assertTrue(bool(check_family["reverse_aux_ready"]))
        self.assertEqual(
            check_family["sample_reverse_aux_texts"],
            ["written payment instruction"],
        )

        play_family = families["family:play"]
        self.assertEqual(play_family["status"], "guardrail_only")
        self.assertEqual(play_family["recommended_action"], "keep_as_negative_control")

        markdown = render_example_sentence_bank_pilot_markdown(report)
        self.assertIn("Target families with any example-bearing rows", markdown)
        self.assertIn("candidate_for_reverse_aux_text_control", str(report))
        self.assertIn("`check -> cheque`", markdown)

    @staticmethod
    def _pack(path: str) -> object:
        class _Pack:
            def __init__(self, path_value: str) -> None:
                self.path = Path(path_value)
                self.provider = "wiktionary"
                self.pack_id = "pack"
                self.direction = "test"

        pack = _Pack(path)
        pack.path.parent.mkdir(parents=True, exist_ok=True)
        pack.path.write_text("", encoding="utf-8")
        return pack


if __name__ == "__main__":
    unittest.main()
