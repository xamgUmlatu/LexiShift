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
    default_frequency_db_path,
    default_reverse_translation_dictionary_path,
    default_translation_dictionary_path,
    known_pairs,
    pair_requirements,
    resolve_pair_capability,
    selectable_srs_pairs,
    supported_rulegen_pairs,
)
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402


class TestLpCapabilities(unittest.TestCase):
    def test_supported_rulegen_pairs_use_capability_registry(self) -> None:
        pairs = supported_rulegen_pairs()
        self.assertEqual(pairs, ("en-ja", "de-en", "en-de", "en-es", "es-en"))

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
            resolved = default_translation_dictionary_path(
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
            resolved = default_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, target)

    def test_en_es_reverse_dictionary_prefers_kaikki_sqlite_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_reverse_translation_dictionary_path(
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
            resolved = default_reverse_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, target)

    def test_translation_dictionary_requirement_uses_generic_capability_flag(self) -> None:
        capability = resolve_pair_capability("en-es")

        self.assertTrue(capability.requires_translation_dictionary_for_rulegen)

    def test_pair_requirements_expose_generic_translation_flag(self) -> None:
        requirements = pair_requirements("en-es")

        self.assertTrue(requirements["requires_translation_dictionary_for_rulegen"])

    def test_en_de_default_reverse_dictionary_uses_english_headword_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_reverse_translation_dictionary_path(
                "en-de",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("freedict-en-de.sqlite"))

    def test_de_en_default_dictionary_uses_english_headword_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("freedict-en-de.sqlite"))

    def test_de_en_default_dictionary_prefers_manifest_backed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            pack_root = language_packs_dir / "freedict-en-de"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "freedict-en-de.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="freedict-en-de",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact,
                source_filename="freedict-eng-deu-1.9-fd1.src.tar.xz",
                sqlite_filename="freedict-en-de.sqlite",
                required_files=("eng-deu.tei",),
            )
            resolved = default_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_de_en_default_reverse_dictionary_uses_german_headword_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_reverse_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertIsNotNone(resolved)
        self.assertTrue(str(resolved).endswith("freedict-de-en.sqlite"))

    def test_de_en_default_reverse_dictionary_prefers_manifest_backed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            pack_root = language_packs_dir / "freedict-de-en"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "freedict-de-en.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="freedict-de-en",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact,
                source_filename="freedict-deu-eng-1.9-fd1.src.tar.xz",
                sqlite_filename="freedict-de-en.sqlite",
                required_files=("deu-eng.tei",),
            )
            resolved = default_reverse_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_en_en_default_frequency_db_prefers_manifest_backed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            pack_root = frequency_packs_dir / "freq-en-coca"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "freq-en-coca.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-en-coca",
                pack_kind="frequency",
                provider="wordfrequency",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                source_filename="lemmas_60k.txt",
                sqlite_filename="freq-en-coca.sqlite",
            )
            resolved = default_frequency_db_path(
                "en-en",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_de_de_default_frequency_db_prefers_manifest_backed_fallback_pack_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            pack_root = frequency_packs_dir / "freq-de-default"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "freq-de-default.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-de-default",
                pack_kind="frequency",
                provider="freq-de-default",
                local_kind="file",
                build_mode="de_frequency_pipeline",
                artifact_path=artifact,
                sqlite_filename="freq-de-default.sqlite",
            )
            resolved = default_frequency_db_path(
                "de-de",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, artifact)


if __name__ == "__main__":
    unittest.main()
