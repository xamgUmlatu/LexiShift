from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_llm_pilot_scoring_en_es import (  # noqa: E402
    build_semantic_veto_llm_pilot_scoring_report,
    render_semantic_veto_llm_pilot_scoring_markdown,
)


class SemanticVetoLlmPilotScoringTests(unittest.TestCase):
    def test_scores_admitted_rows_against_independent_source_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source_batch.json"
            source_path.write_text(_json_text(_source_batch(include_phrase=True)), encoding="utf-8")

            report = build_semantic_veto_llm_pilot_scoring_report(
                plan_payload=_plan(),
                admission_payload=_admission(),
                policy_payload=_policy(),
                dataset_payload=_dataset(),
                source_contract_payload=_source_contract(source_path),
                matrix_payload=_matrix(),
                scorer_id_override="token_jaccard",
                generated_at="2026-05-05T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "frozen_candidate_product_target_passed_on_llm_pilot")
        self.assertEqual(report["summary"]["admitted_row_count"], 3)
        self.assertEqual(report["summary"]["scored_case_count"], 3)
        self.assertEqual(report["summary"]["unscored_case_count"], 0)
        self.assertEqual(report["source_evidence"]["coverage_family_count"], 1)
        self.assertFalse(report["strict_flow"]["evaluation_rows_used_as_evidence"])
        self.assertEqual(report["leakage_checks"]["blocking_issue_count"], 0)

        overall = report["summary"]["overall"]
        self.assertEqual(overall["positive_allow_rate"], 1.0)
        self.assertEqual(overall["negative_abstain_rate"], 1.0)
        self.assertEqual(overall["target_checks"]["target_status"], "pass")
        self.assertEqual(report["failure_rows"], [])

        markdown = render_semantic_veto_llm_pilot_scoring_markdown(report)
        self.assertIn("Semantic Veto LLM Pilot Scoring", markdown)
        self.assertIn("Strict Flow Checks", markdown)

    def test_blocks_scoring_when_source_contract_cannot_cover_candidate_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source_batch.json"
            source_path.write_text(
                _json_text(_source_batch(include_phrase=False)), encoding="utf-8"
            )

            report = build_semantic_veto_llm_pilot_scoring_report(
                plan_payload=_plan(),
                admission_payload=_admission(),
                policy_payload=_policy(),
                dataset_payload=_dataset(),
                source_contract_payload=_source_contract(source_path),
                matrix_payload=_matrix(),
                scorer_id_override="token_jaccard",
                generated_at="2026-05-05T00:00:00Z",
            )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "pilot_scoring_blocked_by_source_coverage")
        self.assertEqual(report["summary"]["scored_case_count"], 0)
        self.assertEqual(report["summary"]["unscored_case_count"], 3)
        self.assertEqual(
            report["coverage_rows"][0]["missing_requirements"], ["phrase_control_examples"]
        )


def _json_text(payload: dict[str, object]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "candidate": {
            "candidate_id": (
                "control_st_masked_all_margin_phrase_override|"
                "shadow_or_phrase_score|lead=0.05|score=0.0"
            ),
            "base_config_id": "control_st_masked_all_margin_phrase_override",
            "phrase_mode": "shadow_or_phrase_score",
            "shadow_lead_min": 0.05,
            "shadow_score_min": 0.0,
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
        },
        "split_policy": {"threshold_tuning_allowed_on_locked_eval": False},
    }


def _admission() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "pair": "en-es",
        "admitted_rows": [
            {
                "row_id": "pilotrow:bank:positive:001",
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "sentence": "The bank approved the loan.",
                "gold_decision": "allow",
                "gold_type": "positive_active",
                "split": "locked_eval",
                "difficulty_tags": ["word_order=canonical_subject_verb_object"],
            },
            {
                "row_id": "pilotrow:bank:shadow:001",
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "sentence": "They sat on the river bank.",
                "gold_decision": "abstain",
                "gold_type": "shadow_negative",
                "split": "discovery",
                "difficulty_tags": ["word_order=canonical_subject_verb_object"],
            },
            {
                "row_id": "pilotrow:bank:phrase:001",
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "sentence": "The bank is on your side.",
                "gold_decision": "abstain",
                "gold_type": "phrase_no_winner",
                "split": "discovery",
                "difficulty_tags": ["word_order=canonical_subject_verb_object"],
            },
        ],
    }


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": True,
            "utility_must_beat_abstain_all_baseline": True,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "test_dataset",
        "families": [
            {
                "family_id": "en-es:sentence-veto:bank:banco",
                "trigger": "bank",
                "active": {
                    "sense_id": "en-es:sentence-veto:bank:banco:active",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                },
                "shadows": [
                    {
                        "sense_id": "en-es:sentence-veto:bank:orilla:shadow",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                    }
                ],
            }
        ],
    }


def _source_contract(source_path: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "batch_path": str(source_path),
        "summary": {"contract_complete": True, "contract_complete_family_count": 1},
    }


def _source_batch(*, include_phrase: bool) -> dict[str, object]:
    rows: list[dict[str, object]] = [
        _source_row(
            "source:bank:active",
            relation_type="anchor_cue",
            candidate_sense_id="en-es:sentence-veto:bank:banco:active",
            evidence_text="The ___ approved a loan.",
        ),
        _source_row(
            "source:bank:shadow",
            relation_type="shadow_candidate",
            candidate_sense_id="en-es:sentence-veto:bank:orilla:shadow",
            evidence_text="They sat beside the river ___.",
            candidate_target="orilla",
        ),
    ]
    if include_phrase:
        rows.append(
            _source_row(
                "source:bank:phrase",
                relation_type="phrase_control_example",
                candidate_sense_id="",
                evidence_text="The ___ is firmly on your side.",
                candidate_target="phrase_control",
            )
        )
    return {
        "schema_version": 1,
        "batch_id": "fixture_source_batch",
        "pair": "en-es",
        "source_id": "fixture_independent_source",
        "source_family": "fixture",
        "model_id": "fixture",
        "rows": rows,
    }


def _source_row(
    row_id: str,
    *,
    relation_type: str,
    candidate_sense_id: str,
    evidence_text: str,
    candidate_target: str = "banco",
) -> dict[str, object]:
    return {
        "row_id": row_id,
        "relation_type": relation_type,
        "trigger": "bank",
        "active_target": "banco",
        "candidate_target": candidate_target,
        "evidence_text": evidence_text,
        "metadata": {
            "family_id": "en-es:sentence-veto:bank:banco",
            "active_sense_id": "en-es:sentence-veto:bank:banco:active",
            "candidate_sense_id": candidate_sense_id,
        },
    }


def _matrix() -> dict[str, object]:
    return {
        "schema_version": 1,
        "config_rows": [
            {
                "config_id": "control_st_masked_all_margin_phrase_override",
                "scorer_id": "token_jaccard",
                "context_view": "masked_sentence",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
