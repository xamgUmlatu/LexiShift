from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.generation import (  # noqa: E402
    CandidateSource,
    RuleCandidate,
    RuleGenerationConfig,
    RuleGenerationPipeline,
)
from lexishift_core.rulegen.ranking import (  # noqa: E402
    DictionaryEntryOrderRankingMechanism,
    ReverseCheckScoringConfig,
)


class _StaticSource(CandidateSource):
    def __init__(self, candidates: list[RuleCandidate]) -> None:
        self._candidates = list(candidates)

    def generate(self, targets, *, language_pair: str):
        target_set = {str(target) for target in targets}
        for candidate in self._candidates:
            if candidate.language_pair != language_pair:
                continue
            if candidate.replacement not in target_set:
                continue
            yield candidate


class TestRulegenGeneration(unittest.TestCase):
    def test_interleave_definition_groups_round_robins_selected_buckets(self) -> None:
        pipeline = RuleGenerationPipeline(
            sources=[
                _StaticSource(
                    [
                        RuleCandidate(
                            source_phrase="square",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={"gloss_index": 0, "definition_bucket_key": "sense:0"},
                        ),
                        RuleCandidate(
                            source_phrase="rectangle",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={"gloss_index": 1, "definition_bucket_key": "sense:0"},
                        ),
                        RuleCandidate(
                            source_phrase="frame",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={"gloss_index": 3, "definition_bucket_key": "sense:1"},
                        ),
                        RuleCandidate(
                            source_phrase="table",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={"gloss_index": 4, "definition_bucket_key": "sense:2"},
                        ),
                    ]
                )
            ]
        )
        results = pipeline.generate_results(
            ["cuadro"],
            config=RuleGenerationConfig(
                language_pair="en-es",
                max_definitions_per_target=3,
                interleave_definition_groups=True,
            ),
        )
        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["square", "frame", "table", "rectangle"],
        )

    def test_reverse_hygiene_suppresses_weak_groups_after_strong_hit(self) -> None:
        pipeline = RuleGenerationPipeline(
            sources=[
                _StaticSource(
                    [
                        RuleCandidate(
                            source_phrase="bed",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 0,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 13,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="watercourse",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 1,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 2,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="mother",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 2,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 0,
                                "reverse_check_total": 1,
                            },
                        ),
                    ]
                )
            ],
            ranking_mechanism=DictionaryEntryOrderRankingMechanism(
                reverse_check=ReverseCheckScoringConfig(
                    enabled=True,
                    match_bonus=0.6,
                    near_bonus=0.1,
                    near_rank_max=2,
                    far_hit_penalty=0.05,
                    miss_penalty=0.8,
                )
            ),
        )
        results = pipeline.generate_results(
            ["madre"],
            config=RuleGenerationConfig(
                language_pair="en-es",
                max_definitions_per_target=3,
            ),
        )
        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["mother"],
        )

    def test_reverse_hygiene_keeps_supported_alternatives(self) -> None:
        pipeline = RuleGenerationPipeline(
            sources=[
                _StaticSource(
                    [
                        RuleCandidate(
                            source_phrase="bank",
                            replacement="banco",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 0,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 3,
                                "reverse_check_total": 24,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="bench",
                            replacement="banco",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 1,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 0,
                                "reverse_check_total": 8,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="seat",
                            replacement="banco",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 2,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 1,
                            },
                        ),
                    ]
                )
            ],
            ranking_mechanism=DictionaryEntryOrderRankingMechanism(
                reverse_check=ReverseCheckScoringConfig(
                    enabled=True,
                    match_bonus=0.6,
                    near_bonus=0.1,
                    near_rank_max=2,
                    far_hit_penalty=0.05,
                    miss_penalty=0.8,
                )
            ),
        )
        results = pipeline.generate_results(
            ["banco"],
            config=RuleGenerationConfig(
                language_pair="en-es",
                max_definitions_per_target=3,
            ),
        )
        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["bench", "bank"],
        )

    def test_reverse_hygiene_keeps_alternatives_when_exact_hit_is_highly_ambiguous(self) -> None:
        pipeline = RuleGenerationPipeline(
            sources=[
                _StaticSource(
                    [
                        RuleCandidate(
                            source_phrase="square",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={
                                "gloss_index": 0,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 0,
                                "reverse_check_total": 22,
                                "definition_bucket_key": "sense:0",
                            },
                        ),
                        RuleCandidate(
                            source_phrase="frame",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={
                                "gloss_index": 1,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 18,
                                "reverse_check_total": 20,
                                "definition_bucket_key": "sense:1",
                            },
                        ),
                        RuleCandidate(
                            source_phrase="table",
                            replacement="cuadro",
                            language_pair="en-es",
                            source_dict="wiktionary_es_en",
                            metadata={
                                "gloss_index": 2,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 9,
                                "definition_bucket_key": "sense:2",
                            },
                        ),
                    ]
                )
            ],
            ranking_mechanism=DictionaryEntryOrderRankingMechanism(
                reverse_check=ReverseCheckScoringConfig(
                    enabled=True,
                    match_bonus=0.2,
                    near_bonus=0.1,
                    near_rank_max=2,
                    far_hit_penalty=0.0,
                    miss_penalty=0.2,
                )
            ),
        )
        results = pipeline.generate_results(
            ["cuadro"],
            config=RuleGenerationConfig(
                language_pair="en-es",
                max_definitions_per_target=3,
            ),
        )
        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["square", "frame", "table"],
        )

    def test_reverse_hygiene_requires_enabled_reverse_check(self) -> None:
        pipeline = RuleGenerationPipeline(
            sources=[
                _StaticSource(
                    [
                        RuleCandidate(
                            source_phrase="bed",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 0,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 13,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="watercourse",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 1,
                                "reverse_check_supported": True,
                                "reverse_check_hit": False,
                                "reverse_check_total": 2,
                            },
                        ),
                        RuleCandidate(
                            source_phrase="mother",
                            replacement="madre",
                            language_pair="en-es",
                            source_dict="freedict_es_en",
                            metadata={
                                "gloss_index": 2,
                                "reverse_check_supported": True,
                                "reverse_check_hit": True,
                                "reverse_check_rank": 0,
                                "reverse_check_total": 1,
                            },
                        ),
                    ]
                )
            ],
            ranking_mechanism=DictionaryEntryOrderRankingMechanism(
                reverse_check=ReverseCheckScoringConfig(enabled=False)
            ),
        )
        results = pipeline.generate_results(
            ["madre"],
            config=RuleGenerationConfig(
                language_pair="en-es",
                max_definitions_per_target=3,
            ),
        )
        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            ["bed", "watercourse", "mother"],
        )


if __name__ == "__main__":
    unittest.main()
