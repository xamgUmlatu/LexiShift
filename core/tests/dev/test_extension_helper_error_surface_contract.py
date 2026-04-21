from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER_ERROR_COPY_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_error_copy.js"
HELPER_RULES_RUNTIME_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js"
)
TRANSLATE_RESOLVER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/bootstrap/translate_resolver.js"
)
PROFILE_RULESETS_STATE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/rules/profile_rulesets_state.js"
)
PROFILE_RULESETS_CONTROLLER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/rules/profile_rulesets_controller.js"
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
            "Node helper error surface contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperErrorSurfaceContract(unittest.TestCase):
    def test_helper_rules_runtime_normalizes_native_transport_failures(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const runtimePath = {json.dumps(str(HELPER_RULES_RUNTIME_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(runtimePath, "utf8"), context, {{ filename: runtimePath }});

const createRuntime = context.LexiShift.contentHelperRulesRuntime.createRuntime;
const runtime = createRuntime({{
  getHelperClient() {{
    return {{
      async getRuleset() {{
        return {{
          ok: false,
          error: {{
            code: "native_host_exited",
            message: "Native host has exited."
          }}
        }};
      }},
      async getSemanticInventory() {{
        throw {{
          code: "bridge_unavailable",
          message: "Could not establish connection. Receiving end does not exist."
        }};
      }},
      async semanticAdmitBatch() {{
        return {{
          ok: false,
          error: {{
            code: "native_error",
            message: "Error when communicating with the native messaging host."
          }}
        }};
      }}
    }};
  }}
}});

(async () => {{
  const rules = await runtime.resolveHelperRules("en-es", "default");
  assert.equal(rules.error, "The helper exited unexpectedly.");

  const inventory = await runtime.resolveSemanticInventory("en-es", "default");
  assert.equal(inventory.error, "Helper unavailable.");

  const batch = await runtime.semanticAdmitBatch({{}}, 1000);
  assert.equal(batch.error, "Could not communicate with the helper.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_profile_rulesets_controller_localizes_helper_transport_failures(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const translateResolverPath = {json.dumps(str(TRANSLATE_RESOLVER_JS))};
const statePath = {json.dumps(str(PROFILE_RULESETS_STATE_JS))};
const controllerPath = {json.dumps(str(PROFILE_RULESETS_CONTROLLER_JS))};

const messages = {{
  status_helper_missing: "Localized missing.",
  status_helper_failed: "Localized helper failure.",
  status_helper_native_messaging_failed: "Localized bridge failure."
}};

function createElement(tag) {{
  return {{
    tagName: tag.toUpperCase(),
    className: "",
    textContent: "",
    children: [],
    dataset: {{}},
    classList: {{ add() {{}} }},
    appendChild(child) {{
      this.children.push(child);
      return child;
    }},
    addEventListener() {{}}
  }};
}}

const refreshButton = {{
  disabled: false,
  dataset: {{}},
  _listener: null,
  addEventListener(type, listener) {{
    if (type === "click") {{
      this._listener = listener;
    }}
  }}
}};

const listRoot = {{
  innerHTML: "",
  children: [],
  appendChild(child) {{
    this.children.push(child);
    return child;
  }}
}};

const statusOutput = {{ textContent: "" }};
const statusCalls = [];
let helperCalls = 0;

const context = vm.createContext({{
  console,
  document: {{
    createElement
  }},
  setTimeout
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(translateResolverPath, "utf8"), context, {{ filename: translateResolverPath }});
vm.runInContext(fs.readFileSync(statePath, "utf8"), context, {{ filename: statePath }});
vm.runInContext(fs.readFileSync(controllerPath, "utf8"), context, {{ filename: controllerPath }});

const createController = context.LexiShift.optionsProfileRulesets.createController;
const controller = createController({{
  t: (key, _subs, fallback) => messages[key] || fallback,
  settingsManager: {{
    async load() {{
      return {{
        srsProfiles: {{ default: {{}} }},
        manualRulesetCacheByPath: {{}}
      }};
    }},
    async save(_payload) {{}},
    normalizeSrsProfileId(value) {{
      return String(value || "").trim() || "default";
    }},
    getSelectedSrsProfileId() {{
      return "default";
    }}
  }},
  helperManager: {{
    async getProfileRulesets() {{
      helperCalls += 1;
      if (helperCalls === 1) {{
        return {{
          ok: false,
          error: {{
            code: "bridge_unavailable",
            message: "Could not establish connection. Receiving end does not exist."
          }}
        }};
      }}
      throw {{
        code: "native_error",
        message: "Error when communicating with the native messaging host."
      }};
    }}
  }},
  setStatus(message) {{
    statusCalls.push(message);
  }},
  log: () => {{}},
  elements: {{
    profileRulesetsList: listRoot,
    profileRulesetsStatus: statusOutput,
    profileRulesetsRefreshButton: refreshButton
  }}
}});

(async () => {{
  await controller.syncForProfile({{ profileId: "default" }});
  assert.equal(statusOutput.textContent, "Localized missing.");

  refreshButton._listener();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(statusCalls.at(-1), "Localized bridge failure.");
  assert.equal(statusOutput.textContent, "Localized bridge failure.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)
