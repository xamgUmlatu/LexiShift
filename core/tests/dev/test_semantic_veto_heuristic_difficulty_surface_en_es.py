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

from semantic_veto_heuristic_difficulty_surface_en_es import (  # noqa: E402
    build_heuristic_difficulty_surface_report,
    render_heuristic_difficulty_surface_markdown,
)


class SemanticVetoHeuristicDifficultySurfaceTests(unittest.TestCase):
    def test_surface_scores_case_type_difficulty_and_preserves_contracts(self) -> None:
        report = build_heuristic_difficulty_surface_report(
            policy=_policy(),
            authoring_payload=_authoring_payload(),
            score_sources=[
                {
                    "source_id": "sentence_transformer_cosine",
                    "report": _score_report(),
                }
            ],
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "heuristic_difficulty_surface_established")

        difficulty = report["summary"]["overall"]["difficulty_scores"]
        self.assertAlmostEqual(difficulty["positive_allow_difficulty"], 1 / 4, places=4)
        self.assertAlmostEqual(difficulty["shadow_negative_difficulty"], 0.0, places=4)
        self.assertAlmostEqual(difficulty["phrase_no_winner_difficulty"], 2 / 4, places=4)

        expansion_cells = {row["cell_id"] for row in report["expansion_plan"]["recommendations"]}
        self.assertIn("core_low_polysemy_phrase:yes", expansion_cells)
        self.assertNotIn(
            "core_low_polysemy_control:shadow_negative:not_applicable",
            expansion_cells,
        )

        rank_breakdown_values = {row["value"] for row in report["breakdowns"]["source_rank_bin"]}
        self.assertIn("missing", rank_breakdown_values)

        formula_rows = report["formula_bakeoff"]["comparison_rows"]
        baseline = next(
            row for row in formula_rows if row["formula_id"] == "baseline_frequency_polysemy"
        )
        self.assertEqual(baseline["excluded_sentinel_triggers"], 1)
        self.assertEqual(baseline["excluded_missing_rank_triggers"], 1)
        self.assertEqual(baseline["compared_triggers"], 2)

        markdown = render_heuristic_difficulty_surface_markdown(report)
        self.assertIn("Formula Bakeoff", markdown)
        self.assertIn("core_low_polysemy_phrase:yes", markdown)


def _policy() -> dict[str, object]:
    return {
        "pair": "en-es",
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
        },
    }


def _authoring_payload() -> dict[str, object]:
    return {
        "authored_triggers": [
            _authored(
                "yes",
                "core_low_polysemy_control",
                "pre_outcome",
                "not_applicable",
                175,
                "1-500",
                1,
                1,
                {"positive_active": 1, "phrase_no_winner": 1},
            ),
            _authored(
                "man",
                "core_high_polysemy",
                "pre_outcome",
                "full",
                95,
                "1-500",
                12,
                2,
                {
                    "positive_active": 1,
                    "shadow_negative": 1,
                    "phrase_no_winner": 1,
                },
            ),
            _authored(
                "mystery",
                "mid_low_polysemy_control",
                "pre_outcome",
                "not_applicable",
                None,
                "missing",
                2,
                1,
                {"positive_active": 1, "phrase_no_winner": 1},
            ),
            _authored(
                "check",
                "measured_missing_rank_high_failure_sentinel",
                "outcome_informed_sentinel",
                "full",
                None,
                "missing",
                38,
                2,
                {"positive_active": 1, "phrase_no_winner": 1},
            ),
        ]
    }


def _authored(
    trigger: str,
    group_id: str,
    selection_mode: str,
    shadow_contract: str,
    rank: float | None,
    rank_bin: str,
    sense_count: int,
    pos_count: int,
    case_type_counts: dict[str, int],
) -> dict[str, object]:
    return {
        "trigger": trigger,
        "group_id": group_id,
        "selection_mode": selection_mode,
        "shadow_contract": shadow_contract,
        "source_rank": rank,
        "source_rank_bin": rank_bin,
        "polysemy_band": "high_10_plus" if sense_count >= 10 else "low_1_to_3",
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
        "target_lemma": f"{trigger}_target",
        "expected_veto_difficulty": "test",
        "case_type_counts": case_type_counts,
    }


def _score_report() -> dict[str, object]:
    return {
        "status": "ok",
        "config": {"scorer_id": "sentence_transformer_cosine"},
        "row_results": [
            _row("yes", "positive_active", "replace", "replace", "1-500", "not_applicable"),
            _row(
                "yes",
                "phrase_no_winner",
                "abstain",
                "replace",
                "1-500",
                "not_applicable",
            ),
            _row("man", "positive_active", "replace", "abstain", "1-500", "full"),
            _row("man", "shadow_negative", "abstain", "abstain", "1-500", "full"),
            _row("man", "phrase_no_winner", "abstain", "abstain", "1-500", "full"),
            _row(
                "mystery",
                "positive_active",
                "replace",
                "replace",
                "missing",
                "not_applicable",
            ),
            _row(
                "mystery",
                "phrase_no_winner",
                "abstain",
                "abstain",
                "missing",
                "not_applicable",
            ),
            _row(
                "check",
                "positive_active",
                "replace",
                "replace",
                "missing",
                "full",
                group_id="measured_missing_rank_high_failure_sentinel",
                selection_mode="outcome_informed_sentinel",
            ),
            _row(
                "check",
                "phrase_no_winner",
                "abstain",
                "replace",
                "missing",
                "full",
                group_id="measured_missing_rank_high_failure_sentinel",
                selection_mode="outcome_informed_sentinel",
            ),
        ],
    }


def _row(
    trigger: str,
    case_type: str,
    gold_decision: str,
    predicted_decision: str,
    rank_bin: str,
    shadow_contract: str,
    *,
    group_id: str | None = None,
    selection_mode: str = "pre_outcome",
) -> dict[str, object]:
    group_id = group_id or (
        "core_low_polysemy_control" if trigger == "yes" else "core_high_polysemy"
    )
    return {
        "case_id": f"{trigger}:{case_type}",
        "family_id": f"family:{trigger}",
        "trigger": trigger,
        "sentence": f"{trigger} sentence",
        "gold_decision": gold_decision,
        "predicted_decision": predicted_decision,
        "gold_winner_type": "active" if gold_decision == "replace" else "none",
        "active_score": 0.6,
        "strongest_shadow_score": 0.55,
        "margin": 0.05,
        "slice_dimensions": {
            "heuristic_group": [group_id],
            "selection_mode": [selection_mode],
            "source_rank_bin": [rank_bin],
            "polysemy_band": ["high_10_plus" if trigger == "man" else "low_1_to_3"],
            "manual_case_type": [case_type],
            "shadow_contract": [shadow_contract],
        },
    }


if __name__ == "__main__":
    unittest.main()
