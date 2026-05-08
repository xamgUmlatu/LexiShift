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
from semantic_veto_evidence_gap_generation_run_en_es import (  # noqa: E402
    build_evidence_gap_generation_execution_safety_report,
    build_evidence_gap_generation_run_bundle,
    render_evidence_gap_generation_run_markdown,
    write_evidence_gap_generation_run_bundle,
)


class SemanticVetoEvidenceGapGenerationRunTests(unittest.TestCase):
    def test_replay_run_accepts_slot_response_and_admission_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = build_evidence_gap_generation_run_bundle(
                request_payload=_request_payload(),
                responses_client=_ReplayResponsesClient(
                    {
                        "requests": [
                            {
                                "request_id": "pilot:req:active",
                                "response_id": "resp_001",
                                "output_text": json.dumps(_active_response()),
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
                generated_at="2026-05-08T00:00:00Z",
                max_requests=1,
            )

            report = bundle["report"]
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["summary"]["accepted_response_count"], 1)
            self.assertEqual(report["summary"]["accepted_generated_item_count"], 2)
            self.assertEqual(report["admission_preview"]["status"], "ok")
            self.assertEqual(report["admission_preview"]["admitted_item_count"], 2)
            self.assertEqual(
                bundle["generated_responses_payload"]["selected_request_ids"],
                ["pilot:req:active"],
            )

            markdown = render_evidence_gap_generation_run_markdown(report)
            self.assertIn("Semantic Veto Evidence-Gap Generation Run", markdown)
            self.assertIn("The bank approved the loan", markdown)

            write_evidence_gap_generation_run_bundle(
                bundle=bundle,
                json_out=Path(tmp) / "summary.json",
                markdown_out=Path(tmp) / "summary.md",
                generated_responses_out=Path(tmp) / "generated_responses.json",
            )
            self.assertTrue((Path(tmp) / "summary.json").exists())
            self.assertTrue((Path(tmp) / "generated_responses.json").exists())

    def test_replay_run_rejects_wrong_request_id_before_admission(self) -> None:
        bad_response = _active_response()
        bad_response["request_id"] = "wrong"
        bundle = build_evidence_gap_generation_run_bundle(
            request_payload=_request_payload(),
            responses_client=_ReplayResponsesClient(
                {
                    "requests": [
                        {
                            "request_id": "pilot:req:active",
                            "output_text": json.dumps(bad_response),
                        }
                    ]
                }
            ),
            batch_dir=Path("unused"),
            execution_mode="replay",
            generated_at="2026-05-08T00:00:00Z",
            max_requests=1,
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["summary"]["invalid_output_count"], 1)
        self.assertIn("request_id did not match", report["request_rows"][0]["error_message"])

    def test_replay_run_accepts_honest_no_competitor_marker(self) -> None:
        bundle = build_evidence_gap_generation_run_bundle(
            request_payload=_shadow_request_payload(),
            responses_client=_ReplayResponsesClient(
                {
                    "requests": [
                        {
                            "request_id": "pilot:req:shadow",
                            "output_text": json.dumps(
                                {
                                    "request_id": "pilot:req:shadow",
                                    "family_id": "family:bank:banco",
                                    "slot_id": "slot:shadow",
                                    "slot_type": "shadow_or_competitor_evidence_probe",
                                    "source_phrase": "bank",
                                    "target_lemma": "",
                                    "unable_to_find_distinct_competitor": True,
                                    "no_distinct_competitor_reason": (
                                        "No clearly distinct competitor was found."
                                    ),
                                    "items": [],
                                }
                            ),
                        }
                    ]
                }
            ),
            batch_dir=Path("unused"),
            execution_mode="replay",
            generated_at="2026-05-08T00:00:00Z",
            max_requests=1,
        )

        report = bundle["report"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["accepted_response_count"], 1)
        self.assertEqual(report["summary"]["accepted_generated_item_count"], 0)
        self.assertEqual(report["admission_preview"]["status"], "ok")
        self.assertEqual(report["admission_preview"]["coverage_shortfall_count"], 0)

    def test_safety_report_estimates_selected_request_cost(self) -> None:
        report = build_evidence_gap_generation_execution_safety_report(
            request_payload=_request_payload(),
            max_requests=1,
            input_rate_per_1m=1.0,
            output_rate_per_1m=2.0,
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["summary"]["selected_request_count"], 1)
        self.assertGreater(report["summary"]["estimated_input_tokens"], 0)
        self.assertIn("estimated_cost_ceiling", report["summary"])


def _request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "pilot": {
            "pilot_id": "semantic_veto_evidence_gap_control_pilot_en_es_v1",
            "prompt_id": "semantic_veto_evidence_gap_generation_v1",
            "request_kind": "semantic_veto_evidence_gap_generation",
        },
        "requests": [
            {
                "request_id": "pilot:req:active",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "arm_rank": 1,
                "global_need_rank": 1,
                "predicted_need": 0.9,
                "slot_id": "slot:active",
                "slot_type": "active_evidence_expansion",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "slot_target_lemma": "banco",
                "known_shadow_targets": ["orilla"],
                "requested_items": 2,
                "prompt_text": "Return a JSON response with two bank examples.",
            }
        ],
    }


def _shadow_request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "pilot": {
            "pilot_id": "semantic_veto_evidence_gap_control_pilot_en_es_v1",
            "prompt_id": "semantic_veto_evidence_gap_generation_v1",
            "request_kind": "semantic_veto_evidence_gap_generation",
        },
        "requests": [
            {
                "request_id": "pilot:req:shadow",
                "family_id": "family:bank:banco",
                "pilot_arm": "high_need",
                "arm_rank": 1,
                "global_need_rank": 1,
                "predicted_need": 0.9,
                "slot_id": "slot:shadow",
                "slot_type": "shadow_or_competitor_evidence_probe",
                "trigger": "bank",
                "active_target_lemma": "banco",
                "slot_target_lemma": "",
                "known_shadow_targets": ["orilla"],
                "requested_items": 2,
                "prompt_text": "Return competitor evidence or an honest no-competitor marker.",
            }
        ],
    }


def _active_response() -> dict[str, object]:
    return {
        "request_id": "pilot:req:active",
        "family_id": "family:bank:banco",
        "slot_id": "slot:active",
        "slot_type": "active_evidence_expansion",
        "source_phrase": "bank",
        "target_lemma": "banco",
        "items": [
            {
                "sentence": "The bank approved the loan after reviewing the application.",
                "evidence_note": "Financial institution sense.",
            },
            {
                "sentence": "A small bank opened near the train station last month.",
                "evidence_note": "Financial institution sense.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
