from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEMANTIC_GATE_RUNTIME_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js"
)
SEMANTIC_REQUEST_CONTEXT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/semantic/semantic_request_context.js"
)
SEMANTIC_GATE_SUMMARY_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/semantic/semantic_gate_summary.js"
)
SEMANTIC_GATE_BATCH_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/semantic/semantic_gate_batch.js"
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

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
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
          decision_policy_id: "en_es_sentence_veto_v3",
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
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
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
  assert.equal(result.summary.decisionPolicyId, "en_es_sentence_veto_v3");

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

    def test_ready_match_can_use_widened_semantic_context_with_mapped_offsets(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://en.wikipedia.org/wiki/Castle" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
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
      calls.push({{ kind: "batch", payload: JSON.parse(JSON.stringify(payload)) }});
      return {{
        response: {{
          schema_version: 1,
          pair: "en-es",
          profile_id: "default",
          decision_policy_id: "en_es_sentence_veto_v3",
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
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
}});

const readyMatch = {{
  startWordIndex: 0,
  endWordIndex: 0,
  rule: {{
    source_phrase: "castle",
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-es",
      semantic_admission: {{
        schema_version: 1,
        status: "ready",
        trigger_id: "trigger:castle",
        sense_id: "sense:castillo",
        competition_set_id: "comp:castle"
      }}
    }}
  }}
}};

(async () => {{
  const result = await runtime.admitMatches({{
    text: "castle",
    tokens: [{{ text: "castle" }}],
    wordPositions: [0],
    matches: [readyMatch],
    semanticContextResolver: () => ({{
      contextText: "A castle is a type of fortified structure built during the Middle Ages.",
      matchStart: 2,
      matchEnd: 8
    }}),
    settings: {{
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});

  const batchPayload = calls.find((entry) => entry.kind === "batch").payload;
  assert.equal(batchPayload.matches.length, 1);
  assert.equal(
    batchPayload.matches[0].context_text,
    "A castle is a type of fortified structure built during the Middle Ages."
  );
  assert.equal(batchPayload.matches[0].match_start, 2);
  assert.equal(batchPayload.matches[0].match_end, 8);
  assert.equal(
    batchPayload.matches[0].context_text.slice(
      batchPayload.matches[0].match_start,
      batchPayload.matches[0].match_end
    ),
    "castle"
  );
  assert.equal(result.matches.includes(readyMatch), true);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_multiple_ready_matches_share_context_but_keep_independent_decisions(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const runtime = context.LexiShift.contentSemanticGateRuntime.createRuntime({{
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
      calls.push({{ kind: "batch", payload: JSON.parse(JSON.stringify(payload)) }});
      return {{
        response: {{
          schema_version: 1,
          pair: "en-es",
          profile_id: "default",
          decision_policy_id: "en_es_sentence_veto_v3",
          fallback_policy: "abstain_on_unavailable",
          decisions: [
            {{
              match_id: "semantic:0",
              decision: "replace",
              decision_source: "policy",
              reason_codes: ["active_margin_clear"]
            }},
            {{
              match_id: "semantic:1",
              decision: "abstain",
              decision_source: "policy",
              reason_codes: ["active_score_below_floor"]
            }}
          ]
        }},
        error: null
      }};
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
}});

function readyMatch(sourcePhrase, startWordIndex, senseId) {{
  return {{
    startWordIndex,
    endWordIndex: startWordIndex,
    rule: {{
      source_phrase: sourcePhrase,
      metadata: {{
        lexishift_origin: "srs",
        language_pair: "en-es",
        semantic_admission: {{
          schema_version: 1,
          status: "ready",
          trigger_id: `trigger:${{sourcePhrase}}`,
          sense_id: senseId,
          competition_set_id: `comp:${{sourcePhrase}}`
        }}
      }}
    }}
  }};
}}

const castleMatch = readyMatch("castle", 1, "sense:castillo");
const fortifiedMatch = readyMatch("fortified", 3, "sense:fortificado");
const sentence = "A castle is a fortified structure.";

(async () => {{
  const result = await runtime.admitMatches({{
    text: sentence,
    tokens: [
      {{ text: "A " }},
      {{ text: "castle" }},
      {{ text: " is a " }},
      {{ text: "fortified" }},
      {{ text: " structure." }}
    ],
    wordPositions: [0, 1, 2, 3, 4],
    matches: [castleMatch, fortifiedMatch],
    semanticContextResolver: (payload) => ({{
      contextText: sentence,
      matchStart: payload.matchStart,
      matchEnd: payload.matchEnd
    }}),
    settings: {{
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});

  const batchPayload = calls.find((entry) => entry.kind === "batch").payload;
  assert.equal(batchPayload.matches.length, 2);
  assert.equal(batchPayload.matches[0].context_text, sentence);
  assert.equal(batchPayload.matches[1].context_text, sentence);
  assert.equal(batchPayload.matches[0].source_phrase, "castle");
  assert.equal(batchPayload.matches[1].source_phrase, "fortified");
  assert.equal(batchPayload.matches[0].match_start, sentence.indexOf("castle"));
  assert.equal(batchPayload.matches[0].match_end, sentence.indexOf("castle") + 6);
  assert.equal(batchPayload.matches[1].match_start, sentence.indexOf("fortified"));
  assert.equal(batchPayload.matches[1].match_end, sentence.indexOf("fortified") + 9);
  assert.equal(result.matches.includes(castleMatch), true);
  assert.equal(result.matches.includes(fortifiedMatch), false);
  assert.equal(result.summary.ready, 2);
  assert.equal(result.summary.policyReplaces, 1);
  assert.equal(result.summary.policyAbstains, 1);
  assert.equal(result.summary.inventoryLookupCalls, 1);
  assert.equal(result.summary.inventoryLookupLatencyMsTotal, 4);
  assert.equal(result.summary.inventoryLookupLatencyMsMax, 4);
  assert.equal(result.summary.inventoryLookupLatencyMsAvg, 4);
  assert.equal(result.summary.helperBatchCalls, 1);
  assert.equal(result.summary.helperRequestCount, 2);
  assert.equal(result.summary.helperBatchMinSize, 2);
  assert.equal(result.summary.helperBatchMaxSize, 2);
  assert.equal(result.summary.helperLatencyMsTotal, 9);
  assert.equal(result.summary.helperLatencyMsMax, 9);
  assert.equal(result.summary.helperLatencyMsAvg, 9);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_concurrent_split_node_admissions_coalesce_when_context_matches(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://en.wikipedia.org/wiki/Castle" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const runtime = context.LexiShift.contentSemanticGateRuntime.createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory(pair, profileId) {{
      calls.push({{ kind: "inventory", pair, profileId }});
      return {{ inventory: {{ pair, profile_id: profileId }}, source: "helper" }};
    }},
    async semanticAdmitBatch(payload) {{
      calls.push({{ kind: "batch", payload: JSON.parse(JSON.stringify(payload)) }});
      return {{
        response: {{
          decision_policy_id: "en_es_sentence_veto_v3",
          decisions: [
            {{
              match_id: "semantic:0:0",
              decision: "replace",
              decision_source: "policy",
              reason_codes: ["active_margin_clear"]
            }},
            {{
              match_id: "semantic:1:0",
              decision: "abstain",
              decision_source: "policy",
              reason_codes: ["active_score_below_floor"]
            }}
          ]
        }}
      }};
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
}});

function readyMatch(sourcePhrase, senseId) {{
  return {{
    startWordIndex: 0,
    endWordIndex: 0,
    rule: {{
      source_phrase: sourcePhrase,
      metadata: {{
        lexishift_origin: "srs",
        language_pair: "en-es",
        semantic_admission: {{
          status: "ready",
          trigger_id: `trigger:${{sourcePhrase}}`,
          sense_id: senseId,
          competition_set_id: `comp:${{sourcePhrase}}`
        }}
      }}
    }}
  }};
}}

const castleMatch = readyMatch("castle", "sense:castillo");
const fortifiedMatch = readyMatch("fortified", "sense:fortificado");
const sentence = "A castle is a type of fortified structure built during the Middle Ages.";

(async () => {{
  const [castleResult, fortifiedResult] = await Promise.all([
    runtime.admitMatches({{
      text: "castle",
      tokens: [{{ text: "castle" }}],
      wordPositions: [0],
      matches: [castleMatch],
      semanticContextResolver: () => ({{
        contextText: sentence,
        matchStart: sentence.indexOf("castle"),
        matchEnd: sentence.indexOf("castle") + 6
      }}),
      settings: {{
        srsEnabled: true,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
        srsProfileId: "default",
        srsPair: "en-es"
      }}
    }}),
    runtime.admitMatches({{
      text: "fortified",
      tokens: [{{ text: "fortified" }}],
      wordPositions: [0],
      matches: [fortifiedMatch],
      semanticContextResolver: () => ({{
        contextText: sentence,
        matchStart: sentence.indexOf("fortified"),
        matchEnd: sentence.indexOf("fortified") + 9
      }}),
      settings: {{
        srsEnabled: true,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
        srsProfileId: "default",
        srsPair: "en-es"
      }}
    }})
  ]);

  assert.equal(calls.filter((entry) => entry.kind === "inventory").length, 1);
  const batchCalls = calls.filter((entry) => entry.kind === "batch");
  assert.equal(batchCalls.length, 1);
  assert.equal(batchCalls[0].payload.matches.length, 2);
  assert.deepEqual(
    batchCalls[0].payload.matches.map((match) => match.source_phrase),
    ["castle", "fortified"]
  );
  assert.equal(castleResult.matches.includes(castleMatch), true);
  assert.equal(fortifiedResult.matches.includes(fortifiedMatch), false);
  assert.equal(castleResult.summary.helperBatchCalls, 1);
  assert.equal(castleResult.summary.helperRequestCount, 2);
  assert.equal(castleResult.summary.helperBatchMinSize, 2);
  assert.equal(fortifiedResult.summary.helperBatchCalls, 0);
  assert.equal(fortifiedResult.summary.ready, 1);
  assert.equal(fortifiedResult.summary.policyAbstains, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_sequential_admissions_reuse_successful_inventory_resolution(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209, 210, 220, 229];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const runtime = context.LexiShift.contentSemanticGateRuntime.createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory(pair, profileId) {{
      calls.push({{ kind: "inventory", pair, profileId }});
      return {{ inventory: {{ pair, profile_id: profileId }}, source: "helper" }};
    }},
    async semanticAdmitBatch(payload) {{
      calls.push({{ kind: "batch", payload: JSON.parse(JSON.stringify(payload)) }});
      return {{
        response: {{
          decision_policy_id: "en_es_sentence_veto_v3",
          decisions: payload.matches.map((match) => ({{
            match_id: match.match_id,
            decision: "replace",
            decision_source: "policy",
            reason_codes: ["active_margin_clear"]
          }}))
        }}
      }};
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
}});

function readyMatch(sourcePhrase) {{
  return {{
    startWordIndex: 0,
    endWordIndex: 0,
    rule: {{
      source_phrase: sourcePhrase,
      metadata: {{
        lexishift_origin: "srs",
        language_pair: "en-es",
        semantic_admission: {{
          status: "ready",
          trigger_id: `trigger:${{sourcePhrase}}`,
          sense_id: `sense:${{sourcePhrase}}`,
          competition_set_id: `comp:${{sourcePhrase}}`
        }}
      }}
    }}
  }};
}}

async function admitWord(sourcePhrase) {{
  const match = readyMatch(sourcePhrase);
  const result = await runtime.admitMatches({{
    text: sourcePhrase,
    tokens: [{{ text: sourcePhrase }}],
    wordPositions: [0],
    matches: [match],
    settings: {{
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});
  return {{ match, result }};
}}

(async () => {{
  const first = await admitWord("castle");
  const second = await admitWord("fortified");

  assert.equal(calls.filter((entry) => entry.kind === "inventory").length, 1);
  assert.equal(calls.filter((entry) => entry.kind === "batch").length, 2);
  assert.equal(first.result.matches.includes(first.match), true);
  assert.equal(second.result.matches.includes(second.match), true);
  assert.equal(first.result.summary.inventorySource, "helper");
  assert.equal(second.result.summary.inventorySource, "helper");
  assert.equal(first.result.summary.inventoryLookupCalls, 1);
  assert.equal(first.result.summary.inventoryLookupLatencyMsTotal, 4);
  assert.equal(second.result.summary.inventoryLookupCalls, 0);
  assert.equal(second.result.summary.inventoryLookupLatencyMsTotal, 0);
  assert.equal(first.result.summary.helperBatchCalls, 1);
  assert.equal(second.result.summary.helperBatchCalls, 1);
  assert.equal(first.result.summary.helperRequestCount, 1);
  assert.equal(second.result.summary.helperRequestCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_concurrent_different_contexts_coalesce_with_per_match_fit_scope(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const nowValues = [100, 104, 200, 209];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://en.wikipedia.org/wiki/Castle" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const runtime = context.LexiShift.contentSemanticGateRuntime.createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory(pair, profileId) {{
      calls.push({{ kind: "inventory", pair, profileId }});
      return {{ inventory: {{ pair, profile_id: profileId }}, source: "helper" }};
    }},
    async semanticAdmitBatch(payload, timeoutMs) {{
      calls.push({{ kind: "batch", timeoutMs, payload: JSON.parse(JSON.stringify(payload)) }});
      return {{
        response: {{
          fit_scope: payload.fit_scope,
          decision_policy_id: "en_es_sentence_veto_v2",
          decisions: payload.matches.map((match) => ({{
            match_id: match.match_id,
            decision: "replace",
            decision_source: "policy",
            reason_codes: ["active_margin_clear"]
          }}))
        }}
      }};
    }}
  }},
  getRuleOrigin: (rule) => String(rule && rule.metadata && rule.metadata.lexishift_origin || "ruleset"),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  ruleOriginSrs: "srs",
  nowMs: () => nowValues.shift()
}});

function readyMatch(sourcePhrase) {{
  return {{
    startWordIndex: 0,
    endWordIndex: 0,
    rule: {{
      source_phrase: sourcePhrase,
      metadata: {{
        lexishift_origin: "srs",
        language_pair: "en-es",
        semantic_admission: {{
          status: "ready",
          trigger_id: `trigger:${{sourcePhrase}}`,
          sense_id: `sense:${{sourcePhrase}}`,
          competition_set_id: `comp:${{sourcePhrase}}`
        }}
      }}
    }}
  }};
}}

const castleMatch = readyMatch("castle");
const scholarMatch = readyMatch("scholars");

(async () => {{
  const [castleResult, scholarResult] = await Promise.all([
    runtime.admitMatches({{
      text: "castle",
      tokens: [{{ text: "castle" }}],
      wordPositions: [0],
      matches: [castleMatch],
      semanticContextResolver: () => ({{
        contextText: "A castle is a type of fortified structure built during the Middle Ages.",
        matchStart: 2,
        matchEnd: 8
      }}),
      settings: {{
        srsEnabled: true,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
        srsProfileId: "default",
        srsPair: "en-es"
      }}
    }}),
    runtime.admitMatches({{
      text: "Scholars",
      tokens: [{{ text: "Scholars" }}],
      wordPositions: [0],
      matches: [scholarMatch],
      semanticContextResolver: () => ({{
        contextText: "Scholars usually consider a castle to be the private fortified residence of a lord.",
        matchStart: 0,
        matchEnd: 8
      }}),
      settings: {{
        srsEnabled: true,
        srsSemanticAdmissionEnabled: true,
        srsSemanticAdmissionFallbackPolicy: "abstain_on_unavailable",
        srsProfileId: "default",
        srsPair: "en-es"
      }}
    }})
  ]);

  assert.equal(calls.filter((entry) => entry.kind === "inventory").length, 1);
  const batchCalls = calls.filter((entry) => entry.kind === "batch");
  assert.equal(batchCalls.length, 1);
  assert.equal(batchCalls[0].timeoutMs, 15000);
  assert.equal(batchCalls[0].payload.fit_scope, "per_match");
  assert.equal(batchCalls[0].payload.matches.length, 2);
  assert.notEqual(
    batchCalls[0].payload.matches[0].context_text,
    batchCalls[0].payload.matches[1].context_text
  );
  assert.equal(castleResult.matches.includes(castleMatch), true);
  assert.equal(scholarResult.matches.includes(scholarMatch), true);
  assert.equal(castleResult.summary.helperBatchCalls, 1);
  assert.equal(castleResult.summary.helperRequestCount, 2);
  assert.equal(castleResult.summary.helperBatchMaxSize, 2);
  assert.equal(scholarResult.summary.helperBatchCalls, 0);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_debug_override_can_force_visible_replace_without_changing_underlying_counts(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createRuntime = context.LexiShift.contentSemanticGateRuntime.createRuntime;
const runtime = createRuntime({{
  helperRulesRuntime: {{
    async resolveSemanticInventory() {{
      return {{
        inventory: {{ pair: "en-es", profile_id: "default" }},
        source: "helper",
        error: null
      }};
    }},
    async semanticAdmitBatch(_payload) {{
      return {{
        response: {{
          schema_version: 1,
          pair: "en-es",
          profile_id: "default",
          decision_policy_id: "en_es_sentence_veto_v3",
          decisions: [
            {{
              match_id: "semantic:0",
              decision: "abstain",
              decision_source: "policy",
              reason_codes: ["active_margin_low"]
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
      debugEnabled: true,
      debugSemanticDecisionOverride: "replace",
      srsEnabled: true,
      srsSemanticAdmissionEnabled: true,
      srsSemanticAdmissionFallbackPolicy: "legacy_on_unavailable",
      srsProfileId: "default",
      srsPair: "en-es"
    }}
  }});

  assert.equal(result.summary.eligible, 1);
  assert.equal(result.summary.ready, 1);
  assert.equal(result.summary.policyReplaces, 0);
  assert.equal(result.summary.policyAbstains, 1);
  assert.equal(result.summary.policyAbstainRate, 1);
  assert.equal(result.summary.debugDecisionOverride, "replace");
  assert.equal(result.summary.debugOverrideApplied, 1);
  assert.equal(result.matches.includes(readyMatch), true);

  const decision = result.decisionMap.get(readyMatch);
  assert.equal(decision.decision, "abstain");
  assert.equal(decision.decision_source, "policy");
  assert.equal(decision.effective_decision, "replace");
  assert.equal(decision.effective_decision_source, "debug_override");
  assert.equal(decision.debug_override, "replace");
  assert.equal(decision.debug_original_decision, "abstain");
  assert.equal(decision.debug_original_decision_source, "policy");
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

const requestContextPath = {json.dumps(str(SEMANTIC_REQUEST_CONTEXT_JS))};
const summaryPath = {json.dumps(str(SEMANTIC_GATE_SUMMARY_JS))};
const batchPath = {json.dumps(str(SEMANTIC_GATE_BATCH_JS))};
const modulePath = {json.dumps(str(SEMANTIC_GATE_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  document: {{ documentElement: {{ lang: "en" }} }},
  location: {{ href: "https://example.com/article" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(summaryPath, "utf8"), context, {{ filename: summaryPath }});
vm.runInContext(fs.readFileSync(requestContextPath, "utf8"), context, {{ filename: requestContextPath }});
vm.runInContext(fs.readFileSync(batchPath, "utf8"), context, {{ filename: batchPath }});
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
