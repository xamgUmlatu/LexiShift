from __future__ import annotations

import json
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

from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
)
from semantic_wordnet_example_frame_batch_en_es import (  # noqa: E402
    build_wordnet_example_frame_bundle,
    render_wordnet_example_frame_batch_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticWordNetExampleFrameBatchTests(unittest.TestCase):
    def test_builds_external_wordnet_active_shadow_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wordnet_dir = Path(tmp_dir)
            _write_wordnet_fixture(wordnet_dir)

            bundle = build_wordnet_example_frame_bundle(
                queue_payload=_queue_payload(),
                dataset_payload=_dataset_payload(),
                wordnet_dir=wordnet_dir,
                data_root=REPO_ROOT,
                scope="all_dataset_families",
                min_link_score=0.1,
                generated_at="2026-04-25T20:00:00Z",
            )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "external")
        self.assertEqual(normalized["source_family"], "external_sense_graph")
        self.assertEqual(normalized["row_count"], 4)
        self.assertEqual(
            [row["relation_type"] for row in normalized["rows"]],
            ["anchor_cue", "shadow_candidate", "anchor_cue", "shadow_candidate"],
        )
        first = normalized["rows"][0]
        self.assertEqual(first["metadata"]["wordnet_synset_id"], "bank-money-n")
        self.assertEqual(first["metadata"]["wordnet_evidence_kind"], "example")
        self.assertFalse(first["runtime_publishable"])

        report = bundle["report"]
        summary = report["summary"]
        self.assertEqual(summary["target_families_with_active_wordnet"], 2)
        self.assertEqual(summary["target_families_with_shadow_wordnet"], 2)
        self.assertEqual(summary["families_with_phrase_control_examples"], 0)

        contract = build_example_frame_contract_report(
            normalized,
            required_family_keys=["fam:bank", "fam:check"],
            generated_at="2026-04-25T20:30:00Z",
        )
        self.assertEqual(contract["status"], "review")
        self.assertEqual(contract["summary"]["semantic_contract_complete_family_count"], 2)
        self.assertEqual(
            contract["summary"]["phrase_containment_contract_complete_family_count"],
            0,
        )

        markdown = render_wordnet_example_frame_batch_markdown(report)
        self.assertIn("WordNet Example-Frame Batch", markdown)
        self.assertIn("external_sense_graph", markdown)

    def test_residual_scope_filters_to_latest_semantic_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wordnet_dir = Path(tmp_dir)
            _write_wordnet_fixture(wordnet_dir)

            bundle = build_wordnet_example_frame_bundle(
                queue_payload=_queue_payload(),
                dataset_payload=_dataset_payload(),
                residual_cycle_payload={"residuals": {"semantic_gap_family_keys": ["fam:check"]}},
                wordnet_dir=wordnet_dir,
                data_root=REPO_ROOT,
                scope="residual_semantic_gaps",
                min_link_score=0.1,
                generated_at="2026-04-25T20:00:00Z",
            )

        normalized = bundle["normalized_batch"]
        family_ids = {row["metadata"]["family_id"] for row in normalized["rows"]}
        self.assertEqual(family_ids, {"fam:check"})
        self.assertEqual(bundle["report"]["summary"]["source_family_count"], 1)
        self.assertEqual(bundle["report"]["summary"]["row_count"], 2)

    def test_optional_related_hyponyms_emit_source_backed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wordnet_dir = Path(tmp_dir)
            _write_wordnet_fixture(wordnet_dir)

            bundle = build_wordnet_example_frame_bundle(
                queue_payload=_queue_payload(),
                dataset_payload=_dataset_payload(),
                wordnet_dir=wordnet_dir,
                data_root=REPO_ROOT,
                scope="all_dataset_families",
                min_link_score=0.1,
                max_rows_per_sense=3,
                include_related_hyponyms=True,
                max_related_rows_per_sense=1,
                related_hyponym_depth=1,
                generated_at="2026-04-25T20:00:00Z",
            )

        normalized = bundle["normalized_batch"]
        related_rows = [
            row
            for row in normalized["rows"]
            if row["metadata"].get("wordnet_source_relation") == "direct_hyponym"
        ]
        self.assertTrue(related_rows)
        self.assertEqual(related_rows[0]["metadata"]["wordnet_relation_path"][0], "bank-money-n")
        self.assertIn("credit union", related_rows[0]["evidence_text"])

    def test_related_hyponyms_can_traverse_bounded_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wordnet_dir = Path(tmp_dir)
            _write_wordnet_fixture(wordnet_dir)

            bundle = build_wordnet_example_frame_bundle(
                queue_payload=_queue_payload(),
                dataset_payload=_dataset_payload(),
                wordnet_dir=wordnet_dir,
                data_root=REPO_ROOT,
                scope="family_keys",
                family_keys=["fam:bank"],
                min_link_score=0.1,
                max_rows_per_sense=8,
                include_related_hyponyms=True,
                max_related_rows_per_sense=2,
                related_hyponym_depth=2,
                generated_at="2026-04-25T20:00:00Z",
            )

        normalized = bundle["normalized_batch"]
        related_paths = [
            row["metadata"].get("wordnet_relation_path")
            for row in normalized["rows"]
            if row["metadata"].get("wordnet_source_relation")
            in {"direct_hyponym", "related_hyponym"}
        ]
        related_relations = {
            row["metadata"].get("wordnet_source_relation")
            for row in normalized["rows"]
            if row["metadata"].get("wordnet_relation_path")
            == ["bank-money-n", "credit-union-n", "community-bank-n"]
        }
        self.assertIn(["bank-money-n", "credit-union-n", "community-bank-n"], related_paths)
        self.assertEqual(related_relations, {"related_hyponym"})

    def test_weak_overlap_uses_wordnet_sense_order_as_source_prior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            wordnet_dir = Path(tmp_dir)
            _write_wordnet_fixture(wordnet_dir)

            index = WordNetIndex.load(wordnet_dir)
            candidates = index.candidates_for_sense(
                trigger="change",
                sense={
                    "sense_id": "fam:change:active",
                    "target_lemma": "cambio",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "change noun sense: process becoming different",
                    },
                },
                min_link_score=0.0,
            )

        self.assertEqual(candidates[0].synset_id, "change-event-n")
        self.assertEqual(candidates[0].sense_rank, 1)
        self.assertEqual(candidates[1].synset_id, "change-money-n")


def _queue_payload() -> dict[str, object]:
    return {
        "queue_id": "semantic_prompt_bakeoff_en_es_v10",
        "pair": "en-es",
        "families": [
            {"family_id": "fam:bank", "trigger": "bank", "role": "target"},
            {"family_id": "fam:check", "trigger": "check", "role": "target"},
        ],
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:bank",
                "trigger": "bank",
                "active": {
                    "sense_id": "fam:bank:active",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "all_evidence_text": "financial bank money deposit account payment",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:bank:shadow",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "all_evidence_text": "river shore water edge bank",
                        },
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
                    "evidence_views": {
                        "all_evidence_text": "written bank payment check order money",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:check:shadow",
                        "target_lemma": "revisar",
                        "canonical_pos": "verb",
                        "evidence_views": {
                            "all_evidence_text": "inspect verify examine quality condition",
                        },
                    }
                ],
            },
        ],
    }


def _write_wordnet_fixture(wordnet_dir: Path) -> None:
    (wordnet_dir / "entries-b.json").write_text(
        json.dumps(
            {
                "bank": {
                    "n": {
                        "sense": [
                            {"id": "bank%1:14:00::", "synset": "bank-money-n"},
                            {"id": "bank%1:17:00::", "synset": "bank-river-n"},
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (wordnet_dir / "entries-c.json").write_text(
        json.dumps(
            {
                "change": {
                    "n": {
                        "sense": [
                            {"id": "change%1:11:00::", "synset": "change-event-n"},
                            {"id": "change%1:21:03::", "synset": "change-money-n"},
                        ]
                    }
                },
                "check": {
                    "n": {
                        "sense": [
                            {"id": "check%1:21:00::", "synset": "check-money-n"},
                        ]
                    },
                    "v": {
                        "sense": [
                            {"id": "check%2:31:00::", "synset": "check-inspect-v"},
                        ]
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (wordnet_dir / "noun.test.json").write_text(
        json.dumps(
            {
                "bank-money-n": {
                    "definition": ["a financial institution that accepts deposits"],
                    "example": ["The bank approved the loan"],
                    "members": ["bank"],
                    "partOfSpeech": "n",
                },
                "credit-union-n": {
                    "definition": ["a cooperative financial institution that accepts deposits"],
                    "example": ["The credit union approved a small loan"],
                    "members": ["credit union"],
                    "hypernym": ["bank-money-n"],
                    "partOfSpeech": "n",
                },
                "community-bank-n": {
                    "definition": ["a local bank owned by community members"],
                    "example": ["The community bank funded the bakery"],
                    "members": ["community bank"],
                    "hypernym": ["credit-union-n"],
                    "partOfSpeech": "n",
                },
                "bank-river-n": {
                    "definition": ["sloping land beside a river"],
                    "example": ["The canoe drifted toward the river bank"],
                    "members": ["bank", "riverbank"],
                    "partOfSpeech": "n",
                },
                "check-money-n": {
                    "definition": ["a written order directing a bank to pay money"],
                    "example": ["He paid the bill by check"],
                    "members": ["check", "cheque"],
                    "partOfSpeech": "n",
                },
                "change-event-n": {
                    "definition": ["an event that occurs when something passes state"],
                    "example": ["The change was gradual"],
                    "members": ["change"],
                    "partOfSpeech": "n",
                },
                "change-money-n": {
                    "definition": ["money received in a different denomination"],
                    "example": ["He got change for a twenty"],
                    "members": ["change"],
                    "partOfSpeech": "n",
                },
            }
        ),
        encoding="utf-8",
    )
    (wordnet_dir / "verb.test.json").write_text(
        json.dumps(
            {
                "check-inspect-v": {
                    "definition": ["examine so as to determine quality or condition"],
                    "example": ["Technicians check the pressure every hour"],
                    "members": ["check", "inspect"],
                    "partOfSpeech": "v",
                },
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
