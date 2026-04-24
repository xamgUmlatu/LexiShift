from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SCRIPT_ROOT = os.path.join(PROJECT_ROOT, "scripts", "testing")
for candidate in (PROJECT_ROOT, SCRIPT_ROOT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_cost_estimate_en_es import build_prompt_cost_estimate_report  # noqa: E402
from semantic_llm_prompt_reporting import render_prompt_cost_estimate_markdown  # noqa: E402


class TestSemanticLlmPromptCostEstimateEnEs(unittest.TestCase):
    def test_build_prompt_cost_estimate_report_computes_token_and_cost_totals(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        report = build_prompt_cost_estimate_report(
            queue_payload=queue_payload,
            slot_manifest_payload=slot_manifest_payload,
            family_inventory_payload=family_inventory_payload,
            prompt_spec_payload=prompt_spec_payload,
            dataset_payload=dataset_payload,
            stage="proxy",
            request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
            chars_per_token=4.0,
            expected_output_tokens=80,
            max_output_tokens=300,
            input_rate_per_1m=0.75,
            output_rate_per_1m=4.5,
            generated_at="2026-04-24T12:00:00Z",
        )

        self.assertEqual(report["summary"]["selected_request_count"], 1)
        self.assertGreater(report["summary"]["estimated_input_tokens"], 0)
        self.assertEqual(report["summary"]["expected_output_tokens"], 80)
        self.assertEqual(report["summary"]["max_output_tokens"], 300)
        self.assertIn("estimated_cost_expected", report["summary"])
        self.assertIn("estimated_cost_ceiling", report["summary"])
        self.assertEqual(
            report["request_rows"][0]["request_id"],
            "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
        )

    def test_render_prompt_cost_estimate_markdown_includes_request_table(self) -> None:
        markdown = render_prompt_cost_estimate_markdown(
            {
                "status": "ok",
                "generated_at": "2026-04-24T12:00:00Z",
                "queue_id": "queue-v10",
                "prompt_spec_id": "spec-v10",
                "prompt_version": "semantic_prompt_bakeoff_v1",
                "stage": "proxy",
                "selected_model_id": "gpt-5.4-mini",
                "input_token_heuristic": "ceil(characters / 4.0)",
                "summary": {
                    "selected_request_count": 1,
                    "estimated_input_tokens": 500,
                    "expected_output_tokens": 80,
                    "max_output_tokens": 300,
                    "estimated_cost_expected": 0.001,
                    "estimated_cost_ceiling": 0.002,
                },
                "rate_info": {
                    "input_rate_per_1m": 0.75,
                    "output_rate_per_1m": 4.5,
                },
                "request_rows": [
                    {
                        "request_id": "req-1",
                        "prompt_slot": "cue_contrastive_general_v1",
                        "estimated_input_tokens": 500,
                        "expected_output_tokens": 80,
                        "max_output_tokens": 300,
                    }
                ],
            }
        )

        self.assertIn("Semantic LLM Prompt Cost Estimate", markdown)
        self.assertIn("req-1", markdown)
        self.assertIn("Estimated cost (expected)", markdown)


def _sample_prompt_inputs() -> (
    tuple[
        dict[str, object],
        dict[str, object],
        dict[str, object],
        dict[str, object],
        dict[str, object],
    ]
):
    queue_payload = {
        "queue_id": "semantic_prompt_bakeoff_en_es_v10",
        "families": [
            {
                "family_id": "en-es:sentence-veto:plant:planta",
                "likely_bucket": "needs_cue_data",
                "primary_prompt_slot": "cue_contrastive_general_v1",
                "notes": ["Calibration family."],
            }
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
        "spec_id": "semantic_prompt_spec_en_es_v10",
        "pair": "en-es",
        "prompt_version": "semantic_prompt_bakeoff_v1",
        "stage_defaults": {
            "proxy": {"model_id": "gpt-5.4-mini", "temperature": 0.2},
            "target": {"model_id": "gpt-5.4", "temperature": 0.2},
        },
        "slots": [
            {
                "prompt_slot": "cue_contrastive_general_v1",
                "status": "active",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "system_prompt": "System prompt.",
                "user_prompt_template": (
                    "Return a JSON object with exactly one key `items`. "
                    "Copy `row_id` {row_id}, `trigger` {trigger}, `active_target` {active_target}, "
                    "`candidate_target` {candidate_target}, `candidate_pos` {candidate_pos}, "
                    "`prompt_slot` {prompt_slot}, `input_ref` {input_ref}. "
                    "Metadata family {family_id}, active {active_sense_id}, candidate {candidate_sense_id}, "
                    "stage {stage}, archetype {family_archetype}. "
                    "Active label {active_sense_label}, gloss {active_gloss_text}. "
                    "Candidate label {candidate_sense_label}, gloss {candidate_gloss_text}. "
                    "Notes {family_notes}. Return JSON only."
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
                    "sense_id": "en-es:sentence-veto:plant:planta:active",
                    "target_lemma": "planta",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "living plant",
                        "gloss_text": "living organism that grows in soil or water",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "en-es:sentence-veto:plant:fabrica:shadow",
                        "target_lemma": "fábrica",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "industrial plant",
                            "gloss_text": "factory where goods are manufactured",
                        },
                    }
                ],
            }
        ]
    }
    return (
        queue_payload,
        slot_manifest_payload,
        family_inventory_payload,
        prompt_spec_payload,
        dataset_payload,
    )


if __name__ == "__main__":
    unittest.main()
