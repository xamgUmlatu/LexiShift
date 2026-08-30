from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_contender_samples_en_ja import (  # noqa: E402
    _band_report,
    _canonical_scored_rows,
    _sample_band_rows,
)
from srs_learner_difficulty_signal_sweep_en_ja import FormulaVariant  # noqa: E402
from srs_learner_difficulty_normalization import difficulty_bands  # noqa: E402


class TestSrsLearnerDifficultyContenderSamples(unittest.TestCase):
    def test_difficulty_bands_partition_unit_interval(self) -> None:
        bands = difficulty_bands(0.25)

        self.assertEqual(
            [band.label for band in bands], ["0.00-0.25", "0.25-0.50", "0.50-0.75", "0.75-1.00"]
        )

    def test_canonical_rows_dedupe_by_lemma_reading_and_prefer_normal_vocab(self) -> None:
        rows = [
            _row(
                "パン",
                "ぱん",
                0.30,
                candidate_state="deprioritized_vocab",
                problem_class="proper_noun",
                core_rank=1,
            ),
            _row(
                "パン",
                "ぱん",
                0.31,
                candidate_state="normal_vocab",
                problem_class="normal_vocab",
                core_rank=5,
            ),
            _row("僕", "ぼく", 0.40),
            _row("僕", "しもべ", 0.80),
        ]

        canonical = _canonical_scored_rows(rows, dedupe_key="lemma_reading")

        self.assertEqual(len(canonical), 3)
        pan = next(row for row in canonical if row["lemma"] == "パン")
        self.assertEqual(pan["candidate_state"], "normal_vocab")
        self.assertEqual(
            sorted((row["lemma"], row["reading"]) for row in canonical),
            [("パン", "ぱん"), ("僕", "しもべ"), ("僕", "ぼく")],
        )

    def test_band_report_does_not_backfill_from_neighboring_bands(self) -> None:
        bands = difficulty_bands(0.25)
        rows = [
            _row("低い", "ひくい", 0.10),
            _row("中央", "ちゅうおう", 0.55),
            _row("高い", "たかい", 0.90),
        ]

        report = _band_report(
            bands[1],
            variant=FormulaVariant(
                variant_id="frequency_only",
                description="",
                weights={"frequency": 1.0},
            ),
            raw_rows=rows,
            canonical_rows=rows,
            sample_count=10,
        )

        self.assertEqual(report["label"], "0.25-0.50")
        self.assertEqual(report["raw_count"], 0)
        self.assertEqual(report["unique_count"], 0)
        self.assertEqual(report["sample_count"], 0)
        self.assertTrue(report["underfilled"])
        self.assertEqual(report["samples"], [])

    def test_sample_band_rows_spreads_within_band_without_padding(self) -> None:
        rows = [_row(str(index), "", index / 100) for index in range(10, 20)]

        samples = _sample_band_rows(rows, sample_count=4)

        self.assertEqual(len(samples), 4)
        self.assertEqual([row["lemma"] for row in samples], ["11", "13", "16", "18"])
        self.assertEqual(len(_sample_band_rows(rows[:2], sample_count=4)), 2)


def _row(
    lemma: str,
    reading: str,
    difficulty: float,
    *,
    candidate_state: str = "normal_vocab",
    problem_class: str = "normal_vocab",
    core_rank: int = 10,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "difficulty": difficulty,
        "candidate_state": candidate_state,
        "problem_class": problem_class,
        "core_rank": core_rank,
        "candidate_identity_key": f"id:{lemma}:{reading}:{difficulty}",
    }


if __name__ == "__main__":
    unittest.main()
