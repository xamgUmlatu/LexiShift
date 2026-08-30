from __future__ import annotations

from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_shape_review_pack_en_ja import (  # noqa: E402
    _blocked_labels,
    _is_english_gloss,
    _is_blocked_label,
    render_blind_review_markdown,
)


class TestSrsLearnerDifficultyResidualShapeReviewPack(unittest.TestCase):
    def test_blocked_labels_handles_exact_reading_and_lemma_wide_blocks(self) -> None:
        blocked = _blocked_labels(
            {
                "labels": [
                    {"lemma": "的", "expected_reading": "まと"},
                    {"lemma": "御"},
                ]
            }
        )

        self.assertTrue(_is_blocked_label("的", "まと", blocked))
        self.assertFalse(_is_blocked_label("的", "てき", blocked))
        self.assertTrue(_is_blocked_label("御", "おん", blocked))

    def test_english_gloss_accepts_jmdict_xml_lang_eng(self) -> None:
        english = ElementTree.Element(
            "gloss",
            {"{http://www.w3.org/XML/1998/namespace}lang": "eng"},
        )
        french = ElementTree.Element(
            "gloss",
            {"{http://www.w3.org/XML/1998/namespace}lang": "fre"},
        )

        self.assertTrue(_is_english_gloss(english))
        self.assertFalse(_is_english_gloss(french))

    def test_blind_review_markdown_omits_model_and_residual_fields(self) -> None:
        markdown = render_blind_review_markdown(
            {
                "review_rows": [
                    {
                        "review_bucket": "cell_a",
                        "lemma": "影響",
                        "reading": "えいきょう",
                        "jmdict_glosses": ["influence"],
                        "jmdict_pos": ["noun"],
                        "jmdict_match": "exact_reading",
                        "candidate_state": "normal_vocab",
                        "problem_class": "normal_vocab",
                        "source_signals": {"max_written_form_burden": 0.9},
                    }
                ]
            }
        )

        self.assertIn("影響", markdown)
        self.assertIn("influence", markdown)
        self.assertIn("exact_reading", markdown)
        for forbidden in (
            "old_score",
            "residual",
            "calibration_delta",
            "holdout_delta",
            "suggested_direction",
        ):
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
