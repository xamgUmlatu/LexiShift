from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEXT_NODE_PROCESSOR_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js"
)
SEMANTIC_CONTEXT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/semantic_context.js"
)
SEMANTIC_CONTEXT_SUPPORT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/semantic_context_support.js"
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
            "Node text-node processor context test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionTextNodeProcessorContextContract(unittest.TestCase):
    def test_split_inline_paragraph_resolves_sentence_context_for_semantic_gate(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticContextPath = {json.dumps(str(SEMANTIC_CONTEXT_JS))};
const semanticContextSupportPath = {json.dumps(str(SEMANTIC_CONTEXT_SUPPORT_JS))};
const modulePath = {json.dumps(str(TEXT_NODE_PROCESSOR_JS))};
const context = vm.createContext({{
  console,
  WeakMap,
  Date,
  performance: {{ now: () => 1 }},
  innerWidth: 1200,
  innerHeight: 800
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(semanticContextSupportPath, "utf8"), context, {{ filename: semanticContextSupportPath }});
vm.runInContext(fs.readFileSync(semanticContextPath, "utf8"), context, {{ filename: semanticContextPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

function textNode(value) {{
  return {{
    nodeType: 3,
    nodeValue: value,
    parentElement: null,
    parentNode: null
  }};
}}

function element(tagName, children = []) {{
  const node = {{
    nodeType: 1,
    tagName,
    childNodes: [],
    parentElement: null,
    parentNode: null,
    hidden: false,
    isContentEditable: false,
    className: "",
    getAttribute() {{ return ""; }}
  }};
  for (const child of children) {{
    child.parentNode = node;
    child.parentElement = node;
    node.childNodes.push(child);
  }}
  return node;
}}

const leading = textNode("A ");
const castle = textNode("castle");
const middle = textNode(" is a type of ");
const fortified = textNode("fortified");
const tail = textNode(" structure built during the Middle Ages.");
element("P", [
  leading,
  element("A", [castle]),
  middle,
  element("B", [fortified]),
  tail
]);

let resolvedContext = null;
let processedNodes = new WeakMap();
const processor = context.LexiShift.contentDomScanTextNodeProcessor.createTextNodeProcessor({{
  getCurrentSettings: () => ({{ enabled: true, debugEnabled: false }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => processedNodes,
  buildReplacementFragment: async (
    text,
    trie,
    settings,
    onTextNode,
    originResolver,
    budget,
    semanticGateRuntime,
    semanticContextResolver
  ) => {{
    assert.equal(text, "castle");
    assert.equal(typeof semanticContextResolver, "function");
    resolvedContext = semanticContextResolver({{ matchStart: 0, matchEnd: 6 }});
    return null;
  }},
  semanticGateRuntime: {{}},
  log: () => {{}}
}});

(async () => {{
  await processor.processTextNode(castle, null);
  assert.ok(resolvedContext);
  assert.equal(
    resolvedContext.contextText,
    "A castle is a type of fortified structure built during the Middle Ages."
  );
  assert.equal(resolvedContext.matchStart, 2);
  assert.equal(resolvedContext.matchEnd, 8);
  assert.equal(
    resolvedContext.contextText.slice(resolvedContext.matchStart, resolvedContext.matchEnd),
    "castle"
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_semantic_context_resolver_enforces_a_hard_word_cap(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticContextPath = {json.dumps(str(SEMANTIC_CONTEXT_JS))};
const semanticContextSupportPath = {json.dumps(str(SEMANTIC_CONTEXT_SUPPORT_JS))};
const modulePath = {json.dumps(str(TEXT_NODE_PROCESSOR_JS))};
const context = vm.createContext({{
  console,
  WeakMap,
  Date,
  performance: {{ now: () => 1 }},
  innerWidth: 1200,
  innerHeight: 800
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(semanticContextSupportPath, "utf8"), context, {{ filename: semanticContextSupportPath }});
vm.runInContext(fs.readFileSync(semanticContextPath, "utf8"), context, {{ filename: semanticContextPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

function textNode(value) {{
  return {{
    nodeType: 3,
    nodeValue: value,
    parentElement: null,
    parentNode: null
  }};
}}

function element(tagName, children = []) {{
  const node = {{
    nodeType: 1,
    tagName,
    childNodes: [],
    parentElement: null,
    parentNode: null,
    hidden: false,
    isContentEditable: false,
    className: "",
    getAttribute() {{ return ""; }}
  }};
  for (const child of children) {{
    child.parentNode = node;
    child.parentElement = node;
    node.childNodes.push(child);
  }}
  return node;
}}

const castle = textNode("castle");
const longTail = textNode(
  " " + Array.from({{ length: 90 }}, (_value, index) => `word${{index}}`).join(" ")
);
element("P", [castle, longTail]);

let resolvedContext = null;
let processedNodes = new WeakMap();
const processor = context.LexiShift.contentDomScanTextNodeProcessor.createTextNodeProcessor({{
  getCurrentSettings: () => ({{ enabled: true, debugEnabled: false }}),
  getCurrentTrie: () => ({{ ready: true }}),
  getProcessedNodes: () => processedNodes,
  buildReplacementFragment: async (
    text,
    trie,
    settings,
    onTextNode,
    originResolver,
    budget,
    semanticGateRuntime,
    semanticContextResolver
  ) => {{
    resolvedContext = semanticContextResolver({{ matchStart: 0, matchEnd: 6 }});
    return null;
  }},
  semanticGateRuntime: {{}},
  log: () => {{}}
}});

(async () => {{
  await processor.processTextNode(castle, null);
  assert.ok(resolvedContext);
  const words = resolvedContext.contextText.split(/\\s+/).filter(Boolean);
  assert.ok(words.length <= 48, `expected <= 48 words, got ${{words.length}}`);
  assert.equal(words[0], "castle");
  assert.equal(
    resolvedContext.contextText.slice(resolvedContext.matchStart, resolvedContext.matchEnd),
    "castle"
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_semantic_context_resolver_handles_boundary_edge_cases(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticContextPath = {json.dumps(str(SEMANTIC_CONTEXT_JS))};
const semanticContextSupportPath = {json.dumps(str(SEMANTIC_CONTEXT_SUPPORT_JS))};
const context = vm.createContext({{
  console,
  WeakMap,
  Date,
  performance: {{ now: () => 1 }},
  innerWidth: 1200,
  innerHeight: 800
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(semanticContextSupportPath, "utf8"), context, {{ filename: semanticContextSupportPath }});
vm.runInContext(fs.readFileSync(semanticContextPath, "utf8"), context, {{ filename: semanticContextPath }});

function textNode(value) {{
  return {{
    nodeType: 3,
    nodeValue: value,
    parentElement: null,
    parentNode: null
  }};
}}

function element(tagName, children = [], options = {{}}) {{
  const attrs = options.attrs || {{}};
  const node = {{
    nodeType: 1,
    tagName,
    childNodes: [],
    parentElement: null,
    parentNode: null,
    hidden: Boolean(options.hidden),
    isContentEditable: Boolean(options.isContentEditable),
    className: options.className || "",
    getAttribute(name) {{ return attrs[name] || ""; }}
  }};
  for (const child of children) {{
    child.parentNode = node;
    child.parentElement = node;
    node.childNodes.push(child);
  }}
  return node;
}}

function resolve(textNode, matchStart, matchEnd, nodeFilters = {{}}) {{
  const resolver = context.LexiShift.contentDomScanSemanticContext.createResolver(
    textNode,
    {{ nodeFilters }}
  );
  return resolver({{ matchStart, matchEnd }});
}}

{{
  const current = textNode("castle");
  element("P", [
    textNode("The "),
    current,
    textNode(", built during the Middle Ages, guarded the town.")
  ]);

  const resolved = resolve(current, 0, 6);
  assert.equal(
    resolved.contextText,
    "The castle, built during the Middle Ages, guarded the town."
  );
  assert.equal(resolved.matchStart, 4);
  assert.equal(resolved.matchEnd, 10);
  assert.equal(resolved.contextText.slice(resolved.matchStart, resolved.matchEnd), "castle");
}}

{{
  const current = textNode("castle");
  element("P", [
    textNode("A castle stood there."),
    textNode(" Another "),
    current,
    textNode(" was rebuilt later.")
  ]);

  const resolved = resolve(current, 0, 6);
  assert.equal(resolved.contextText, "Another castle was rebuilt later.");
  assert.equal(resolved.matchStart, 8);
  assert.equal(resolved.matchEnd, 14);
  assert.equal(resolved.contextText.slice(resolved.matchStart, resolved.matchEnd), "castle");
}}

{{
  const current = textNode("castle");
  element("DIV", [
    element("P", [textNode("Navigation castle should not leak.")]),
    element("P", [current, textNode(" was rebuilt later.")])
  ]);

  const resolved = resolve(current, 0, 6);
  assert.equal(resolved.contextText, "castle was rebuilt later.");
  assert.equal(resolved.matchStart, 0);
  assert.equal(resolved.matchEnd, 6);
}}

{{
  const current = textNode("castle");
  element("P", [
    textNode("Visible "),
    element("SPAN", [textNode("hidden castle should not appear ")], {{ hidden: true }}),
    element(
      "SPAN",
      [textNode("old castle should not appear ")],
      {{ className: "lexishift-replacement" }}
    ),
    current,
    textNode(" remains visible.")
  ]);

  const resolved = resolve(current, 0, 6);
  assert.equal(resolved.contextText, "Visible castle remains visible.");
  assert.equal(resolved.matchStart, 8);
  assert.equal(resolved.matchEnd, 14);
  assert.equal(resolved.contextText.slice(resolved.matchStart, resolved.matchEnd), "castle");
}}
"""
        _run_node(script)

    def test_resolver_clips_single_node_sentences_and_reuses_block_cache(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticContextPath = {json.dumps(str(SEMANTIC_CONTEXT_JS))};
const semanticContextSupportPath = {json.dumps(str(SEMANTIC_CONTEXT_SUPPORT_JS))};
const context = vm.createContext({{
  console,
  WeakMap,
  Date,
  performance: {{ now: () => 1 }},
  innerWidth: 1200,
  innerHeight: 800
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(semanticContextSupportPath, "utf8"), context, {{ filename: semanticContextSupportPath }});
vm.runInContext(fs.readFileSync(semanticContextPath, "utf8"), context, {{ filename: semanticContextPath }});

function textNode(value) {{
  return {{
    nodeType: 3,
    nodeValue: value,
    parentElement: null,
    parentNode: null
  }};
}}

function element(tagName, children = []) {{
  const node = {{
    nodeType: 1,
    tagName,
    childNodes: [],
    parentElement: null,
    parentNode: null,
    hidden: false,
    isContentEditable: false,
    className: "",
    getAttribute() {{ return ""; }}
  }};
  for (const child of children) {{
    child.parentNode = node;
    child.parentElement = node;
    node.childNodes.push(child);
  }}
  return node;
}}

function createResolver(textNode, options = {{}}) {{
  return context.LexiShift.contentDomScanSemanticContext.createResolver(textNode, options);
}}

{{
  const value = "A castle is fortified. Scholars usually consider a castle private.";
  const node = textNode(value);
  element("P", [node]);
  const resolver = createResolver(node);

  const firstStart = value.indexOf("castle");
  const first = resolver({{ matchStart: firstStart, matchEnd: firstStart + 6 }});
  assert.equal(first.contextText, "A castle is fortified.");
  assert.equal(first.matchStart, 2);
  assert.equal(first.matchEnd, 8);

  const secondStart = value.lastIndexOf("castle");
  const second = resolver({{ matchStart: secondStart, matchEnd: secondStart + 6 }});
  assert.equal(second.contextText, "Scholars usually consider a castle private.");
  assert.equal(second.matchStart, "Scholars usually consider a ".length);
  assert.equal(second.contextText.slice(second.matchStart, second.matchEnd), "castle");
}}

{{
  const cache = context.LexiShift.contentDomScanSemanticContext.createContextCache();
  const castle = textNode("castle");
  const fortified = textNode("fortified");
  element("P", [
    textNode("A "),
    castle,
    textNode(" is a "),
    fortified,
    textNode(" structure.")
  ]);

  const castleResolver = createResolver(castle, {{ cache }});
  const fortifiedResolver = createResolver(fortified, {{ cache }});
  const castleContext = castleResolver({{ matchStart: 0, matchEnd: 6 }});
  const fortifiedContext = fortifiedResolver({{ matchStart: 0, matchEnd: 9 }});

  assert.equal(castleContext.contextText, "A castle is a fortified structure.");
  assert.equal(fortifiedContext.contextText, castleContext.contextText);
  assert.equal(castleContext.matchStart, 2);
  assert.equal(castleContext.matchEnd, 8);
  assert.equal(fortifiedContext.matchStart, "A castle is a ".length);
  assert.equal(fortifiedContext.matchEnd, "A castle is a fortified".length);
  assert.equal(cache.stats.containerBuilds, 1);
  assert.equal(cache.stats.recordReuses, 1);
  assert.equal(cache.stats.usableReuses, 2);
}}
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
