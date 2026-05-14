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
    annotate_rules_with_srs_serving_metadata,
    initialize_store_from_frequency_list_with_report,
    run_rulegen_for_pair,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.rulegen.generation import RuleCandidate  # noqa: E402
from lexishift_core.rulegen.semantic_publication import (  # noqa: E402
    annotate_results_with_semantic_admission,
)
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

    def test_annotates_rules_with_srs_due_serving_metadata(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    next_due="2000-01-01T00:00:00+00:00",
                    scheduler_state="review",
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
        self.assertEqual(beta_srs["item_id"], "en-ja:beta")
        self.assertFalse(beta_srs["in_due"])
        self.assertIsNone(rules[2].metadata)

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


if __name__ == "__main__":
    unittest.main()
