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
    return {{
      matches: payload.matches,
      decisionMap: new Map(payload.matches.map((match) => [match, {{ decision: "replace" }}])),
      summary: {{ eligible: 2, ready: 2 }}
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

(async () => {{
  const preflight = await context.LexiShift.replacements.buildReplacementFragment(
    text,
    {{}},
    settings,
    null,
    originResolver,
    null,
    semanticGateRuntime,
    null,
    {{ dryRun: true }}
  );
  assert.equal(helperCalls, 1);
  assert.ok(preflight.semanticResultOverride);

  const budget = {{ maxTotal: 1, maxPerLemma: 0, usedTotal: 0, usedByLemma: {{}} }};
  const rendered = await context.LexiShift.replacements.buildReplacementFragment(
    text,
    {{}},
    settings,
    null,
    originResolver,
    budget,
    semanticGateRuntime,
    null,
    {{ semanticResultOverride: preflight.semanticResultOverride }}
  );

  assert.equal(helperCalls, 1);
  assert.equal(rendered.replacements, 1);
  assert.equal(rendered.budgetKeys.length, 1);
  assert.equal(rendered.fragment.children.filter((child) => child.dataset).length, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
