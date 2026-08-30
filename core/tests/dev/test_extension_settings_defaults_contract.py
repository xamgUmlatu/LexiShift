from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_DEFAULTS_JS = PROJECT_ROOT / "apps/chrome-extension/shared/settings/settings_defaults.js"
OPTIONS_HTML = PROJECT_ROOT / "apps/chrome-extension/options.html"


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
            "Node extension settings defaults contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSettingsDefaultsContract(unittest.TestCase):
    def test_legacy_text_node_limit_is_deemphasized_after_sentence_limit(self) -> None:
        html = OPTIONS_HTML.read_text(encoding="utf-8")
        sentence_index = html.index('id="max-replacements-per-sentence"')
        legacy_summary_index = html.index('data-i18n="summary_legacy_replacement_compatibility"')
        legacy_input_index = html.index('id="max-one-per-block"')

        self.assertLess(sentence_index, legacy_summary_index)
        self.assertLess(legacy_summary_index, legacy_input_index)
        self.assertEqual(html.count('id="max-one-per-block"'), 1)
        self.assertIn(
            "For learner-facing density, set Max replacements per sentence to 1.",
            html,
        )

    def test_standard_replacement_density_defaults_are_explicit(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SETTINGS_DEFAULTS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const density = context.LexiShift.replacementDensityDefaults.standard;
assert.equal(density.maxOnePerTextBlock, false);
assert.equal(density.allowAdjacentReplacements, true);
assert.equal(density.maxReplacementsPerPage, 0);
assert.equal(density.maxReplacementsPerLemmaPerPage, 0);
assert.equal(density.maxReplacementsPerSentence, 0);
assert.equal(context.LexiShift.defaults.maxOnePerTextBlock, density.maxOnePerTextBlock);
assert.equal(context.LexiShift.defaults.allowAdjacentReplacements, density.allowAdjacentReplacements);
assert.equal(context.LexiShift.defaults.maxReplacementsPerPage, density.maxReplacementsPerPage);
assert.equal(
  context.LexiShift.defaults.maxReplacementsPerLemmaPerPage,
  density.maxReplacementsPerLemmaPerPage
);
assert.equal(
  context.LexiShift.defaults.maxReplacementsPerSentence,
  density.maxReplacementsPerSentence
);
assert.equal(typeof context.LexiShift.defaults.srsBrowsingSourceMiningOptions, "object");
assert.equal(
  Object.keys(context.LexiShift.defaults.srsBrowsingSourceMiningOptions).length,
  0
);
assert.equal(typeof context.LexiShift.defaults.srsBrowsingSourceIndexOptions, "object");
assert.equal(
  Object.keys(context.LexiShift.defaults.srsBrowsingSourceIndexOptions).length,
  0
);
assert.equal(
  context.LexiShift.defaults.srsSemanticAdmissionFallbackPolicy,
  "abstain_on_unavailable"
);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
