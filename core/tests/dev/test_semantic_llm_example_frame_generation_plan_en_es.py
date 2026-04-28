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
        self.assertEqual(summary["request_count"], 10)
        self.assertEqual(summary["family_count"], 2)
        self.assertEqual(summary["candidate_slot_count"], 2)
        self.assertEqual(summary["planned_semantic_candidate_count"], 10)
        self.assertEqual(summary["planned_phrase_candidate_count"], 0)
        self.assertEqual(
            summary["requests_by_generation_target"],
            {
                "shadow_example": 5,
                "active_example": 5,
            },
        )
        self.assertEqual(
            [row["request_id"] for row in report["request_rows"]],
            [
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow:candidate-01",
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow:candidate-02",
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow:candidate-03",
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow:candidate-04",
                "en-es:example-frame-missing:shadow:fam-check:fam-check-revisar-shadow:candidate-05",
                "en-es:example-frame-missing:active:fam-play:candidate-01",
                "en-es:example-frame-missing:active:fam-play:candidate-02",
                "en-es:example-frame-missing:active:fam-play:candidate-03",
                "en-es:example-frame-missing:active:fam-play:candidate-04",
                "en-es:example-frame-missing:active:fam-play:candidate-05",
            ],
        )
        self.assertEqual(
            summary["requests_by_candidate_strategy"],
            {"standard_semantic": 10},
        )

        prompts = "\n".join(str(row["user_prompt"]) for row in report["request_rows"])
        self.assertIn("Queue context:", prompts)
        self.assertIn("archetype: cross_pos", prompts)
        self.assertIn("competing sense 1", prompts)
        self.assertIn("Candidate attempt: 1 of 5.", prompts)
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

        first_preview = report["request_rows"][0]["expected_row_preview"]
        self.assertEqual(first_preview["metadata"]["candidate_index"], 1)
        self.assertEqual(first_preview["metadata"]["candidate_count"], 5)
        self.assertEqual(first_preview["metadata"]["candidate_strategy"], "standard_semantic")
        self.assertFalse(first_preview["runtime_publishable"])
        self.assertEqual(first_preview["metadata"]["queue_role"], "target")

        markdown = render_example_frame_generation_plan_markdown(report)
        self.assertIn("LLM Example-Frame Generation Plan", markdown)
        self.assertIn("Requests: `10`", markdown)
        self.assertIn("Generation targets: `active_example, shadow_example`", markdown)
        self.assertIn("Planned semantic candidates: `10`", markdown)

    def test_can_plan_active_shadow_coverage_without_phrase_rows(self) -> None:
        report = build_example_frame_generation_plan(
            dataset_payload=_dataset_payload(),
            required_family_payload=_queue_payload(),
            base_evidence_batch_payload=_base_batch_payload(),
            generation_targets=("active_example", "shadow_example"),
            semantic_candidates_per_row=1,
            generated_at="2026-04-25T13:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(report["generation_targets"], ["active_example", "shadow_example"])
        self.assertEqual(summary["request_count"], 2)
        self.assertEqual(summary["family_count"], 2)
        self.assertEqual(
            summary["requests_by_generation_target"],
            {
                "shadow_example": 1,
                "active_example": 1,
            },
        )
        self.assertEqual(
            [row["prompt_slot"] for row in report["request_rows"]],
            ["shadow_example", "active_example"],
        )
        self.assertNotIn(
            "phrase_control_example",
            {str(row.get("prompt_slot") or "") for row in report["request_rows"]},
        )

    def test_can_explicitly_plan_phrase_containment_rows(self) -> None:
        report = build_example_frame_generation_plan(
            dataset_payload=_dataset_payload(),
            required_family_payload=_queue_payload(),
            base_evidence_batch_payload=_base_batch_payload(),
            generation_targets=("phrase_control_example",),
            generated_at="2026-04-25T13:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(report["generation_targets"], ["phrase_control_example"])
        self.assertEqual(summary["request_count"], 2)
        self.assertEqual(summary["planned_semantic_candidate_count"], 0)
        self.assertEqual(summary["planned_phrase_candidate_count"], 2)
        phrase_request = report["request_rows"][0]
        phrase_preview = phrase_request["expected_row_preview"]
        self.assertEqual(phrase_preview["relation_type"], "phrase_control_example")
        self.assertEqual(phrase_preview["roles"], ["discrimination", "phrase_containment"])
        self.assertEqual(phrase_preview["metadata"]["candidate_strategy"], "phrase_containment")
        self.assertEqual(phrase_preview["metadata"]["gold_decision"], "abstain")

    def test_uses_hard_candidate_count_for_same_pos_semantic_rows(self) -> None:
        report = build_example_frame_generation_plan(
            dataset_payload=_same_pos_dataset_payload(),
            required_family_payload=_same_pos_queue_payload(),
            base_evidence_batch_payload=_same_pos_base_batch_payload(),
            generation_targets=("shadow_example",),
            semantic_candidates_per_row=2,
            hard_semantic_candidates_per_row=3,
            generated_at="2026-04-25T13:00:00Z",
        )

        summary = report["summary"]
        self.assertEqual(summary["request_count"], 3)
        self.assertEqual(
            summary["requests_by_candidate_strategy"],
            {"same_pos_hard_semantic": 3},
        )
        self.assertEqual(
            [row["candidate_index"] for row in report["request_rows"]],
            [1, 2, 3],
        )
        self.assertTrue(all(row["candidate_count"] == 3 for row in report["request_rows"]))
        self.assertIn(
            "candidate-03",
            report["request_rows"][-1]["request_id"],
        )

    def test_rejects_unknown_generation_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported generation_targets"):
            build_example_frame_generation_plan(
                dataset_payload=_dataset_payload(),
                required_family_payload=_queue_payload(),
                base_evidence_batch_payload=_base_batch_payload(),
                generation_targets=("active_example", "misspelled_target"),
                generated_at="2026-04-25T13:00:00Z",
            )


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


def _same_pos_queue_payload() -> dict[str, object]:
    return {
        "queue_id": "semantic_prompt_bakeoff_en_es_same_pos",
        "pair": "en-es",
        "families": [
            {
                "family_id": "fam:plant",
                "trigger": "plant",
                "role": "target",
                "archetype": "same_pos",
                "likely_bucket": "needs_cue_data",
            }
        ],
    }


def _same_pos_dataset_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_same_pos",
        "families": [
            {
                "family_id": "fam:plant",
                "trigger": "plant",
                "active": {
                    "sense_id": "fam:plant:planta:active",
                    "target_lemma": "planta",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "living organism with roots",
                        "gloss_text": "green organism that grows in soil",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:plant:fabrica:shadow",
                        "target_lemma": "fabrica",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "industrial facility",
                            "gloss_text": "factory or production site",
                        },
                    }
                ],
                "cases": [{"sentence": "Workers entered the plant before dawn."}],
            }
        ],
    }


def _same_pos_base_batch_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_version": "semantic_evidence_v1",
        "batch_id": "same-pos-base",
        "pair": "en-es",
        "source_type": "external",
        "source_id": "reverse_aux_example_frames",
        "source_family": "installed_translation_pack",
        "rows": [
            _normalized_row(
                row_id="plant-active",
                family_id="fam:plant",
                relation_type="anchor_cue",
                trigger="plant",
                active_target="planta",
                candidate_target="planta",
            )
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
