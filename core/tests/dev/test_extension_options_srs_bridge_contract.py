from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKGROUND_JS = PROJECT_ROOT / "apps/chrome-extension/background.js"
HELPER_ERROR_COPY_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_error_copy.js"
HELPER_TRANSPORT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_transport_extension.js"
)
HELPER_CLIENT_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_client.js"
HELPER_BASE_METHODS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/base_methods.js"
HELPER_DIAGNOSTICS_METHODS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/helper/diagnostics_methods.js"
)
HELPER_SRS_SET_METHODS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/helper/srs_set_methods.js"
)
HELPER_MANAGER_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper_manager.js"


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
            "Node options SRS bridge contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionOptionsSrsBridgeContract(unittest.TestCase):
    def test_options_srs_actions_route_through_background_native_bridge(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const backgroundPath = {json.dumps(str(BACKGROUND_JS))};
const optionFiles = [
  {json.dumps(str(HELPER_ERROR_COPY_JS))},
  {json.dumps(str(HELPER_TRANSPORT_JS))},
  {json.dumps(str(HELPER_CLIENT_JS))},
  {json.dumps(str(HELPER_BASE_METHODS_JS))},
  {json.dumps(str(HELPER_DIAGNOSTICS_METHODS_JS))},
  {json.dumps(str(HELPER_SRS_SET_METHODS_JS))},
  {json.dumps(str(HELPER_MANAGER_JS))}
];

let bridgeListener = null;
const nativeRequests = [];
const bridgeMessages = [];

const backgroundChrome = {{
  runtime: {{
    lastError: null,
    sendNativeMessage(host, request, callback) {{
      nativeRequests.push({{ host, request }});
      callback({{ ok: true, data: {{ status: "ok", type: request.type }} }});
    }},
    onMessage: {{
      addListener(fn) {{
        bridgeListener = fn;
      }}
    }}
  }}
}};
const backgroundContext = vm.createContext({{
  console,
  chrome: backgroundChrome,
  setTimeout: () => 1,
  clearTimeout: () => {{}},
  Date,
  Math
}});
backgroundContext.globalThis = backgroundContext;
vm.runInContext(
  fs.readFileSync(backgroundPath, "utf8"),
  backgroundContext,
  {{ filename: backgroundPath }}
);
assert.equal(typeof bridgeListener, "function");

const optionsChrome = {{
  runtime: {{
    lastError: null,
    sendMessage(message, callback) {{
      bridgeMessages.push(message);
      const keepAlive = bridgeListener(message, null, callback);
      assert.equal(keepAlive, true);
    }}
  }}
}};
const context = vm.createContext({{
  console,
  chrome: optionsChrome,
  setTimeout: () => 1,
  clearTimeout: () => {{}},
  Date,
  Math
}});
context.globalThis = context;
context.LexiShift = {{
  helperCache: {{
    async loadRuleset() {{ return null; }},
    async loadSnapshot() {{ return null; }},
    async loadSemanticInventory() {{ return null; }}
  }},
  srsRuntimeDiagnostics: {{
    async loadLastState() {{ return null; }}
  }}
}};

for (const file of optionFiles) {{
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(
    file === {json.dumps(str(HELPER_MANAGER_JS))}
      ? `${{source}}\\nthis.__HelperManager = HelperManager;`
      : source,
    context,
    {{ filename: file }}
  );
}}

const normalize = (value) => JSON.parse(JSON.stringify(value));
const manager = new context.__HelperManager({{
  t(_key, _args, fallback) {{
    return fallback || "";
  }}
}}, () => {{}});
const profileContext = {{
  interests: ["animals"],
  topic_weights: {{ animals: 0.8 }},
  proficiency: {{ self_reported_level: 0.42 }}
}};

(async () => {{
  await manager.initializeSrsSet("en-es", {{
    bootstrapTopN: 1200,
    initialActiveCount: 48,
    maxActiveItemsHint: 64
  }}, {{
    profileId: "alpha profile",
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    trigger: "unit_initialize",
    profileContext
  }});
  await manager.planSrsSet("en-es", 900, {{
    profileId: "alpha profile",
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    trigger: "unit_plan",
    profileContext
  }});
  await manager.previewSrsAdmission("en-es", 900, {{
    profileId: "alpha profile",
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    previewCount: 12,
    previewSamplingMode: "top_k_weighted",
    previewSeed: 77,
    trigger: "unit_preview",
    profileContext
  }});
  await manager.refreshSrsSet("en-es", {{
    profileId: "alpha profile",
    setTopN: 2500,
    feedbackWindowSize: 80,
    maxActiveItems: 70,
    maxNewItems: 5,
    allowedPos: "noun, verb",
    persistStore: true,
    strategy: "profile_growth",
    trigger: "unit_refresh",
    profileContext
  }});
  await manager.openResourceSettings("en-es", {{
    profileId: "alpha profile",
    missingInputs: [
      {{ type: "set_source_db", path: "/missing/freq-es-cde.sqlite" }}
    ]
  }});

  assert.deepEqual(bridgeMessages.map((message) => message.requestType), [
    "srs_initialize",
    "srs_plan_set",
    "srs_preview_admission",
    "srs_refresh",
    "open_resource_settings"
  ]);
  assert.deepEqual(bridgeMessages.map((message) => message.timeoutMs), [
    30000,
    15000,
    60000,
    30000,
    4000
  ]);
  assert.deepEqual(nativeRequests.map((entry) => entry.host), [
    "com.lexishift.helper",
    "com.lexishift.helper",
    "com.lexishift.helper",
    "com.lexishift.helper",
    "com.lexishift.helper"
  ]);
  assert.deepEqual(nativeRequests.map((entry) => entry.request.type), [
    "srs_initialize",
    "srs_plan_set",
    "srs_preview_admission",
    "srs_refresh",
    "open_resource_settings"
  ]);

  assert.deepEqual(normalize(nativeRequests[0].request.payload), {{
    pair: "en-es",
    profile_id: "alpha profile",
    set_top_n: 1200,
    bootstrap_top_n: 1200,
    initial_active_count: 48,
    max_active_items_hint: 64,
    replace_pair: false,
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    trigger: "unit_initialize",
    profile_context: profileContext
  }});
  assert.deepEqual(normalize(nativeRequests[1].request.payload), {{
    pair: "en-es",
    profile_id: "alpha profile",
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    set_top_n: 900,
    bootstrap_top_n: 900,
    initial_active_count: 40,
    max_active_items_hint: null,
    trigger: "unit_plan",
    profile_context: profileContext
  }});
  assert.deepEqual(normalize(nativeRequests[2].request.payload), {{
    pair: "en-es",
    profile_id: "alpha profile",
    strategy: "profile_bootstrap",
    objective: "bootstrap",
    set_top_n: 900,
    bootstrap_top_n: 900,
    initial_active_count: 40,
    max_active_items_hint: null,
    preview_count: 12,
    preview_sampling_mode: "top_k_weighted",
    preview_seed: 77,
    trigger: "unit_preview",
    profile_context: profileContext
  }});
  assert.deepEqual(normalize(nativeRequests[3].request.payload), {{
    pair: "en-es",
    profile_id: "alpha profile",
    set_top_n: 2500,
    feedback_window_size: 80,
    max_active_items: 70,
    max_new_items: 5,
    allowed_pos: ["noun", "verb"],
    persist_store: true,
    strategy: "profile_growth",
    trigger: "unit_refresh",
    profile_context: profileContext
  }});
  assert.deepEqual(normalize(nativeRequests[4].request.payload), {{
    pair: "en-es",
    profile_id: "alpha profile",
    resource_context: "srs_story_setup",
    missing_inputs: [
      {{ type: "set_source_db", path: "/missing/freq-es-cde.sqlite" }}
    ]
  }});
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
