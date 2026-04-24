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

from semantic_llm_example_frame_remediation_plan_en_es import (  # noqa: E402
    build_example_frame_remediation_plan,
    render_example_frame_remediation_plan_markdown,
)


class SemanticLlmExampleFrameRemediationPlanTests(unittest.TestCase):
    def test_builds_active_and_shadow_remediation_requests_without_case_text(self) -> None:
        report = build_example_frame_remediation_plan(
            dataset_payload=_dataset_payload(),
            required_family_payload=_queue_payload(),
            prototype_payload=_prototype_payload(),
            model_id="gpt-5.4-mini",
            generated_at="2026-04-25T16:00:00Z",
        )

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["source_id"], "llm_example_frame_residual_remediation")
        self.assertEqual(report["summary"]["request_count"], 2)
        self.assertEqual(
            report["summary"]["requests_by_generation_target"],
            {
                "remediation_active_example": 1,
                "remediation_shadow_example": 1,
            },
        )
        request_ids = [row["request_id"] for row in report["request_rows"]]
        self.assertTrue(all("example-frame-remediation" in value for value in request_ids))

        prompts = "\n".join(str(row["user_prompt"]) for row in report["request_rows"])
        self.assertNotIn("He signed the check before mailing the rent.", prompts)
        self.assertNotIn("Witnesses report heavy rain near the coast.", prompts)
        self.assertIn("finance", prompts)
        self.assertIn("communication", prompts)

        active = report["request_rows"][0]
        shadow = report["request_rows"][1]
        self.assertEqual(active["prompt_slot"], "remediation_active_example")
        self.assertEqual(shadow["prompt_slot"], "remediation_shadow_example")
        self.assertNotIn(":missing:v1", active["expected_row_preview"]["row_id"])
        self.assertIn(
            ":remediation-active-001:v1",
            active["expected_row_preview"]["row_id"],
        )
        self.assertIn(
            ":remediation-shadow-003:v1",
            shadow["expected_row_preview"]["row_id"],
        )
        self.assertEqual(
            shadow["expected_row_preview"]["metadata"]["candidate_sense_id"],
            "fam:report:shadow",
        )

        markdown = render_example_frame_remediation_plan_markdown(report)
        self.assertIn("Example-Frame Remediation Plan", markdown)
        self.assertIn("false_abstain_active_example_gap", markdown)
        self.assertIn("harmful_replace_shadow_example_gap", markdown)


def _queue_payload() -> dict[str, object]:
    return {
        "queue_id": "semantic_prompt_bakeoff_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "role": "target",
                "likely_bucket": "needs_cue_data",
            },
            {
                "family_id": "fam:report",
                "trigger": "report",
                "role": "target",
                "likely_bucket": "needs_shadow_data",
            },
        ],
    }


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_test",
        "families": [
            _family(
                family_id="fam:check",
                trigger="check",
                active_target="cheque",
                active_sense_id="fam:check:active",
                active_label="bank check",
                active_gloss="written payment instrument",
                shadow_target="revisar",
                shadow_sense_id="fam:check:shadow",
                shadow_label="inspect",
                shadow_gloss="look over or verify",
            ),
            _family(
                family_id="fam:report",
                trigger="report",
                active_target="informe",
                active_sense_id="fam:report:active",
                active_label="written report",
                active_gloss="document describing facts",
                shadow_target="informar",
                shadow_sense_id="fam:report:shadow",
                shadow_label="to report",
                shadow_gloss="communicate or state information",
            ),
        ],
    }


def _family(
    *,
    family_id: str,
    trigger: str,
    active_target: str,
    active_sense_id: str,
    active_label: str,
    active_gloss: str,
    shadow_target: str,
    shadow_sense_id: str,
    shadow_label: str,
    shadow_gloss: str,
) -> dict[str, object]:
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {
            "sense_id": active_sense_id,
            "target_lemma": active_target,
            "canonical_pos": "noun",
            "evidence_views": {
                "sense_label": active_label,
                "gloss_text": active_gloss,
            },
        },
        "shadows": [
            {
                "sense_id": shadow_sense_id,
                "target_lemma": shadow_target,
                "canonical_pos": "verb",
                "evidence_views": {
                    "sense_label": shadow_label,
                    "gloss_text": shadow_gloss,
                },
            }
        ],
        "cases": [],
    }


def _prototype_payload() -> dict[str, object]:
    return {
        "configurations": [
            {
                "config_id": "prototype_reviewed_examples_phrase_containment_guard",
                "row_results": [
                    {
                        "case_id": "check:001",
                        "family_id": "fam:check",
                        "gold_decision": "replace",
                        "gold_winner": "fam:check:active",
                        "predicted_decision": "abstain",
                        "slice_tags": ["finance", "cross_pos"],
                        "sentence": "He signed the check before mailing the rent.",
                    },
                    {
                        "case_id": "report:003",
                        "family_id": "fam:report",
                        "gold_decision": "abstain",
                        "gold_winner": "fam:report:shadow",
                        "predicted_decision": "replace",
                        "slice_tags": ["communication", "verb", "cross_pos"],
                        "sentence": "Witnesses report heavy rain near the coast.",
                    },
                ],
            }
        ]
    }


if __name__ == "__main__":
    unittest.main()
