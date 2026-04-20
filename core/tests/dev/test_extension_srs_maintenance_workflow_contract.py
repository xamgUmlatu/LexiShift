from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAINTENANCE_WORKFLOW_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js"
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
            "Node SRS maintenance-workflow contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSrsMaintenanceWorkflowContract(unittest.TestCase):
    def test_initialize_workflow_forwards_planning_state_and_only_marks_ruleset_update_on_published_apply(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(MAINTENANCE_WORKFLOW_JS))};
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

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const initializeButton = {{ disabled: false }};
const output = {{ textContent: "" }};
const helperCalls = [];
const outputs = [];
const statuses = [];
const results = [
  {{
    applied: true,
    added_items: 4,
    total_items_for_pair: 20,
    plan: {{ strategy_effective: "profile_bootstrap" }},
    bootstrap_diagnostics: {{ selected_count: 4 }},
    rulegen: {{ published: true, targets: 4, rules: 7 }}
  }},
  {{
    applied: false,
    added_items: 0,
    total_items_for_pair: 20,
    plan: {{ strategy_effective: "profile_bootstrap" }},
    bootstrap_diagnostics: {{}},
    rulegen: {{ published: false }}
  }}
];
let rulesetUpdatedCount = 0;

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    defaults: {{
      srsBootstrapTopN: 800,
      srsInitialActiveCount: 40,
      srsMaxActive: 20
    }},
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async initializeSrsSet(pair, sizing, options) {{
      helperCalls.push({{ pair, sizing, options }});
      return results.shift();
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "travel" }}),
  resolvePlanningState: () => ({{
    profile: {{
      srsBootstrapTopN: 900,
      srsInitialActiveCount: 33,
      srsMaxActive: 24
    }},
    profileContext: {{
      pair: "en-ja",
      profile_id: "travel",
      interests: ["animals", "travel"],
      constraints: {{ max_active_items: 24 }},
      sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
    }},
    contextMeta: {{
      source: "current_form",
      pendingOverrides: ["interests"]
    }}
  }}),
  confirmFn: () => true,
  log: () => {{}},
  colors: {{
    SUCCESS: "#3c5a2a",
    ERROR: "#b42318",
    DEFAULT: "#6c675f"
  }},
  output,
  initializeButton,
  setOutputText: (text) => {{
    output.textContent = text;
    outputs.push(text);
  }},
  markRulesetUpdatedNow: async () => {{
    rulesetUpdatedCount += 1;
  }},
  preflightSrsPairResources: async () => true,
  buildInitializeResultOutput: (options) =>
    `init:${{options.applied}}:${{options.added}}:${{options.publishedRulegen ? options.publishedRulegen.published !== false : false}}`
}});

(async () => {{
  await workflows.initializeSet();

  assert.equal(initializeButton.disabled, false);
  assert.equal(helperCalls.length, 1);
  assert.equal(helperCalls[0].pair, "en-ja");
  assert.deepEqual(normalize(helperCalls[0].sizing), {{
    bootstrapTopN: 900,
    initialActiveCount: 33,
    maxActiveItemsHint: 24
  }});
  assert.equal(helperCalls[0].options.profileId, "travel");
  assert.equal(helperCalls[0].options.strategy, "profile_bootstrap");
  assert.equal(helperCalls[0].options.objective, "bootstrap");
  assert.equal(helperCalls[0].options.trigger, "options_initialize_button");
  assert.deepEqual(normalize(helperCalls[0].options.profileContext), {{
    pair: "en-ja",
    profile_id: "travel",
    interests: ["animals", "travel"],
    constraints: {{ max_active_items: 24 }},
    sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
  }});
  assert.equal(outputs[0], "Initializing S…");
  assert.equal(outputs[1], "init:true:4:true");
  assert.equal(
    statuses[0].message,
    "S initialized for en-ja."
  );
  assert.equal(statuses[0].color, "#3c5a2a");
  assert.equal(rulesetUpdatedCount, 1);

  await workflows.initializeSet();

  assert.equal(initializeButton.disabled, false);
  assert.equal(helperCalls.length, 2);
  assert.equal(outputs[2], "Initializing S…");
  assert.equal(outputs[3], "init:false:0:false");
  assert.equal(
    statuses[1].message,
    "S planning completed for en-ja; no changes were applied."
  );
  assert.equal(statuses[1].color, "#6c675f");
  assert.equal(rulesetUpdatedCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_refresh_workflow_short_circuits_on_preflight_and_can_refresh_ruleset_timestamp_on_noop(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(MAINTENANCE_WORKFLOW_JS))};
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

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const refreshButton = {{ disabled: false }};
const output = {{ textContent: "" }};
const helperCalls = [];
const outputs = [];
const statuses = [];
const preflightCalls = [];
let rulesetUpdatedCount = 0;

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    defaults: {{
      srsBootstrapTopN: 800,
      srsMaxActive: 40
    }},
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async refreshSrsSet(pair, options) {{
      helperCalls.push({{ pair, options }});
      return {{
        applied: false,
        added_items: 0,
        admission_refresh: {{
          feedback_window: {{ sampled_feedback_count: 0 }}
        }},
        rulegen: {{
          published: true,
          targets: 8,
          rules: 10
        }}
      }};
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "travel" }}),
  resolvePlanningState: () => ({{
    profile: {{
      srsBootstrapTopN: 900,
      srsMaxActive: 24
    }},
    profileContext: {{
      pair: "en-ja",
      profile_id: "travel",
      interests: ["animals"],
      constraints: {{ max_active_items: 24 }}
    }},
    contextMeta: {{
      source: "saved_profile",
      pendingOverrides: []
    }}
  }}),
  log: () => {{}},
  colors: {{
    SUCCESS: "#3c5a2a",
    ERROR: "#b42318",
    DEFAULT: "#6c675f"
  }},
  output,
  refreshButton,
  setOutputText: (text) => {{
    output.textContent = text;
    outputs.push(text);
  }},
  markRulesetUpdatedNow: async () => {{
    rulesetUpdatedCount += 1;
  }},
  preflightSrsPairResources: async (pair, profileId, actionLabel) => {{
    preflightCalls.push({{ pair, profileId, actionLabel }});
    if (preflightCalls.length === 1) {{
      output.textContent = "blocked: missing resources";
      outputs.push("blocked: missing resources");
      statuses.push({{
        message: "Missing resources for en-ja. Add the required files and try again.",
        color: "#b42318"
      }});
      return false;
    }}
    return true;
  }},
  buildRefreshResultOutput: (options) =>
    `refresh:${{options.applied}}:${{options.added}}:${{options.publishedRulegen ? options.publishedRulegen.published !== false : false}}`
}});

(async () => {{
  await workflows.refreshSetNow();

  assert.equal(refreshButton.disabled, false);
  assert.equal(helperCalls.length, 0);
  assert.deepEqual(normalize(preflightCalls[0]), {{
    pair: "en-ja",
    profileId: "travel",
    actionLabel: "S refresh"
  }});
  assert.equal(outputs[0], "Refreshing S and publishing rules…");
  assert.equal(outputs[1], "blocked: missing resources");
  assert.equal(statuses[0].message, "Missing resources for en-ja. Add the required files and try again.");
  assert.equal(rulesetUpdatedCount, 0);

  await workflows.refreshSetNow();

  assert.equal(refreshButton.disabled, false);
  assert.equal(helperCalls.length, 1);
  assert.equal(helperCalls[0].pair, "en-ja");
  assert.equal(helperCalls[0].options.profileId, "travel");
  assert.equal(helperCalls[0].options.setTopN, 900);
  assert.equal(helperCalls[0].options.maxActiveItems, 24);
  assert.equal(helperCalls[0].options.trigger, "options_refresh_set_button");
  assert.deepEqual(normalize(helperCalls[0].options.profileContext), {{
    pair: "en-ja",
    profile_id: "travel",
    interests: ["animals"],
    constraints: {{ max_active_items: 24 }}
  }});
  assert.equal(outputs[2], "Refreshing S and publishing rules…");
  assert.equal(outputs[3], "refresh:false:0:true");
  assert.equal(
    statuses[1].message,
    "S refresh for en-ja: no new admissions."
  );
  assert.equal(statuses[1].color, "#6c675f");
  assert.equal(rulesetUpdatedCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_reset_workflow_requires_double_confirm_and_maps_outdated_helper_error(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(MAINTENANCE_WORKFLOW_JS))};
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

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
const resetButton = {{ disabled: false }};
const output = {{ textContent: "stale output" }};
const statuses = [];
const confirmMessages = [];
const helperCalls = [];
let loadCount = 0;
const responses = [false, true, false, true, true];

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    async load() {{
      loadCount += 1;
      return {{ saved: true }};
    }},
    getSelectedSrsProfileId() {{
      return "travel";
    }}
  }},
  helperManager: {{
    async resetSrs(pair, options) {{
      helperCalls.push({{ pair, options }});
      throw new Error("Unknown command: reset_srs");
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-ja",
  confirmFn: (message) => {{
    confirmMessages.push(message);
    return responses.shift();
  }},
  log: () => {{}},
  colors: {{
    SUCCESS: "#3c5a2a",
    ERROR: "#b42318",
    DEFAULT: "#6c675f"
  }},
  output,
  resetButton,
  setOutputText: (text) => {{
    output.textContent = text;
  }}
}});

(async () => {{
  await workflows.resetSrsData();
  assert.equal(loadCount, 0);
  assert.equal(helperCalls.length, 0);
  assert.equal(resetButton.disabled, false);

  await workflows.resetSrsData();
  assert.equal(loadCount, 0);
  assert.equal(helperCalls.length, 0);
  assert.equal(resetButton.disabled, false);

  await workflows.resetSrsData();
  assert.equal(loadCount, 1);
  assert.equal(helperCalls.length, 1);
  assert.equal(helperCalls[0].pair, "en-ja");
  assert.equal(helperCalls[0].options.profileId, "travel");
  assert.equal(resetButton.disabled, false);
  assert.equal(
    statuses[0].message,
    "Resetting SRS data…"
  );
  assert.equal(
    statuses[1].message,
    "Helper outdated: command not found. Restart helper?"
  );
  assert.equal(statuses[1].color, "#b42318");
  assert.equal(output.textContent, "stale output");
  assert.equal(confirmMessages.length, 5);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
