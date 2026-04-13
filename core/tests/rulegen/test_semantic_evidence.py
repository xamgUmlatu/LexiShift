from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402


class TestSemanticEvidence(unittest.TestCase):
    def test_normalize_llm_intake_batch_builds_deterministic_rows(self) -> None:
        batch = {
            "schema_version": 1,
            "batch_id": "llm-en-es-001",
            "pair": "en-es",
            "source_type": "llm",
            "source_id": "llm_shadow_proposals",
            "source_family": "silver_llm_generation",
            "roles": ["candidate_generation"],
            "generated_at": "2026-04-14T10:00:00Z",
            "ingested_at": "2026-04-14T10:05:00Z",
            "review_state": "unreviewed",
            "model_id": "gpt-5.4",
            "prompt_version": "shadow-proposals-v1",
            "temperature": 0.2,
            "cost_metadata": {"input_tokens": 123, "output_tokens": 45},
            "provenance": {"request_id": "req_123"},
            "items": [
                {
                    "row_id": "row-1",
                    "relation_type": "shadow_candidate",
                    "trigger": " Catch   sight of ",
                    "active_target": " Vista ",
                    "candidate_target": " coger ",
                    "candidate_pos": " Verb ",
                    "evidence_text": "Use for catching or grabbing.",
                    "confidence": "0.63",
                    "review_state": "accepted",
                    "promotion_state": "kept",
                    "runtime_publishable": True,
                    "input_ref": "prompt-input-1",
                    "raw_response_ref": "response-1",
                    "candidate_sense_hint": {
                        "provider": "wiktionary_es_en",
                        "locator_kind": "wiktionary_ordinal",
                        "entry_ord": "2",
                        "sense_ord": 1,
                        "sense_label": "to catch, seize",
                        "unknown_extra": "keep-me",
                    },
                }
            ],
        }

        normalized_one = normalize_llm_intake_batch(batch)
        normalized_two = normalize_llm_intake_batch(batch)

        self.assertEqual(normalized_one["normalization_version"], "semantic_evidence_v1")
        self.assertEqual(normalized_one["row_count"], 1)
        self.assertEqual(normalized_one["rows"], normalized_two["rows"])

        row = normalized_one["rows"][0]
        self.assertEqual(row["trigger"], "Catch sight of")
        self.assertEqual(row["normalized_trigger"], "catch sight of")
        self.assertEqual(row["active_target"], "Vista")
        self.assertEqual(row["normalized_active_target"], "vista")
        self.assertEqual(row["candidate_target"], "coger")
        self.assertEqual(row["candidate_pos"], "verb")
        self.assertEqual(row["review_state"], "accepted")
        self.assertEqual(row["promotion_state"], "kept")
        self.assertEqual(row["linkage_status"], "partially_linked")
        self.assertTrue(row["is_multiword"])
        self.assertFalse(row["runtime_publishable"])
        self.assertEqual(row["confidence"], 0.63)
        self.assertEqual(row["provenance"]["requested_runtime_publishable"], True)
        self.assertEqual(
            row["candidate_sense_hint"]["metadata"]["unknown_extra"],
            "keep-me",
        )

    def test_normalize_llm_intake_batch_inherits_batch_defaults(self) -> None:
        normalized = normalize_llm_intake_batch(
            {
                "schema_version": 1,
                "batch_id": "llm-en-es-002",
                "pair": "en-es",
                "source_type": "llm",
                "source_id": "llm_anchor_cues",
                "source_family": "silver_llm_generation",
                "roles": ["cue_generation"],
                "generated_at": "2026-04-14T10:00:00Z",
                "ingested_at": "2026-04-14T10:05:00Z",
                "review_state": "unreviewed",
                "model_id": "gpt-5.4-mini",
                "prompt_version": "anchor-cues-v1",
                "items": [
                    {
                        "row_id": "row-2",
                        "relation_type": "anchor_cue",
                        "trigger": "work",
                        "active_target": "trabajo",
                        "candidate_target": "obra",
                        "evidence_text": "Use for labor or employment contexts.",
                    }
                ],
            }
        )

        row = normalized["rows"][0]
        self.assertEqual(row["roles"], ["cue_generation"])
        self.assertEqual(row["review_state"], "unreviewed")
        self.assertEqual(row["promotion_state"], "proposed")
        self.assertEqual(row["linkage_status"], "unlinked")
        self.assertEqual(row["relation_type"], "anchor_cue")

    def test_normalize_llm_intake_batch_rejects_pair_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match batch pair"):
            normalize_llm_intake_batch(
                {
                    "schema_version": 1,
                    "batch_id": "llm-en-es-003",
                    "pair": "en-es",
                    "source_type": "llm",
                    "source_id": "llm_shadow_proposals",
                    "source_family": "silver_llm_generation",
                    "roles": ["candidate_generation"],
                    "generated_at": "2026-04-14T10:00:00Z",
                    "ingested_at": "2026-04-14T10:05:00Z",
                    "review_state": "unreviewed",
                    "model_id": "gpt-5.4",
                    "prompt_version": "shadow-proposals-v1",
                    "items": [
                        {
                            "row_id": "row-3",
                            "pair": "en-ja",
                            "relation_type": "shadow_candidate",
                            "trigger": "ball",
                            "active_target": "pelota",
                            "candidate_target": "baile",
                            "evidence_text": "Mismatched pair row.",
                        }
                    ],
                }
            )

    def test_normalize_llm_intake_batch_requires_candidate_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate_target must be a non-empty string"):
            normalize_llm_intake_batch(
                {
                    "schema_version": 1,
                    "batch_id": "llm-en-es-004",
                    "pair": "en-es",
                    "source_type": "llm",
                    "source_id": "llm_shadow_proposals",
                    "source_family": "silver_llm_generation",
                    "roles": ["candidate_generation"],
                    "generated_at": "2026-04-14T10:00:00Z",
                    "ingested_at": "2026-04-14T10:05:00Z",
                    "review_state": "unreviewed",
                    "model_id": "gpt-5.4",
                    "prompt_version": "shadow-proposals-v1",
                    "items": [
                        {
                            "row_id": "row-4",
                            "relation_type": "shadow_candidate",
                            "trigger": "ball",
                            "active_target": "pelota",
                            "evidence_text": "Missing candidate target.",
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
