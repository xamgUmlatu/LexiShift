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


if __name__ == "__main__":
    unittest.main()
