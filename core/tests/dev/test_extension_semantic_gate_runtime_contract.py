from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEMANTIC_GATE_RUNTIME_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js"
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
            "Node semantic-gate contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSemanticGateRuntimeContract(unittest.TestCase):
    def test_gate_batches_only_ready_matches_and_counts_non_ready_fallbacks(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createRuntime = context.LexiShift.contentSemanticGateRuntime.createRuntime;
const runtime = createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory(pair, profileId) {{
      calls.push({{ kind: "inventory", pair, profileId }});
      return {{
        inventory: {{ pair: "en-es", profile_id: "default" }},
        source: "helper",
        error: null
      }};
    }},
    async semanticAdmitBatch(payload) {{
      calls.push({{
        kind: "batch",
        payload: JSON.parse(JSON.stringify(payload))
      }});
      return {{
        response: {{
          schema_version: 1,
          pair: "en-es",
          profile_id: "default",
          decision_policy_id: "en_es_sentence_veto_v1",
          fallback_policy: "abstain_on_unavailable",
          decisions: [
            {{
              match_id: "semantic:0",
              decision: "replace",
              decision_source: "policy",
              reason_codes: ["active_margin_clear"]
            }}
          ]
        }},
        error: null
      }};
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs"
}});

const readyMatch = {{
  startWordIndex: 5,
  endWordIndex: 5,
  rule: {{
    source_phrase: "bank",
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-es",
      semantic_admission: {{
        schema_version: 1,
        status: "ready",
        trigger_id: "trigger:bank",
        sense_id: "sense:banco",
        competition_set_id: "comp:bank",
        phrase_set_id: "phrase:bank"
      }}
    }}
  }}
}};
const pendingMatch = {{
  startWordIndex: 5,
  endWordIndex: 5,
  rule: {{
    source_phrase: "bank",
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-es",
      semantic_admission: {{
        schema_version: 1,
        status: "pending",
        trigger_id: "trigger:bank",
        sense_id: "sense:banco",
        competition_set_id: "comp:bank"
      }}
    }}
  }}
}};
const rulesetMatch = {{
  startWordIndex: 5,
  endWordIndex: 5,
  rule: {{
    source_phrase: "bank",
    metadata: {{
      lexishift_origin: "ruleset",
      language_pair: "en-es",
      semantic_admission: {{
        schema_version: 1,
        status: "ready"
      }}
    }}
  }}
}};
const noAdmissionMatch = {{
  startWordIndex: 5,
  endWordIndex: 5,
  rule: {{
    source_phrase: "bank",
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-es"
    }}
  }}
}};

(async () => {{
  const result = await runtime.admitMatches({{
    text: "I deposited cash at the bank yesterday.",
    tokens: [
      {{ text: "I " }},
      {{ text: "deposited " }},
      {{ text: "cash " }},
      {{ text: "at " }},
      {{ text: "the " }},
      {{ text: "bank" }},
      {{ text: " yesterday." }}
    ],
    wordPositions: [0, 1, 2, 3, 4, 5, 6],
    matches: [readyMatch, pendingMatch, rulesetMatch, noAdmissionMatch],
    settings: {{
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});

  assert.equal(calls.filter((entry) => entry.kind === "inventory").length, 1);
  assert.equal(calls.filter((entry) => entry.kind === "batch").length, 1);
  const batchPayload = calls.find((entry) => entry.kind === "batch").payload;
  assert.equal(batchPayload.matches.length, 1);
  assert.equal(batchPayload.matches[0].match_id, "semantic:0");
  assert.equal(batchPayload.matches[0].semantic_admission.status, "ready");

  assert.equal(result.summary.eligible, 2);
  assert.equal(result.summary.ready, 1);
  assert.equal(result.summary.policyReplaces, 1);
  assert.equal(result.summary.fallbackAbstains, 1);
  assert.equal(result.summary.decisionPolicyId, "en_es_sentence_veto_v1");

  assert.equal(result.matches.includes(readyMatch), true);
  assert.equal(result.matches.includes(pendingMatch), false);
  assert.equal(result.matches.includes(rulesetMatch), true);
  assert.equal(result.matches.includes(noAdmissionMatch), true);

  const pendingDecision = result.decisionMap.get(pendingMatch);
  assert.equal(pendingDecision.decision, "abstain");
  assert.equal(pendingDecision.decision_source, "fallback_policy");
  assert.deepEqual(
    JSON.parse(JSON.stringify(pendingDecision.reason_codes)),
    ["semantic_status_pending"]
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_gate_falls_back_locally_when_inventory_is_unavailable(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createRuntime = context.LexiShift.contentSemanticGateRuntime.createRuntime;
const runtime = createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory(pair, profileId) {{
      calls.push({{ kind: "inventory", pair, profileId }});
      return {{
        inventory: null,
        source: "helper",
        error: "Helper offline."
      }};
    }},
    async semanticAdmitBatch(_payload) {{
      calls.push({{ kind: "batch" }});
      throw new Error("semanticAdmitBatch should not be called when inventory is unavailable");
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs"
}});

const readyMatch = {{
  startWordIndex: 5,
  endWordIndex: 5,
  rule: {{
    source_phrase: "bank",
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-es",
      semantic_admission: {{
        schema_version: 1,
        status: "ready",
        trigger_id: "trigger:bank",
        sense_id: "sense:banco",
        competition_set_id: "comp:bank"
      }}
    }}
  }}
}};

(async () => {{
  const result = await runtime.admitMatches({{
    text: "I deposited cash at the bank yesterday.",
    tokens: [
      {{ text: "I " }},
      {{ text: "deposited " }},
      {{ text: "cash " }},
      {{ text: "at " }},
      {{ text: "the " }},
      {{ text: "bank" }},
      {{ text: " yesterday." }}
    ],
    wordPositions: [0, 1, 2, 3, 4, 5, 6],
    matches: [readyMatch],
    settings: {{
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "legacy_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});

  assert.equal(calls.filter((entry) => entry.kind === "inventory").length, 1);
  assert.equal(calls.some((entry) => entry.kind === "batch"), false);

  assert.equal(result.summary.eligible, 1);
  assert.equal(result.summary.ready, 1);
  assert.equal(result.summary.fallbackReplaces, 1);
  assert.equal(result.summary.inventorySource, "helper");
  assert.equal(result.summary.inventoryError, "Helper offline.");
  assert.equal(result.matches.includes(readyMatch), true);

  const readyDecision = result.decisionMap.get(readyMatch);
  assert.equal(readyDecision.decision, "replace");
  assert.equal(readyDecision.decision_source, "fallback_policy");
  assert.deepEqual(
    JSON.parse(JSON.stringify(readyDecision.reason_codes)),
    ["semantic_inventory_unavailable"]
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
