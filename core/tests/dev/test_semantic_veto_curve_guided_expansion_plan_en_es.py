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

from semantic_veto_curve_guided_expansion_plan_en_es import (  # noqa: E402
    build_curve_guided_expansion_plan_report,
    render_curve_guided_expansion_markdown,
)


class SemanticVetoCurveGuidedExpansionPlanTests(unittest.TestCase):
    def test_curve_guided_plan_turns_surface_signals_into_expansion_queue(self) -> None:
        report = build_curve_guided_expansion_plan_report(
            shape_payload=_shape_payload(),
            surface_payload=_surface_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "curve_guided_expansion_plan_established")
        self.assertEqual(report["summary"]["primary_cell_count"], 3)
        self.assertEqual(report["summary"]["sentinel_cell_count"], 1)
        self.assertGreaterEqual(report["summary"]["queued_cell_count"], 2)

        phrase_row = next(
            row
            for row in report["expansion_queue"]
            if row["manual_case_type"] == "phrase_no_winner"
        )
        self.assertEqual(phrase_row["priority"], "P0")
        self.assertIn("strong_surface_curve_signal", phrase_row["reasons"])
        self.assertIn("underfilled_cell", phrase_row["reasons"])
        self.assertEqual(phrase_row["manual_discovery_rows"], 4)
        self.assertEqual(phrase_row["llm_discovery_rows"], 16)
        self.assertEqual(phrase_row["locked_eval_rows"], 8)

        case_types = {row["manual_case_type"] for row in report["case_type_summary"]}
        self.assertIn("phrase_no_winner", case_types)
        self.assertIn("shadow_negative", case_types)
        shadow_row = next(
            row for row in report["expansion_queue"] if row["manual_case_type"] == "shadow_negative"
        )
        self.assertTrue(
            all(
                signal["gate_id"] in {None, "shadow_negative"}
                for signal in shadow_row["surface_signals"]
            )
        )

        markdown = render_curve_guided_expansion_markdown(report)
        self.assertIn("Curve-Guided Expansion Plan", markdown)
        self.assertIn("Strongest Curve Signals", markdown)
        self.assertIn("Expansion Queue", markdown)

    def test_missing_curve_signals_are_review_status(self) -> None:
        report = build_curve_guided_expansion_plan_report(
            shape_payload=_shape_payload(),
            surface_payload={"sweep_reports": []},
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("surface_report_has_no_curve_signals", report["summary"]["issues"])


def _shape_payload() -> dict[str, object]:
    phrase_id = (
        "scorer_id=tfidf_cosine::selection_mode=pre_outcome::"
        "heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::"
        "shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus"
    )
    shadow_id = (
        "scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::"
        "heuristic_group=missing_rank_probe::manual_case_type=shadow_negative::"
        "shadow_contract=full::source_rank_bin=missing::polysemy_band=high_10_plus"
    )
    positive_id = (
        "scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::"
        "heuristic_group=missing_rank_probe::manual_case_type=positive_active::"
        "shadow_contract=full::source_rank_bin=missing::polysemy_band=high_10_plus"
    )
    return {
        "pair": "en-es",
        "decision": "formula_shape_bakeoff_established",
        "cell_observations": [
            _cell(
                cell_id=phrase_id,
                selection_mode="pre_outcome",
                manual_case_type="phrase_no_winner",
                heuristic_group="core_high_polysemy",
                scorer_id="tfidf_cosine",
                underfilled_rate=0.9,
                posterior_failure_rate=0.35,
                uncertainty_width=0.8,
                triggers=["help"],
            ),
            _cell(
                cell_id=shadow_id,
                selection_mode="pre_outcome",
                manual_case_type="shadow_negative",
                heuristic_group="missing_rank_probe",
                scorer_id="sentence_transformer_cosine",
                near_tie_rate=0.5,
                posterior_failure_rate=0.45,
                uncertainty_width=0.7,
                triggers=["check"],
            ),
            _cell(
                cell_id=positive_id,
                selection_mode="pre_outcome",
                manual_case_type="positive_active",
                heuristic_group="missing_rank_probe",
                scorer_id="sentence_transformer_cosine",
                active_low_rate=0.6,
                posterior_failure_rate=0.2,
                uncertainty_width=0.35,
                triggers=["change"],
            ),
            _cell(
                cell_id="sentinel:phrase",
                selection_mode="outcome_informed_sentinel",
                manual_case_type="phrase_no_winner",
                heuristic_group="measured_missing_rank_high_failure_sentinel",
                scorer_id="sentence_transformer_cosine",
                underfilled_rate=0.8,
                posterior_failure_rate=0.5,
                uncertainty_width=0.7,
                triggers=["order"],
            ),
        ],
        "top_priority_cells": [
            {
                "cell_id": phrase_id,
                "manual_case_type": "phrase_no_winner",
                "normalized_data_help_priority": 1.0,
                "uncertainty_width": 0.8,
            },
            {
                "cell_id": shadow_id,
                "manual_case_type": "shadow_negative",
                "normalized_data_help_priority": 0.72,
                "uncertainty_width": 0.7,
            },
        ],
        "recommendations": [
            {
                "cell_id": phrase_id,
                "priority": "P0",
                "manual_discovery_rows": 4,
                "llm_discovery_rows": 16,
                "locked_eval_rows": 8,
            }
        ],
    }


def _cell(
    *,
    cell_id: str,
    selection_mode: str,
    manual_case_type: str,
    heuristic_group: str,
    scorer_id: str,
    posterior_failure_rate: float,
    uncertainty_width: float,
    triggers: list[str],
    underfilled_rate: float = 0.0,
    near_tie_rate: float = 0.0,
    active_low_rate: float = 0.0,
) -> dict[str, object]:
    return {
        "cell_id": cell_id,
        "selection_mode": selection_mode,
        "cell_split": "discovery",
        "manual_case_type": manual_case_type,
        "heuristic_group": heuristic_group,
        "scorer_id": scorer_id,
        "shadow_contract": "full",
        "source_rank_bin": "missing",
        "polysemy_band": "high_10_plus",
        "case_rows": 1,
        "failure_count": 0,
        "posterior_failure_rate": posterior_failure_rate,
        "uncertainty_interval": {"width": uncertainty_width},
        "features": {
            "underfilled_rate": underfilled_rate,
            "near_tie_rate": near_tie_rate,
            "active_low_rate": active_low_rate,
            "rank_missing_rate": 1.0,
        },
        "triggers": triggers,
    }


def _surface_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "formula_weight_surface_established",
        "sweep_reports": [
            {
                "sweep_id": "gated_phrase_shadow_positive_weight_sweep",
                "feature_curve_summaries": [
                    _feature_curve(
                        "phrase_no_winner.underfilled_rate",
                        "phrase_no_winner",
                        "underfilled_rate",
                        0.31,
                    ),
                    _feature_curve(
                        "shadow_negative.near_tie_rate",
                        "shadow_negative",
                        "near_tie_rate",
                        0.24,
                    ),
                    _feature_curve(
                        "positive_active.active_low_rate",
                        "positive_active",
                        "active_low_rate",
                        0.18,
                    ),
                ],
                "pairwise_curve_summaries": [
                    {
                        "curve_id": "phrase_no_winner.rank_missing_rate_vs_underfilled_rate",
                        "gate_id": "phrase_no_winner",
                        "left_feature": "rank_missing_rate",
                        "right_feature": "underfilled_rate",
                        "best_discovery_spearman": 0.29,
                        "best_locked_spearman": 0.21,
                        "curve_shape": "interior_peak",
                    }
                ],
            }
        ],
    }


def _feature_curve(
    curve_id: str,
    gate_id: str,
    feature_id: str,
    discovery_spearman: float,
) -> dict[str, object]:
    return {
        "curve_id": curve_id,
        "gate_id": gate_id,
        "feature_id": feature_id,
        "best_discovery_spearman": discovery_spearman,
        "best_locked_spearman": discovery_spearman - 0.03,
        "selected_alpha": 0.2,
        "best_alpha": 0.4,
        "curve_shape": "interior_peak",
    }


if __name__ == "__main__":
    unittest.main()
