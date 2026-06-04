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

from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
)
from semantic_wiktextract_example_frame_batch_en_es import (  # noqa: E402
    build_wiktextract_example_frame_bundle,
    render_wiktextract_example_frame_batch_markdown,
)


class SemanticWiktextractExampleFrameBatchTests(unittest.TestCase):
    def test_builds_raw_wiktextract_residual_example_rows(self) -> None:
        bundle = build_wiktextract_example_frame_bundle(
            queue_payload=_queue_payload(),
            dataset_payload=_dataset_payload(),
            records_by_trigger={"plant": _plant_records()},
            data_root=REPO_ROOT,
            raw_wiktextract_path=Path("/tmp/raw-wiktextract.jsonl.gz"),
            family_keys=["fam:plant"],
            scope="family_keys",
            generated_at="2026-04-25T21:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "external")
        self.assertEqual(normalized["source_family"], "external_example_corpus")
        self.assertEqual(normalized["row_count"], 4)
        self.assertEqual(
            [row["relation_type"] for row in normalized["rows"]],
            ["anchor_cue", "anchor_cue", "shadow_candidate", "shadow_candidate"],
        )
        self.assertIn("garden", normalized["rows"][0]["evidence_text"])
        self.assertEqual(
            normalized["rows"][0]["metadata"]["source_view"],
            "raw_wiktextract_example",
        )

        contract = build_example_frame_contract_report(
            normalized,
            required_family_keys=["fam:plant"],
            generated_at="2026-04-25T21:30:00Z",
        )
        self.assertEqual(contract["summary"]["semantic_contract_complete_family_count"], 1)
        self.assertEqual(
            contract["summary"]["phrase_containment_contract_complete_family_count"],
            0,
        )

        markdown = render_wiktextract_example_frame_batch_markdown(bundle["report"])
        self.assertIn("Wiktextract Example-Frame Batch", markdown)
        self.assertIn("external_example_corpus", markdown)


def _queue_payload() -> dict[str, object]:
    return {
        "queue_id": "test",
        "pair": "en-es",
        "families": [{"family_id": "fam:plant", "trigger": "plant", "role": "target"}],
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:plant",
                "trigger": "plant",
                "active": {
                    "sense_id": "fam:plant:active",
                    "target_lemma": "planta",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "living plant organism grows leaves soil water",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:plant:shadow",
                        "target_lemma": "fábrica",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "all_evidence_text": "industrial plant factory production facility",
                        },
                    }
                ],
            }
        ],
    }


def _plant_records() -> list[dict[str, object]]:
    return [
        {
            "word": "plant",
            "lang_code": "en",
            "pos": "noun",
            "senses": [
                {
                    "glosses": ["an organism capable of photosynthesis"],
                    "examples": [
                        {
                            "text": "The garden had colourful plants around the border.",
                            "type": "example",
                        },
                        {
                            "text": "The plant needs more sunlight in the afternoon.",
                            "type": "example",
                        },
                    ],
                },
                {
                    "glosses": ["a factory or industrial facility"],
                    "examples": [
                        {
                            "text": "The company has production plants in three countries.",
                            "type": "example",
                        },
                        {
                            "text": "My dad worked at the plant for 27 years.",
                            "type": "example",
                        },
                    ],
                },
            ],
        }
    ]


if __name__ == "__main__":
    unittest.main()
