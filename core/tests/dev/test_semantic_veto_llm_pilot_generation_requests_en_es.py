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

from semantic_veto_llm_pilot_generation_requests_en_es import (  # noqa: E402
    build_semantic_veto_llm_pilot_generation_request_report,
    render_semantic_veto_llm_pilot_generation_request_markdown,
)


class SemanticVetoLlmPilotGenerationRequestsTests(unittest.TestCase):
    def test_renders_one_request_per_planned_row(self) -> None:
        report = build_semantic_veto_llm_pilot_generation_request_report(
            plan_payload=_plan_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "ready_for_llm_batch_execution")
        self.assertEqual(report["summary"]["planned_request_count"], 3)
        self.assertEqual(report["summary"]["request_count"], 3)
        self.assertEqual(
            report["summary"]["requests_by_gold_type"],
            {
                "phrase_no_winner": 1,
                "positive_active": 1,
                "shadow_negative": 1,
            },
        )
        self.assertTrue(report["request_checks"]["unique_request_ids"])
        self.assertTrue(report["request_checks"]["unique_expected_row_ids"])

        first = report["requests"][0]
        self.assertEqual(first["gold_type"], "positive_active")
        self.assertEqual(first["gold_decision"], "allow")
        self.assertIn("Return exactly one JSON object", first["prompt_text"])
        self.assertIn("must not contain the Spanish candidate replacement", first["prompt_text"])
        self.assertEqual(first["strata"]["word_order"], "canonical_subject_verb_object")

        markdown = render_semantic_veto_llm_pilot_generation_request_markdown(report)
        self.assertIn("ready_for_llm_batch_execution", markdown)
        self.assertIn("Generated rows are evaluation data only", markdown)

    def test_rejects_request_packet_when_plan_is_not_prefight_clean(self) -> None:
        plan = _plan_payload()
        plan["candidate"]["runtime_policy_change"] = "default_on"
        report = build_semantic_veto_llm_pilot_generation_request_report(
            plan_payload=plan,
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "request_packet_needs_repair")
        self.assertEqual(report["summary"]["request_count"], 0)
        self.assertGreater(report["plan_checks"]["issue_count"], 0)


def _plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pilot_id": "semantic_veto_llm_pilot_en_es_v1",
        "pair": "en-es",
        "status": "no_spend_preflight",
        "purpose": "test plan",
        "candidate": {
            "candidate_id": (
                "control_st_masked_all_margin_phrase_override|"
                "shadow_or_phrase_score|lead=0.05|score=0.0"
            ),
            "decision_shape": "allow_default_shadow_veto",
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
        },
        "flow_steps": [
            {"step_id": "freeze_candidate", "required": True},
            {"step_id": "select_pilot_families", "required": True},
            {"step_id": "generate_rows", "required": False},
            {"step_id": "admission_filter", "required": True},
            {"step_id": "split_discovery_locked_eval", "required": True},
            {"step_id": "score_candidate", "required": True},
            {"step_id": "expand_or_diagnose", "required": True},
        ],
        "split_policy": {
            "method": "sha256_row_id_modulo",
            "modulo": 4,
            "locked_eval_remainders": [0],
            "threshold_tuning_allowed_on_locked_eval": False,
        },
        "generation_strata": {
            "word_order": ["canonical_subject_verb_object", "fronted_context"],
            "trigger_position": ["middle"],
            "context_distance": ["near_disambiguator"],
            "morphology": ["singular_or_base"],
            "register": ["ordinary_web"],
            "difficulty": ["obvious"],
        },
        "row_contract": {
            "required_fields": [
                "row_id",
                "family_id",
                "trigger",
                "candidate_replacement",
                "sentence",
                "gold_decision",
                "gold_type",
                "active_sense",
                "gold_reason",
                "pos",
                "generator_id",
                "prompt_id",
            ],
            "gold_types": [
                "positive_active",
                "shadow_negative",
                "phrase_no_winner",
            ],
            "gold_decisions": ["allow", "abstain"],
            "decision_by_gold_type": {
                "positive_active": "allow",
                "shadow_negative": "abstain",
                "phrase_no_winner": "abstain",
            },
            "conditional_fields": {
                "shadow_negative": ["negative_sense"],
                "phrase_no_winner": ["no_winner_reason"],
            },
        },
        "admission_filters": [
            {"filter_id": "required_fields_present", "severity": "reject"},
            {"filter_id": "known_pilot_family", "severity": "reject"},
            {"filter_id": "gold_decision_matches_gold_type", "severity": "reject"},
            {"filter_id": "trigger_present_in_sentence", "severity": "reject"},
            {
                "filter_id": "spanish_target_lemma_absent_from_sentence",
                "severity": "reject",
            },
            {"filter_id": "label_leakage_absent_from_sentence", "severity": "reject"},
            {"filter_id": "duplicate_sentence_absent", "severity": "reject"},
            {"filter_id": "duplicate_row_id_absent", "severity": "reject"},
            {"filter_id": "conditional_reason_present", "severity": "reject"},
            {"filter_id": "minimum_sentence_shape", "severity": "reject"},
            {
                "filter_id": "locked_eval_not_used_for_threshold_tuning",
                "severity": "reject",
            },
        ],
        "pilot_families": [
            {
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "active_sense": "financial institution",
                "pos": "noun",
                "planned_rows": {
                    "positive_active": 1,
                    "shadow_negative": 1,
                    "phrase_no_winner": 1,
                },
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
