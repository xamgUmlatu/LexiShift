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

from semantic_veto_veto_only_probe_en_es import (  # noqa: E402
    build_veto_only_probe_report,
    render_veto_only_probe_markdown,
)


class SemanticVetoVetoOnlyProbeTests(unittest.TestCase):
    def test_allow_default_shadow_veto_can_pass_product_target(self) -> None:
        report = build_veto_only_probe_report(
            policy=_policy(),
            matrix=_matrix_report(),
            shadow_lead_grid=[0.05],
            shadow_score_grid=[0.1],
            generated_at="2026-05-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "veto_only_product_target_pass_found")
        self.assertEqual(report["summary"]["target_pass_count"], 3)
        self.assertTrue(report["e2e_checks"]["policy_rows_emitted"], 4)

        best = report["summary"]["best_product_rank_row"]
        self.assertEqual(best["config_id"], "shadow_signal")
        self.assertEqual(best["positive_allow_rate"], 1.0)
        self.assertEqual(best["negative_abstain_rate"], 0.6)
        self.assertEqual(best["target_status"], "pass")

        markdown = render_veto_only_probe_markdown(report)
        self.assertIn("Veto-Only Probe", markdown)
        self.assertIn("shadow_signal", markdown)
        self.assertIn("score_product_outcome_counts", markdown)

    def test_phrase_mode_only_blocks_phrase_when_enabled(self) -> None:
        report = build_veto_only_probe_report(
            policy=_policy(),
            matrix=_phrase_matrix_report(),
            shadow_lead_grid=[0.05],
            shadow_score_grid=[0.1],
            generated_at="2026-05-01T00:00:00Z",
        )

        by_mode = {row["phrase_mode"]: row for row in report["rows"]}
        self.assertEqual(by_mode["shadow_only"]["negative_abstain_rate"], 0.0)
        self.assertEqual(by_mode["shadow_or_phrase"]["negative_abstain_rate"], 1.0)
        self.assertEqual(by_mode["shadow_or_phrase"]["target_status"], "pass")


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "test_policy",
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": True,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _matrix_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "matrix_id": "fixture_matrix",
        "dataset_id": "fixture_v10",
        "config_rows": [
            {
                "config_id": "shadow_signal",
                "label": "Shadow signal fixture",
                "scorer_id": "fixture_scorer",
                "context_view": "masked_sentence",
                "sense_representation": "all_evidence_text",
                "aggregation_rule": "single_concatenated_text",
                "decision_rule": "active_minus_strongest_shadow",
            },
            {
                "config_id": "weak_shadow",
                "label": "Weak shadow fixture",
                "scorer_id": "fixture_scorer",
                "context_view": "masked_sentence",
                "sense_representation": "all_evidence_text",
                "aggregation_rule": "single_concatenated_text",
                "decision_rule": "active_minus_strongest_shadow",
            },
        ],
        "case_results": [
            *[
                _case("shadow_signal", f"positive-{index}", "replace", 0.6, 0.1)
                for index in range(5)
            ],
            *[
                _case("shadow_signal", f"negative-block-{index}", "abstain", 0.1, 0.3)
                for index in range(3)
            ],
            *[
                _case("shadow_signal", f"negative-allow-{index}", "abstain", 0.3, 0.1)
                for index in range(2)
            ],
            *[_case("weak_shadow", f"positive-{index}", "replace", 0.6, 0.1) for index in range(5)],
            *[_case("weak_shadow", f"negative-{index}", "abstain", 0.3, 0.1) for index in range(5)],
        ],
    }


def _phrase_matrix_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ok",
        "matrix_id": "fixture_phrase_matrix",
        "dataset_id": "fixture_v10",
        "config_rows": [
            {
                "config_id": "phrase_signal",
                "label": "Phrase signal fixture",
                "scorer_id": "fixture_scorer",
                "context_view": "masked_sentence",
                "sense_representation": "all_evidence_text",
                "aggregation_rule": "single_concatenated_text",
                "decision_rule": "active_minus_strongest_shadow",
            }
        ],
        "case_results": [
            _case("phrase_signal", "positive-1", "replace", 0.6, 0.1),
            _case(
                "phrase_signal",
                "phrase-negative-1",
                "abstain",
                0.6,
                0.1,
                phrase_preemption_hit=True,
            ),
        ],
    }


def _case(
    config_id: str,
    case_id: str,
    gold_decision: str,
    active_score: float,
    shadow_score: float,
    *,
    phrase_preemption_hit: bool = False,
) -> dict[str, object]:
    return {
        "config_id": config_id,
        "case_id": case_id,
        "family_id": f"family:{case_id}",
        "trigger": case_id.split("-")[0],
        "sentence": f"Fixture sentence for {case_id}.",
        "gold_decision": gold_decision,
        "gold_winner_type": "active" if gold_decision == "replace" else "shadow",
        "active_score": active_score,
        "strongest_shadow_score": shadow_score,
        "phrase_preemption_hit": phrase_preemption_hit,
    }


if __name__ == "__main__":
    unittest.main()
