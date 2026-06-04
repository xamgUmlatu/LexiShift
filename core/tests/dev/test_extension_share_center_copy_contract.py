from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPTIONS_HTML = PROJECT_ROOT / "apps/chrome-extension/options.html"
EN_MESSAGES = PROJECT_ROOT / "apps/chrome-extension/_locales/en/messages.json"
LOCALE_FILES = {
    "en": EN_MESSAGES,
    "de": PROJECT_ROOT / "apps/chrome-extension/_locales/de/messages.json",
    "ja": PROJECT_ROOT / "apps/chrome-extension/_locales/ja/messages.json",
    "zh": PROJECT_ROOT / "apps/chrome-extension/_locales/zh/messages.json",
}


class TestExtensionShareCenterCopyContract(unittest.TestCase):
    def test_options_html_wires_share_center_compatibility_note(self) -> None:
        html = OPTIONS_HTML.read_text(encoding="utf-8")

        self.assertIn('data-i18n="share_center_compatibility_note"', html)
        self.assertIn('data-i18n="share_center_mode_full_hint"', html)
        self.assertIn('data-i18n="share_center_target_profile_settings_hint"', html)

    def test_locale_catalogs_define_share_center_compatibility_copy(self) -> None:
        required_keys = (
            "hint_share_center_export_mode",
            "share_center_mode_full_hint",
            "share_center_target_profile_settings_hint",
            "share_center_hint_ready_full_export",
            "share_center_compatibility_note",
        )

        for locale, path in LOCALE_FILES.items():
            with self.subTest(locale=locale):
                messages = json.loads(path.read_text(encoding="utf-8"))
                for key in required_keys:
                    self.assertIn(key, messages)
                    self.assertTrue(str(messages[key].get("message") or "").strip())

    def test_english_copy_names_existing_formats(self) -> None:
        messages = json.loads(EN_MESSAGES.read_text(encoding="utf-8"))

        self.assertIn(
            "existing profile share format",
            messages["share_center_mode_full_hint"]["message"],
        )
        self.assertIn(
            "existing SRS settings format",
            messages["share_center_target_profile_settings_hint"]["message"],
        )
        self.assertIn(
            "existing profile share format",
            messages["share_center_hint_ready_full_export"]["message"],
        )
        self.assertIn(
            "existing profile share format",
            messages["share_center_compatibility_note"]["message"],
        )
        self.assertIn(
            "existing SRS settings format",
            messages["share_center_compatibility_note"]["message"],
        )


if __name__ == "__main__":
    unittest.main()
