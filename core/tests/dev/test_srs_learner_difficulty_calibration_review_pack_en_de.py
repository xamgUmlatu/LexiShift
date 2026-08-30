from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_calibration_review_pack_en_de import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyCalibrationReviewPackEnDeTests(unittest.TestCase):
    def test_builds_label_schema_split_and_signal_family_rows(self) -> None:
        report = build_report(
            signal_rows=_signal_rows_fixture(),
            target_count=20,
            band_sample_count=1,
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_de_learner_difficulty_calibration_review_pack_ready",
        )
        self.assertFalse(report["manual_labels_added"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertEqual(report["summary"]["row_count"], 13)
        self.assertEqual(report["summary"]["holdout_count"], 4)
        self.assertEqual(report["summary"]["calibration_count"], 9)
        self.assertIn("expected_learner_difficulty", report["label_schema"]["fields"])

        review_rows = report["review_rows"]
        self.assertEqual(review_rows[2]["recommended_split"], "holdout")
        self.assertEqual(review_rows[0]["recommended_split"], "calibration")
        self.assertIsNone(review_rows[0]["label"]["expected_learner_difficulty"])
        reasons = {reason for row in review_rows for reason in row["selection_reasons"]}
        self.assertIn("early_content_anchor", reasons)
        self.assertIn("topic_documented", reasons)
        self.assertIn("cognate_or_transparent", reasons)
        self.assertIn("long_or_compound", reasons)

        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Calibration Review Pack", markdown)
        self.assertIn("expected_learner_difficulty", markdown)
        self.assertIn("Review Rows", markdown)


def _signal_rows_fixture() -> list[dict[str, object]]:
    return [
        _row("sein", 1, "other", 0.03, other=1.0, translations=("be", "being")),
        _row("haus", 2, "noun", 0.12, translations=("house",), english_common=0.95),
        _row("spielen", 3, "verb", 0.18, topics=("games",), translations=("play",)),
        _row("problem", 4, "noun", 0.22, similarity=0.92, translations=("problem",)),
        _row("wasser", 5, "noun", 0.31, translations=("water",)),
        _row("schnell", 6, "adjective", 0.42, translations=("fast", "quick")),
        _row("fallen", 7, "verb", 0.51, similarity=0.80, translations=("fall",)),
        _row(
            "bank", 8, "noun", 0.58, translations=("bench", "bank", "banking"), translation_count=8
        ),
        _row("arbeitszimmer", 9, "noun", 0.66, length=0.34, compound=1.0, translations=("study",)),
        _row("ultraviolett", 10, "adjective", 0.74, length=0.25, translations=("ultraviolet",)),
        _row("unübersichtlichkeit", 11, "noun", 0.86, length=0.75, translations=("confusion",)),
        _row("zzztail", 12, "other", 0.94, translations=()),
        _row(
            "deterministisch",
            13,
            "adjective",
            0.99,
            similarity=0.70,
            translations=("deterministic",),
        ),
    ]


def _row(
    lemma: str,
    rank: int,
    pos_bucket: str,
    base: float,
    *,
    other: float = 0.0,
    length: float = 0.0,
    compound: float = 0.0,
    topics: tuple[str, ...] = (),
    translations: tuple[str, ...] = (),
    similarity: float = 0.0,
    english_common: float = 0.0,
    translation_count: int | None = None,
) -> dict[str, object]:
    return {
        "language_pair": "en-de",
        "lemma": lemma,
        "core_rank": float(rank),
        "pmw": max(1.0, 1000.0 / rank),
        "pos": pos_bucket.upper(),
        "pos_bucket": pos_bucket,
        "frequency_blend": base,
        "rank_base": base,
        "pmw_base": base,
        "content_pos_gate": 1.0 if pos_bucket in {"noun", "verb", "adjective", "adverb"} else 0.0,
        "other_pos_risk": other,
        "length_risk": length,
        "compound_like": compound,
        "topic_documented": 1.0 if topics else 0.0,
        "topics": list(topics),
        "translation_count": translation_count
        if translation_count is not None
        else len(translations),
        "translation_count_score": 0.5 if translation_count else 0.0,
        "translations": list(translations),
        "english_translation_tokens": list(translations),
        "english_translation_frequency_ease": english_common,
        "english_translation_similarity_ease": similarity,
        "reverse_support_count": min(3, len(translations)),
        "reverse_support_score": min(1.0, len(translations) / 3.0),
        "reverse_support_terms": list(translations),
    }


if __name__ == "__main__":
    unittest.main()
