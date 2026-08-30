from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MATCHER_JS = PROJECT_ROOT / "apps/chrome-extension/content/processing/matcher.js"


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
            "Node matcher contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionMatcherContract(unittest.TestCase):
    def test_title_case_is_unicode_aware_for_accented_replacements(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(MATCHER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const matcher = context.LexiShift.matcher;

assert.equal(matcher.applyCase("música", ["music"], "match"), "música");
assert.equal(matcher.applyCase("música", ["Music"], "match"), "Música");
assert.equal(matcher.applyCase("música", ["MUSIC"], "match"), "MÚSICA");
assert.equal(matcher.applyCase("música rápida", ["Music"], "match"), "Música Rápida");
assert.equal(matcher.applyCase("música", ["music"], "title"), "Música");
assert.equal(matcher.titleCaseReplacement("álbum de música"), "Álbum De Música");
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
