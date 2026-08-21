from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_polysemy_gate_diagnostic_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)
from srs_learner_difficulty_polysemy_sweep_en_es import PolysemyProfile  # noqa: E402


class SrsLearnerDifficultyPolysemyGateDiagnosticEnEsTests(unittest.TestCase):
    def test_compares_ungated_and_gated_profile_tradeoffs(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            formula_sweep_payload={},
            polysemy_sweep_payload={},
            calibration_payload={
                "labels": [
                    _label("parte", 0.24),
                    _label("más", 0.07),
                    _label("agua", 0.08),
                ]
            },
            holdout_payload={"labels": [_label("par", 0.34), _label("por", 0.18)]},
            candidate_id="spalex_blend__no_ls__no_cog__no_wf__no_guard",
            profiles=[
                _profile("ungated", pos_gate="none"),
                _profile("noun_adj_only", pos_gate="noun_adj_only"),
            ],
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_polysemy_gate_diagnostic_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        compared = report["summary"]["compared_profiles"]
        self.assertEqual(
            {row["profile"]["pos_gate"] for row in compared}, {"none", "noun_adj_only"}
        )

        gated = next(
            row for row in report["diagnostics"] if row["profile"]["pos_gate"] == "noun_adj_only"
        )
        ungated = next(row for row in report["diagnostics"] if row["profile"]["pos_gate"] == "none")
        gated_cal_moves = {row["lemma"] for row in gated["calibration"]["largest_score_moves"]}
        ungated_cal_moves = {row["lemma"] for row in ungated["calibration"]["largest_score_moves"]}

        self.assertIn("parte", gated_cal_moves)
        self.assertNotIn("más", gated_cal_moves)
        self.assertIn("más", ungated_cal_moves)
        self.assertIn("metric_deltas", gated["holdout"])
        self.assertIn("pairwise_changes", gated["holdout"])

        markdown = render_markdown(report)
        self.assertIn("en-es Polysemy Gate Diagnostic", markdown)
        self.assertIn("noun_adj_only", markdown)


def _profile(profile_id: str, *, pos_gate: str) -> PolysemyProfile:
    return PolysemyProfile(
        profile_id=profile_id,
        sense_ceiling=8.0,
        entry_weight=0.15,
        weight=0.30,
        cap=0.16,
        early_cutoff=0.50,
        early_power=1.0,
        common_min_zipf=4.5,
        learner_source_gate="none",
        pos_gate=pos_gate,
        min_senses=4,
    )


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("parte", 0.05, sense_count=8, entry_count=2, source_count=0.666667, zipf=6.0),
        _row("par", 0.14, sense_count=7, entry_count=3, source_count=0.666667, zipf=5.1),
        _row("agua", 0.08, sense_count=7, entry_count=1, source_count=1.0, zipf=5.5),
        _row(
            "más",
            0.09,
            sense_count=9,
            entry_count=3,
            source_count=0.666667,
            zipf=6.6,
            pos_bucket="adverb",
        ),
        _row(
            "por",
            0.10,
            sense_count=18,
            entry_count=2,
            source_count=0.666667,
            zipf=7.0,
            pos_bucket="other",
            function_risk=1.0,
            other_risk=1.0,
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
    function_risk: float = 0.0,
    other_risk: float = 0.0,
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
            "pos_function_risk": function_risk,
            "pos_other_risk": other_risk,
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
        "expected_difficulty_band": "fixture",
        "expected_candidate_state": "normal_vocab",
    }
