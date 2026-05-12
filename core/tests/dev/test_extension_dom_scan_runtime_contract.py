from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCAN_ORDER_JS = PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/scan_order.js"
PAGE_BUDGET_TRACKER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/page_budget_tracker.js"
)
SEMANTIC_PERFORMANCE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/semantic_performance_metrics.js"
)
SEMANTIC_NODE_SCHEDULER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/semantic_node_scheduler.js"
)
DOM_SCAN_RUNTIME_JS = PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan_runtime.js"


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
            "Node DOM-scan runtime contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionDomScanRuntimeContract(unittest.TestCase):
    def test_scan_order_prioritizes_viewport_nodes_and_keeps_stable_order_without_budgets(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SCAN_ORDER_JS))};
const context = vm.createContext({{
  console,
  innerWidth: 1280,
  innerHeight: 720,
  location: {{
    origin: "https://example.com",
    pathname: "/article"
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createReorderNodesForScan =
  context.LexiShift.contentDomScanOrder.createReorderNodesForScan;
const reorderNodesForScan = createReorderNodesForScan();
const nodes = [
  {{
    id: "far-above",
    parentElement: {{
      getBoundingClientRect() {{
        return {{ top: -1200, bottom: -900, left: 0, right: 400 }};
      }}
    }}
  }},
  {{
    id: "visible-a",
    parentElement: {{
      getBoundingClientRect() {{
        return {{ top: 100, bottom: 160, left: 0, right: 400 }};
      }}
    }}
  }},
  {{
    id: "near-below",
    parentElement: {{
      getBoundingClientRect() {{
        return {{ top: 900, bottom: 980, left: 0, right: 400 }};
      }}
    }}
  }},
  {{
    id: "visible-b",
    parentElement: {{
      getBoundingClientRect() {{
        return {{ top: 320, bottom: 380, left: 0, right: 400 }};
      }}
    }}
  }}
];
const ids = (list) => list.map((entry) => entry.id);

assert.deepEqual(
  ids(reorderNodesForScan(nodes, {{ maxReplacementsPerPage: 0, maxReplacementsPerLemmaPerPage: 0 }})),
  ["visible-a", "visible-b", "near-below", "far-above"]
);
"""
        _run_node(script)

    def test_scan_order_distributes_within_viewport_band_when_page_budgets_are_active(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SCAN_ORDER_JS))};
const context = vm.createContext({{
  console,
  innerWidth: 1280,
  innerHeight: 720,
  location: {{
    origin: "https://example.com",
    pathname: "/article"
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createReorderNodesForScan =
  context.LexiShift.contentDomScanOrder.createReorderNodesForScan;
const reorderNodesForScan = createReorderNodesForScan();
const nodes = "abcdefgh".split("").map((id) => ({{
  id,
  parentElement: {{
    getBoundingClientRect() {{
      return {{ top: 100, bottom: 160, left: 0, right: 400 }};
    }}
  }}
}}));
const ids = (list) => list.map((entry) => entry.id);
const first = ids(reorderNodesForScan(nodes, {{
  maxReplacementsPerPage: 3,
  srsProfileId: "default"
}}));
const second = ids(reorderNodesForScan(nodes, {{
  maxReplacementsPerPage: 3,
  srsProfileId: "default"
}}));
const differentProfile = ids(reorderNodesForScan(nodes, {{
  maxReplacementsPerPage: 3,
  srsProfileId: "travel"
}}));

assert.deepEqual(first, second);
assert.notDeepEqual(first, ids(nodes));
assert.notDeepEqual(first, differentProfile);
assert.deepEqual([...first].sort(), ids(nodes).sort());
"""
        _run_node(script)

    def test_page_budget_tracker_seeds_from_existing_replacements_and_updates_usage(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PAGE_BUDGET_TRACKER_JS))};
const context = vm.createContext({{
  console,
  document: {{
    querySelectorAll(selector) {{
      assert.equal(selector, ".lexishift-replacement");
      return [
        {{ dataset: {{ replacement: "Hola" }}, textContent: "Hola" }},
        {{ dataset: {{ replacement: "hola" }}, textContent: "hola" }},
        {{ dataset: {{}}, textContent: "Adios" }}
      ];
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createPageBudgetTracker =
  context.LexiShift.contentDomScanPageBudgetTracker.createPageBudgetTracker;
const tracker = createPageBudgetTracker();

assert.equal(
  tracker.buildPageBudgetState({{
    maxReplacementsPerPage: 0,
    maxReplacementsPerLemmaPerPage: 0
  }}),
  null
);

const state = tracker.buildPageBudgetState({{
  maxReplacementsPerPage: "5",
  maxReplacementsPerLemmaPerPage: "2"
}});

assert.equal(state.maxTotal, 5);
assert.equal(state.maxPerLemma, 2);
assert.equal(state.usedTotal, 3);
assert.equal(state.usedByLemma.hola, 2);
assert.equal(state.usedByLemma.adios, 1);

tracker.updatePageBudgetUsage(state, ["hola", "nuevo"]);
assert.equal(state.usedTotal, 5);
assert.equal(state.usedByLemma.hola, 3);
assert.equal(state.usedByLemma.nuevo, 1);
"""
        _run_node(script)

    def test_dom_scan_runtime_builds_budget_before_reordering_and_processes_reordered_nodes(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticPerformancePath = {json.dumps(str(SEMANTIC_PERFORMANCE_JS))};
const semanticNodeSchedulerPath = {json.dumps(str(SEMANTIC_NODE_SCHEDULER_JS))};
const modulePath = {json.dumps(str(DOM_SCAN_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  document: {{
    body: {{
      innerText: "alpha beta gamma",
      textContent: "alpha beta gamma"
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  contentDomScanNodeFilters: {{
    createNodeFilters() {{
      return {{
        isEditable() {{ return false; }},
        isExcluded() {{ return false; }},
        isLexiShiftNode() {{ return false; }}
      }};
    }}
  }},
  contentDomScanPageBudgetTracker: {{
    createPageBudgetTracker() {{
      return {{
        buildPageBudgetState(settings) {{
          calls.push(["build-budget", settings.maxReplacementsPerPage]);
          return {{ maxTotal: settings.maxReplacementsPerPage, usedTotal: 0, usedByLemma: {{}} }};
        }},
        updatePageBudgetUsage() {{
          calls.push(["update-budget"]);
        }}
      }};
    }}
  }},
  contentDomScanOrder: {{
    createReorderNodesForScan() {{
      return (nodes, settings) => {{
        calls.push(["reorder", nodes.map((node) => node.id), settings.maxReplacementsPerPage]);
        return [nodes[2], nodes[0], nodes[1]];
      }};
    }}
  }},
  contentDomScanCounters: {{
        createScanCounters() {{
          const createCounter = () => ({{
            firstReplacementLatencyMs: null,
            firstVisibleReplacementLatencyMs: null,
            scanDurationMs: null,
            yieldCount: 0,
            totalNodes: 0,
            emptyNodes: 0,
            whitespaceNodes: 0,
        replacements: 0,
        nodes: 0,
        scanned: 0,
        skippedEditable: 0,
        skippedExcluded: 0,
        skippedLexi: 0,
        skippedCached: 0,
        detailLogs: 0,
        detailLimit: 0,
        detailTruncated: false,
        focusWord: "",
        focusSubstringNodes: 0,
        focusTokenNodes: 0,
        focusReplaced: 0,
        focusUnmatched: 0,
        focusSkippedEditable: 0,
        focusSkippedExcluded: 0,
        focusSkippedLexi: 0,
        focusSkippedCached: 0,
        focusSubstringNoToken: 0,
        focusDetailLogs: 0,
        focusDetailLimit: 0,
        focusDetailTruncated: false,
        semanticEligible: 0,
        semanticReady: 0,
        semanticPolicyReplaces: 0,
        semanticPolicyAbstains: 0,
        semanticPolicySoftAffordances: 0,
        semanticFallbackReplaces: 0,
        semanticFallbackAbstains: 0,
        semanticFallbackSoftAffordances: 0,
        semanticDecisionPolicyId: ""
      }});
      return {{
        createFullScanCounter() {{
          return createCounter();
        }},
        createMutationCounter() {{
          return createCounter();
        }}
      }};
    }}
  }},
  contentDomScanTextNodeProcessor: {{
    createTextNodeProcessor(options) {{
      return {{
        async processTextNode(node, counter) {{
          const budgetState = options.getPageBudgetState();
          calls.push([
            "process",
            node.id,
            budgetState ? budgetState.maxTotal : null,
            budgetState ? budgetState.usedTotal : null
          ]);
          counter.scanned += 1;
        }}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticPerformancePath, "utf8"), context, {{ filename: semanticPerformancePath }});
vm.runInContext(fs.readFileSync(semanticNodeSchedulerPath, "utf8"), context, {{ filename: semanticNodeSchedulerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createRuntime = context.LexiShift.contentDomScanRuntime.createRuntime;
let processedNodes = new WeakMap();
const runtime = createRuntime({{
  getCurrentSettings: () => ({{
    enabled: true,
    debugEnabled: false,
    maxReplacementsPerPage: 2,
    srsProfileId: "default"
  }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => processedNodes,
  setProcessedNodes: (value) => {{
    processedNodes = value;
  }},
  isApplyingChanges: () => false,
  buildReplacementFragment: () => null,
  collectTextNodes: () => [{{ id: "a" }}, {{ id: "b" }}, {{ id: "c" }}],
  log: () => {{}}
}});

(async () => {{
  const counter = await runtime.processDocument();

  assert.equal(counter.scanned, 3);
  assert.deepEqual(calls, [
    ["build-budget", 2],
    ["reorder", ["a", "b", "c"], 2],
    ["process", "c", 2, 0],
    ["process", "a", 2, 0],
    ["process", "b", 2, 0]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_dom_scan_runtime_tracks_first_replacement_and_scan_timings(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(DOM_SCAN_RUNTIME_JS))};
const logs = [];
const context = vm.createContext({{
  console,
  document: {{
    body: {{
      innerText: "alpha beta gamma",
      textContent: "alpha beta gamma"
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  contentDomScanNodeFilters: {{
    createNodeFilters() {{
      return {{
        isEditable() {{ return false; }},
        isExcluded() {{ return false; }},
        isLexiShiftNode() {{ return false; }}
      }};
    }}
  }},
  contentDomScanCounters: {{
    createScanCounters() {{
      const createCounter = () => ({{
        firstReplacementLatencyMs: Number.NaN,
        firstVisibleReplacementLatencyMs: Number.NaN,
        scanDurationMs: Number.NaN,
        yieldCount: 0,
        totalNodes: 0,
        emptyNodes: 0,
        whitespaceNodes: 0,
        replacements: 0,
        nodes: 0,
        scanned: 0,
        skippedEditable: 0,
        skippedExcluded: 0,
        skippedLexi: 0,
        skippedCached: 0,
        detailLogs: 0,
        detailLimit: 0,
        detailTruncated: false,
        focusWord: "",
        focusSubstringNodes: 0,
        focusTokenNodes: 0,
        focusReplaced: 0,
        focusUnmatched: 0,
        focusSkippedEditable: 0,
        focusSkippedExcluded: 0,
        focusSkippedLexi: 0,
        focusSkippedCached: 0,
        focusSubstringNoToken: 0,
        focusDetailLogs: 0,
        focusDetailLimit: 0,
        focusDetailTruncated: false,
        semanticEligible: 0,
        semanticReady: 0,
        semanticPolicyReplaces: 0,
        semanticPolicyAbstains: 0,
        semanticPolicySoftAffordances: 0,
        semanticFallbackReplaces: 0,
        semanticFallbackAbstains: 0,
        semanticFallbackSoftAffordances: 0,
        semanticDecisionPolicyId: ""
      }});
      return {{
        createFullScanCounter() {{
          return createCounter();
        }},
        createMutationCounter() {{
          return createCounter();
        }}
      }};
    }}
  }},
  contentDomScanTextNodeProcessor: {{
    createTextNodeProcessor(options) {{
      return {{
        async processTextNode(_node, counter) {{
          const scanStartedAtMs = Number.isFinite(Number(counter.scanStartedAtMs))
            ? Number(counter.scanStartedAtMs)
            : options.nowMs();
          if (!Number.isFinite(Number(counter.scanStartedAtMs))) {{
            counter.scanStartedAtMs = scanStartedAtMs;
          }}
          if (!Number.isFinite(Number(counter.firstReplacementLatencyMs))) {{
            counter.firstReplacementLatencyMs = options.nowMs() - scanStartedAtMs;
          }}
          counter.replacements += 1;
          counter.nodes += 1;
          counter.scanned += 1;
        }}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createRuntime = context.LexiShift.contentDomScanRuntime.createRuntime;
let nowValue = 100;
const runtime = createRuntime({{
  nowMs: () => {{
    nowValue += 5;
    return nowValue;
  }},
  getCurrentSettings: () => ({{
    enabled: true,
    debugEnabled: true
  }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => new WeakMap(),
  setProcessedNodes: () => {{}},
  isApplyingChanges: () => false,
  buildReplacementFragment: () => null,
  collectTextNodes: () => [{{ id: "a" }}],
  log: (...args) => logs.push(args)
}});

(async () => {{
  const counter = await runtime.processDocument();
  assert.equal(counter.replacements, 1);
  assert.equal(counter.firstReplacementLatencyMs, 5);
  assert.equal(Number.isNaN(counter.firstVisibleReplacementLatencyMs), true);
  assert.equal(counter.scanDurationMs, 10);
  assert.equal(counter.yieldCount, 0);
  assert.equal(logs.some((entry) => entry[0] === "Scan timing:"), true);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_dom_scan_runtime_queues_semantic_nodes_concurrently_without_page_budget(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticPerformancePath = {json.dumps(str(SEMANTIC_PERFORMANCE_JS))};
const semanticNodeSchedulerPath = {json.dumps(str(SEMANTIC_NODE_SCHEDULER_JS))};
const modulePath = {json.dumps(str(DOM_SCAN_RUNTIME_JS))};
const calls = [];
const pending = [];
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout,
  document: {{
    body: {{
      innerText: "castle fortified",
      textContent: "castle fortified"
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  contentDomScanTextNodeProcessor: {{
    createTextNodeProcessor(options) {{
      return {{
        async processTextNode(node, counter) {{
          calls.push(["process", node.id]);
          counter.scanned += 1;
          await options.semanticGateRuntime.admitMatches({{ text: node.id, matches: [node.id] }});
          calls.push(["done", node.id]);
        }}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticPerformancePath, "utf8"), context, {{ filename: semanticPerformancePath }});
vm.runInContext(fs.readFileSync(semanticNodeSchedulerPath, "utf8"), context, {{ filename: semanticNodeSchedulerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const semanticGateRuntime = {{
  admitMatches(payload) {{
    calls.push(["admit", payload.text]);
    return new Promise((resolve, reject) => {{
      const timeout = setTimeout(() => reject(new Error("semantic calls were not queued together")), 100);
      pending.push({{ resolve, timeout }});
      if (pending.length === 2) {{
        for (const entry of pending.splice(0)) {{
          clearTimeout(entry.timeout);
          entry.resolve({{ matches: [], decisionMap: new Map(), summary: null }});
        }}
      }}
    }});
  }}
}};

const runtime = context.LexiShift.contentDomScanRuntime.createRuntime({{
  getCurrentSettings: () => ({{
    enabled: true,
    debugEnabled: false,
    srsSemanticAdmissionEnabled: true
  }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => new WeakMap(),
  setProcessedNodes: () => {{}},
  isApplyingChanges: () => false,
  buildReplacementFragment: () => null,
  semanticGateRuntime,
  collectTextNodes: () => [{{ id: "castle" }}, {{ id: "fortified" }}],
  log: () => {{}}
}});

(async () => {{
  const counter = await runtime.processDocument();
  assert.equal(counter.scanned, 2);
  assert.equal(counter.semanticScanNodeBatchCalls, 1);
  assert.equal(counter.semanticScanNodeCount, 2);
  assert.equal(counter.semanticScanNodeBatchMinSize, 2);
  assert.equal(counter.semanticScanNodeBatchMaxSize, 2);
  assert.equal(counter.semanticScanNodeConcurrentBatches, 1);
  assert.equal(counter.semanticScanNodeSerialBatches, 0);
  assert.equal(counter.semanticScanNodeSerialBudgetBatches, 0);
  assert.deepEqual(calls.slice(0, 4), [
    ["process", "castle"],
    ["admit", "castle"],
    ["process", "fortified"],
    ["admit", "fortified"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_dom_scan_runtime_reports_page_budget_serial_semantic_scheduling(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticPerformancePath = {json.dumps(str(SEMANTIC_PERFORMANCE_JS))};
const semanticNodeSchedulerPath = {json.dumps(str(SEMANTIC_NODE_SCHEDULER_JS))};
const modulePath = {json.dumps(str(DOM_SCAN_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout,
  document: {{
    body: {{
      innerText: "castle fortified",
      textContent: "castle fortified"
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  contentDomScanPageBudgetTracker: {{
    createPageBudgetTracker() {{
      return {{
        buildPageBudgetState() {{
          return {{ maxTotal: 10, maxPerLemma: 1, usedTotal: 0, usedByLemma: {{}} }};
        }},
        updatePageBudgetUsage() {{}}
      }};
    }}
  }},
  contentDomScanTextNodeProcessor: {{
    createTextNodeProcessor(options) {{
      return {{
        async processTextNode(node, counter) {{
          calls.push(["process", node.id]);
          counter.scanned += 1;
          await options.semanticGateRuntime.admitMatches({{ text: node.id, matches: [node.id] }});
          calls.push(["done", node.id]);
        }}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticPerformancePath, "utf8"), context, {{ filename: semanticPerformancePath }});
vm.runInContext(fs.readFileSync(semanticNodeSchedulerPath, "utf8"), context, {{ filename: semanticNodeSchedulerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const semanticGateRuntime = {{
  async admitMatches(payload) {{
    calls.push(["admit", payload.text]);
    return {{ matches: [], decisionMap: new Map(), summary: null }};
  }}
}};

const runtime = context.LexiShift.contentDomScanRuntime.createRuntime({{
  getCurrentSettings: () => ({{
    enabled: true,
    debugEnabled: false,
    srsSemanticAdmissionEnabled: true,
    maxReplacementsPerPage: 10,
    maxReplacementsPerLemmaPerPage: 1
  }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => new WeakMap(),
  setProcessedNodes: () => {{}},
  isApplyingChanges: () => false,
  buildReplacementFragment: () => null,
  semanticGateRuntime,
  collectTextNodes: () => [{{ id: "castle" }}, {{ id: "fortified" }}],
  log: () => {{}}
}});

(async () => {{
  const counter = await runtime.processDocument();
  assert.equal(counter.scanned, 2);
  assert.equal(counter.semanticScanNodeBatchCalls, 2);
  assert.equal(counter.semanticScanNodeCount, 2);
  assert.equal(counter.semanticScanNodeBatchMinSize, 1);
  assert.equal(counter.semanticScanNodeBatchMaxSize, 1);
  assert.equal(counter.semanticScanNodeConcurrentBatches, 0);
  assert.equal(counter.semanticScanNodeSerialBatches, 2);
  assert.equal(counter.semanticScanNodeSerialBudgetBatches, 2);
  assert.deepEqual(calls, [
    ["process", "castle"],
    ["admit", "castle"],
    ["done", "castle"],
    ["process", "fortified"],
    ["admit", "fortified"],
    ["done", "fortified"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_dom_scan_runtime_prefetches_semantic_nodes_concurrently_with_page_budget(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticPerformancePath = {json.dumps(str(SEMANTIC_PERFORMANCE_JS))};
const semanticNodeSchedulerPath = {json.dumps(str(SEMANTIC_NODE_SCHEDULER_JS))};
const modulePath = {json.dumps(str(DOM_SCAN_RUNTIME_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout,
  document: {{
    body: {{
      innerText: "castle fortified",
      textContent: "castle fortified"
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  contentDomScanPageBudgetTracker: {{
    createPageBudgetTracker() {{
      return {{
        buildPageBudgetState() {{
          return {{ maxTotal: 10, maxPerLemma: 1, usedTotal: 0, usedByLemma: {{}} }};
        }},
        updatePageBudgetUsage() {{}}
      }};
    }}
  }},
  contentDomScanTextNodeProcessor: {{
    createTextNodeProcessor(options) {{
      return {{
        async preflightSemanticTextNode(node, counter, runOptions) {{
          assert.equal(runOptions.semanticPreflightBudget.maxTotal, 10);
          assert.equal(runOptions.semanticPreflightBudget.maxPerLemma, 1);
          calls.push(["preflight", node.id]);
          await options.semanticGateRuntime.admitMatches({{ text: node.id, matches: [node.id] }});
          calls.push(["preflight-done", node.id]);
          return {{
            semanticResultOverride: {{
              allowedMatchSignatures: new Set([node.id]),
              decisionBySignature: new Map()
            }}
          }};
        }},
        async processTextNode(node, counter, runOptions) {{
          calls.push(["process", node.id, Boolean(runOptions && runOptions.semanticResultOverride)]);
          counter.scanned += 1;
        }}
      }};
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticPerformancePath, "utf8"), context, {{ filename: semanticPerformancePath }});
vm.runInContext(fs.readFileSync(semanticNodeSchedulerPath, "utf8"), context, {{ filename: semanticNodeSchedulerPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const semanticGateRuntime = {{
  async admitMatches(payload) {{
    calls.push(["admit", payload.text]);
    return {{ matches: [], decisionMap: new Map(), summary: null }};
  }}
}};

const runtime = context.LexiShift.contentDomScanRuntime.createRuntime({{
  getCurrentSettings: () => ({{
    enabled: true,
    debugEnabled: false,
    srsSemanticAdmissionEnabled: true,
    maxReplacementsPerPage: 10,
    maxReplacementsPerLemmaPerPage: 1
  }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => new WeakMap(),
  setProcessedNodes: () => {{}},
  isApplyingChanges: () => false,
  buildReplacementFragment: () => null,
  semanticGateRuntime,
  collectTextNodes: () => [{{ id: "castle" }}, {{ id: "fortified" }}],
  log: () => {{}}
}});

(async () => {{
  const counter = await runtime.processDocument();
  assert.equal(counter.scanned, 2);
  assert.equal(counter.semanticScanNodeBatchCalls, 1);
  assert.equal(counter.semanticScanNodeCount, 2);
  assert.equal(counter.semanticScanNodeBatchMinSize, 2);
  assert.equal(counter.semanticScanNodeBatchMaxSize, 2);
  assert.equal(counter.semanticScanNodeConcurrentBatches, 1);
  assert.equal(counter.semanticScanNodeSerialBatches, 0);
  assert.equal(counter.semanticScanNodeSerialBudgetBatches, 0);
  assert.deepEqual(calls, [
    ["preflight", "castle"],
    ["admit", "castle"],
    ["preflight", "fortified"],
    ["admit", "fortified"],
    ["preflight-done", "castle"],
    ["preflight-done", "fortified"],
    ["process", "castle", true],
    ["process", "fortified", true]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
