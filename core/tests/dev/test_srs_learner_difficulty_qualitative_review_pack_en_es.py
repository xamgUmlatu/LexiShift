from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_qualitative_review_pack_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyQualitativeReviewPackEnEsTests(unittest.TestCase):
    def test_builds_combined_current_quality_pack(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            sweep_payload={},
            calibration_payload={
                "labels": [
                    _label("zapato", 0.20, "normal_vocab", ["ordinary_core_word"]),
                    _label("arcaísmo", 0.88, "normal_vocab", ["marked_rare_or_regional"]),
                ]
            },
            holdout_payload={"labels": [_label("hospital", 0.12, "normal_vocab", [])]},
            form_preference_payload={
                "decision": "fixture_form_preference",
                "audit_rows": [
                    {
                        "lemma": "gafa",
                        "preferred_mate": "gafas",
                        "preferred_mate_in_candidate_rows": False,
                        "mate_gap": 1.49,
                        "current_score": 0.82,
                        "severity": "strong",
                        "support": {"pos_bucket": "other"},
                        "translations": ["glasses"],
                    }
                ],
            },
            candidate_id="spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard",
            band_sample_count=2,
            beginner_count=3,
            residual_count=3,
            form_preference_count=2,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_qualitative_review_pack_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        self.assertFalse(report["manual_labels_added"])
        self.assertEqual(report["summary"]["thin_band_count"], 10)
        self.assertGreater(report["summary"]["thin_band_sample_count"], 0)
        self.assertGreaterEqual(report["summary"]["beginner_row_count"], 2)

        residuals = {row["lemma"]: row for row in report["labeled_residual_errors"]}
        self.assertIn("zapato", residuals)
        self.assertEqual(residuals["zapato"]["direction"], "too_hard")
        self.assertIn("gafa", [row["lemma"] for row in report["form_preference_concerns"]])

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Qualitative Review Pack", markdown)
        self.assertIn("Thin-Band Samples", markdown)
        self.assertIn("Largest Labeled Residuals", markdown)
        self.assertIn("Form-Preference Concerns", markdown)


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("casa", 10, 0.05, "noun", "noun"),
        _row("hospital", 20, 0.14, "noun", "noun", cognate=0.20),
        _row("zapato", 30, 0.55, "noun", "noun"),
        _row("global", 40, 0.36, "adjective", "adjective", cognate=0.50),
        _row("arcaísmo", 50, 0.72, "noun", "noun", marked=0.80),
        _row("gafa", 60, 0.82, "other", "other", other=1.0),
        _row("desoxirribonucleico", 70, 0.96, "adjective", "adjective"),
    ]
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": len(rows)},
        "rows": rows,
    }


def _row(
    lemma: str,
    rank: int,
    score: float,
    pos: str,
    pos_bucket: str,
    *,
    cognate: float = 0.0,
    marked: float = 0.0,
    other: float = 0.0,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "spalex_rank": rank,
        "pos": pos,
        "pos_bucket": pos_bucket,
        "candidate_state": "normal_vocab",
        "translations": [f"{lemma} translation"],
        "components": {
            "spalex_blend": score,
            "zipf_base": score,
            "rank_base": score,
            "learner_core_gap_zipf_confident": 0.0,
            "cognate_rescue": cognate,
            "false_friend_caution": 0.0,
            "gated_dict_marked_usage_risk": marked,
            "dict_marked_usage_risk": marked,
            "pos_other_risk": other,
        },
        "dictionary": {
            "entry_count": 1,
            "sense_count": 1,
            "marked_terms": ["rare"] if marked else [],
            "topics": [],
        },
        "variant_scores": {
            "spalex_blend_frequency": score,
            "learner_source_zipf_medium": score,
        },
    }


def _label(
    lemma: str,
    expected: float,
    state: str,
    flags: list[str],
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": state,
        "expected_learner_difficulty": expected,
        "review_flags": flags,
    }


if __name__ == "__main__":
    unittest.main()
