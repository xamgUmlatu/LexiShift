from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import semantic_source_margin_policy_sweep_en_es as sweep_module  # noqa: E402
from semantic_source_margin_policy_sweep_en_es import (  # noqa: E402
    HeldoutSuiteSpec,
    build_margin_policy_sweep_report,
    render_margin_policy_sweep_markdown,
)


class SemanticSourceMarginPolicySweepTests(unittest.TestCase):
    def test_margin_sweep_selects_smallest_margin_that_passes_every_suite(self) -> None:
        report = build_margin_policy_sweep_report(
            base_dataset_payload=_base_dataset(),
            evidence_batch_payload=_evidence_batch(),
            heldout_suites=[
                HeldoutSuiteSpec(
                    suite_id="active_shadow_test",
                    path=Path("active.json"),
                    payload=_active_shadow_cases(),
                ),
                HeldoutSuiteSpec(
                    suite_id="phrase_test",
                    path=Path("phrase.json"),
                    payload=_phrase_cases(),
                ),
            ],
            margins=(0.0, 0.1),
            scorer_id="token_jaccard",
            context_view="masked_sentence",
            min_active_score=0.0,
            include_full_v10_ablation=False,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "margin_candidate_found")
        self.assertEqual(report["summary"]["recommended_min_margin"], 0.1)
        self.assertEqual(report["summary"]["recommended_phrase_prototype_margin"], 0.0)
        self.assertEqual(
            report["summary"]["recommended_policy"],
            {"min_margin": 0.1, "phrase_prototype_margin": 0.0},
        )
        self.assertEqual(report["recommendation"]["passing_margins"], [0.1])
        self.assertEqual(
            report["recommendation"]["passing_policies"],
            [{"min_margin": 0.1, "phrase_prototype_margin": 0.0}],
        )
        self.assertIn(
            "margin_candidate_requires_non_v10_stress_before_runtime_default",
            report["limitations"],
        )

        phrase_margin_zero = [
            row
            for row in report["rows"]
            if row["suite_id"] == "phrase_test"
            and row["min_margin"] == 0.0
            and row["phrase_prototype_margin"] == 0.0
        ][0]
        self.assertFalse(phrase_margin_zero["passes"])
        self.assertEqual(phrase_margin_zero["harmful_replace_count"], 1)

        markdown = render_margin_policy_sweep_markdown(report)
        self.assertIn("Semantic Source Margin Policy Sweep", markdown)
        self.assertIn("Recommended min margin", markdown)
        self.assertIn("phrase_test", markdown)

    def test_margin_sweep_reports_review_when_no_scalar_margin_passes(self) -> None:
        report = build_margin_policy_sweep_report(
            base_dataset_payload=_base_dataset(),
            evidence_batch_payload=_evidence_batch(),
            heldout_suites=[
                HeldoutSuiteSpec(
                    suite_id="active_shadow_test",
                    path=Path("active.json"),
                    payload=_active_shadow_cases(),
                ),
                HeldoutSuiteSpec(
                    suite_id="phrase_test",
                    path=Path("phrase.json"),
                    payload=_phrase_cases(),
                ),
            ],
            margins=(0.0, 0.95),
            scorer_id="token_jaccard",
            context_view="masked_sentence",
            min_active_score=0.0,
            include_full_v10_ablation=False,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "margin_review")
        self.assertIsNone(report["summary"]["recommended_min_margin"])
        self.assertIsNone(report["summary"]["recommended_phrase_prototype_margin"])
        self.assertEqual(report["recommendation"]["passing_margins"], [])
        self.assertEqual(report["recommendation"]["passing_policies"], [])
        self.assertEqual(report["recommendation"]["reason"], "no_policy_passed")
        self.assertIn(
            "no_scalar_margin_policy_passed_current_suites",
            report["limitations"],
        )

        blockers_by_margin = report["recommendation"]["blockers_by_margin"]
        self.assertIn("m=0;phrase=0", blockers_by_margin)
        self.assertIn("m=0.95;phrase=0", blockers_by_margin)

    def test_margin_sweep_can_cross_phrase_prototype_margin(self) -> None:
        report = build_margin_policy_sweep_report(
            base_dataset_payload=_base_dataset(),
            evidence_batch_payload=_evidence_batch(),
            heldout_suites=[
                HeldoutSuiteSpec(
                    suite_id="active_shadow_test",
                    path=Path("active.json"),
                    payload=_active_shadow_cases(),
                )
            ],
            margins=(0.0,),
            phrase_prototype_margins=(0.0, 0.2),
            scorer_id="token_jaccard",
            context_view="masked_sentence",
            min_active_score=0.0,
            include_full_v10_ablation=False,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["grid"]["phrase_prototype_margins"], [0.0, 0.2])
        self.assertEqual(report["summary"]["row_count"], 2)
        self.assertEqual(
            {row["phrase_prototype_margin"] for row in report["rows"]},
            {0.0, 0.2},
        )

    def test_surface_pos_shape_replays_margin_grid_from_single_score_trace(self) -> None:
        base_row = {
            "row_results": [
                {
                    "case_id": "active:modifier:001",
                    "gold_decision": "replace",
                    "active_score": 0.54,
                    "strongest_shadow_score": 0.56,
                    "phrase_control_score": 0.575,
                    "active_evidence_text": "upset adjective sense: mentally troubled",
                    "phrase_control_evidence_text": "turn something over",
                    "surface_pos_signal": "active_modifier_frame",
                }
            ],
            "phrase_preemption_hit_count": 0,
        }
        with (
            patch.object(
                sweep_module,
                "_base_phrase_prototype_matrix_row",
                return_value=base_row,
            ) as base_matrix,
            patch.object(
                sweep_module,
                "build_source_heldout_validation_report",
                side_effect=AssertionError("surface-POS policy sweep should replay traces"),
            ),
        ):
            report = build_margin_policy_sweep_report(
                base_dataset_payload=_base_dataset(),
                evidence_batch_payload=_evidence_batch(),
                heldout_suites=[
                    HeldoutSuiteSpec(
                        suite_id="active_shadow_test",
                        path=Path("active.json"),
                        payload=_active_shadow_cases(),
                    )
                ],
                margins=(0.0, 0.03),
                phrase_prototype_margins=(0.02,),
                scorer_id="token_jaccard",
                context_view="masked_sentence",
                min_active_score=0.0,
                decision_shape="active_shadow_phrase_semantic_surface_pos",
                include_full_v10_ablation=False,
                generated_at="2026-04-29T12:00:00Z",
            )

        self.assertEqual(base_matrix.call_count, 1)
        self.assertEqual(report["summary"]["row_count"], 2)
        self.assertEqual(
            {row["min_margin"] for row in report["rows"]},
            {0.0, 0.03},
        )
        self.assertTrue(all(row["passes"] for row in report["rows"]))
        self.assertTrue(all(row["active_rescue_applied_count"] == 1 for row in report["rows"]))


def _base_dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "base_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "active": {
                    "sense_id": "fam:check:active",
                    "target_lemma": "cheque",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "payment document",
                        "all_evidence_text": "payment document rent paid",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "fam:check:shadow",
                        "target_lemma": "control",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "verification mark",
                            "all_evidence_text": "verification mark rent paid",
                        },
                    }
                ],
                "cases": [],
            }
        ],
    }


def _active_shadow_cases() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "active_shadow_test_cases",
        "case_scope": "semantic_active_shadow_only",
        "families": [
            {
                "family_id": "fam:check",
                "cases": [
                    {
                        "case_id": "active:check:001",
                        "sentence": "The cheque rent paid check arrived.",
                        "source_phrase": "check",
                        "gold_winner": "fam:check:active",
                        "gold_decision": "replace",
                    }
                ],
            }
        ],
    }


def _phrase_cases() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "phrase_test_cases",
        "case_scope": "phrase_no_winner_only",
        "families": [
            {
                "family_id": "fam:check",
                "cases": [
                    {
                        "case_id": "phrase:check:001",
                        "sentence": "The rent paid check cleared.",
                        "source_phrase": "check",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                    }
                ],
            }
        ],
    }


def _evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "test_source",
        "batch_id": "test_batch",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "check",
                "evidence_text": "cheque rent paid",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                    "candidate_sense_id": "fam:check:active",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "check",
                "evidence_text": "voucher rent paid",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                    "candidate_sense_id": "fam:check:shadow",
                },
            },
        ],
        "row_count": 2,
    }


if __name__ == "__main__":
    unittest.main()
