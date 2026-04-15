from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.selector import (  # noqa: E402
    SELECTION_POLICY_TOP_N,
    SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
    SelectorCandidate,
    SelectorConfig,
    select_candidates,
)


class TestSelectorSelectionPolicy(unittest.TestCase):
    def test_top_n_selection_returns_ranked_prefix(self) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-en", base_freq=0.9),
            SelectorCandidate(lemma="beta", language_pair="en-en", base_freq=0.6),
            SelectorCandidate(lemma="gamma", language_pair="en-en", base_freq=0.2),
        ]

        selected = select_candidates(
            candidates,
            config=SelectorConfig(
                selection_policy=SELECTION_POLICY_TOP_N,
                top_n=2,
            ),
            selection_count=2,
        )

        self.assertEqual([entry.candidate.lemma for entry in selected], ["alpha", "beta"])

    def test_weighted_selection_is_seed_reproducible(self) -> None:
        candidates = [
            SelectorCandidate(lemma="alpha", language_pair="en-en", base_freq=0.9),
            SelectorCandidate(lemma="beta", language_pair="en-en", base_freq=0.6),
            SelectorCandidate(lemma="gamma", language_pair="en-en", base_freq=0.2),
        ]
        config = SelectorConfig(
            selection_policy=SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
            top_n=2,
        )

        selected = select_candidates(
            candidates,
            config=config,
            selection_count=2,
            seed=1,
        )

        self.assertEqual([entry.candidate.lemma for entry in selected], ["alpha", "gamma"])


if __name__ == "__main__":
    unittest.main()
