from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SCRIPT_ROOT = os.path.join(PROJECT_ROOT, "scripts", "testing")
for candidate in (PROJECT_ROOT, SCRIPT_ROOT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_preflight_en_es import build_prompt_preflight_report  # noqa: E402
from semantic_llm_prompt_reporting import render_prompt_preflight_markdown  # noqa: E402


class TestSemanticLlmPromptPreflightEnEs(unittest.TestCase):
    def test_build_prompt_preflight_report_marks_local_env_blocked_when_key_hidden(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_rc = Path(tmpdir) / ".zshrc"
            shell_rc.write_text("# no key here\n", encoding="utf-8")
            try:
                report = build_prompt_preflight_report(
                    queue_payload=queue_payload,
                    slot_manifest_payload=slot_manifest_payload,
                    family_inventory_payload=family_inventory_payload,
                    prompt_spec_payload=prompt_spec_payload,
                    dataset_payload=dataset_payload,
                    stage="proxy",
                    batch_dir=Path(PROJECT_ROOT)
                    / "docs"
                    / "test_outputs"
                    / "experiments"
                    / "semantic_llm_prompt_batches",
                    shell_rc=shell_rc,
                    request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                    generated_at="2026-04-24T12:00:00Z",
                )
            finally:
                if original_key is not None:
                    os.environ["OPENAI_API_KEY"] = original_key

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["summary"]["current_shell_ready"])
        self.assertFalse(report["summary"]["sourced_shell_ready"])
        self.assertFalse(report["summary"]["local_env_ready"])
        self.assertTrue(report["summary"]["live_spend_guarded"])
        self.assertIn("--execute-live", report["live_command_example"])
        self.assertIn("--require-selected-request-count 1", report["live_command_example"])
        self.assertIn("--max-estimated-cost-ceiling-usd <USD_CAP>", report["live_command_example"])
        self.assertEqual(report["summary"]["selected_request_count"], 1)

    def test_build_prompt_preflight_report_marks_sourced_shell_ready_when_rc_has_key(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_rc = Path(tmpdir) / ".zshrc"
            shell_rc.write_text('export OPENAI_API_KEY="placeholder"\n', encoding="utf-8")
            try:
                report = build_prompt_preflight_report(
                    queue_payload=queue_payload,
                    slot_manifest_payload=slot_manifest_payload,
                    family_inventory_payload=family_inventory_payload,
                    prompt_spec_payload=prompt_spec_payload,
                    dataset_payload=dataset_payload,
                    stage="proxy",
                    batch_dir=Path(PROJECT_ROOT)
                    / "docs"
                    / "test_outputs"
                    / "experiments"
                    / "semantic_llm_prompt_batches",
                    shell_rc=shell_rc,
                    request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                    generated_at="2026-04-24T12:00:00Z",
                )
            finally:
                if original_key is not None:
                    os.environ["OPENAI_API_KEY"] = original_key

        self.assertEqual(report["status"], "sourced-shell-ready")
        self.assertFalse(report["summary"]["current_shell_ready"])
        self.assertTrue(report["summary"]["sourced_shell_ready"])
        self.assertTrue(report["summary"]["local_env_ready"])
        self.assertIn("--require-selected-request-count 1", report["live_command_example"])
        self.assertIn("--input-rate-per-1m <INPUT_RATE>", report["live_command_example"])

    def test_render_prompt_preflight_markdown_includes_env_and_request_table(self) -> None:
        markdown = render_prompt_preflight_markdown(
            {
                "status": "ready",
                "generated_at": "2026-04-24T12:00:00Z",
                "queue_id": "queue-v10",
                "prompt_spec_id": "spec-v10",
                "prompt_version": "semantic_prompt_bakeoff_v1",
                "stage": "proxy",
                "selected_model_id": "gpt-5.4-mini",
                "selected_temperature": 0.2,
                "summary": {
                    "selected_request_count": 2,
                    "selected_family_count": 2,
                    "selected_slot_count": 2,
                    "current_shell_ready": False,
                    "sourced_shell_ready": True,
                    "local_env_ready": True,
                    "live_spend_guarded": True,
                },
                "env_checks": [
                    {
                        "check_id": "current_python_openai_sdk_installed",
                        "status": "ok",
                        "notes": "Installed.",
                    }
                ],
                "planned_artifacts": {
                    "raw_response_bundle_json": "docs/test_outputs/experiments/raw.json",
                    "intake_batch_json": "docs/test_outputs/experiments/intake.json",
                    "normalized_batch_json": "docs/test_outputs/experiments/norm.json",
                },
                "request_rows": [
                    {
                        "request_id": "req-1",
                        "prompt_slot": "cue_contrastive_general_v1",
                        "family_id": "en-es:sentence-veto:plant:planta",
                        "trigger": "plant",
                        "active_target": "planta",
                        "candidate_target": "fábrica",
                    }
                ],
                "live_command_example": "PYTHONPATH=apps/gui/src:core .venv/bin/python scripts/testing/semantic_llm_prompt_bakeoff_en_es.py --stage proxy --execute-live --require-selected-request-count 1 --input-rate-per-1m <INPUT_RATE> --output-rate-per-1m <OUTPUT_RATE> --max-estimated-cost-ceiling-usd <USD_CAP>",
            }
        )

        self.assertIn("Semantic LLM Prompt Preflight", markdown)
        self.assertIn("openai_sdk_installed", markdown)
        self.assertIn("req-1", markdown)
        self.assertIn("--execute-live", markdown)


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
