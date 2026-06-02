from __future__ import annotations

import json
import os
import re
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

    def test_options_helper_domains_exist(self) -> None:
        required = [
            EXT_ROOT / "shared" / "helper" / "helper_error_copy.js",
            EXT_ROOT / "shared" / "helper" / "word_info_api.js",
            EXT_ROOT / "options" / "core" / "helper" / "base_methods.js",
            EXT_ROOT / "options" / "core" / "helper" / "diagnostics_methods.js",
            EXT_ROOT / "options" / "core" / "helper" / "srs_set_methods.js",
            EXT_ROOT / "options" / "core" / "helper_manager.js",
        ]
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [])

    def test_options_html_loads_helper_domain_scripts_before_manager(self) -> None:
        html_path = EXT_ROOT / "options.html"
        html = html_path.read_text(encoding="utf-8")
        ordered_markers = [
            'src="shared/helper/helper_error_copy.js"',
            'src="shared/helper/helper_client.js"',
            'src="shared/helper/word_info_api.js"',
            'src="options/core/helper/base_methods.js"',
            'src="options/core/helper/diagnostics_methods.js"',
            'src="options/core/helper/srs_set_methods.js"',
            'src="options/core/helper_manager.js"',
        ]
        positions = [html.find(marker) for marker in ordered_markers]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_options_bootstrap_domains_exist(self) -> None:
        required = [
            EXT_ROOT / "options" / "core" / "bootstrap" / "controller_factory.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "ui_bridge.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "language_prefs_adapter.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "translate_resolver.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "dom_aliases.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "controller_adapters.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "controller_graph_elements.js",
            EXT_ROOT / "options" / "core" / "bootstrap" / "controller_graph.js",
        ]
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [])

    def test_options_html_loads_bootstrap_scripts_before_options_root(self) -> None:
        html_path = EXT_ROOT / "options.html"
        html = html_path.read_text(encoding="utf-8")
        ordered_markers = [
            'src="options/core/bootstrap/controller_factory.js"',
            'src="options/core/bootstrap/ui_bridge.js"',
            'src="options/core/bootstrap/language_prefs_adapter.js"',
            'src="options/core/bootstrap/translate_resolver.js"',
            'src="options/core/bootstrap/dom_aliases.js"',
            'src="options/core/bootstrap/controller_adapters.js"',
            'src="options/core/bootstrap/controller_graph_elements.js"',
            'src="options/core/bootstrap/controller_graph.js"',
            'src="options.js"',
        ]
        positions = [html.find(marker) for marker in ordered_markers]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_options_html_loads_full_srs_action_stack_before_controller(self) -> None:
        html_path = EXT_ROOT / "options.html"
        html = html_path.read_text(encoding="utf-8")
        ordered_markers = [
            'src="options/controllers/srs/planning_state.js"',
            'src="options/controllers/srs/actions/planning_state_resolver.js"',
            'src="options/controllers/srs/actions/admission_preview_formatter.js"',
            'src="options/controllers/srs/actions/admission_preview_workflow.js"',
            'src="options/controllers/srs/actions/rebalance_formatter.js"',
            'src="options/controllers/srs/actions/rebalance_workflow.js"',
            'src="options/controllers/srs/actions/formatters.js"',
            'src="options/controllers/srs/actions/shared.js"',
            'src="options/controllers/srs/actions/semantic_pack_install_workflow.js"',
            'src="options/controllers/srs/actions/words_dashboard_model.js"',
            'src="options/controllers/srs/actions/words_dashboard_formatting.js"',
            'src="options/controllers/srs/actions/words_dashboard_renderer.js"',
            'src="options/controllers/srs/actions/words_dashboard_rule_details.js"',
            'src="options/controllers/srs/actions/words_dashboard_workflow.js"',
            'src="options/controllers/srs/actions/maintenance_workflow.js"',
            'src="options/controllers/srs/actions/workflows.js"',
            'src="options/controllers/srs/actions_controller.js"',
        ]
        positions = [html.find(marker) for marker in ordered_markers]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_options_html_i18n_keys_exist_in_all_locale_catalogs(self) -> None:
        html_path = EXT_ROOT / "options.html"
        html = html_path.read_text(encoding="utf-8")
        keys = sorted(set(re.findall(r'data-i18n(?:-placeholder)?="([^"]+)"', html)))

        missing_by_locale: dict[str, list[str]] = {}
        for locale_path in sorted((EXT_ROOT / "_locales").glob("*/messages.json")):
            locale = locale_path.parent.name
            messages = json.loads(locale_path.read_text(encoding="utf-8"))
            missing = [key for key in keys if key not in messages]
            if missing:
                missing_by_locale[locale] = missing

        self.assertEqual(missing_by_locale, {})

    def test_learning_dashboard_page_loads_dependencies_in_order(self) -> None:
        html_path = EXT_ROOT / "learning_dashboard.html"
        html = html_path.read_text(encoding="utf-8")
        ordered_markers = [
            'src="shared/helper/helper_error_copy.js"',
            'src="shared/helper/helper_transport_extension.js"',
            'src="shared/helper/helper_client.js"',
            'src="shared/helper/word_info_api.js"',
            'src="shared/settings/settings_defaults.js"',
            'src="options/core/settings/base_methods.js"',
            'src="options/core/settings/srs_profile_methods.js"',
            'src="options/core/settings_manager.js"',
            'src="options/core/helper/srs_set_methods.js"',
            'src="options/core/helper_manager.js"',
            'src="options/controllers/srs/actions/words_dashboard_model.js"',
            'src="options/controllers/srs/actions/words_dashboard_formatting.js"',
            'src="learning_dashboard_model.js"',
            'src="learning_dashboard_view.js"',
            'src="learning_dashboard.js"',
        ]
        positions = [html.find(marker) for marker in ordered_markers]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_learning_dashboard_i18n_keys_exist_in_all_locale_catalogs(self) -> None:
        html_path = EXT_ROOT / "learning_dashboard.html"
        html = html_path.read_text(encoding="utf-8")
        keys = sorted(set(re.findall(r'data-i18n(?:-placeholder)?="([^"]+)"', html)))

        missing_by_locale: dict[str, list[str]] = {}
        for locale_path in sorted((EXT_ROOT / "_locales").glob("*/messages.json")):
            locale = locale_path.parent.name
            messages = json.loads(locale_path.read_text(encoding="utf-8"))
            missing = [key for key in keys if key not in messages]
            if missing:
                missing_by_locale[locale] = missing

        self.assertEqual(missing_by_locale, {})

    def test_content_runtime_and_ui_modules_are_registered_in_manifest_order(self) -> None:
        manifest_path = EXT_ROOT / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scripts = manifest["content_scripts"][0]["js"]
        required_order = [
            "shared/helper/helper_error_copy.js",
            "shared/helper/helper_transport_extension.js",
            "shared/helper/helper_client.js",
            "shared/helper/word_info_api.js",
            "content/processing/replacement_semantic_debug.js",
            "content/processing/replacement_semantic_override.js",
            "content/processing/replacements.js",
            "content/runtime/dom_scan/node_filters.js",
            "content/runtime/dom_scan/page_budget_tracker.js",
            "content/runtime/dom_scan/scan_order.js",
            "content/runtime/dom_scan/semantic_performance_metrics.js",
            "content/runtime/dom_scan/semantic_node_scheduler.js",
            "content/runtime/dom_scan/scan_counters.js",
            "content/runtime/dom_scan/semantic_context_support.js",
            "content/runtime/dom_scan/semantic_context.js",
            "content/runtime/dom_scan/text_node_processor.js",
            "content/runtime/dom_scan_runtime.js",
            "content/runtime/rules/helper_rules_runtime.js",
            "content/runtime/rules/active_rules_runtime.js",
            "content/runtime/semantic/semantic_gate_summary.js",
            "content/runtime/semantic/semantic_request_context.js",
            "content/runtime/semantic/semantic_gate_batch.js",
            "content/runtime/semantic/semantic_gate_runtime.js",
            "content/runtime/diagnostics/apply_diagnostics_reporter.js",
            "content/runtime/apply_runtime_actions.js",
            "content/runtime/apply_settings_pipeline.js",
            "content/runtime/feedback/feedback_runtime_controller.js",
            "content/runtime/settings_change_router.js",
            "content/ui/popup_modules/module_registry.js",
            "content/ui/popup_modules/quick_definition_module.js",
            "content/ui/popup_modules/japanese_script_module.js",
            "content/ui/feedback_popup_controller.js",
            "content/ui/ui.js",
        ]
        indices = [scripts.index(path) for path in required_order]
        self.assertEqual(indices, sorted(indices))

    def test_page_general_event_binders_exist(self) -> None:
        required = [
            EXT_ROOT
            / "options"
            / "controllers"
            / "page"
            / "events"
            / "general"
            / "rules_bindings.js",
            EXT_ROOT
            / "options"
            / "controllers"
            / "page"
            / "events"
            / "general"
            / "display_bindings.js",
            EXT_ROOT
            / "options"
            / "controllers"
            / "page"
            / "events"
            / "general"
            / "language_bindings.js",
            EXT_ROOT
            / "options"
            / "controllers"
            / "page"
            / "events"
            / "general"
            / "integrations_bindings.js",
        ]
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
