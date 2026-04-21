from __future__ import annotations

import json
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
I18N_ROOT = PROJECT_ROOT / "apps" / "gui" / "resources" / "i18n"
EN_PATH = I18N_ROOT / "en.json"
LOCALE_PATHS = {
    "de": I18N_ROOT / "de.json",
    "ja": I18N_ROOT / "ja.json",
    "zh": I18N_ROOT / "zh.json",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lookup(catalog: dict, dotted_key: str):
    node = catalog
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class TestGuiI18nCatalogs(unittest.TestCase):
    def test_browser_connections_catalog_exists_in_all_gui_locales(self) -> None:
        en_catalog = _load(EN_PATH)
        en_section = _lookup(en_catalog, "dialogs.browser_connections")
        self.assertIsInstance(en_section, dict)

        for locale, path in LOCALE_PATHS.items():
            catalog = _load(path)
            section = _lookup(catalog, "dialogs.browser_connections")
            self.assertIsInstance(section, dict, f"{locale} missing dialogs.browser_connections")
            self.assertEqual(
                sorted(section.keys()),
                sorted(en_section.keys()),
                f"{locale} browser_connections keys differ from en",
            )

    def test_browser_connection_menu_and_settings_keys_exist_in_all_gui_locales(self) -> None:
        required_string_keys = (
            "menu.browser_connections",
            "menu.install_helper",
            "menu.manage_browser_connections",
            "menu.repair_browser_connections",
            "settings.helper_status",
            "settings.helper_connections",
            "settings.helper_install",
            "settings.helper_manage_connections",
            "settings.helper_repair_connections",
            "settings.helper_status_installed",
            "settings.helper_status_needs_repair",
            "settings.helper_status_missing",
            "language_packs.language_description",
        )

        for locale, path in LOCALE_PATHS.items():
            catalog = _load(path)
            for key in required_string_keys:
                value = _lookup(catalog, key)
                self.assertIsInstance(value, str, f"{locale} missing {key}")
                self.assertTrue(value.strip(), f"{locale} has empty {key}")


if __name__ == "__main__":
    unittest.main()
