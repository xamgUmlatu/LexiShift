from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
CORE_ROOT = REPO_ROOT / "core"
for path in (GUI_SRC, CORE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


class TestGuiImportContract(unittest.TestCase):
    def test_language_packs_reexports_pack_catalogs(self) -> None:
        language_packs_catalog = importlib.import_module("language_packs_catalog")
        language_packs = importlib.import_module("language_packs")

        self.assertIs(language_packs.LANGUAGE_PACKS, language_packs_catalog.LANGUAGE_PACKS)
        self.assertIs(language_packs.FREQUENCY_PACKS, language_packs_catalog.FREQUENCY_PACKS)
        self.assertIs(language_packs.EMBEDDING_PACKS, language_packs_catalog.EMBEDDING_PACKS)
        self.assertIs(
            language_packs.CROSS_EMBEDDING_PACKS,
            language_packs_catalog.CROSS_EMBEDDING_PACKS,
        )

    def test_settings_language_packs_import_succeeds(self) -> None:
        sys.modules.pop("settings_language_packs", None)
        module = importlib.import_module("settings_language_packs")

        self.assertTrue(hasattr(module, "LanguagePackPanel"))

    def test_language_pack_catalog_includes_ja_kaikki_pack(self) -> None:
        language_packs_catalog = importlib.import_module("language_packs_catalog")

        packs = {pack.pack_id: pack for pack in language_packs_catalog.LANGUAGE_PACKS}
        pack = packs.get("wiktionary-ja-en")

        self.assertIsNotNone(pack)
        self.assertEqual(pack.sqlite_filename, "wiktionary-ja-en.sqlite")
        self.assertEqual(pack.build_mode, "kaikki_glosses_to_sqlite")
        self.assertEqual(pack.source_lang_code, "ja")
        self.assertEqual(pack.gloss_language, "en")

    def test_frequency_topic_enrichment_config_uses_companion_sqlite_when_present(self) -> None:
        language_packs_catalog = importlib.import_module("language_packs_catalog")

        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            (language_packs_dir / "wiktionary-ja-en.sqlite").write_text("", encoding="utf-8")
            (language_packs_dir / "wiktionary-es-en.sqlite").write_text("", encoding="utf-8")

            ja_config = language_packs_catalog._frequency_topic_enrichment_config(  # type: ignore[attr-defined]
                "freq-ja-bccwj",
                language_packs_dir=language_packs_dir,
            )
            es_config = language_packs_catalog._frequency_topic_enrichment_config(  # type: ignore[attr-defined]
                "freq-es-cde",
                language_packs_dir=language_packs_dir,
            )
            en_config = language_packs_catalog._frequency_topic_enrichment_config(  # type: ignore[attr-defined]
                "freq-en-coca",
                language_packs_dir=language_packs_dir,
            )

        self.assertIsNotNone(ja_config)
        self.assertEqual(ja_config.source_provider, "wiktionary-ja-en")
        self.assertEqual(ja_config.source_sqlite_path.name, "wiktionary-ja-en.sqlite")
        self.assertIsNotNone(es_config)
        self.assertEqual(es_config.source_provider, "wiktionary-es-en")
        self.assertEqual(es_config.source_sqlite_path.name, "wiktionary-es-en.sqlite")
        self.assertIsNone(en_config)


if __name__ == "__main__":
    unittest.main()
