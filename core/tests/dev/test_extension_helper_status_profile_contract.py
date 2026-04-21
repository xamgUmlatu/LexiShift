from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER_CLIENT_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_client.js"
TRANSLATE_RESOLVER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/bootstrap/translate_resolver.js"
)
HELPER_ACTIONS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/helper/actions_controller.js"
)
PAGE_INIT_JS = PROJECT_ROOT / "apps/chrome-extension/options/controllers/page/init_controller.js"


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
            "Node helper status profile contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperStatusProfileContract(unittest.TestCase):
    def test_helper_client_status_includes_profile_id_when_provided(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload) {{
    calls.push({{ type, payload }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.getStatus("suisui");
  await client.getStatus();
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{ type: "status", payload: {{ profile_id: "suisui" }} }},
    {{ type: "status", payload: {{}} }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_actions_refresh_status_forwards_profile_id(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const translateResolverPath = {json.dumps(str(TRANSLATE_RESOLVER_JS))};
const actionsPath = {json.dumps(str(HELPER_ACTIONS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(translateResolverPath, "utf8"), context, {{ filename: translateResolverPath }});
vm.runInContext(fs.readFileSync(actionsPath, "utf8"), context, {{ filename: actionsPath }});

const createController = context.LexiShift.optionsHelperActions.createController;
const statusUpdates = [];
let capturedProfileId = null;
const controller = createController({{
  t: (_key, _subs, fallback) => fallback || "",
  helperManager: {{
    async getStatus(profileId) {{
      capturedProfileId = profileId;
      return {{ message: "Helper connected.", lastRun: "2026-04-22T00:00:00Z" }};
    }}
  }},
  setHelperStatus(message, lastRun) {{
    statusUpdates.push([message, lastRun]);
  }}
}});

(async () => {{
  await controller.refreshStatus("suisui");
  assert.equal(capturedProfileId, "suisui");
  assert.deepEqual(statusUpdates, [
    ["Connecting…", ""],
    ["Helper connected.", "2026-04-22T00:00:00Z"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_page_init_refreshes_helper_status_for_selected_profile(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const translateResolverPath = {json.dumps(str(TRANSLATE_RESOLVER_JS))};
const pageInitPath = {json.dumps(str(PAGE_INIT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(translateResolverPath, "utf8"), context, {{ filename: translateResolverPath }});
vm.runInContext(fs.readFileSync(pageInitPath, "utf8"), context, {{ filename: pageInitPath }});

const createController = context.LexiShift.optionsPageInit.createController;
let refreshedProfileId = null;
const controller = createController({{
  settingsManager: {{
    defaults: {{
      highlightColor: "#ffcc00",
      maxReplacementsPerPage: 0,
      maxReplacementsPerLemmaPerPage: 0
    }},
    currentRules: [],
    async load() {{
      return {{
        enabled: true,
        highlightEnabled: true,
        highlightColor: "#ffcc00",
        maxOnePerTextBlock: false,
        allowAdjacentReplacements: true,
        maxReplacementsPerPage: 0,
        maxReplacementsPerLemmaPerPage: 0,
        debugEnabled: false,
        debugFocusWord: "",
        uiLanguage: "system",
        rules: [],
        rulesSource: "editor",
        rulesUpdatedAt: "",
        rulesFileName: "",
        customRulesetEnabled: true,
        srsSelectedProfileId: "suisui"
      }};
    }},
    getSelectedSrsProfileId(items) {{
      return items.srsSelectedProfileId || "default";
    }},
    getProfileLanguagePrefs(_items, _options) {{
      return {{ sourceLanguage: "en", targetLanguage: "es" }};
    }},
    async publishProfileLanguagePrefs() {{}}
  }},
  i18n: {{
    async load() {{}}
  }},
  helperActionsController: {{
    async refreshStatus(profileId) {{
      refreshedProfileId = profileId;
    }}
  }},
  applyLanguagePrefsToInputs() {{
    return "en-es";
  }},
  loadSrsProfileForPair: async () => {{}},
  updateRulesSourceUI: () => {{}},
  updateRulesMeta: () => {{}},
  applyTargetLanguagePrefsLocalization: () => {{}},
  renderSrsProfileStatus: () => {{}},
  renderProfileBackgroundStatus: () => {{}},
  setSrsProfileStatusLocalized: () => {{}},
  setHelperStatus: () => {{}},
  elements: {{
    enabledInput: {{ checked: false }},
    highlightEnabledInput: {{ checked: false }},
    highlightColorInput: {{ value: "" }},
    highlightColorText: {{ value: "", disabled: false }},
    maxOnePerBlockInput: {{ checked: false }},
    allowAdjacentInput: {{ checked: false }},
    maxReplacementsPerPageInput: {{ value: "" }},
    maxReplacementsPerLemmaPageInput: {{ value: "" }},
    debugEnabledInput: {{ checked: false }},
    debugFocusInput: {{ value: "", disabled: false }},
    srsRulegenOutput: {{ textContent: "stale" }},
    debugHelperTestOutput: {{ textContent: "stale" }},
    debugOpenDataDirOutput: {{ textContent: "stale" }},
    languageSelect: {{ value: "" }},
    rulesInput: {{ value: "" }},
    fileStatus: {{ textContent: "" }},
    customRulesetEnabledInput: {{ checked: false }}
  }}
}});

(async () => {{
  await controller.load();
  assert.equal(refreshedProfileId, "suisui");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
