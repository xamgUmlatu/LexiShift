from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPLACEMENTS_JS = PROJECT_ROOT / "apps/chrome-extension/content/processing/replacements.js"
REPLACEMENT_SEMANTIC_DEBUG_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/processing/replacement_semantic_debug.js"
)
REPLACEMENT_SEMANTIC_OVERRIDE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/processing/replacement_semantic_override.js"
)
REPLACEMENT_SELECTION_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/processing/replacement_selection.js"
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
            "Node replacements contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionReplacementsContract(unittest.TestCase):
    def test_replacement_span_exposes_debug_semantic_metadata(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticDebugPath = {json.dumps(str(REPLACEMENT_SEMANTIC_DEBUG_JS))};
const modulePath = {json.dumps(str(REPLACEMENTS_JS))};
const context = vm.createContext({{
  console,
  document: {{
    createElement() {{
      return {{
        className: "",
        dataset: {{}},
        classList: {{
          add(...classes) {{
            this._classes = (this._classes || []).concat(classes);
          }}
        }},
        title: "",
        textContent: ""
      }};
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  tokenizer: {{}},
  matcher: {{}},
  replacementSelection: {{}}
}};
vm.runInContext(fs.readFileSync(semanticDebugPath, "utf8"), context, {{ filename: semanticDebugPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const span = context.LexiShift.replacements.createReplacementSpan(
  "light",
  {{
    canonicalReplacement: "luz",
    displayReplacement: "luz",
    displayScript: "",
    scriptForms: null,
    wordPackage: null
  }},
  {{
    source_phrase: "light",
    metadata: {{
      language_pair: "en-es"
    }}
  }},
  true,
  "srs",
  {{
    status: "ready",
    trigger_id: "trigger:light",
    phrase_set_id: "phrase:light",
    decision: "abstain",
    decision_source: "policy",
    reason_codes: ["active_margin_too_low", "phrase_guard_kept_original"],
    sense_id: "sense:luz",
    competition_set_id: "comp:light",
    score_margin: 0.02,
    active_score: 0.18,
    top_shadow_score: 0.16
  }}
);

assert.equal(span.dataset.semanticStatus, "ready");
assert.equal(span.dataset.semanticTriggerId, "trigger:light");
assert.equal(span.dataset.semanticPhraseSetId, "phrase:light");
assert.equal(span.dataset.semanticDecision, "abstain");
assert.equal(span.dataset.semanticDecisionSource, "policy");
assert.equal(span.dataset.semanticReasonCodes, "active_margin_too_low,phrase_guard_kept_original");
assert.equal(span.dataset.semanticSenseId, "sense:luz");
assert.equal(span.dataset.semanticCompetitionSetId, "comp:light");
assert.equal(span.dataset.semanticScoreMargin, "0.02");
assert.equal(span.dataset.semanticActiveScore, "0.18");
assert.equal(span.dataset.semanticTopShadowScore, "0.16");
assert.equal(span.dataset.lexishiftScanSkip, "true");
assert.equal(span.title, "Click to toggle original");
        """
        _run_node(script)

    def test_semantic_result_override_reuses_preflight_decisions_without_helper_call(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const semanticDebugPath = {json.dumps(str(REPLACEMENT_SEMANTIC_DEBUG_JS))};
const semanticOverridePath = {json.dumps(str(REPLACEMENT_SEMANTIC_OVERRIDE_JS))};
const selectionPath = {json.dumps(str(REPLACEMENT_SELECTION_JS))};
const modulePath = {json.dumps(str(REPLACEMENTS_JS))};
const context = vm.createContext({{
  console,
  location: {{ origin: "https://example.com", pathname: "/article" }},
  document: {{
    createDocumentFragment() {{
      return {{
        children: [],
        appendChild(child) {{
          this.children.push(child);
        }}
      }};
    }},
    createTextNode(text) {{
      return {{ nodeType: 3, textContent: text }};
    }},
    createElement() {{
      return {{
        className: "",
        dataset: {{}},
        classList: {{
          add(...classes) {{
            this._classes = (this._classes || []).concat(classes);
          }}
        }},
        title: "",
        textContent: ""
      }};
    }}
  }}
}});
context.globalThis = context;
const rules = {{
  castle: {{
    source_phrase: "castle",
    replacement: "castillo",
    priority: 1,
    metadata: {{
      language_pair: "en-es",
      lexishift_origin: "srs",
      semantic_admission: {{
        trigger_id: "trigger:castle",
        phrase_set_id: "phrase:castle",
        sense_id: "sense:castle",
        competition_set_id: "competition:castle"
      }}
    }}
  }},
  fortified: {{
    source_phrase: "fortified",
    replacement: "fortificado",
    priority: 1,
    metadata: {{
      language_pair: "en-es",
      lexishift_origin: "srs",
      semantic_admission: {{
        trigger_id: "trigger:fortified",
        phrase_set_id: "phrase:fortified",
        sense_id: "sense:fortified",
        competition_set_id: "competition:fortified"
      }}
    }}
  }}
}};
context.LexiShift = {{
  tokenizer: {{
    tokenize(text) {{
      return String(text).split(/(\\s+)/).filter(Boolean).map((part) => ({{
        kind: /^\\s+$/.test(part) ? "space" : "word",
        text: part
      }}));
    }},
    computeGapOk(_tokens, wordPositions) {{
      return wordPositions.map(() => true);
    }}
  }},
  matcher: {{
    findLongestMatch(_trie, wordTexts, _gapOk, wordIndex) {{
      const key = String(wordTexts[wordIndex] || "").toLowerCase();
      const rule = rules[key];
      return rule ? {{ startWordIndex: wordIndex, endWordIndex: wordIndex, rule }} : null;
    }},
    applyCase(replacement) {{
      return replacement;
    }}
  }}
}};
vm.runInContext(fs.readFileSync(semanticDebugPath, "utf8"), context, {{ filename: semanticDebugPath }});
vm.runInContext(fs.readFileSync(semanticOverridePath, "utf8"), context, {{ filename: semanticOverridePath }});
vm.runInContext(fs.readFileSync(selectionPath, "utf8"), context, {{ filename: selectionPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

let helperCalls = 0;
const semanticGateRuntime = {{
  async admitMatches(payload) {{
    helperCalls += 1;
    assert.equal(payload.matches.length, 2);
    const admitted = payload.matches.filter(
      (match) => match.rule.source_phrase === "fortified"
    );
    return {{
      matches: admitted,
      decisionMap: new Map(admitted.map((match) => [match, {{ decision: "replace" }}])),
      summary: {{ eligible: 2, ready: 1 }}
    }};
  }}
}};
const settings = {{
  debugEnabled: false,
  highlightEnabled: false,
  allowAdjacentReplacements: true,
  maxOnePerTextBlock: false,
  srsSemanticAdmissionEnabled: true,
  srsProfileId: "default"
}};
const text = "castle fortified";
const originResolver = (rule) => String(rule.metadata.lexishift_origin || "");
const sentenceKey = "container:1:sentence:0";
const sentenceResolver = () => ({{ sentenceKey }});
const budget = {{
  maxTotal: 1,
  maxPerLemma: 0,
  maxPerSentence: 1,
  usedTotal: 0,
  usedByLemma: {{}},
  usedBySentence: {{}}
}};

(async () => {{
  const preflight = await context.LexiShift.replacements.buildReplacementFragment(
    text,
    {{}},
    settings,
    null,
    originResolver,
    budget,
    semanticGateRuntime,
    sentenceResolver,
    {{ dryRun: true }}
  );
  assert.equal(helperCalls, 1);
  assert.ok(preflight.semanticResultOverride);

  const rendered = await context.LexiShift.replacements.buildReplacementFragment(
    text,
    {{}},
    settings,
    null,
    originResolver,
    budget,
    semanticGateRuntime,
    sentenceResolver,
    {{ semanticResultOverride: preflight.semanticResultOverride }}
  );

  assert.equal(helperCalls, 1);
  assert.equal(rendered.replacements, 1);
  assert.equal(rendered.budgetKeys.length, 1);
  assert.equal(rendered.budgetKeys[0], "fortificado");
  assert.equal(rendered.budgetEntries.length, 1);
  assert.equal(rendered.budgetEntries[0].sentenceKey, sentenceKey);
  const spans = rendered.fragment.children.filter((child) => child.dataset);
  assert.equal(spans.length, 1);
  assert.equal(spans[0].dataset.sentenceKey, sentenceKey);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
        """
        _run_node(script)

    def test_unified_budget_limits_per_sentence_and_respects_existing_usage(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const selectionPath = {json.dumps(str(REPLACEMENT_SELECTION_JS))};
const context = vm.createContext({{
  console,
  location: {{ origin: "https://example.com", pathname: "/lesson" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(selectionPath, "utf8"), context, {{ filename: selectionPath }});

const selection = context.LexiShift.replacementSelection;
function match(source, sentenceKey, wordIndex) {{
  return {{
    startWordIndex: wordIndex,
    endWordIndex: wordIndex,
    sentenceKey,
    rule: {{
      source_phrase: source,
      replacement: `translated-${{source}}`,
      metadata: {{ lexishift_origin: "ruleset", language_pair: "en-es" }}
    }}
  }};
}}

const candidates = [
  match("one", "sentence:1", 0),
  match("two", "sentence:1", 1),
  match("three", "sentence:2", 2),
  match("four", "sentence:2", 3)
];
const settings = {{
  maxOnePerTextBlock: false,
  allowAdjacentReplacements: true,
  srsProfileId: "default"
}};
const budget = {{
  maxTotal: 2,
  maxPerLemma: 0,
  maxPerSentence: 1,
  usedTotal: 0,
  usedByLemma: {{}},
  usedBySentence: {{}}
}};
const selected = selection.filterMatches(
  candidates,
  settings,
  [true, true, true, true],
  budget,
  123456
);

assert.equal(selected.length, 2);
assert.equal(
  JSON.stringify(selected.map((entry) => entry.sentenceKey).sort()),
  JSON.stringify(["sentence:1", "sentence:2"])
);

const existingUsage = selection.filterMatches(
  candidates,
  settings,
  [true, true, true, true],
  {{
    ...budget,
    usedTotal: 1,
    usedBySentence: {{ "sentence:1": 1 }}
  }},
  123456
);
assert.equal(existingUsage.length, 1);
assert.equal(existingUsage[0].sentenceKey, "sentence:2");

const pageRejections = {{}};
selection.filterMatches(
  candidates.slice(0, 3),
  settings,
  [true, true, true],
  {{
    maxTotal: 1,
    maxPerLemma: 0,
    maxPerSentence: 0,
    usedTotal: 0,
    usedByLemma: {{}},
    usedBySentence: {{}}
  }},
  123456,
  pageRejections
);
assert.deepEqual(JSON.parse(JSON.stringify(pageRejections)), {{ page: 2 }});

const repeatedLemma = [
  match("lemma-one", "sentence:3", 0),
  match("lemma-two", "sentence:4", 1)
];
repeatedLemma[0].rule.replacement = "shared-lemma";
repeatedLemma[1].rule.replacement = "shared-lemma";
const lemmaRejections = {{}};
selection.filterMatches(
  repeatedLemma,
  settings,
  [true, true],
  {{
    maxTotal: 0,
    maxPerLemma: 1,
    maxPerSentence: 0,
    usedTotal: 0,
    usedByLemma: {{}},
    usedBySentence: {{}}
  }},
  123456,
  lemmaRejections
);
assert.deepEqual(JSON.parse(JSON.stringify(lemmaRejections)), {{ lemma: 1 }});

const sentenceRejections = {{}};
selection.filterMatches(
  candidates.slice(0, 2),
  settings,
  [true, true],
  {{
    maxTotal: 0,
    maxPerLemma: 0,
    maxPerSentence: 1,
    usedTotal: 0,
    usedByLemma: {{}},
    usedBySentence: {{}}
  }},
  123456,
  sentenceRejections
);
assert.deepEqual(JSON.parse(JSON.stringify(sentenceRejections)), {{ sentence: 1 }});
"""
        _run_node(script)

    def test_page_budget_prefers_active_learning_srs_before_mature_or_future_srs(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const selectionPath = {json.dumps(str(REPLACEMENT_SELECTION_JS))};
const context = vm.createContext({{
  console,
  location: {{ origin: "https://example.com", pathname: "/lesson" }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(selectionPath, "utf8"), context, {{ filename: selectionPath }});

const selection = context.LexiShift.replacementSelection;
const nowMs = Date.parse("2026-05-26T00:00:00Z");
function match(replacement, srs) {{
  return {{
    startWordIndex: 0,
    endWordIndex: 0,
    rule: {{
      source_phrase: replacement,
      replacement,
      metadata: {{
        lexishift_origin: "srs",
        language_pair: "en-es",
        rulegen: {{ srs }}
      }}
    }}
  }};
}}

const learning = match("aprendizaje", {{
  next_due: "2026-05-25T00:00:00Z",
  in_due: true,
  scheduler_state: "learning",
  stability: 1.0
}});
const mature = match("maduro", {{
  next_due: "2026-05-25T00:00:00Z",
  in_due: true,
  scheduler_state: "review",
  stability: 30.0
}});
const future = match("futuro", {{
  next_due: "2099-01-01T00:00:00Z",
  in_due: false,
  scheduler_state: "review",
  stability: 2.0
}});

assert.equal(selection.getReplacementLoadTier(learning, nowMs), 0);
assert.equal(selection.getReplacementLoadTier(mature, nowMs), 24);
assert.equal(selection.getReplacementLoadTier(future, nowMs), 80);

const filtered = selection.filterMatches(
  [future, mature, learning],
  {{
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    srsProfileId: "default",
    srsReplacementNowMs: nowMs
  }},
  [true, true, true],
  {{ maxTotal: 1, maxPerLemma: 0, usedTotal: 0, usedByLemma: {{}} }},
  123456
);

assert.equal(filtered.length, 1);
assert.equal(filtered[0].rule.replacement, "aprendizaje");

const single = selection.filterMatches(
  [mature, learning],
  {{
    maxOnePerTextBlock: true,
    allowAdjacentReplacements: true,
    srsProfileId: "default",
    srsReplacementNowMs: nowMs
  }},
  [true, true],
  null,
  789
);

assert.equal(single.length, 1);
assert.equal(single[0].rule.replacement, "aprendizaje");
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
