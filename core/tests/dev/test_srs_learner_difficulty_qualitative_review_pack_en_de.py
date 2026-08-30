from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_qualitative_review_pack_en_de import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyQualitativeReviewPackEnDeTests(unittest.TestCase):
    def test_builds_review_pack_from_signal_rows_and_labels(self) -> None:
        report = build_report(
            signal_rows=[
                _row("sein", 1, 0.03, "noun"),
                _row("katze", 2, 0.38, "noun"),
                _row("mittwochmorgen", 3, 0.66, "other", length=0.55, compound=1.0),
                _row("überraschungsangriff", 4, 0.92, "other", length=0.85, compound=1.0),
                _row("ander", 5, 0.09, "other"),
            ],
            sweep_payload={},
            calibration_payload={
                "labels": [
                    _label("sein", 0.02, "normal_vocab", []),
                    _label("katze", 0.08, "normal_vocab", []),
                    _label("mittwochmorgen", 0.30, "normal_vocab", ["compound_or_long_form"]),
                    _label(
                        "ander",
                        None,
                        "restricted_admission",
                        ["bad_standalone_srs_item"],
                    ),
                ]
            },
            holdout_payload={
                "labels": [
                    _label(
                        "überraschungsangriff",
                        0.78,
                        "normal_vocab",
                        ["compound_or_long_form"],
                    )
                ]
            },
            candidate_id="raw_frequency_blend",
            candidate_grid="refined",
            band_sample_count=2,
            beginner_count=3,
            residual_count=3,
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_de_learner_difficulty_qualitative_review_pack_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        self.assertFalse(report["manual_labels_added"])
        self.assertEqual(report["summary"]["candidate_rows_scanned"], 5)
        self.assertEqual(report["summary"]["thin_band_count"], 10)
        self.assertGreater(report["summary"]["thin_band_sample_count"], 0)

        residuals = {row["lemma"]: row for row in report["labeled_residual_errors"]}
        self.assertIn("katze", residuals)
        self.assertIn("mittwochmorgen", residuals)
        self.assertNotIn("ander", residuals)
        self.assertEqual(residuals["katze"]["direction"], "too_hard")

        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Qualitative Review Pack", markdown)
        self.assertIn("Thin-Band Samples", markdown)
        self.assertIn("Largest Labeled Residuals", markdown)


def _row(
    lemma: str,
    rank: int,
    score: float,
    pos_bucket: str,
    *,
    length: float = 0.0,
    compound: float = 0.0,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "frequency_blend": score,
        "rank_base": score,
        "pmw_base": score,
        "pos": pos_bucket,
        "pos_bucket": pos_bucket,
        "core_rank": rank,
        "translations": [f"{lemma} translation"],
        "length_risk": length,
        "compound_like": compound,
        "translation_count_score": 0.2,
        "reverse_support_score": 0.3,
    }


def _label(
    lemma: str,
    expected: float | None,
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
