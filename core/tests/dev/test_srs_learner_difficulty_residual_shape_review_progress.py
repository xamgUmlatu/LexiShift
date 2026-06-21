from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_shape_review_progress_en_ja import (  # noqa: E402
    build_report,
    render_markdown,
)


class TestSrsLearnerDifficultyResidualShapeReviewProgress(unittest.TestCase):
    def test_counts_numeric_vocab_and_policy_labels_separately(self) -> None:
        report = build_report(
            review_pack_path=_write_json(
                {
                    "review_rows": [
                        {
                            "review_bucket": "cell_a",
                            "lemma": "火曜",
                            "reading": "かよう",
                            "jmdict_glosses": ["Tuesday"],
                        },
                        {
                            "review_bucket": "cell_d",
                            "lemma": "磯躑躅",
                            "reading": "いそつつじ",
                            "jmdict_glosses": ["plant species"],
                        },
                        {
                            "review_bucket": "cell_b",
                            "lemma": "未評",
                            "reading": "みひょう",
                            "jmdict_glosses": ["unreviewed"],
                        },
                    ]
                }
            ),
            triage_path=_write_json(
                {
                    "triage_rows": [
                        {
                            "row_number": 1,
                            "review_route": "possible_overhard_general_vocab",
                            "review_priority": "high",
                        },
                        {
                            "row_number": 2,
                            "review_route": "tail_topic_or_omit_review",
                            "review_priority": "high",
                        },
                        {
                            "row_number": 3,
                            "review_route": "burden_shape_review",
                            "review_priority": "medium",
                        },
                    ]
                }
            ),
            labels_path=_write_json(
                {
                    "labels": [
                        {
                            "lemma": "火曜",
                            "expected_reading": "かよう",
                            "treatment": "vocab",
                            "expected_candidate_state": "normal_vocab",
                            "expected_learner_difficulty": 0.14,
                        },
                        {
                            "lemma": "磯躑躅",
                            "expected_reading": "いそつつじ",
                            "treatment": "topic_only",
                            "expected_candidate_state": "deprioritized_vocab",
                            "reference_difficulty": 0.98,
                        },
                    ]
                }
            ),
            next_batch_limit=5,
        )

        counts = report["counts"]
        self.assertEqual(counts["reviewed_rows"], 2)
        self.assertEqual(counts["numeric_vocab_labels"], 1)
        self.assertEqual(counts["policy_or_source_labels"], 1)
        self.assertEqual(counts["remaining_by_route"], {"burden_shape_review": 1})
        self.assertTrue(report["reviewed_rows"][0]["promotion_candidate"])
        self.assertFalse(report["reviewed_rows"][1]["promotion_candidate"])

    def test_render_markdown_includes_reviewed_and_next_batch_sections(self) -> None:
        report = build_report(
            review_pack_path=_write_json(
                {
                    "review_rows": [
                        {
                            "review_bucket": "cell_a",
                            "lemma": "火曜",
                            "reading": "かよう",
                            "jmdict_glosses": ["Tuesday"],
                        }
                    ]
                }
            ),
            triage_path=_write_json(
                {
                    "triage_rows": [
                        {
                            "row_number": 1,
                            "review_route": "possible_overhard_general_vocab",
                            "review_priority": "high",
                        }
                    ]
                }
            ),
            labels_path=_write_json({"labels": []}),
            next_batch_limit=5,
        )

        markdown = render_markdown(report)
        self.assertIn("Suggested Next Batch", markdown)
        self.assertIn("火曜", markdown)


def _write_json(payload: dict[str, object]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with handle:
        json.dump(payload, handle, ensure_ascii=False)
    return Path(handle.name)


if __name__ == "__main__":
    unittest.main()
