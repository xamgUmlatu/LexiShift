from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_JS = PROJECT_ROOT / "apps/chrome-extension/learning_dashboard_model.js"
VIEW_JS = PROJECT_ROOT / "apps/chrome-extension/learning_dashboard_view.js"
FORMATTING_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/words_dashboard_formatting.js"
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
            "Node learning dashboard page test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionLearningDashboardPage(unittest.TestCase):
    def test_model_builds_word_info_requests_and_view_glosses(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modelPath = {json.dumps(str(MODEL_JS))};
const viewPath = {json.dumps(str(VIEW_JS))};
const formattingPath = {json.dumps(str(FORMATTING_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};

vm.runInContext(fs.readFileSync(formattingPath, "utf8"), context, {{ filename: formattingPath }});
vm.runInContext(fs.readFileSync(modelPath, "utf8"), context, {{ filename: modelPath }});
vm.runInContext(fs.readFileSync(viewPath, "utf8"), context, {{ filename: viewPath }});

const model = context.LexiShift.learningDashboardModel;
const view = context.LexiShift.learningDashboardView;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const item = {{
  item_id: "en-es:perro",
  lemma: "perro",
  display: "perro",
  topic_hints: ["animals"],
  rule_summary: {{
    enabled_rule_count: 2,
    source_phrases: ["dog", "hound"]
  }},
  advanced: {{
    word_package: {{
      surface: "perro",
      pos_canonical: "noun",
      topic_hints: ["animals"]
    }}
  }}
}};

assert.deepEqual(normalize(model.createWordInfoRequest({{ item, pair: "en-es", profileId: "suisui" }})), {{
  profileId: "suisui",
  pair: "en-es",
  lemma: "perro",
  display: "perro",
  origin: "srs",
  sourcePhrase: "dog",
  wordPackage: {{
    surface: "perro",
    pos_canonical: "noun",
    topic_hints: ["animals"]
  }}
}});
assert.equal(model.resolveTopicLabel(item), "Animals");
assert.equal(model.sourcePhraseSummary(item), "dog, hound");
assert.equal(model.hasPublishedRules(item), true);
assert.equal(model.formatActivity({{ review_count: 1, exposures: 3 }}), "1 review | 3 seen");
assert.equal(model.resolveGlossPreview({{
  glosses: [
    {{ text: "dog" }},
    {{ text: "hound" }},
    {{ text: "pet" }}
  ]
}}), "dog, hound");

assert.deepEqual(normalize(view.resolveGlosses({{
  glosses: [
    {{ text: "dog", details: ["domestic animal", "canid", "extra"] }},
    {{ text: "dog", details: ["duplicate"] }},
    {{ text: "hound" }}
  ]
}})), [
  {{ text: "dog", details: ["domestic animal", "canid"] }},
  {{ text: "hound", details: [] }}
]);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
