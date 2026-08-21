from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_final_ranking_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyFinalRankingEnEsTests(unittest.TestCase):
    def test_exports_full_corrected_ranking_with_manual_metadata(self) -> None:
        report, csv_rows = build_report(
            formula_report=_formula_report_fixture(),
            sweep_payload={},
            calibration_payload={
                "calibration_id": "fixture-cal",
                "labels": [
                    _label("parte", 0.24),
                    _label("hoy", 0.05),
                    _label("agua", 0.08),
                ],
            },
            holdout_payload={"holdout_id": "fixture-holdout", "labels": [_label("son", 0.12)]},
            corrections_payload={
                "status": "sidecar_review_input",
                "corrections": [
                    _floor("parte", 0.24),
                    _override("hoy", 0.05),
                    _override(
                        "son",
                        0.12,
                        correction_types=["score_override", "restricted_admission"],
                        admission_override="inflected_or_nonlemma_form",
                    ),
                ],
            },
            candidate_id="spalex_blend__no_ls__no_cog__no_wf__no_guard",
            first_review_count=4,
            csv_out=Path("docs/test_outputs/fixture.csv"),
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_final_ranking_review_ready",
        )
        self.assertFalse(report["runtime_behavior_changed"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertEqual(report["correction_summary"]["moved_count"], 3)
        self.assertEqual([row["lemma"] for row in csv_rows], ["hoy", "agua", "son", "parte"])

        son = next(row for row in csv_rows if row["lemma"] == "son")
        self.assertEqual(son["score"], 0.12)
        self.assertEqual(son["correction_types"], "score_override,restricted_admission")
        self.assertEqual(son["admission_override"], "inflected_or_nonlemma_form")
        self.assertEqual(son["topic_stretch_allowed"], "False")

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Final Ranking Review", markdown)
        self.assertIn("Manual Correction Summary", markdown)
        self.assertIn("inflected_or_nonlemma_form", markdown)


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("parte", 0.05, pos_bucket="noun"),
        _row("hoy", 0.10, pos_bucket="adverb"),
        _row("son", 0.21, pos_bucket="verb"),
        _row("agua", 0.08, pos_bucket="noun"),
    ]
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": len(rows)},
        "rows": rows,
    }


def _row(lemma: str, score: float, *, pos_bucket: str) -> dict[str, object]:
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
            "learner_source_count": 1.0,
            "learner_source_known": 1.0,
            "cognate_rescue": 0.0,
            "false_friend_caution": 0.0,
            "weak_form_risk": 0.0,
            "pos_function_risk": 0.0,
            "pos_other_risk": 0.0,
        },
        "dictionary": {
            "sense_count": 1,
            "entry_count": 1,
            "marked_terms": [],
            "topics": [],
        },
        "variant_scores": {"spalex_blend_frequency": score},
    }


def _label(lemma: str, expected: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_learner_difficulty": expected,
        "expected_difficulty_band": "fixture",
        "expected_candidate_state": "normal_vocab",
    }


def _floor(lemma: str, min_score: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "status": "active",
        "correction_types": ["score_floor"],
        "min_score": min_score,
        "admission_override": "normal_vocab",
        "rationale": "fixture floor",
    }


def _override(
    lemma: str,
    score: float,
    *,
    correction_types: list[str] | None = None,
    admission_override: str = "normal_vocab",
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "status": "active",
        "correction_types": correction_types or ["score_override"],
        "score_override": score,
        "admission_override": admission_override,
        "rationale": "fixture override",
    }
