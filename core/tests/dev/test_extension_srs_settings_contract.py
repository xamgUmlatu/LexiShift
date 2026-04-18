from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROFILE_RUNTIME_CONTROLLER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js"
)
SRS_BINDINGS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/page/events/srs_bindings.js"
)
SETTINGS_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/base_methods.js"
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
    def test_controller_save_keeps_signal_updates_narrow_and_preserves_nested_siblings(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

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
      srsSemanticAdmissionEnabled: false,
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
    srsSemanticAdmissionEnabledInput: {{ checked: true }},
    srsSemanticAdmissionFallbackPolicyInput: {{ value: "abstain_on_unavailable" }},
    srsFeedbackSrsInput: {{ checked: true }},
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
  assert.equal(captured.status.message, "SRS settings saved.");
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
      srsSemanticAdmissionEnabled: false,
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
    srsSemanticAdmissionEnabledInput: {{ checked: true }},
    srsSemanticAdmissionFallbackPolicyInput: {{ value: "abstain_on_unavailable" }},
    srsFeedbackSrsInput: {{ checked: true }},
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
const settingNames = new Set([
  "enabled",
  "maxActive",
  "bootstrapTopN",
  "initialActiveCount",
  "topicInterests",
  "proficiencyEstimate",
  "challengeTarget",
  "sound",
  "highlight",
  "highlightText",
  "semanticAdmissionEnabled",
  "semanticFallbackPolicy",
  "feedbackSrs",
  "feedbackRules",
  "exposureLogging"
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
  srsSemanticAdmissionEnabledInput: makeElement("semanticAdmissionEnabled"),
  srsSemanticAdmissionFallbackPolicyInput: makeElement("semanticFallbackPolicy"),
  srsFeedbackSrsInput: makeElement("feedbackSrs"),
  srsFeedbackRulesInput: makeElement("feedbackRules"),
  srsExposureLoggingInput: makeElement("exposureLogging")
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
  Array.from(settingNames).sort()
);
for (const entry of settingsBindings) {{
  assert.equal(entry.eventName, "change");
  assert.equal(entry.fallbackMessage, "Failed to save SRS settings.");
}}
assert.equal(
  directBindings.some((entry) => settingNames.has(entry.name)),
  false
);
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


if __name__ == "__main__":
    unittest.main()
