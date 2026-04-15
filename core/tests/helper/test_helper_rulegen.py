from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.rulegen import (  # noqa: E402
    RulegenConfig,
    SetInitializationConfig,
    initialize_store_from_frequency_list_with_report,
    run_rulegen_for_pair,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsItem, SrsStore  # noqa: E402


class TestHelperRulegenInitialization(unittest.TestCase):
    def test_limits_admission_to_initial_active_count(self) -> None:
        selected = [
            SimpleNamespace(lemma="alpha", language_pair="en-ja"),
            SimpleNamespace(lemma="beta", language_pair="en-ja"),
            SimpleNamespace(lemma="gamma", language_pair="en-ja"),
            SimpleNamespace(lemma="delta", language_pair="en-ja"),
            SimpleNamespace(lemma="epsilon", language_pair="en-ja"),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=2,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        self.assertEqual(len(store.items), 2)
        self.assertEqual(report.selected_count, 5)
        self.assertEqual(report.selected_unique_count, 5)
        self.assertEqual(report.admitted_count, 2)
        self.assertEqual(report.inserted_count, 2)
        self.assertEqual(report.updated_count, 0)
        self.assertEqual(tuple(report.initial_active_preview), ("alpha", "beta"))

    def test_deduplicates_before_admission(self) -> None:
        selected = [
            SimpleNamespace(lemma="alpha", language_pair="en-ja"),
            SimpleNamespace(lemma="alpha", language_pair="en-ja"),
            SimpleNamespace(lemma="beta", language_pair="en-ja"),
            SimpleNamespace(lemma="gamma", language_pair="en-ja"),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=3,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        self.assertEqual(len(store.items), 3)
        self.assertEqual(report.selected_count, 4)
        self.assertEqual(report.selected_unique_count, 3)
        self.assertEqual(report.admitted_count, 3)
        self.assertEqual(report.inserted_count, 3)

    def test_reports_updates_for_existing_items_in_admitted_subset(self) -> None:
        selected = [
            SimpleNamespace(lemma="alpha", language_pair="en-ja"),
            SimpleNamespace(lemma="beta", language_pair="en-ja"),
            SimpleNamespace(lemma="gamma", language_pair="en-ja"),
        ]
        existing = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
            ),
            version=1,
        )
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                existing,
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=2,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        self.assertEqual(len(store.items), 2)
        self.assertEqual(report.admitted_count, 2)
        self.assertEqual(report.inserted_count, 1)
        self.assertEqual(report.updated_count, 1)

    def test_existing_item_state_is_preserved_on_reinitialize(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.75,
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.60,
            ),
        ]
        existing = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    confidence=0.42,
                    stability=3.0,
                    difficulty=0.25,
                    last_seen="2026-02-07T10:00:00Z",
                    next_due="2026-02-14T10:00:00Z",
                    exposures=9,
                ),
            ),
            version=1,
        )

        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                existing,
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=2,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        by_lemma = {item.lemma: item for item in store.items}
        self.assertEqual(report.updated_count, 1)
        self.assertAlmostEqual(by_lemma["alpha"].confidence or 0.0, 0.42, places=6)
        self.assertAlmostEqual(by_lemma["alpha"].stability or 0.0, 3.0, places=6)
        self.assertAlmostEqual(by_lemma["alpha"].difficulty or 0.0, 0.25, places=6)
        self.assertEqual(by_lemma["alpha"].exposures, 9)

    def test_persists_admission_weight_as_confidence_and_reports_profile(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                base_weight=0.9,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.9,
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                base_weight=0.8,
                pos="動詞-一般",
                pos_bucket="verb",
                pos_weight=0.7,
                admission_weight=0.56,
            ),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=2,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        by_lemma = {item.lemma: item for item in store.items}
        self.assertAlmostEqual(by_lemma["alpha"].confidence or 0.0, 0.9, places=6)
        self.assertAlmostEqual(by_lemma["beta"].confidence or 0.0, 0.56, places=6)
        self.assertIn("noun", report.admission_weight_profile)
        self.assertIn("verb", report.admission_weight_profile)
        self.assertEqual(report.initial_active_weight_preview[0]["lemma"], "alpha")

    def test_profile_bootstrap_reranks_by_challenge_fit(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                base_weight=0.75,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.75,
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                base_weight=0.70,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.70,
            ),
            SimpleNamespace(
                lemma="gamma",
                language_pair="en-ja",
                base_weight=0.60,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.60,
            ),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=1,
                    language_pair="en-ja",
                    strategy="profile_bootstrap",
                    selection_policy_override="top_n",
                    profile_context={
                        "proficiency": {"self_reported_level": 0.35},
                        "difficulty_preferences": {
                            "target_challenge_center": 0.35,
                            "target_challenge_spread": 0.07,
                        },
                    },
                ),
            )

        self.assertEqual([item.lemma for item in store.items], ["beta"])
        self.assertEqual(report.initial_active_preview, ("beta",))
        self.assertEqual(report.selection_strategy, "profile_bootstrap")
        self.assertEqual(report.selector_version, "profile_bootstrap_v3")
        preview = report.profile_bootstrap_diagnostics["ranking_preview"][0]
        self.assertEqual(preview["lemma"], "beta")
        self.assertGreater(preview["rank_delta"], 0)
        self.assertIn("challenge_fit", preview["explanation"].lower())
        self.assertEqual(
            report.profile_bootstrap_diagnostics["profile_context"]["signal_sources"][
                "challenge_preference"
            ],
            "difficulty_preferences.target_challenge_center",
        )

    def test_profile_bootstrap_uses_topic_affinity_when_candidate_topics_exist(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                base_weight=0.72,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.72,
                metadata={"sense_topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                base_weight=0.78,
                pos="名詞-普通名詞-一般",
                pos_bucket="noun",
                pos_weight=1.0,
                admission_weight=0.78,
                metadata={"sense_topics": ["science"]},
            ),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=1,
                    language_pair="en-ja",
                    strategy="profile_bootstrap",
                    selection_policy_override="top_n",
                    profile_context={"interests": ["animals"]},
                ),
            )

        self.assertEqual([item.lemma for item in store.items], ["alpha"])
        preview = report.profile_bootstrap_diagnostics["ranking_preview"][0]
        self.assertEqual(preview["lemma"], "alpha")
        self.assertAlmostEqual(preview["signals"]["topic_affinity"] or 0.0, 1.0, places=6)
        self.assertIn("topic_affinity", preview["explanation"].lower())
        self.assertEqual(preview["signals"]["topic_affinity_source"], "topic_hint:animals")

    def test_frequency_bootstrap_uses_weighted_selector_for_live_admission(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="alpha",
                language_pair="en-ja",
                admission_weight=0.9,
                pos_bucket="noun",
            ),
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                admission_weight=0.6,
                pos_bucket="noun",
            ),
            SimpleNamespace(
                lemma="gamma",
                language_pair="en-ja",
                admission_weight=0.2,
                pos_bucket="noun",
            ),
        ]

        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=2,
                    language_pair="en-ja",
                    selection_seed=1,
                ),
            )

        self.assertEqual(report.selection_policy, "weighted_without_replacement")
        self.assertEqual(report.selection_seed, 1)
        self.assertEqual([item.lemma for item in store.items], ["alpha", "gamma"])
        self.assertEqual(report.initial_active_preview, ("alpha", "gamma"))

    def test_initialization_persists_selected_word_package(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="所",
                language_pair="en-ja",
                admission_weight=0.75,
                word_package={
                    "version": 1,
                    "language_tag": "ja",
                    "surface": "所",
                    "reading": "ところ",
                    "script_forms": {
                        "kanji": "所",
                        "kana": "ところ",
                        "romaji": "tokoro",
                    },
                    "source": {"provider": "freq-ja-bccwj"},
                },
            ),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=1,
                    language_pair="en-ja",
                    selection_policy_override="top_n",
                ),
            )

        self.assertEqual(report.admitted_count, 1)
        self.assertEqual(store.items[0].item_id, "en-ja:所")
        self.assertIsNotNone(store.items[0].word_package)
        self.assertEqual(store.items[0].word_package["reading"], "ところ")

    def test_run_rulegen_for_pair_passes_word_package_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-ja:所",
                        lemma="所",
                        language_pair="en-ja",
                        source_type="initial_set",
                        word_package={
                            "version": 1,
                            "language_tag": "ja",
                            "surface": "所",
                            "reading": "ところ",
                            "script_forms": {
                                "kanji": "所",
                                "kana": "ところ",
                                "romaji": "tokoro",
                            },
                            "source": {"provider": "freq-ja-bccwj"},
                        },
                    ),
                ),
                version=1,
            )
            with patch(
                "lexishift_core.helper.rulegen.run_rules_with_adapter", return_value=[]
            ) as run_rules:
                run_rulegen_for_pair(
                    paths=paths,
                    pair="en-ja",
                    store=store,
                    settings=None,
                    jmdict_path=Path("/tmp/JMdict_e"),
                    rulegen_config=RulegenConfig(language_pair="en-ja"),
                    initialize_if_empty=False,
                    persist_store=False,
                )

        run_rules.assert_called_once()
        request = run_rules.call_args.args[0]
        self.assertIn("所", request.word_packages_by_target)
        self.assertEqual(request.word_packages_by_target["所"]["reading"], "ところ")
        self.assertEqual(request.max_definitions_per_target, 3)
        self.assertIsNone(request.max_rules_per_target)
        self.assertAlmostEqual(request.semantic_demotion_scale, 1.0, places=6)
        self.assertTrue(request.scoring.pos_match.enabled)
        self.assertAlmostEqual(request.scoring.weights.pos_match, 0.1, places=6)
        self.assertFalse(request.reverse_check.enabled)


if __name__ == "__main__":
    unittest.main()
