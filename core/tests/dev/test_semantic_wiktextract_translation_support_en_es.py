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

from semantic_non_v10_source_support_conversion_en_es import (  # noqa: E402
    build_source_support_conversion_report,
)
from semantic_wiktextract_translation_support_en_es import (  # noqa: E402
    build_wiktextract_translation_support_bundle,
    render_wiktextract_translation_support_markdown,
)


class SemanticWiktextractTranslationSupportTests(unittest.TestCase):
    def test_overlay_marks_matching_translation_supported(self) -> None:
        bundle = build_wiktextract_translation_support_bundle(
            dataset_payload=_dataset_payload(),
            records_by_trigger={"black": _black_records()},
            raw_wiktextract_path=Path("/tmp/raw.jsonl.gz"),
            generated_at="2026-04-29T00:00:00Z",
        )

        report = bundle["report"]
        supported = bundle["supported_dataset"]
        active = supported["families"][0]["active"]
        metadata = active["metadata"]

        self.assertEqual(report["status"], "ok")
        self.assertTrue(metadata["wiktextract_translation_support"])
        self.assertIn("wiktextract_en_es_translation_table", metadata["support_sources"])
        self.assertEqual(
            metadata["wiktextract_translation_support_matches"][0]["translation_word"],
            "oscuro",
        )

        conversion = build_source_support_conversion_report(
            dataset_payload=supported,
            generated_at="2026-04-29T00:05:00Z",
        )
        self.assertEqual(conversion["summary"]["fully_supported_family_count"], 1)
        self.assertEqual(conversion["summary"]["support_work_item_count"], 0)

    def test_overlay_requires_spanish_target_and_matching_pos(self) -> None:
        records = _black_records()
        records[0]["pos"] = "noun"
        bundle = build_wiktextract_translation_support_bundle(
            dataset_payload=_dataset_payload(),
            records_by_trigger={"black": records},
            raw_wiktextract_path=Path("/tmp/raw.jsonl.gz"),
            generated_at="2026-04-29T00:00:00Z",
        )

        report = bundle["report"]
        active = bundle["supported_dataset"]["families"][0]["active"]

        self.assertEqual(report["status"], "review")
        self.assertNotIn("wiktextract_translation_support", active["metadata"])

    def test_render_markdown_summarizes_overlay(self) -> None:
        bundle = build_wiktextract_translation_support_bundle(
            dataset_payload=_dataset_payload(),
            records_by_trigger={"black": _black_records()},
            raw_wiktextract_path=Path("/tmp/raw.jsonl.gz"),
            generated_at="2026-04-29T00:00:00Z",
        )

        markdown = render_wiktextract_translation_support_markdown(bundle["report"])

        self.assertIn("Wiktextract Translation Support Overlay", markdown)
        self.assertIn("Newly supported senses: `1`", markdown)
        self.assertIn("`black`", markdown)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "en-es:sentence-veto:black:oscuro",
                "trigger": "black",
                "active": {
                    "sense_id": "black:active",
                    "target_lemma": "oscuro",
                    "canonical_pos": "adjective",
                    "evidence_views": {"all_evidence_text": "black dark without light"},
                    "metadata": {
                        "reverse_support": False,
                        "freedict_support": False,
                        "translation_sense_text": "without light",
                        "support_sources": ["wiktionary_en_es"],
                    },
                },
                "shadows": [
                    {
                        "sense_id": "black:shadow",
                        "target_lemma": "negro",
                        "canonical_pos": "noun",
                        "evidence_views": {"all_evidence_text": "black color noun"},
                        "metadata": {
                            "reverse_support": True,
                            "freedict_support": False,
                            "support_sources": ["wiktionary_en_es", "wiktionary_es_en"],
                        },
                    }
                ],
            }
        ],
    }


def _black_records() -> list[dict[str, object]]:
    return [
        {
            "word": "black",
            "lang_code": "en",
            "pos": "adj",
            "translations": [
                {
                    "lang": "Spanish",
                    "code": "es",
                    "sense": "without light",
                    "word": "oscuro",
                }
            ],
        }
    ]


if __name__ == "__main__":
    unittest.main()
