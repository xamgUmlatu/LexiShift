from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SCRIPT_ROOT = os.path.join(PROJECT_ROOT, "scripts", "testing")
for candidate in (PROJECT_ROOT, SCRIPT_ROOT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_reporting import render_prompt_smoke_markdown  # noqa: E402
from semantic_llm_prompt_smoke import build_prompt_smoke_report  # noqa: E402


class TestSemanticLlmPromptSmoke(unittest.TestCase):
    def test_build_prompt_smoke_report_renders_active_slot_requests(self) -> None:
        queue_payload = {
            "queue_id": "queue-v10",
            "families": [
                {
                    "family_id": "en-es:sentence-veto:plant:planta",
                    "likely_bucket": "needs_cue_data",
                    "primary_prompt_slot": "cue_contrastive_general_v1",
                    "notes": ["Calibration family."],
                },
                {
                    "family_id": "en-es:sentence-veto:play:obra",
                    "likely_bucket": "needs_phrase_parsing_fix",
                    "primary_prompt_slot": "",
                    "notes": ["Negative control only."],
                },
            ],
            "default_negative_control_family_ids": ["en-es:sentence-veto:play:obra"],
        }
        slot_manifest_payload = {
            "slots": [
                {
                    "prompt_slot": "cue_contrastive_general_v1",
                    "status": "active",
                    "target_family_ids": ["en-es:sentence-veto:plant:planta"],
                    "target_archetypes": ["ordinary_weak_active_support"],
                    "notes": ["General cue slot."],
                }
            ]
        }
        family_inventory_payload = {
            "families": [
                {
                    "family_id": "en-es:sentence-veto:plant:planta",
                    "bucket_evidence": ["Plant is still weak-active-support."],
                }
            ]
        }
        prompt_spec_payload = {
            "spec_id": "spec-v10",
            "pair": "en-es",
            "prompt_version": "semantic_prompt_bakeoff_v1",
            "stage_defaults": {
                "proxy": {"model_id": "gpt-5.4-mini", "temperature": 0.2},
                "target": {"model_id": "gpt-5.4", "temperature": 0.2},
            },
            "slots": [
                {
                    "prompt_slot": "cue_contrastive_general_v1",
                    "relation_type": "anchor_cue",
                    "system_prompt": "System prompt.",
                    "user_prompt_template": (
                        "Trigger {trigger}; active {active_target}; candidate {candidate_target}; "
                        "notes {family_notes}; stage {stage}; row {row_id}; input {input_ref}"
                    ),
                }
            ],
        }
        dataset_payload = {
            "families": [
                {
                    "family_id": "en-es:sentence-veto:plant:planta",
                    "trigger": "plant",
                    "active": {
                        "sense_id": "active-1",
                        "target_lemma": "planta",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "living organism",
                            "gloss_text": "botanical organism",
                        },
                    },
                    "shadows": [
                        {
                            "sense_id": "shadow-1",
                            "target_lemma": "fábrica",
                            "canonical_pos": "noun",
                            "evidence_views": {
                                "sense_label": "industrial facility",
                                "gloss_text": "factory building",
                            },
                        }
                    ],
                }
            ]
        }

        report = build_prompt_smoke_report(
            queue_payload=queue_payload,
            slot_manifest_payload=slot_manifest_payload,
            family_inventory_payload=family_inventory_payload,
            prompt_spec_payload=prompt_spec_payload,
            dataset_payload=dataset_payload,
            stage="proxy",
            generated_at="2026-04-24T12:00:00Z",
        )

        self.assertEqual(report["selected_model_id"], "gpt-5.4-mini")
        self.assertEqual(report["summary"]["request_count"], 1)
        request = report["request_rows"][0]
        self.assertEqual(request["prompt_slot"], "cue_contrastive_general_v1")
        self.assertEqual(request["active_target"], "planta")
        self.assertEqual(request["candidate_target"], "fábrica")
        self.assertIn("Calibration family.", request["user_prompt"])
        self.assertIn("Plant is still weak-active-support.", request["user_prompt"])
        self.assertEqual(
            request["expected_row_preview"]["prompt_slot"], "cue_contrastive_general_v1"
        )

    def test_render_prompt_smoke_markdown_includes_sample_request(self) -> None:
        markdown = render_prompt_smoke_markdown(
            {
                "status": "ok",
                "generated_at": "2026-04-24T12:00:00Z",
                "queue_id": "queue-v10",
                "prompt_spec_id": "spec-v10",
                "prompt_version": "semantic_prompt_bakeoff_v1",
                "stage": "proxy",
                "selected_model_id": "gpt-5.4-mini",
                "selected_temperature": 0.2,
                "summary": {
                    "active_slot_count": 1,
                    "request_count": 1,
                    "target_family_count": 1,
                    "negative_control_count": 1,
                },
                "slot_rows": [
                    {
                        "prompt_slot": "cue_contrastive_general_v1",
                        "status": "active",
                        "target_family_count": 1,
                        "request_count": 1,
                        "notes": ["General cue slot."],
                    }
                ],
                "sample_requests": [
                    {
                        "request_id": "req-1",
                        "prompt_slot": "cue_contrastive_general_v1",
                        "family_id": "en-es:sentence-veto:plant:planta",
                        "trigger": "plant",
                        "active_target": "planta",
                        "candidate_target": "fábrica",
                        "model_id": "gpt-5.4-mini",
                        "temperature": 0.2,
                        "system_prompt": "System prompt.",
                        "user_prompt": "User prompt.",
                        "expected_row_preview": {
                            "row_id": "row-1",
                            "prompt_slot": "cue_contrastive_general_v1",
                        },
                    }
                ],
            }
        )

        self.assertIn("Semantic LLM Prompt Smoke", markdown)
        self.assertIn("cue_contrastive_general_v1", markdown)
        self.assertIn("req-1", markdown)


if __name__ == "__main__":
    unittest.main()
