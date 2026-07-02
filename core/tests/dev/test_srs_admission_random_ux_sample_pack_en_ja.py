from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_admission_random_ux_sample_pack_en_ja import (  # noqa: E402
    annotate_words_for_review,
    summarize_words,
)


class TestSrsAdmissionRandomUxSamplePackEnJa(unittest.TestCase):
    def test_annotates_difficulty_delta_and_topic_leniency_summary(self) -> None:
        words = annotate_words_for_review(
            [
                {
                    "lemma": "社会",
                    "corrected_difficulty": 0.35,
                    "topic_affinity_source": "topic_hint:law_politics_civics",
                },
                {
                    "lemma": "する",
                    "corrected_difficulty": 0.02,
                },
                {
                    "lemma": "政府",
                    "runtime_difficulty_estimate": 0.42,
                    "topic_affinity_source": "topic_hint:law_politics_civics",
                },
            ],
            proficiency=0.30,
        )
        summary = summarize_words(words, proficiency=0.30)

        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["topic_mover_counts"], {"law_politics_civics": 2})
        self.assertEqual(summary["topic_movers"]["count"], 2)
        self.assertEqual(summary["topic_movers"]["above_proficiency_count"], 2)
        self.assertEqual(summary["topic_movers"]["above_proficiency_plus_0_10_count"], 1)
        self.assertEqual(summary["non_topic"]["above_proficiency_count"], 0)
        self.assertAlmostEqual(words[0]["difficulty_minus_proficiency"], 0.05)
        self.assertTrue(words[2]["above_proficiency_plus_0_10"])


if __name__ == "__main__":
    unittest.main()
