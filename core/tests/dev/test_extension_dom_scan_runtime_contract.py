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
    def test_scan_order_only_reorders_when_page_budgets_are_active(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SCAN_ORDER_JS))};
const context = vm.createContext({{
  console,
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
const nodes = "abcdefgh".split("").map((id) => ({{ id }}));
const ids = (list) => list.map((entry) => entry.id);

assert.equal(reorderNodesForScan(nodes, {{}}), nodes);
assert.equal(
  reorderNodesForScan(nodes, {{
    maxReplacementsPerPage: 0,
    maxReplacementsPerLemmaPerPage: 0
  }}),
  nodes
);

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


if __name__ == "__main__":
    unittest.main()
