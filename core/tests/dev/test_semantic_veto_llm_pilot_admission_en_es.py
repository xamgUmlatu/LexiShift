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

from semantic_veto_llm_pilot_admission_en_es import (  # noqa: E402
    build_semantic_veto_llm_pilot_admission_report,
    render_semantic_veto_llm_pilot_admission_markdown,
)


class SemanticVetoLlmPilotAdmissionTests(unittest.TestCase):
    def test_no_spend_preflight_is_ready_before_rows_exist(self) -> None:
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "ready_for_generation")
        self.assertEqual(report["plan_checks"]["issue_count"], 0)
        self.assertFalse(report["admission_summary"]["generated_rows_present"])
        self.assertEqual(report["planning_summary"]["planned_row_count"], 3)
        self.assertEqual(report["candidate"]["runtime_policy_change"], "none")

        markdown = render_semantic_veto_llm_pilot_admission_markdown(report)
        self.assertIn("ready_for_generation", markdown)
        self.assertIn("control_st_masked_all_margin_phrase_override", markdown)

    def test_admits_clean_rows_and_assigns_deterministic_splits(self) -> None:
        payload = {"rows": [_positive_row(), _shadow_row(), _phrase_row()]}
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload=payload,
            generated_at="2026-05-05T00:00:00Z",
        )
        repeat = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload=payload,
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "admitted_for_scoring")
        self.assertEqual(report["admission_summary"]["admitted_row_count"], 3)
        self.assertEqual(report["admission_summary"]["rejected_row_count"], 0)
        self.assertTrue(all(row["shortfall_count"] == 0 for row in report["family_coverage"]))
        self.assertEqual(
            [row["split"] for row in report["admitted_rows"]],
            [row["split"] for row in repeat["admitted_rows"]],
        )

    def test_request_packet_alignment_must_match_generated_row_ids(self) -> None:
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload={
                "selected_expected_row_ids": [
                    "pilotrow:pilot_bank_banco:positive_active:001",
                    "pilotrow:pilot_bank_banco:shadow_negative:001",
                    "pilotrow:pilot_bank_banco:phrase_no_winner:001",
                ],
                "rows": [
                    _positive_row("pilotrow:pilot_bank_banco:positive_active:001"),
                    _shadow_row("pilotrow:pilot_bank_banco:shadow_negative:001"),
                    _phrase_row("pilotrow:pilot_bank_banco:phrase_no_winner:001"),
                ],
            },
            generation_requests_payload=_request_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "admitted_for_scoring")
        self.assertTrue(report["request_alignment"]["request_packet_present"])
        self.assertEqual(report["request_alignment"]["expected_row_count"], 3)
        self.assertEqual(report["request_alignment"]["matched_expected_row_count"], 3)

    def test_request_alignment_uses_selected_subset_for_smoke_batches(self) -> None:
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload={
                "selected_expected_row_ids": [
                    "pilotrow:pilot_bank_banco:positive_active:001",
                ],
                "rows": [
                    _positive_row("pilotrow:pilot_bank_banco:positive_active:001"),
                ],
            },
            generation_requests_payload=_request_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "pilot_coverage_incomplete")
        self.assertEqual(report["request_alignment"]["expected_row_count"], 1)
        self.assertEqual(report["request_alignment"]["matched_expected_row_count"], 1)
        self.assertEqual(report["request_alignment"]["missing_expected_row_ids"], [])
        self.assertEqual(report["admission_summary"]["admitted_row_count"], 1)

    def test_request_packet_alignment_rejects_unexpected_generated_rows(self) -> None:
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload={
                "selected_expected_row_ids": [
                    "pilotrow:pilot_bank_banco:positive_active:001",
                    "pilotrow:pilot_bank_banco:shadow_negative:001",
                    "pilotrow:pilot_bank_banco:phrase_no_winner:001",
                ],
                "rows": [
                    _positive_row("pilotrow:pilot_bank_banco:positive_active:001"),
                    _shadow_row("pilotrow:pilot_bank_banco:shadow_negative:001"),
                    _phrase_row("pilotrow:pilot_bank_banco:unexpected:001"),
                ],
            },
            generation_requests_payload=_request_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "generated_rows_need_repair")
        self.assertEqual(report["rejection_reasons"]["unexpected_row_id"], 1)
        self.assertEqual(
            report["request_alignment"]["missing_expected_row_ids"],
            ["pilotrow:pilot_bank_banco:phrase_no_winner:001"],
        )
        self.assertEqual(
            report["request_alignment"]["unexpected_row_ids"],
            ["pilotrow:pilot_bank_banco:unexpected:001"],
        )

    def test_rejects_leakage_duplicates_and_contract_breaks(self) -> None:
        report = build_semantic_veto_llm_pilot_admission_report(
            plan_payload=_plan_payload(),
            generated_rows_payload={
                "rows": [
                    _positive_row(),
                    _shadow_row(),
                    _phrase_row(),
                    {
                        **_positive_row("pilot:bank:banco:bad-target"),
                        "sentence": "The bank used banco in the generated sentence deliberately.",
                    },
                    {
                        **_positive_row(),
                        "sentence": "The bank opened another downtown office this morning.",
                    },
                    {
                        **_shadow_row("pilot:bank:banco:bad-decision"),
                        "gold_decision": "allow",
                    },
                ]
            },
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "generated_rows_need_repair")
        self.assertEqual(report["admission_summary"]["admitted_row_count"], 3)
        self.assertEqual(report["admission_summary"]["rejected_row_count"], 3)
        reasons = report["rejection_reasons"]
        self.assertEqual(reasons["spanish_target_lemma_in_sentence"], 1)
        self.assertEqual(reasons["duplicate_row_id"], 1)
        self.assertEqual(reasons["gold_decision_mismatch"], 1)


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
            "word_order": ["canonical_subject_verb_object"],
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


def _request_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "decision": "ready_for_llm_batch_execution",
        "requests": [
            {
                "expected_row_id": "pilotrow:pilot_bank_banco:positive_active:001",
                "family_id": "pilot:bank:banco",
                "gold_type": "positive_active",
            },
            {
                "expected_row_id": "pilotrow:pilot_bank_banco:shadow_negative:001",
                "family_id": "pilot:bank:banco",
                "gold_type": "shadow_negative",
            },
            {
                "expected_row_id": "pilotrow:pilot_bank_banco:phrase_no_winner:001",
                "family_id": "pilot:bank:banco",
                "gold_type": "phrase_no_winner",
            },
        ],
    }


def _positive_row(row_id: str = "pilot:bank:banco:positive:001") -> dict[str, object]:
    return {
        "row_id": row_id,
        "family_id": "pilot:bank:banco",
        "trigger": "bank",
        "candidate_replacement": "banco",
        "sentence": "The bank approved my loan application yesterday.",
        "gold_decision": "allow",
        "gold_type": "positive_active",
        "active_sense": "financial institution",
        "gold_reason": "The sentence refers to a financial institution.",
        "pos": "noun",
        "generator_id": "test-generator",
        "prompt_id": "pilot-prompt-v1",
    }


def _shadow_row(row_id: str = "pilot:bank:banco:shadow:001") -> dict[str, object]:
    return {
        "row_id": row_id,
        "family_id": "pilot:bank:banco",
        "trigger": "bank",
        "candidate_replacement": "banco",
        "sentence": "The river bank eroded after heavy rain last night.",
        "gold_decision": "abstain",
        "gold_type": "shadow_negative",
        "active_sense": "financial institution",
        "negative_sense": "land beside a river",
        "gold_reason": "The sentence refers to land beside water.",
        "pos": "noun",
        "generator_id": "test-generator",
        "prompt_id": "pilot-prompt-v1",
    }


def _phrase_row(row_id: str = "pilot:bank:banco:phrase:001") -> dict[str, object]:
    return {
        "row_id": row_id,
        "family_id": "pilot:bank:banco",
        "trigger": "bank",
        "candidate_replacement": "banco",
        "sentence": "I will bank on that promise during negotiations.",
        "gold_decision": "abstain",
        "gold_type": "phrase_no_winner",
        "active_sense": "financial institution",
        "no_winner_reason": "The phrase uses bank on as a verb phrase.",
        "gold_reason": "The candidate noun replacement would not fit the phrase.",
        "pos": "noun",
        "generator_id": "test-generator",
        "prompt_id": "pilot-prompt-v1",
    }


if __name__ == "__main__":
    unittest.main()
