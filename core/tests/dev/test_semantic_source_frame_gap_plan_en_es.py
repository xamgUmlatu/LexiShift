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

from semantic_source_frame_gap_plan_en_es import (  # noqa: E402
    build_source_frame_gap_plan,
    render_source_frame_gap_plan_markdown,
)
from semantic_llm_example_frame_generation_run_en_es import (  # noqa: E402
    build_example_frame_generation_run_bundle,
)
from semantic_llm_prompt_bakeoff_en_es import _ReplayResponsesClient  # noqa: E402


class SemanticSourceFrameGapPlanTests(unittest.TestCase):
    def test_plan_requests_only_missing_selector_ready_sense_slots(self) -> None:
        report = build_source_frame_gap_plan(
            dataset_payload=_tiny_dataset(),
            alignment_audit_payload=_tiny_alignment_audit(),
            standard_candidates_per_slot=2,
            hard_candidates_per_slot=3,
        )

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["summary"]["slot_count"], 2)
        self.assertEqual(report["summary"]["selector_ready_slot_count"], 1)
        self.assertEqual(report["summary"]["missing_slot_count"], 1)
        self.assertEqual(report["summary"]["request_count"], 3)
        self.assertEqual(report["summary"]["diversity_frame_count"], 3)
        self.assertEqual(report["prompt_version"], "aligned-sentence-frame-v2")

        request = report["request_rows"][0]
        self.assertEqual(request["generation_target"], "shadow_example")
        self.assertEqual(request["prompt_slot"], "shadow_example")
        self.assertEqual(request["model_id"], "gpt-5.4-mini")
        self.assertEqual(request["diversity_frame_id"], "specific_role_action")
        self.assertEqual(request["roles"], ["discrimination"])
        self.assertEqual(
            request["candidate_sense_id"],
            "en-es:sentence-veto:ball:baile:shadow",
        )
        self.assertEqual(
            [row["diversity_frame_id"] for row in report["request_rows"]],
            ["specific_role_action", "place_time_observation", "problem_resolution"],
        )
        expected = request["expected_row_preview"]
        self.assertEqual(expected["relation_type"], "shadow_candidate")
        self.assertEqual(expected["metadata"]["source_gap"], "selector_ready_sentence_frame")
        self.assertEqual(expected["metadata"]["diversity_frame_id"], "specific_role_action")
        self.assertIn("at least two useful words before", request["user_prompt"])
        self.assertIn("Diversity frame: `specific_role_action`", request["user_prompt"])
        self.assertNotIn("The goalkeeper punched the ball over the bar.", request["user_prompt"])

        markdown = render_source_frame_gap_plan_markdown(report)
        self.assertIn("Source Frame Gap Plan", markdown)
        self.assertIn("Planned candidate requests: `3`", markdown)
        self.assertIn("Candidate diversity frames: `3`", markdown)

    def test_plan_can_feed_existing_generation_runner(self) -> None:
        report = build_source_frame_gap_plan(
            dataset_payload=_tiny_dataset(),
            alignment_audit_payload=_tiny_alignment_audit(),
            standard_candidates_per_slot=1,
            hard_candidates_per_slot=1,
            model_id="fixture-model",
            temperature=0.1,
        )
        replay_payload = {
            "requests": [
                {
                    "request_id": report["request_rows"][0]["request_id"],
                    "output_text": json_items("They attended a formal ball in the old hall."),
                    "usage": {"input_tokens": 10, "output_tokens": 7},
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_example_frame_generation_run_bundle(
                plan_payload=report,
                responses_client=_ReplayResponsesClient(replay_payload),
                batch_dir=Path(tmpdir),
                execution_mode="replay",
                max_requests=1,
                generated_at="2026-04-29T00:00:00Z",
                run_id="frame-gap-fixture",
            )

        self.assertEqual(bundle["report"]["status"], "ok")
        self.assertEqual(bundle["report"]["summary"]["normalized_row_count"], 1)
        row = bundle["normalized_batch"]["rows"][0]
        self.assertEqual(row["source_id"], "llm_aligned_sentence_frame_rows")
        self.assertEqual(row["relation_type"], "shadow_candidate")
        self.assertEqual(row["metadata"]["source_gap"], "selector_ready_sentence_frame")


def _tiny_alignment_audit() -> dict[str, object]:
    return {
        "schema_version": 1,
        "audited_rows": [
            {
                "candidate_sense_id": "en-es:sentence-veto:ball:pelota:active",
                "selector_ready": True,
            },
            {
                "candidate_sense_id": "en-es:sentence-veto:ball:baile:shadow",
                "selector_ready": False,
            },
        ],
    }


def _tiny_dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "tiny",
        "families": [
            {
                "family_id": "en-es:sentence-veto:ball:pelota",
                "trigger": "ball",
                "active": {
                    "sense_id": "en-es:sentence-veto:ball:pelota:active",
                    "target_lemma": "pelota",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "ball used in games or sports",
                        "gloss_text": "object generally spherical and used in play",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "en-es:sentence-veto:ball:baile:shadow",
                        "target_lemma": "baile",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "formal dance event",
                            "gloss_text": "gala or social dance gathering",
                        },
                    }
                ],
                "cases": [
                    {
                        "case_id": "leakage-sentinel",
                        "sentence": "The goalkeeper punched the ball over the bar.",
                    }
                ],
            }
        ],
    }


def json_items(evidence_text: str) -> str:
    return json.dumps({"items": [{"evidence_text": evidence_text}]})


if __name__ == "__main__":
    unittest.main()
