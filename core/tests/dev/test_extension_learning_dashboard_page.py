from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_JS = PROJECT_ROOT / "apps/chrome-extension/learning_dashboard_model.js"
VIEW_JS = PROJECT_ROOT / "apps/chrome-extension/learning_dashboard_view.js"
THEME_JS = PROJECT_ROOT / "apps/chrome-extension/learning_dashboard_theme.js"
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
assert.equal(model.pairDisplayLabel("en-es"), "English -> Español");
assert.deepEqual(normalize(model.listPracticePairs({{
  srsProfiles: {{
    suisui: {{
      srsByPair: {{
        "en-ja": {{ srsEnabled: true }},
        "en-es": {{ srsEnabled: true }},
        "en-de": {{ srsEnabled: false }}
      }}
    }}
  }}
}}, "suisui")), [
  {{ pair: "en-es", label: "English -> Español" }},
  {{ pair: "en-ja", label: "English -> 日本語" }}
]);
assert.deepEqual(normalize(model.listPracticePairs({{
  srsProfiles: {{
    suisui: {{
      srsByPair: {{}}
    }}
  }}
}}, "suisui", {{ fallbackPair: "en-ja" }})), [
  {{ pair: "en-ja", label: "English -> 日本語" }}
]);
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

    def test_view_uses_source_phrase_when_definition_lookup_fails(self) -> None:
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

function node(tagName) {{
  return {{
    tagName,
    children: [],
    className: "",
    href: "",
    rel: "",
    target: "",
    _text: "",
    get firstChild() {{ return this.children[0] || null; }},
    set textContent(value) {{ this._text = String(value || ""); }},
    get textContent() {{
      return [this._text, ...this.children.map((child) => child.textContent || "")].join("");
    }},
    appendChild(child) {{ this.children.push(child); return child; }},
    removeChild(child) {{
      const index = this.children.indexOf(child);
      if (index >= 0) this.children.splice(index, 1);
      return child;
    }}
  }};
}}

const detailRoot = node("div");
const doc = {{ createElement: node }};
const wordInfoByKey = new Map([[
  "en-ja:会社",
  {{ status: "error", error: new Error("timeout") }}
]]);
context.LexiShift.learningDashboardView.renderDetail({{
  advancedEnabled: false,
  doc,
  elements: {{ detailRoot }},
  ensureRuleDetails: () => Promise.resolve(null),
  ensureWordInfo: () => Promise.resolve(null),
  getSelectedKey: () => "en-ja:会社",
  isAdvancedEnabled: () => false,
  item: {{
    item_id: "en-ja:会社",
    lemma: "会社",
    display: "会社",
    status_label: "Learning",
    review_count: 0,
    exposures: 0,
    rule_summary: {{
      enabled_rule_count: 1,
      source_phrases: ["company"]
    }}
  }},
  renderDetail: () => {{}},
  t: (_key, _subs, fallback) => fallback,
  wordInfoByKey
}});

assert.match(detailRoot.textContent, /company/);
assert.doesNotMatch(detailRoot.textContent, /Definition unavailable/);
"""
        _run_node(script)

    def test_theme_applier_uses_selected_profile_ui_preferences(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const themePath = {json.dumps(str(THEME_JS))};
const context = vm.createContext({{ console, URL }});
context.globalThis = context;
context.document = {{
  body: {{ style: {{}} }},
  documentElement: {{ style: {{}} }}
}};
context.LexiShift = {{
  optionsProfileBackgroundUtils: {{
    normalizeBackdropColor(value) {{ return String(value || "").toLowerCase(); }},
    clampOpacity(value) {{ return Number(value); }},
    clampPositionPercent(value) {{ return Number(value); }},
    hexColorToRgb() {{ return {{ r: 68, g: 85, b: 170 }}; }}
  }}
}};

const calls = [];
context.LexiShift.optionsProfileBackgroundPageBackgroundManager = {{
  createManager(options) {{
    calls.push(["pageFactory", Boolean(options.documentRef.body)]);
    return {{
      applyBackdropOnly(color) {{ calls.push(["backdrop", color]); }},
      applyBackgroundFromBlob() {{ calls.push(["image"]); }}
    }};
  }}
}};
context.LexiShift.optionsProfileBackgroundCardThemeManager = {{
  createManager(options) {{
    calls.push(["cardFactory", Boolean(options.documentRef.documentElement)]);
    return {{
      applyCardThemeFromPrefs(prefs) {{ calls.push(["cardTheme", prefs.cardThemeHueDeg]); }}
    }};
  }}
}};

vm.runInContext(fs.readFileSync(themePath, "utf8"), context, {{ filename: themePath }});
const normalize = (value) => JSON.parse(JSON.stringify(value));

const settingsManager = {{
  defaults: {{ profileCardThemeHueDeg: 0 }},
  async load() {{ return {{ loaded: true }}; }},
  getSelectedSrsProfileId(items) {{
    assert.equal(items.loaded, true);
    return "suisui";
  }},
  getProfileUiPrefs(items, options) {{
    assert.equal(options.profileId, "suisui");
    return {{
      backgroundEnabled: false,
      backgroundBackdropColor: "#4455AA",
      cardThemeHueDeg: 42
    }};
  }}
}};

(async () => {{
  const applier = context.LexiShift.learningDashboardTheme.createThemeApplier({{
    documentRef: context.document,
    settingsManager
  }});
  const result = await applier.applyTheme({{ items: {{ loaded: true }} }});
  assert.deepEqual(normalize(result), {{ profileId: "suisui", applied: true }});
  assert.deepEqual(calls, [
    ["pageFactory", true],
    ["cardFactory", true],
    ["cardTheme", 42],
    ["backdrop", "#4455aa"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
