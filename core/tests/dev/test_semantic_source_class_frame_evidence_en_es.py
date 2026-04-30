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

from semantic_source_class_frame_evidence_en_es import (  # noqa: E402
    build_source_class_frame_evidence_bundle,
    render_source_class_frame_evidence_markdown,
)


class SemanticSourceClassFrameEvidenceTests(unittest.TestCase):
    def test_builds_non_authorization_class_rows_from_source_text(self) -> None:
        bundle = build_source_class_frame_evidence_bundle(
            dataset_payload=_dataset_payload(),
            generated_at="2026-05-01T05:30:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "internal")
        self.assertEqual(normalized["source_family"], "internal_rulegen_artifact")
        self.assertGreaterEqual(normalized["row_count"], 9)

        class_ids = {row["metadata"]["semantic_class_id"] for row in normalized["rows"]}
        self.assertGreaterEqual(
            class_ids,
            {
                "sports_points_scoring",
                "collision_malfunction",
                "commercial_organization",
            },
        )
        self.assertNotIn("permission_authorization", class_ids)
        self.assertNotIn(
            "tantos", " ".join(row["evidence_text"].lower() for row in normalized["rows"])
        )
        self.assertNotIn(
            "choque", " ".join(row["evidence_text"].lower() for row in normalized["rows"])
        )
        self.assertNotIn(
            "firma", " ".join(row["evidence_text"].lower() for row in normalized["rows"])
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "ok")
        self.assertGreaterEqual(report["summary"]["matching_class_count"], 3)
        self.assertGreaterEqual(report["summary"]["matching_sense_count"], 3)
        self.assertEqual(report["summary"]["row_count"], normalized["row_count"])
        self.assertFalse(
            any(
                sense_row["target_lemma_in_source_match_text"]
                for family in report["family_rows"]
                for sense_row in family["sense_rows"]
            )
        )

        markdown = render_source_class_frame_evidence_markdown(report)
        self.assertIn("Source-Class Frame Evidence Batch", markdown)
        self.assertIn("sports_points_scoring", markdown)
        self.assertIn("Source Trigger Audit", markdown)

    def test_splits_overbroad_wave7_source_classes(self) -> None:
        dataset = _dataset_payload()
        dataset["families"] = [
            {
                "family_id": "fam:gross",
                "trigger": "gross",
                "active": _sense(
                    sense_id="gross:active",
                    target="repulsivo",
                    pos="adjective",
                    text="causing disgust",
                ),
                "shadows": [
                    _sense(
                        sense_id="gross:shadow",
                        target="gruesa",
                        pos="noun",
                        text="twelve dozen",
                    )
                ],
            },
            {
                "family_id": "fam:full",
                "trigger": "full",
                "active": _sense(
                    sense_id="full:active",
                    target="lleno",
                    pos="adjective",
                    text="containing the maximum possible amount",
                ),
                "shadows": [
                    _sense(
                        sense_id="full:shadow",
                        target="abatanar",
                        pos="verb",
                        text="to make cloth denser",
                    )
                ],
            },
            {
                "family_id": "fam:meet",
                "trigger": "meet",
                "active": _sense(
                    sense_id="meet:active",
                    target="adecuado",
                    pos="adjective",
                    text="suitable, right; proper",
                ),
                "shadows": [
                    _sense(
                        sense_id="meet:shadow",
                        target="encontrar",
                        pos="verb",
                        text="to come face to face with by accident; to encounter",
                    )
                ],
            },
            {
                "family_id": "fam:even",
                "trigger": "even",
                "active": _sense(
                    sense_id="even:active",
                    target="tarde",
                    pos="noun",
                    text="Evening of the day",
                ),
                "shadows": [
                    _sense(
                        sense_id="even:shadow",
                        target="allanar",
                        pos="verb",
                        text="to make even",
                    )
                ],
            },
        ]

        bundle = build_source_class_frame_evidence_bundle(
            dataset_payload=dataset,
            generated_at="2026-05-01T05:30:00Z",
        )

        rows = bundle["normalized_batch"]["rows"]
        by_sense = {
            row["metadata"]["candidate_sense_id"]: set()
            for row in rows
            if isinstance(row.get("metadata"), dict)
        }
        for row in rows:
            metadata = row["metadata"]
            by_sense[metadata["candidate_sense_id"]].add(metadata["semantic_class_id"])

        self.assertIn("disgust_repulsion", by_sense["gross:active"])
        self.assertIn("quantity_dozen_count", by_sense["gross:shadow"])
        self.assertIn("full_capacity", by_sense["full:active"])
        self.assertIn("textile_fulling", by_sense["full:shadow"])
        self.assertIn("suitability", by_sense["meet:active"])
        self.assertIn("meeting_encounter", by_sense["meet:shadow"])
        self.assertNotIn("collision_malfunction", by_sense["meet:shadow"])
        self.assertIn("evening_time", by_sense["even:active"])

    def test_reports_review_when_no_class_matches(self) -> None:
        dataset = _dataset_payload()
        dataset["families"] = [
            {
                "family_id": "fam:plain",
                "trigger": "plain",
                "active": _sense(
                    sense_id="plain:active",
                    target="llano",
                    pos="adjective",
                    text="simple and without decoration",
                ),
                "shadows": [],
            }
        ]

        bundle = build_source_class_frame_evidence_bundle(
            dataset_payload=dataset,
            generated_at="2026-05-01T05:30:00Z",
        )

        self.assertIsNone(bundle["normalized_batch"])
        self.assertEqual(bundle["report"]["status"], "review")
        self.assertEqual(bundle["report"]["summary"]["row_count"], 0)


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:score",
                "trigger": "score",
                "active": _sense(
                    sense_id="score:active",
                    target="tantos",
                    pos="noun",
                    text="number of points earned",
                ),
                "shadows": [
                    _sense(
                        sense_id="score:shadow",
                        target="anotar",
                        pos="verb",
                        text="to earn points in a game",
                    )
                ],
            },
            {
                "family_id": "fam:crash",
                "trigger": "crash",
                "active": _sense(
                    sense_id="crash:active",
                    target="choque",
                    pos="noun",
                    text="vehicle accident",
                ),
                "shadows": [
                    _sense(
                        sense_id="crash:shadow",
                        target="fallo",
                        pos="noun",
                        text="computer malfunction",
                    )
                ],
            },
            {
                "family_id": "fam:firm",
                "trigger": "firm",
                "active": _sense(
                    sense_id="firm:active",
                    target="firma",
                    pos="noun",
                    text="business partnership",
                ),
                "shadows": [],
            },
        ],
    }


def _sense(*, sense_id: str, target: str, pos: str, text: str) -> dict[str, object]:
    return {
        "sense_id": sense_id,
        "target_lemma": target,
        "canonical_pos": pos,
        "evidence_views": {
            "sense_label": f"test {pos} sense: {text}",
            "gloss_text": text,
            "sense_gloss_bundle": f"test {pos} sense: {text} | {text}",
        },
        "metadata": {
            "translation_sense_text": text,
            "support_sources": ["wiktextract_en_es_translation_table"],
            "wiktextract_translation_support": True,
            "wiktextract_translation_support_matches": [
                {
                    "record_word": "test",
                    "record_pos": pos,
                    "translation_word": target,
                    "translation_sense": text,
                    "translation_tags": [],
                    "sense_overlap": [],
                }
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
