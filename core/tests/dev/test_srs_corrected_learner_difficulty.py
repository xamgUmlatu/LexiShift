from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CANDIDATE_STATE_SUPPRESSED_DEFAULT,
)
from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV,
    CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV,
    clear_corrected_learner_difficulty_cache,
    estimate_learner_difficulty,
    resolve_corrected_learner_difficulty_csv_path,
)
from lexishift_core.srs.profile_bootstrap import (  # noqa: E402
    extract_profile_bootstrap_candidate_traits,
)


def _write_corrected_csv(path: Path) -> Path:
    path.write_text(
        "\n".join(
            (
                "rank,lemma,reading,score,band,candidate_state,correction_types,"
                "display_form,admission_override,topic_stretch_allowed,"
                "manual_correction_active",
                "1,alpha,,0.270000,0.25-0.30,normal_vocab,,,,True,",
                "2,beta,,0.550000,0.55-0.60,normal_vocab,restricted_admission,,"
                "restricted_admission,False,yes",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class _Seed:
    def __init__(self, lemma: str, *, language_pair: str = "en-es") -> None:
        self.lemma = lemma
        self.language_pair = language_pair
        self.base_weight = 0.99
        self.admission_weight = 0.99
        self.metadata = {}


class TestSrsCorrectedLearnerDifficulty(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV, None)
        os.environ.pop(CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV, None)
        clear_corrected_learner_difficulty_cache()

    def test_estimate_uses_en_es_corrected_csv_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = _write_corrected_csv(Path(tmp) / "corrected.csv")
            os.environ[CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV] = str(csv_path)
            clear_corrected_learner_difficulty_cache()

            estimate = estimate_learner_difficulty(
                language_pair="en-es",
                lemma="alpha",
                frequency_proxy=0.01,
            )

        self.assertAlmostEqual(estimate.value, 0.27)
        self.assertIn("en_es_corrected_ranking", estimate.proxy)
        self.assertIn("en_es_corrected_learner_difficulty_csv", estimate.sources)

    def test_en_es_corrected_ranking_is_packaged_for_runtime_default(self) -> None:
        os.environ.pop(CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV, None)
        clear_corrected_learner_difficulty_cache()

        packaged_path = resolve_corrected_learner_difficulty_csv_path(
            language_pair="en-es",
        )
        estimate = estimate_learner_difficulty(
            language_pair="en-es",
            lemma="trabajo",
            frequency_proxy=0.99,
        )

        self.assertIsNotNone(packaged_path)
        self.assertAlmostEqual(estimate.value, 0.044893)
        self.assertIn("en_es_corrected_learner_difficulty_csv", estimate.sources)

    def test_en_de_corrected_ranking_is_packaged_for_runtime_default(self) -> None:
        os.environ.pop(CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV, None)
        clear_corrected_learner_difficulty_cache()

        packaged_path = resolve_corrected_learner_difficulty_csv_path(
            language_pair="en-de",
        )
        estimate = estimate_learner_difficulty(
            language_pair="en-de",
            lemma="ander",
            frequency_proxy=0.99,
        )

        self.assertIsNotNone(packaged_path)
        self.assertAlmostEqual(estimate.value, 0.08667)
        self.assertIn("en_de_corrected_learner_difficulty_csv", estimate.sources)

    def test_profile_bootstrap_traits_use_en_es_corrected_score_and_restriction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = _write_corrected_csv(Path(tmp) / "corrected.csv")
            os.environ[CORRECTED_EN_ES_LEARNER_DIFFICULTY_CSV_ENV] = str(csv_path)
            clear_corrected_learner_difficulty_cache()

            traits = extract_profile_bootstrap_candidate_traits(_Seed("beta"))

        self.assertAlmostEqual(traits.difficulty_estimate, 0.55)
        self.assertIn("en_es_corrected_learner_difficulty_csv", traits.difficulty_sources)
        self.assertEqual(traits.candidate_state, CANDIDATE_STATE_SUPPRESSED_DEFAULT)
        self.assertEqual(traits.admission_suitability, 0.0)

    def test_profile_bootstrap_traits_use_en_de_packaged_restriction(self) -> None:
        os.environ.pop(CORRECTED_EN_DE_LEARNER_DIFFICULTY_CSV_ENV, None)
        clear_corrected_learner_difficulty_cache()

        traits = extract_profile_bootstrap_candidate_traits(_Seed("ander", language_pair="en-de"))

        self.assertIn("en_de_corrected_learner_difficulty_csv", traits.difficulty_sources)
        self.assertEqual(traits.candidate_state, CANDIDATE_STATE_SUPPRESSED_DEFAULT)
        self.assertEqual(traits.admission_suitability, 0.0)

    def test_other_pairs_still_fall_back_to_frequency_proxy(self) -> None:
        estimate = estimate_learner_difficulty(
            language_pair="en-fr",
            lemma="alpha",
            frequency_proxy=0.42,
        )

        self.assertAlmostEqual(estimate.value, 0.42)
        self.assertEqual(estimate.sources, ("frequency_proxy",))


if __name__ == "__main__":
    unittest.main()
