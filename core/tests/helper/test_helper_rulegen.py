from __future__ import annotations

import os
import json
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
    annotate_rules_with_srs_serving_metadata,
    initialize_store_from_frequency_list_with_report,
    load_target_word_packages_from_store,
    load_targets_from_store,
    run_rulegen_for_pair,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.use_cases.semantic_pack_install import DEFAULT_PACK_ID  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.rulegen.generation import RuleCandidate  # noqa: E402
from lexishift_core.rulegen.semantic_publication import (  # noqa: E402
    annotate_results_with_semantic_admission,
)
from lexishift_core.srs import SRS_LIFECYCLE_DISCARDED, SrsItem, SrsStore  # noqa: E402


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
                ),
            )

        self.assertEqual(len(store.items), 2)
        self.assertEqual(report.selected_count, 5)
        self.assertEqual(report.selected_unique_count, 5)
        self.assertEqual(report.admitted_count, 2)
        self.assertEqual(report.inserted_count, 2)
        self.assertEqual(report.updated_count, 0)
        self.assertEqual(
            tuple(report.selected_unique_lemmas),
            ("alpha", "beta", "gamma", "delta", "epsilon"),
        )
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
                ),
            )

        self.assertEqual(len(store.items), 3)
        self.assertEqual(report.selected_count, 4)
        self.assertEqual(report.selected_unique_count, 3)
        self.assertEqual(report.admitted_count, 3)
        self.assertEqual(report.inserted_count, 3)

    def test_blocked_lemmas_are_not_selected_for_initial_admission(self) -> None:
        selected = [
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
                    initial_active_count=2,
                    language_pair="en-ja",
                    blocked_lemmas=("alpha",),
                ),
            )

        self.assertEqual([item.lemma for item in store.items], ["beta", "gamma"])
        self.assertEqual(tuple(report.initial_active_preview), ("beta", "gamma"))
        self.assertEqual(tuple(report.blocked_lemmas), ("alpha",))

    def test_same_surface_dedupe_prefers_admissible_reading_row(self) -> None:
        suffix_package = {
            "version": 1,
            "language_tag": "ja",
            "surface": "的",
            "reading": "てき",
            "script_forms": {"kanji": "的", "kana": "てき", "romaji": "teki"},
            "source": {"provider": "freq-ja-bccwj"},
            "pos": "接尾辞-形状詞的",
            "pos_raw": "接尾辞-形状詞的",
        }
        noun_package = {
            "version": 1,
            "language_tag": "ja",
            "surface": "的",
            "reading": "まと",
            "script_forms": {"kanji": "的", "kana": "まと", "romaji": "mato"},
            "source": {"provider": "freq-ja-bccwj"},
            "pos": "名詞-普通名詞-一般",
            "pos_raw": "名詞-普通名詞-一般",
        }
        selected = [
            SimpleNamespace(
                lemma="的",
                language_pair="en-ja",
                base_weight=0.99,
                admission_weight=0.99,
                admission_suitability=0.02,
                pos="接尾辞-形状詞的",
                word_package=suffix_package,
            ),
            SimpleNamespace(
                lemma="的",
                language_pair="en-ja",
                base_weight=0.20,
                admission_weight=0.20,
                admission_suitability=1.0,
                pos="名詞-普通名詞-一般",
                word_package=noun_package,
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
                ),
            )

        self.assertEqual(report.selected_unique_count, 1)
        self.assertEqual(report.admitted_count, 1)
        self.assertEqual(store.items[0].lemma, "的")
        self.assertEqual(store.items[0].word_package["reading"], "まと")
        self.assertEqual(report.initial_active_weight_preview[0]["pos"], "名詞-普通名詞-一般")

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
                ),
            )

        by_lemma = {item.lemma: item for item in store.items}
        self.assertAlmostEqual(by_lemma["alpha"].confidence or 0.0, 0.9, places=6)
        self.assertAlmostEqual(by_lemma["beta"].confidence or 0.0, 0.56, places=6)
        self.assertIn("noun", report.admission_weight_profile)
        self.assertIn("verb", report.admission_weight_profile)
        self.assertEqual(report.initial_active_weight_preview[0]["lemma"], "alpha")

    def test_profile_bootstrap_uses_reserved_topic_lane_by_default(self) -> None:
        selected = [
            SimpleNamespace(
                lemma="animal-a",
                language_pair="en-ja",
                admission_weight=0.78,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="animal-b",
                language_pair="en-ja",
                admission_weight=0.76,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="animal-c",
                language_pair="en-ja",
                admission_weight=0.74,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(lemma="general-a", language_pair="en-ja", admission_weight=0.72),
            SimpleNamespace(lemma="general-b", language_pair="en-ja", admission_weight=0.70),
        ]
        with patch("lexishift_core.helper.rulegen.build_seed_candidates", return_value=selected):
            store, report = initialize_store_from_frequency_list_with_report(
                SrsStore(),
                config=SetInitializationConfig(
                    frequency_db=Path("/tmp/freq.sqlite"),
                    jmdict_path=Path("/tmp/JMdict_e"),
                    top_n=800,
                    initial_active_count=4,
                    language_pair="en-ja",
                    strategy="profile_bootstrap",
                    profile_context={"interests": ["animals"]},
                ),
            )

        self.assertEqual(report.selection_policy, "reserved_topic_lane")
        self.assertEqual(len(store.items), 4)
        self.assertEqual(
            tuple(report.initial_active_preview),
            ("animal-a", "animal-b", "general-a", "general-b"),
        )

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
                "lexishift_core.helper.rulegen.run_results_with_adapter", return_value=[]
            ) as run_results:
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

        run_results.assert_called_once()
        request = run_results.call_args.args[0]
        self.assertIn("所", request.word_packages_by_target)
        self.assertEqual(request.word_packages_by_target["所"]["reading"], "ところ")
        self.assertEqual(request.max_definitions_per_target, 3)
        self.assertIsNone(request.max_rules_per_target)
        self.assertAlmostEqual(request.semantic_demotion_scale, 1.0, places=6)
        self.assertTrue(request.scoring.pos_match.enabled)
        self.assertAlmostEqual(request.scoring.weights.pos_match, 0.1, places=6)
        self.assertFalse(request.reverse_check.enabled)

    def test_run_rulegen_for_pair_resolves_source_frequency_prior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            pack_root = paths.frequency_packs_dir / "freq-en-leipzig-default"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                paths.frequency_packs_dir,
                pack_id="freq-en-leipzig-default",
                pack_kind="frequency",
                provider="freq-en-leipzig-default",
                local_kind="file",
                build_mode="en_frequency_pipeline",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-de:Zeit",
                        lemma="Zeit",
                        language_pair="en-de",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            with patch(
                "lexishift_core.helper.rulegen.run_results_with_adapter", return_value=[]
            ) as run_results:
                run_rulegen_for_pair(
                    paths=paths,
                    pair="en-de",
                    store=store,
                    settings=None,
                    translation_dict_path=Path("/tmp/freedict-de-en.sqlite"),
                    rulegen_config=RulegenConfig(
                        language_pair="en-de",
                        enable_source_frequency_prior=True,
                    ),
                    initialize_if_empty=False,
                    persist_store=False,
                )

        request = run_results.call_args.args[0]
        self.assertTrue(request.enable_source_frequency_prior)
        self.assertEqual(request.source_frequency_db_path, artifact)

    def test_store_targets_and_packages_exclude_inactive_lifecycle_items(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    word_package={"surface": "alpha"},
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                    lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                    word_package={"surface": "beta"},
                ),
            ),
            version=1,
        )

        self.assertEqual(load_targets_from_store(store, pair="en-ja"), ["alpha"])
        self.assertEqual(
            load_targets_from_store(
                store,
                pair="en-ja",
                active_item_ids=("en-ja:alpha", "en-ja:beta"),
            ),
            ["alpha"],
        )
        packages = load_target_word_packages_from_store(
            store,
            pair="en-ja",
            active_item_ids=("en-ja:alpha", "en-ja:beta"),
        )

        self.assertEqual(tuple(packages), ("alpha",))

    def test_annotates_rules_with_srs_due_serving_metadata(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    stability=18.0,
                    difficulty=4.25,
                    last_seen="1999-12-31T00:00:00+00:00",
                    last_review="1999-12-31T12:00:00+00:00",
                    next_due="2000-01-01T00:00:00+00:00",
                    scheduler_state="review",
                    exposures=7,
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                    next_due="2099-01-01T00:00:00+00:00",
                    scheduler_state="review",
                ),
            ),
            version=1,
        )

        rules = annotate_rules_with_srs_serving_metadata(
            (
                VocabRule(source_phrase="one", replacement="alpha"),
                VocabRule(source_phrase="two", replacement="beta"),
                VocabRule(source_phrase="three", replacement="gamma"),
            ),
            store=store,
            pair="en-ja",
            active_item_ids=("en-ja:alpha", "en-ja:beta"),
        )

        alpha_srs = rules[0].metadata.rulegen["srs"]
        beta_srs = rules[1].metadata.rulegen["srs"]
        self.assertEqual(alpha_srs["item_id"], "en-ja:alpha")
        self.assertTrue(alpha_srs["in_due"])
        self.assertEqual(alpha_srs["stability"], 18.0)
        self.assertEqual(alpha_srs["difficulty"], 4.25)
        self.assertEqual(alpha_srs["last_seen"], "1999-12-31T00:00:00+00:00")
        self.assertEqual(alpha_srs["last_review"], "1999-12-31T12:00:00+00:00")
        self.assertEqual(alpha_srs["exposures"], 7)
        self.assertEqual(alpha_srs["review_count"], 0)
        self.assertEqual(beta_srs["item_id"], "en-ja:beta")
        self.assertFalse(beta_srs["in_due"])
        self.assertIsNone(rules[2].metadata)

    def test_rule_srs_metadata_excludes_inactive_lifecycle_items(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                    lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                ),
            ),
            version=1,
        )

        rules = annotate_rules_with_srs_serving_metadata(
            (
                VocabRule(source_phrase="one", replacement="alpha"),
                VocabRule(source_phrase="two", replacement="beta"),
            ),
            store=store,
            pair="en-ja",
            active_item_ids=("en-ja:alpha", "en-ja:beta"),
        )

        self.assertIsNotNone(rules[0].metadata)
        self.assertIsNone(rules[1].metadata)

    def test_run_rulegen_for_pair_can_upgrade_primary_rules_from_semantic_context_targets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-es:pelota",
                        lemma="pelota",
                        language_pair="en-es",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            primary_results = annotate_results_with_semantic_admission(
                [
                    _build_semantic_result(
                        source_phrase="ball",
                        replacement="pelota",
                        entry_ord=20,
                        sense_ord=0,
                    ),
                ]
            )
            context_results = annotate_results_with_semantic_admission(
                [
                    _build_semantic_result(
                        source_phrase="ball",
                        replacement="pelota",
                        entry_ord=20,
                        sense_ord=0,
                    ),
                    _build_semantic_result(
                        source_phrase="ball",
                        replacement="baile",
                        entry_ord=21,
                        sense_ord=0,
                    ),
                ]
            )
            with patch(
                "lexishift_core.helper.rulegen.run_results_with_adapter",
                side_effect=(primary_results, context_results),
            ) as run_results:
                _updated_store, output = run_rulegen_for_pair(
                    paths=paths,
                    pair="en-es",
                    store=store,
                    settings=None,
                    translation_dict_path=Path("/tmp/freedict-es-en.sqlite"),
                    rulegen_config=RulegenConfig(language_pair="en-es"),
                    initialize_if_empty=False,
                    persist_store=False,
                    semantic_context_targets=("pelota", "baile"),
                )

        self.assertEqual(run_results.call_count, 2)
        primary_request = run_results.call_args_list[0].args[0]
        context_request = run_results.call_args_list[1].args[0]
        self.assertEqual(tuple(primary_request.targets), ("pelota",))
        self.assertEqual(tuple(context_request.targets), ("pelota", "baile"))
        merged_admission = output.rules[0].metadata.semantic_admission
        assert isinstance(merged_admission, dict)
        self.assertEqual(merged_admission["status"], "ready")
        self.assertEqual(len(output.semantic_inventory["competition_sets"]), 1)
        competition_set = next(iter(output.semantic_inventory["competition_sets"].values()))
        self.assertEqual(competition_set["status"], "ready")

    def test_run_rulegen_for_pair_can_upgrade_primary_rules_from_installed_semantic_pack(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = build_helper_paths(root)
            pack_inventory = (
                paths.language_packs_dir
                / "en-es"
                / "semantic_packs"
                / DEFAULT_PACK_ID
                / "semantic_inventory.json"
            )
            pack_inventory.parent.mkdir(parents=True, exist_ok=True)
            pack_inventory.write_text(
                json.dumps(_build_reference_semantic_inventory(), ensure_ascii=False),
                encoding="utf-8",
            )
            store = SrsStore(
                items=(
                    SrsItem(
                        item_id="en-es:luz",
                        lemma="luz",
                        language_pair="en-es",
                        source_type="initial_set",
                    ),
                ),
                version=1,
            )
            primary_results = annotate_results_with_semantic_admission(
                [
                    _build_semantic_result(
                        source_phrase="light",
                        replacement="luz",
                        entry_ord=30,
                        sense_ord=0,
                    ),
                ]
            )
            with patch(
                "lexishift_core.helper.rulegen.run_results_with_adapter",
                return_value=primary_results,
            ) as run_results:
                _updated_store, output = run_rulegen_for_pair(
                    paths=paths,
                    pair="en-es",
                    store=store,
                    settings=None,
                    translation_dict_path=Path("/tmp/freedict-es-en.sqlite"),
                    rulegen_config=RulegenConfig(language_pair="en-es"),
                    initialize_if_empty=False,
                    persist_store=False,
                )

        self.assertEqual(run_results.call_count, 1)
        self.assertEqual(len(output.rules), 1)
        admission = output.rules[0].metadata.semantic_admission
        assert isinstance(admission, dict)
        self.assertEqual(admission["status"], "ready")
        self.assertEqual(admission["trigger_id"], "pack:trigger:light")
        self.assertIn("pack:competition:light:luz", output.semantic_inventory["competition_sets"])


def _build_semantic_result(
    *,
    source_phrase: str,
    replacement: str,
    entry_ord: int,
    sense_ord: int,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate=RuleCandidate(
            source_phrase=source_phrase,
            replacement=replacement,
            language_pair="en-es",
            source_dict="wiktionary_es_en",
            metadata={
                "sense_provenance": {
                    "entry_ord": entry_ord,
                    "sense_ord": sense_ord,
                    "gloss_ord": 0,
                    "sense_raw_glosses": (f"{replacement} sense",),
                },
                "gloss_provenance": {
                    "raw_gloss_text": f"{source_phrase} -> {replacement}",
                    "fragment_emitted_text": source_phrase,
                },
            },
        ),
        rule=VocabRule(
            source_phrase=source_phrase,
            replacement=replacement,
            metadata=RuleMetadata(language_pair="en-es"),
        ),
        confidence=0.9,
    )


def _build_reference_semantic_inventory() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "profile_id": "semantic_pack_builder",
        "generated_at": "2026-04-09T00:00:00Z",
        "capability": {},
        "triggers": {
            "pack:trigger:light": {
                "trigger_id": "pack:trigger:light",
                "source_phrase": "light",
            }
        },
        "senses": {
            "pack:sense:luz": {
                "sense_id": "pack:sense:luz",
                "trigger_id": "pack:trigger:light",
                "target_lemma": "luz",
            }
        },
        "competition_sets": {
            "pack:competition:light:luz": {
                "competition_set_id": "pack:competition:light:luz",
                "trigger_id": "pack:trigger:light",
                "status": "ready",
                "active_sense_id": "pack:sense:luz",
                "shadow_sense_ids": [],
            }
        },
        "phrase_sets": {},
    }


if __name__ == "__main__":
    unittest.main()
