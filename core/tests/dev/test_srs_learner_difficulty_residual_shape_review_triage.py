from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_shape_review_triage_en_ja import (  # noqa: E402
    build_report,
    render_markdown,
)


class TestSrsLearnerDifficultyResidualShapeReviewTriage(unittest.TestCase):
    def test_source_reading_mismatch_routes_to_source_review_first(self) -> None:
        report = build_report(
            review_pack_path=_write_review_pack(
                [
                    {
                        "review_bucket": "cell_c",
                        "lemma": "鋸歯",
                        "reading": "のこば",
                        "jmdict_glosses": ["teeth of a saw"],
                        "jmdict_pos": ["noun"],
                        "jmdict_match": "lemma_only",
                        "source_signals": {"frequency": 0.99},
                    }
                ]
            )
        )

        row = report["triage_rows"][0]
        self.assertEqual(row["review_route"], "source_review_first")
        self.assertEqual(row["review_priority"], "high")

    def test_jlpt_low_frequency_difficulty_routes_to_possible_overhard_general_vocab(
        self,
    ) -> None:
        report = build_report(
            review_pack_path=_write_review_pack(
                [
                    {
                        "review_bucket": "cell_a",
                        "lemma": "一瞬",
                        "reading": "いっしゅん",
                        "jmdict_glosses": ["instant"],
                        "jmdict_pos": ["noun"],
                        "jmdict_match": "exact_reading",
                        "jlpt_vocab_level": 3.0,
                        "source_signals": {
                            "frequency": 0.65,
                            "max_written_form_burden": 0.8,
                        },
                    }
                ]
            )
        )

        row = report["triage_rows"][0]
        self.assertEqual(row["review_route"], "possible_overhard_general_vocab")
        self.assertEqual(row["review_priority"], "high")

    def test_render_markdown_includes_route_counts(self) -> None:
        report = build_report(
            review_pack_path=_write_review_pack(
                [
                    {
                        "review_bucket": "cell_a",
                        "lemma": "姿勢",
                        "reading": "しせい",
                        "jmdict_glosses": ["posture"],
                        "jmdict_pos": ["noun"],
                        "jmdict_match": "exact_reading",
                        "jlpt_vocab_level": 2.0,
                        "source_signals": {"frequency": 0.62},
                    }
                ]
            )
        )
        markdown = render_markdown(report)

        self.assertIn("possible_overhard_general_vocab", markdown)
        self.assertIn("姿勢", markdown)


def _write_review_pack(rows: list[dict[str, object]]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with handle:
        import json

        json.dump({"review_rows": rows}, handle, ensure_ascii=False)
    return Path(handle.name)


if __name__ == "__main__":
    unittest.main()
