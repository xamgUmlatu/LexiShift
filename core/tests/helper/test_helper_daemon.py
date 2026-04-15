from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REPO_ROOT = os.path.dirname(CORE_ROOT)
GUI_SRC = os.path.join(REPO_ROOT, "apps", "gui", "src")
for candidate in (CORE_ROOT, GUI_SRC):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from helper_daemon import DaemonConfig, _build_job_config, _supported_pairs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import SrsItem, SrsStore, save_srs_store  # noqa: E402


class TestHelperDaemon(unittest.TestCase):
    def test_supported_pairs_include_en_de_and_en_es(self) -> None:
        pairs = _supported_pairs()
        self.assertIn("en-ja", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("en-es", pairs)

    def test_build_job_config_requires_translation_dict_for_en_ja_rulegen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-ja", paths, config))

            translation_dict_path = paths.language_packs_dir / "wiktionary-ja-en.sqlite"
            translation_dict_path.parent.mkdir(parents=True, exist_ok=True)
            translation_dict_path.write_bytes(b"SQLite format 3\x00")

            job = _build_job_config("en-ja", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-ja")
            self.assertEqual(job.translation_dict_path, translation_dict_path)

    def test_build_job_config_skips_empty_store_en_ja_without_jmdict_seed_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            translation_dict_path = paths.language_packs_dir / "wiktionary-ja-en.sqlite"
            translation_dict_path.parent.mkdir(parents=True, exist_ok=True)
            translation_dict_path.write_bytes(b"SQLite format 3\x00")
            frequency_path = paths.frequency_packs_dir / "freq-ja-bccwj.sqlite"
            frequency_path.parent.mkdir(parents=True, exist_ok=True)
            frequency_path.write_bytes(b"SQLite format 3\x00")

            self.assertIsNone(_build_job_config("en-ja", paths, config))

    def test_build_job_config_allows_existing_en_ja_store_without_jmdict_seed_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            translation_dict_path = paths.language_packs_dir / "wiktionary-ja-en.sqlite"
            translation_dict_path.parent.mkdir(parents=True, exist_ok=True)
            translation_dict_path.write_bytes(b"SQLite format 3\x00")
            frequency_path = paths.frequency_packs_dir / "freq-ja-bccwj.sqlite"
            frequency_path.parent.mkdir(parents=True, exist_ok=True)
            frequency_path.write_bytes(b"SQLite format 3\x00")
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-ja:alpha",
                            lemma="alpha",
                            language_pair="en-ja",
                            source_type="initial_set",
                        ),
                    ),
                    version=1,
                ),
                paths.srs_store_path,
            )

            job = _build_job_config("en-ja", paths, config)
            self.assertIsNotNone(job)
            assert job is not None
            self.assertEqual(job.translation_dict_path, translation_dict_path)
            self.assertTrue(str(job.jmdict_path).endswith("JMdict_e"))

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
            self.assertEqual(job.translation_dict_path, freedict_path)
            self.assertIsNone(job.jmdict_path)

    def test_build_job_config_requires_freedict_for_en_es(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("en-es", paths, config))

            freedict_path = paths.language_packs_dir / "spa-eng.tei"
            freedict_path.parent.mkdir(parents=True, exist_ok=True)
            freedict_path.write_text("<TEI/>", encoding="utf-8")

            job = _build_job_config("en-es", paths, config)
            self.assertIsNotNone(job)
            self.assertEqual(job.pair, "en-es")
            self.assertEqual(job.translation_dict_path, freedict_path)
            self.assertIsNone(job.jmdict_path)

    def test_build_job_config_skips_pairs_without_rulegen_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            config = DaemonConfig()
            self.assertIsNone(_build_job_config("de-en", paths, config))


if __name__ == "__main__":
    unittest.main()
