from __future__ import annotations

import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV,
    clear_corrected_learner_difficulty_cache,
    lookup_corrected_en_ja_learner_difficulty,
    resolve_corrected_en_ja_learner_difficulty_csv_path,
    resolve_packaged_en_ja_learner_difficulty_manual_corrections_path,
)
from lexishift_core.srs.profile_bootstrap import (  # noqa: E402
    FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
    FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY,
    FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY,
    PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_POLICY_VERSION,
    PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_POLICY_VERSION,
    PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_POLICY_VERSION,
    attach_precomputed_profile_bootstrap_candidate_traits,
    build_profile_bootstrap_signal_pack,
    clear_profile_bootstrap_candidate_trait_cache,
    extract_profile_bootstrap_candidate_traits,
    normalize_profile_bootstrap_context,
    rerank_seed_words_for_profile,
    score_seed_words_for_frontier_gaussian_hybrid_profile,
    score_seed_words_for_frontier_gaussian_profile,
    score_seed_words_for_profile,
    summarize_profile_bootstrap_context,
)
from lexishift_core.srs.profile_bootstrap_support import (  # noqa: E402
    compute_frontier_gaussian_fit,
)
from lexishift_core.srs.admission_features import (  # noqa: E402
    ADMISSION_CANDIDATE_FEATURES_METADATA_KEY,
    ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY,
)


def _seed_with_difficulty(
    lemma: str,
    difficulty: float,
    *,
    topics: list[str] | None = None,
    admission_suitability: float = 1.0,
) -> SimpleNamespace:
    commonness = max(0.0, min(1.0, 1.0 - float(difficulty)))
    metadata: dict[str, object] = {}
    if topics:
        metadata["topics"] = list(topics)
    return SimpleNamespace(
        lemma=lemma,
        language_pair="en-es",
        base_weight=commonness,
        admission_weight=commonness,
        admission_suitability=admission_suitability,
        metadata=metadata,
    )


class TestProfileBootstrapContextNormalization(unittest.TestCase):
    def test_normalizes_explicit_profile_contract(self) -> None:
        normalized = normalize_profile_bootstrap_context(
            {
                "interests": ["animals"],
                "topic_weights": {"science": 0.4},
                "proficiency": {"self_reported_level": 0.35},
                "difficulty_preferences": {
                    "target_challenge_center": 0.58,
                    "target_challenge_spread": 0.15,
                },
                "empirical_trends": {
                    "topic_bias": {"animals": 0.7, "daily_life": 0.2},
                },
            }
        )

        self.assertEqual(normalized.interests, ("animals",))
        self.assertAlmostEqual(normalized.explicit_topic_weights["animals"], 1.0, places=6)
        self.assertAlmostEqual(normalized.explicit_topic_weights["science"], 0.4, places=6)
        self.assertAlmostEqual(normalized.topic_weights["animals"], 1.0, places=6)
        self.assertAlmostEqual(normalized.topic_weights["science"], 0.4, places=6)
        self.assertAlmostEqual(normalized.topic_weights["daily_life"], 0.2, places=6)
        self.assertEqual(normalized.topic_weight_sources["animals"], "interests")
        self.assertEqual(normalized.topic_weight_sources["science"], "topic_weights")
        self.assertEqual(
            normalized.signal_sources["proficiency"],
            "proficiency.self_reported_level",
        )
        self.assertEqual(
            normalized.signal_sources["challenge_preference"],
            "difficulty_preferences.target_challenge_center",
        )
        self.assertEqual(
            normalized.active_signals,
            ("interests", "proficiency", "challenge_preference"),
        )
        self.assertEqual(normalized.missing_signals, ())

    def test_reports_missing_signals_explicitly(self) -> None:
        normalized = normalize_profile_bootstrap_context({"interests": ["animals"]})

        self.assertEqual(normalized.active_signals, ("interests",))
        self.assertEqual(
            normalized.missing_signals,
            ("proficiency", "challenge_preference"),
        )


class TestProfileBootstrapFrontierGaussianMath(unittest.TestCase):
    def test_policy_summary_exposes_passive_frontier_gaussian_candidate(self) -> None:
        summary = summarize_profile_bootstrap_context(
            {"proficiency": {"estimated_value": 0.93}},
            policy=FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY,
        )

        self.assertEqual(
            summary["policy"]["version"],
            PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_POLICY_VERSION,
        )
        frontier = summary["policy"]["frontier_gaussian"]
        self.assertAlmostEqual(frontier["sigma_low_advanced"], 0.07, places=6)
        self.assertAlmostEqual(frontier["frontier_lane_share"], 0.72, places=6)
        self.assertEqual(summary["selector_version"], "profile_bootstrap_v6")

    def test_high_proficiency_frontier_has_narrow_lower_tail(self) -> None:
        policy = FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY
        on_frontier = compute_frontier_gaussian_fit(0.93, 0.93, policy=policy)
        slightly_below = compute_frontier_gaussian_fit(0.84, 0.93, policy=policy)
        far_below = compute_frontier_gaussian_fit(0.70, 0.93, policy=policy)
        above = compute_frontier_gaussian_fit(0.99, 0.93, policy=policy)

        self.assertAlmostEqual(on_frontier.frontier_fit, 1.0, places=6)
        self.assertGreater(slightly_below.frontier_fit, 0.50)
        self.assertLess(far_below.frontier_fit, 0.02)
        self.assertGreater(above.frontier_fit, 0.88)
        self.assertLess(on_frontier.sigma_low or 0.0, 0.08)

    def test_topic_widens_frontier_without_bypassing_extreme_mismatch(self) -> None:
        policy = FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY
        neutral = compute_frontier_gaussian_fit(0.78, 0.93, policy=policy)
        topical = compute_frontier_gaussian_fit(
            0.78,
            0.93,
            topic_affinity=1.0,
            policy=policy,
        )
        beginner_extreme_topic = compute_frontier_gaussian_fit(
            0.90,
            0.30,
            topic_affinity=1.0,
            policy=policy,
        )

        self.assertGreater(topical.topic_fit, neutral.frontier_fit)
        self.assertGreater(topical.topic_sigma_low or 0.0, neutral.sigma_low or 0.0)
        self.assertLess(beginner_extreme_topic.topic_fit, 0.01)

    def test_trail_fit_targets_missed_words_below_frontier_not_arbitrary_easy_words(
        self,
    ) -> None:
        policy = FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY
        near_trail = compute_frontier_gaussian_fit(0.81, 0.93, policy=policy)
        very_easy = compute_frontier_gaussian_fit(0.30, 0.93, policy=policy)
        on_frontier = compute_frontier_gaussian_fit(0.93, 0.93, policy=policy)

        self.assertGreater(near_trail.trail_fit, 0.99)
        self.assertLess(very_easy.trail_fit, 0.001)
        self.assertAlmostEqual(on_frontier.trail_fit, 0.0, places=6)

    def test_missing_proficiency_keeps_frontier_fit_neutral(self) -> None:
        fit = compute_frontier_gaussian_fit(
            0.50,
            None,
            topic_affinity=1.0,
            policy=FRONTIER_GAUSSIAN_PROFILE_BOOTSTRAP_POLICY,
        )

        self.assertIsNone(fit.target)
        self.assertEqual(fit.frontier_fit, 0.0)
        self.assertEqual(fit.topic_fit, 0.0)
        self.assertEqual(fit.trail_fit, 0.0)

    def test_policy_summary_exposes_passive_frontier_gaussian_hybrid_candidate(
        self,
    ) -> None:
        summary = summarize_profile_bootstrap_context(
            {"proficiency": {"estimated_value": 0.45}},
            policy=FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
        )

        self.assertEqual(
            summary["policy"]["version"],
            PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_POLICY_VERSION,
        )
        frontier = summary["policy"]["frontier_gaussian"]
        self.assertAlmostEqual(frontier["hybrid_topic_min_share"], 0.25, places=6)
        self.assertAlmostEqual(frontier["hybrid_topic_max_share"], 0.45, places=6)
        self.assertAlmostEqual(frontier["hybrid_topic_min_lane_score"], 0.08, places=6)
        self.assertAlmostEqual(frontier["hybrid_topic_lower_margin"], 0.20, places=6)
        self.assertIsNone(frontier["hybrid_topic_lower_penalty_sigma"])

    def test_policy_summary_exposes_passive_soft_topic_hybrid_candidate(
        self,
    ) -> None:
        summary = summarize_profile_bootstrap_context(
            {"proficiency": {"estimated_value": 0.45}},
            policy=FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY,
        )

        self.assertEqual(
            summary["policy"]["version"],
            PROFILE_BOOTSTRAP_FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_POLICY_VERSION,
        )
        frontier = summary["policy"]["frontier_gaussian"]
        self.assertAlmostEqual(
            frontier["hybrid_topic_lower_penalty_sigma"],
            0.03,
            places=6,
        )

    def test_frontier_gaussian_hybrid_preserves_beginner_core_lane(self) -> None:
        seeds = [
            _seed_with_difficulty("core_a", 0.01),
            _seed_with_difficulty("core_b", 0.02),
            _seed_with_difficulty("core_c", 0.03),
            _seed_with_difficulty("core_d", 0.04),
            _seed_with_difficulty("frontier_a", 0.10),
            _seed_with_difficulty("frontier_b", 0.11),
            _seed_with_difficulty("frontier_c", 0.12),
            _seed_with_difficulty("frontier_d", 0.13),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={"proficiency": {"estimated_value": 0.10}},
            selection_count=6,
            preview_limit=6,
        )

        self.assertEqual(diagnostics["selection_policy"], "frontier_gaussian_hybrid_lanes")
        self.assertEqual(diagnostics["lane_targets"]["core"], 2)
        self.assertEqual([entry.selected_lane for entry in selected[:2]], ["core", "core"])
        self.assertEqual(
            [entry.traits.lemma for entry in selected[:2]],
            ["core_a", "core_b"],
        )

    def test_frontier_gaussian_hybrid_uses_core_profile_when_proficiency_missing(
        self,
    ) -> None:
        seeds = [
            _seed_with_difficulty("common", 0.01),
            _seed_with_difficulty("topic_match", 0.02, topics=["animals"]),
            _seed_with_difficulty("general", 0.03),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={"interests": ["animals"]},
            selection_count=2,
            preview_limit=2,
        )

        self.assertEqual(
            diagnostics["lane_targets"],
            {"core": 2, "frontier": 0, "trail": 0, "topic": 0},
        )
        self.assertEqual([entry.selected_lane for entry in selected], ["core", "core"])
        self.assertEqual(selected[0].traits.lemma, "topic_match")

    def test_frontier_gaussian_hybrid_expands_topic_lane_when_near_level_depth_exists(
        self,
    ) -> None:
        seeds = [
            _seed_with_difficulty(f"topic_{index}", 0.43 + (index * 0.002), topics=["animals"])
            for index in range(12)
        ] + [
            _seed_with_difficulty(f"frontier_{index}", 0.45 + (index * 0.001))
            for index in range(12)
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.45},
            },
            selection_count=10,
            preview_limit=10,
        )

        self.assertGreaterEqual(diagnostics["lane_targets"]["topic"], 3)
        self.assertGreaterEqual(
            [entry.selected_lane for entry in selected].count("topic"),
            3,
        )
        self.assertGreater(
            diagnostics["hybrid_topic_depth"]["eligible_candidate_count"],
            0,
        )

    def test_frontier_gaussian_hybrid_filters_extreme_topic_mismatch(self) -> None:
        seeds = [
            _seed_with_difficulty("topic_extreme_easy", 0.30, topics=["animals"]),
            _seed_with_difficulty("topic_near", 0.68, topics=["animals"]),
            _seed_with_difficulty("frontier_exact", 0.73),
            _seed_with_difficulty("frontier_above", 0.75),
            _seed_with_difficulty("trail", 0.61),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.73},
            },
            selection_count=4,
            preview_limit=4,
        )

        self.assertEqual(diagnostics["hybrid_topic_depth"]["eligible_candidate_count"], 1)
        self.assertIn("topic_near", [entry.traits.lemma for entry in selected])
        self.assertNotIn("topic_extreme_easy", [entry.traits.lemma for entry in selected])

    def test_frontier_gaussian_hybrid_soft_topic_keeps_near_lower_tail_topic(
        self,
    ) -> None:
        seeds = [
            _seed_with_difficulty("topic_just_below_guard", 0.525, topics=["animals"]),
            _seed_with_difficulty("topic_far_below_guard", 0.40, topics=["animals"]),
            _seed_with_difficulty("frontier_exact", 0.73),
            _seed_with_difficulty("frontier_above", 0.75),
            _seed_with_difficulty("trail", 0.61),
        ]

        hard_selected, hard_diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.73},
            },
            selection_count=3,
            preview_limit=3,
            policy=FRONTIER_GAUSSIAN_HYBRID_PROFILE_BOOTSTRAP_POLICY,
        )
        soft_selected, soft_diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.73},
            },
            selection_count=3,
            preview_limit=3,
            policy=FRONTIER_GAUSSIAN_HYBRID_SOFT_TOPIC_PROFILE_BOOTSTRAP_POLICY,
        )

        self.assertNotIn(
            "topic_just_below_guard",
            [entry.traits.lemma for entry in hard_selected],
        )
        self.assertIn(
            "topic_just_below_guard",
            [entry.traits.lemma for entry in soft_selected],
        )
        self.assertNotIn(
            "topic_far_below_guard",
            [entry.traits.lemma for entry in soft_selected],
        )
        self.assertEqual(
            hard_diagnostics["hybrid_topic_depth"]["eligible_candidate_count"],
            0,
        )
        self.assertEqual(
            soft_diagnostics["hybrid_topic_depth"]["eligible_candidate_count"],
            1,
        )

    def test_frontier_gaussian_hybrid_dedupes_same_lemma_candidates(self) -> None:
        seeds = [
            _seed_with_difficulty("duplicate", 0.45, topics=["animals"]),
            _seed_with_difficulty("duplicate", 0.45, topics=["animals"]),
            _seed_with_difficulty("frontier_a", 0.45),
            _seed_with_difficulty("frontier_b", 0.46),
            _seed_with_difficulty("frontier_c", 0.47),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_hybrid_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.45},
            },
            selection_count=5,
            preview_limit=5,
        )

        lemmas = [entry.traits.lemma for entry in selected]
        self.assertEqual(lemmas.count("duplicate"), 1)
        self.assertEqual(diagnostics["selected_candidate_count"], 4)

    def test_frontier_gaussian_lane_selector_fills_deterministic_quotas(self) -> None:
        seeds = [
            _seed_with_difficulty("topic_near", 0.78, topics=["animals"]),
            _seed_with_difficulty("topic_extreme_easy", 0.30, topics=["animals"]),
            _seed_with_difficulty("trail_center", 0.81),
            _seed_with_difficulty("trail_near", 0.84),
            _seed_with_difficulty("frontier_exact", 0.93),
            _seed_with_difficulty("frontier_above", 0.99),
            _seed_with_difficulty("frontier_slight_below", 0.90),
            _seed_with_difficulty("frontier_high_below", 0.88),
            _seed_with_difficulty("frontier_upper", 0.96),
            _seed_with_difficulty("frontier_more_below", 0.86),
            _seed_with_difficulty("frontier_other", 0.92),
            _seed_with_difficulty("too_easy", 0.30),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.93},
            },
            selection_count=10,
            preview_limit=10,
        )

        self.assertEqual(diagnostics["selection_policy"], "frontier_gaussian_lanes")
        self.assertEqual(
            diagnostics["lane_targets"],
            {"frontier": 7, "trail": 2, "topic": 1},
        )
        self.assertEqual(
            diagnostics["filled_lane_counts"],
            {"frontier": 7, "trail": 2, "topic": 1},
        )
        self.assertEqual(len(selected), 10)
        self.assertEqual(selected[0].selected_lane, "topic")
        self.assertEqual(selected[0].traits.lemma, "topic_near")
        selected_by_lane = {
            lane: [entry.traits.lemma for entry in selected if entry.selected_lane == lane]
            for lane in ("topic", "trail", "frontier")
        }
        self.assertEqual(selected_by_lane["topic"], ["topic_near"])
        self.assertEqual(selected_by_lane["trail"], ["trail_center", "trail_near"])
        self.assertNotIn("topic_extreme_easy", [entry.traits.lemma for entry in selected])
        preview_first = diagnostics["ranking_preview"][0]
        self.assertEqual(preview_first["selected_lane"], "topic")
        self.assertIn("frontier_gaussian", preview_first)
        self.assertIn("base_profile_bootstrap", diagnostics)

    def test_frontier_gaussian_lane_selector_spills_sparse_topic_quota_to_frontier(
        self,
    ) -> None:
        seeds = [
            _seed_with_difficulty("frontier_exact", 0.93),
            _seed_with_difficulty("frontier_above", 0.99),
            _seed_with_difficulty("frontier_slight_below", 0.90),
            _seed_with_difficulty("trail_center", 0.81),
            _seed_with_difficulty("too_easy", 0.30),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_profile(
            seeds,
            profile_context={"proficiency": {"estimated_value": 0.93}},
            selection_count=4,
            preview_limit=4,
        )

        self.assertEqual(diagnostics["lane_targets"], {"frontier": 3, "trail": 1, "topic": 0})
        self.assertEqual([entry.selected_lane for entry in selected].count("frontier"), 3)
        self.assertEqual([entry.selected_lane for entry in selected].count("trail"), 1)
        self.assertEqual(
            [entry.traits.lemma for entry in selected[:2]],
            [
                "trail_center",
                "frontier_exact",
            ],
        )

    def test_frontier_gaussian_lane_selector_excludes_zero_suitability_candidates(
        self,
    ) -> None:
        seeds = [
            _seed_with_difficulty("valid_frontier", 0.93),
            _seed_with_difficulty("suppressed_frontier", 0.94, admission_suitability=0.0),
            _seed_with_difficulty("valid_trail", 0.81),
        ]

        selected, diagnostics = score_seed_words_for_frontier_gaussian_profile(
            seeds,
            profile_context={"proficiency": {"estimated_value": 0.93}},
            selection_count=3,
            preview_limit=3,
        )

        self.assertEqual(diagnostics["selectable_candidate_count"], 2)
        self.assertEqual(
            [entry.traits.lemma for entry in selected],
            ["valid_trail", "valid_frontier"],
        )
        self.assertNotIn(
            "suppressed_frontier",
            [entry["lemma"] for entry in diagnostics["ranking_preview"]],
        )


class TestProfileBootstrapTraits(unittest.TestCase):
    def test_extracts_candidate_traits_separately_from_user_context(self) -> None:
        traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="する",
                admission_weight=0.72,
                metadata={
                    "sense_topics": ["animals"],
                    "source_surface_original": "為る",
                },
                word_package={
                    "surface": "する",
                    "reading": "する",
                    "sublemma": "為る",
                    "lform_raw": "する",
                    "script_forms": {"kanji": "為る", "kana": "する"},
                    "profile_topics": ["daily_life"],
                    "source": {
                        "surface_normalized_from": "為る",
                        "topics": "grammar",
                    },
                },
            )
        )

        self.assertAlmostEqual(traits.base_freq, 0.72, places=6)
        self.assertAlmostEqual(traits.difficulty_estimate, 0.28, places=6)
        self.assertEqual(traits.difficulty_proxy, "1_minus_base_weight")
        self.assertEqual(set(traits.lexical_forms), {"する", "為る"})
        self.assertEqual(set(traits.raw_topic_hints), {"animals", "daily_life", "grammar"})
        self.assertEqual(set(traits.topic_hints), {"animals", "daily_life", "grammar"})

    def test_difficulty_uses_base_weight_not_pos_demoted_admission_weight(self) -> None:
        traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="七百",
                language_pair="en-ja",
                pos="名詞-数詞",
                base_weight=0.82,
                admission_weight=0.33,
                metadata={},
            )
        )

        self.assertAlmostEqual(traits.lexical_commonness, 0.82, places=6)
        self.assertAlmostEqual(traits.coverage_gain, 0.33, places=6)
        self.assertAlmostEqual(traits.base_freq, 0.33, places=6)
        self.assertAlmostEqual(traits.difficulty_estimate, 0.18, places=6)
        self.assertEqual(traits.candidate_state, "suppressed_default")
        self.assertEqual(traits.presentation_mode, "suppress")
        self.assertEqual(traits.problem_class, "numeral_or_counter")
        self.assertAlmostEqual(traits.admission_suitability, 0.0, places=6)

    def test_reuses_precomputed_candidate_traits_when_policy_version_matches(self) -> None:
        seed = SimpleNamespace(
            lemma="dog",
            language_pair="en-ja",
            base_weight=0.70,
            admission_weight=0.70,
            metadata={"sense_topics": ["pets"]},
        )

        attached_count = attach_precomputed_profile_bootstrap_candidate_traits([seed])

        self.assertEqual(attached_count, 1)
        self.assertIn(ADMISSION_CANDIDATE_FEATURES_METADATA_KEY, seed.metadata)
        self.assertIn(ADMISSION_CANDIDATE_FEATURES_PRECOMPUTE_VERSION_KEY, seed.metadata)
        seed.base_weight = 0.05
        seed.admission_weight = 0.05
        traits = extract_profile_bootstrap_candidate_traits(seed)

        self.assertAlmostEqual(traits.lexical_commonness, 0.70, places=6)
        self.assertEqual(traits.topic_hints, ("animals", "pets"))

    def test_runtime_candidate_trait_cache_respects_topic_metadata_changes(self) -> None:
        clear_profile_bootstrap_candidate_trait_cache()
        first_seed = SimpleNamespace(
            lemma="dog",
            language_pair="en-ja",
            base_weight=0.70,
            admission_weight=0.70,
            metadata={},
        )
        second_seed = SimpleNamespace(
            lemma="dog",
            language_pair="en-ja",
            base_weight=0.70,
            admission_weight=0.70,
            metadata={"profile_topics": ["pets"]},
        )

        first_traits = extract_profile_bootstrap_candidate_traits(first_seed)
        second_traits = extract_profile_bootstrap_candidate_traits(second_seed)

        self.assertNotIn("pets", first_traits.topic_hints)
        self.assertIn("pets", second_traits.topic_hints)

    def test_en_ja_corrected_ranking_uses_packaged_resource_by_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            clear_corrected_learner_difficulty_cache()
            traits = extract_profile_bootstrap_candidate_traits(
                SimpleNamespace(
                    lemma="つく",
                    language_pair="en-ja",
                    pos="名詞-普通名詞-一般",
                    base_weight=0.99,
                    admission_weight=0.99,
                    metadata={},
                    word_package={"reading": "ツク"},
                )
            )
            resolved_csv = resolve_corrected_en_ja_learner_difficulty_csv_path()
            resolved_manual = resolve_packaged_en_ja_learner_difficulty_manual_corrections_path()
            clear_corrected_learner_difficulty_cache()

        self.assertIsNotNone(resolved_csv)
        self.assertIsNotNone(resolved_manual)
        self.assertAlmostEqual(traits.difficulty_estimate, 0.006081, places=6)
        self.assertEqual(
            traits.difficulty_proxy,
            "learner_difficulty_v1:en_ja_corrected_ranking:exact_pair",
        )
        self.assertEqual(traits.candidate_state, "suppressed_default")
        self.assertEqual(traits.presentation_mode, "suppress")

    def test_en_ja_learner_difficulty_overlay_remains_fallback_when_csv_unavailable(
        self,
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: "/tmp/missing-lexishift.csv"},
        ):
            clear_corrected_learner_difficulty_cache()
            traits = extract_profile_bootstrap_candidate_traits(
                SimpleNamespace(
                    lemma="猫",
                    language_pair="en-ja",
                    pos="名詞-普通名詞-一般",
                    base_weight=0.39,
                    admission_weight=0.39,
                    metadata={},
                )
            )
            clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.20, places=6)
        self.assertEqual(
            traits.difficulty_proxy,
            "learner_difficulty_v1:en_ja_exact_overlay",
        )
        self.assertIn("beginner_core_animal", traits.difficulty_sources)

    def test_en_ja_reading_specific_overlay_covers_missing_frequency_seed_rows(self) -> None:
        with mock.patch.dict(
            os.environ,
            {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: "/tmp/missing-lexishift.csv"},
        ):
            clear_corrected_learner_difficulty_cache()
            traits = extract_profile_bootstrap_candidate_traits(
                SimpleNamespace(
                    lemma="週",
                    language_pair="en-ja",
                    pos="名詞-普通名詞-助数詞可能",
                    base_weight=0.35,
                    admission_weight=0.35,
                    metadata={},
                    word_package={"reading": "シュウ", "lform_raw": "シュウ"},
                )
            )
            clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.22, places=6)
        self.assertEqual(
            traits.difficulty_proxy,
            "learner_difficulty_v1:en_ja_reading_exact_overlay",
        )
        self.assertIn("common_calendar_reading", traits.difficulty_sources)

    def test_en_ja_corrected_ranking_csv_overrides_frequency_difficulty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band\n")
                handle.write("1,行く,いく,0.004,0.00-0.05\n")
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                traits = extract_profile_bootstrap_candidate_traits(
                    SimpleNamespace(
                        lemma="行く",
                        language_pair="en-ja",
                        base_weight=0.40,
                        admission_weight=0.40,
                        metadata={},
                        word_package={"reading": "イク"},
                    )
                )
                clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.004, places=6)
        self.assertEqual(
            traits.difficulty_proxy,
            "learner_difficulty_v1:en_ja_corrected_ranking:exact_pair",
        )
        self.assertIn("en_ja_corrected_learner_difficulty_csv", traits.difficulty_sources)

    def test_en_ja_corrected_ranking_matches_unique_display_form(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band,correction_types,display_form\n")
                handle.write("1,段々,だんだん,0.096,0.05-0.10,display_only,だんだん\n")
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                traits = extract_profile_bootstrap_candidate_traits(
                    SimpleNamespace(
                        lemma="だんだん",
                        language_pair="en-ja",
                        base_weight=0.31,
                        admission_weight=0.31,
                        metadata={},
                    )
                )
                match = lookup_corrected_en_ja_learner_difficulty(lemma="だんだん")
                clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.096, places=6)
        self.assertEqual(
            traits.difficulty_proxy,
            "learner_difficulty_v1:en_ja_corrected_ranking:exact_display_pair",
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.match_mode, "unique_display_form")

    def test_en_ja_corrected_ranking_avoids_ambiguous_display_form_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band,correction_types,display_form\n")
                handle.write("1,仮名一,かな,0.10,0.10-0.15,display_only,かな\n")
                handle.write("2,仮名二,かなに,0.60,0.60-0.65,display_only,かな\n")
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                ambiguous = lookup_corrected_en_ja_learner_difficulty(lemma="かな")
                exact = lookup_corrected_en_ja_learner_difficulty(
                    lemma="かな",
                    reading="かなに",
                )
                clear_corrected_learner_difficulty_cache()

        self.assertIsNone(ambiguous)
        self.assertIsNotNone(exact)
        self.assertEqual(exact.match_mode, "exact_display_pair")
        self.assertAlmostEqual(exact.row.score, 0.60, places=6)

    def test_en_ja_corrected_ranking_avoids_reading_only_homophone_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band\n")
                handle.write("1,園,その,0.35,0.35-0.40\n")
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                traits = extract_profile_bootstrap_candidate_traits(
                    SimpleNamespace(
                        lemma="其の",
                        language_pair="en-ja",
                        base_weight=0.90,
                        admission_weight=0.90,
                        metadata={},
                        word_package={"reading": "ソノ"},
                    )
                )
                clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.10, places=6)
        self.assertEqual(traits.difficulty_proxy, "1_minus_base_weight")

    def test_en_ja_corrected_ranking_excludes_standalone_srs_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band,correction_types,admission_override\n")
                handle.write(
                    "1,つく,つく,0.006,0.00-0.05,exclude_standalone_srs,exclude_standalone_srs\n"
                )
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                traits = extract_profile_bootstrap_candidate_traits(
                    SimpleNamespace(
                        lemma="つく",
                        language_pair="en-ja",
                        base_weight=0.90,
                        admission_weight=0.90,
                        metadata={},
                        word_package={"reading": "ツク"},
                    )
                )
                clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.006, places=6)
        self.assertEqual(traits.candidate_state, "suppressed_default")
        self.assertEqual(traits.presentation_mode, "suppress")
        self.assertAlmostEqual(traits.admission_suitability, 0.0, places=6)
        self.assertIn(
            "corrected_ranking:exclude_standalone_srs",
            traits.classification_reasons,
        )

    def test_en_ja_corrected_ranking_restricts_reviewed_variant_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "corrected.csv")
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                handle.write("rank,lemma,reading,score,band,correction_types,admission_override\n")
                handle.write(
                    '1,居る,おる,0.24,0.20-0.25,"score_floor,'
                    'restricted_admission",variant_reading\n'
                )
            with mock.patch.dict(
                os.environ,
                {CORRECTED_EN_JA_LEARNER_DIFFICULTY_CSV_ENV: csv_path},
            ):
                clear_corrected_learner_difficulty_cache()
                traits = extract_profile_bootstrap_candidate_traits(
                    SimpleNamespace(
                        lemma="居る",
                        language_pair="en-ja",
                        base_weight=0.70,
                        admission_weight=0.70,
                        metadata={},
                        word_package={"reading": "オル"},
                    )
                )
                clear_corrected_learner_difficulty_cache()

        self.assertAlmostEqual(traits.difficulty_estimate, 0.24, places=6)
        self.assertEqual(traits.candidate_state, "suppressed_default")
        self.assertEqual(traits.presentation_mode, "suppress")
        self.assertEqual(traits.problem_class, "variant_reading")
        self.assertAlmostEqual(traits.admission_suitability, 0.0, places=6)

    def test_builds_signal_pack_from_traits_and_context(self) -> None:
        context = normalize_profile_bootstrap_context(
            {
                "interests": ["animals"],
                "proficiency": {"self_reported_level": 0.35},
                "difficulty_preferences": {"target_challenge_center": 0.30},
            }
        )
        traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="猫",
                admission_weight=0.72,
                metadata={"sense_topics": ["animals"]},
            )
        )

        signal_pack = build_profile_bootstrap_signal_pack(traits, context)
        self.assertAlmostEqual(signal_pack.topic_affinity, 1.0, places=6)
        self.assertEqual(signal_pack.topic_affinity_source, "topic_hint:animals")
        self.assertGreater(signal_pack.proficiency_fit, 0.0)
        self.assertGreater(signal_pack.challenge_fit, 0.0)
        self.assertAlmostEqual(signal_pack.readiness_multiplier, 1.0, places=6)
        self.assertAlmostEqual(signal_pack.admission_suitability, 1.0, places=6)

    def test_deprioritized_vocab_candidates_recover_suitability_when_topic_matches(self) -> None:
        topic_context = normalize_profile_bootstrap_context({"interests": ["history"]})
        neutral_context = normalize_profile_bootstrap_context({})
        traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="自民",
                language_pair="en-ja",
                pos="名詞-固有名詞-一般",
                base_weight=0.70,
                admission_weight=0.70,
                metadata={"topics": ["history"]},
            )
        )

        topic_signal_pack = build_profile_bootstrap_signal_pack(traits, topic_context)
        neutral_signal_pack = build_profile_bootstrap_signal_pack(traits, neutral_context)

        self.assertEqual(traits.candidate_state, "deprioritized_vocab")
        self.assertAlmostEqual(neutral_signal_pack.admission_suitability, 0.25, places=6)
        self.assertAlmostEqual(topic_signal_pack.admission_suitability, 0.80, places=6)

    def test_readiness_gate_suppresses_far_too_easy_words_for_advanced_users(self) -> None:
        context = normalize_profile_bootstrap_context(
            {
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.80},
                "difficulty_preferences": {
                    "target_challenge_center": 0.80,
                    "target_challenge_spread": 0.12,
                },
            }
        )
        slightly_easy_topic_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="falcon",
                admission_weight=0.44,
                metadata={"topics": ["animals"]},
            )
        )
        far_too_easy_topic_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="cat",
                admission_weight=0.90,
                metadata={"topics": ["animals"]},
            )
        )

        slightly_easy_signal_pack = build_profile_bootstrap_signal_pack(
            slightly_easy_topic_traits,
            context,
        )
        far_too_easy_signal_pack = build_profile_bootstrap_signal_pack(
            far_too_easy_topic_traits,
            context,
        )

        self.assertGreater(slightly_easy_signal_pack.readiness_multiplier, 0.95)
        self.assertAlmostEqual(slightly_easy_signal_pack.readiness_lower_bound, 0.53, places=6)
        self.assertAlmostEqual(slightly_easy_signal_pack.readiness_too_easy_gap, 0.0, places=6)
        self.assertLess(far_too_easy_signal_pack.readiness_multiplier, 0.01)
        self.assertGreater(far_too_easy_signal_pack.readiness_too_easy_gap, 0.40)

    def test_advanced_proficiency_fit_does_not_boost_far_too_easy_words(self) -> None:
        easy_seed = SimpleNamespace(
            lemma="easy_probe",
            language_pair="en-ja",
            base_weight=0.81,
            admission_weight=0.81,
            metadata={},
        )
        near_seed = SimpleNamespace(
            lemma="near_probe",
            language_pair="en-ja",
            base_weight=0.35,
            admission_weight=0.35,
            metadata={},
        )
        harder_seed = SimpleNamespace(
            lemma="harder_probe",
            language_pair="en-ja",
            base_weight=0.15,
            admission_weight=0.15,
            metadata={},
        )

        scored_entries, _diagnostics = score_seed_words_for_profile(
            [easy_seed, near_seed, harder_seed],
            profile_context={"proficiency": {"estimated_value": 0.75}},
            preview_limit=3,
        )

        self.assertEqual(
            [entry.traits.lemma for entry in scored_entries],
            ["near_probe", "harder_probe", "easy_probe"],
        )
        hard_entry = scored_entries[1]
        easy_entry = scored_entries[2]
        self.assertGreater(hard_entry.signal_pack.proficiency_fit, 0.80)
        self.assertAlmostEqual(easy_entry.signal_pack.difficulty_estimate, 0.19, places=6)
        self.assertLess(easy_entry.signal_pack.proficiency_fit, 0.10)
        self.assertLess(easy_entry.signal_pack.readiness_multiplier, 0.001)
        self.assertIn("readiness_gate", easy_entry.scored_candidate.breakdown.penalties)

    def test_explicit_challenge_target_sets_readiness_center(self) -> None:
        context = normalize_profile_bootstrap_context(
            {
                "proficiency": {"estimated_value": 0.80},
                "difficulty_preferences": {
                    "target_challenge_center": 0.20,
                    "target_challenge_spread": 0.12,
                },
            }
        )
        easy_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="cat",
                admission_weight=0.80,
                metadata={},
            )
        )

        signal_pack = build_profile_bootstrap_signal_pack(easy_traits, context)

        self.assertEqual(signal_pack.readiness_center_source, "challenge_target")
        self.assertAlmostEqual(signal_pack.readiness_center or 0.0, 0.20, places=6)
        self.assertAlmostEqual(signal_pack.readiness_multiplier, 1.0, places=6)
        self.assertAlmostEqual(signal_pack.readiness_too_easy_gap, 0.0, places=6)

    def test_topic_family_expansion_allows_pets_to_match_animals(self) -> None:
        context = normalize_profile_bootstrap_context({"interests": ["animals"]})
        traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="dog",
                admission_weight=0.62,
                metadata={"sense_topics": ["pets"]},
            )
        )

        signal_pack = build_profile_bootstrap_signal_pack(traits, context)
        self.assertIn("pets", traits.raw_topic_hints)
        self.assertIn("animals", traits.topic_hints)
        self.assertAlmostEqual(signal_pack.topic_affinity, 1.0, places=6)
        self.assertEqual(signal_pack.topic_affinity_source, "topic_hint:pets->animals")

    def test_topic_specificity_dampens_mixed_domain_matches(self) -> None:
        context = normalize_profile_bootstrap_context({"interests": ["sports"]})
        clean_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="penal",
                admission_weight=0.60,
                metadata={"sense_topics": ["ball-games", "soccer", "sports"]},
            )
        )
        mixed_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="titular",
                admission_weight=0.60,
                metadata={
                    "sense_topics": [
                        "sports",
                        "chemistry",
                        "natural-sciences",
                        "physical-sciences",
                    ]
                },
            )
        )

        clean_signal_pack = build_profile_bootstrap_signal_pack(clean_traits, context)
        mixed_signal_pack = build_profile_bootstrap_signal_pack(mixed_traits, context)

        self.assertGreater(clean_signal_pack.topic_affinity, mixed_signal_pack.topic_affinity)
        self.assertGreater(clean_signal_pack.topic_specificity, mixed_signal_pack.topic_specificity)
        self.assertEqual(clean_signal_pack.topic_support_count, 3)
        self.assertEqual(clean_signal_pack.topic_hint_count, 3)
        self.assertEqual(mixed_signal_pack.topic_support_count, 1)
        self.assertEqual(mixed_signal_pack.topic_hint_count, 4)
        self.assertEqual(mixed_signal_pack.topic_affinity_source, "topic_hint:sports")


class TestProfileBootstrapReranking(unittest.TestCase):
    def test_neutral_context_preserves_frequency_order(self) -> None:
        seeds = [
            SimpleNamespace(lemma="alpha", language_pair="en-ja", admission_weight=0.80),
            SimpleNamespace(lemma="beta", language_pair="en-ja", admission_weight=0.70),
        ]

        reranked, diagnostics = rerank_seed_words_for_profile(seeds, profile_context={})

        self.assertEqual([item.lemma for item in reranked], ["alpha", "beta"])
        self.assertEqual(
            diagnostics["profile_context"]["missing_signals"],
            ["interests", "proficiency", "challenge_preference"],
        )
        self.assertEqual(
            diagnostics["ranking_preview"][0]["explanation"],
            "Kept in neutral frequency order because profile signals were effectively neutral.",
        )
        self.assertEqual(diagnostics["selection_policy"], "reserved_topic_lane")
        self.assertAlmostEqual(
            diagnostics["policy"]["topic_lane_max_share"],
            0.5,
            places=6,
        )

    def test_interest_match_explanation_reports_profile_lift_and_coverage_support(self) -> None:
        seeds = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.80,
                metadata={},
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.70,
                metadata={"topics": ["animals"]},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={"interests": ["animals"]},
        )

        self.assertEqual(diagnostics["ranking_preview"][0]["lemma"], "beta")
        self.assertEqual(
            diagnostics["ranking_preview"][0]["explanation"],
            "Boosted by topic_affinity, while remaining supported by coverage_gain.",
        )
        self.assertEqual(
            diagnostics["ranking_preview"][1]["explanation"],
            "Still supported by coverage_gain, but moved down because other items received stronger overall profile lift.",
        )

    def test_interest_match_uses_canonical_topic_families(self) -> None:
        seeds = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.80,
                metadata={},
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.70,
                metadata={"topics": ["card-games"]},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={"interests": ["games"]},
        )

        self.assertEqual(diagnostics["ranking_preview"][0]["lemma"], "beta")
        self.assertEqual(
            diagnostics["ranking_preview"][0]["signals"]["topic_affinity_source"],
            "topic_hint:card_games->games",
        )

    def test_readiness_gate_lets_relevant_near_level_words_beat_too_easy_words(
        self,
    ) -> None:
        seeds = [
            SimpleNamespace(
                lemma="basic",
                language_pair="en-ja",
                admission_weight=0.95,
                metadata={},
            ),
            SimpleNamespace(
                lemma="falcon",
                language_pair="en-ja",
                admission_weight=0.44,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="advanced",
                language_pair="en-ja",
                admission_weight=0.20,
                metadata={},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.80},
                "difficulty_preferences": {
                    "target_challenge_center": 0.80,
                    "target_challenge_spread": 0.12,
                },
            },
        )

        preview_by_lemma = {entry["lemma"]: entry for entry in diagnostics["ranking_preview"]}
        self.assertEqual(diagnostics["ranking_preview"][0]["lemma"], "falcon")
        self.assertGreater(
            preview_by_lemma["falcon"]["signals"]["readiness_multiplier"],
            0.95,
        )
        self.assertLess(
            preview_by_lemma["basic"]["signals"]["readiness_multiplier"],
            0.001,
        )
        self.assertIn(
            "readiness_gate",
            preview_by_lemma["basic"]["penalties"],
        )

    def test_admission_suitability_suppresses_compositional_numbers_in_default_vocab_lane(
        self,
    ) -> None:
        seeds = [
            SimpleNamespace(
                lemma="学校",
                language_pair="en-ja",
                pos="名詞-普通名詞",
                base_weight=0.50,
                admission_weight=0.50,
                metadata={},
            ),
            SimpleNamespace(
                lemma="七百",
                language_pair="en-ja",
                pos="名詞-数詞",
                base_weight=0.95,
                admission_weight=0.95,
                metadata={},
            ),
        ]

        reranked, diagnostics = rerank_seed_words_for_profile(seeds, profile_context={})

        self.assertEqual([item.lemma for item in reranked], ["学校", "七百"])
        preview_by_lemma = {entry["lemma"]: entry for entry in diagnostics["ranking_preview"]}
        self.assertEqual(
            preview_by_lemma["七百"]["candidate_traits"]["candidate_state"],
            "suppressed_default",
        )
        self.assertAlmostEqual(
            preview_by_lemma["七百"]["signals"]["admission_suitability"],
            0.0,
            places=6,
        )
        self.assertIn(
            "admission_suitability",
            preview_by_lemma["七百"]["penalties"],
        )

    def test_active_topic_support_reports_sparse_topic_as_not_ready(self) -> None:
        seeds = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.80,
                metadata={},
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.70,
                metadata={"topics": ["animals"]},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={"interests": ["animals"]},
        )

        support_summary = diagnostics["active_topic_support"]
        self.assertEqual(support_summary["scope"], "neutral_seed_frontier")
        self.assertEqual(support_summary["total_candidates"], 2)
        self.assertEqual(len(support_summary["topics"]), 1)
        topic_entry = support_summary["topics"][0]
        self.assertEqual(topic_entry["topic"], "animals")
        self.assertEqual(topic_entry["candidate_count"], 1)
        self.assertAlmostEqual(topic_entry["support_mass"], 0.7, places=6)
        self.assertFalse(topic_entry["eligible_for_scarcity_calibration"])
        self.assertAlmostEqual(topic_entry["scarcity_multiplier_preview"], 1.0, places=6)
        self.assertEqual(
            topic_entry["scarcity_readiness_reasons"],
            ["support_count_below_min", "support_mass_below_min"],
        )
        self.assertEqual(topic_entry["top_examples"], ["beta"])

    def test_topic_depth_by_level_reports_preferred_topic_readiness_bands(self) -> None:
        seeds = [
            SimpleNamespace(
                lemma="cat",
                language_pair="en-ja",
                admission_weight=0.90,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="falcon",
                language_pair="en-ja",
                admission_weight=0.44,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="advanced",
                language_pair="en-ja",
                admission_weight=0.20,
                metadata={},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={
                "interests": ["animals"],
                "proficiency": {"estimated_value": 0.80},
                "difficulty_preferences": {
                    "target_challenge_center": 0.80,
                    "target_challenge_spread": 0.12,
                },
            },
        )

        depth = diagnostics["topic_depth_by_level"]
        self.assertEqual(depth["version"], "profile_topic_depth_v1")
        self.assertEqual(depth["total_candidates"], 3)
        topic_entry = depth["topics"][0]
        self.assertEqual(topic_entry["topic"], "animals")
        self.assertEqual(topic_entry["candidate_count"], 2)
        self.assertEqual(topic_entry["ready_candidate_count"], 1)
        self.assertAlmostEqual(topic_entry["max_difficulty"], 0.56, places=6)
        bands_by_id = {entry["band"]: entry for entry in topic_entry["bands"]}
        self.assertEqual(bands_by_id["0.00-0.20"]["candidate_count"], 1)
        self.assertEqual(bands_by_id["0.00-0.20"]["ready_candidate_count"], 0)
        self.assertEqual(bands_by_id["0.40-0.60"]["candidate_count"], 1)
        self.assertEqual(bands_by_id["0.40-0.60"]["ready_candidate_count"], 1)
        self.assertEqual(
            bands_by_id["0.40-0.60"]["top_examples"][0]["lemma"],
            "falcon",
        )

    def test_active_topic_support_reports_eligible_topic_when_frontier_support_is_real(
        self,
    ) -> None:
        seeds = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.80,
                metadata={},
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.70,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="gamma",
                language_pair="en-ja",
                admission_weight=0.60,
                metadata={"topics": ["pets"]},
            ),
            SimpleNamespace(
                lemma="delta",
                language_pair="en-ja",
                admission_weight=0.55,
                metadata={"topics": ["animals"]},
            ),
        ]

        _reranked, diagnostics = rerank_seed_words_for_profile(
            seeds,
            profile_context={"interests": ["animals"]},
        )

        topic_entry = diagnostics["active_topic_support"]["topics"][0]
        self.assertEqual(topic_entry["topic"], "animals")
        self.assertEqual(topic_entry["candidate_count"], 3)
        self.assertGreater(topic_entry["support_mass"], 1.0)
        self.assertTrue(topic_entry["eligible_for_scarcity_calibration"])
        self.assertEqual(topic_entry["scarcity_readiness"], "eligible")
        self.assertEqual(topic_entry["scarcity_readiness_reasons"], [])
        self.assertGreater(topic_entry["scarcity_multiplier_preview"], 1.0)
        self.assertEqual(topic_entry["top_examples"], ["beta", "gamma", "delta"])

    def test_scarcity_bonus_activates_only_for_sparse_but_real_topic_support(self) -> None:
        context = normalize_profile_bootstrap_context({"interests": ["animals"]})
        sparse_supported_seeds = [
            SimpleNamespace(lemma="alpha", admission_weight=0.80, metadata={}),
            SimpleNamespace(lemma="beta", admission_weight=0.70, metadata={"topics": ["animals"]}),
            SimpleNamespace(lemma="gamma", admission_weight=0.60, metadata={"topics": ["pets"]}),
            SimpleNamespace(lemma="delta", admission_weight=0.55, metadata={"topics": ["animals"]}),
        ]
        support_summary = rerank_seed_words_for_profile(
            sparse_supported_seeds,
            profile_context={"interests": ["animals"]},
        )[1]["active_topic_support"]
        support_by_topic = {entry["topic"]: entry for entry in support_summary["topics"]}

        sparse_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="epsilon",
                admission_weight=0.58,
                metadata={"topics": ["animals"]},
            )
        )
        neutral_traits = extract_profile_bootstrap_candidate_traits(
            SimpleNamespace(
                lemma="zeta",
                admission_weight=0.58,
                metadata={},
            )
        )

        sparse_signal_pack = build_profile_bootstrap_signal_pack(
            sparse_traits,
            context,
            active_topic_support=support_by_topic,
        )
        neutral_signal_pack = build_profile_bootstrap_signal_pack(
            neutral_traits,
            context,
            active_topic_support=support_by_topic,
        )

        self.assertGreater(sparse_signal_pack.scarcity_bonus, 0.0)
        self.assertEqual(sparse_signal_pack.scarcity_bonus_source, "topic:animals")
        self.assertEqual(neutral_signal_pack.scarcity_bonus, 0.0)
        self.assertIsNone(neutral_signal_pack.scarcity_bonus_source)


if __name__ == "__main__":
    unittest.main()
