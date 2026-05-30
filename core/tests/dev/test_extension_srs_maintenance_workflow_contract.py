from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAINTENANCE_WORKFLOW_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js"
)
DELETE_STORY_STATE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/delete_story_state.js"
)
WORDS_DASHBOARD_WORKFLOW_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_workflow.js"
)
WORDS_DASHBOARD_MODEL_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_model.js"
)
WORDS_DASHBOARD_RULE_DETAILS_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_rule_details.js"
)
WORDS_DASHBOARD_RENDERER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_renderer.js"
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
  assert.equal(outputs[0], "Initializing story…");
  assert.equal(outputs[1], "init:true:4:true");
  assert.equal(
    statuses[0].message,
    "Story initialized for en-ja."
  );
  assert.equal(statuses[0].color, "#3c5a2a");
  assert.equal(rulesetUpdatedCount, 1);

  await workflows.initializeSet();

  assert.equal(initializeButton.disabled, false);
  assert.equal(helperCalls.length, 2);
  assert.equal(outputs[2], "Initializing story…");
  assert.equal(outputs[3], "init:false:0:false");
  assert.equal(
    statuses[1].message,
    "Story setup checked for en-ja; no changes were applied."
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
    actionLabel: "learning word refresh"
  }});
  assert.equal(outputs[0], "Refreshing learning words…");
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
  assert.equal(helperCalls[0].options.strategy, "profile_growth");
  assert.equal(helperCalls[0].options.trigger, "options_refresh_set_button");
  assert.deepEqual(normalize(helperCalls[0].options.profileContext), {{
    pair: "en-ja",
    profile_id: "travel",
    interests: ["animals"],
    constraints: {{ max_active_items: 24 }}
  }});
  assert.equal(outputs[2], "Refreshing learning words…");
  assert.equal(outputs[3], "refresh:false:0:true");
  assert.equal(
    statuses[1].message,
    "Learning words refreshed for en-ja: no new words added."
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

const deleteStatePath = {json.dumps(str(DELETE_STORY_STATE_JS))};
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
vm.runInContext(fs.readFileSync(deleteStatePath, "utf8"), context, {{ filename: deleteStatePath }});
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
    "Deleting SRS story…"
  );
  assert.equal(
    statuses[1].message,
    "Delete failed: helper command not found. Restart helper?"
  );
  assert.equal(statuses[1].color, "#b42318");
  assert.equal(output.textContent, "stale output");
  assert.deepEqual(confirmMessages, [
    "Delete this SRS story for the current profile and language pair? This cannot be undone.",
    "Delete this SRS story for the current profile and language pair? This cannot be undone.",
    "Really delete this story's learning words, review history, and discard data?",
    "Delete this SRS story for the current profile and language pair? This cannot be undone.",
    "Really delete this story's learning words, review history, and discard data?"
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_reset_workflow_deletes_local_story_state_and_reloads_profile(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const deleteStatePath = {json.dumps(str(DELETE_STORY_STATE_JS))};
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
vm.runInContext(fs.readFileSync(deleteStatePath, "utf8"), context, {{ filename: deleteStatePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createMaintenanceWorkflows =
  context.LexiShift.optionsSrsActionMaintenanceWorkflow.createMaintenanceWorkflows;
const resetButton = {{ disabled: false }};
const output = {{ textContent: "stale output" }};
const statuses = [];
const helperCalls = [];
const deleteCalls = [];
const publishCalls = [];
const reloadCalls = [];
const normalize = (value) => JSON.parse(JSON.stringify(value));
let loadCount = 0;

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    async load() {{
      loadCount += 1;
      return {{ loadCount }};
    }},
    getSelectedSrsProfileId() {{
      return "suisui";
    }},
    async deleteSrsProfilePair(pair, options) {{
      deleteCalls.push({{ pair, options }});
    }},
    async publishSrsRuntimeProfile(pair, profile, extraUpdates, options) {{
      publishCalls.push({{ pair, profile, extraUpdates, options }});
    }}
  }},
  helperManager: {{
    async resetSrs(pair, options) {{
      helperCalls.push({{ pair, options }});
      return {{ deleted: true }};
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-es",
  confirmFn: () => true,
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
  }},
  loadSrsProfileForPair: async (items, pair, options) => {{
    reloadCalls.push({{ items, pair, options }});
  }}
}});

(async () => {{
  await workflows.resetSrsData();

  assert.equal(resetButton.disabled, false);
  assert.equal(loadCount, 2);
  assert.deepEqual(normalize(helperCalls), [
    {{ pair: "en-es", options: {{ profileId: "suisui" }} }}
  ]);
  assert.deepEqual(normalize(deleteCalls), [
    {{ pair: "en-es", options: {{ profileId: "suisui" }} }}
  ]);
  assert.deepEqual(normalize(publishCalls), [
    {{
      pair: "en-es",
      profile: {{ srsEnabled: false }},
      extraUpdates: {{ srsSelectedProfileId: "suisui" }},
      options: {{ profileId: "suisui" }}
    }}
  ]);
  assert.deepEqual(normalize(reloadCalls), [
    {{
      items: {{ loadCount: 2 }},
      pair: "en-es",
      options: {{ profileId: "suisui", forceHelperRefresh: true }}
    }}
  ]);
  assert.equal(statuses[0].message, "Deleting SRS story…");
  assert.equal(statuses[1].message, "SRS story deleted.");
  assert.equal(statuses[1].color, "#3c5a2a");
  assert.equal(output.textContent, "");
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

const wordsDashboardModelPath = {json.dumps(str(WORDS_DASHBOARD_MODEL_JS))};
const wordsDashboardRendererPath = {json.dumps(str(WORDS_DASHBOARD_RENDERER_JS))};
const wordsDashboardRuleDetailsPath = {json.dumps(str(WORDS_DASHBOARD_RULE_DETAILS_JS))};
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
vm.runInContext(fs.readFileSync(wordsDashboardModelPath, "utf8"), context, {{ filename: wordsDashboardModelPath }});
vm.runInContext(fs.readFileSync(wordsDashboardRendererPath, "utf8"), context, {{ filename: wordsDashboardRendererPath }});
vm.runInContext(fs.readFileSync(wordsDashboardRuleDetailsPath, "utf8"), context, {{ filename: wordsDashboardRuleDetailsPath }});
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
    }},
    addEventListener(type, handler) {{
      this.listeners = this.listeners || {{}};
      this.listeners[type] = handler;
    }},
    click() {{
      return this.listeners && this.listeners.click ? this.listeners.click() : undefined;
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
const searchInput = makeNode("input");
searchInput.value = "";
const statusFilterInput = makeNode("select");
statusFilterInput.value = "all";
const sortInput = makeNode("select");
sortInput.value = "source";
const pageSizeInput = makeNode("select");
pageSizeInput.value = "2";
const clearFiltersButton = makeNode("button");
const paginationRoot = makeNode("div");
paginationRoot.ownerDocument = doc;
const pageInfoRoot = makeNode("span");
pageInfoRoot.ownerDocument = doc;
const firstPageButton = makeNode("button");
const prevPageButton = makeNode("button");
const nextPageButton = makeNode("button");
const lastPageButton = makeNode("button");
const metaRoot = makeNode("div");
metaRoot.ownerDocument = doc;
const statuses = [];
const listCalls = [];
const ruleDetailsCalls = [];
const discardCalls = [];
const confirms = [];
let listCallCount = 0;

const workflows = createMaintenanceWorkflows({{
  settingsManager: {{
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async listSrsItems(pair, options) {{
      listCalls.push({{ pair, options }});
      listCallCount += 1;
      if (listCallCount > 1) {{
        return {{
          status: "ok",
          inventory_source: "inventory",
          ruleset_exists: true,
          rule_summary: {{
            enabled_rule_count: 1
          }},
          summary: {{
            total: 1,
            active: 0,
            due_now: 0,
            due_soon: 0,
            queued: 0,
            removed: 1,
            active_zero_exposure: 0,
            active_zero_feedback: 0,
            active_zero_exposure_zero_feedback: 0,
            active_zero_exposure_zero_feedback_age_unknown: 0,
            active_stale_zero_exposure_zero_feedback: 0,
            active_without_enabled_rules: 0,
            encounter_watch: 0,
            encounter_stale_age_days: 7,
            serving_now: 0,
            serving_not_due: 0,
            serving_without_enabled_rules: 0
          }},
          items: [
            {{
              item_id: "en-es:perro",
              lemma: "perro",
              display: "perro",
              reading: "perro",
              status: "discarded",
              status_label: "Discarded",
              review_count: 2,
              exposures: 3,
              serving: false,
              serving_state: "removed",
              serving_label: "Removed",
              source_label: "freq-es-cde",
              advanced: {{
                lifecycle_state: "discarded",
                lifecycle_reason: "user_blocked"
              }}
            }}
          ]
        }};
      }}
      return {{
        status: "ok",
        inventory_source: "inventory",
        ruleset_exists: true,
        rule_summary: {{
          enabled_rule_count: 4
        }},
        summary: {{
          total: 3,
          active: 2,
          due_now: 1,
          due_soon: 1,
          queued: 1,
          removed: 0,
          active_zero_exposure: 1,
          active_zero_feedback: 1,
          active_zero_exposure_zero_feedback: 1,
          active_zero_exposure_zero_feedback_age_unknown: 0,
          active_stale_zero_exposure_zero_feedback: 1,
          active_without_enabled_rules: 0,
          encounter_watch: 1,
          encounter_stale_age_days: 7,
          serving_now: 1,
          serving_not_due: 1,
          serving_without_enabled_rules: 0
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
            serving: true,
            serving_state: "replacing_now",
            serving_label: "Now",
            source_label: "freq-es-cde",
            encounter_state: {{
              zero_exposure: false,
              zero_feedback: false,
              zero_exposure_zero_feedback: false,
              zero_exposure_zero_feedback_age_unknown: false,
              stale_zero_exposure_zero_feedback: false,
              stale_age_days: 7,
              without_enabled_rules: false,
              needs_attention: false
            }},
            rule_summary: {{
              enabled_rule_count: 2,
              source_phrases: ["dog", "hound"],
              source_preview_truncated: false
            }},
            advanced: {{
              lifecycle_state: "active",
              scheduler_state: "review",
              scheduler_step: 1,
              confidence: 0.9,
              stability: 4,
              difficulty: 3
            }}
          }},
          {{
            item_id: "en-es:gato",
            lemma: "gato",
            display: "gato",
            reading: "gato",
            status: "queued",
            status_label: "Queued",
            review_count: 0,
            exposures: 1,
            serving: false,
            serving_state: "queued",
            serving_label: "Queued",
            source_label: "freq-es-cde",
            encounter_state: {{
              zero_exposure: false,
              zero_feedback: false,
              zero_exposure_zero_feedback: false,
              zero_exposure_zero_feedback_age_unknown: false,
              stale_zero_exposure_zero_feedback: false,
              stale_age_days: 7,
              without_enabled_rules: false,
              needs_attention: false
            }},
            rule_summary: {{
              enabled_rule_count: 1,
              source_phrases: ["cat"],
              source_preview_truncated: false
            }},
            advanced: {{
              lifecycle_state: "active",
              scheduler_state: "new"
            }}
          }},
          {{
            item_id: "en-es:ave",
            lemma: "ave",
            display: "ave",
            reading: "ave",
            status: "due_soon",
            status_label: "Due soon",
            due_in_seconds: 3600,
            review_count: 0,
            exposures: 0,
            serving: false,
            serving_state: "not_due",
            serving_label: "Not due",
            source_label: "freq-es-cde",
            encounter_state: {{
              zero_exposure: true,
              zero_feedback: true,
              zero_exposure_zero_feedback: true,
              zero_exposure_zero_feedback_age_unknown: false,
              stale_zero_exposure_zero_feedback: true,
              stale_age_days: 7,
              without_enabled_rules: false,
              needs_attention: true
            }},
            rule_summary: {{
              enabled_rule_count: 1,
              source_phrases: ["bird"],
              source_preview_truncated: false
            }},
            advanced: {{
              lifecycle_state: "active",
              scheduler_state: "review"
            }}
          }}
        ]
      }};
    }},
    async getSrsItemRuleDetails(pair, lemma, options) {{
      ruleDetailsCalls.push({{ pair, lemma, options }});
      return {{
        status: "ok",
        lemma,
        rule_count: 2,
        enabled_rule_count: 2,
        returned_rule_count: 2,
        limit: 50,
        truncated: false,
        rules: [
          {{
            source_phrase: "dog",
            replacement: "perro",
            enabled: true,
            priority: 5,
            case_policy: "match",
            tags: ["animal"],
            metadata: {{
              confidence: 0.92,
              source_type: "rulegen",
              word_package: {{
                pos_canonical: "noun",
                source_provider: "freq-es-cde"
              }}
            }}
          }},
          {{
            source_phrase: "hound",
            replacement: "perro",
            enabled: true,
            priority: 1,
            case_policy: "match",
            tags: [],
            metadata: {{}}
          }}
        ]
      }};
    }},
    async discardSrsItem(pair, lemma, options) {{
      discardCalls.push({{ pair, lemma, options }});
      return {{ status: "ok", lemma, reason: "user_blocked" }};
    }}
  }},
  translate: null,
  setStatus: (message, color) => {{
    statuses.push({{ message, color }});
  }},
  resolvePair: () => "en-es",
  syncSelectedProfile: async (items) => ({{ items, profileId: "alpha" }}),
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
  wordsRefreshButton: refreshButton,
  wordsAdvancedInput: {{ checked: false }},
  wordsSearchInput: searchInput,
  wordsStatusFilterInput: statusFilterInput,
  wordsSortInput: sortInput,
  wordsPageSizeInput: pageSizeInput,
  wordsClearFiltersButton: clearFiltersButton,
  wordsSummaryRoot: summaryRoot,
  wordsPaginationRoot: paginationRoot,
  wordsPageInfoRoot: pageInfoRoot,
  wordsFirstPageButton: firstPageButton,
  wordsPrevPageButton: prevPageButton,
  wordsNextPageButton: nextPageButton,
  wordsLastPageButton: lastPageButton,
  wordsMetaRoot: metaRoot,
  wordsListRoot: listRoot
}});
const metaText = () => metaRoot.children.map((child) => child.textContent).join(" ");

(async () => {{
  assert.equal(clearFiltersButton.disabled, true);
  await workflows.refreshWordsDashboard();
  assert.equal(refreshButton.disabled, false);
  assert.deepEqual(JSON.parse(JSON.stringify(listCalls)), [
    {{ pair: "en-es", options: {{ profileId: "alpha" }} }}
  ]);
  assert.equal(summaryRoot.children.length, 8);
  assert.equal(summaryRoot.children[0].children[0].textContent, "2");
  assert.equal(summaryRoot.children[3].children[0].textContent, "1");
  assert.equal(summaryRoot.children[4].children[0].textContent, "1");
  assert.equal(summaryRoot.children[5].children[0].textContent, "1");
  assert.equal(summaryRoot.children[7].children[0].textContent, "3");
  assert.equal(listRoot.children.length, 2);
  assert.equal(pageInfoRoot.textContent, "Showing 1-2 of 3 words");
  assert.equal(prevPageButton.disabled, true);
  assert.equal(nextPageButton.disabled, false);
  assert.equal(metaText().includes("Last refreshed:"), true);
  assert.equal(metaText().includes("Loaded: 3 words"), true);
  assert.equal(metaText().includes("Viewing: 3 words"), true);
  assert.equal(metaText().includes("Replacing now: 1 word"), true);
  assert.equal(metaText().includes("Encounter watch: 1 word (1 unseen/no feedback, 1 over 7d)"), true);
  assert.equal(metaText().includes("Inventory: inventory"), true);
  assert.equal(metaText().includes("Ruleset: 4 rules"), true);
  const refreshMetaLabel = metaRoot.children[0].textContent;
  assert.equal(listRoot.children[0].children.length, 5);
  assert.equal(statuses[0].message, "Loaded 3 SRS words.");
  assert.equal(listRoot.children[0].children[2].children[3].textContent, "Rules: 2");
  assert.equal(listRoot.children[0].children[2].children[5].textContent, "Replacing: Now");
  assert.equal(listRoot.children[0].children[3].textContent, "Matches: dog, hound");
  assert.equal(listRoot.children[0].children[4].className, "srs-word-actions");
  assert.equal(listRoot.children[0].children[4].children[0].textContent, "Rule details");

  await listRoot.children[0].children[4].children[0].click();
  assert.deepEqual(JSON.parse(JSON.stringify(ruleDetailsCalls)), [
    {{ pair: "en-es", lemma: "perro", options: {{ profileId: "alpha", limit: 50 }} }}
  ]);
  assert.equal(statuses[1].message, "Loaded rule details for perro.");
  assert.equal(listRoot.children[0].children[4].className, "srs-word-rule-details");
  assert.equal(
    listRoot.children[0].children[4].children[0].textContent,
    "Showing 2 of 2 published rules."
  );
  assert.equal(listRoot.children[0].children[4].children[1].children[0].textContent, "dog -> perro");

  await listRoot.children[0].children[5].children[0].click();
  assert.equal(listRoot.children[0].children.length, 5);

  await nextPageButton.click();
  assert.equal(pageInfoRoot.textContent, "Showing 3-3 of 3 words");
  assert.equal(prevPageButton.disabled, false);
  assert.equal(nextPageButton.disabled, true);
  assert.equal(listRoot.children.length, 1);
  assert.equal(listRoot.children[0].children[0].children[0].textContent, "ave");
  assert.equal(listRoot.children[0].children[2].children[6].textContent, "Watch: unseen/no feedback >7d");
  await prevPageButton.click();
  assert.equal(pageInfoRoot.textContent, "Showing 1-2 of 3 words");

  searchInput.value = "gat";
  searchInput.listeners.input();
  assert.equal(clearFiltersButton.disabled, false);
  assert.equal(listRoot.children[0].className, "srs-words-filter-note");
  assert.equal(listRoot.children[0].textContent, "Filtered to 1 of 3 words.");
  assert.equal(listRoot.children[1].children[0].children[0].textContent, "gato");
  assert.equal(pageInfoRoot.textContent, "Showing 1-1 of 1 words");
  assert.equal(metaText().includes("Viewing: 1 word"), true);
  assert.equal(metaRoot.children[0].textContent, refreshMetaLabel);

  searchInput.listeners.keydown({{ key: "Escape" }});
  assert.equal(searchInput.value, "");
  assert.equal(clearFiltersButton.disabled, true);
  assert.equal(pageInfoRoot.textContent, "Showing 1-2 of 3 words");
  assert.equal(metaRoot.children[0].textContent, refreshMetaLabel);

  searchInput.value = "hound";
  searchInput.listeners.input();
  assert.equal(listRoot.children[0].textContent, "Filtered to 1 of 3 words.");
  assert.equal(listRoot.children[1].children[0].children[0].textContent, "perro");

  clearFiltersButton.click();
  assert.equal(searchInput.value, "");
  assert.equal(statusFilterInput.value, "all");
  assert.equal(sortInput.value, "source");
  assert.equal(clearFiltersButton.disabled, true);
  assert.equal(pageInfoRoot.textContent, "Showing 1-2 of 3 words");

  searchInput.value = "";
  searchInput.listeners.input();
  statusFilterInput.value = "due";
  statusFilterInput.listeners.change();
  assert.equal(clearFiltersButton.disabled, false);
  assert.equal(listRoot.children[0].textContent, "Filtered to 2 of 3 words.");
  sortInput.value = "word";
  sortInput.listeners.change();
  assert.equal(listRoot.children[1].children[0].children[0].textContent, "ave");
  assert.equal(listRoot.children[2].children[0].children[0].textContent, "perro");

  statusFilterInput.value = "all";
  statusFilterInput.listeners.change();
  sortInput.value = "source";
  sortInput.listeners.change();
  assert.equal(clearFiltersButton.disabled, true);
  assert.equal(listRoot.children.length, 2);
  assert.equal(listRoot.children[0].children[0].children[0].textContent, "perro");

  workflows.setWordsDashboardAdvanced(true);
  assert.equal(listRoot.children.length, 2);
  assert.equal(listRoot.children[0].children.length, 6);
  assert.equal(listRoot.children[0].children[4].className, "srs-word-advanced");
  assert.equal(listRoot.children[0].children[5].className, "srs-word-actions");

  await listRoot.children[0].children[5].children[1].click();
  assert.equal(confirms.length, 1);
  assert.equal(confirms[0], "Discard perro? It will be removed from SRS and blocked from future admission until SRS data is reset.");
  assert.deepEqual(JSON.parse(JSON.stringify(discardCalls)), [
    {{ pair: "en-es", lemma: "perro", options: {{ profileId: "alpha" }} }}
  ]);
  assert.equal(listCalls.length, 2);
  assert.equal(statuses[2].message, "Discarded perro.");
  assert.equal(statuses[3].message, "Loaded 1 SRS words.");
  assert.equal(summaryRoot.children[0].children[0].textContent, "0");
  assert.equal(summaryRoot.children[6].children[0].textContent, "1");
  assert.equal(pageInfoRoot.textContent, "Showing 1-1 of 1 words");
  assert.equal(metaText().includes("Loaded: 1 word"), true);
  assert.equal(metaText().includes("Encounter watch: none"), true);
  assert.equal(listRoot.children[0].children[1].textContent, "Discarded");
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
