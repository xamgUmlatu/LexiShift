from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = os.path.dirname(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(CORE_ROOT)
GUI_SRC = os.path.join(REPO_ROOT, "apps", "gui", "src")
for candidate in (CORE_ROOT, GUI_SRC):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from helper_daemon import DaemonConfig, _build_job_config, _supported_pairs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


class TestHelperDaemon(unittest.TestCase):
    def test_supported_pairs_include_en_de(self) -> None:
        pairs = _supported_pairs()
        self.assertIn("en-ja", pairs)
        self.assertIn("en-de", pairs)

    def test_build_job_config_requires_jmdict_for_en_ja(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-ja", paths, config))

            jmdict_path = paths.language_packs_dir / "JMdict_e"
            jmdict_path.parent.mkdir(parents=True, exist_ok=True)
            jmdict_path.write_text("<JMdict/>", encoding="utf-8")

            job = _build_job_config("en-ja", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-ja")
            self.assertEqual(job.jmdict_path, jmdict_path)

    def test_build_job_config_requires_freedict_for_en_de(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-de", paths, config))

            freedict_path = paths.language_packs_dir / "deu-eng.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("en-de", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-de")
            self.assertEqual(job.freedict_de_en_path, freedict_path)
            self.assertIsNone(job.jmdict_path)

    def test_build_job_config_skips_pairs_without_rulegen_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("de-en", paths, config))


if __name__ == "__main__":
    unittest.main()
