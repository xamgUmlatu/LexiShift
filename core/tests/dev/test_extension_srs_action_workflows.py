from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLANNING_STATE_JS = PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/planning_state.js"
ADMISSION_PREVIEW_WORKFLOW_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/admission_preview_workflow.js"
)
REBALANCE_WORKFLOW_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/rebalance_workflow.js"
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
            f"Node workflow test failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


class TestExtensionSrsActionWorkflows(unittest.TestCase):
    def test_planning_state_normalizes_unsaved_admission_overrides(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PLANNING_STATE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createResolver = context.LexiShift.optionsSrsPlanningState.createResolver;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const settingsManager = {{
  defaults: {{
    srsMaxActive: 20,
    srsBootstrapTopN: 800,
    srsInitialActiveCount: 40
  }},
  getSrsProfile() {{
    return {{
      profileId: "default",
      srsMaxActive: 20,
      srsBootstrapTopN: 800,
      srsInitialActiveCount: 40
    }};
  }},
  getSrsProfileSignals() {{
    return {{
      interests: ["animals"],
      objectives: [],
      proficiency: {{ estimated_value: 0.25 }},
      difficultyPreferences: {{ target_challenge_center: 0.35 }},
      empiricalTrends: {{}},
      sourcePreferences: {{}}
    }};
  }},
  resolveSrsSetSizing(raw, defaults) {{
    return {{
      srsBootstrapTopN: Number.parseInt(raw.srsBootstrapTopN, 10) || defaults.srsBootstrapTopN,
      srsInitialActiveCount: Number.parseInt(raw.srsInitialActiveCount, 10)
        || defaults.srsInitialActiveCount
    }};
  }},
  composeSrsPlanContext(pairKey, profile, signals, options) {{
    return {{
      pair: pairKey,
      profile_id: options.profileId,
      interests: signals.interests,
      proficiency: signals.proficiency,
      difficulty_preferences: signals.difficultyPreferences,
      constraints: {{ max_active_items: profile.srsMaxActive }},
      sizing: {{
        bootstrap_top_n: profile.srsBootstrapTopN,
        initial_active_count: profile.srsInitialActiveCount
      }}
    }};
  }}
}};

const resolver = createResolver({{
  settingsManager,
  parseInterestList: (value) => String(value || "")
    .split(",")
    .map((entry) => String(entry || "").trim())
    .filter(Boolean),
  parseOptionalPercent: (value) => {{
    const trimmed = String(value || "").trim();
    if (!trimmed) {{
      return null;
    }}
    const parsed = Number.parseFloat(trimmed);
    return Number.isFinite(parsed) ? Math.min(100, Math.max(0, parsed)) / 100 : null;
  }},
  srsMaxActiveInput: {{ value: "24" }},
  srsBootstrapTopNInput: {{ value: "900" }},
  srsInitialActiveCountInput: {{ value: "33" }},
  srsTopicInterestsInput: {{ value: "animals, travel" }},
  srsProficiencyEstimateInput: {{ value: "55" }},
  srsChallengeTargetInput: {{ value: "65" }}
}});

const result = resolver({{}}, "en-ja", {{ profileId: "default" }});

assert.equal(result.contextMeta.source, "current_form");
assert.deepEqual(
  normalize(result.contextMeta.pendingOverrides).sort(),
  [
    "bootstrap_top_n",
    "challenge_target",
    "initial_active_count",
    "interests",
    "max_active_items",
    "proficiency_estimate"
  ].sort()
);
assert.equal(result.profile.srsMaxActive, 24);
assert.equal(result.profile.srsBootstrapTopN, 900);
assert.equal(result.profile.srsInitialActiveCount, 33);
assert.deepEqual(normalize(result.profileContext), {{
  pair: "en-ja",
  profile_id: "default",
  interests: ["animals", "travel"],
  proficiency: {{ estimated_value: 0.55 }},
  difficulty_preferences: {{ target_challenge_center: 0.65 }},
  constraints: {{ max_active_items: 24 }},
  sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
}});
"""
        _run_node(script)

    def test_admission_preview_workflow_forwards_normalized_profile_context(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(ADMISSION_PREVIEW_WORKFLOW_JS))};
const context = vm.createContext({{ console, Uint32Array }});
context.globalThis = context;
context.crypto = {{
  getRandomValues(buffer) {{
    buffer[0] = 424242;
    return buffer;
  }}
}};
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

const createAdmissionPreviewWorkflow =
  context.LexiShift.optionsSrsAdmissionPreviewWorkflow.createAdmissionPreviewWorkflow;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const request = {{}};
const admissionPreviewButton = {{ disabled: false }};
const workflow = createAdmissionPreviewWorkflow({{
  settingsManager: {{
    async load() {{
      return {{ saved: true }};
    }}
  }},
  helperManager: {{
    async previewSrsAdmission(pair, sizing, options) {{
      request.pair = pair;
      request.sizing = sizing;
      request.options = options;
      return {{
        profile_id: "default",
        plan: {{ strategy: "profile_bootstrap" }},
        preview: {{ sampled: [] }}
      }};
    }}
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "default" }}),
  resolvePlanningState: () => ({{
    profile: {{
      srsBootstrapTopN: 900,
      srsInitialActiveCount: 33,
      srsMaxActive: 24
    }},
    profileContext: {{
      pair: "en-ja",
      profile_id: "default",
      interests: ["animals", "travel"],
      proficiency: {{ estimated_value: 0.55 }},
      difficulty_preferences: {{ target_challenge_center: 0.65 }},
      constraints: {{ max_active_items: 24 }},
      sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
    }},
    contextMeta: {{
      source: "current_form",
      pendingOverrides: ["interests", "proficiency_estimate", "challenge_target"]
    }}
  }}),
  preflightSrsPairResources: async () => true,
  buildAdmissionPreviewOutput: () => "",
  admissionPreviewButton,
  setAdmissionPreviewOutputText: () => {{}},
  log: () => {{}}
}});

(async () => {{
  await workflow();
  assert.equal(admissionPreviewButton.disabled, false);
  assert.equal(request.pair, "en-ja");
  assert.deepEqual(normalize(request.sizing), {{
    bootstrapTopN: 900,
    initialActiveCount: 33,
    maxActiveItemsHint: 24
  }});
  assert.equal(request.options.profileId, "default");
  assert.equal(request.options.strategy, "profile_bootstrap");
  assert.equal(request.options.objective, "bootstrap");
  assert.equal(request.options.trigger, "options_admission_preview_button");
  assert.equal(request.options.previewCount, 5);
  assert.equal(request.options.previewSamplingMode, "weighted_without_replacement");
  assert.equal(request.options.previewSeed, 424242);
  assert.deepEqual(normalize(request.options.profileContext), {{
    pair: "en-ja",
    profile_id: "default",
    interests: ["animals", "travel"],
    proficiency: {{ estimated_value: 0.55 }},
    difficulty_preferences: {{ target_challenge_center: 0.65 }},
    constraints: {{ max_active_items: 24 }},
    sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
  }});
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_rebalance_workflows_forward_normalized_profile_context(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(REBALANCE_WORKFLOW_JS))};
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

const createRebalanceWorkflows =
  context.LexiShift.optionsSrsRebalanceWorkflow.createRebalanceWorkflows;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const calls = [];
let rulesetUpdatedCount = 0;
const rebalancePreviewButton = {{ disabled: false }};
const rebalanceApplyButton = {{ disabled: false }};
const profileContext = {{
  pair: "en-ja",
  profile_id: "default",
  interests: ["animals", "travel"],
  proficiency: {{ estimated_value: 0.55 }},
  difficulty_preferences: {{ target_challenge_center: 0.65 }},
  constraints: {{ max_active_items: 24 }},
  sizing: {{ bootstrap_top_n: 900, initial_active_count: 33 }}
}};
const workflows = createRebalanceWorkflows({{
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
    async planSrsRebalance(pair, options) {{
      calls.push({{ kind: "plan", pair, options }});
      return {{
        profile_id: "default",
        plan: {{ can_execute: true }},
        summary: {{
          proposed_keep_count: 2,
          proposed_park_count: 1,
          proposed_activate_count: 3
        }}
      }};
    }},
    async applySrsRebalance(pair, options) {{
      calls.push({{ kind: "apply", pair, options }});
      return {{
        profile_id: "default",
        applied: true,
        rulegen: {{ published: true }}
      }};
    }}
  }},
  resolvePair: () => "en-ja",
  syncSelectedProfile: async (items) => ({{ items, profileId: "default" }}),
  resolvePlanningState: () => ({{
    profile: {{
      srsBootstrapTopN: 900,
      srsMaxActive: 24
    }},
    profileContext,
    contextMeta: {{
      source: "current_form",
      pendingOverrides: ["interests", "proficiency_estimate", "challenge_target"]
    }}
  }}),
  preflightSrsPairResources: async () => true,
  buildRebalanceResultOutput: () => "",
  rebalancePreviewButton,
  rebalanceApplyButton,
  setOutputText: () => {{}},
  setStatus: () => {{}},
  confirmFn: () => true,
  markRulesetUpdatedNow: async () => {{
    rulesetUpdatedCount += 1;
  }},
  log: () => {{}}
}});

(async () => {{
  await workflows.previewRebalance();
  await workflows.applyRebalance();

  assert.equal(rebalancePreviewButton.disabled, false);
  assert.equal(rebalanceApplyButton.disabled, false);
  assert.equal(calls.length, 3);

  const previewCall = calls[0];
  assert.equal(previewCall.kind, "plan");
  assert.equal(previewCall.pair, "en-ja");
  assert.equal(previewCall.options.trigger, "options_rebalance_preview_button");
  assert.equal(previewCall.options.setTopN, 900);
  assert.equal(previewCall.options.maxActiveItems, 24);
  assert.deepEqual(normalize(previewCall.options.profileContext), profileContext);

  const applyPreviewCall = calls[1];
  assert.equal(applyPreviewCall.kind, "plan");
  assert.equal(applyPreviewCall.options.trigger, "options_rebalance_apply_preview");
  assert.equal(applyPreviewCall.options.setTopN, 900);
  assert.equal(applyPreviewCall.options.maxActiveItems, 24);
  assert.deepEqual(normalize(applyPreviewCall.options.profileContext), profileContext);

  const applyCall = calls[2];
  assert.equal(applyCall.kind, "apply");
  assert.equal(applyCall.options.trigger, "options_rebalance_apply_button");
  assert.equal(applyCall.options.setTopN, 900);
  assert.equal(applyCall.options.maxActiveItems, 24);
  assert.deepEqual(normalize(applyCall.options.profileContext), profileContext);
  assert.equal(rulesetUpdatedCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)
