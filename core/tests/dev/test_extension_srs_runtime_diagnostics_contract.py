from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORTER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js"
)
RUNTIME_DIAGNOSTICS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_runtime_diagnostics.js"
)
DIAGNOSTICS_METHODS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/helper/diagnostics_methods.js"
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
            "Node runtime diagnostics contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSrsRuntimeDiagnosticsContract(unittest.TestCase):
    def test_apply_diagnostics_reporter_persists_semantic_policy_metadata(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(REPORTER_JS))};
const persisted = [];
const logs = [];
const context = vm.createContext({{
  console,
  window: {{ location: {{ href: "https://example.com/page" }} }},
  document: {{ readyState: "complete", body: {{ childElementCount: 0, innerText: "" }} }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const reporter = context.LexiShift.contentApplyDiagnosticsReporter.createReporter({{
  log: (...args) => logs.push(args),
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  persistRuntimeState: (payload) => persisted.push(payload),
  getFrameInfo: () => ({{ frameType: "top" }})
}});

reporter.report({{
  currentSettings: {{
    enabled: true,
    srsEnabled: true,
    srsPair: "en-es",
    targetLanguage: "es",
    debugEnabled: true
  }},
  normalizedRules: [],
  enabledRules: [],
  activeRules: [],
  originCounts: {{ ruleset: 0, srs: 0 }},
  activeOriginCounts: {{ ruleset: 0, srs: 0 }},
  rulesSource: "helper",
  helperRulesError: null,
  srsProfileId: "default",
  srsStats: null,
  focusWord: "",
  focusRulesCount: 0,
  semanticAdmissionEnabled: true,
  semanticRuntimeCapability: "active",
  semanticRuntimeReasonCode: "ready_rules_available",
  semanticPointerRuleCount: 8,
  semanticReadyRuleCount: 5,
  semanticFallbackPolicy: "soft_affordance_on_unavailable",
  semanticInventoryLoaded: true,
  semanticInventorySource: "helper",
  semanticInventoryError: "",
  scanSummary: {{
    semanticEligible: 8,
    semanticReady: 5,
    semanticPolicyReplaces: 2,
    semanticPolicyAbstains: 1,
    semanticPolicySoftAffordances: 2,
    semanticFallbackReplaces: 0,
    semanticFallbackAbstains: 1,
    semanticFallbackSoftAffordances: 2,
    semanticDecisionPolicyId: "en_es_sentence_veto_v2"
  }}
}});

assert.equal(persisted.length, 1);
assert.equal(persisted[0].semantic_runtime_capability, "active");
assert.equal(persisted[0].semantic_runtime_reason_code, "ready_rules_available");
assert.equal(persisted[0].semantic_pointer_rule_count, 8);
assert.equal(persisted[0].semantic_ready_rule_count, 5);
assert.equal(persisted[0].semantic_matches_ready, 5);
assert.equal(persisted[0].semantic_policy_soft_affordances, 2);
assert.equal(persisted[0].semantic_fallback_soft_affordances, 2);
assert.equal(persisted[0].semantic_decision_policy_id, "en_es_sentence_veto_v2");
"""
        _run_node(script)

    def test_runtime_diagnostics_storage_roundtrips_new_semantic_fields(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(RUNTIME_DIAGNOSTICS_JS))};
const storage = {{}};
const context = vm.createContext({{
  console,
  chrome: {{
    storage: {{
      local: {{
        set(payload, callback) {{
          Object.assign(storage, payload);
          if (typeof callback === "function") {{
            callback();
          }}
        }},
        get(defaults, callback) {{
          const items = {{ ...defaults }};
          for (const [key, value] of Object.entries(storage)) {{
            items[key] = value;
          }}
          callback(items);
        }}
      }}
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const runtimeDiagnostics = context.LexiShift.srsRuntimeDiagnostics;

(async () => {{
  await runtimeDiagnostics.saveLastState({{
    pair: "en-es",
    profile_id: "default",
    semantic_runtime_capability: "published_unready",
    semantic_runtime_reason_code: "no_ready_rules",
    semantic_pointer_rule_count: 7,
    semantic_ready_rule_count: 0,
    semantic_matches_ready: 7,
    semantic_policy_soft_affordances: 3,
    semantic_fallback_soft_affordances: 2,
    semantic_decision_policy_id: "en_es_sentence_veto_v2"
  }});
  const loaded = await runtimeDiagnostics.loadLastState();
  assert.equal(loaded.semantic_runtime_capability, "published_unready");
  assert.equal(loaded.semantic_runtime_reason_code, "no_ready_rules");
  assert.equal(loaded.semantic_pointer_rule_count, 7);
  assert.equal(loaded.semantic_ready_rule_count, 0);
  assert.equal(loaded.semantic_matches_ready, 7);
  assert.equal(loaded.semantic_policy_soft_affordances, 3);
  assert.equal(loaded.semantic_fallback_soft_affordances, 2);
  assert.equal(loaded.semantic_decision_policy_id, "en_es_sentence_veto_v2");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_diagnostics_methods_surface_cache_generation_alignment(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(DIAGNOSTICS_METHODS_JS))};
const context = vm.createContext({{
  console
}});
context.globalThis = context;
context.LexiShift = {{
  helperCache: {{
    async loadRuleset() {{
      return {{ rules: [{{ replacement: "pelota" }}, {{ replacement: "baile" }}] }};
    }},
    async loadSnapshot() {{
      return {{
        generation_id: "en-es:default:abc123",
        stats: {{ target_count: 2 }}
      }};
    }},
    async loadSemanticInventory() {{
      return {{
        schema_version: 1,
        generation_id: "en-es:default:abc123",
        competition_sets: {{ a: {{}}, b: {{}} }},
        phrase_sets: {{ p: {{}} }}
      }};
    }}
  }},
  srsRuntimeDiagnostics: {{
    async loadLastState() {{
      return {{ semantic_decision_policy_id: "en_es_sentence_veto_v2" }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const proto = {{
  normalizeProfileId(value) {{
    return String(value || "").trim() || "default";
  }},
  getClient() {{
    return null;
  }},
  i18n: {{
    t(_key, _args, fallback) {{
      return fallback;
    }}
  }}
}};
context.LexiShift.installHelperDiagnosticsMethods(proto);

(async () => {{
  const result = await proto.getSrsRuntimeDiagnostics("en-es", {{ profileId: "default" }});
  assert.equal(result.cache.ruleset_exists, true);
  assert.equal(result.cache.ruleset_rules_count, 2);
  assert.equal(result.cache.snapshot_generation_id, "en-es:default:abc123");
  assert.equal(result.cache.semantic_inventory_schema_version, 1);
  assert.equal(result.cache.semantic_inventory_generation_id, "en-es:default:abc123");
  assert.equal(result.cache.semantic_inventory_competition_set_count, 2);
  assert.equal(result.cache.semantic_inventory_phrase_set_count, 1);
  assert.equal(result.cache.snapshot_semantic_generation_aligned, true);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
