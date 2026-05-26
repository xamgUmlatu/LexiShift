from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAINTENANCE_WORKFLOW_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js"
)
WORDS_DASHBOARD_WORKFLOW_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_workflow.js"
)
SEMANTIC_PACK_INSTALL_WORKFLOW_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/semantic_pack_install_workflow.js"
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

const semanticPackModulePath = {json.dumps(str(SEMANTIC_PACK_INSTALL_WORKFLOW_JS))};
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
vm.runInContext(fs.readFileSync(semanticPackModulePath, "utf8"), context, {{ filename: semanticPackModulePath }});
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

    def test_words_dashboard_refreshes_read_only_items_and_advanced_toggle(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const wordsDashboardModulePath = {json.dumps(str(WORDS_DASHBOARD_WORKFLOW_JS))};
const modulePath = {json.dumps(str(MAINTENANCE_WORKFLOW_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, args, fallback) => {{
            if (Array.isArray(args) && fallback) return fallback;
            return fallback;
          }});
    }}
  }}
}};
vm.runInContext(fs.readFileSync(wordsDashboardModulePath, "utf8"), context, {{ filename: wordsDashboardModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
function makeNode(tagName) {{
  return {{
    tagName,
    className: "",
    textContent: "",
    children: [],
    attributes: {{}},
    ownerDocument: null,
    get firstChild() {{
      return this.children[0] || null;
    }},
    appendChild(child) {{
      this.children.push(child);
      return child;
    }},
    removeChild(child) {{
      this.children = this.children.filter((item) => item !== child);
    }},
    setAttribute(name, value) {{
      this.attributes[name] = String(value);
    }}
  }};
}}
const doc = {{
  createElement(tagName) {{
    const node = makeNode(tagName);
    node.ownerDocument = doc;
    return node;
  }}
}};
const summaryRoot = makeNode("div");
summaryRoot.ownerDocument = doc;
const listRoot = makeNode("div");
listRoot.ownerDocument = doc;
const refreshButton = {{ disabled: false }};
const statuses = [];
const helperCalls = [];

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async listSrsItems(pair, options) {{
      helperCalls.push({{ pair, options }});
      return {{
        status: "ok",
        summary: {{
          total: 1,
          active: 1,
          due_now: 1,
          due_soon: 0,
          queued: 0,
          removed: 0
        }},
        items: [
          {{
            item_id: "en-es:perro",
            lemma: "perro",
            display: "perro",
            reading: "perro",
            status: "due_now",
            status_label: "Due now",
            due_in_seconds: -60,
            review_count: 2,
            exposures: 3,
            source_label: "freq-es-cde",
            advanced: {{
              lifecycle_state: "active",
              scheduler_state: "review",
              scheduler_step: 1,
              confidence: 0.9,
              stability: 4,
              difficulty: 3
            }}
          }}
        ]
      }};
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-es",
  syncSelectedProfile: async (items) => ({{ items, profileId: "alpha" }}),
  log: () => {{}},
  colors: {{
    SUCCESS: "#3c5a2a",
    ERROR: "#b42318",
    DEFAULT: "#6c675f"
  }},
  wordsRefreshButton: refreshButton,
  wordsAdvancedInput: {{ checked: false }},
  wordsSummaryRoot: summaryRoot,
  wordsListRoot: listRoot
}});

(async () => {{
  await workflows.refreshWordsDashboard();
  assert.equal(refreshButton.disabled, false);
  assert.deepEqual(JSON.parse(JSON.stringify(helperCalls)), [
    {{ pair: "en-es", options: {{ profileId: "alpha" }} }}
  ]);
  assert.equal(summaryRoot.children.length, 6);
  assert.equal(summaryRoot.children[0].children[0].textContent, "1");
  assert.equal(listRoot.children.length, 1);
  assert.equal(listRoot.children[0].children.length, 3);
  assert.equal(statuses[0].message, "Loaded 1 SRS words.");

  workflows.setWordsDashboardAdvanced(true);
  assert.equal(listRoot.children.length, 1);
  assert.equal(listRoot.children[0].children.length, 4);
  assert.equal(listRoot.children[0].children[3].className, "srs-word-advanced");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_semantic_pack_install_workflow_requires_review_and_refreshes_status(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticPackModulePath = {json.dumps(str(SEMANTIC_PACK_INSTALL_WORKFLOW_JS))};
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
vm.runInContext(fs.readFileSync(semanticPackModulePath, "utf8"), context, {{ filename: semanticPackModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const button = {{ disabled: false }};
const inventoryInput = {{ value: "" }};
const packInput = {{ value: "en-es-active-v1" }};
const defaultRootInput = {{ checked: false }};
const dataRootInput = {{ value: "/tmp/lexishift-data" }};
const output = {{ textContent: "" }};
const helperCalls = [];
const statuses = [];
const confirms = [];
let rulesetUpdatedCount = 0;
let semanticStatusRefresh = null;

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async installSemanticPack(pair, options) {{
      helperCalls.push({{ pair, options }});
      return {{
        status: "ok",
        pack_id: "en-es-active-v1",
        profile_id: "semantic-alpha",
        summary: {{
          rule_count: 49,
          competition_set_count: 49
        }},
        target_paths: {{
          ruleset: "/tmp/lexishift-data/srs/profiles/semantic-alpha/srs_ruleset_en-es.json"
        }}
      }};
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-es",
  syncSelectedProfile: async (items) => ({{ items, profileId: "semantic-alpha" }}),
  confirmFn: (message) => {{
    confirms.push(message);
    return true;
  }},
  log: () => {{}},
  colors: {{
    SUCCESS: "#3c5a2a",
    ERROR: "#b42318",
    DEFAULT: "#6c675f"
  }},
  semanticPackInventoryPathInput: inventoryInput,
  semanticPackIdInput: packInput,
  semanticPackDefaultDataRootInput: defaultRootInput,
  semanticPackDataRootInput: dataRootInput,
  semanticPackInstallButton: button,
  semanticPackInstallOutput: output,
  markRulesetUpdatedNow: async () => {{
    rulesetUpdatedCount += 1;
  }},
  refreshSemanticAdmissionStatus: async (pair, profileId) => {{
    semanticStatusRefresh = {{ pair, profileId }};
  }}
}});

(async () => {{
  await workflows.installSemanticPack();

  assert.equal(button.disabled, false);
  assert.equal(confirms.length, 1);
  assert.equal(confirms[0], "Install semantic pack for en-es profile semantic-alpha? This overwrites the profile-local semantic publication files.");
  assert.deepEqual(normalize(helperCalls), [
    {{
      pair: "en-es",
      options: {{
        profileId: "semantic-alpha",
        semanticInventoryPath: "",
        packId: "en-es-active-v1",
        allowDefaultDataRoot: false,
        dataRoot: "/tmp/lexishift-data"
      }}
    }}
  ]);
  assert.equal(output.textContent.includes("Installed en-es-active-v1 for semantic-alpha"), true);
  assert.equal(output.textContent.includes("ruleset: /tmp/lexishift-data"), true);
  assert.equal(rulesetUpdatedCount, 1);
  assert.deepEqual(normalize(semanticStatusRefresh), {{
    pair: "en-es",
    profileId: "semantic-alpha"
  }});
  assert.equal(statuses[0].message, "Semantic pack installed.");
  assert.equal(statuses[0].color, "#3c5a2a");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
