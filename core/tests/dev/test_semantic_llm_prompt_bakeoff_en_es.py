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

from semantic_llm_prompt_bakeoff_en_es import (  # noqa: E402
    _assert_live_safety_guards,
    _build_batch_id,
    _ReplayResponsesClient,
    _slug,
    build_prompt_execution_safety_report,
    build_prompt_bakeoff_bundle,
    write_prompt_bakeoff_bundle,
)
from semantic_llm_prompt_reporting import render_prompt_bakeoff_markdown  # noqa: E402


class _FakeResponsesClient:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)

    def create(self, **_: object) -> object:
        if not self._responses:
            raise AssertionError("No fake responses left")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeResponse:
    def __init__(
        self,
        *,
        response_id: str,
        output_text: str,
        usage: dict[str, object] | None = None,
    ) -> None:
        self.id = response_id
        self.output_text = output_text
        self._usage = usage or {
            "input_tokens": 120,
            "output_tokens": 18,
            "output_tokens_details": {"reasoning_tokens": 0},
        }

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        self.assert_mode(mode)
        return {
            "id": self.id,
            "status": "completed",
            "usage": self._usage,
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": self.output_text}],
                }
            ],
        }

    @staticmethod
    def assert_mode(mode: str) -> None:
        if mode != "json":
            raise AssertionError(f"Unexpected model_dump mode {mode!r}")


class TestSemanticLlmPromptBakeoffEnEs(unittest.TestCase):
    def test_build_prompt_bakeoff_bundle_keeps_valid_row_and_normalizes_it(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        client = _FakeResponsesClient(
            [
                _FakeResponse(
                    response_id="resp_123",
                    output_text=(
                        '{"items":[{"evidence_text":"living organism with leaves or roots",'
                        '"confidence":0.82}]}'
                    ),
                )
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=client,
                batch_dir=Path(tmpdir) / "batches",
                request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                generated_at="2026-04-24T12:00:00Z",
            )

        report = bundle["report"]
        intake_batch = bundle["intake_batch"]
        normalized_batch = bundle["normalized_batch"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["accepted_item_count"], 1)
        self.assertEqual(report["summary"]["normalized_row_count"], 1)
        self.assertEqual(
            intake_batch["items"][0]["raw_response_ref"].split("#")[1],
            "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
        )
        self.assertEqual(normalized_batch["row_count"], 1)
        self.assertEqual(normalized_batch["rows"][0]["linkage_status"], "partially_linked")
        self.assertEqual(report["request_rows"][0]["status"], "accepted")
        self.assertEqual(
            report["request_rows"][0]["evidence_text"], "living organism with leaves or roots"
        )

    def test_build_prompt_bakeoff_bundle_rejects_malformed_model_row(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        client = _FakeResponsesClient(
            [
                _FakeResponse(
                    response_id="resp_bad",
                    output_text=(
                        '{"items":[{"evidence_text":"living organism with leaves or roots",'
                        '"extra_key":"should_fail"}]}'
                    ),
                )
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=client,
                batch_dir=Path(tmpdir) / "batches",
                request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                generated_at="2026-04-24T12:00:00Z",
            )

        report = bundle["report"]
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["summary"]["accepted_item_count"], 0)
        self.assertEqual(report["summary"]["invalid_output_count"], 1)
        self.assertIsNone(bundle["intake_batch"])
        self.assertIsNone(bundle["normalized_batch"])
        self.assertIn("unexpected item keys", report["request_rows"][0]["error_message"])

    def test_render_prompt_bakeoff_markdown_includes_request_outcome(self) -> None:
        markdown = render_prompt_bakeoff_markdown(
            {
                "status": "partial",
                "generated_at": "2026-04-24T12:00:00Z",
                "queue_id": "queue-v10",
                "prompt_spec_id": "spec-v10",
                "prompt_version": "semantic_prompt_bakeoff_v1",
                "stage": "proxy",
                "batch_id": "en-es:proxy:20260424T120000Z",
                "source_id": "queue-v10:proxy",
                "selected_model_id": "gpt-5.4-mini",
                "selected_temperature": 0.2,
                "summary": {
                    "selected_request_count": 2,
                    "accepted_item_count": 1,
                    "api_error_count": 0,
                    "invalid_output_count": 1,
                    "normalized_row_count": 1,
                    "input_tokens": 120,
                    "output_tokens": 18,
                },
                "artifacts": {
                    "raw_response_bundle_json": "docs/test_outputs/experiments/semantic_llm_prompt_batches/bundle.json",
                    "intake_batch_json": "docs/test_outputs/experiments/semantic_llm_prompt_batches/intake.json",
                    "normalized_batch_json": "docs/test_outputs/experiments/semantic_llm_prompt_batches/normalized.json",
                },
                "request_rows": [
                    {
                        "request_id": "req-1",
                        "prompt_slot": "cue_contrastive_general_v1",
                        "family_id": "en-es:sentence-veto:plant:planta",
                        "status": "accepted",
                        "evidence_text": "living organism with leaves or roots",
                    },
                    {
                        "request_id": "req-2",
                        "prompt_slot": "cue_cross_pos_frame_v1",
                        "family_id": "en-es:sentence-veto:check:cheque",
                        "status": "invalid_output",
                        "error_message": "ValueError: unexpected item keys",
                    },
                ],
            }
        )

        self.assertIn("Semantic LLM Prompt Bakeoff", markdown)
        self.assertIn("req-1", markdown)
        self.assertIn("living organism with leaves or roots", markdown)
        self.assertIn("unexpected item keys", markdown)

    def test_build_prompt_bakeoff_bundle_marks_replay_mode_and_counts_mixed_outcomes(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        queue_payload["families"].append(
            {
                "family_id": "en-es:sentence-veto:drink:bebida",
                "likely_bucket": "needs_cue_data",
                "primary_prompt_slot": "cue_contrastive_general_v1",
                "notes": ["Replay API error calibration family."],
            }
        )
        slot_manifest_payload["slots"][0]["target_family_ids"].append(
            "en-es:sentence-veto:drink:bebida"
        )
        family_inventory_payload["families"].append(
            {
                "family_id": "en-es:sentence-veto:drink:bebida",
                "bucket_evidence": ["Drink remains weak-active-support."],
            }
        )
        dataset_payload["families"].append(
            {
                "family_id": "en-es:sentence-veto:drink:bebida",
                "trigger": "drink",
                "active": {
                    "sense_id": "en-es:sentence-veto:drink:bebida:active",
                    "target_lemma": "bebida",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "drink noun",
                        "gloss_text": "liquid meant for drinking",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "en-es:sentence-veto:drink:beber:shadow",
                        "target_lemma": "beber",
                        "canonical_pos": "verb",
                        "evidence_views": {
                            "sense_label": "drink verb",
                            "gloss_text": "to consume a liquid",
                        },
                    }
                ],
            }
        )

        replay_client = _ReplayResponsesClient(
            {
                "requests": [
                    {
                        "request_id": "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
                        "response_id": "replay_resp_plant_ok",
                        "usage": {
                            "input_tokens": 101,
                            "output_tokens": 22,
                            "output_tokens_details": {"reasoning_tokens": 0},
                        },
                        "output_text": '{"items":[{"evidence_text":"living organism with leaves or roots","confidence":0.82}]}',
                    },
                    {
                        "request_id": "en-es:proxy:cue-contrastive-general-v1:drink:beber",
                        "error_type": "RuntimeError",
                        "error_message": "Replay induced API failure",
                    },
                ]
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=replay_client,
                batch_dir=Path(tmpdir) / "batches",
                request_ids=[
                    "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
                    "en-es:proxy:cue-contrastive-general-v1:drink:beber",
                ],
                generated_at="2026-04-24T12:00:00Z",
                execution_mode="replay",
                replay_source="docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json",
            )

        report = bundle["report"]
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["execution_mode"], "replay")
        self.assertTrue(str(report["batch_id"]).endswith(":replay"))
        self.assertEqual(report["summary"]["accepted_item_count"], 1)
        self.assertEqual(report["summary"]["api_error_count"], 1)
        self.assertEqual(report["summary"]["invalid_output_count"], 0)
        self.assertEqual(
            bundle["intake_batch"]["provenance"]["replay_source"],
            "docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json",
        )

    def test_write_prompt_bakeoff_bundle_persists_artifacts(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        client = _FakeResponsesClient(
            [
                _FakeResponse(
                    response_id="resp_write",
                    output_text=(
                        '{"items":[{"evidence_text":"living organism with leaves or roots",'
                        '"confidence":0.82}]}'
                    ),
                )
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=client,
                batch_dir=tmp_path / "batches",
                request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                generated_at="2026-04-24T12:00:00Z",
            )
            json_out = tmp_path / "summary.json"
            markdown_out = tmp_path / "summary.md"
            write_prompt_bakeoff_bundle(bundle=bundle, json_out=json_out, markdown_out=markdown_out)

            self.assertTrue((tmp_path / "batches").exists())
            self.assertTrue(Path(bundle["journal_path"]).exists())
            self.assertTrue(Path(bundle["raw_response_bundle_path"]).exists())
            self.assertTrue(Path(bundle["intake_batch_path"]).exists())
            self.assertTrue(Path(bundle["normalized_batch_path"]).exists())
            self.assertTrue(json_out.exists())
            self.assertTrue(markdown_out.exists())
            self.assertIn("Semantic LLM Prompt Bakeoff", markdown_out.read_text(encoding="utf-8"))
            summary_payload = json_out.read_text(encoding="utf-8")
            self.assertIn('"status": "ok"', summary_payload)
            self.assertIn('"execution_mode": "live"', summary_payload)

    def test_build_prompt_bakeoff_bundle_resume_reuses_completed_requests(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batches"
            first_client = _FakeResponsesClient(
                [
                    _FakeResponse(
                        response_id="resp_resume",
                        output_text=(
                            '{"items":[{"evidence_text":"living organism with leaves or roots",'
                            '"confidence":0.82}]}'
                        ),
                    )
                ]
            )
            first_bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=first_client,
                batch_dir=batch_dir,
                request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                generated_at="2026-04-24T12:00:00Z",
                run_id="resume-safe-run",
            )
            resumed_bundle = build_prompt_bakeoff_bundle(
                queue_payload=queue_payload,
                slot_manifest_payload=slot_manifest_payload,
                family_inventory_payload=family_inventory_payload,
                prompt_spec_payload=prompt_spec_payload,
                dataset_payload=dataset_payload,
                stage="proxy",
                responses_client=_FakeResponsesClient([]),
                batch_dir=batch_dir,
                request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                generated_at="2026-04-24T12:05:00Z",
                run_id="resume-safe-run",
                resume=True,
            )

            self.assertEqual(first_bundle["report"]["summary"]["accepted_item_count"], 1)
            self.assertEqual(resumed_bundle["report"]["summary"]["accepted_item_count"], 1)
            self.assertEqual(resumed_bundle["report"]["request_rows"][0]["status"], "accepted")
            self.assertTrue(Path(resumed_bundle["journal_path"]).exists())

    def test_build_prompt_bakeoff_bundle_resume_refuses_ambiguous_started_request(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batches"
            batch_id = _build_batch_id(
                pair="en-es",
                stage="proxy",
                generated_at="2026-04-24T12:00:00Z",
                execution_mode="live",
                run_id="ambiguous-run",
            )
            journal_path = batch_dir / f"{_slug(batch_id)}_journal.jsonl"
            journal_path.parent.mkdir(parents=True, exist_ok=True)
            journal_path.write_text(
                '{"schema_version":1,"event_type":"request_started","batch_id":"'
                + batch_id
                + '","generated_at":"2026-04-24T12:00:00Z","request_id":"en-es:proxy:cue-contrastive-general-v1:plant:fabrica","prompt_slot":"cue_contrastive_general_v1","family_id":"en-es:sentence-veto:plant:planta","model_id":"gpt-5.4-mini"}\n',
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as exc:
                build_prompt_bakeoff_bundle(
                    queue_payload=queue_payload,
                    slot_manifest_payload=slot_manifest_payload,
                    family_inventory_payload=family_inventory_payload,
                    prompt_spec_payload=prompt_spec_payload,
                    dataset_payload=dataset_payload,
                    stage="proxy",
                    responses_client=_FakeResponsesClient([]),
                    batch_dir=batch_dir,
                    request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
                    generated_at="2026-04-24T12:05:00Z",
                    run_id="ambiguous-run",
                    resume=True,
                )
            self.assertIn("started requests without recorded outcomes", str(exc.exception))

    def test_build_prompt_execution_safety_report_estimates_selected_live_slice(self) -> None:
        (
            queue_payload,
            slot_manifest_payload,
            family_inventory_payload,
            prompt_spec_payload,
            dataset_payload,
        ) = _sample_prompt_inputs()
        report = build_prompt_execution_safety_report(
            queue_payload=queue_payload,
            slot_manifest_payload=slot_manifest_payload,
            family_inventory_payload=family_inventory_payload,
            prompt_spec_payload=prompt_spec_payload,
            dataset_payload=dataset_payload,
            stage="proxy",
            request_ids=["en-es:proxy:cue-contrastive-general-v1:plant:fabrica"],
            max_requests=1,
            chars_per_token=4.0,
            expected_output_tokens=80,
            max_output_tokens=300,
            input_rate_per_1m=0.75,
            output_rate_per_1m=4.5,
            generated_at="2026-04-24T12:00:00Z",
        )

        self.assertEqual(report["summary"]["selected_request_count"], 1)
        self.assertGreater(report["summary"]["estimated_input_tokens"], 0)
        self.assertIn("estimated_cost_expected", report["summary"])
        self.assertIn("estimated_cost_ceiling", report["summary"])
        self.assertEqual(
            report["request_rows"][0]["request_id"],
            "en-es:proxy:cue-contrastive-general-v1:plant:fabrica",
        )

    def test_assert_live_safety_guards_rejects_count_mismatch(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            _assert_live_safety_guards(
                safety_report={
                    "summary": {
                        "selected_request_count": 2,
                        "estimated_cost_expected": 0.001,
                        "estimated_cost_ceiling": 0.002,
                    }
                },
                run_id="count-mismatch-run",
                require_selected_request_count=1,
                input_rate_per_1m=0.75,
                output_rate_per_1m=4.5,
                max_estimated_cost_usd=0.01,
                max_estimated_cost_ceiling_usd=0.02,
            )
        self.assertIn("selected_request_count=2", str(exc.exception))

    def test_assert_live_safety_guards_rejects_missing_ceiling_cap(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            _assert_live_safety_guards(
                safety_report={
                    "summary": {
                        "selected_request_count": 1,
                        "estimated_cost_expected": 0.001,
                        "estimated_cost_ceiling": 0.002,
                    }
                },
                run_id="missing-ceiling-run",
                require_selected_request_count=1,
                input_rate_per_1m=0.75,
                output_rate_per_1m=4.5,
                max_estimated_cost_usd=None,
                max_estimated_cost_ceiling_usd=None,
            )
        self.assertIn("max-estimated-cost-ceiling-usd", str(exc.exception))

    def test_assert_live_safety_guards_rejects_missing_run_id(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            _assert_live_safety_guards(
                safety_report={
                    "summary": {
                        "selected_request_count": 1,
                        "estimated_cost_expected": 0.001,
                        "estimated_cost_ceiling": 0.002,
                    }
                },
                run_id="",
                require_selected_request_count=1,
                input_rate_per_1m=0.75,
                output_rate_per_1m=4.5,
                max_estimated_cost_usd=0.01,
                max_estimated_cost_ceiling_usd=0.02,
            )
        self.assertIn("--run-id", str(exc.exception))


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
