from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REPO_ROOT = os.path.dirname(CORE_ROOT)
SCRIPTS_TESTING = os.path.join(REPO_ROOT, "scripts", "testing")
for candidate in (CORE_ROOT, SCRIPTS_TESTING):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from srs_journey_harness_support import create_pair_resources  # noqa: E402
from srs_quality_harness_support import build_pair_resources  # noqa: E402


class TestSrsHarnessResourceNormalization(unittest.TestCase):
    def test_quality_harness_en_de_writes_sqlite_translation_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            build_pair_resources(paths, pair="en-de")

            translation_path = paths.language_packs_dir / "freedict-de-en.sqlite"
            self.assertTrue(translation_path.exists())
            self.assertFalse((paths.language_packs_dir / "deu-eng.tei").exists())
            with sqlite3.connect(translation_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            self.assertEqual(count, 70)

    def test_journey_harness_en_es_uses_sqlite_forward_and_reverse_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            resources = create_pair_resources(paths, pair="en-es")

            forward_path = resources["translation_dict_path"]
            reverse_path = resources["reverse_translation_dict_path"]
            self.assertIsInstance(forward_path, Path)
            self.assertIsInstance(reverse_path, Path)
            self.assertEqual(forward_path.suffix, ".sqlite")
            self.assertEqual(reverse_path.suffix, ".sqlite")
            self.assertFalse((paths.language_packs_dir / "eng-spa.tei").exists())
            with sqlite3.connect(forward_path) as conn:
                forward_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            with sqlite3.connect(reverse_path) as conn:
                reverse_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            self.assertEqual(forward_count, 7)
            self.assertEqual(reverse_count, 7)


if __name__ == "__main__":
    unittest.main()
