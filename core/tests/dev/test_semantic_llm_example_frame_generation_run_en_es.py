from __future__ import annotations

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

from semantic_example_frame_batch_merge_en_es import (  # noqa: E402
    build_merged_example_frame_batch_report,
    render_merged_example_frame_batch_markdown,
)
from semantic_llm_example_frame_generation_run_en_es import (  # noqa: E402
    build_example_frame_execution_safety_report,
    build_example_frame_generation_run_bundle,
    render_example_frame_generation_run_markdown,
    write_example_frame_generation_run_bundle,
)


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
    def __init__(self, *, response_id: str, output_text: str) -> None:
        self.id = response_id
        self.output_text = output_text

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        if mode != "json":
            raise AssertionError(f"Unexpected model_dump mode {mode!r}")
        return {
            "id": self.id,
            "status": "completed",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 12,
                "output_tokens_details": {"reasoning_tokens": 0},
            },
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": self.output_text}],
                }
            ],
        }


class SemanticLlmExampleFrameGenerationRunTests(unittest.TestCase):
    def test_replay_like_execution_normalizes_accepted_rows(self) -> None:
        client = _FakeResponsesClient(
            [
                _FakeResponse(
                    response_id="resp_shadow",
                    output_text='{"items":[{"evidence_text":"They check every invoice before filing it.","confidence":0.8}]}',
                ),
                _FakeResponse(
                    response_id="resp_phrase",
                    output_text='{"items":[{"evidence_text":"Please check in before the meeting starts."}]}',
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_example_frame_generation_run_bundle(
                plan_payload=_plan_payload(),
                responses_client=client,
                batch_dir=Path(tmpdir) / "batches",
                execution_mode="replay",
                replay_source="fixture.json",
                generated_at="2026-04-25T14:00:00Z",
            )

        report = bundle["report"]
        normalized = bundle["normalized_batch"]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["accepted_item_count"], 2)
        self.assertEqual(report["summary"]["normalized_row_count"], 2)
        self.assertEqual(normalized["source_id"], "llm_example_frame_missing_rows")
        self.assertEqual(normalized["rows"][0]["relation_type"], "shadow_candidate")
        self.assertEqual(normalized["rows"][1]["relation_type"], "phrase_control_example")
        self.assertIn("phrase_containment", normalized["rows"][1]["roles"])
        self.assertFalse(normalized["rows"][1]["runtime_publishable"])

        markdown = render_example_frame_generation_run_markdown(report)
        self.assertIn("LLM Example-Frame Generation Run", markdown)
        self.assertIn("They check every invoice", markdown)

    def test_write_bundle_and_merge_with_reverse_aux_base(self) -> None:
        client = _FakeResponsesClient(
            [
                _FakeResponse(
                    response_id="resp_shadow",
                    output_text='{"items":[{"evidence_text":"They check every invoice before filing it."}]}',
                ),
                _FakeResponse(
                    response_id="resp_phrase",
                    output_text='{"items":[{"evidence_text":"Please check in before the meeting starts."}]}',
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            bundle = build_example_frame_generation_run_bundle(
                plan_payload=_plan_payload(),
                responses_client=client,
                batch_dir=tmp_path / "batches",
                execution_mode="replay",
                replay_source="fixture.json",
                generated_at="2026-04-25T14:00:00Z",
            )
            write_example_frame_generation_run_bundle(
                bundle=bundle,
                json_out=tmp_path / "summary.json",
                markdown_out=tmp_path / "summary.md",
            )
            self.assertTrue(Path(bundle["raw_response_bundle_path"]).exists())
            self.assertTrue(Path(bundle["normalized_batch_path"]).exists())

            merge_report = build_merged_example_frame_batch_report(
                base_batch_payload=_base_batch_payload(),
                add_batch_payloads=[bundle["normalized_batch"]],
                generated_at="2026-04-25T14:05:00Z",
            )

        merged = merge_report["merged_batch"]
        self.assertEqual(merged["row_count"], 3)
        self.assertEqual(merge_report["summary"]["family_count"], 1)
        self.assertEqual(
            merge_report["summary"]["relation_counts"],
            {
                "anchor_cue": 1,
                "shadow_candidate": 1,
                "phrase_control_example": 1,
            },
        )
        self.assertEqual(merge_report["component_batches"][0]["accepted_row_count"], 1)
        self.assertEqual(merge_report["component_batches"][1]["accepted_row_count"], 2)
        self.assertIn(
            "Example-Frame Batch Merge", render_merged_example_frame_batch_markdown(merge_report)
        )

    def test_safety_report_counts_selected_rows_and_cost(self) -> None:
        report = build_example_frame_execution_safety_report(
            plan_payload=_plan_payload(),
            input_rate_per_1m=0.15,
            output_rate_per_1m=0.6,
            generated_at="2026-04-25T14:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(summary["selected_request_count"], 2)
        self.assertGreater(summary["estimated_input_tokens"], 0)
        self.assertIn("estimated_cost_ceiling", summary)


def _plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "base_batch_id": "base",
        "source_id": "llm_example_frame_missing_rows",
        "prompt_version": "example-frame-missing-rows-v1",
        "selected_model_id": "gpt-5.4-mini",
        "selected_temperature": 0.2,
        "required_family_source": "queue",
        "request_rows": [
            _request_row(
                request_id="en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow",
                relation_type="shadow_candidate",
                roles=["discrimination"],
                candidate_target="revisar",
                candidate_pos="verb",
                generation_target="shadow_example",
            ),
            _request_row(
                request_id="en-es:example-frame-missing:phrase-control:fam-check",
                relation_type="phrase_control_example",
                roles=["discrimination", "phrase_containment"],
                candidate_target="phrase_control",
                candidate_pos="phrase_control",
                generation_target="phrase_control_example",
            ),
        ],
    }


def _request_row(
    *,
    request_id: str,
    relation_type: str,
    roles: list[str],
    candidate_target: str,
    candidate_pos: str,
    generation_target: str,
) -> dict[str, object]:
    return {
        "request_id": request_id,
        "prompt_slot": generation_target,
        "family_id": "fam:check",
        "trigger": "check",
        "active_target": "cheque",
        "candidate_target": candidate_target,
        "candidate_pos": candidate_pos,
        "relation_type": relation_type,
        "roles": roles,
        "model_id": "gpt-5.4-mini",
        "temperature": 0.2,
        "system_prompt": "Return JSON only.",
        "user_prompt": "English trigger: check\nReturn one original example.",
        "expected_row_preview": {
            "row_id": f"fam-check:{generation_target}",
            "relation_type": relation_type,
            "roles": roles,
            "trigger": "check",
            "active_target": "cheque",
            "candidate_target": candidate_target,
            "candidate_pos": candidate_pos,
            "prompt_slot": generation_target,
            "input_ref": request_id,
            "review_state": "unreviewed",
            "promotion_state": "proposed",
            "runtime_publishable": False,
            "metadata": {
                "family_id": "fam:check",
                "active_sense_id": "fam:check:cheque:active",
                "candidate_sense_id": "fam:check:revisar:shadow"
                if relation_type == "shadow_candidate"
                else "",
                "generation_target": generation_target,
                "source_gap": generation_target,
            },
        },
    }


def _base_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "base",
        "pair": "en-es",
        "source_type": "external",
        "source_id": "reverse_aux_example_frames",
        "source_family": "installed_translation_pack",
        "roles": ["discrimination"],
        "rows": [
            {
                "row_id": "base-active",
                "source_id": "reverse_aux_example_frames",
                "relation_type": "anchor_cue",
                "roles": ["cue_generation", "discrimination"],
                "trigger": "check",
                "active_target": "cheque",
                "candidate_target": "cheque",
                "evidence_text": "written payment instruction",
                "runtime_publishable": False,
                "metadata": {"family_id": "fam:check"},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
