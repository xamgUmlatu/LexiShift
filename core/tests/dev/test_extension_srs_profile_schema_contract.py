from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/base_methods.js"
SIGNALS_METHODS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/settings/signals_methods.js"
HELPER_ERROR_COPY_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_error_copy.js"
HELPER_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/base_methods.js"
HELPER_SRS_SET_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/srs_set_methods.js"


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
            "Node profile-schema contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSrsProfileSchemaContract(unittest.TestCase):
    def test_signal_allowlist_drops_unknown_top_level_families(self) -> None:
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

function SettingsManager() {{}}
SettingsManager.prototype.DEFAULT_PROFILE_ID = "default";
SettingsManager.prototype.defaults = {{}};
installBaseMethods(SettingsManager);
installSignalsMethods(SettingsManager);

const manager = new SettingsManager();
const pruned = manager._pruneSignals({{
  interests: ["animals"],
  objectives: ["daily_reading"],
  proficiency: {{ estimated_value: 0.35 }},
  difficultyPreferences: {{ target_challenge_center: 0.55 }},
  empiricalTrends: {{ topic_bias: {{ animals: 0.4 }} }},
  sourcePreferences: {{ prefer_frequency_list: true }},
  unknownFamily: {{ surprise: true }},
  anotherUnknown: ["x"]
}});

assert.deepEqual(
  Object.keys(pruned).sort(),
  [
    "difficultyPreferences",
    "empiricalTrends",
    "interests",
    "objectives",
    "proficiency",
    "sourcePreferences"
  ].sort()
);
assert.equal("unknownFamily" in pruned, false);
assert.equal("anotherUnknown" in pruned, false);
"""
        _run_node(script)

    def test_helper_request_uses_top_level_sizing_even_if_profile_context_mirror_disagrees(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const helperSrsSetPath = {json.dumps(str(HELPER_SRS_SET_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});
vm.runInContext(fs.readFileSync(helperSrsSetPath, "utf8"), context, {{ filename: helperSrsSetPath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const installHelperSrsSetMethods = context.LexiShift.installHelperSrsSetMethods;

const captured = {{}};
const proto = {{
  i18n: {{ t: (_key, _args, fallback) => fallback }},
  logger: () => {{}}
}};
installHelperBaseMethods(proto);
installHelperSrsSetMethods(proto);
proto.getClient = function getClient() {{
  return {{
    async previewSrsAdmission(request) {{
      captured.request = request;
      return {{ ok: true, data: {{ ok: true }} }};
    }}
  }};
}};

(async () => {{
  await proto.previewSrsAdmission(
    "en-ja",
    {{
      bootstrapTopN: 900,
      initialActiveCount: 33,
      maxActiveItemsHint: 24
    }},
    {{
      profileId: "default",
      profileContext: {{
        pair: "en-ja",
        profile_id: "default",
        constraints: {{ max_active_items: 7 }},
        sizing: {{ bootstrap_top_n: 123, initial_active_count: 7 }}
      }}
    }}
  );

  assert.equal(captured.request.profile_id, "default");
  assert.equal(captured.request.set_top_n, 900);
  assert.equal(captured.request.bootstrap_top_n, 900);
  assert.equal(captured.request.initial_active_count, 33);
  assert.equal(captured.request.max_active_items_hint, 24);
  assert.equal(captured.request.preview_count, 10);
  assert.deepEqual(captured.request.profile_context.constraints, {{ max_active_items: 7 }});
  assert.deepEqual(captured.request.profile_context.sizing, {{
    bootstrap_top_n: 123,
    initial_active_count: 7
  }});
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
