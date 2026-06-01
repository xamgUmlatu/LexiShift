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


def _flatten_keys(node: object, prefix: str = "") -> set[str]:
    if not isinstance(node, dict):
        return set()
    keys: set[str] = set()
    for key, value in node.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        keys.add(dotted)
        keys.update(_flatten_keys(value, dotted))
    return keys


class TestGuiI18nCatalogs(unittest.TestCase):
    def test_gui_locale_catalog_shapes_match_english_catalog(self) -> None:
        en_catalog = _load(EN_PATH)
        en_keys = _flatten_keys(en_catalog)

        for locale, path in LOCALE_PATHS.items():
            catalog = _load(path)
            self.assertEqual(
                sorted(_flatten_keys(catalog)),
                sorted(en_keys),
                f"{locale} catalog keys differ from en",
            )

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
            "settings.helper_status",
            "settings.helper_connections",
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

    def test_learning_language_resource_catalogs_exist_in_all_gui_locales(self) -> None:
        en_catalog = _load(EN_PATH)
        required_sections = (
            "language_packs.learning_pairs",
            "language_packs.pair_setup",
        )

        for section_key in required_sections:
            en_section = _lookup(en_catalog, section_key)
            self.assertIsInstance(en_section, dict)
            for locale, path in LOCALE_PATHS.items():
                catalog = _load(path)
                section = _lookup(catalog, section_key)
                self.assertIsInstance(section, dict, f"{locale} missing {section_key}")
                self.assertEqual(
                    sorted(section.keys()),
                    sorted(en_section.keys()),
                    f"{locale} {section_key} keys differ from en",
                )


if __name__ == "__main__":
    unittest.main()
