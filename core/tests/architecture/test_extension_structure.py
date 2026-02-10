from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

CORE_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PROJECT_ROOT = CORE_ROOT.parent
EXT_ROOT = PROJECT_ROOT / "apps" / "chrome-extension"


class TestExtensionStructure(unittest.TestCase):
    def test_options_settings_domains_exist(self) -> None:
        required = [
            EXT_ROOT / "options" / "core" / "settings" / "base_methods.js",
            EXT_ROOT / "options" / "core" / "settings" / "language_methods.js",
            EXT_ROOT / "options" / "core" / "settings" / "ui_prefs_methods.js",
            EXT_ROOT / "options" / "core" / "settings" / "signals_methods.js",
            EXT_ROOT / "options" / "core" / "settings" / "srs_profile_methods.js",
            EXT_ROOT / "options" / "core" / "settings_manager.js",
        ]
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [])

    def test_options_html_loads_settings_domain_scripts_before_manager(self) -> None:
        html_path = EXT_ROOT / "options.html"
        html = html_path.read_text(encoding="utf-8")
        ordered_markers = [
            'src="options/core/settings/base_methods.js"',
            'src="options/core/settings/language_methods.js"',
            'src="options/core/settings/ui_prefs_methods.js"',
            'src="options/core/settings/signals_methods.js"',
            'src="options/core/settings/srs_profile_methods.js"',
            'src="options/core/settings_manager.js"',
        ]
        positions = [html.find(marker) for marker in ordered_markers]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_content_ui_popup_modules_are_registered_in_manifest_order(self) -> None:
        manifest_path = EXT_ROOT / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scripts = manifest["content_scripts"][0]["js"]
        required_order = [
            "content/runtime/dom_scan_runtime.js",
            "content/runtime/rules/helper_rules_runtime.js",
            "content/runtime/rules/active_rules_runtime.js",
            "content/runtime/diagnostics/apply_diagnostics_reporter.js",
            "content/runtime/feedback/feedback_runtime_controller.js",
            "content/runtime/settings_change_router.js",
            "content/ui/popup_modules/japanese_script_module.js",
            "content/ui/feedback_popup_controller.js",
            "content/ui/ui.js",
        ]
        indices = [scripts.index(path) for path in required_order]
        self.assertEqual(indices, sorted(indices))

    def test_page_general_event_binders_exist(self) -> None:
        required = [
            EXT_ROOT / "options" / "controllers" / "page" / "events" / "general" / "rules_bindings.js",
            EXT_ROOT / "options" / "controllers" / "page" / "events" / "general" / "display_bindings.js",
            EXT_ROOT / "options" / "controllers" / "page" / "events" / "general" / "language_bindings.js",
            EXT_ROOT / "options" / "controllers" / "page" / "events" / "general" / "integrations_bindings.js",
        ]
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
