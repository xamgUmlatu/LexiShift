from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAGE_MINING_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_page_mining.js"
SOURCE_MORPHOLOGY_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_source_morphology.js"
)
SOURCE_MINING_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_source_mining.js"


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
            "Node browsing page-mining test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionBrowsingPageMining(unittest.TestCase):
    def test_builds_conservative_source_mapping_signals_from_active_srs_rules(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const mining = context.LexiShift.srsBrowsingSourceMining;
const normalize = (value) => JSON.parse(JSON.stringify(value));
function srsRule(source, replacement, reading) {{
  return {{
    source_phrase: source,
    replacement,
    enabled: true,
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-ja",
      word_package: {{
        version: 1,
        language_tag: "ja",
        surface: replacement,
        reading,
        script_forms: {{ kanji: replacement, kana: reading }},
        source: {{ provider: "test" }}
      }}
    }}
  }};
}}
const rows = normalize(mining.buildSourceMappingSignals(
  "Fermentation drives this article. Blood pressure appears once. fermentation is repeated.",
  [
    srsRule("fermentation", "発酵", "はっこう"),
    srsRule("blood pressure", "血圧", "けつあつ"),
    {{ ...srsRule("fermentation", "発酵", "はっこう"), metadata: {{ lexishift_origin: "ruleset", language_pair: "en-ja" }} }},
    {{ ...srsRule("fermentation", "fermentación", ""), metadata: {{ lexishift_origin: "srs", language_pair: "en-es" }} }}
  ],
  {{ srsPair: "en-ja" }},
  {{ maxSourceCountPerTarget: 3 }}
));

assert.deepEqual(rows, [
  {{
    language_pair: "en-ja",
    lemma: "血圧",
    target_key: "血圧|けつあつ",
    target_reading: "けつあつ",
    reading_confidence: 1,
    side: "source",
    count: 1,
    observation_source: "source_mapping",
    source_mapping_confidence: 0.72
  }},
  {{
    language_pair: "en-ja",
    lemma: "発酵",
    target_key: "発酵|はっこう",
    target_reading: "はっこう",
    reading_confidence: 1,
    side: "source",
    count: 2,
    observation_source: "source_mapping",
    source_mapping_confidence: 0.58
  }}
]);
"""
        _run_node(script)

    def test_source_mapping_matches_morphology_variants_and_tunable_confidence(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const mining = context.LexiShift.srsBrowsingSourceMining;
const normalize = (value) => JSON.parse(JSON.stringify(value));
function srsRule(source, replacement, reading) {{
  return {{
    source_phrase: source,
    replacement,
    enabled: true,
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-ja",
      word_package: {{
        version: 1,
        language_tag: "ja",
        surface: replacement,
        reading,
        script_forms: {{ kanji: replacement, kana: reading }},
        source: {{ provider: "test" }}
      }}
    }}
  }};
}}

const variantTerms = mining.sourceTermVariants("fermentation", {{
  sourceSingleWordConfidence: 0.6,
  sourceDerivationConfidenceMultiplier: 0.8
}}).map((variant) => variant.term);
assert.equal(variantTerms.includes("fermented"), true);
assert.equal(variantTerms.includes("fermenting"), true);
assert.equal(variantTerms.includes("ferments"), true);

const rows = normalize(mining.buildSourceMappingSignals(
  "Fermented vegetables are fermenting in jars; the starter ferments slowly.",
  [srsRule("fermentation", "発酵", "はっこう")],
  {{ srsPair: "en-ja" }},
  {{
    sourceSingleWordConfidence: 0.6,
    sourceDerivationConfidenceMultiplier: 0.8,
    maxSourceCountPerTarget: 5
  }}
));

assert.deepEqual(rows, [
  {{
    language_pair: "en-ja",
    lemma: "発酵",
    target_key: "発酵|はっこう",
    target_reading: "はっこう",
    reading_confidence: 1,
    side: "source",
    count: 3,
    observation_source: "source_mapping",
    source_mapping_confidence: 0.48
  }}
]);
"""
        _run_node(script)

    def test_rejects_broad_or_ambiguous_source_mapping_terms(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const mining = context.LexiShift.srsBrowsingSourceMining;
const normalize = (value) => JSON.parse(JSON.stringify(value));
function srsRule(source, replacement, reading) {{
  return {{
    source_phrase: source,
    replacement,
    enabled: true,
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-ja",
      word_package: {{
        version: 1,
        language_tag: "ja",
        surface: replacement,
        reading,
        script_forms: {{ kanji: replacement, kana: reading }},
        source: {{ provider: "test" }}
      }}
    }}
  }};
}}
const rows = normalize(mining.buildSourceMappingSignals(
  "Light work can run a set of systems.",
  [
    srsRule("light", "光", "ひかり"),
    srsRule("light", "軽い", "かるい"),
    srsRule("work", "仕事", "しごと"),
    srsRule("run", "走る", "はしる"),
    srsRule("set", "組", "くみ")
  ],
  {{ srsPair: "en-ja" }},
  {{}}
));

assert.deepEqual(rows, []);
assert.deepEqual(normalize(mining.buildSourceMappingIndex(
  [
    srsRule("light", "光", "ひかり"),
    srsRule("light", "軽い", "かるい"),
    srsRule("work", "仕事", "しごと")
  ],
  {{ srsPair: "en-ja" }},
  {{}}
)), []);
"""
        _run_node(script)

    def test_collects_visible_source_text_without_hidden_or_extension_content(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

function text(value) {{
  return {{ nodeType: 3, nodeValue: value }};
}}
function element(tagName, children, options) {{
  const opts = options || {{}};
  const node = {{
    nodeType: 1,
    tagName,
    childNodes: [],
    classList: {{
      contains(name) {{
        return Array.from(opts.classNames || []).includes(name);
      }}
    }},
    closest(selector) {{
      if (
        selector.includes(".lexishift-replacement")
        && Array.from(opts.classNames || []).includes("lexishift-replacement")
      ) {{
        return node;
      }}
      if (selector.includes("data-lexishift-scan-skip") && opts.scanSkip) {{
        return node;
      }}
      return null;
    }},
    getClientRects() {{
      return [{{ width: 1, height: 1 }}];
    }}
  }};
  node.childNodes = Array.from(children || []);
  for (const child of node.childNodes) {{
    child.parentNode = node;
    child.parentElement = node;
  }}
  return node;
}}

const rootNode = element("main", [
  element("p", [text("Fermentation visible text.")]),
  element("script", [text("hidden script fermentation")]),
  element("span", [text("ignored replacement fermentation")], {{
    classNames: ["lexishift-replacement"]
  }}),
  element("span", [text("ignored skip fermentation")], {{ scanSkip: true }}),
  element("ruby", [
    text("発酵"),
    element("rt", [text("はっこう")]),
    element("rp", [text(")")])
  ])
]);

const collected = context.LexiShift.srsBrowsingSourceMining.collectVisibleSourceText(
  rootNode,
  {{ includeInvisible: true }}
);
assert.equal(collected.includes("Fermentation visible text."), true);
assert.equal(collected.includes("hidden script"), false);
assert.equal(collected.includes("ignored replacement"), false);
assert.equal(collected.includes("ignored skip"), false);
assert.equal(collected.includes("はっこう"), false);
assert.equal(collected.includes("発酵"), true);
"""
        _run_node(script)

    def test_builds_ruby_target_surface_signals_for_en_ja(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const mining = context.LexiShift.srsBrowsingPageMining;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const rows = normalize(mining.buildRubyTargetSignals(
  [
    {{ surface: "発酵", reading: "はっこう" }},
    {{ surface: "発酵", reading: "はっこう" }},
    {{ surface: "未確認", reading: "not-kana" }},
    {{ surface: "長すぎる長すぎる長すぎる長すぎる", reading: "ながすぎる" }}
  ],
  {{ srsPair: "en-ja" }},
  {{ maxCountPerTarget: 5 }}
));

assert.deepEqual(rows, [
  {{
    language_pair: "en-ja",
    lemma: "発酵",
    target_key: "発酵|はっこう",
    target_reading: "はっこう",
    side: "target",
    count: 2,
    reading_confidence: 1,
    source_mapping_confidence: 1,
    observation_source: "target_surface"
  }}
]);
assert.deepEqual(normalize(mining.buildRubyTargetSignals(
  [{{ surface: "発酵", reading: "はっこう" }}],
  {{ srsPair: "en-es" }},
  {{}}
)), []);
"""
        _run_node(script)

    def test_miner_queues_source_and_ruby_signals_on_same_reading_key(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const mining = context.LexiShift.srsBrowsingPageMining;
const normalize = (value) => JSON.parse(JSON.stringify(value));
function text(value) {{
  return {{ nodeType: 3, nodeValue: value }};
}}
function element(tagName, children, options) {{
  const opts = options || {{}};
  const node = {{
    nodeType: 1,
    tagName,
    id: opts.id || "",
    childNodes: [],
    classList: {{
      length: 0,
      contains() {{ return false; }}
    }},
    closest() {{ return null; }},
    getClientRects() {{
      return [{{ width: 1, height: 1 }}];
    }},
    querySelectorAll(selector) {{
      const matches = [];
      function visit(candidate) {{
        if (
          candidate
          && candidate.nodeType === 1
          && String(candidate.tagName || "").toLowerCase() === selector
        ) {{
          matches.push(candidate);
        }}
        for (const child of Array.from(candidate.childNodes || [])) visit(child);
      }}
      visit(node);
      return matches;
    }}
  }};
  node.childNodes = Array.from(children || []);
  for (const child of node.childNodes) {{
    child.parentNode = node;
    child.parentElement = node;
  }}
  node.textContent = opts.textContent || node.childNodes.map((child) => child.textContent || child.nodeValue || "").join("");
  return node;
}}
function srsRule(source, replacement, reading) {{
  return {{
    source_phrase: source,
    replacement,
    enabled: true,
    metadata: {{
      lexishift_origin: "srs",
      language_pair: "en-ja",
      word_package: {{
        version: 1,
        language_tag: "ja",
        surface: replacement,
        reading,
        script_forms: {{ kanji: replacement, kana: reading }}
      }}
    }}
  }};
}}

const rt = element("rt", [text("はっこう")], {{ textContent: "はっこう" }});
const ruby = element("ruby", [text("発酵"), rt]);
const rootNode = element("main", [
  text("Fermentation appears in the source page. "),
  ruby,
  text(" is also present with ruby.")
]);
const calls = [];
const miner = mining.createMiner({{
  includeInvisible: true,
  getCurrentSettings: () => ({{
    srsPair: "en-ja",
    srsBrowsingAdmissionSignalsEnabled: true
  }}),
  getSourceMiningRules: () => [srsRule("fermentation", "発酵", "はっこう")],
  browsingAdmissionSignals: {{
    recordExposureBatch(signals, settings) {{
      calls.push({{ signals: normalize(signals), settings }});
      return Promise.resolve({{ status: "queued", accepted: signals.length }});
    }}
  }}
}});

(async () => {{
  const result = await miner.mineDocument(rootNode, "unit-test");
  assert.equal(result.status, "queued");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].signals.length, 2);
  const target = calls[0].signals.find((signal) => signal.side === "target");
  const source = calls[0].signals.find((signal) => signal.side === "source");
  assert.equal(target.target_key, "発酵|はっこう");
  assert.equal(source.target_key, "発酵|はっこう");
  assert.equal(target.target_reading, "はっこう");
  assert.equal(source.target_reading, "はっこう");
  assert.equal(target.lemma, "発酵");
  assert.equal(source.lemma, "発酵");
  assert.equal(target.observation_source, "target_surface");
  assert.equal(source.observation_source, "source_mapping");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_extracts_ruby_pair_without_rt_or_rp_text(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

function text(value) {{
  return {{ nodeType: 3, nodeValue: value }};
}}
function element(tagName, children, textContent) {{
  return {{
    nodeType: 1,
    tagName,
    childNodes: children || [],
    textContent: textContent || "",
    querySelectorAll(selector) {{
      const matches = [];
      function visit(node) {{
        if (node.nodeType === 1 && String(node.tagName).toLowerCase() === selector) {{
          matches.push(node);
        }}
        for (const child of Array.from(node.childNodes || [])) visit(child);
      }}
      visit(this);
      return matches;
    }}
  }};
}}

const ruby = element("ruby", [
  text("発"),
  element("rt", [text("はっ")], "はっ"),
  text("酵"),
  element("rp", [text(")")], ")"),
  element("rt", [text("こう")], "こう")
]);
const pair = context.LexiShift.srsBrowsingPageMining.extractRubyPair(ruby);
assert.deepEqual(JSON.parse(JSON.stringify(pair)), {{ surface: "発酵", reading: "はっこう" }});
"""
        _run_node(script)

    def test_miner_dedupes_seen_ruby_targets_until_reset(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sourceMorphologyModulePath = {json.dumps(str(SOURCE_MORPHOLOGY_JS))};
const sourceModulePath = {json.dumps(str(SOURCE_MINING_JS))};
const modulePath = {json.dumps(str(PAGE_MINING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(sourceMorphologyModulePath, "utf8"),
  context,
  {{ filename: sourceMorphologyModulePath }}
);
vm.runInContext(fs.readFileSync(sourceModulePath, "utf8"), context, {{ filename: sourceModulePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const calls = [];
const mining = context.LexiShift.srsBrowsingPageMining;
const miner = mining.createMiner({{
  getCurrentSettings: () => ({{
    srsPair: "en-ja",
    srsBrowsingAdmissionSignalsEnabled: true
  }}),
  includeInvisible: true,
  browsingAdmissionSignals: {{
    recordExposureBatch(signals, settings) {{
      calls.push({{ signals: JSON.parse(JSON.stringify(signals)), settings }});
      return Promise.resolve({{ status: "queued", accepted: signals.length }});
    }}
  }}
}});
const rootNode = {{
  querySelectorAll(selector) {{
    assert.equal(selector, "ruby");
    return [
      {{
        nodeType: 1,
        tagName: "ruby",
        childNodes: [
          {{ nodeType: 3, nodeValue: "発酵" }},
          {{
            nodeType: 1,
            tagName: "rt",
            textContent: "はっこう",
            childNodes: [{{ nodeType: 3, nodeValue: "はっこう" }}]
          }}
        ],
        querySelectorAll() {{
          return [{{ textContent: "はっこう" }}];
        }}
      }}
    ];
  }}
}};

(async () => {{
  assert.equal((await miner.mineDocument(rootNode, "first")).status, "queued");
  assert.equal((await miner.mineDocument(rootNode, "second")).status, "empty");
  miner.clearSeen();
  assert.equal((await miner.mineDocument(rootNode, "third")).status, "queued");
  assert.equal(calls.length, 2);
  assert.equal(calls[0].signals[0].target_key, "発酵|はっこう");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
