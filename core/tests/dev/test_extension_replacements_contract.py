from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPLACEMENTS_JS = PROJECT_ROOT / "apps/chrome-extension/content/processing/replacements.js"


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


if __name__ == "__main__":
    unittest.main()
