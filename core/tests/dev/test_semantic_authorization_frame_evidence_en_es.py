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

from semantic_authorization_frame_evidence_en_es import (  # noqa: E402
    AUTHORIZATION_TEMPLATES,
    build_authorization_frame_evidence_bundle,
    render_authorization_frame_evidence_markdown,
)


class SemanticAuthorizationFrameEvidenceTests(unittest.TestCase):
    def test_builds_authorization_rows_without_target_leakage(self) -> None:
        bundle = build_authorization_frame_evidence_bundle(
            dataset_payload=_dataset_payload(),
            generated_at="2026-04-29T04:30:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["source_type"], "internal")
        self.assertEqual(normalized["source_family"], "internal_rulegen_artifact")
        self.assertEqual(normalized["row_count"], len(AUTHORIZATION_TEMPLATES))

        rows = normalized["rows"]
        self.assertTrue(all(row["relation_type"] == "anchor_cue" for row in rows))
        self.assertEqual(
            {row["candidate_sense_hint"]["target_key"] for row in rows},
            {"leave:active"},
        )
        self.assertEqual(
            {row["metadata"]["semantic_class_id"] for row in rows},
            {"permission_authorization"},
        )
        self.assertIn("approved permission request", {row["evidence_text"] for row in rows})
        self.assertNotIn("permiso", " ".join(row["evidence_text"].lower() for row in rows))

        report = bundle["report"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["matching_sense_count"], 1)
        self.assertEqual(report["summary"]["active_row_count"], len(AUTHORIZATION_TEMPLATES))
        self.assertEqual(report["summary"]["shadow_row_count"], 0)
        active_sense_row = report["family_rows"][0]["sense_rows"][0]
        self.assertTrue(active_sense_row["matched"])
        self.assertIn("permission to be absent", active_sense_row["source_match_text"])
        self.assertFalse(active_sense_row["target_lemma_in_source_match_text"])
        self.assertIn(
            "wiktextract_en_es_translation_table",
            active_sense_row["support_sources"],
        )

        markdown = render_authorization_frame_evidence_markdown(report)
        self.assertIn("Authorization-Frame Evidence Batch", markdown)
        self.assertIn("internal_rulegen_artifact", markdown)
        self.assertIn("Source Trigger Audit", markdown)
        self.assertIn("permission to be absent", markdown)

    def test_can_emit_shadow_rows_when_authorization_sense_is_shadow(self) -> None:
        dataset = _dataset_payload()
        _mark_active_as_absence_sense(dataset)
        dataset["families"][0]["shadows"][0]["metadata"]["translation_sense_text"] = (
            "official permission"
        )

        bundle = build_authorization_frame_evidence_bundle(
            dataset_payload=dataset,
            generated_at="2026-04-29T04:30:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["row_count"], len(AUTHORIZATION_TEMPLATES))
        self.assertTrue(
            all(row["relation_type"] == "shadow_candidate" for row in normalized["rows"])
        )
        self.assertEqual(
            {row["candidate_sense_hint"]["target_key"] for row in normalized["rows"]},
            {"leave:shadow"},
        )

    def test_reports_review_when_no_authorization_sense_is_present(self) -> None:
        dataset = _dataset_payload()
        _mark_active_as_absence_sense(dataset)

        bundle = build_authorization_frame_evidence_bundle(
            dataset_payload=dataset,
            generated_at="2026-04-29T04:30:00Z",
        )

        self.assertIsNone(bundle["normalized_batch"])
        self.assertEqual(bundle["report"]["status"], "review")
        self.assertEqual(bundle["report"]["summary"]["row_count"], 0)


def _mark_active_as_absence_sense(dataset: dict[str, object]) -> None:
    active = dataset["families"][0]["active"]
    active["metadata"]["translation_sense_text"] = "absence from work"
    active["metadata"]["wiktextract_translation_support_matches"][0]["translation_sense"] = (
        "absence from work"
    )
    active["metadata"]["wiktextract_translation_support_matches"][0]["sense_overlap"] = ["absence"]
    active["evidence_views"]["gloss_text"] = "absence from work"
    active["evidence_views"]["sense_label"] = "leave noun sense: absence from work"
    active["evidence_views"]["sense_gloss_bundle"] = (
        "leave noun sense: absence from work | absence from work"
    )
    active["evidence_views"]["all_evidence_text"] = (
        "permiso | leave noun sense: absence from work | absence from work"
    )


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test",
        "families": [
            {
                "family_id": "fam:leave",
                "trigger": "leave",
                "active": {
                    "sense_id": "leave:active",
                    "target_lemma": "permiso",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "leave noun sense: permission to be absent",
                        "gloss_text": "permission to be absent",
                        "all_evidence_text": (
                            "permiso | leave noun sense: permission to be absent"
                        ),
                    },
                    "metadata": {
                        "translation_sense_text": "permission to be absent",
                        "support_sources": [
                            "wiktionary_en_es",
                            "wiktextract_en_es_translation_table",
                        ],
                        "wiktextract_translation_support": True,
                        "wiktextract_translation_support_matches": [
                            {
                                "record_word": "leave",
                                "record_pos": "noun",
                                "translation_word": "permiso",
                                "translation_sense": "permission to be absent",
                                "translation_tags": ["masculine"],
                                "sense_overlap": ["permission"],
                            }
                        ],
                    },
                },
                "shadows": [
                    {
                        "sense_id": "leave:shadow",
                        "target_lemma": "excedencia",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "leave noun sense: absence from work",
                            "gloss_text": "absence from work",
                            "all_evidence_text": (
                                "excedencia | leave noun sense: absence from work"
                            ),
                        },
                        "metadata": {
                            "translation_sense_text": "absence from work",
                            "support_sources": [
                                "wiktionary_en_es",
                                "wiktextract_en_es_translation_table",
                            ],
                        },
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
