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

from lexishift_core.helper_rulegen import (  # noqa: E402
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
        with patch("lexishift_core.helper_rulegen.build_seed_candidates", return_value=selected):
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
        with patch("lexishift_core.helper_rulegen.build_seed_candidates", return_value=selected):
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
        with patch("lexishift_core.helper_rulegen.build_seed_candidates", return_value=selected):
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


if __name__ == "__main__":
    unittest.main()
