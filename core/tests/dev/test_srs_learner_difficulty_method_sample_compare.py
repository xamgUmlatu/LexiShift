from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_method_sample_compare_en_ja import (  # noqa: E402
    _band_report,
    _bands,
    _dedupe_rows,
    _sample_spread_rows,
    _select_old_trace_record,
)


class TestSrsLearnerDifficultyMethodSampleCompare(unittest.TestCase):
    def test_select_old_trace_record_uses_requested_score(self) -> None:
        record = _select_old_trace_record(
            {
                "variant_records": [
                    {"variant_id": "a", "scores": {"balanced_score": 0.1}},
                    {"variant_id": "b", "scores": {"balanced_score": 0.9}},
                ]
            },
            score_key="balanced_score",
        )

        self.assertEqual(record["variant_id"], "b")

    def test_bands_partition_unit_interval(self) -> None:
        bands = _bands(0.25)

        self.assertEqual(
            [band["label"] for band in bands],
            ["0.00-0.25", "0.25-0.50", "0.50-0.75", "0.75-1.00"],
        )
        self.assertTrue(bands[-1]["is_last"])

    def test_sample_spread_rows_spreads_without_padding(self) -> None:
        rows = [{"lemma": str(index)} for index in range(10)]

        samples = _sample_spread_rows(rows, sample_count=4)

        self.assertEqual([row["lemma"] for row in samples], ["1", "3", "6", "8"])
        self.assertEqual(len(_sample_spread_rows(rows[:2], sample_count=4)), 2)

    def test_dedupe_rows_prefers_normal_vocab_and_lower_core_rank(self) -> None:
        rows = [
            _row("パン", "ぱん", "deprioritized_vocab", 1),
            _row("パン", "ぱん", "normal_vocab", 10),
            _row("犬", "いぬ", "normal_vocab", 3),
            _row("犬", "いぬ", "normal_vocab", 2),
        ]

        deduped = _dedupe_rows(rows)

        pan = next(row for row in deduped if row["lemma"] == "パン")
        dog = next(row for row in deduped if row["lemma"] == "犬")
        self.assertEqual(pan["candidate_state"], "normal_vocab")
        self.assertEqual(dog["core_rank"], 2)

    def test_band_report_counts_overlap_and_samples_by_model_score(self) -> None:
        band = _bands(0.5)[0]
        rows = [
            {
                "lemma": "a",
                "reading": "",
                "candidate_state": "normal_vocab",
                "old_score": 0.1,
                "new_score": 0.7,
            },
            {
                "lemma": "b",
                "reading": "",
                "candidate_state": "normal_vocab",
                "old_score": 0.2,
                "new_score": 0.2,
            },
            {
                "lemma": "c",
                "reading": "",
                "candidate_state": "normal_vocab",
                "old_score": 0.8,
                "new_score": 0.3,
            },
        ]

        report = _band_report(
            band,
            rows=rows,
            sample_count=10,
            sample_states=("normal_vocab",),
        )

        self.assertEqual(report["old_count"], 2)
        self.assertEqual(report["new_count"], 2)
        self.assertEqual(report["overlap_count"], 1)


def _row(
    lemma: str,
    reading: str,
    candidate_state: str,
    core_rank: int,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "reading": reading,
        "candidate_state": candidate_state,
        "core_rank": core_rank,
    }


if __name__ == "__main__":
    unittest.main()
