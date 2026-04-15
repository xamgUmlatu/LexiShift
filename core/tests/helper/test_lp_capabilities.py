from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_freedict_de_en_path,
    default_freedict_reverse_path,
    default_reverse_translation_dictionary_path,
    default_translation_dictionary_path,
    known_pairs,
    selectable_srs_pairs,
    supported_rulegen_pairs,
)


class TestLpCapabilities(unittest.TestCase):
    def test_supported_rulegen_pairs_use_capability_registry(self) -> None:
        pairs = supported_rulegen_pairs()
        self.assertEqual(pairs, ("en-ja", "en-de", "en-es", "es-en"))

    def test_srs_selectable_pairs_include_current_gui_pairs(self) -> None:
        pairs = selectable_srs_pairs()
        self.assertIn("en-ja", pairs)
        self.assertIn("en-en", pairs)
        self.assertIn("ja-ja", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("de-de", pairs)
        self.assertIn("de-en", pairs)
        self.assertIn("en-es", pairs)
        self.assertIn("es-en", pairs)
        self.assertIn("es-es", pairs)

    def test_known_pairs_contains_all_declared_capabilities(self) -> None:
        pairs = known_pairs()
        self.assertIn("en-zh", pairs)
        self.assertIn("en-de", pairs)
        self.assertIn("de-en", pairs)
        self.assertIn("en-es", pairs)
        self.assertIn("es-en", pairs)
        self.assertIn("es-es", pairs)

    def test_en_es_default_dictionary_prefers_kaikki_sqlite_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_freedict_de_en_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("wiktionary-es-en.sqlite"))

    def test_en_es_default_dictionary_uses_existing_kaikki_sqlite_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            target = language_packs_dir / "wiktionary-es-en.sqlite"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"SQLite format 3\x00")
            resolved = default_freedict_de_en_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, target)

    def test_translation_dictionary_alias_matches_legacy_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            legacy = default_freedict_de_en_path("en-es", language_packs_dir=language_packs_dir)
            alias = default_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(alias, legacy)

    def test_en_ja_default_dictionary_prefers_kaikki_sqlite_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_translation_dictionary_path(
                "en-ja",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("wiktionary-ja-en.sqlite"))

    def test_en_ja_default_dictionary_falls_back_to_existing_jmdict_when_kaikki_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            target = language_packs_dir / "JMdict_e"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("<JMdict/>", encoding="utf-8")
            resolved = default_translation_dictionary_path(
                "en-ja",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, target)

    def test_en_ja_default_dictionary_prefers_kaikki_when_both_sources_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            jmdict_target = language_packs_dir / "JMdict_e"
            kaikki_target = language_packs_dir / "wiktionary-ja-en.sqlite"
            jmdict_target.parent.mkdir(parents=True, exist_ok=True)
            jmdict_target.write_text("<JMdict/>", encoding="utf-8")
            kaikki_target.write_bytes(b"SQLite format 3\x00")
            resolved = default_translation_dictionary_path(
                "en-ja",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, kaikki_target)

    def test_en_es_reverse_dictionary_prefers_kaikki_sqlite_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_freedict_reverse_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("wiktionary-en-es.sqlite"))

    def test_en_es_reverse_dictionary_uses_existing_kaikki_sqlite_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            target = language_packs_dir / "wiktionary-en-es.sqlite"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"SQLite format 3\x00")
            resolved = default_freedict_reverse_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, target)

    def test_reverse_translation_dictionary_alias_matches_legacy_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            legacy = default_freedict_reverse_path("en-es", language_packs_dir=language_packs_dir)
            alias = default_reverse_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(alias, legacy)


if __name__ == "__main__":
    unittest.main()
