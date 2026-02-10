from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.rulegen import (  # noqa: E402
    SetInitializationConfig,
    initialize_store_from_frequency_list_with_report,
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


if __name__ == "__main__":
    unittest.main()
