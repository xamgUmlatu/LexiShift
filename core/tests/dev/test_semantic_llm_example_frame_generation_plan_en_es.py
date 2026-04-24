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

from semantic_llm_example_frame_generation_plan_en_es import (  # noqa: E402
    build_example_frame_generation_plan,
    render_example_frame_generation_plan_markdown,
)


class SemanticLlmExampleFrameGenerationPlanTests(unittest.TestCase):
    def test_builds_only_missing_rows_without_reviewed_or_translation_leakage(self) -> None:
        report = build_example_frame_generation_plan(
            dataset_payload=_dataset_payload(),
            required_family_payload=_queue_payload(),
            base_evidence_batch_payload=_base_batch_payload(),
            generated_at="2026-04-25T13:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(summary["request_count"], 4)
        self.assertEqual(summary["family_count"], 2)
        self.assertEqual(
            summary["requests_by_generation_target"],
            {
                "shadow_example": 1,
                "phrase_control_example": 2,
                "active_example": 1,
            },
        )
        self.assertEqual(
            [row["request_id"] for row in report["request_rows"]],
            [
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow",
                "en-es:example-frame-missing:phrase-control:fam-check",
                "en-es:example-frame-missing:active:fam-play",
                "en-es:example-frame-missing:phrase-control:fam-play",
            ],
        )

        prompts = "\n".join(str(row["user_prompt"]) for row in report["request_rows"])
        self.assertIn("Queue context:", prompts)
        self.assertIn("archetype: cross_pos", prompts)
        self.assertIn("competing sense 1", prompts)
        for leaked_text in (
            "cheque",
            "revisar",
            "obra",
            "jugar",
            "She signed the check after lunch.",
            "They will check the door later.",
            "The play opened downtown.",
        ):
            self.assertNotIn(leaked_text, prompts)

        phrase_request = report["request_rows"][1]
        phrase_preview = phrase_request["expected_row_preview"]
        self.assertEqual(phrase_preview["relation_type"], "phrase_control_example")
        self.assertEqual(phrase_preview["roles"], ["discrimination", "phrase_containment"])
        self.assertFalse(phrase_preview["runtime_publishable"])
        self.assertEqual(phrase_preview["metadata"]["queue_role"], "target")
        self.assertEqual(phrase_preview["metadata"]["gold_decision"], "abstain")

        markdown = render_example_frame_generation_plan_markdown(report)
        self.assertIn("LLM Example-Frame Generation Plan", markdown)
        self.assertIn("Requests: `4`", markdown)


def _queue_payload() -> dict[str, object]:
    return {
        "queue_id": "semantic_prompt_bakeoff_en_es_v10",
        "pair": "en-es",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "role": "target",
                "archetype": "cross_pos",
                "likely_bucket": "needs_cue_data",
                "notes": ["Need a shadow and a phrase-control row."],
            },
            {
                "family_id": "fam:play",
                "trigger": "play",
                "role": "negative_control",
                "archetype": "phrase_leak_control",
                "likely_bucket": "needs_phrase_parsing_fix",
                "notes": ["Keep as a phrase-sensitive guardrail."],
            },
        ],
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_v10",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "active": {
                    "sense_id": "fam:check:cheque:active",
                    "target_lemma": "cheque",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "written payment instrument",
                        "gloss_text": "bank document used to pay money",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:check:revisar:shadow",
                        "target_lemma": "revisar",
                        "canonical_pos": "verb",
                        "evidence_views": {
                            "sense_label": "inspect or verify",
                            "gloss_text": "look over something carefully",
                        },
                    }
                ],
                "cases": [
                    {"sentence": "She signed the check after lunch."},
                    {"sentence": "They will check the door later."},
                ],
            },
            {
                "family_id": "fam:play",
                "trigger": "play",
                "active": {
                    "sense_id": "fam:play:obra:active",
                    "target_lemma": "obra",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "theatrical drama",
                        "gloss_text": "stage work performed by actors",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:play:jugar:shadow",
                        "target_lemma": "jugar",
                        "canonical_pos": "verb",
                        "evidence_views": {
                            "sense_label": "participate in a game",
                            "gloss_text": "take part in a sport or game",
                        },
                    }
                ],
                "cases": [
                    {"sentence": "The play opened downtown."},
                ],
            },
        ],
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
        "rows": [
            _normalized_row(
                row_id="check-active",
                family_id="fam:check",
                relation_type="anchor_cue",
                trigger="check",
                active_target="cheque",
                candidate_target="cheque",
            ),
            _normalized_row(
                row_id="play-shadow",
                family_id="fam:play",
                relation_type="shadow_candidate",
                trigger="play",
                active_target="obra",
                candidate_target="jugar",
            ),
        ],
    }


def _normalized_row(
    *,
    row_id: str,
    family_id: str,
    relation_type: str,
    trigger: str,
    active_target: str,
    candidate_target: str,
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "relation_type": relation_type,
        "roles": ["discrimination"],
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "evidence_text": "existing evidence",
        "runtime_publishable": False,
        "metadata": {"family_id": family_id},
    }


if __name__ == "__main__":
    unittest.main()
