from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEMANTIC_STATUS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/semantic_admission_status.js"
)
PROFILE_RUNTIME_CONTROLLER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js"
)
PROFILE_RUNTIME_VALUES_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/profile_runtime_values.js"
)
AUTO_REFRESH_SETTINGS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/auto_refresh_settings.js"
)
STORY_FLOW_CONTROLLER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/story_flow_controller.js"
)
STORY_FLOW_RESOURCE_CHECK_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/story_flow_resource_check.js"
)
STORY_FLOW_BUSY_OVERLAY_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/story_flow_busy_overlay.js"
)
STORY_FLOW_INITIALIZER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/story_flow_initializer.js"
)
STORY_FLOW_UTILS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/story_flow_utils.js"
)
ADMISSION_PREVIEW_FORMATTER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/admission_preview_formatter.js"
)
CONTROLLER_GRAPH_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/bootstrap/controller_graph.js"
)
SRS_BINDINGS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/page/events/srs_bindings.js"
)
OPTIONS_HTML = PROJECT_ROOT / "apps/chrome-extension/options.html"
OPTIONS_CSS = PROJECT_ROOT / "apps/chrome-extension/options.css"
TOPIC_TAXONOMY_JSON = PROJECT_ROOT / "docs/test_inputs/srs_topic_preference_taxonomy_en_es.json"
SRS_START_CARD_PRESENTER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/srs_start_card_presenter.js"
)
SRS_STORY_VIEW_MODEL_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/srs_story_view_model.js"
)
UI_MANAGER_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/ui_manager.js"
UI_MANAGER_DOM_IDS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/ui_manager_dom_ids.js"
UI_MANAGER_PROFILE_BACKGROUND_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/ui_manager_profile_background.js"
)
SRS_TOPIC_SUPPORT_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/srs_topic_support.js"
SETTINGS_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/base_methods.js"
SETTINGS_LANGUAGE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/settings/language_methods.js"
)
SETTINGS_SRS_PROFILE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/settings/srs_profile_methods.js"
)
SIGNALS_METHODS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/signals_methods.js"
SETTINGS_UI_PREFS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/settings/ui_prefs_methods.js"
)


def _run_node(script: str) -> None:
    result = subprocess.run(
        ["node"],
        input=script,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "Node settings-contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSrsSettingsContract(unittest.TestCase):
    def test_topic_interest_picker_matches_strict_mvp_taxonomy_visibility(self) -> None:
        taxonomy = json.loads(TOPIC_TAXONOMY_JSON.read_text(encoding="utf-8"))
        expected_topic_ids = [
            str(family["id"])
            for family in taxonomy["families"]
            if family.get("mvp_picker_visibility") == "strict_mvp_visible"
        ]
        html = OPTIONS_HTML.read_text(encoding="utf-8")
        actual_topic_ids = re.findall(r'data-srs-topic-interest="([^"]+)"', html)

        self.assertEqual(actual_topic_ids, expected_topic_ids)
        self.assertNotIn("plants_nature", actual_topic_ids)
        self.assertNotIn("travel_places_transport", actual_topic_ids)

    def test_admission_preview_topic_tags_use_options_locale_messages(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const formatterPath = {json.dumps(str(ADMISSION_PREVIEW_FORMATTER_JS))};
const messages = {{
  topic_srs_general: "Localized General",
  topic_srs_medicine_health: "Localized Medicine"
}};
const context = vm.createContext({{
  console,
  LexiShift: {{
    optionsTranslateResolver: {{
      resolveTranslate(translate) {{
        return typeof translate === "function"
          ? translate
          : ((key, _args, fallback) => messages[key] || fallback);
      }}
    }}
  }}
}});
context.globalThis = context;
vm.runInContext(fs.readFileSync(formatterPath, "utf8"), context, {{ filename: formatterPath }});

const view = context.LexiShift.optionsSrsAdmissionPreviewFormatter.buildAdmissionPreviewView({{
  translate: (key, _args, fallback) => messages[key] || fallback,
  srsPair: "en-de",
  plan: {{ can_execute: true }},
  preview: {{
    admitted_count: 2,
    sample_count_effective: 2,
    admitted_words: [
      {{ lemma: "haus", signals: {{}} }},
      {{
        lemma: "arzt",
        signals: {{ topic_affinity_source: "topic_hint:medicine_health" }}
      }}
    ],
    profile_bootstrap: {{
      profile_context: {{ interests: ["medicine_health"] }},
      active_topic_support: {{ topics: [] }}
    }}
  }}
}});

assert.match(view.html, /Localized General/);
assert.match(view.html, /Localized Medicine/);
assert.doesNotMatch(view.html, />general</);
assert.doesNotMatch(view.html, />medicine & health</i);
assert.match(view.html, /Selected topics: Localized Medicine/);
"""
        _run_node(script)

    def test_en_ja_topic_chip_support_matches_approved_strong_overlay_families(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const supportPath = {json.dumps(str(SRS_TOPIC_SUPPORT_JS))};
const context = vm.createContext({{
  console,
  chrome: {{
    i18n: {{
      getMessage(key, substitutions) {{
        return `${{key}}:${{(substitutions || []).join(",")}}`;
      }}
    }}
  }}
}});
context.globalThis = context;
vm.runInContext(fs.readFileSync(supportPath, "utf8"), context, {{ filename: supportPath }});

const support = context.LexiShift.optionsSrsTopicSupport;
const expectedSupported = [
  "finance_business",
  "games",
  "law_politics_civics",
  "medicine_health",
  "science_technology",
  "sports_fitness"
];
assert.deepEqual(Array.from(support.supportedTopicsForPair("en-ja")).sort(), expectedSupported);
assert.equal(support.isTopicSupported("en-ja", "medicine_health"), true);
assert.equal(support.isTopicSupported("en-ja", "animals"), false);
assert.equal(support.isTopicSupported("en-ja", "food_cooking"), false);
assert.equal(support.isTopicSupported("en-es", "animals"), true);

function button(topic) {{
  const attrs = {{ "data-srs-topic-interest": topic }};
  return {{
    disabled: false,
    classList: {{
      values: new Set(),
      toggle(name, enabled) {{
        if (enabled) this.values.add(name);
        else this.values.delete(name);
      }}
    }},
    getAttribute(name) {{ return attrs[name] || ""; }},
    setAttribute(name, value) {{ attrs[name] = String(value); }},
    removeAttribute(name) {{ delete attrs[name]; }},
    attrs
  }};
}}
const enabled = button("medicine_health");
const disabled = button("animals");
support.applyTopicChipSupport([enabled, disabled], "en-ja");
assert.equal(enabled.disabled, false);
assert.equal(enabled.attrs["aria-disabled"], "false");
assert.equal(enabled.attrs.title, undefined);
assert.equal(disabled.disabled, true);
assert.equal(disabled.attrs["aria-disabled"], "true");
assert.equal(disabled.classList.values.has("is-unsupported"), true);
assert.equal(disabled.attrs.title, "tooltip_srs_topic_not_covered:en-ja");
"""
        _run_node(script)

    def test_profile_background_uses_asset_presence_without_enable_checkbox(self) -> None:
        html = OPTIONS_HTML.read_text(encoding="utf-8")
        self.assertNotIn('id="profile-bg-enabled"', html)
        self.assertNotIn('id="profile-bg-apply"', html)
        self.assertNotIn("toggle_profile_bg_enabled", html)
        self.assertNotIn("button_profile_bg_apply", html)

        for locale in ("en", "de", "ja", "zh"):
            messages_path = PROJECT_ROOT / f"apps/chrome-extension/_locales/{locale}/messages.json"
            messages = json.loads(messages_path.read_text(encoding="utf-8"))
            self.assertNotIn("toggle_profile_bg_enabled", messages)
            self.assertNotIn("button_profile_bg_apply", messages)

    def test_profile_background_asset_presence_enables_saved_image(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const basePath = {json.dumps(str(SETTINGS_BASE_JS))};
const uiPrefsPath = {json.dumps(str(SETTINGS_UI_PREFS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  profileUiThemePrefs: {{
    resolveCardThemeDefaults() {{
      return {{
        hueDeg: 0,
        saturationPercent: 100,
        brightnessPercent: 100,
        transparencyPercent: 100
      }};
    }},
    normalizeCardThemePrefs(raw, options) {{
      const fallback = options && options.fallback ? options.fallback : {{}};
      const defaults = options && options.defaults ? options.defaults : {{}};
      return {{
        cardThemeHueDeg: raw.cardThemeHueDeg ?? fallback.cardThemeHueDeg ?? defaults.cardThemeHueDeg ?? 0,
        cardThemeSaturationPercent:
          raw.cardThemeSaturationPercent
          ?? fallback.cardThemeSaturationPercent
          ?? defaults.cardThemeSaturationPercent
          ?? 100,
        cardThemeBrightnessPercent:
          raw.cardThemeBrightnessPercent
          ?? fallback.cardThemeBrightnessPercent
          ?? defaults.cardThemeBrightnessPercent
          ?? 100,
        cardThemeTransparencyPercent:
          raw.cardThemeTransparencyPercent
          ?? fallback.cardThemeTransparencyPercent
          ?? defaults.cardThemeTransparencyPercent
          ?? 100
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(basePath, "utf8"), context, {{ filename: basePath }});
vm.runInContext(fs.readFileSync(uiPrefsPath, "utf8"), context, {{ filename: uiPrefsPath }});

function SettingsManager() {{
  this.DEFAULT_PROFILE_ID = "default";
  this.defaults = {{
    srsPair: "en-en",
    profileBackgroundOpacity: 0.18,
    profileBackgroundBackdropColor: "#fbf7f0",
    profileBackgroundPositionX: 50,
    profileBackgroundPositionY: 50,
    profileCardThemeHueDeg: 0,
    profileCardThemeSaturationPercent: 100,
    profileCardThemeBrightnessPercent: 100,
    profileCardThemeTransparencyPercent: 100
  }};
}}
context.LexiShift.optionsSettingsInstallBaseMethods(SettingsManager);
context.LexiShift.optionsSettingsInstallUiPrefsMethods(SettingsManager);

const manager = new SettingsManager();
const prefs = manager.getProfileUiPrefs({{
  optionsSelectedProfileId: "suisui",
  srsProfiles: {{
    suisui: {{
      uiPrefs: {{
        backgroundEnabled: false,
        backgroundAssetId: "suisui:profile_background:asset",
        backgroundOpacity: 0.22,
        backgroundBackdropColor: "#123456"
      }}
    }}
  }}
}}, {{ profileId: "suisui" }});

assert.equal(prefs.profileId, "suisui");
assert.equal(prefs.backgroundAssetId, "suisui:profile_background:asset");
assert.equal(prefs.backgroundEnabled, true);
assert.equal(prefs.backgroundOpacity, 0.22);
assert.equal(prefs.backgroundBackdropColor, "#123456");
"""
        _run_node(script)

    def test_srs_maintenance_and_challenge_controls_are_collapsed(self) -> None:
        html = OPTIONS_HTML.read_text(encoding="utf-8")
        css = OPTIONS_CSS.read_text(encoding="utf-8")
        ui_js = UI_MANAGER_JS.read_text(encoding="utf-8")
        story_view_model_js = SRS_STORY_VIEW_MODEL_JS.read_text(encoding="utf-8")

        self.assertIn('class="srs-story-list"', html)
        self.assertIn('id="srs-story-current-card"', html)
        self.assertIn('id="srs-story-current-heading"', html)
        self.assertIn('id="srs-story-current-pair"', html)
        self.assertIn('id="srs-story-current-meta"', html)
        self.assertIn('data-i18n="heading_srs_practice_settings"', html)
        self.assertLess(
            html.index('id="srs-story-current-card"'),
            html.index('id="srs-story-pair-list"'),
        )
        self.assertNotIn("Selected SRS story", html)
        self.assertNotIn("Current SRS story", html)
        self.assertNotIn("Preferences, dashboard, and maintenance", html)
        self.assertNotIn("Admission preferences", html)
        self.assertNotIn("New-word preferences", html)
        self.assertNotIn("Next words", html)
        self.assertNotIn("Uses installed language data for SRS stories.", html)
        self.assertNotIn('data-i18n="hint_srs_dataset"', html)
        self.assertNotIn("Preview rebalance to current preferences", html)
        self.assertNotIn("heading_srs_current_story", html)
        self.assertNotIn("badge_srs_selected_story", html)
        self.assertIn("optionsSrsStoryViewModel", ui_js)
        self.assertIn('"badge_srs_active_story"', story_view_model_js)
        self.assertLess(
            html.index("options/core/srs_story_view_model.js"),
            html.index("options/core/ui_manager.js"),
        )
        self.assertLess(
            html.index("options/core/ui_manager_dom_ids.js"),
            html.index("options/core/ui_manager.js"),
        )
        self.assertLess(
            html.index("options/core/ui_manager_profile_background.js"),
            html.index("options/core/ui_manager.js"),
        )
        self.assertIn('id="srs-story-start-heading"', html)
        self.assertIn('id="srs-story-flow"', html)
        self.assertIn('id="srs-story-flow-source-language"', html)
        self.assertIn('id="srs-story-flow-target-language"', html)
        self.assertIn(
            '<select id="srs-story-flow-profile-id" hidden aria-hidden="true" tabindex="-1">',
            html,
        )
        self.assertNotIn('label for="srs-story-flow-profile-id"', html)
        self.assertNotIn("Choose a profile and language pair", html)
        self.assertIn('id="srs-story-flow-sample"', html)
        self.assertIn('id="srs-story-flow-initialize"', html)
        self.assertIn('id="srs-story-flow-busy-backdrop"', html)
        self.assertIn('id="srs-story-flow-busy-message"', html)
        self.assertIn('id="srs-story-flow-resource-check"', html)
        self.assertIn('id="srs-story-flow-resource-message"', html)
        self.assertIn('id="srs-story-flow-resource-list"', html)
        self.assertIn('id="srs-story-flow-open-resource-settings"', html)
        self.assertIn('id="srs-story-flow-retry-resources"', html)
        self.assertLess(html.index("story_flow_utils.js"), html.index("story_flow_controller.js"))
        self.assertLess(
            html.index("story_flow_resource_check.js"), html.index("story_flow_controller.js")
        )
        self.assertLess(
            html.index("story_flow_busy_overlay.js"), html.index("story_flow_controller.js")
        )
        self.assertLess(
            html.index("story_flow_initializer.js"), html.index("story_flow_controller.js")
        )
        self.assertLess(html.index("delete_story_state.js"), html.index("maintenance_workflow.js"))
        self.assertIn('<select id="source-language" hidden aria-hidden="true">', html)
        self.assertIn('<select id="target-language" hidden aria-hidden="true">', html)
        self.assertRegex(
            html,
            r'(?s)<button\s+id="srs-initialize-set"[^>]*hidden[^>]*>',
        )
        self.assertIn(
            '<input id="srs-enabled" type="checkbox" hidden aria-hidden="true" />',
            html,
        )
        self.assertNotIn('class="toggle srs-enable-switch"', html)
        self.assertNotIn("srs-enable-switch-ui", html)
        current_story_open_tag = re.search(
            r'<details\s+id="srs-story-current-card"\s+class="srs-active-story-panel"[^>]*>',
            html,
        )
        self.assertIsNotNone(current_story_open_tag)
        self.assertNotIn(" open", current_story_open_tag.group(0))
        self.assertRegex(
            html,
            r'(?s)<details\s+id="srs-story-current-card"\s+class="srs-active-story-panel"'
            r'.*?<summary class="srs-active-story-summary">'
            r'.*?data-i18n="badge_srs_active_story"',
        )
        self.assertRegex(
            html,
            r'(?s)<input\s+[^>]*id="srs-proficiency-estimate"[^>]*type="range"'
            r'[^>]*data-srs-has-value="false"',
        )
        self.assertIn('id="srs-proficiency-estimate-value"', html)
        self.assertIn('id="srs-proficiency-estimate-saved"', html)
        self.assertIn('id="srs-proficiency-estimate-restore"', html)
        self.assertIn('id="srs-save-preferences"', html)
        self.assertIn('id="srs-preferences-save-status"', html)
        self.assertIn('data-i18n="hint_srs_max_active"', html)
        self.assertIn('<input id="srs-initial-active-count" type="hidden" />', html)
        self.assertIn('<input id="srs-bootstrap-top-n" type="hidden" />', html)
        self.assertNotIn('data-i18n="summary_srs_story_pool_advanced"', html)
        self.assertNotIn('data-i18n="section_srs_admission_preferences"', html)
        self.assertIn('data-i18n="summary_srs_starting_size_advanced"', html)
        current_card_start = current_story_open_tag.start()
        start_card_start = html.index('<article class="srs-story-start-card"', current_card_start)
        current_card_markup = html[current_card_start:start_card_start]
        self.assertNotIn('data-i18n="hint_srs_current_story"', current_card_markup)
        self.assertNotIn('data-i18n="hint_srs_admission_preferences"', current_card_markup)
        self.assertNotIn('data-i18n="hint_srs_topic_interest_presets"', current_card_markup)
        self.assertNotIn('data-i18n="badge_srs_topic_interest_pair_support"', current_card_markup)
        self.assertNotIn('for="source-language"', current_card_markup)
        self.assertNotIn('for="target-language"', current_card_markup)
        self.assertNotIn('id="target-language-gear"', current_card_markup)
        self.assertNotIn('for="srs-initial-active-count"', current_card_markup)
        self.assertNotIn('for="srs-bootstrap-top-n"', current_card_markup)
        self.assertNotIn('id="srs-story-flow-bootstrap-top-n"', html)
        self.assertRegex(
            html,
            r'(?s)<details class="advanced srs-story-size-advanced srs-story-flow-size-advanced">'
            r'.*?for="srs-story-flow-initial-active-count"',
        )
        admission_start = current_card_markup.index(
            'class="srs-settings-section srs-admission-settings"'
        )
        sampling_start = current_card_markup.index('id="srs-story-sampling-curtain"')
        dashboard_start = current_card_markup.index('id="srs-story-dashboard-link-card"')
        appearance_start = current_card_markup.index('class="srs-display-inline-controls"')
        advanced_start = current_card_markup.index(
            'class="advanced srs-maintenance-tools srs-story-advanced-tools"'
        )
        self.assertLess(admission_start, sampling_start)
        self.assertLess(sampling_start, dashboard_start)
        self.assertLess(dashboard_start, appearance_start)
        self.assertLess(appearance_start, advanced_start)
        self.assertIn('class="advanced srs-advanced-topic-tags" hidden', html)
        self.assertNotIn('id="srs-feedback-srs-enabled"', html)
        self.assertNotIn('id="srs-feedback-rules-enabled"', html)
        self.assertNotIn('id="srs-auto-refresh-enabled"', html)
        self.assertNotIn('data-i18n="toggle_srs_feedback_srs"', html)
        self.assertNotIn('data-i18n="toggle_srs_feedback_rules"', html)
        self.assertNotIn('data-i18n="toggle_srs_auto_refresh"', html)
        self.assertNotIn('data-i18n="section_srs_display_feedback"', html)
        self.assertNotIn('class="advanced srs-technical-status"', current_card_markup)
        self.assertNotIn('id="helper-status"', current_card_markup)
        self.assertNotIn('id="srs-semantic-admission-status"', current_card_markup)
        self.assertRegex(
            html,
            r'(?s)<section id="srs-story-dashboard-link-card" class="srs-story-link-card srs-story-dashboard-link-card">'
            r'.*?data-i18n="heading_srs_vocabulary_library_entry"'
            r'.*?href="learning_dashboard.html"'
            r'.*?data-i18n="button_srs_words_open_library"',
        )
        self.assertNotIn('class="srs-words-dashboard"', current_card_markup)
        self.assertNotIn('id="srs-words-refresh"', current_card_markup)
        self.assertRegex(
            html,
            r'(?s)<details id="srs-story-sampling-curtain" class="srs-story-curtain srs-story-sampling-curtain">'
            r'.*?class="srs-curtain-summary".*?data-i18n="hint_srs_story_sampling_curtain"'
            r'.*?class="srs-curtain-action".*?id="srs-admission-preview"',
        )
        self.assertRegex(
            html,
            r'(?s)<details class="advanced srs-advanced-challenge" hidden>'
            r'.*?id="srs-challenge-target"',
        )
        self.assertNotIn('data-i18n="summary_srs_story_settings"', current_card_markup)
        self.assertNotIn('data-i18n="hint_srs_story_settings"', current_card_markup)
        self.assertNotIn('data-i18n="hint_srs_story_advanced"', current_card_markup)
        self.assertNotIn('id="srs-rebalance-preview"', current_card_markup)
        self.assertNotIn('id="srs-rebalance-apply"', current_card_markup)
        self.assertNotIn('id="srs-refresh-set"', current_card_markup)
        self.assertRegex(
            html,
            r'(?s)<details class="advanced srs-maintenance-tools srs-story-advanced-tools">'
            r'.*?data-i18n="summary_srs_story_advanced"'
            r'.*?<section class="srs-auto-refresh-settings"'
            r'.*?data-i18n="summary_srs_auto_refresh"',
        )
        self.assertNotRegex(
            current_card_markup,
            r'<details class="advanced srs-auto-refresh-settings"',
        )
        self.assertRegex(
            html,
            r'(?s)<details class="advanced srs-maintenance-tools srs-story-advanced-tools">'
            r'.*?id="srs-delete-story"',
        )
        self.assertIn('data-i18n="button_srs_delete_story"', current_card_markup)
        self.assertNotIn('id="srs-reset"', current_card_markup)
        self.assertNotIn('data-i18n="button_srs_reset"', current_card_markup)
        self.assertIn('class="danger-button"', html)
        self.assertNotIn(".srs-enable-switch", css)
        self.assertNotIn(".srs-enable-switch-ui", css)
        self.assertIn(".srs-toggle-switch-ui", css)
        self.assertIn(".srs-active-practice-row", css)
        self.assertIn(".srs-preference-actions", css)
        self.assertIn(".srs-story-advanced-tools", css)
        self.assertIn(".srs-field-grid", css)
        self.assertIn(".advanced.srs-story-size-advanced", css)
        self.assertRegex(
            css,
            r"(?s)\.srs-story-pair-card\s*\{"
            r".*?border: 1px solid var\(--ls-group-subcard-separator\);"
            r".*?background: var\(--ls-group-subcard-bg\);",
        )
        self.assertRegex(
            css,
            r"(?s)\.srs-story-start-card\s*\{"
            r".*?border: 1px solid var\(--ls-group-subcard-separator\);"
            r".*?background: var\(--ls-group-subcard-bg\);",
        )
        self.assertRegex(
            css,
            r"(?s)\.srs-topic-interest-picker\s*\{"
            r".*?border: 1px solid var\(--ls-group-subcard-separator\);"
            r".*?background: var\(--ls-group-subcard-bg\);",
        )
        self.assertRegex(
            css,
            r"(?s)\.srs-story-curtain\s*\{"
            r".*?border: 1px solid var\(--ls-group-subcard-separator\);"
            r".*?background: var\(--ls-srs-preview-bg\);",
        )
        self.assertIn(".srs-curtain-summary", css)
        self.assertIn(".srs-curtain-action", css)
        self.assertIn(".srs-range-field", css)
        self.assertIn(".srs-saved-setting", css)
        self.assertIn(".srs-preview:empty", css)
        self.assertIn(".srs-preview:not(:empty)", css)

    def test_story_flow_persists_visible_values_before_initialize(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(STORY_FLOW_CONTROLLER_JS))};
const resourcePath = {json.dumps(str(STORY_FLOW_RESOURCE_CHECK_JS))};
const busyOverlayPath = {json.dumps(str(STORY_FLOW_BUSY_OVERLAY_JS))};
const initializerPath = {json.dumps(str(STORY_FLOW_INITIALIZER_JS))};
const utilsPath = {json.dumps(str(STORY_FLOW_UTILS_JS))};

function createClassList() {{
  const values = new Set();
  return {{
    toggle(name, force) {{
      if (force) {{
        values.add(name);
      }} else {{
        values.delete(name);
      }}
    }},
    contains(name) {{
      return values.has(name);
    }}
  }};
}}

function createOption(value, text) {{
  return {{
    value,
    textContent: text || value,
    cloneNode() {{
      return createOption(this.value, this.textContent);
    }}
  }};
}}

function createSelect(value, optionValues) {{
  const select = {{
    value: value || "",
    options: [],
    disabled: false,
    appendChild(option) {{
      this.options.push(option);
      if (!this.value) {{
        this.value = option.value;
      }}
      return option;
    }}
  }};
  Object.defineProperty(select, "innerHTML", {{
    get() {{
      return "";
    }},
    set(_value) {{
      this.options.length = 0;
    }}
  }});
  (optionValues || []).forEach((entry) => select.appendChild(createOption(entry, entry)));
  select.value = value || (select.options[0] && select.options[0].value) || "";
  return select;
}}

function createButton(attrs) {{
  const attributes = {{ ...(attrs || {{}}) }};
  return {{
    disabled: false,
    classList: createClassList(),
    attributes,
    listeners: {{}},
    addEventListener(name, handler) {{
      this.listeners[name] = handler;
    }},
    getAttribute(name) {{
      return attributes[name] || "";
    }},
    setAttribute(name, value) {{
      attributes[name] = String(value);
    }}
  }};
}}

function createInput(value) {{
  const hasValue = String(value || "").trim() !== "";
  return {{
    value: value || "",
    checked: false,
    type: "range",
    dataset: {{ srsHasValue: hasValue ? "true" : "false" }},
    addEventListener() {{}}
  }};
}}

const context = vm.createContext({{
  console,
  document: {{
    body: {{ classList: createClassList() }},
    createElement(tagName) {{
      if (tagName !== "option") throw new Error(`Unexpected element: ${{tagName}}`);
      return createOption("", "");
    }},
    addEventListener() {{}}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(utilsPath, "utf8"), context, {{ filename: utilsPath }});
vm.runInContext(fs.readFileSync(resourcePath, "utf8"), context, {{ filename: resourcePath }});
vm.runInContext(fs.readFileSync(busyOverlayPath, "utf8"), context, {{ filename: busyOverlayPath }});
vm.runInContext(fs.readFileSync(initializerPath, "utf8"), context, {{ filename: initializerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const calls = [];
const mainTopicAnimals = createButton({{ "data-srs-topic-interest": "animals" }});
const modalTopicAnimals = createButton({{ "data-srs-story-topic-interest": "animals" }});
const mainSamplingCurtain = {{ open: false }};
const mainAdmissionPreviewOutput = {{ textContent: "sample output" }};
const backdrop = {{
  classList: createClassList(),
  setAttribute(name, value) {{
    this[name] = value;
  }},
  addEventListener() {{}}
}};
const busyBackdrop = {{
  classList: createClassList(),
  setAttribute(name, value) {{
    this[name] = value;
  }}
}};
const modalRoot = {{ focus() {{ calls.push("focus"); }} }};

const elements = {{
  startButton: createButton(),
  backdrop,
  root: modalRoot,
  closeButton: createButton(),
  modalSourceLanguageInput: createSelect("en", ["en", "es"]),
  modalTargetLanguageInput: createSelect("es", ["en", "es"]),
  modalProfileIdInput: createSelect("family", ["default", "family"]),
  modalProficiencyEstimateInput: createInput("70"),
  modalProficiencyEstimateValueOutput: {{ textContent: "" }},
  modalTopicInterestsInput: createInput("animals"),
  modalTopicInterestChipButtons: [modalTopicAnimals],
  modalMaxActiveInput: createInput("30"),
  modalInitialActiveCountInput: createInput("40"),
  sampleButton: createButton(),
  initializeButton: createButton(),
	  previewOutput: {{ textContent: "", innerHTML: "", style: {{}} }},
  busyBackdrop,
  busyMessage: {{ textContent: "" }},
  mainSourceLanguageInput: createSelect("ja", ["ja", "en", "es"]),
  mainTargetLanguageInput: createSelect("en", ["ja", "en", "es"]),
  mainProfileIdInput: createSelect("default", ["default", "family"]),
  mainSrsEnabledInput: {{ checked: true }},
  mainProficiencyEstimateInput: createInput("44"),
  mainTopicInterestsInput: createInput(""),
  mainTopicInterestChipButtons: [mainTopicAnimals],
  mainMaxActiveInput: createInput("20"),
  mainInitialActiveCountInput: createInput("25"),
  mainSamplingCurtain,
  mainAdmissionPreviewOutput
}};

const controller = context.LexiShift.optionsSrsStoryFlow.createController({{
  t: (_key, _args, fallback) => fallback,
  setStatus: (message) => calls.push(`status:${{message}}`),
  saveSrsProfileId: async () => calls.push("saveProfile"),
  saveLanguageSettings: async () => calls.push("saveLanguage"),
  saveSrsSettings: async () => calls.push("saveSrs"),
  srsActionsController: {{
	    previewAdmission: async (options) => {{
	      calls.push(`previewAdmission:${{options.pairKey}}:${{options.profileId}}`);
	      options.setOutputText({{ html: "<strong>sample output</strong>", text: "sample output" }});
	    }},
    initializeSet: async () => {{
      calls.push("initializeSet");
      assert.equal(busyBackdrop.classList.contains("hidden"), false);
      assert.equal(busyBackdrop["aria-hidden"], "false");
      assert.equal(elements.busyMessage.textContent, "Saving settings and starting Vocabulary Practice…");
      assert.equal(elements.closeButton.disabled, true);
    }}
  }},
  log: () => {{}},
  reloadPage: () => calls.push("reloadPage"),
  elements
}});

(async () => {{
  controller.open();
  assert.equal(elements.modalProficiencyEstimateInput.value, "0");
  assert.equal(elements.modalProficiencyEstimateInput.dataset.srsHasValue, "true");
  assert.equal(elements.modalProficiencyEstimateValueOutput.textContent, "0%");
  assert.equal(elements.modalTopicInterestsInput.value, "");
  assert.equal(modalTopicAnimals.attributes["aria-pressed"], "false");
  elements.modalSourceLanguageInput.value = "en";
  elements.modalTargetLanguageInput.value = "es";
  elements.modalProfileIdInput.value = "family";
  elements.modalProficiencyEstimateInput.value = "70";
  elements.modalProficiencyEstimateInput.dataset.srsHasValue = "true";
  elements.modalTopicInterestsInput.value = "animals";
  elements.modalMaxActiveInput.value = "30";
  elements.modalInitialActiveCountInput.value = "40";
  calls.length = 0;

  await controller.persistVisibleSettings();
  assert.deepEqual(calls, ["saveLanguage", "saveSrs"]);
  assert.equal(elements.mainProfileIdInput.value, "default");
  assert.equal(elements.modalProfileIdInput.value, "default");
  assert.equal(elements.mainSourceLanguageInput.value, "en");
  assert.equal(elements.mainTargetLanguageInput.value, "es");
  assert.equal(elements.mainSrsEnabledInput.checked, false);
  assert.equal(elements.mainProficiencyEstimateInput.value, "70");
  assert.equal(elements.mainTopicInterestsInput.value, "animals");
  assert.equal(elements.mainMaxActiveInput.value, "30");
  assert.equal(elements.mainInitialActiveCountInput.value, "40");
  assert.equal(mainTopicAnimals.attributes["aria-pressed"], "true");

	  calls.length = 0;
	  await controller.previewAdmission();
	  assert.deepEqual(calls, ["previewAdmission:en-es:default", "status:Sample updated."]);
	  assert.equal(elements.mainSrsEnabledInput.checked, false);
	  assert.equal(mainSamplingCurtain.open, false);
	  assert.equal(elements.previewOutput.innerHTML, "<strong>sample output</strong>");

  calls.length = 0;
  await controller.initializeStory();
  assert.deepEqual(calls.slice(0, 3), ["saveLanguage", "saveSrs", "initializeSet"]);
  assert.equal(calls[calls.length - 1], "reloadPage");
  assert.equal(elements.mainSrsEnabledInput.checked, true);
  assert.equal(busyBackdrop.classList.contains("hidden"), true);
  assert.equal(busyBackdrop["aria-hidden"], "true");
  assert.equal(elements.closeButton.disabled, false);
}})().catch((err) => {{
  console.error(err);
  process.exitCode = 1;
}});
"""
        _run_node(script)

    def test_story_flow_surfaces_missing_resources_and_opens_gui_settings(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(STORY_FLOW_CONTROLLER_JS))};
const resourcePath = {json.dumps(str(STORY_FLOW_RESOURCE_CHECK_JS))};
const busyOverlayPath = {json.dumps(str(STORY_FLOW_BUSY_OVERLAY_JS))};
const initializerPath = {json.dumps(str(STORY_FLOW_INITIALIZER_JS))};
const utilsPath = {json.dumps(str(STORY_FLOW_UTILS_JS))};

function createClassList(initialValues) {{
  const values = new Set(initialValues || []);
  return {{
    toggle(name, force) {{
      if (force) {{
        values.add(name);
      }} else {{
        values.delete(name);
      }}
    }},
    contains(name) {{
      return values.has(name);
    }}
  }};
}}

function createOption(value, text) {{
  return {{
    value,
    textContent: text || value,
    cloneNode() {{
      return createOption(this.value, this.textContent);
    }}
  }};
}}

function createSelect(value, optionValues) {{
  const select = {{
    value: value || "",
    options: [],
    appendChild(option) {{
      this.options.push(option);
      if (!this.value) {{
        this.value = option.value;
      }}
      return option;
    }}
  }};
  Object.defineProperty(select, "innerHTML", {{
    get() {{
      return "";
    }},
    set(_value) {{
      this.options.length = 0;
    }}
  }});
  (optionValues || []).forEach((entry) => select.appendChild(createOption(entry, entry)));
  select.value = value || (select.options[0] && select.options[0].value) || "";
  return select;
}}

function createInput(value) {{
  const hasValue = String(value || "").trim() !== "";
  return {{
    value: value || "",
    checked: false,
    type: "range",
    dataset: {{ srsHasValue: hasValue ? "true" : "false" }},
    addEventListener() {{}}
  }};
}}

function createButton(attrs) {{
  const attributes = {{ ...(attrs || {{}}) }};
  return {{
    disabled: false,
    classList: createClassList(),
    addEventListener() {{}},
    getAttribute(name) {{
      return attributes[name] || "";
    }},
    setAttribute(name, value) {{
      attributes[name] = String(value);
    }}
  }};
}}

const resourceList = {{
  children: [],
  appendChild(item) {{
    this.children.push(item);
    return item;
  }}
}};
Object.defineProperty(resourceList, "innerHTML", {{
  get() {{
    return "";
  }},
  set(_value) {{
    resourceList.children.length = 0;
  }}
}});

const context = vm.createContext({{
  console,
  document: {{
    body: {{ classList: createClassList() }},
    createElement(tagName) {{
      if (tagName === "option") return createOption("", "");
      if (tagName === "li") return {{ textContent: "" }};
      throw new Error(`Unexpected element: ${{tagName}}`);
    }},
    addEventListener() {{}}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(utilsPath, "utf8"), context, {{ filename: utilsPath }});
vm.runInContext(fs.readFileSync(resourcePath, "utf8"), context, {{ filename: resourcePath }});
vm.runInContext(fs.readFileSync(busyOverlayPath, "utf8"), context, {{ filename: busyOverlayPath }});
vm.runInContext(fs.readFileSync(initializerPath, "utf8"), context, {{ filename: initializerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const captured = [];
const normalize = (value) => JSON.parse(JSON.stringify(value));
const resourceCheckRoot = {{ classList: createClassList(["hidden"]) }};
const resourceMessage = {{ textContent: "" }};
const resourceOpenButton = createButton();
const backdrop = {{
  classList: createClassList(["hidden"]),
  setAttribute(name, value) {{
    this[name] = value;
  }},
  addEventListener() {{}}
}};
const modalRoot = {{ focus() {{}} }};

const elements = {{
  startButton: createButton(),
  backdrop,
  root: modalRoot,
  closeButton: createButton(),
  modalSourceLanguageInput: createSelect("en", ["en", "es"]),
  modalTargetLanguageInput: createSelect("es", ["en", "es"]),
  modalProfileIdInput: createSelect("family", ["default", "family"]),
  modalProficiencyEstimateInput: createInput(""),
  modalTopicInterestsInput: createInput("animals"),
  modalTopicInterestChipButtons: [],
  modalMaxActiveInput: createInput("40"),
  modalBootstrapTopNInput: createInput("1000"),
  modalInitialActiveCountInput: createInput("40"),
  sampleButton: createButton(),
  initializeButton: createButton(),
  previewOutput: {{ textContent: "", style: {{}} }},
  resourceCheckRoot,
  resourceMessage,
  resourceList,
  resourceOpenButton,
  resourceRetryButton: createButton(),
  mainSourceLanguageInput: createSelect("en", ["en", "es"]),
  mainTargetLanguageInput: createSelect("es", ["en", "es"]),
  mainProfileIdInput: createSelect("family", ["default", "family"]),
  mainSrsEnabledInput: {{ checked: false }},
  mainProficiencyEstimateInput: createInput(""),
  mainTopicInterestsInput: createInput("animals"),
  mainTopicInterestChipButtons: [],
  mainMaxActiveInput: createInput("40"),
  mainBootstrapTopNInput: createInput("1000"),
  mainInitialActiveCountInput: createInput("40")
}};

const controller = context.LexiShift.optionsSrsStoryFlow.createController({{
  t: (_key, _args, fallback) => fallback,
  setStatus: () => {{}},
  saveSrsProfileId: async () => {{}},
  saveLanguageSettings: async () => {{}},
  saveSrsSettings: async () => {{}},
  helperManager: {{
    async openResourceSettings(pair, options) {{
      captured.push({{ pair, options }});
      return "Opened LexiShift resource settings.";
    }}
  }},
  log: () => {{}},
  elements
}});

(async () => {{
  controller.open();
  controller.handleResourcePreflightBlocked({{
    detail: {{
      pair: "en-es",
      profileId: "family",
      missingInputs: [
        {{ type: "translation_dict_path", path: "/missing/wiktionary-es-en.sqlite" }},
        {{ type: "translation_pack_path", path: "/missing/wiktionary-es-en.sqlite" }},
        {{ type: "set_source_db", path: "/missing/freq-es-cde.sqlite" }}
      ]
    }}
  }});

  assert.equal(resourceCheckRoot.classList.contains("hidden"), false);
  assert.match(resourceMessage.textContent, /en-es/);
  assert.equal(resourceList.children.length, 2);
  assert.match(resourceList.children[0].textContent, /Spanish-English dictionary/);
  assert.match(resourceList.children[1].textContent, /Spanish word frequency data/);
  assert.doesNotMatch(
    resourceList.children.map((item) => item.textContent).join(" "),
    /\\/missing\\//
  );

  await controller.openResourceSettings();
  assert.equal(resourceOpenButton.disabled, false);
  assert.equal(captured.length, 1);
  assert.equal(captured[0].pair, "en-es");
  assert.deepEqual(normalize(captured[0].options), {{
    profileId: "family",
    resourceContext: "srs_story_setup",
    missingInputs: [
      {{ type: "translation_dict_path", path: "/missing/wiktionary-es-en.sqlite" }},
      {{ type: "translation_pack_path", path: "/missing/wiktionary-es-en.sqlite" }},
      {{ type: "set_source_db", path: "/missing/freq-es-cde.sqlite" }}
    ]
  }});
  assert.match(resourceMessage.textContent, /After installing/);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_controller_graph_constructs_story_flow_after_controller_adapters(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(CONTROLLER_GRAPH_JS))};
const calls = [];
const context = vm.createContext({{ console, globalThis: {{}} }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }},
  optionsControllerGraphElements: {{
    buildElements() {{
      return {{
        profileBackground: {{}},
        profileRulesets: {{}},
        srsActions: {{}},
        srsStoryFlow: {{}},
        rulesShare: {{}},
        shareCenter: {{}},
        helperActions: {{}},
        srsProfileRuntime: {{}},
        displayReplacement: {{}},
        pageInit: {{}},
        eventWiring: {{}}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const controllerAdapters = {{
  saveLanguageSettings: async () => {{}},
  saveSrsSettings: async () => {{}},
  saveSrsProfileId: async () => {{}},
  saveDisplaySettings: async () => {{}},
  saveReplacementSettings: async () => {{}},
  loadSrsProfileForPair: async () => {{}},
  applyTargetLanguagePrefsLocalization: () => {{}},
  renderSrsProfileStatus: () => {{}},
  renderProfileBackgroundStatus: () => {{}},
  setSrsProfileStatusLocalized: () => {{}},
  refreshSrsProfiles: async () => {{}},
  setTargetLanguagePrefsModalOpen: () => {{}},
  updateTargetLanguagePrefsModalVisibility: () => {{}}
}};

function createGenericController(moduleKey) {{
  calls.push(moduleKey);
  if (moduleKey === "optionsProfileStatus") {{
    return {{
      setLocalized: () => {{}},
      setMessage: () => {{}}
    }};
  }}
  if (moduleKey === "optionsTargetLanguageModal") {{
    return {{
      syncVisibility: () => {{}},
      refreshModulePrefs: async () => {{}}
    }};
  }}
  if (moduleKey === "optionsSrsProfileSelector") {{
    return {{
      syncSelected: async (items) => ({{ items, profileId: "default" }}),
      clearCache: () => {{}}
    }};
  }}
  if (moduleKey === "optionsProfileRulesets" || moduleKey === "optionsShareCenter") {{
    return {{
      syncForProfile: async () => {{}}
    }};
  }}
  if (moduleKey === "optionsProfileBackground") {{
    return {{
      syncForLoadedPrefs: async () => {{}}
    }};
  }}
  if (moduleKey === "optionsSrsProfileRuntime") {{
    return {{
      resolveEffectiveSrsPlanningState: () => null,
      refreshSemanticAdmissionStatus: async () => "unknown",
      loadSrsProfileForPair: async () => {{}},
      refreshSrsProfiles: async () => {{}}
    }};
  }}
  if (moduleKey === "optionsSrsActions") {{
    return {{
      previewAdmission: async () => {{}},
      initializeSet: async () => {{}}
    }};
  }}
  if (moduleKey === "optionsSrsStoryFlow") {{
    assert.equal(typeof this.saveLanguageSettings, "function");
    assert.equal(typeof this.saveSrsSettings, "function");
    assert.equal(typeof this.saveSrsProfileId, "function");
    return {{ bind: () => {{}} }};
  }}
  if (moduleKey === "optionsPageInit" || moduleKey === "optionsEventWiring") {{
    return {{ load: async () => {{}}, bind: () => {{}} }};
  }}
  return {{}};
}}

const graph = context.LexiShift.optionsControllerGraph.createControllerGraph({{
  settingsManager: {{
    getSelectedSrsProfileId: () => "default",
    getProfileLanguagePrefs: () => ({{ sourceLanguage: "en", targetLanguage: "es" }}),
    publishProfileLanguagePrefs: async () => {{}}
  }},
  i18n: {{}},
  t: (_key, _args, fallback) => fallback,
  rulesManager: {{}},
  ui: {{
    COLORS: {{ SUCCESS: "green", ERROR: "red", DEFAULT: "gray" }}
  }},
  helperManager: {{}},
  uiBridge: {{
    setStatus: () => {{}},
    setHelperStatus: () => {{}},
    updateRulesSourceUI: () => {{}},
    updateRulesMeta: () => {{}}
  }},
  requireControllerFactory(moduleKey) {{
    return function controllerFactory(options) {{
      return createGenericController.call(options || {{}}, moduleKey);
    }};
  }},
  languagePrefsAdapterFactory() {{
    return {{
      resolveCurrentTargetLanguage: () => "es",
      resolvePairFromInputs: () => "en-es",
      applyLanguagePrefsToInputs: () => "en-es"
    }};
  }},
  controllerAdaptersFactory() {{
    calls.push("optionsControllerAdapters");
    return controllerAdapters;
  }},
  dom: {{}}
}});

assert.equal(typeof graph.pageInitController.load, "function");
assert.equal(typeof graph.eventWiringController.bind, "function");
assert.ok(calls.indexOf("optionsControllerAdapters") < calls.indexOf("optionsSrsStoryFlow"));
"""
        _run_node(script)

    def test_controller_save_keeps_signal_updates_narrow_and_preserves_nested_siblings(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticStatusPath = {json.dumps(str(SEMANTIC_STATUS_JS))};
const profileValuesPath = {json.dumps(str(PROFILE_RUNTIME_VALUES_JS))};
const autoRefreshSettingsPath = {json.dumps(str(AUTO_REFRESH_SETTINGS_JS))};
const modulePath = {json.dumps(str(PROFILE_RUNTIME_CONTROLLER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticStatusPath, "utf8"), context, {{ filename: semanticStatusPath }});
vm.runInContext(fs.readFileSync(profileValuesPath, "utf8"), context, {{ filename: profileValuesPath }});
vm.runInContext(fs.readFileSync(autoRefreshSettingsPath, "utf8"), context, {{ filename: autoRefreshSettingsPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createController = context.LexiShift.optionsSrsProfileRuntime.createController;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const captured = {{}};

const existingSignals = {{
  interests: ["animals"],
  objectives: ["jlpt_n4"],
  proficiency: {{
    estimated_value: 0.25,
    known_lemmas: ["cat", "dog"],
    self_reported_level: "beginner"
  }},
  difficultyPreferences: {{
    target_challenge_center: 0.35,
    target_challenge_spread: 0.2,
    goal_mode: "growth"
  }},
  empiricalTrends: {{
    topic_bias: {{ animals: 0.4 }}
  }},
  sourcePreferences: {{
    prefer_frequency_list: true
  }}
}};

const controller = createController({{
  settingsManager: {{
    defaults: {{
      sourceLanguage: "en",
      targetLanguage: "ja",
      srsMaxActive: 20,
      srsBootstrapTopN: null,
      srsInitialActiveCount: 40,
      srsHighlightColor: "#2F74D0",
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "legacy_on_unavailable",
      srsFeedbackSrsEnabled: true,
      srsFeedbackRulesEnabled: false,
      srsExposureLoggingEnabled: true
    }},
    async load() {{
      return {{ loaded: true }};
    }},
    getSrsProfileSignals() {{
      return normalize(existingSignals);
    }},
    resolveSrsSetSizing(raw, defaults) {{
      return {{
        srsBootstrapTopN: null,
        srsInitialActiveCount: Number.parseInt(raw.srsInitialActiveCount, 10)
          || defaults.srsInitialActiveCount
      }};
    }},
    async updateSrsProfile(pairKey, profile, globalUpdates, options) {{
      captured.profileSave = {{ pairKey, profile, globalUpdates, options }};
      return {{ profileId: "default" }};
    }},
    async publishSrsRuntimeProfile(pairKey, profile, extraUpdates, options) {{
      captured.runtimePublish = {{ pairKey, profile, extraUpdates, options }};
      return {{}};
    }},
    async updateSrsProfileSignals(pairKey, updates, options) {{
      captured.signalSave = {{ pairKey, updates, options }};
      return {{ profileId: "default" }};
    }}
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "default" }}),
  setStatus: (message, color) => {{
    captured.status = {{ message, color }};
  }},
  log: () => {{}},
  ui: {{}},
  elements: {{
    sourceLanguageInput: {{ value: "en" }},
    targetLanguageInput: {{ value: "ja" }},
    srsEnabledInput: {{ checked: true }},
    srsMaxActiveInput: {{ value: "24" }},
    srsInitialActiveCountInput: {{ value: "33" }},
      srsTopicInterestsInput: {{ value: "animals, travel" }},
      srsProficiencyEstimateInput: {{ value: "55" }},
      srsChallengeTargetInput: {{ value: "65" }},
      srsSoundInput: {{ checked: true }},
      srsHighlightInput: {{ value: "#445566" }},
      srsHighlightTextInput: {{ value: "" }},
      srsExposureLoggingInput: {{ checked: true }}
  }}
}});

(async () => {{
  await controller.saveSrsSettings();

  assert.equal(captured.profileSave.pairKey, "en-ja");
  assert.equal(captured.profileSave.profile.srsMaxActive, 24);
  assert.equal(captured.profileSave.profile.srsBootstrapTopN, null);
  assert.equal(captured.profileSave.profile.srsInitialActiveCount, 33);
  assert.equal(captured.profileSave.profile.srsSemanticAdmissionEnabled, true);
  assert.equal(captured.profileSave.profile.srsSemanticAdmissionFallbackPolicy, "legacy_on_unavailable");
  assert.equal(captured.profileSave.profile.srsFeedbackSrsEnabled, true);
  assert.equal(captured.profileSave.profile.srsFeedbackRulesEnabled, false);
  assert.equal(captured.profileSave.profile.srsAutoRefreshEnabled, true);
  assert.equal("interests" in captured.profileSave.profile, false);

  assert.equal(captured.signalSave.pairKey, "en-ja");
  assert.deepEqual(
    Object.keys(captured.signalSave.updates).sort(),
    ["difficultyPreferences", "interests", "proficiency"]
  );
  assert.deepEqual(normalize(captured.signalSave.updates.interests), ["animals", "travel"]);
  assert.deepEqual(normalize(captured.signalSave.updates.proficiency), {{
    estimated_value: 0.55,
    known_lemmas: ["cat", "dog"],
    self_reported_level: "beginner"
  }});
  assert.deepEqual(normalize(captured.signalSave.updates.difficultyPreferences), {{
    target_challenge_center: 0.65,
    target_challenge_spread: 0.2,
    goal_mode: "growth"
  }});
  assert.equal(captured.signalSave.options.profileId, "default");
  assert.equal(captured.status.message, "Practice settings saved.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_controller_save_surfaces_partial_save_when_signal_persistence_fails(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticStatusPath = {json.dumps(str(SEMANTIC_STATUS_JS))};
const profileValuesPath = {json.dumps(str(PROFILE_RUNTIME_VALUES_JS))};
const autoRefreshSettingsPath = {json.dumps(str(AUTO_REFRESH_SETTINGS_JS))};
const modulePath = {json.dumps(str(PROFILE_RUNTIME_CONTROLLER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticStatusPath, "utf8"), context, {{ filename: semanticStatusPath }});
vm.runInContext(fs.readFileSync(profileValuesPath, "utf8"), context, {{ filename: profileValuesPath }});
vm.runInContext(fs.readFileSync(autoRefreshSettingsPath, "utf8"), context, {{ filename: autoRefreshSettingsPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createController = context.LexiShift.optionsSrsProfileRuntime.createController;
const captured = {{ steps: [] }};

const controller = createController({{
  settingsManager: {{
    defaults: {{
      sourceLanguage: "en",
      targetLanguage: "ja",
      srsMaxActive: 20,
      srsBootstrapTopN: null,
      srsInitialActiveCount: 40,
      srsHighlightColor: "#2F74D0",
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "legacy_on_unavailable",
      srsFeedbackSrsEnabled: true,
      srsFeedbackRulesEnabled: false,
      srsExposureLoggingEnabled: true
    }},
    async load() {{
      return {{ loaded: true }};
    }},
    getSrsProfileSignals() {{
      return {{
        interests: ["animals"],
        proficiency: {{ estimated_value: 0.25 }},
        difficultyPreferences: {{ target_challenge_center: 0.35 }}
      }};
    }},
    resolveSrsSetSizing(raw, defaults) {{
      return {{
        srsBootstrapTopN: null,
        srsInitialActiveCount: Number.parseInt(raw.srsInitialActiveCount, 10)
          || defaults.srsInitialActiveCount
      }};
    }},
    async updateSrsProfile() {{
      captured.steps.push("profile");
      return {{ profileId: "default" }};
    }},
    async publishSrsRuntimeProfile() {{
      captured.steps.push("runtime");
      return {{}};
    }},
    async updateSrsProfileSignals() {{
      captured.steps.push("signals");
      throw new Error("Signal write failed.");
    }}
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "default" }}),
  setStatus: (message, color) => {{
    captured.status = {{ message, color }};
  }},
  log: () => {{}},
  ui: {{}},
  elements: {{
    sourceLanguageInput: {{ value: "en" }},
    targetLanguageInput: {{ value: "ja" }},
    srsEnabledInput: {{ checked: true }},
    srsMaxActiveInput: {{ value: "24" }},
    srsInitialActiveCountInput: {{ value: "33" }},
    srsTopicInterestsInput: {{ value: "animals, travel" }},
    srsProficiencyEstimateInput: {{ value: "55" }},
    srsChallengeTargetInput: {{ value: "65" }},
    srsSoundInput: {{ checked: true }},
    srsHighlightInput: {{ value: "#445566" }},
    srsHighlightTextInput: {{ value: "" }},
    srsExposureLoggingInput: {{ checked: true }}
  }}
}});

(async () => {{
  await assert.rejects(
    () => controller.saveSrsSettings(),
    (error) => {{
      assert.match(error.message, /partially saved/i);
      assert.match(error.message, /Signal write failed\\./);
      assert.equal(error.partialSave, true);
      assert.equal(error.savePhase, "signals");
      return true;
    }}
  );
  assert.deepEqual(captured.steps, ["profile", "runtime", "signals"]);
  assert.equal(captured.status, undefined);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_bindings_route_settings_changes_through_async_handler(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SRS_BINDINGS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const bind = context.LexiShift.optionsEventSrsBindings.bind;
const asyncBindings = [];
const directBindings = [];
const autoSaveSettingNames = new Set([
  "enabled",
  "sound",
  "highlight",
  "highlightText",
  "exposureLogging",
  "savePreferences"
]);
const draftSettingNames = new Set([
  "maxActive",
  "bootstrapTopN",
  "initialActiveCount",
  "topicInterests",
  "proficiencyEstimate",
  "challengeTarget"
]);

function makeElement(name) {{
  return {{
    __name: name,
    value: "",
    addEventListener(eventName, _handler) {{
      directBindings.push({{ name, eventName }});
    }}
  }};
}}

const elements = {{
  srsEnabledInput: makeElement("enabled"),
  srsMaxActiveInput: makeElement("maxActive"),
  srsBootstrapTopNInput: makeElement("bootstrapTopN"),
  srsInitialActiveCountInput: makeElement("initialActiveCount"),
  srsTopicInterestsInput: makeElement("topicInterests"),
  srsProficiencyEstimateInput: makeElement("proficiencyEstimate"),
  srsChallengeTargetInput: makeElement("challengeTarget"),
  srsSoundInput: makeElement("sound"),
  srsHighlightInput: makeElement("highlight"),
  srsHighlightTextInput: makeElement("highlightText"),
  srsExposureLoggingInput: makeElement("exposureLogging"),
  srsSavePreferencesButton: makeElement("savePreferences"),
  srsPreferencesSaveStatusOutput: makeElement("preferencesSaveStatus")
}};

bind({{
  bindAsyncListener: (element, eventName, _action, config) => {{
    if (!element) {{
      return;
    }}
    asyncBindings.push({{
      name: element.__name,
      eventName,
      fallbackMessage: config.fallbackMessage(),
      logMessage: config.logMessage
    }});
  }},
  saveSrsSettings: async () => {{}},
  saveSrsProfileId: async () => {{}},
  refreshSrsProfiles: async () => {{}},
  helperActionsController: {{}},
  srsActionsController: {{
    initializeSet: async () => {{}},
    previewAdmission: async () => {{}},
    previewRebalance: async () => {{}},
    applyRebalance: async () => {{}},
    refreshSetNow: async () => {{}},
    runRuntimeDiagnostics: async () => {{}},
    previewSampledRulegen: async () => {{}},
    resetSrsData: async () => {{}}
  }},
  elements
}});

const settingsBindings = asyncBindings.filter((entry) => entry.logMessage === "SRS settings save failed.");
assert.deepEqual(
  settingsBindings.map((entry) => entry.name).sort(),
  Array.from(autoSaveSettingNames).sort()
);
for (const entry of settingsBindings) {{
  assert.equal(entry.eventName, entry.name === "savePreferences" ? "click" : "change");
  assert.equal(entry.fallbackMessage, "Failed to save practice settings.");
}}
assert.deepEqual(directBindings, [
  {{ name: "maxActive", eventName: "change" }},
  {{ name: "bootstrapTopN", eventName: "change" }},
  {{ name: "initialActiveCount", eventName: "change" }},
  {{ name: "topicInterests", eventName: "change" }},
  {{ name: "topicInterests", eventName: "input" }},
  {{ name: "proficiencyEstimate", eventName: "input" }},
  {{ name: "proficiencyEstimate", eventName: "change" }},
  {{ name: "challengeTarget", eventName: "change" }}
]);
assert.deepEqual(
  new Set(directBindings.map((entry) => entry.name)),
  draftSettingNames
);
"""
        _run_node(script)

    def test_topic_interest_chips_update_interest_signal_input_and_require_save(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SRS_BINDINGS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const bind = context.LexiShift.optionsEventSrsBindings.bind;
const savedValues = [];

function makeInput(value) {{
  return {{
    value,
    asyncListeners: {{}},
    listeners: {{}},
    addEventListener(eventName, handler) {{
      this.listeners[eventName] = handler;
    }}
  }};
}}

function makeChip(topic) {{
  const classes = new Set();
  const attributes = {{
    "data-srs-topic-interest": topic,
    "aria-pressed": "false"
  }};
  return {{
    attributes,
    asyncListeners: {{}},
    classList: {{
      toggle(name, selected) {{
        if (selected) {{
          classes.add(name);
        }} else {{
          classes.delete(name);
        }}
      }},
      contains(name) {{
        return classes.has(name);
      }}
    }},
    getAttribute(name) {{
      return attributes[name] || "";
    }},
    setAttribute(name, value) {{
      attributes[name] = value;
    }}
  }};
}}

const topicInput = makeInput("travel, animals");
const animalsChip = makeChip("animals");
const foodChip = makeChip("food_cooking");
const saveButton = makeInput("");
saveButton.disabled = true;
const saveStatus = {{
  textContent: "",
  classList: {{
    toggle() {{}}
  }}
}};

bind({{
  bindAsyncListener: (element, eventName, action) => {{
    if (!element) {{
      return;
    }}
    element.asyncListeners[eventName] = action;
  }},
  saveSrsSettings: async () => {{
    savedValues.push(topicInput.value);
  }},
  saveSrsProfileId: async () => {{}},
  refreshSrsProfiles: async () => {{}},
  helperActionsController: {{}},
  srsActionsController: {{
    initializeSet: async () => {{}},
    previewAdmission: async () => {{}},
    previewRebalance: async () => {{}},
    applyRebalance: async () => {{}},
    refreshSetNow: async () => {{}},
    runRuntimeDiagnostics: async () => {{}},
    previewSampledRulegen: async () => {{}},
    resetSrsData: async () => {{}}
  }},
  elements: {{
    srsTopicInterestsInput: topicInput,
    srsTopicInterestChipButtons: [animalsChip, foodChip],
    srsSavePreferencesButton: saveButton,
    srsPreferencesSaveStatusOutput: saveStatus
  }}
}});

assert.equal(animalsChip.attributes["aria-pressed"], "true");
assert.equal(animalsChip.classList.contains("is-selected"), true);
assert.equal(foodChip.attributes["aria-pressed"], "false");

(async () => {{
  await foodChip.asyncListeners.click();
  assert.equal(topicInput.value, "travel, animals, food_cooking");
  assert.deepEqual(savedValues, []);
  assert.equal(saveButton.disabled, false);
  assert.equal(saveStatus.textContent, "Unsaved changes.");
  assert.equal(foodChip.attributes["aria-pressed"], "true");
  await saveButton.asyncListeners.click();
  assert.deepEqual(savedValues, ["travel, animals, food_cooking"]);
  assert.equal(saveButton.disabled, true);
  assert.equal(saveStatus.textContent, "Preferences saved.");

  await animalsChip.asyncListeners.click();
  assert.equal(topicInput.value, "travel, food_cooking");
  assert.deepEqual(savedValues, ["travel, animals, food_cooking"]);
  assert.equal(saveButton.disabled, false);
  assert.equal(animalsChip.attributes["aria-pressed"], "false");

  topicInput.value = "animals, food_cooking";
  topicInput.listeners.input();
  assert.equal(animalsChip.attributes["aria-pressed"], "true");
  assert.equal(foodChip.attributes["aria-pressed"], "true");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_proficiency_previous_setting_restore_is_draft_until_save(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SRS_BINDINGS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const bind = context.LexiShift.optionsEventSrsBindings.bind;
const savedValues = [];

function makeElement(value = "") {{
  return {{
    value,
    textContent: "",
    disabled: false,
    dataset: {{}},
    listeners: {{}},
    asyncListeners: {{}},
    classList: {{
      toggle() {{}}
    }},
    addEventListener(eventName, handler) {{
      this.listeners[eventName] = handler;
    }}
  }};
}}

const proficiencyInput = makeElement("80");
proficiencyInput.dataset.srsHasValue = "true";
const currentOutput = makeElement();
const previousOutput = makeElement();
previousOutput.dataset.srsSavedHasValue = "true";
previousOutput.dataset.srsSavedValue = "25";
const restoreButton = makeElement();
const saveButton = makeElement();
saveButton.disabled = true;
const saveStatus = makeElement();

bind({{
  bindAsyncListener: (element, eventName, action) => {{
    if (!element) {{
      return;
    }}
    element.asyncListeners[eventName] = action;
  }},
  saveSrsSettings: async () => {{
    savedValues.push(proficiencyInput.value);
  }},
  saveSrsProfileId: async () => {{}},
  refreshSrsProfiles: async () => {{}},
  helperActionsController: {{}},
  srsActionsController: {{
    initializeSet: async () => {{}},
    previewAdmission: async () => {{}},
    previewRebalance: async () => {{}},
    applyRebalance: async () => {{}},
    refreshSetNow: async () => {{}},
    runRuntimeDiagnostics: async () => {{}},
    previewSampledRulegen: async () => {{}},
    resetSrsData: async () => {{}}
  }},
  elements: {{
    srsProficiencyEstimateInput: proficiencyInput,
    srsProficiencyEstimateValueOutput: currentOutput,
    srsProficiencyEstimateSavedOutput: previousOutput,
    srsProficiencyEstimateRestoreButton: restoreButton,
    srsSavePreferencesButton: saveButton,
    srsPreferencesSaveStatusOutput: saveStatus
  }}
}});

assert.equal(currentOutput.textContent, "80%");
assert.equal(saveButton.disabled, true);

(async () => {{
  await restoreButton.asyncListeners.click();
  assert.equal(proficiencyInput.value, "25");
  assert.equal(currentOutput.textContent, "25%");
  assert.equal(saveButton.disabled, false);
  assert.equal(saveStatus.textContent, "Unsaved changes.");
  assert.deepEqual(savedValues, []);

  await saveButton.asyncListeners.click();
  assert.deepEqual(savedValues, ["25"]);
  assert.equal(previousOutput.textContent, "25%");
  assert.equal(previousOutput.dataset.srsSavedValue, "25");
  assert.equal(saveButton.disabled, true);
  assert.equal(saveStatus.textContent, "Preferences saved.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_signal_persistence_preserves_unedited_top_level_families(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const settingsBasePath = {json.dumps(str(SETTINGS_BASE_JS))};
const signalsPath = {json.dumps(str(SIGNALS_METHODS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(settingsBasePath, "utf8"), context, {{ filename: settingsBasePath }});
vm.runInContext(fs.readFileSync(signalsPath, "utf8"), context, {{ filename: signalsPath }});

const installBaseMethods = context.LexiShift.optionsSettingsInstallBaseMethods;
const installSignalsMethods = context.LexiShift.optionsSettingsInstallSignalsMethods;
const normalize = (value) => JSON.parse(JSON.stringify(value));

function SettingsManager() {{
  this._items = {{
    srsSelectedProfileId: "default",
    srsProfiles: {{
      default: {{
        srsSignalsByPair: {{
          "en-ja": {{
            interests: ["animals"],
            objectives: ["jlpt_n4"],
            proficiency: {{
              estimated_value: 0.25,
              known_lemmas: ["cat", "dog"],
              self_reported_level: "beginner"
            }},
            difficultyPreferences: {{
              target_challenge_center: 0.35,
              target_challenge_spread: 0.2,
              goal_mode: "growth"
            }},
            empiricalTrends: {{
              topic_bias: {{ animals: 0.4 }}
            }},
            sourcePreferences: {{
              prefer_frequency_list: true
            }}
          }}
        }}
      }}
    }}
  }};
}}

SettingsManager.prototype.DEFAULT_PROFILE_ID = "default";
SettingsManager.prototype.defaults = {{ srsPair: "en-en" }};
SettingsManager.prototype.load = async function load() {{
  return normalize(this._items);
}};
SettingsManager.prototype.save = async function save(updates) {{
  this._items = {{
    ...this._items,
    ...updates
  }};
}};

installBaseMethods(SettingsManager);
installSignalsMethods(SettingsManager);

const manager = new SettingsManager();

(async () => {{
  await manager.updateSrsProfileSignals("en-ja", {{
    interests: ["animals", "travel"],
    proficiency: {{
      estimated_value: 0.55,
      known_lemmas: ["cat", "dog"],
      self_reported_level: "beginner"
    }},
    difficultyPreferences: {{
      target_challenge_center: 0.65,
      target_challenge_spread: 0.2,
      goal_mode: "growth"
    }}
  }}, {{
    profileId: "default"
  }});

  const savedSignals = manager._items.srsProfiles.default.srsSignalsByPair["en-ja"];
  assert.deepEqual(normalize(savedSignals), {{
    interests: ["animals", "travel"],
    objectives: ["jlpt_n4"],
    proficiency: {{
      estimated_value: 0.55,
      known_lemmas: ["cat", "dog"],
      self_reported_level: "beginner"
    }},
    difficultyPreferences: {{
      target_challenge_center: 0.65,
      target_challenge_spread: 0.2,
      goal_mode: "growth"
    }},
    empiricalTrends: {{
      topic_bias: {{ animals: 0.4 }}
    }},
    sourcePreferences: {{
      prefer_frequency_list: true
    }}
  }});
  assert.equal(manager._items.srsSelectedProfileId, "default");
  assert.equal(manager._items.srsProfileId, "default");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_activate_srs_profile_pair_makes_selected_story_the_only_active_runtime_story(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const settingsBasePath = {json.dumps(str(SETTINGS_BASE_JS))};
const settingsLanguagePath = {json.dumps(str(SETTINGS_LANGUAGE_JS))};
const settingsProfilePath = {json.dumps(str(SETTINGS_SRS_PROFILE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(settingsBasePath, "utf8"), context, {{ filename: settingsBasePath }});
vm.runInContext(fs.readFileSync(settingsLanguagePath, "utf8"), context, {{ filename: settingsLanguagePath }});
vm.runInContext(fs.readFileSync(settingsProfilePath, "utf8"), context, {{ filename: settingsProfilePath }});

const installBaseMethods = context.LexiShift.optionsSettingsInstallBaseMethods;
const installLanguageMethods = context.LexiShift.optionsSettingsInstallLanguageMethods;
const installSrsProfileMethods = context.LexiShift.optionsSettingsInstallSrsProfileMethods;
const normalize = (value) => JSON.parse(JSON.stringify(value));

function SettingsManager() {{
  this._items = {{
    sourceLanguage: "en",
    targetLanguage: "es",
    targetDisplayScript: "kanji",
    srsPair: "en-es",
    srsEnabled: true,
    srsSelectedProfileId: "suisui",
    srsProfiles: {{
      suisui: {{
        languagePrefs: {{
          sourceLanguage: "en",
          targetLanguage: "es",
          srsPairAuto: true,
          srsPair: "en-es",
          targetScriptPrefs: {{ ja: {{ primaryDisplayScript: "romaji" }} }}
        }},
        srsByPair: {{
          "en-es": {{ srsEnabled: true, srsMaxActive: 40 }},
          "en-de": {{ srsEnabled: false, srsMaxActive: 30 }},
          "en-ja": {{ srsEnabled: true, srsMaxActive: 20 }}
        }},
        srsSignalsByPair: {{}}
      }}
    }}
  }};
}}

SettingsManager.prototype.DEFAULT_PROFILE_ID = "default";
SettingsManager.prototype.defaults = {{
  sourceLanguage: "en",
  targetLanguage: "en",
  targetDisplayScript: "kanji",
  srsPair: "en-en",
  srsMaxActive: 40,
  srsBootstrapTopN: null,
  srsInitialActiveCount: 40,
  srsSoundEnabled: true,
  srsHighlightColor: "#2F74D0",
  srsFeedbackSrsEnabled: true,
  srsFeedbackRulesEnabled: false,
  srsExposureLoggingEnabled: true,
  srsAutoRefreshEnabled: true,
  srsAutoRefreshMinFeedbackEvents: 4,
  srsAutoRefreshMinGoodEasy: 2,
  srsAutoRefreshRepeatMinGoodEasy: 4,
  srsAutoRefreshCooldownMinutes: 0
}};
SettingsManager.prototype.load = async function load() {{
  return normalize(this._items);
}};
SettingsManager.prototype.save = async function save(updates) {{
  this._items = {{
    ...this._items,
    ...updates
  }};
}};

installBaseMethods(SettingsManager);
installLanguageMethods(SettingsManager);
installSrsProfileMethods(SettingsManager);

const manager = new SettingsManager();

(async () => {{
  const result = await manager.activateSrsProfilePair("en-de", {{
    profileId: "suisui"
  }});

  assert.deepEqual(normalize(result), {{
    pairKey: "en-de",
    profileId: "suisui",
    sourceLanguage: "en",
    targetLanguage: "de"
  }});
  assert.equal(manager._items.sourceLanguage, "en");
  assert.equal(manager._items.targetLanguage, "de");
  assert.equal(manager._items.srsPair, "en-de");
  assert.equal(manager._items.srsEnabled, true);
  assert.equal(manager._items.srsSelectedProfileId, "suisui");
  assert.equal(manager._items.srsProfileId, "suisui");

  const savedProfile = manager._items.srsProfiles.suisui;
  assert.equal(savedProfile.languagePrefs.sourceLanguage, "en");
  assert.equal(savedProfile.languagePrefs.targetLanguage, "de");
  assert.equal(savedProfile.languagePrefs.srsPair, "en-de");
  assert.equal(savedProfile.srsByPair["en-de"].srsEnabled, true);
  assert.equal(savedProfile.srsByPair["en-es"].srsEnabled, false);
  assert.equal(savedProfile.srsByPair["en-ja"].srsEnabled, false);

  const pairs = manager.listSrsProfilePairs(manager._items, {{
    profileId: "suisui",
    activePair: "en-de"
  }});
  assert.deepEqual(normalize(pairs.map((entry) => [
    entry.pairKey,
    entry.isActive,
    entry.srsEnabled,
    entry.creationIndex
  ])), [
    ["en-es", false, false, 0],
    ["en-de", true, true, 1],
    ["en-ja", false, false, 2]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_delete_srs_profile_pair_removes_story_state_and_runtime_enablement(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const settingsBasePath = {json.dumps(str(SETTINGS_BASE_JS))};
const settingsProfilePath = {json.dumps(str(SETTINGS_SRS_PROFILE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(settingsBasePath, "utf8"), context, {{ filename: settingsBasePath }});
vm.runInContext(fs.readFileSync(settingsProfilePath, "utf8"), context, {{ filename: settingsProfilePath }});

const installBaseMethods = context.LexiShift.optionsSettingsInstallBaseMethods;
const installSrsProfileMethods = context.LexiShift.optionsSettingsInstallSrsProfileMethods;
const normalize = (value) => JSON.parse(JSON.stringify(value));

function SettingsManager() {{
  this._items = {{
    srsSelectedProfileId: "suisui",
    srsProfiles: {{
      suisui: {{
        languagePrefs: {{ sourceLanguage: "en", targetLanguage: "es" }},
        srsByPair: {{
          "en-es": {{
            srsEnabled: true,
            srsMaxActive: 40,
            srsFeedbackSrsEnabled: false,
            srsAutoRefreshEnabled: false
          }},
          "en-ja": {{ srsEnabled: true, srsMaxActive: 20 }}
        }},
        srsSignalsByPair: {{
          "en-es": {{ interests: ["animals"] }},
          "en-ja": {{ interests: ["games"] }}
        }}
      }}
    }}
  }};
}}

SettingsManager.prototype.DEFAULT_PROFILE_ID = "default";
SettingsManager.prototype.defaults = {{
  srsPair: "en-en",
  srsMaxActive: 40,
  srsBootstrapTopN: null,
  srsInitialActiveCount: 40,
  srsSoundEnabled: true,
  srsHighlightColor: "#2F74D0",
  srsFeedbackSrsEnabled: true,
  srsFeedbackRulesEnabled: false,
  srsExposureLoggingEnabled: true,
  srsAutoRefreshEnabled: true,
  srsAutoRefreshMinFeedbackEvents: 4,
  srsAutoRefreshMinGoodEasy: 2,
  srsAutoRefreshRepeatMinGoodEasy: 4,
  srsAutoRefreshCooldownMinutes: 0
}};
SettingsManager.prototype.load = async function load() {{
  return normalize(this._items);
}};
SettingsManager.prototype.save = async function save(updates) {{
  this._items = {{
    ...this._items,
    ...updates
  }};
}};

installBaseMethods(SettingsManager);
installSrsProfileMethods(SettingsManager);

const manager = new SettingsManager();

(async () => {{
  const initialProfile = manager.getSrsProfile(manager._items, "en-es", {{
    profileId: "suisui"
  }});
  assert.equal(initialProfile.srsPairCount, 2);
  assert.equal(initialProfile.srsFeedbackSrsEnabled, true);
  assert.equal(initialProfile.srsAutoRefreshEnabled, true);

  const result = await manager.deleteSrsProfilePair("en-es", {{
    profileId: "suisui"
  }});

  assert.deepEqual(normalize(result), {{
    pairKey: "en-es",
    profileId: "suisui",
    nextPairKey: "en-ja",
    remainingPairCount: 1
  }});
  const savedProfile = manager._items.srsProfiles.suisui;
  assert.equal(Object.hasOwn(savedProfile.srsByPair, "en-es"), false);
  assert.equal(Object.hasOwn(savedProfile.srsSignalsByPair, "en-es"), false);
  assert.deepEqual(normalize(savedProfile.srsByPair["en-ja"]), {{
    srsEnabled: true,
    srsMaxActive: 20
  }});
  assert.deepEqual(normalize(savedProfile.srsSignalsByPair["en-ja"]), {{
    interests: ["games"]
  }});
  assert.equal(manager._items.srsSelectedProfileId, "suisui");
  assert.equal(manager._items.srsProfileId, "suisui");
  assert.equal(manager._items.srsPair, "en-ja");
  assert.equal(manager._items.srsEnabled, true);
  assert.equal(manager._items.sourceLanguage, "en");
  assert.equal(manager._items.targetLanguage, "ja");

  const deletedProfile = manager.getSrsProfile(manager._items, "en-es", {{
    profileId: "suisui"
  }});
  assert.equal(deletedProfile.srsEnabled, false);
  assert.equal(deletedProfile.srsMaxActive, 40);
  assert.equal(deletedProfile.srsPairCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_srs_story_card_visibility_tracks_loaded_story_existence(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const viewModelPath = {json.dumps(str(SRS_STORY_VIEW_MODEL_JS))};
const uiManagerDomIdsPath = {json.dumps(str(UI_MANAGER_DOM_IDS_JS))};
const uiManagerProfileBackgroundPath = {json.dumps(str(UI_MANAGER_PROFILE_BACKGROUND_JS))};
const uiManagerPath = {json.dumps(str(UI_MANAGER_JS))};
const storyCard = {{ hidden: false, open: true }};
const context = vm.createContext({{
  console,
  document: {{
    getElementById(id) {{
      return id === "srs-story-current-card" ? storyCard : null;
    }},
    querySelectorAll() {{
      return [];
    }}
  }},
  setTimeout(callback) {{
    callback();
  }}
}});
context.globalThis = context;
vm.runInContext(fs.readFileSync(viewModelPath, "utf8"), context, {{ filename: viewModelPath }});
vm.runInContext(fs.readFileSync(uiManagerDomIdsPath, "utf8"), context, {{ filename: uiManagerDomIdsPath }});
vm.runInContext(fs.readFileSync(uiManagerProfileBackgroundPath, "utf8"), context, {{ filename: uiManagerProfileBackgroundPath }});
vm.runInContext(
  `${{fs.readFileSync(uiManagerPath, "utf8")}}\nglobalThis.__UIManager = UIManager;`,
  context,
  {{ filename: uiManagerPath }}
);

const ui = new context.__UIManager();

	ui.updateSrsInputs({{ srsEnabled: false, srsStoryExists: false }}, {{}});
	assert.equal(storyCard.hidden, true);
	assert.equal(storyCard.open, false);

	ui.updateSrsInputs({{ srsEnabled: false, srsStoryExists: true }}, {{}});
	assert.equal(storyCard.hidden, false);
	assert.equal(storyCard.open, false);

	ui.updateSrsInputs({{ srsEnabled: true }}, {{}});
	assert.equal(storyCard.hidden, false);
	assert.equal(storyCard.open, false);
"""
        _run_node(script)

    def test_srs_story_view_model_separates_current_story_from_switchable_stories(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const viewModelPath = {json.dumps(str(SRS_STORY_VIEW_MODEL_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
vm.runInContext(fs.readFileSync(viewModelPath, "utf8"), context, {{ filename: viewModelPath }});

const viewModel = context.LexiShift.optionsSrsStoryViewModel;

const emptyCard = viewModel.currentStoryCard({{ srsStoryExists: false, srsEnabled: false }});
assert.equal(emptyCard.exists, false);
assert.equal(emptyCard.shouldShow, false);
assert.equal(emptyCard.badgeKey, "badge_srs_active_story");
assert.equal(emptyCard.badgeFallback, "Active");
assert.equal(viewModel.currentStoryCard({{ srsStoryExists: true, srsEnabled: false }}).shouldShow, true);
assert.equal(viewModel.currentStoryCard({{ srsEnabled: true }}).shouldShow, true);

const cards = viewModel.switchableStoryCards({{
  currentPairKey: "en-de",
  entries: [
    {{ pairKey: "en-es", isActive: false, srsEnabled: true, creationIndex: 0, srsMaxActive: 30 }},
    {{ pairKey: "en-de", isActive: true, srsEnabled: true, creationIndex: 1, srsMaxActive: 40 }},
    {{ pairKey: "en-ja", isActive: false, srsEnabled: false, creationIndex: 2, srsMaxActive: 20 }}
  ]
}});
assert.deepEqual(cards.map((card) => card.pairKey), ["en-es", "en-ja"]);
assert.equal(cards[0].canSwitch, true);
assert.equal(cards[0].creationIndex, 0);
assert.equal(cards[1].creationIndex, 2);
assert.equal(cards[0].badgeKey, undefined);
assert.equal(cards[1].badgeKey, undefined);
"""
        _run_node(script)

    def test_srs_story_pair_list_omits_active_story_and_localizes_summary(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const viewModelPath = {json.dumps(str(SRS_STORY_VIEW_MODEL_JS))};
const uiManagerDomIdsPath = {json.dumps(str(UI_MANAGER_DOM_IDS_JS))};
const uiManagerProfileBackgroundPath = {json.dumps(str(UI_MANAGER_PROFILE_BACKGROUND_JS))};
const uiManagerPath = {json.dumps(str(UI_MANAGER_JS))};
const elements = new Map();
function createElement(options) {{
  const opts = options || {{}};
  return {{
    hidden: false,
    open: false,
    value: opts.value || "",
    textContent: "",
    innerHTML: "",
    style: {{}},
    selectedIndex: opts.selectedIndex ?? -1,
    options: opts.options || [],
    addEventListener() {{}}
  }};
}}
elements.set("source-language", createElement({{
  value: "en",
  selectedIndex: 0,
  options: [{{ value: "en", textContent: "English" }}]
}}));
elements.set("target-language", createElement({{
  value: "de",
  selectedIndex: 1,
  options: [
    {{ value: "es", textContent: "Español" }},
    {{ value: "de", textContent: "Deutsch" }}
  ]
}}));
elements.set("srs-max-active", createElement({{ value: "40" }}));
elements.set("srs-story-current-card", createElement());
elements.set("srs-story-current-pair", createElement());
elements.set("srs-story-current-meta", createElement());
elements.set("srs-story-pair-list", createElement());

const messages = {{
  label_srs_active_words: "$1 localized active",
  section_srs: "Localized Practice",
  button_srs_story_switch: "Localized Switch"
}};
const context = vm.createContext({{
  console,
  chrome: {{
    i18n: {{
      getMessage(key, substitutions) {{
        const template = messages[key] || "";
        const first = Array.isArray(substitutions) ? substitutions[0] : substitutions;
        return template.replace("$1", first || "");
      }}
    }}
  }},
  document: {{
    getElementById(id) {{
      return elements.get(id) || null;
    }},
    querySelectorAll() {{
      return [];
    }}
  }},
  setTimeout(callback) {{
    callback();
  }}
}});
context.globalThis = context;
vm.runInContext(fs.readFileSync(viewModelPath, "utf8"), context, {{ filename: viewModelPath }});
vm.runInContext(fs.readFileSync(uiManagerDomIdsPath, "utf8"), context, {{ filename: uiManagerDomIdsPath }});
vm.runInContext(fs.readFileSync(uiManagerProfileBackgroundPath, "utf8"), context, {{ filename: uiManagerProfileBackgroundPath }});
vm.runInContext(
  `${{fs.readFileSync(uiManagerPath, "utf8")}}\nglobalThis.__UIManager = UIManager;`,
  context,
  {{ filename: uiManagerPath }}
);

const ui = new context.__UIManager();
ui.updateSrsStorySummary();
assert.equal(elements.get("srs-story-current-pair").textContent, "English -> Deutsch");
assert.equal(elements.get("srs-story-current-meta").textContent, "40 localized active");

ui.updateSrsStoryPairList([
  {{ pairKey: "en-es", isActive: false, srsEnabled: false, creationIndex: 0, srsMaxActive: 40 }},
  {{ pairKey: "en-de", isActive: true, srsEnabled: true, creationIndex: 1, srsMaxActive: 30 }},
  {{ pairKey: "en-ja", isActive: false, srsEnabled: false, creationIndex: 2, srsMaxActive: 20 }}
]);
const markup = elements.get("srs-story-pair-list").innerHTML;
assert.equal(elements.get("srs-story-pair-list").hidden, false);
assert.equal(elements.get("srs-story-current-card").style.order, "1");
assert.match(markup, /data-srs-story-pair="en-es" style="order: 0;"/);
assert.doesNotMatch(markup, /data-srs-story-pair="en-de"/);
assert.match(markup, /data-srs-story-pair="en-ja" style="order: 2;"/);
assert.ok(markup.indexOf('data-srs-story-pair="en-es"') < markup.indexOf('data-srs-story-pair="en-ja"'));
assert.match(markup, /20 localized active/);
assert.doesNotMatch(markup, /Localized Ready|Localized Paused/);
assert.match(markup, /Localized Switch/);

ui.updateSrsStoryPairList([
  {{ pairKey: "en-de", isActive: true, srsEnabled: true, creationIndex: 0, srsMaxActive: 40 }}
]);
assert.equal(elements.get("srs-story-pair-list").hidden, true);
assert.equal(elements.get("srs-story-pair-list").innerHTML, "");
assert.equal(elements.get("srs-story-current-card").style.order, "0");
"""
        _run_node(script)

    def test_srs_start_card_copy_switches_after_existing_practice(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const presenterPath = {json.dumps(str(SRS_START_CARD_PRESENTER_JS))};
const uiManagerDomIdsPath = {json.dumps(str(UI_MANAGER_DOM_IDS_JS))};
const uiManagerProfileBackgroundPath = {json.dumps(str(UI_MANAGER_PROFILE_BACKGROUND_JS))};
const uiManagerPath = {json.dumps(str(UI_MANAGER_JS))};
const elements = new Map();
function createElement() {{
  return {{
    hidden: false,
    open: false,
    checked: false,
    value: "",
    textContent: "",
    dataset: {{}},
    options: [],
    selectedIndex: -1
  }};
}}
[
  "srs-story-current-card",
  "srs-story-current-pair",
  "srs-story-start-heading",
  "srs-story-start-hint",
  "srs-story-start"
].forEach((id) => elements.set(id, createElement()));

const context = vm.createContext({{
  console,
  document: {{
    getElementById(id) {{
      return elements.get(id) || null;
    }},
    querySelectorAll() {{
      return [];
    }}
  }},
  setTimeout(callback) {{
    callback();
  }}
}});
context.globalThis = context;
vm.runInContext(fs.readFileSync(presenterPath, "utf8"), context, {{ filename: presenterPath }});
vm.runInContext(fs.readFileSync(uiManagerDomIdsPath, "utf8"), context, {{ filename: uiManagerDomIdsPath }});
vm.runInContext(fs.readFileSync(uiManagerProfileBackgroundPath, "utf8"), context, {{ filename: uiManagerProfileBackgroundPath }});
vm.runInContext(
  `${{fs.readFileSync(uiManagerPath, "utf8")}}\nglobalThis.__UIManager = UIManager;`,
  context,
  {{ filename: uiManagerPath }}
);

const translated = {{
  heading_srs_start_new_story: "T:start",
  hint_srs_start_new_story: "T:first hint",
  button_srs_start_new_story: "T:start button",
  heading_srs_add_new_story: "T:add",
  hint_srs_add_new_story: "T:add hint",
  button_srs_add_new_story: "T:add button"
}};
const ui = new context.__UIManager();
ui.srsStartCardPresenter = context.LexiShift.optionsSrsStartCardPresenter.createPresenter({{
  i18n: {{
    t(key, _subs, fallback) {{
      return translated[key] || fallback;
    }}
  }}
}});

ui.updateSrsInputs({{ srsEnabled: false, srsPairCount: 0 }}, {{}});
assert.equal(elements.get("srs-story-start-heading").textContent, "T:start");
assert.equal(elements.get("srs-story-start-hint").textContent, "T:first hint");
assert.equal(elements.get("srs-story-start").textContent, "T:start button");
assert.equal(elements.get("srs-story-start-heading").dataset.i18n, "heading_srs_start_new_story");

ui.updateSrsInputs({{ srsEnabled: true, srsPairCount: 1 }}, {{}});
assert.equal(elements.get("srs-story-start-heading").textContent, "T:add");
assert.equal(elements.get("srs-story-start-hint").textContent, "T:add hint");
assert.equal(elements.get("srs-story-start").textContent, "T:add button");
assert.equal(elements.get("srs-story-start-heading").dataset.i18n, "heading_srs_add_new_story");
"""
        _run_node(script)

    def test_controller_refreshes_read_only_semantic_status_from_helper_diagnostics(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticStatusPath = {json.dumps(str(SEMANTIC_STATUS_JS))};
const profileValuesPath = {json.dumps(str(PROFILE_RUNTIME_VALUES_JS))};
const autoRefreshSettingsPath = {json.dumps(str(AUTO_REFRESH_SETTINGS_JS))};
const modulePath = {json.dumps(str(PROFILE_RUNTIME_CONTROLLER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticStatusPath, "utf8"), context, {{ filename: semanticStatusPath }});
vm.runInContext(fs.readFileSync(profileValuesPath, "utf8"), context, {{ filename: profileValuesPath }});
vm.runInContext(fs.readFileSync(autoRefreshSettingsPath, "utf8"), context, {{ filename: autoRefreshSettingsPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createController = context.LexiShift.optionsSrsProfileRuntime.createController;
const statusOutput = {{ textContent: "" }};
const detailOutput = {{ textContent: "" }};
let publishProfileUiPrefsCalls = 0;

const controller = createController({{
  settingsManager: {{
    defaults: {{
      sourceLanguage: "en",
      targetLanguage: "es",
      srsMaxActive: 40,
      srsBootstrapTopN: null,
      srsInitialActiveCount: 40,
      srsHighlightColor: "#2F74D0",
      srsFeedbackSrsEnabled: true,
      srsFeedbackRulesEnabled: false,
      srsExposureLoggingEnabled: true
    }},
    getSrsProfile() {{
      return {{
        profileId: "default",
        srsEnabled: true,
        srsMaxActive: 40,
        srsBootstrapTopN: null,
        srsInitialActiveCount: 40,
        srsSoundEnabled: true,
        srsHighlightColor: "#2F74D0",
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "legacy_on_unavailable",
        srsFeedbackSrsEnabled: true,
        srsFeedbackRulesEnabled: false,
        srsExposureLoggingEnabled: true
      }};
    }},
    getSrsProfileSignals() {{
      return {{}};
    }},
    getProfileUiPrefs() {{
      return {{}};
    }},
    async publishProfileUiPrefs() {{
      publishProfileUiPrefsCalls += 1;
    }},
    async publishSrsRuntimeProfile() {{
      return {{}};
    }}
  }},
  helperManager: {{
    async getSrsRuntimeDiagnostics() {{
      return {{
        helper: {{
          semantic_runtime_capability: "published_unready"
        }}
      }};
    }}
  }},
  ui: {{
    updateSrsInputs() {{}},
    updateProfileBackgroundInputs() {{}}
  }},
  resolvePair: () => "en-es",
  syncSelectedProfile: async (items) => ({{ items, profileId: "default" }}),
  syncProfileRulesetsForProfile: async () => {{}},
  syncShareCenterForProfile: async () => {{}},
  syncProfileBackgroundForPrefs: async () => {{}},
  setStatus: () => {{}},
  setProfileStatusLocalized: () => {{}},
  setProfileStatusMessage: () => {{}},
  log: () => {{}},
  elements: {{
    sourceLanguageInput: {{ value: "en" }},
    targetLanguageInput: {{ value: "es" }},
    srsEnabledInput: {{ checked: true }},
    srsSemanticAdmissionStatusOutput: statusOutput,
    srsSemanticAdmissionStatusDetailOutput: detailOutput
  }}
}});

(async () => {{
  await controller.loadSrsProfileForPair({{}}, "en-es");
  assert.equal(publishProfileUiPrefsCalls, 0);
  assert.equal(statusOutput.textContent, "Not yet available");
  assert.match(detailOutput.textContent, /no ready coverage yet/i);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
