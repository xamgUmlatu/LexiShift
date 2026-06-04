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

from semantic_llm_prompt_bakeoff_en_es import _ReplayResponsesClient  # noqa: E402
from semantic_veto_llm_pilot_generation_run_en_es import (  # noqa: E402
    build_semantic_veto_llm_pilot_execution_safety_report,
    build_semantic_veto_llm_pilot_generation_run_bundle,
    render_generation_run_markdown,
    write_semantic_veto_llm_pilot_generation_run_bundle,
)


class SemanticVetoLlmPilotGenerationRunTests(unittest.TestCase):
    def test_replay_run_accepts_generated_eval_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient(
                    {
                        "requests": [
                            {
                                "request_id": "req:bank:positive:001",
                                "response_id": "resp_001",
                                "output_text": json.dumps(_generated_row()),
                                "usage": {
                                    "input_tokens": 100,
                                    "output_tokens": 80,
                                    "output_tokens_details": {"reasoning_tokens": 0},
                                },
                            }
                        ]
                    }
                ),
                batch_dir=Path(tmp),
                execution_mode="replay",
                replay_source="fixture",
                generated_at="2026-05-05T00:00:00Z",
            )

            report = bundle["report"]
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["summary"]["accepted_row_count"], 1)
            self.assertEqual(report["summary"]["input_tokens"], 100)
            self.assertEqual(bundle["generated_rows_payload"]["rows"][0]["row_id"], "row:bank:001")
            self.assertEqual(
                bundle["generated_rows_payload"]["selected_expected_row_ids"],
                ["row:bank:001"],
            )

            markdown = render_generation_run_markdown(report)
            self.assertIn("Semantic Veto LLM Pilot Generation Run", markdown)
            self.assertIn("The bank approved the loan yesterday.", markdown)

            write_semantic_veto_llm_pilot_generation_run_bundle(
                bundle=bundle,
                json_out=Path(tmp) / "summary.json",
                markdown_out=Path(tmp) / "summary.md",
                generated_rows_out=Path(tmp) / "generated_rows.json",
            )
            self.assertTrue((Path(tmp) / "summary.json").exists())
            self.assertTrue((Path(tmp) / "generated_rows.json").exists())

    def test_live_resume_restores_generated_rows_from_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient(
                    {
                        "requests": [
                            {
                                "request_id": "req:bank:positive:001",
                                "response_id": "resp_001",
                                "output_text": json.dumps(_generated_row()),
                            }
                        ]
                    }
                ),
                batch_dir=Path(tmp),
                execution_mode="live",
                run_id="resume-test",
                generated_at="2026-05-05T00:00:00Z",
            )
            self.assertEqual(first["report"]["summary"]["accepted_row_count"], 1)

            resumed = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient({"requests": []}),
                batch_dir=Path(tmp),
                execution_mode="live",
                run_id="resume-test",
                resume=True,
                generated_at="2026-05-05T00:00:00Z",
            )

            self.assertEqual(resumed["report"]["summary"]["accepted_row_count"], 1)
            self.assertEqual(len(resumed["generated_rows_payload"]["rows"]), 1)
            self.assertEqual(
                resumed["generated_rows_payload"]["rows"][0]["sentence"],
                "The bank approved the loan yesterday.",
            )

    def test_live_resume_can_retry_invalid_output_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_row = _generated_row()
            bad_row.pop("candidate_replacement")
            first = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient(
                    {
                        "requests": [
                            {
                                "request_id": "req:bank:positive:001",
                                "response_id": "resp_bad",
                                "output_text": json.dumps(bad_row),
                            }
                        ]
                    }
                ),
                batch_dir=Path(tmp),
                execution_mode="live",
                run_id="retry-test",
                generated_at="2026-05-05T00:00:00Z",
            )
            self.assertEqual(first["report"]["status"], "error")
            self.assertEqual(first["report"]["summary"]["invalid_output_count"], 1)

            retried = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient(
                    {
                        "requests": [
                            {
                                "request_id": "req:bank:positive:001",
                                "response_id": "resp_good",
                                "output_text": json.dumps(_generated_row()),
                            }
                        ]
                    }
                ),
                batch_dir=Path(tmp),
                execution_mode="live",
                run_id="retry-test",
                resume=True,
                retry_invalid_outputs=True,
                generated_at="2026-05-05T00:00:00Z",
            )

            self.assertEqual(retried["report"]["status"], "ok")
            self.assertEqual(retried["report"]["summary"]["accepted_row_count"], 1)
            self.assertEqual(retried["generated_rows_payload"]["rows"][0]["row_id"], "row:bank:001")

            restored = build_semantic_veto_llm_pilot_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient({"requests": []}),
                batch_dir=Path(tmp),
                execution_mode="live",
                run_id="retry-test",
                resume=True,
                generated_at="2026-05-05T00:00:00Z",
            )
            self.assertEqual(restored["report"]["status"], "ok")
            self.assertEqual(restored["report"]["summary"]["accepted_row_count"], 1)

    def test_rejects_output_with_wrong_row_id(self) -> None:
        bad_row = _generated_row()
        bad_row["row_id"] = "wrong"
        bundle = build_semantic_veto_llm_pilot_generation_run_bundle(
            request_payload=_request_payload(),
            responses_client=_ReplayResponsesClient(
                {
                    "requests": [
                        {
                            "request_id": "req:bank:positive:001",
                            "output_text": json.dumps(bad_row),
                        }
                    ]
                }
            ),
            batch_dir=Path("unused"),
            execution_mode="replay",
            generated_at="2026-05-05T00:00:00Z",
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["summary"]["invalid_output_count"], 1)
        self.assertIn("did not match expected", report["request_rows"][0]["error_message"])

    def test_safety_report_estimates_selected_request_cost(self) -> None:
        report = build_semantic_veto_llm_pilot_execution_safety_report(
            request_payload=_request_payload(),
            max_requests=1,
            input_rate_per_1m=1.0,
            output_rate_per_1m=2.0,
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["summary"]["selected_request_count"], 1)
        self.assertGreater(report["summary"]["estimated_input_tokens"], 0)
        self.assertIn("estimated_cost_ceiling", report["summary"])


def _request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "pilot": {
            "pilot_id": "semantic_veto_llm_pilot_en_es_v1",
            "prompt_id": "semantic_veto_eval_sentence_pilot_v1",
        },
        "requests": [
            {
                "request_id": "req:bank:positive:001",
                "expected_row_id": "row:bank:001",
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "active_sense": "financial institution",
                "pos": "noun",
                "gold_type": "positive_active",
                "gold_decision": "allow",
                "prompt_text": "Return a bank sentence as JSON.",
            }
        ],
    }


def _generated_row() -> dict[str, object]:
    return {
        "row_id": "row:bank:001",
        "family_id": "pilot:bank:banco",
        "trigger": "bank",
        "candidate_replacement": "banco",
        "sentence": "The bank approved the loan yesterday.",
        "gold_decision": "allow",
        "gold_type": "positive_active",
        "active_sense": "financial institution",
        "negative_sense": "",
        "no_winner_reason": "",
        "gold_reason": "The sentence refers to a financial institution.",
        "pos": "noun",
        "generator_id": "test-model",
        "prompt_id": "semantic_veto_eval_sentence_pilot_v1",
        "difficulty_tags": ["obvious"],
    }


if __name__ == "__main__":
    unittest.main()
