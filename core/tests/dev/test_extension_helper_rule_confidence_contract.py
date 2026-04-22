from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ACTIVE_RULES_RUNTIME_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/rules/active_rules_runtime.js"
)
SRS_GATE_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_gate.js"


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
            "Node helper-rule confidence contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperRuleConfidenceContract(unittest.TestCase):
    def test_runtime_keeps_low_confidence_helper_rules_once_emitted(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const activeRulesRuntimePath = {json.dumps(str(ACTIVE_RULES_RUNTIME_JS))};
const srsGatePath = {json.dumps(str(SRS_GATE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};

vm.runInContext(fs.readFileSync(srsGatePath, "utf8"), context, {{ filename: srsGatePath }});
vm.runInContext(
  fs.readFileSync(activeRulesRuntimePath, "utf8"),
  context,
  {{ filename: activeRulesRuntimePath }}
);

const createRuntime = context.LexiShift.contentActiveRulesRuntime.createRuntime;

function tagRulesWithOrigin(rules, origin) {{
  return (Array.isArray(rules) ? rules : []).map((rule) => ({{
    ...rule,
    metadata: {{
      ...(rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {{}}),
      lexishift_origin:
        (rule && rule.metadata && rule.metadata.lexishift_origin)
        || origin
    }}
  }}));
}}

function getRuleOrigin(rule) {{
  return String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset");
}}

const runtime = createRuntime({{
  normalizeRules: (rules) => (Array.isArray(rules) ? rules : []),
  tagRulesWithOrigin,
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  helperRulesRuntime: {{
    async resolveHelperRules(pair, profileId) {{
      assert.equal(pair, "en-ja");
      assert.equal(profileId, "default");
      return {{
        source: "helper",
        error: null,
        rules: [
          {{
            source_phrase: "thin",
            replacement: "alpha",
            enabled: true,
            metadata: {{
              lexishift_origin: "srs",
              confidence: 0.05
            }}
          }},
          {{
            source_phrase: "thick",
            replacement: "beta",
            enabled: true,
            metadata: {{
              lexishift_origin: "srs",
              confidence: 0.95
            }}
          }},
          {{
            source_phrase: "disabled",
            replacement: "gamma",
            enabled: false,
            metadata: {{
              lexishift_origin: "srs",
              confidence: 0.01
            }}
          }}
        ]
      }};
    }}
  }},
  srsGate: context.LexiShift.srsGate,
  getRuleOrigin,
  ruleOriginSrs: "srs",
  ruleOriginRuleset: "ruleset"
}});

(async () => {{
  const resolution = await runtime.resolveActiveRules(
    {{
      srsEnabled: true,
      srsPair: "en-ja",
      srsProfileId: "default",
      profileRules: [],
      rules: []
    }},
    () => {{}},
    {{ helperAvailable: true }}
  );

  assert.equal(resolution.rulesSource, "local+helper");
  assert.equal(resolution.enabledRules.length, 2);
  assert.equal(resolution.activeRules.length, 2);
  assert.equal(resolution.originCounts.srs, 2);
  assert.equal(resolution.activeOriginCounts.srs, 2);
  assert.equal(resolution.srsStats.mode, "helper_ruleset");
  assert.equal(resolution.srsStats.srsActiveCount, 2);
  assert.equal(
    JSON.stringify(resolution.activeRules.map((rule) => rule.replacement).sort()),
    JSON.stringify(["alpha", "beta"])
  );
  assert.equal(
    JSON.stringify(
      resolution.activeRules.map((rule) => rule.metadata.confidence).sort((a, b) => a - b)
    ),
    JSON.stringify([0.05, 0.95])
  );
  assert.equal(
    JSON.stringify(Array.from(resolution.srsActiveLemmas).sort()),
    JSON.stringify(["alpha", "beta"])
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_runtime_auto_enables_semantic_admission_only_for_ready_coverage(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const activeRulesRuntimePath = {json.dumps(str(ACTIVE_RULES_RUNTIME_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};

vm.runInContext(
  fs.readFileSync(activeRulesRuntimePath, "utf8"),
  context,
  {{ filename: activeRulesRuntimePath }}
);

const createRuntime = context.LexiShift.contentActiveRulesRuntime.createRuntime;

function tagRulesWithOrigin(rules, origin) {{
  return (Array.isArray(rules) ? rules : []).map((rule) => ({{
    ...rule,
    metadata: {{
      ...(rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {{}}),
      lexishift_origin:
        (rule && rule.metadata && rule.metadata.lexishift_origin)
        || origin
    }}
  }}));
}}

function getRuleOrigin(rule) {{
  return String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset");
}}

const runtime = createRuntime({{
  normalizeRules: (rules) => (Array.isArray(rules) ? rules : []),
  tagRulesWithOrigin,
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  helperRulesRuntime: {{
    async resolveHelperRules(_pair, _profileId) {{
      return {{
        source: "helper",
        error: null,
        rules: [
          {{
            source_phrase: "time",
            replacement: "hora",
            enabled: true,
            metadata: {{
              lexishift_origin: "srs",
              semantic_admission: {{ schema_version: 1, status: "ready" }}
            }}
          }},
          {{
            source_phrase: "light",
            replacement: "luz",
            enabled: true,
            metadata: {{
              lexishift_origin: "srs",
              semantic_admission: {{ schema_version: 1, status: "unavailable" }}
            }}
          }}
        ]
      }};
    }},
    async resolveSemanticInventory(_pair, _profileId) {{
      return {{
        inventory: {{ schema_version: 1 }},
        source: "helper",
        error: null
      }};
    }}
  }},
  srsGate: null,
  getRuleOrigin,
  ruleOriginSrs: "srs",
  ruleOriginRuleset: "ruleset"
}});

(async () => {{
  const resolution = await runtime.resolveActiveRules(
    {{
      srsEnabled: true,
      srsPair: "en-es",
      srsProfileId: "default",
      profileRules: [],
      rules: []
    }},
    () => {{}},
    {{ helperAvailable: true }}
  );

  assert.equal(resolution.semanticRuntimeCapability, "active");
  assert.equal(resolution.semanticRuntimeReasonCode, "ready_rules_available");
  assert.equal(resolution.semanticPointerRuleCount, 2);
  assert.equal(resolution.semanticReadyRuleCount, 1);
  assert.equal(resolution.semanticAdmissionEnabled, true);
  assert.equal(resolution.semanticFallbackPolicy, "legacy_on_unavailable");
  assert.equal(resolution.semanticInventoryLoaded, true);
  assert.equal(resolution.semanticInventorySource, "helper");
  assert.equal(Number.isFinite(Number(resolution.timings.activeRulesResolveMs)), true);
  assert.equal(Number.isFinite(Number(resolution.timings.helperRulesResolveMs)), true);
  assert.equal(Number.isFinite(Number(resolution.timings.semanticInventoryResolveMs)), true);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
