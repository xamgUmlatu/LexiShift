from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper_engine import reset_srs_data  # noqa: E402
from lexishift_core.helper_paths import HelperPaths, build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsItem, SrsStore, load_srs_store, save_srs_store  # noqa: E402


def _seed_store_and_outputs(root: Path) -> HelperPaths:
    paths = build_helper_paths(root)
    save_srs_store(
        SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="seed",
                ),
                SrsItem(
                    item_id="en-en:beta",
                    lemma="beta",
                    language_pair="en-en",
                    source_type="seed",
                ),
            ),
            version=1,
        ),
        paths.srs_store_path,
    )
    paths.snapshot_path("en-ja").write_text("{}", encoding="utf-8")
    paths.snapshot_path("en-en").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-ja").write_text("{}", encoding="utf-8")
    paths.ruleset_path("en-en").write_text("{}", encoding="utf-8")
    return paths


class TestHelperEngineReset(unittest.TestCase):
    def test_reset_pair_removes_only_that_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_store_and_outputs(Path(tmp))
            result = reset_srs_data(paths, pair="en-ja")

            store = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(store.items), 1)
            self.assertEqual(store.items[0].item_id, "en-en:beta")

            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertTrue(paths.snapshot_path("en-en").exists())
            self.assertTrue(paths.ruleset_path("en-en").exists())

            self.assertEqual(result["pair"], "en-ja")
            self.assertEqual(result["removed_items"], 1)
            self.assertEqual(result["remaining_items"], 1)
            self.assertEqual(result["removed_snapshots"], 1)
            self.assertEqual(result["removed_rulesets"], 1)

    def test_reset_all_removes_all_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _seed_store_and_outputs(Path(tmp))
            result = reset_srs_data(paths)

            store = load_srs_store(paths.srs_store_path)
            self.assertEqual(len(store.items), 0)

            self.assertFalse(paths.snapshot_path("en-ja").exists())
            self.assertFalse(paths.snapshot_path("en-en").exists())
            self.assertFalse(paths.ruleset_path("en-ja").exists())
            self.assertFalse(paths.ruleset_path("en-en").exists())

            self.assertEqual(result["pair"], "all")
            self.assertEqual(result["removed_items"], 2)
            self.assertEqual(result["remaining_items"], 0)
            self.assertEqual(result["removed_snapshots"], 2)
            self.assertEqual(result["removed_rulesets"], 2)


if __name__ == "__main__":
    unittest.main()
