from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_polysemy_sweep_en_es import (  # noqa: E402
    PolysemyProfile,
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyPolysemySweepEnEsTests(unittest.TestCase):
    def test_sweeps_bounded_tax_without_taxing_all_source_beginner(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            sweep_payload={},
            calibration_payload={
                "labels": [
                    _label("parte", 0.24),
                    _label("agua", 0.08),
                    _label("idea", 0.08),
                    _label("más", 0.07),
                ]
            },
            holdout_payload={"labels": [_label("par", 0.34)]},
            candidate_id="spalex_blend__no_ls__no_cog__no_wf__no_guard",
            profiles=[
                PolysemyProfile(
                    profile_id="fixture_polysemy_tax",
                    sense_ceiling=8.0,
                    entry_weight=0.15,
                    weight=0.30,
                    cap=0.16,
                    early_cutoff=0.50,
                    early_power=1.0,
                    common_min_zipf=4.5,
                    learner_source_gate="not_all_sources",
                    pos_gate="content_only",
                    min_senses=4,
                )
            ],
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_polysemy_sweep_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        self.assertFalse(report["manual_labels_added"])
        self.assertEqual(report["method"]["profile_count"], 1)
        self.assertEqual(report["inputs"]["focus_row_count"], 2)
        self.assertEqual(report["inputs"]["protected_row_count"], 3)

        selected = report["selected_profile_details"][0]
        focus_by_lemma = {row["lemma"]: row for row in selected["focus_rows"]}
        self.assertGreater(focus_by_lemma["parte"]["after"], focus_by_lemma["parte"]["before"])
        self.assertLess(focus_by_lemma["parte"]["error_delta"], 0.0)
        self.assertGreater(focus_by_lemma["par"]["after"], focus_by_lemma["par"]["before"])

        raises_by_lemma = {row["lemma"]: row for row in selected["largest_raises"]}
        self.assertNotIn("agua", raises_by_lemma)
        self.assertNotIn("más", raises_by_lemma)
        self.assertEqual(selected["protected_regression_count"], 0)

        markdown = render_markdown(report)
        self.assertIn("en-es Polysemy Tax Sweep", markdown)
        self.assertIn("Focus rows", markdown)
        self.assertIn("fixture_polysemy_tax", markdown)


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("parte", 0.05, sense_count=8, entry_count=2, source_count=0.666667, zipf=6.0),
        _row("par", 0.14, sense_count=7, entry_count=3, source_count=0.666667, zipf=5.1),
        _row("agua", 0.08, sense_count=7, entry_count=1, source_count=1.0, zipf=5.5),
        _row("idea", 0.08, sense_count=1, entry_count=1, source_count=0.666667, zipf=5.4),
        _row(
            "más",
            0.09,
            sense_count=9,
            entry_count=3,
            source_count=0.666667,
            zipf=6.6,
            pos_bucket="adverb",
        ),
    ]
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": len(rows)},
        "rows": rows,
    }


def _row(
    lemma: str,
    score: float,
    *,
    sense_count: int,
    entry_count: int,
    source_count: float,
    zipf: float,
    pos_bucket: str = "noun",
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "candidate_state": "normal_vocab",
        "pos": pos_bucket,
        "pos_bucket": pos_bucket,
        "spalex_rank": 100,
        "translations": [lemma],
        "components": {
            "spalex_blend": score,
            "zipf_base": score,
            "rank_base": score,
            "wordfreq_zipf": zipf,
            "learner_source_count": source_count,
            "learner_source_known": 1.0,
            "pos_content_gate": 0.7 if pos_bucket == "adverb" else 1.0,
            "pos_function_risk": 0.0,
            "pos_other_risk": 0.0,
        },
        "dictionary": {
            "sense_count": sense_count,
            "entry_count": entry_count,
            "marked_terms": [],
            "topics": [],
        },
        "variant_scores": {
            "spalex_blend_frequency": score,
        },
    }


def _label(lemma: str, expected: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_learner_difficulty": expected,
        "expected_candidate_state": "normal_vocab",
        "expected_difficulty_band": "fixture",
    }


if __name__ == "__main__":
    unittest.main()
