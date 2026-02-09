from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs_admission_policy import (  # noqa: E402
    AdmissionPosWeights,
    classify_pos_bucket,
    compute_admission_weight,
)


class TestSrsAdmissionPolicy(unittest.TestCase):
    def test_classify_japanese_pos_bucket(self) -> None:
        self.assertEqual(
            classify_pos_bucket(language_pair="en-ja", raw_pos="名詞-普通名詞-一般"),
            "noun",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-ja", raw_pos="形容詞-一般"),
            "adjective",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-ja", raw_pos="動詞-一般"),
            "verb",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-ja", raw_pos="副詞-一般"),
            "adverb",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-ja", raw_pos="助詞-格助詞"),
            "other",
        )

    def test_compute_admission_weight_applies_bucket_weight(self) -> None:
        bucket, pos_weight, admission_weight = compute_admission_weight(
            language_pair="en-ja",
            raw_pos="動詞-一般",
            base_weight=0.8,
            pos_weights=AdmissionPosWeights(
                noun=1.0,
                adjective=0.9,
                verb=0.75,
                adverb=0.5,
                other=0.25,
            ),
        )
        self.assertEqual(bucket, "verb")
        self.assertAlmostEqual(pos_weight, 0.75, places=6)
        self.assertAlmostEqual(admission_weight, 0.6, places=6)

    def test_classify_german_pos_bucket(self) -> None:
        self.assertEqual(
            classify_pos_bucket(language_pair="en-de", raw_pos="SUB:NOM:SIN:NEU"),
            "noun",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-de", raw_pos="ADJ:PRD:POS"),
            "adjective",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-de", raw_pos="VER:3:SIN:PRÄ"),
            "verb",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-de", raw_pos="ADV:MOD|PRO:DEM"),
            "adverb",
        )
        self.assertEqual(
            classify_pos_bucket(language_pair="en-de", raw_pos="PRO:DEM"),
            "other",
        )

    def test_compute_admission_weight_with_german_pos(self) -> None:
        bucket, pos_weight, admission_weight = compute_admission_weight(
            language_pair="en-de",
            raw_pos="SUB:NOM:SIN:NEU",
            base_weight=0.5,
            pos_weights=AdmissionPosWeights(
                noun=0.9,
                adjective=0.8,
                verb=0.7,
                adverb=0.6,
                other=0.4,
            ),
        )
        self.assertEqual(bucket, "noun")
        self.assertAlmostEqual(pos_weight, 0.9, places=6)
        self.assertAlmostEqual(admission_weight, 0.45, places=6)


if __name__ == "__main__":
    unittest.main()
