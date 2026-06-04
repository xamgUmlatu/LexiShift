from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_DEFAULTS_JS = PROJECT_ROOT / "apps/chrome-extension/shared/settings/settings_defaults.js"


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
assert.equal(density.allowAdjacentReplacements, false);
assert.equal(density.maxReplacementsPerPage, 20);
assert.equal(density.maxReplacementsPerLemmaPerPage, 2);
assert.equal(context.LexiShift.defaults.maxOnePerTextBlock, density.maxOnePerTextBlock);
assert.equal(context.LexiShift.defaults.allowAdjacentReplacements, density.allowAdjacentReplacements);
assert.equal(context.LexiShift.defaults.maxReplacementsPerPage, density.maxReplacementsPerPage);
assert.equal(
  context.LexiShift.defaults.maxReplacementsPerLemmaPerPage,
  density.maxReplacementsPerLemmaPerPage
);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
