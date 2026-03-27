from __future__ import annotations

from dataclasses import replace
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import FreedictGlossRecord  # noqa: E402
from lexishift_core.rulegen.generation import (  # noqa: E402
    RuleConfidenceSignals,
    RuleGenerationConfig,
    RuleScorer,
    materialize_rule_generation_result,
    resolve_reverse_hygiene_anchor_allowed_from_values,
    score_rule_confidence_signals,
)
from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsKaikkiPolicyConfig,
    EnEsCompiledBenchmarkEvaluationTables,
    EnEsCompiledBenchmarkSweepTables,
    EnEsCompiledSignalProvider,
    EnEsRulegenConfig,
    _build_compiled_overlay_demotion_rows,
    _build_compiled_filter_table_cache_key,
    _build_compiled_score_table_cache_key,
    _build_compiled_definition_row_group,
    build_en_es_compiled_candidate_filter_table,
    build_en_es_compiled_candidate_score_table,
    build_en_es_compiled_selected_row_table,
    build_en_es_pipeline,
    build_en_es_compiled_resources,
    generate_en_es_results,
    prepare_en_es_compiled_benchmark_evaluation_tables,
    prepare_en_es_compiled_benchmark_sweep_tables,
)
from lexishift_core.rulegen.ranking import (  # noqa: E402
    CandidateRankingContext,
    DictionaryEntryOrderRankingMechanism,
    resolve_effective_semantic_demotion_value,
    resolve_reverse_check_delta_from_values,
    resolve_reverse_check_strength_from_values,
    score_dictionary_entry_order_values,
)


class TestRulegenEnEsCompiledResources(unittest.TestCase):
    def test_compiled_resources_preserve_rulegen_outputs(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(translation="house", pos_raw="noun"),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 1, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )

        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled = generate_en_es_results(
            ["casa"],
            config=replace(base_config, compiled_resources=compiled_resources),
        )

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )
        self.assertEqual(
            compiled[0].candidate.metadata.get("reverse_check_source_norm"),
            expected[0].candidate.metadata.get("reverse_check_source_norm"),
        )

    def test_compiled_selected_row_table_matches_non_variant_results(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(translation="house", pos_raw="noun"),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 1, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )

        selected_rows = build_en_es_compiled_selected_row_table(["casa"], config=config)
        compiled_results = generate_en_es_results(["casa"], config=config)

        candidate_table = compiled_resources.candidate_table
        assert candidate_table is not None
        self.assertEqual(selected_rows.targets, ("casa",))
        self.assertEqual(
            tuple(
                candidate_table.normalized_source_phrases[row_id]
                for row_id in selected_rows.candidate_row_id_rows[0]
            ),
            tuple(result.candidate.source_phrase for result in compiled_results),
        )
        self.assertAlmostEqual(
            float(selected_rows.top1_confidences[0] or 0.0),
            float(compiled_results[0].rule.metadata.confidence or 0.0),
            places=6,
        )
        self.assertEqual(
            selected_rows.normalized_source_phrase_rows,
            (tuple(result.candidate.source_phrase for result in compiled_results),),
        )

    def test_compiled_selected_row_table_matches_variant_results(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                )
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=True,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )

        selected_rows = build_en_es_compiled_selected_row_table(["casa"], config=config)
        compiled_results = generate_en_es_results(["casa"], config=config)

        self.assertEqual(selected_rows.targets, ("casa",))
        self.assertEqual(
            selected_rows.normalized_source_phrase_rows,
            (tuple(result.candidate.source_phrase for result in compiled_results),),
        )
        self.assertEqual(
            selected_rows.variant_rule_counts,
            (sum(1 for result in compiled_results if result.candidate.metadata.get("variant")),),
        )
        self.assertEqual(
            selected_rows.top1_variant_flags,
            (bool(compiled_results[0].candidate.metadata.get("variant")),),
        )
        self.assertAlmostEqual(
            float(selected_rows.top1_confidences[0] or 0.0),
            float(compiled_results[0].rule.metadata.confidence or 0.0),
            places=6,
        )

    def test_compiled_resources_preserve_variant_rulegen_outputs(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                )
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=True,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )

        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled = generate_en_es_results(
            ["casa"],
            config=replace(base_config, compiled_resources=compiled_resources),
        )

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )
        self.assertEqual(
            [bool(result.candidate.metadata.get("variant")) for result in compiled],
            [bool(result.candidate.metadata.get("variant")) for result in expected],
        )

    def test_compiled_resources_preserve_outputs_with_live_kaikki_demotion(self) -> None:
        records = {
            "red": [
                FreedictGlossRecord(
                    translation="network",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 0,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_topics": ("mathematics",),
                    },
                ),
                FreedictGlossRecord(
                    translation="net",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        word_packages = {
            "red": {
                "version": 1,
                "language_tag": "es",
                "surface": "red",
                "reading": "red",
                "script_forms": {"default": "red"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            kaikki_policy=EnEsKaikkiPolicyConfig(enable_live_demotion=True),
        )

        expected = generate_en_es_results(["red"], config=base_config)
        compiled_resources = build_en_es_compiled_resources(
            targets=("red",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled = generate_en_es_results(
            ["red"],
            config=replace(base_config, compiled_resources=compiled_resources),
        )

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_compiled_resources_assign_stable_candidate_and_family_ids(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 0,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                    },
                )
            ],
            "red": [
                FreedictGlossRecord(
                    translation="network",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 1,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_topics": ("mathematics",),
                    },
                )
            ],
        }

        compiled_resources = build_en_es_compiled_resources(
            targets=("red", "casa"),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=None,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )

        self.assertEqual(compiled_resources.target_ids_by_target["casa"], 0)
        self.assertEqual(compiled_resources.target_ids_by_target["red"], 1)
        self.assertEqual(len(compiled_resources.candidate_facts), 2)
        self.assertIn("math_geometry", compiled_resources.family_marker_ids_by_name)
        self.assertIsNotNone(compiled_resources.candidate_table)

        red_context = compiled_resources.compiled_targets_by_target["red"]
        red_candidate = red_context.base_candidates[0]
        red_fact = red_context.candidate_facts[0]
        self.assertEqual(red_context.target_id, 1)
        self.assertEqual(red_candidate.metadata.get("compiled_target_id"), 1)
        self.assertEqual(red_candidate.metadata.get("compiled_candidate_id"), 1)
        self.assertEqual(red_fact.candidate_id, 1)
        self.assertEqual(red_fact.target_id, 1)
        self.assertEqual(red_fact.kaikkei_family_names, ("math_geometry",))
        self.assertEqual(
            red_candidate.metadata.get("compiled_family_marker_ids"),
            (compiled_resources.family_marker_ids_by_name["math_geometry"],),
        )
        assert compiled_resources.candidate_table is not None
        self.assertEqual(compiled_resources.candidate_table.candidate_ids, (0, 1))
        self.assertEqual(compiled_resources.candidate_table.target_ids, (0, 1))
        self.assertEqual(
            compiled_resources.candidate_table.candidate_row_id_by_candidate_id,
            {0: 0, 1: 1},
        )
        self.assertEqual(
            compiled_resources.candidate_table.candidate_row_ids_by_target_id,
            {0: (0,), 1: (1,)},
        )
        self.assertEqual(
            compiled_resources.candidate_table.candidate_row_ids_by_family_marker_id,
            {compiled_resources.family_marker_ids_by_name["math_geometry"]: (1,)},
        )
        self.assertEqual(compiled_resources.candidate_table.phrase_flags, (False, False))
        self.assertEqual(compiled_resources.candidate_table.variant_flags, (False, False))

    def test_compiled_resources_bypass_static_target_compilation_helpers(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 1, "sense_ord": 0, "gloss_ord": 0},
                )
            ]
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=None,
            language_pair="en-es",
            source_dict="freedict_es_en",
            dictionary_pos_source_profile="freedict",
        )

        with (
            patch(
                "lexishift_core.rulegen.pairs.en_es.resolve_target_word_package",
                side_effect=AssertionError("resolve_target_word_package should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es._collect_sanitized_gloss_records",
                side_effect=AssertionError("_collect_sanitized_gloss_records should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es.build_kaikki_record_views",
                side_effect=AssertionError("build_kaikki_record_views should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es._build_static_candidate_inventory",
                side_effect=AssertionError("_build_static_candidate_inventory should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es._build_gloss_provenance",
                side_effect=AssertionError("_build_gloss_provenance should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es.build_candidate_pos_metadata",
                side_effect=AssertionError("build_candidate_pos_metadata should not run"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es.build_optional_pos_match_provider",
                side_effect=AssertionError("build_optional_pos_match_provider should not run"),
            ),
        ):
            results = generate_en_es_results(
                ["casa"],
                config=EnEsRulegenConfig(
                    freedict_es_en_path=Path("/tmp/unused"),
                    gloss_records_by_target=records,
                    include_variants=False,
                    compiled_resources=compiled_resources,
                ),
            )

        self.assertEqual([result.candidate.source_phrase for result in results], ["house"])

    def test_compiled_candidate_score_table_matches_current_scoring_and_ranking(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )

        score_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=config,
        )
        filter_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=config,
        )

        provider = EnEsCompiledSignalProvider(
            dict_priorities={config.source_dict_id: config.dict_priority},
            gloss_decay=config.gloss_decay,
            pos_match=config.scoring.pos_match,
            variant_penalty=config.variant_penalty,
            candidate_facts_by_id={
                fact.candidate_id: fact for fact in compiled_resources.candidate_facts
            },
        )
        scorer = RuleScorer(weights=config.scoring.weights)
        ranking = DictionaryEntryOrderRankingMechanism(reverse_check=config.reverse_check)
        target_context = compiled_resources.compiled_targets_by_target["casa"]

        expected_confidences = []
        expected_ranking_scores = []
        for candidate in target_context.base_candidates:
            signals = provider.signals(candidate)
            confidence = scorer.score(
                RuleConfidenceSignals(
                    dict_priority=signals.dict_priority,
                    frequency_weight=signals.frequency_weight,
                    pos_match=signals.pos_match,
                    variant_penalty=signals.variant_penalty,
                    phrase_penalty=signals.phrase_penalty,
                    embedding_score=signals.embedding_score,
                )
            )
            expected_confidences.append(confidence)
            expected_ranking_scores.append(
                ranking.score(
                    CandidateRankingContext(
                        source_phrase=candidate.source_phrase,
                        replacement=candidate.replacement,
                        metadata=candidate.metadata,
                        confidence=confidence,
                        semantic_demotion_scale=config.semantic_demotion_scale,
                    )
                )
            )

        self.assertEqual(score_table.candidate_ids, (0, 1))
        self.assertEqual(
            score_table.confidence_scores,
            tuple(expected_confidences),
        )
        self.assertEqual(
            score_table.ranking_scores,
            tuple(expected_ranking_scores),
        )
        self.assertEqual(
            score_table.effective_semantic_demotion_values,
            tuple(
                resolve_effective_semantic_demotion_value(
                    semantic_demotion=float(candidate.metadata.get("semantic_demotion") or 0.0),
                    scale=config.semantic_demotion_scale,
                )
                for candidate in target_context.base_candidates
            ),
        )
        self.assertEqual(
            score_table.reverse_check_delta_values,
            tuple(
                resolve_reverse_check_delta_from_values(
                    supported=candidate.metadata.get("reverse_check_supported"),
                    hit=candidate.metadata.get("reverse_check_hit"),
                    rank=candidate.metadata.get("reverse_check_rank"),
                    total=candidate.metadata.get("reverse_check_total"),
                    config=config.reverse_check,
                )
                for candidate in target_context.base_candidates
            ),
        )
        self.assertEqual(
            score_table.reverse_check_strength_values,
            tuple(
                resolve_reverse_check_strength_from_values(
                    supported=candidate.metadata.get("reverse_check_supported"),
                    hit=candidate.metadata.get("reverse_check_hit"),
                    rank=candidate.metadata.get("reverse_check_rank"),
                    total=candidate.metadata.get("reverse_check_total"),
                    config=config.reverse_check,
                )
                for candidate in target_context.base_candidates
            ),
        )
        self.assertEqual(
            score_table.reverse_hygiene_anchor_allowed_flags,
            tuple(
                resolve_reverse_hygiene_anchor_allowed_from_values(
                    hit=candidate.metadata.get("reverse_check_hit"),
                    rank=candidate.metadata.get("reverse_check_rank"),
                    total=candidate.metadata.get("reverse_check_total"),
                )
                for candidate in target_context.base_candidates
            ),
        )
        self.assertEqual(
            score_table.row_sort_keys,
            tuple(
                (
                    -float(expected_ranking_scores[row_id]),
                    -float(expected_confidences[row_id]),
                    str(filter_table.normalized_source_phrases[row_id] or "").lower(),
                )
                for row_id in range(len(score_table.candidate_ids))
            ),
        )
        target_id = compiled_resources.target_ids_by_target["casa"]
        self.assertEqual(
            score_table.ranked_candidate_row_ids_by_target_id,
            {
                target_id: tuple(
                    sorted(
                        range(len(score_table.candidate_ids)),
                        key=lambda row_id: score_table.row_sort_keys[row_id],
                    )
                )
            },
        )

    def test_compiled_candidate_score_table_uses_direct_scalar_helpers(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 1, "gloss_ord": 0},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )

        with (
            patch(
                "lexishift_core.rulegen.pairs.en_es.score_rule_confidence_signals",
                wraps=score_rule_confidence_signals,
            ) as score_helper,
            patch(
                "lexishift_core.rulegen.pairs.en_es.score_dictionary_entry_order_values",
                wraps=score_dictionary_entry_order_values,
            ) as ranking_helper,
            patch(
                "lexishift_core.rulegen.pairs.en_es.resolve_reverse_check_strength_from_values",
                wraps=resolve_reverse_check_strength_from_values,
            ) as reverse_strength_helper,
            patch(
                "lexishift_core.rulegen.pairs.en_es.resolve_reverse_hygiene_anchor_allowed_from_values",
                wraps=resolve_reverse_hygiene_anchor_allowed_from_values,
            ) as reverse_anchor_helper,
            patch(
                "lexishift_core.rulegen.pairs.en_es.RuleScorer.score",
                side_effect=AssertionError("compiled score table should use direct score helper"),
            ),
            patch(
                "lexishift_core.rulegen.pairs.en_es.DictionaryEntryOrderRankingMechanism.score",
                side_effect=AssertionError("compiled score table should use direct ranking helper"),
            ),
        ):
            score_table = build_en_es_compiled_candidate_score_table(
                compiled_resources=compiled_resources,
                config=config,
            )

        self.assertEqual(score_helper.call_count, len(score_table.candidate_ids))
        self.assertEqual(ranking_helper.call_count, len(score_table.candidate_ids))
        self.assertEqual(reverse_strength_helper.call_count, len(score_table.candidate_ids))
        self.assertEqual(reverse_anchor_helper.call_count, len(score_table.candidate_ids))

    def test_compiled_candidate_filter_table_matches_live_normalization_and_filters(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation=" To Run! ",
                    pos_raw="verb",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
                FreedictGlossRecord(
                    translation="houses",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 2},
                ),
                FreedictGlossRecord(
                    translation="the",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 3},
                ),
                FreedictGlossRecord(
                    translation="friend's",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 4},
                ),
                FreedictGlossRecord(
                    translation="in order to",
                    pos_raw="preposition",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 5},
                ),
                FreedictGlossRecord(
                    translation="oh",
                    pos_raw="interjection",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 6},
                ),
                FreedictGlossRecord(
                    translation="a",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 7},
                ),
            ]
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        filter_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=base_config,
        )
        candidate_table = compiled_resources.candidate_table
        self.assertIsNotNone(candidate_table)
        live_pipeline = build_en_es_pipeline(base_config)
        normalized_by_row_id: dict[int, str] = {}
        accepted_by_row_id: dict[int, bool] = {}
        for candidate in live_pipeline._iter_candidates(["casa"], base_config.language_pair):
            row_id = int(candidate.metadata.get("compiled_candidate_index"))
            normalized_by_row_id[row_id] = candidate.source_phrase
            accepted_by_row_id[row_id] = live_pipeline._accept(candidate)

        self.assertEqual(
            filter_table.normalized_source_phrases,
            tuple(
                normalized_by_row_id[row_id] for row_id in range(len(filter_table.candidate_ids))
            ),
        )
        self.assertEqual(
            candidate_table.normalized_source_phrases,
            filter_table.normalized_source_phrases,
        )
        expected_definition_group_ids: list[int] = []
        expected_definition_group_ids_by_key: dict[tuple[str, object], int] = {}
        for row_id in range(len(filter_table.candidate_ids)):
            definition_bucket_id = int(candidate_table.definition_bucket_ids[row_id])
            definition_group_key: tuple[str, object]
            if definition_bucket_id >= 0:
                definition_group_key = ("definition_bucket_id", definition_bucket_id)
            else:
                definition_group_key = (
                    "source_phrase",
                    str(filter_table.normalized_source_phrases[row_id] or "").strip().lower(),
                )
            expected_definition_group_ids.append(
                expected_definition_group_ids_by_key.setdefault(
                    definition_group_key,
                    len(expected_definition_group_ids_by_key),
                )
            )
        self.assertEqual(
            filter_table.definition_group_ids,
            tuple(expected_definition_group_ids),
        )
        self.assertEqual(
            filter_table.accepted_flags,
            tuple(
                bool(accepted_by_row_id.get(row_id, False))
                for row_id in range(len(filter_table.candidate_ids))
            ),
        )
        self.assertEqual(filter_table.normalized_source_phrases[0], "house")
        self.assertEqual(filter_table.normalized_source_phrases[1], "run")
        self.assertFalse(filter_table.inflection_artifact_flags[2])
        self.assertFalse(filter_table.stopword_flags[3])
        self.assertFalse(filter_table.possessive_flags[4])
        self.assertTrue(filter_table.gloss_shape_flags[5])
        self.assertFalse(filter_table.shadowed_interjection_flags[6])
        self.assertFalse(filter_table.length_flags[7])
        self.assertEqual(
            filter_table.accepted_flags, (True, True, False, False, False, True, False, False)
        )
        self.assertEqual(
            filter_table.accepted_candidate_row_ids_by_target_id,
            {compiled_resources.target_ids_by_target["casa"]: (0, 1, 5)},
        )
        self.assertEqual(
            filter_table.accepted_candidate_row_id_groups_by_target_id,
            {compiled_resources.target_ids_by_target["casa"]: ((0,), (1,), (5,))},
        )

    def test_compiled_definition_row_group_sorts_once_and_carries_best_row_summary(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        filter_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=config,
        )
        score_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=config,
        )

        group = _build_compiled_definition_row_group(
            (1, 0),
            score_table=score_table,
        )

        self.assertEqual(group.row_ids, (1, 0))
        self.assertEqual(group.sorted_row_ids, (0, 1))
        self.assertEqual(group.best_row_id, 0)
        self.assertEqual(filter_table.definition_group_ids[0], filter_table.definition_group_ids[1])
        self.assertEqual(
            group.sort_key,
            (
                -float(score_table.ranking_scores[0]),
                -float(score_table.confidence_scores[0]),
                "house",
            ),
        )
        self.assertEqual(group.reverse_strength, 1.0)
        self.assertTrue(group.allows_reverse_hygiene_anchor)
        projected_group = _build_compiled_definition_row_group(
            (1, 0),
            sorted_row_ids=score_table.ranked_candidate_row_ids_by_target_id[
                compiled_resources.target_ids_by_target["casa"]
            ],
            score_table=score_table,
        )
        self.assertEqual(projected_group.sorted_row_ids, (0, 1))
        self.assertEqual(projected_group.best_row_id, 0)

    def test_compiled_filter_table_cache_reuses_unrelated_config_variants(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="the",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )

        base_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=base_config,
        )
        unrelated_config = replace(
            base_config,
            dict_priority=0.1,
            confidence_threshold=0.5,
        )
        unrelated_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=unrelated_config,
        )
        filter_changed_config = replace(
            base_config,
            enable_stopword_filter=False,
        )
        filter_changed_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_resources,
            config=filter_changed_config,
        )

        self.assertIs(base_table, unrelated_table)
        self.assertIsNot(base_table, filter_changed_table)

    def test_compiled_cache_keys_use_stable_resource_tokens(self) -> None:
        records = {
            "casa": [FreedictGlossRecord(translation="house", pos_raw="noun")],
        }
        compiled_a = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target={},
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        compiled_b = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target={},
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )

        self.assertNotEqual(
            _build_compiled_filter_table_cache_key(
                compiled_resources=compiled_a,
                config=config,
            ),
            _build_compiled_filter_table_cache_key(
                compiled_resources=compiled_b,
                config=config,
            ),
        )
        self.assertNotEqual(
            _build_compiled_score_table_cache_key(
                compiled_resources=compiled_a,
                config=config,
            ),
            _build_compiled_score_table_cache_key(
                compiled_resources=compiled_b,
                config=config,
            ),
        )

    def test_compiled_score_table_cache_reuses_variant_dimension_only(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )

        base_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=base_config,
        )
        variant_only_config = replace(
            base_config,
            include_variants=True,
            confidence_threshold=0.5,
        )
        variant_only_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=variant_only_config,
        )
        reverse_changed_config = replace(
            base_config,
            reverse_check=replace(base_config.reverse_check, enabled=True, match_bonus=0.3),
        )
        reverse_changed_table = build_en_es_compiled_candidate_score_table(
            compiled_resources=compiled_resources,
            config=reverse_changed_config,
        )

        self.assertIs(base_table, variant_only_table)
        self.assertIsNot(base_table, reverse_changed_table)

    def test_compiled_overlay_demotion_rows_cache_reuses_policy_only_inputs(self) -> None:
        records = {
            "marca": [
                FreedictGlossRecord(
                    translation="abbr",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 0,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_form_of": ("abbreviation",),
                    },
                ),
                FreedictGlossRecord(
                    translation="term",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        word_packages = {
            "marca": {
                "version": 1,
                "language_tag": "es",
                "surface": "marca",
                "reading": "marca",
                "script_forms": {"default": "marca"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("marca",),
            records_by_target=records,
            reverse_records_by_source=None,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
            kaikki_policy=EnEsKaikkiPolicyConfig(enable_live_demotion=True),
        )
        score_only_changed_config = replace(
            base_config,
            dict_priority=0.2,
            scoring=replace(
                base_config.scoring,
                weights=replace(base_config.scoring.weights, dict_priority=0.3),
            ),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es._build_compiled_overlay_demotion_rows",
            wraps=_build_compiled_overlay_demotion_rows,
        ) as build_overlay:
            build_en_es_compiled_candidate_score_table(
                compiled_resources=compiled_resources,
                config=base_config,
            )
            build_en_es_compiled_candidate_score_table(
                compiled_resources=compiled_resources,
                config=score_only_changed_config,
            )

        self.assertEqual(build_overlay.call_count, 1)

    def test_prepare_compiled_benchmark_evaluation_tables_preserves_selected_rows(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )
        variant_config = replace(base_config, include_variants=True)
        reverse_changed_config = replace(
            base_config,
            reverse_check=replace(base_config.reverse_check, enabled=True, match_bonus=0.3),
        )

        prepared_tables = prepare_en_es_compiled_benchmark_evaluation_tables(
            configs=(base_config, variant_config, reverse_changed_config)
        )

        self.assertEqual(len(prepared_tables), 3)
        self.assertTrue(
            all(
                isinstance(prepared_table, EnEsCompiledBenchmarkEvaluationTables)
                for prepared_table in prepared_tables
            )
        )
        self.assertEqual(
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=base_config,
                filter_table=prepared_tables[0].filter_table,
                score_table=prepared_tables[0].score_table,
            ),
            build_en_es_compiled_selected_row_table(["casa"], config=base_config),
        )
        self.assertEqual(
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=variant_config,
                filter_table=prepared_tables[1].filter_table,
                score_table=prepared_tables[1].score_table,
            ),
            build_en_es_compiled_selected_row_table(["casa"], config=variant_config),
        )
        self.assertEqual(
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=reverse_changed_config,
                filter_table=prepared_tables[2].filter_table,
                score_table=prepared_tables[2].score_table,
            ),
            build_en_es_compiled_selected_row_table(["casa"], config=reverse_changed_config),
        )

    def test_prepare_compiled_benchmark_sweep_tables_preserves_selected_rows(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=compiled_resources,
        )
        variant_config = replace(base_config, include_variants=True)
        reverse_changed_config = replace(
            base_config,
            reverse_check=replace(base_config.reverse_check, enabled=True, match_bonus=0.3),
        )

        prepared_tables = prepare_en_es_compiled_benchmark_sweep_tables(
            targets=("casa",),
            configs=(base_config, variant_config, reverse_changed_config),
        )

        self.assertEqual(len(prepared_tables), 3)
        self.assertTrue(
            all(
                isinstance(prepared_table, EnEsCompiledBenchmarkSweepTables)
                for prepared_table in prepared_tables
            )
        )
        self.assertEqual(
            prepared_tables[0].selected_row_table,
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=base_config,
                filter_table=prepared_tables[0].filter_table,
                score_table=prepared_tables[0].score_table,
                include_normalized_source_phrase_rows=False,
            ),
        )
        self.assertEqual(
            prepared_tables[1].selected_row_table,
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=variant_config,
                filter_table=prepared_tables[1].filter_table,
                score_table=prepared_tables[1].score_table,
                include_normalized_source_phrase_rows=False,
            ),
        )
        self.assertEqual(
            prepared_tables[2].selected_row_table,
            build_en_es_compiled_selected_row_table(
                ["casa"],
                config=reverse_changed_config,
                filter_table=prepared_tables[2].filter_table,
                score_table=prepared_tables[2].score_table,
                include_normalized_source_phrase_rows=False,
            ),
        )
        self.assertEqual(prepared_tables[0].selected_row_table.normalized_source_phrase_rows, ((),))

    def test_compiled_pipeline_uses_precomputed_candidate_filter_rows_for_non_variant_configs(
        self,
    ) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation=" To Run! ",
                    pos_raw="verb",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
                FreedictGlossRecord(
                    translation="houses",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 2},
                ),
                FreedictGlossRecord(
                    translation="the",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 3},
                ),
                FreedictGlossRecord(
                    translation="friend's",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 4},
                ),
                FreedictGlossRecord(
                    translation="in order to",
                    pos_raw="preposition",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 5},
                ),
                FreedictGlossRecord(
                    translation="oh",
                    pos_raw="interjection",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 6},
                ),
            ]
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=None,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es._build_filters",
            side_effect=AssertionError("compiled non-variant path should not build live filters"),
        ):
            pipeline = build_en_es_pipeline(compiled_config)

        self.assertEqual(pipeline._normalizers, [])
        self.assertEqual(pipeline._filters, [])
        iterated_candidates = list(
            pipeline._iter_candidates(["casa"], compiled_config.language_pair)
        )
        self.assertEqual(
            [candidate.source_phrase for candidate in iterated_candidates],
            ["house", "run", "in order to"],
        )

        compiled = generate_en_es_results(["casa"], config=compiled_config)
        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_compiled_pipeline_dedupe_groups_preserve_threshold_fallback_to_later_duplicate(
        self,
    ) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="to house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            confidence_threshold=0.85,
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=reverse_records,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )
        filter_table = build_en_es_compiled_candidate_filter_table(
            compiled_resources=compiled_config.compiled_resources,
            config=compiled_config,
        )
        target_id = compiled_config.compiled_resources.target_ids_by_target["casa"]
        self.assertEqual(
            filter_table.accepted_candidate_row_id_groups_by_target_id[target_id],
            ((0, 1),),
        )

        compiled = generate_en_es_results(["casa"], config=compiled_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_compiled_pipeline_resolves_base_candidates_from_row_local_index(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_resources = build_en_es_compiled_resources(
            targets=("casa",),
            records_by_target=records,
            reverse_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            dictionary_pos_source_profile="wiktionary",
        )
        stripped_targets = {
            target: replace(
                context,
                base_candidates=tuple(
                    replace(
                        candidate,
                        metadata={
                            key: value
                            for key, value in candidate.metadata.items()
                            if key != "compiled_candidate_id"
                        },
                    )
                    for candidate in context.base_candidates
                ),
            )
            for target, context in compiled_resources.compiled_targets_by_target.items()
        }
        compiled_config = replace(
            base_config,
            compiled_resources=replace(
                compiled_resources,
                compiled_targets_by_target=stripped_targets,
            ),
        )

        compiled = generate_en_es_results(["casa"], config=compiled_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_non_variant_compiled_result_fast_path_bypasses_pipeline(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation=" To Run! ",
                    pos_raw="verb",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
                FreedictGlossRecord(
                    translation="in order to",
                    pos_raw="preposition",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 5},
                ),
            ]
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=None,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es.build_en_es_pipeline",
            side_effect=AssertionError("non-variant compiled generation should bypass pipeline"),
        ):
            compiled = generate_en_es_results(["casa"], config=compiled_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in compiled],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_non_variant_compiled_fast_path_limits_rows_before_materialization(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 1, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="roof",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 2, "gloss_ord": 0},
                ),
            ]
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            max_definitions_per_target=1,
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        compiled_config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=None,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es.materialize_rule_generation_result",
            wraps=materialize_rule_generation_result,
        ) as materialize:
            compiled = generate_en_es_results(["casa"], config=compiled_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in compiled],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(materialize.call_count, len(compiled))
        self.assertLess(materialize.call_count, 3)

    def test_compiled_pipeline_uses_precomputed_ranking_scores(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=True,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=reverse_records,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )
        pipeline = build_en_es_pipeline(config)
        rule_config = RuleGenerationConfig(
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            interleave_definition_groups=config.interleave_definition_groups,
            semantic_demotion_scale=config.semantic_demotion_scale,
            tags=("translation", config.source_dict_id),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es.DictionaryEntryOrderRankingMechanism.score",
            side_effect=AssertionError("compiled runtime should not call fallback ranking score"),
        ):
            results = pipeline.generate_results(["casa"], config=rule_config)

        self.assertEqual([result.candidate.source_phrase for result in results], ["house", "home"])

    def test_compiled_pipeline_uses_precomputed_ranking_scores_with_live_overlay(self) -> None:
        records = {
            "marca": [
                FreedictGlossRecord(
                    translation="abbr",
                    pos_raw="noun",
                    metadata={
                        "entry_ord": 0,
                        "sense_ord": 0,
                        "gloss_ord": 0,
                        "sense_form_of": ("abbreviation",),
                    },
                ),
                FreedictGlossRecord(
                    translation="term",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 1},
                ),
            ]
        }
        word_packages = {
            "marca": {
                "version": 1,
                "language_tag": "es",
                "surface": "marca",
                "reading": "marca",
                "script_forms": {"default": "marca"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
            kaikki_policy=EnEsKaikkiPolicyConfig(enable_live_demotion=True),
        )
        expected = generate_en_es_results(["marca"], config=base_config)
        config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("marca",),
                records_by_target=records,
                reverse_records_by_source=None,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )
        pipeline = build_en_es_pipeline(config)
        rule_config = RuleGenerationConfig(
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            interleave_definition_groups=config.interleave_definition_groups,
            semantic_demotion_scale=config.semantic_demotion_scale,
            tags=("translation", config.source_dict_id),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es.DictionaryEntryOrderRankingMechanism.score",
            side_effect=AssertionError("compiled runtime should not call fallback ranking score"),
        ):
            results = pipeline.generate_results(["marca"], config=rule_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            [result.candidate.source_phrase for result in expected],
        )
        self.assertEqual(
            [result.rule.metadata.confidence for result in results],
            [result.rule.metadata.confidence for result in expected],
        )

    def test_compiled_pipeline_preserves_reverse_hygiene_with_ranking_wrapper(self) -> None:
        records = {
            "casa": [
                FreedictGlossRecord(
                    translation="house",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 0, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="home",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 1, "gloss_ord": 0},
                ),
                FreedictGlossRecord(
                    translation="roof",
                    pos_raw="noun",
                    metadata={"entry_ord": 0, "sense_ord": 2, "gloss_ord": 0},
                ),
            ]
        }
        reverse_records = {
            "house": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "home": [FreedictGlossRecord(translation="casa", pos_raw="noun")],
            "roof": [FreedictGlossRecord(translation="techo", pos_raw="noun")],
        }
        word_packages = {
            "casa": {
                "version": 1,
                "language_tag": "es",
                "surface": "casa",
                "reading": "casa",
                "script_forms": {"default": "casa"},
                "source": {"provider": "freq-es-cde"},
                "pos": {"canonical": "noun"},
            }
        }
        base_config = EnEsRulegenConfig(
            freedict_es_en_path=Path("/tmp/unused"),
            gloss_records_by_target=records,
            reverse_gloss_records_by_source=reverse_records,
            word_packages_by_target=word_packages,
            include_variants=False,
            source_dict_id="wiktionary_es_en",
            reverse_source_dict_id="wiktionary_en_es",
            dictionary_pos_source_profile="wiktionary",
        )
        expected = generate_en_es_results(["casa"], config=base_config)
        config = replace(
            base_config,
            compiled_resources=build_en_es_compiled_resources(
                targets=("casa",),
                records_by_target=records,
                reverse_records_by_source=reverse_records,
                word_packages_by_target=word_packages,
                language_pair="en-es",
                source_dict="wiktionary_es_en",
                dictionary_pos_source_profile="wiktionary",
            ),
        )
        pipeline = build_en_es_pipeline(config)
        rule_config = RuleGenerationConfig(
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            interleave_definition_groups=config.interleave_definition_groups,
            semantic_demotion_scale=config.semantic_demotion_scale,
            tags=("translation", config.source_dict_id),
        )

        with patch(
            "lexishift_core.rulegen.pairs.en_es.DictionaryEntryOrderRankingMechanism.score",
            side_effect=AssertionError("compiled runtime should not call fallback ranking score"),
        ):
            results = pipeline.generate_results(["casa"], config=rule_config)

        self.assertEqual(
            [result.candidate.source_phrase for result in results],
            [result.candidate.source_phrase for result in expected],
        )


if __name__ == "__main__":
    unittest.main()
