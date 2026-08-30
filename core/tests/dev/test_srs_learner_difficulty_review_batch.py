from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_review_batch_en_ja import (  # noqa: E402
    MatrixRow,
    _band_quotas,
    _kanji_chars,
    _select_holdout_candidates,
    render_simple_review_markdown,
)


class TestSrsLearnerDifficultyReviewBatch(unittest.TestCase):
    def test_kanji_chars_extracts_cjk_without_kana_or_latin(self) -> None:
        self.assertEqual(_kanji_chars("胸Bむね々猫"), {"胸", "猫"})

    def test_band_quotas_keep_requested_total(self) -> None:
        quotas = _band_quotas(173, band_count=20)

        self.assertEqual(sum(quotas), 173)
        self.assertEqual(quotas[:3], [9, 9, 9])
        self.assertEqual(quotas[-1], 8)

    def test_holdout_selection_excludes_existing_and_selected_kanji(self) -> None:
        rows = [
            _row("胸", "むね", 0.10, core_rank=10),
            _row("猫", "ねこ", 0.12, core_rank=11),
            _row("森", "もり", 0.13, core_rank=12),
            _row("海", "うみ", 0.14, core_rank=13),
            _row("山", "やま", 0.15, core_rank=14),
            _row("胸筋", "きょうきん", 0.16, core_rank=15),
        ]

        selected = _select_holdout_candidates(
            rows,
            target_count=3,
            blocked_keys=set(),
            blocked_kanji={"胸"},
            prediction_context=None,
        )

        self.assertEqual(len(selected), 3)
        selected_kanji = [kanji for row in selected for kanji in row["kanji"]]
        self.assertNotIn("胸", selected_kanji)
        self.assertEqual(len(selected_kanji), len(set(selected_kanji)))

    def test_simple_review_markdown_hides_diagnostic_scores(self) -> None:
        markdown = render_simple_review_markdown(
            {
                "fresh_holdout_candidates": [
                    {
                        "lemma": "作る",
                        "reading": "つくる",
                        "target_curve_position": 0.02,
                        "signals": {"frequency": 0.4},
                    }
                ]
            },
            rows_key="fresh_holdout_candidates",
            title="review",
            purpose="purpose",
        )

        self.assertIn("| 1 | 作る | つくる |  |  |  |", markdown)
        self.assertNotIn("target_curve_position", markdown)
        self.assertNotIn("frequency", markdown)
        self.assertNotIn("curve", markdown)


def _row(
    lemma: str,
    reading: str,
    target_curve_position: float,
    *,
    core_rank: int,
) -> MatrixRow:
    return MatrixRow(
        index=core_rank,
        identity_key=f"id:{lemma}:{reading}",
        lemma=lemma,
        reading=reading,
        candidate_state="normal_vocab",
        problem_class="normal_vocab",
        core_rank=float(core_rank),
        current_value=target_curve_position,
        frequency_value=target_curve_position,
        target_curve_position=target_curve_position,
        signals={"frequency": target_curve_position},
    )


if __name__ == "__main__":
    unittest.main()
