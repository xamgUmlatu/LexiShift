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
    default_japanese_lesson_vocabulary_path,
    default_jmdict_path,
    default_jlpt_vocabulary_path,
    default_kanjivg_path,
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

    def test_en_es_default_dictionary_finds_manifestless_pack_main_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            target = language_packs_dir / "wiktionary-es-en" / "main.sqlite"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"SQLite format 3\x00")

            resolved = default_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, target)

    def test_en_es_manifestless_kaikki_still_beats_manifest_backed_freedict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            wiktionary_artifact = language_packs_dir / "wiktionary-es-en" / "main.sqlite"
            wiktionary_artifact.parent.mkdir(parents=True, exist_ok=True)
            wiktionary_artifact.write_bytes(b"SQLite format 3\x00")
            freedict_artifact = language_packs_dir / "freedict-es-en" / "main.sqlite"
            freedict_artifact.parent.mkdir(parents=True, exist_ok=True)
            freedict_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="freedict-es-en",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=freedict_artifact,
                source_filename="freedict-spa-eng-0.3.1.src.tar.xz",
                sqlite_filename="main.sqlite",
                required_files=("spa-eng.tei",),
            )

            resolved = default_translation_dictionary_path(
                "en-es",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, wiktionary_artifact)

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

    def test_en_ja_default_jmdict_prefers_managed_installed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            artifact = language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("<JMdict/>", encoding="utf-8")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="jmdict-ja-en",
                pack_kind="language",
                provider="jmdict",
                local_kind="file",
                build_mode="download_only",
                artifact_path=artifact,
                source_filename="JMdict_e.gz",
                required_files=("JMdict_e",),
            )

            resolved = default_jmdict_path("en-ja", language_packs_dir=language_packs_dir)

        self.assertEqual(resolved, artifact)

    def test_en_ja_default_jmdict_finds_manifestless_managed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            artifact = language_packs_dir / "jmdict-ja-en" / "JMdict_e"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("<JMdict/>", encoding="utf-8")

            resolved = default_jmdict_path("en-ja", language_packs_dir=language_packs_dir)

        self.assertEqual(resolved, artifact)

    def test_en_ja_default_jmdict_keeps_legacy_root_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            resolved = default_jmdict_path("en-ja", language_packs_dir=language_packs_dir)

        self.assertEqual(resolved, language_packs_dir / "JMdict_e")

    def test_en_ja_default_kanjivg_prefers_managed_installed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            artifact = language_packs_dir / "kanjivg-ja" / "kanjivg-20250816.xml"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("<kanjivg/>", encoding="utf-8")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="kanjivg-ja",
                pack_kind="language",
                provider="kanjivg",
                local_kind="dir",
                build_mode="download_only",
                artifact_path=artifact,
                source_filename="kanjivg-20250816.xml.gz",
                required_files=("kanjivg-20250816.xml",),
            )

            resolved = default_kanjivg_path("en-ja", language_packs_dir=language_packs_dir)

        self.assertEqual(resolved, artifact)

    def test_en_ja_default_jlpt_vocab_prefers_managed_installed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            artifact = language_packs_dir / "jlpt-tanos-vocab-ja" / "JLPT_vocab_ALL.csv"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("Kanji,Reading,Level\n猫,ねこ,5\n", encoding="utf-8")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="jlpt-tanos-vocab-ja",
                pack_kind="language",
                provider="tanos",
                local_kind="file",
                build_mode="download_only",
                artifact_path=artifact,
                source_filename="JLPT_vocab_ALL.csv",
            )

            resolved = default_jlpt_vocabulary_path(
                "en-ja",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, artifact)

    def test_en_ja_default_lesson_vocab_prefers_managed_installed_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            artifact = language_packs_dir / "sbsjapanese1-ja"
            (artifact / "EPUB").mkdir(parents=True, exist_ok=True)
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="sbsjapanese1-ja",
                pack_kind="language",
                provider="utsa_pressbooks",
                local_kind="dir",
                build_mode="download_only",
                artifact_path=artifact,
                source_filename="sbsjapanese1.zip",
            )

            resolved = default_japanese_lesson_vocabulary_path(
                "en-ja",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, artifact)

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
            artifact = pack_root / "main.sqlite"
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
                sqlite_filename="main.sqlite",
                required_files=("eng-deu.tei",),
            )
            resolved = default_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_de_en_default_dictionary_finds_legacy_file_inside_expected_pack_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            pack_root = language_packs_dir / "freedict-en-de"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "eng-deu.tei"
            artifact.write_text("<TEI/>", encoding="utf-8")

            resolved = default_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, artifact)

    def test_de_en_default_dictionary_ignores_unrelated_nested_legacy_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            unrelated = language_packs_dir / "scratch" / "eng-deu.tei"
            unrelated.parent.mkdir(parents=True, exist_ok=True)
            unrelated.write_text("<TEI/>", encoding="utf-8")

            resolved = default_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )

        self.assertEqual(resolved, language_packs_dir / "freedict-en-de.sqlite")

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
            artifact = pack_root / "main.sqlite"
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
                sqlite_filename="main.sqlite",
                required_files=("deu-eng.tei",),
            )
            resolved = default_reverse_translation_dictionary_path(
                "de-en",
                language_packs_dir=language_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_en_en_default_frequency_db_prefers_manifest_backed_leipzig_pack_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            pack_root = frequency_packs_dir / "freq-en-leipzig-default"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-en-leipzig-default",
                pack_kind="frequency",
                provider="leipzig wortschatz",
                local_kind="file",
                build_mode="en_frequency_pipeline",
                artifact_path=artifact,
                source_filename="eng_news_2025_1M.tar.gz",
                sqlite_filename="main.sqlite",
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
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-de-default",
                pack_kind="frequency",
                provider="freq-de-default",
                local_kind="file",
                build_mode="de_frequency_pipeline",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )
            resolved = default_frequency_db_path(
                "de-de",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, artifact)

    def test_en_en_default_frequency_db_falls_back_to_legacy_filename_without_manifest(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            resolved = default_frequency_db_path(
                "en-en",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, frequency_packs_dir / "freq-en-leipzig-default.sqlite")

    def test_en_en_default_frequency_db_uses_coca_fallback_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            fallback = frequency_packs_dir / "freq-en-coca.sqlite"
            fallback.write_bytes(b"SQLite format 3\x00")
            resolved = default_frequency_db_path(
                "en-en",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, fallback)

    def test_en_es_default_frequency_db_uses_spalex_candidate_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            resolved = default_frequency_db_path(
                "en-es",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, frequency_packs_dir / "freq-es-spalex-v1.sqlite")

    def test_en_es_default_frequency_db_ignores_installed_legacy_cde(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frequency_packs_dir = Path(tmp)
            cde_pack_root = frequency_packs_dir / "freq-es-cde"
            cde_pack_root.mkdir(parents=True, exist_ok=True)
            cde_artifact = cde_pack_root / "main.sqlite"
            cde_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_packs_dir,
                pack_id="freq-es-cde",
                pack_kind="frequency",
                provider="freq-es-cde",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=cde_artifact,
                sqlite_filename="main.sqlite",
            )
            resolved = default_frequency_db_path(
                "en-es",
                frequency_packs_dir=frequency_packs_dir,
            )
        self.assertEqual(resolved, frequency_packs_dir / "freq-es-spalex-v1.sqlite")


if __name__ == "__main__":
    unittest.main()
