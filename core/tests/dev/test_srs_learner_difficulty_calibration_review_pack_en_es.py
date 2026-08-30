from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_calibration_review_pack_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyCalibrationReviewPackEnEsTests(unittest.TestCase):
    def test_builds_label_schema_split_and_stratified_rows(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            target_count=12,
            band_sample_count=1,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_calibration_review_pack_ready",
        )
        self.assertFalse(report["manual_labels_added"])
        self.assertEqual(report["summary"]["row_count"], 10)
        self.assertEqual(report["summary"]["holdout_count"], 3)
        self.assertEqual(report["summary"]["calibration_count"], 7)
        self.assertIn("expected_learner_difficulty", report["label_schema"]["fields"])

        review_rows = report["review_rows"]
        self.assertEqual(review_rows[2]["recommended_split"], "holdout")
        self.assertEqual(review_rows[0]["recommended_split"], "calibration")
        self.assertEqual(review_rows[0]["label"]["expected_learner_difficulty"], None)
        all_reasons = {reason for row in review_rows for reason in row["selection_reasons"]}
        self.assertIn("tail_guard_raise", all_reasons)
        self.assertIn("cognate_lower", all_reasons)

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Calibration Review Pack", markdown)
        self.assertIn("expected_learner_difficulty", markdown)
        self.assertIn("Review Rows", markdown)

    def test_balanced_profile_prioritizes_content_and_keeps_tail_anchors(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            target_count=10,
            band_sample_count=1,
            selection_profile="balanced",
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_balanced_calibration_review_pack_ready",
        )
        self.assertEqual(report["method"]["selection_profile"], "balanced")
        self.assertEqual(report["summary"]["row_count"], 10)

        reasons = {reason for row in report["review_rows"] for reason in row["selection_reasons"]}
        self.assertIn("function_anchor", reasons)
        self.assertIn("core_content_low_rank", reasons)
        self.assertTrue(any(reason.startswith("content_band_") for reason in reasons))
        self.assertIn("tail_guard_raise_marked", reasons)

        markdown = render_markdown(report)
        self.assertIn("Selection profile: `balanced`", markdown)


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("que", 1, "pronoun", "other", 0.02, 0.02, 0.10, 0.02, pos_function=1.0, pos_other=1.0),
        _row("hospital", 2, "noun", "noun", 0.12, 0.12, 0.08, 0.06, cognate=0.7),
        _row("social", 3, "adjective", "adjective", 0.22, 0.22, 0.16, 0.16, cognate=0.6),
        _row("familia", 4, "noun", "noun", 0.35, 0.35, 0.34, 0.34, cognate=0.2),
        _row("actor", 5, "noun", "noun", 0.45, 0.45, 0.40, 0.40, cognate=0.4),
        _row("lecho", 6, "noun", "noun", 0.55, 0.55, 0.55, 0.55),
        _row("rareza", 7, "noun", "noun", 0.65, 0.78, 0.70, 0.65, marked=1.0),
        _row("otro", 8, "other", "other", 0.75, 0.84, 0.85, 0.75, pos_function=0.65, pos_other=1.0),
        _row(
            "recondito",
            9,
            "other",
            "other",
            0.85,
            0.95,
            0.95,
            0.85,
            pos_function=0.65,
            pos_other=1.0,
        ),
        _row(
            "ultimísimo",
            10,
            "other",
            "other",
            0.95,
            0.98,
            0.99,
            0.95,
            pos_function=0.65,
            pos_other=1.0,
        ),
    ]
    return {
        "decision": "en_es_formula_probe_ready",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 10},
        "rows": rows,
    }


def _row(
    lemma: str,
    rank: int,
    pos: str,
    pos_bucket: str,
    base: float,
    tail: float,
    transfer: float,
    cognate_score: float,
    *,
    pos_function: float = 0.0,
    pos_other: float = 0.0,
    marked: float = 0.0,
    cognate: float = 0.0,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "spalex_rank": float(rank),
        "pos": pos,
        "pos_bucket": pos_bucket,
        "candidate_state": "normal_vocab",
        "translations": [lemma],
        "variant_scores": {
            "spalex_blend_frequency": base,
            "tail_guard_medium": tail,
            "transfer_all_light": transfer,
            "cognate_rescue_light": cognate_score,
        },
        "components": {
            "pos_function_risk": pos_function,
            "pos_other_risk": pos_other,
            "dict_marked_usage_risk": marked,
            "gated_dict_marked_usage_risk": marked,
            "dict_ambiguity": 0.2 if marked else 0.0,
            "tail_dict_ambiguity": 0.1 if marked else 0.0,
            "weak_form_risk": 0.0,
            "char_length_difficulty": 0.3 if len(lemma) >= 8 else 0.0,
            "diacritic_burden_light": 0.2 if any(ch in lemma for ch in "áéíóúñ") else 0.0,
            "cognate_rescue": cognate,
            "false_friend_caution": 0.0,
        },
    }


if __name__ == "__main__":
    unittest.main()
