from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_repaired_full_band_formula_sweep_en_es import (  # noqa: E402
    build_repaired_full_band_formula_sweep_report,
    render_repaired_full_band_formula_sweep_markdown,
)


class SemanticVetoRepairedFullBandFormulaSweepTests(unittest.TestCase):
    def test_sweeps_programmatic_family_formulas_on_approved_dataset(self) -> None:
        report = build_repaired_full_band_formula_sweep_report(
            dataset_payload=_dataset(),
            score_surface_payload=_score_surface(),
            generated_at="2026-05-08T00:00:00Z",
            top_k=1,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "repaired_full_band_formula_sweep_established")
        self.assertEqual(report["summary"]["family_count"], 4)
        self.assertEqual(report["summary"]["observation_count"], 4)
        self.assertTrue(report["e2e_checks"]["dataset_is_user_approved"])
        self.assertTrue(
            report["e2e_checks"]["formula_features_do_not_use_gold_or_prediction_labels"]
        )
        self.assertGreater(report["summary"]["fixed_formula_count"], 0)
        self.assertGreater(report["summary"]["sweep_formula_count"], 0)
        self.assertTrue(report["summary"]["best_by_scope"])
        self.assertTrue(report["top_need_rows"])

        markdown = render_repaired_full_band_formula_sweep_markdown(report)
        self.assertIn("Repaired-Full Band Formula Sweep", markdown)
        self.assertIn("Top Need Rows", markdown)


def _dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "unit",
        "manual_review_state": "approved_by_user",
        "families": [
            _family("family-0", "change", "cambio", "zipf_5_plus_very_common", "high_10_plus", 2),
            _family("family-1", "bank", "banco", "zipf_4_to_5_common", "medium_4_to_9", 1),
            _family("family-2", "cat", "gato", "zipf_3_to_4_mid", "low_1_to_3", 0),
            _family("family-3", "bouillon", "caldo", "zipf_below_3_rare", "low_1_to_3", 0),
        ],
    }


def _family(
    family_id: str,
    trigger: str,
    target: str,
    source_band: str,
    polysemy: str,
    shadow_count: int,
) -> dict[str, object]:
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {"target_lemma": target},
        "shadows": [{"target_lemma": f"shadow-{index}"} for index in range(shadow_count)],
        "cases": [
            {
                "slice_dimensions": {
                    "source_zipf_band_en": [source_band],
                    "target_zipf_band_es": ["zipf_4_to_5_common"],
                    "polysemy_band": [polysemy],
                    "pos_shape": ["cross_pos_polysemy" if shadow_count else "single_sense"],
                }
            }
        ],
    }


def _score_surface() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "full_family_score_surface_established",
        "row_results": [
            _row("family-0", "change", "replace", "abstain"),
            _row("family-1", "bank", "abstain", "replace"),
            _row("family-2", "cat", "replace", "replace"),
            _row("family-3", "bouillon", "abstain", "abstain"),
        ],
    }


def _row(family_id: str, trigger: str, gold: str, predicted: str) -> dict[str, object]:
    error = "correct"
    if gold == "replace" and predicted == "abstain":
        error = "false_abstain"
    if gold == "abstain" and predicted == "replace":
        error = "harmful_replace"
    return {
        "case_id": f"{family_id}:001",
        "family_id": family_id,
        "trigger": trigger,
        "scorer_id": "sentence_transformer_cosine",
        "gold_decision": gold,
        "predicted_decision": predicted,
        "error_type": error,
    }


if __name__ == "__main__":
    unittest.main()
