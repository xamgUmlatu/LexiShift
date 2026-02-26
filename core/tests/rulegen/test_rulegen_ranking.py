from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.ranking import (  # noqa: E402
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
    build_ranking_sort_key,
)


class TestRulegenRanking(unittest.TestCase):
    def test_dictionary_entry_order_scores_earlier_gloss_higher(self) -> None:
        mechanism = DictionaryEntryOrderRankingMechanism()
        early = CandidateRankingContext(
            source_phrase="house",
            replacement="casa",
            metadata={"gloss_index": 0},
            confidence=0.1,
        )
        late = CandidateRankingContext(
            source_phrase="residence",
            replacement="casa",
            metadata={"gloss_index": 3},
            confidence=0.9,
        )
        self.assertGreater(mechanism.score(early), mechanism.score(late))

    def test_dictionary_entry_order_uses_fallback_when_index_missing(self) -> None:
        mechanism = DictionaryEntryOrderRankingMechanism(missing_index_score=0.12)
        context = CandidateRankingContext(
            source_phrase="unknown",
            replacement="casa",
            metadata={},
            confidence=0.4,
        )
        self.assertAlmostEqual(mechanism.score(context), 0.12, places=6)

    def test_semantic_demotion_reduces_dictionary_order_score(self) -> None:
        mechanism = DictionaryEntryOrderRankingMechanism()
        base = CandidateRankingContext(
            source_phrase="appearing",
            replacement="様",
            metadata={"gloss_index": 0},
            confidence=0.5,
        )
        demoted = CandidateRankingContext(
            source_phrase="appearing",
            replacement="様",
            metadata={"gloss_index": 0, "semantic_demotion": 0.9},
            confidence=0.5,
        )
        self.assertGreater(mechanism.score(base), mechanism.score(demoted))
        self.assertAlmostEqual(mechanism.score(demoted), 0.1, places=6)

    def test_semantic_demotion_scale_modulates_penalty(self) -> None:
        mechanism = DictionaryEntryOrderRankingMechanism()
        demoted = CandidateRankingContext(
            source_phrase="appearing",
            replacement="様",
            metadata={"gloss_index": 0, "semantic_demotion": 0.9},
            confidence=0.5,
        )
        disabled = CandidateRankingContext(
            source_phrase="appearing",
            replacement="様",
            metadata={"gloss_index": 0, "semantic_demotion": 0.9},
            confidence=0.5,
            semantic_demotion_scale=0.0,
        )
        softened = CandidateRankingContext(
            source_phrase="appearing",
            replacement="様",
            metadata={"gloss_index": 0, "semantic_demotion": 0.9},
            confidence=0.5,
            semantic_demotion_scale=0.5,
        )
        self.assertAlmostEqual(mechanism.score(disabled), 1.0, places=6)
        self.assertAlmostEqual(mechanism.score(softened), 0.55, places=6)
        self.assertAlmostEqual(mechanism.score(demoted), 0.1, places=6)

    def test_sort_key_prefers_score_then_confidence_then_source(self) -> None:
        alpha = CandidateRankingContext(
            source_phrase="alpha",
            replacement="x",
            metadata={},
            confidence=0.8,
        )
        beta = CandidateRankingContext(
            source_phrase="beta",
            replacement="x",
            metadata={},
            confidence=0.7,
        )
        alpha_key = build_ranking_sort_key(alpha, score=0.5)
        beta_key = build_ranking_sort_key(beta, score=0.5)
        self.assertLess(alpha_key, beta_key)


if __name__ == "__main__":
    unittest.main()
