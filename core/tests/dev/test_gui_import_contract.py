from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
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
        self.assertIs(
            language_packs.build_pack_catalogs, language_packs_catalog.build_pack_catalogs
        )

    def test_settings_language_packs_import_succeeds(self) -> None:
        sys.modules.pop("settings_language_packs", None)
        module = importlib.import_module("settings_language_packs")

        self.assertTrue(hasattr(module, "LanguagePackPanel"))


if __name__ == "__main__":
    unittest.main()
