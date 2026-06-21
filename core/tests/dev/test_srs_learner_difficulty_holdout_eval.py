from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_holdout_eval_en_ja import (  # noqa: E402
    _select_trace_rows,
    holdout_json_payload,
    observed_for_context,
    parse_holdout_review_markdown,
)


class TestSrsLearnerDifficultyHoldoutEval(unittest.TestCase):
    def test_parse_holdout_review_markdown_numeric_and_treatment_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "holdout.md"
            path.write_text(
                "\n".join(
                    [
                        "| # | lemma | reading | expected_difficulty | treatment | notes |",
                        "|---:|---|---|---:|---|---|",
                        "| 1 | 作る | つくる | 0.02 |  |  |",
                        "| 2 | デ杯 | ではい |  | topic_only | Sports-specific. |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = parse_holdout_review_markdown(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].lemma, "作る")
        self.assertEqual(rows[0].expected_difficulty, 0.02)
        self.assertEqual(rows[1].treatment, "topic_only")
        self.assertIsNone(rows[1].expected_difficulty)

    def test_holdout_json_payload_maps_numeric_and_topic_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "holdout.md"
            path.write_text("", encoding="utf-8")
            rows = [
                *parse_holdout_review_markdown(
                    _write_review(
                        path,
                        [
                            "| 1 | 作る | つくる | 0.02 |  |  |",
                            "| 2 | デ杯 | ではい |  | topic_only | Sports-specific. |",
                        ],
                    )
                )
            ]

            payload = holdout_json_payload(rows, review_markdown=path)

        labels = payload["labels"]
        self.assertEqual(labels[0]["expected_candidate_state"], "normal_vocab")
        self.assertEqual(labels[0]["expected_difficulty_band"], "beginner")
        self.assertEqual(labels[1]["expected_candidate_state"], "deprioritized_vocab")
        self.assertIsNone(labels[1]["expected_difficulty_band"])

    def test_observed_for_context_uses_fallback_for_unmapped_rows(self) -> None:
        observed = observed_for_context(
            np.asarray([0.1, 0.2], dtype=np.float32),
            {"component_indices": np.asarray([1, -1], dtype=np.int64)},
            fallback_values=np.asarray([0.9, 0.8], dtype=np.float32),
        )

        self.assertAlmostEqual(float(observed[0]), 0.2, places=6)
        self.assertAlmostEqual(float(observed[1]), 0.8, places=6)

    def test_select_trace_rows_takes_leaders_from_each_score_key(self) -> None:
        records = {
            "balanced": {
                "variant_id": "balanced",
                "scores": {"balanced_score": 0.9, "high_tail_score": 0.1},
            },
            "tail": {
                "variant_id": "tail",
                "scores": {"balanced_score": 0.5, "high_tail_score": 1.0},
            },
            "middle": {
                "variant_id": "middle",
                "scores": {"balanced_score": 0.7, "high_tail_score": 0.5},
            },
        }

        rows = _select_trace_rows(
            records,
            trace_report={"score_keys": ["balanced_score", "high_tail_score"]},
            limit=2,
            top_per_score=1,
        )

        self.assertEqual([row["variant_id"] for row in rows], ["balanced", "tail"])


def _write_review(path: Path, rows: list[str]) -> Path:
    path.write_text(
        "\n".join(
            [
                "| # | lemma | reading | expected_difficulty | treatment | notes |",
                "|---:|---|---|---:|---|---|",
                *rows,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
