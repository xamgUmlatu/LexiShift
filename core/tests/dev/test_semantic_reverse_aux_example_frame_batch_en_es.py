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
from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
)
from semantic_reverse_aux_example_frame_batch_en_es import (  # noqa: E402
    build_reverse_aux_example_frame_bundle,
    render_reverse_aux_example_frame_batch_markdown,
)


class SemanticReverseAuxExampleFrameBatchTests(unittest.TestCase):
    def test_builds_external_reverse_aux_batch_and_keeps_contract_gap_visible(self) -> None:
        bundle = build_reverse_aux_example_frame_bundle(
            queue_payload=_queue_payload(),
            dataset_payload=_dataset_payload(),
            reverse_records_by_trigger={
                "order": (
                    TranslationGlossRecord(
                        translation="pedido",
                        pos_raw="noun",
                        metadata={"translation_sense_text": "request for a product or service"},
                    ),
                    TranslationGlossRecord(
                        translation="ordenar",
                        pos_raw="verb",
                        metadata={"translation_sense_text": "to set in any order"},
                    ),
                ),
                "check": (
                    TranslationGlossRecord(
                        translation="cheque",
                        pos_raw="noun",
                        metadata={"translation_sense_text": "written payment instruction"},
                    ),
                ),
            },
            data_root=REPO_ROOT,
            reverse_pack=_pack("/tmp/reverse-aux-test.sqlite"),
            generated_at="2026-04-25T12:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "external")
        self.assertEqual(normalized["source_family"], "installed_translation_pack")
        self.assertEqual(normalized["row_count"], 3)
        self.assertEqual(
            [row["relation_type"] for row in normalized["rows"]],
            ["anchor_cue", "shadow_candidate", "anchor_cue"],
        )

        report = bundle["report"]
        summary = report["summary"]
        self.assertEqual(summary["target_families_with_active_aux"], 2)
        self.assertEqual(summary["target_families_with_shadow_aux"], 1)
        self.assertEqual(summary["families_with_phrase_control_examples"], 0)

        contract = build_example_frame_contract_report(
            normalized,
            required_family_keys=["fam:order", "fam:check"],
            generated_at="2026-04-25T12:30:00Z",
        )
        self.assertEqual(contract["status"], "review")
        self.assertEqual(contract["summary"]["contract_complete_family_count"], 0)
        self.assertEqual(contract["summary"]["missing_shadow_family_keys"], ["fam:check"])
        self.assertEqual(
            contract["summary"]["missing_phrase_control_family_keys"],
            ["fam:check", "fam:order"],
        )

        markdown = render_reverse_aux_example_frame_batch_markdown(report)
        self.assertIn("Reverse Aux Example-Frame Batch", markdown)
        self.assertIn("not contract-complete", markdown)


def _queue_payload() -> dict[str, object]:
    return {
        "queue_id": "semantic_prompt_bakeoff_en_es_v10",
        "pair": "en-es",
        "families": [
            {"family_id": "fam:order", "trigger": "order", "role": "target"},
            {"family_id": "fam:check", "trigger": "check", "role": "target"},
        ],
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_v10",
        "families": [
            {
                "family_id": "fam:order",
                "trigger": "order",
                "active": {
                    "sense_id": "fam:order:active",
                    "target_lemma": "pedido",
                    "canonical_pos": "noun",
                },
                "shadows": [
                    {
                        "sense_id": "fam:order:shadow",
                        "target_lemma": "ordenar",
                        "canonical_pos": "verb",
                    }
                ],
            },
            {
                "family_id": "fam:check",
                "trigger": "check",
                "active": {
                    "sense_id": "fam:check:active",
                    "target_lemma": "cheque",
                    "canonical_pos": "noun",
                },
                "shadows": [
                    {
                        "sense_id": "fam:check:shadow",
                        "target_lemma": "revisar",
                        "canonical_pos": "verb",
                    }
                ],
            },
        ],
    }


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
