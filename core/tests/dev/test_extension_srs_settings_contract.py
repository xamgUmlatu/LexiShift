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
UI_MANAGER_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/ui_manager.js"
SETTINGS_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/base_methods.js"
SETTINGS_SRS_PROFILE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/settings/srs_profile_methods.js"
)
SIGNALS_METHODS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/signals_methods.js"


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

    def test_srs_maintenance_and_challenge_controls_are_collapsed(self) -> None:
        html = OPTIONS_HTML.read_text(encoding="utf-8")
        css = OPTIONS_CSS.read_text(encoding="utf-8")

        self.assertIn('class="srs-story-list"', html)
        self.assertIn('id="srs-story-current-card"', html)
        self.assertIn('id="srs-story-current-heading"', html)
        self.assertIn('id="srs-story-current-pair"', html)
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
        self.assertIn('data-i18n="badge_srs_active_story"', html)
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
            r'<details id="srs-story-current-card" class="srs-story-card"[^>]*>',
            html,
        )
        self.assertIsNotNone(current_story_open_tag)
        self.assertNotIn(" open", current_story_open_tag.group(0))
        self.assertRegex(
            html,
            r'(?s)<details id="srs-story-current-card" class="srs-story-card"'
            r'.*?<summary class="srs-story-summary">.*?class="srs-story-badge"',
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
        current_card_start = html.index('<details id="srs-story-current-card"')
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
        self.assertRegex(
            html,
            r'(?s)<details class="advanced srs-story-size-advanced srs-story-flow-size-advanced">'
            r'.*?id="srs-story-flow-bootstrap-top-n"'
            r'.*?for="srs-story-flow-initial-active-count"',
        )
        admission_start = current_card_markup.index(
            'class="srs-settings-section srs-admission-settings"'
        )
        sampling_start = current_card_markup.index('id="srs-story-sampling-curtain"')
        dashboard_start = current_card_markup.index('id="srs-story-dashboard-link-card"')
        appearance_start = current_card_markup.index(
            'class="srs-settings-section srs-appearance-settings"'
        )
        advanced_start = current_card_markup.index(
            'class="advanced srs-maintenance-tools srs-story-advanced-tools"'
        )
        self.assertLess(admission_start, sampling_start)
        self.assertLess(sampling_start, dashboard_start)
        self.assertLess(dashboard_start, appearance_start)
        self.assertLess(appearance_start, advanced_start)
        self.assertIn('class="advanced srs-advanced-topic-tags" hidden', html)
        self.assertNotIn('id="srs-feedback-srs-enabled"', html)
        self.assertNotIn('id="srs-auto-refresh-enabled"', html)
        self.assertNotIn('data-i18n="toggle_srs_feedback_srs"', html)
        self.assertNotIn('data-i18n="toggle_srs_auto_refresh"', html)
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
            r"(?s)\.srs-story-card,\s*\.srs-story-start-card\s*\{"
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
  modalBootstrapTopNInput: createInput("1000"),
  modalInitialActiveCountInput: createInput("40"),
  sampleButton: createButton(),
  initializeButton: createButton(),
  previewOutput: {{ textContent: "", style: {{}} }},
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
  mainBootstrapTopNInput: createInput("800"),
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
    previewAdmission: async () => calls.push("previewAdmission"),
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
  elements.modalBootstrapTopNInput.value = "1000";
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
  assert.equal(elements.mainBootstrapTopNInput.value, "1000");
  assert.equal(elements.mainInitialActiveCountInput.value, "40");
  assert.equal(mainTopicAnimals.attributes["aria-pressed"], "true");

  calls.length = 0;
  await controller.previewAdmission();
  assert.deepEqual(calls.slice(0, 3), ["saveLanguage", "saveSrs", "previewAdmission"]);
  assert.equal(elements.mainSrsEnabledInput.checked, false);
  assert.equal(mainSamplingCurtain.open, true);
  assert.equal(elements.previewOutput.textContent, "sample output");

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
      srsBootstrapTopN: 800,
      srsInitialActiveCount: 40,
      srsHighlightColor: "#2F74D0",
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
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
        srsBootstrapTopN: Number.parseInt(raw.srsBootstrapTopN, 10) || defaults.srsBootstrapTopN,
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
    srsBootstrapTopNInput: {{ value: "900" }},
    srsInitialActiveCountInput: {{ value: "33" }},
      srsTopicInterestsInput: {{ value: "animals, travel" }},
      srsProficiencyEstimateInput: {{ value: "55" }},
      srsChallengeTargetInput: {{ value: "65" }},
      srsSoundInput: {{ checked: true }},
      srsHighlightInput: {{ value: "#445566" }},
      srsHighlightTextInput: {{ value: "" }},
      srsFeedbackRulesInput: {{ checked: false }},
      srsExposureLoggingInput: {{ checked: true }}
  }}
}});

(async () => {{
  await controller.saveSrsSettings();

  assert.equal(captured.profileSave.pairKey, "en-ja");
  assert.equal(captured.profileSave.profile.srsMaxActive, 24);
  assert.equal(captured.profileSave.profile.srsBootstrapTopN, 900);
  assert.equal(captured.profileSave.profile.srsInitialActiveCount, 33);
  assert.equal(captured.profileSave.profile.srsSemanticAdmissionEnabled, true);
  assert.equal(captured.profileSave.profile.srsSemanticAdmissionFallbackPolicy, "abstain_on_unavailable");
  assert.equal(captured.profileSave.profile.srsFeedbackSrsEnabled, true);
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
      srsBootstrapTopN: 800,
      srsInitialActiveCount: 40,
      srsHighlightColor: "#2F74D0",
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
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
        srsBootstrapTopN: Number.parseInt(raw.srsBootstrapTopN, 10) || defaults.srsBootstrapTopN,
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
    srsBootstrapTopNInput: {{ value: "900" }},
    srsInitialActiveCountInput: {{ value: "33" }},
    srsTopicInterestsInput: {{ value: "animals, travel" }},
    srsProficiencyEstimateInput: {{ value: "55" }},
    srsChallengeTargetInput: {{ value: "65" }},
    srsSoundInput: {{ checked: true }},
    srsHighlightInput: {{ value: "#445566" }},
    srsHighlightTextInput: {{ value: "" }},
    srsFeedbackRulesInput: {{ checked: false }},
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
  "feedbackRules",
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
  srsFeedbackRulesInput: makeElement("feedbackRules"),
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
  srsBootstrapTopN: 800,
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

  assert.deepEqual(normalize(result), {{ pairKey: "en-es", profileId: "suisui" }});
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
  assert.equal(manager._items.srsPair, "en-es");
  assert.equal(manager._items.srsEnabled, false);

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

    def test_srs_story_card_visibility_tracks_loaded_profile_enablement(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

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
vm.runInContext(
  `${{fs.readFileSync(uiManagerPath, "utf8")}}\nglobalThis.__UIManager = UIManager;`,
  context,
  {{ filename: uiManagerPath }}
);

const ui = new context.__UIManager();

ui.updateSrsInputs({{ srsEnabled: false }}, {{}});
assert.equal(storyCard.hidden, true);
assert.equal(storyCard.open, false);

ui.updateSrsInputs({{ srsEnabled: true }}, {{}});
assert.equal(storyCard.hidden, false);
assert.equal(storyCard.open, false);
"""
        _run_node(script)

    def test_srs_start_card_copy_switches_after_existing_practice(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const presenterPath = {json.dumps(str(SRS_START_CARD_PRESENTER_JS))};
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

const controller = createController({{
  settingsManager: {{
    defaults: {{
      sourceLanguage: "en",
      targetLanguage: "es",
      srsMaxActive: 40,
      srsBootstrapTopN: 800,
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
        srsBootstrapTopN: 800,
        srsInitialActiveCount: 40,
        srsSoundEnabled: true,
        srsHighlightColor: "#2F74D0",
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
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
