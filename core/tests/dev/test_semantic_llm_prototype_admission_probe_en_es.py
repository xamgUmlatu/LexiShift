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

from semantic_llm_prototype_admission_probe_en_es import (  # noqa: E402
    build_prototype_admission_report,
    render_prototype_admission_markdown,
)
from semantic_llm_reviewed_example_frame_batch_en_es import (  # noqa: E402
    build_reviewed_example_frame_bundle,
)


class SemanticLlmPrototypeAdmissionProbeTests(unittest.TestCase):
    def test_prototype_admission_probe_preserves_binary_decision_contract(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            scorer_id="tfidf_cosine",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision_contract"], "binary_replace_or_abstain")
        self.assertFalse(report["runtime_publishable"])
        config_ids = {
            str(row.get("config_id") or "")
            for row in report["configurations"]
            if isinstance(row, dict)
        }
        self.assertIn("prototype_reviewed_examples_family_guard", config_ids)
        self.assertIn("prototype_reviewed_examples_active_guard", config_ids)
        self.assertIn("prototype_reviewed_examples_phrase_containment_guard", config_ids)
        self.assertIn("prototype_reviewed_examples_surface_pos_rescue_guard", config_ids)
        self.assertIn("prototype_reviewed_examples_phrase_prototype_guard", config_ids)
        self.assertIn("active_guard_result", report["summary_findings"])
        self.assertIn("phrase_containment_guard_result", report["summary_findings"])
        self.assertIn("surface_pos_rescue_guard_result", report["summary_findings"])
        self.assertIn("phrase_prototype_guard_result", report["summary_findings"])
        for config in report["configurations"]:
            self.assertTrue(isinstance(config, dict))
            for row in config["row_results"]:
                self.assertIn(row["predicted_decision"], {"replace", "abstain"})

        markdown = render_prototype_admission_markdown(report)
        self.assertIn("Semantic LLM Prototype Admission Probe", markdown)
        self.assertIn("Prototype reviewed examples, active phrase guard", markdown)
        self.assertIn("Prototype reviewed examples, phrase-control containment guard", markdown)
        self.assertIn("Prototype reviewed examples, surface-POS rescue guard", markdown)
        self.assertIn("Prototype reviewed examples, phrase-control prototype guard", markdown)

    def test_prototype_admission_probe_can_expand_to_all_dataset_families(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            all_dataset_families=True,
            scorer_id="tfidf_cosine",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["evaluation_scope"], "all_dataset_families")
        self.assertEqual(
            report["queue_id"],
            "en_es_sentence_veto_test_all_family_prototype_probe",
        )
        self.assertEqual(
            {str(row.get("family_id") or "") for row in report["coverage_rows"]},
            {"fam:check", "fam:order"},
        )
        phrase_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_phrase_containment_guard"
        )
        self.assertEqual(phrase_guard["summary"]["harmful_replace_count"], 0)

    def test_prototype_admission_probe_excludes_loader_only_cases(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        dataset_payload["families"][0]["cases"].append(
            {
                "case_id": "check:loader:001",
                "sentence": "The word check is being checked for bank draft.",
                "source_phrase": "check",
                "gold_winner": "fam:check:active",
                "gold_decision": "replace",
                "slice_tags": ["loader_only", "not_quality_evaluation"],
            }
        )

        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            scorer_id="tfidf_cosine",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        active_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_active_guard"
        )
        self.assertEqual(active_guard["summary"]["cases_total"], 2)
        self.assertNotIn(
            "check:loader:001",
            {str(row.get("case_id") or "") for row in active_guard["row_results"]},
        )

    def test_prototype_admission_probe_can_use_evidence_batch_rows(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        bundle = build_reviewed_example_frame_bundle(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            run_id="test",
            generated_at="2026-04-25T12:00:00Z",
        )
        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            evidence_batch_payload=bundle["normalized_batch"],
            scorer_id="tfidf_cosine",
            min_active_score=0.0,
            min_margin=0.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["evidence_source"], "evidence_batch")
        phrase_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_phrase_containment_guard"
        )
        self.assertEqual(phrase_guard["summary"]["harmful_replace_count"], 0)

    def test_phrase_containment_gate_uses_local_patterns_not_semantic_similarity(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        dataset_payload["families"][0]["cases"].append(
            {
                "case_id": "check:003",
                "sentence": "The rain check expires tomorrow.",
                "source_phrase": "check",
                "gold_winner": "none",
                "gold_decision": "abstain",
                "slice_tags": ["phrase_control"],
            }
        )
        evidence_batch = _normalized_evidence_batch()

        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            evidence_batch_payload=evidence_batch,
            scorer_id="token_jaccard",
            min_active_score=0.0,
            min_margin=-1.0,
            generated_at="2026-04-25T12:00:00Z",
        )

        containment_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_phrase_containment_guard"
        )
        rows = {row["case_id"]: row for row in containment_guard["row_results"]}
        self.assertFalse(rows["check:001"]["phrase_containment_hit"])
        self.assertEqual(rows["check:001"]["predicted_decision"], "replace")
        self.assertTrue(rows["check:003"]["phrase_containment_hit"])
        self.assertEqual(rows["check:003"]["phrase_containment_pattern"], "rain check")
        self.assertEqual(rows["check:003"]["predicted_decision"], "abstain")

    def test_surface_pos_rescue_uses_local_syntax_without_changing_binary_contract(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            evidence_batch_payload=_normalized_evidence_batch(),
            scorer_id="token_jaccard",
            min_active_score=0.0,
            min_margin=0.5,
            generated_at="2026-04-25T12:00:00Z",
        )

        surface_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_surface_pos_rescue_guard"
        )
        rows = {row["case_id"]: row for row in surface_guard["row_results"]}
        self.assertEqual(rows["check:001"]["predicted_decision"], "replace")
        self.assertTrue(rows["check:001"]["active_rescue_applied"])
        self.assertEqual(rows["check:001"]["surface_pos_signal"], "active_noun_frame")
        self.assertEqual(rows["check:002"]["predicted_decision"], "abstain")

    def test_surface_pos_rescue_does_not_override_strongest_noun_shadow(self) -> None:
        queue_payload, dataset_payload = _mixed_shadow_inputs()
        report = build_prototype_admission_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            evidence_batch_payload=_mixed_shadow_evidence_batch(),
            scorer_id="token_jaccard",
            min_active_score=0.0,
            min_margin=0.5,
            generated_at="2026-04-25T12:00:00Z",
        )

        surface_guard = next(
            row
            for row in report["configurations"]
            if row["config_id"] == "prototype_reviewed_examples_surface_pos_rescue_guard"
        )
        rows = {row["case_id"]: row for row in surface_guard["row_results"]}
        self.assertEqual(rows["case:002"]["surface_pos_signal"], "active_noun_frame")
        self.assertFalse(rows["case:002"]["active_rescue_applied"])
        self.assertEqual(
            rows["case:002"]["surface_pos_rescue_blocked_reason"],
            "strongest_shadow_not_verb_like",
        )
        self.assertEqual(rows["case:002"]["predicted_decision"], "abstain")


def _sample_inputs() -> tuple[dict[str, object], dict[str, object]]:
    queue_payload = {
        "queue_id": "semantic_prompt_bakeoff_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "role": "target",
                "likely_bucket": "needs_cue_data",
            }
        ],
    }
    dataset_payload = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_test",
        "families": [
            _family(
                family_id="fam:check",
                trigger="check",
                active_target="cheque",
                shadow_target="revisar",
                active_case_id="check:001",
                active_sentence="The check was signed and deposited yesterday.",
                shadow_case_id="check:002",
                shadow_sentence="They will check the records carefully tonight.",
            ),
            _family(
                family_id="fam:order",
                trigger="order",
                active_target="pedido",
                shadow_target="ordenar",
                active_case_id="order:001",
                active_sentence="The order arrived in a sealed box.",
                shadow_case_id="order:002",
                shadow_sentence="Please order the reports by date.",
            ),
        ],
    }
    return queue_payload, dataset_payload


def _normalized_evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "test_evidence",
        "batch_id": "test",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "check",
                "evidence_text": "cleared deposit payment rent",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "check",
                "evidence_text": "inspect records figures",
                "metadata": {
                    "family_id": "fam:check",
                    "candidate_sense_id": "fam:check:shadow",
                },
            },
            {
                "relation_type": "phrase_control_example",
                "trigger": "check",
                "evidence_text": "The rain check is valid next week.",
                "metadata": {"family_id": "fam:check"},
            },
        ],
    }


def _mixed_shadow_inputs() -> tuple[dict[str, object], dict[str, object]]:
    family_id = "fam:case"
    active_id = f"{family_id}:active"
    container_id = f"{family_id}:container"
    inspect_id = f"{family_id}:inspect"
    return (
        {
            "queue_id": "semantic_prompt_bakeoff_test_mixed_shadow",
            "families": [
                {
                    "family_id": family_id,
                    "trigger": "case",
                    "role": "target",
                    "likely_bucket": "needs_cue_data",
                }
            ],
        },
        {
            "schema_version": 1,
            "pair": "en-es",
            "dataset_id": "en_es_sentence_veto_mixed_shadow_test",
            "families": [
                {
                    "family_id": family_id,
                    "trigger": "case",
                    "active": {
                        "sense_id": active_id,
                        "target_lemma": "caso",
                        "canonical_pos": "noun",
                        "evidence_views": {"all_evidence_text": "legal court matter"},
                    },
                    "shadows": [
                        {
                            "sense_id": container_id,
                            "target_lemma": "estuche",
                            "canonical_pos": "noun",
                            "evidence_views": {"all_evidence_text": "container box shelf"},
                        },
                        {
                            "sense_id": inspect_id,
                            "target_lemma": "vigilar",
                            "canonical_pos": "verb",
                            "evidence_views": {"all_evidence_text": "inspect house rob"},
                        },
                    ],
                    "cases": [
                        {
                            "case_id": "case:001",
                            "sentence": "The court case resumed after lunch.",
                            "source_phrase": "case",
                            "gold_winner": active_id,
                            "gold_decision": "replace",
                        },
                        {
                            "case_id": "case:002",
                            "sentence": "The case on the shelf was empty.",
                            "source_phrase": "case",
                            "gold_winner": container_id,
                            "gold_decision": "abstain",
                        },
                    ],
                }
            ],
        },
    )


def _mixed_shadow_evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "test_mixed_shadow_evidence",
        "batch_id": "test-mixed-shadow",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "case",
                "evidence_text": "legal court matter",
                "metadata": {
                    "family_id": "fam:case",
                    "active_sense_id": "fam:case:active",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "case",
                "evidence_text": "container shelf empty",
                "metadata": {
                    "family_id": "fam:case",
                    "candidate_sense_id": "fam:case:container",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "case",
                "evidence_text": "inspect house rob",
                "metadata": {
                    "family_id": "fam:case",
                    "candidate_sense_id": "fam:case:inspect",
                },
            },
        ],
    }


def _family(
    *,
    family_id: str,
    trigger: str,
    active_target: str,
    shadow_target: str,
    active_case_id: str,
    active_sentence: str,
    shadow_case_id: str,
    shadow_sentence: str,
) -> dict[str, object]:
    active_id = f"{family_id}:active"
    shadow_id = f"{family_id}:shadow"
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {
            "sense_id": active_id,
            "target_lemma": active_target,
            "canonical_pos": "noun",
            "evidence_views": {
                "sense_label": f"{trigger} noun",
                "all_evidence_text": f"{trigger} noun",
            },
        },
        "shadows": [
            {
                "sense_id": shadow_id,
                "target_lemma": shadow_target,
                "canonical_pos": "verb",
                "evidence_views": {
                    "sense_label": f"{trigger} verb",
                    "all_evidence_text": f"{trigger} verb",
                },
            }
        ],
        "cases": [
            {
                "case_id": active_case_id,
                "sentence": active_sentence,
                "source_phrase": trigger,
                "gold_winner": active_id,
                "gold_decision": "replace",
                "slice_tags": ["clear_active", "cross_pos"],
            },
            {
                "case_id": shadow_case_id,
                "sentence": shadow_sentence,
                "source_phrase": trigger,
                "gold_winner": shadow_id,
                "gold_decision": "abstain",
                "slice_tags": ["clear_shadow", "cross_pos"],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
