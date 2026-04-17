from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRS_GATE_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_gate.js"


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
            "Node runtime-gate contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionSrsRuntimeGateContract(unittest.TestCase):
    def test_helper_ruleset_gate_accepts_all_srs_rules_without_due_filtering(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SRS_GATE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const buildSrsGate = context.LexiShift.srsGate.buildSrsGate;

(async () => {{
  const enabledRules = [
    {{
      replacement: "alpha",
      metadata: {{
        lexishift_origin: "srs",
        next_due: "2099-01-01T00:00:00Z",
        in_due: false
      }}
    }},
    {{
      replacement: "beta",
      metadata: {{
        lexishift_origin: "srs",
        next_due: "2000-01-01T00:00:00Z",
        in_due: true
      }}
    }},
    {{
      replacement: "gamma",
      metadata: {{
        lexishift_origin: "ruleset"
      }}
    }}
  ];

  const gate = await buildSrsGate({{ srsEnabled: true }}, enabledRules, () => {{}});

  assert.equal(gate.enabled, true);
  assert.equal(gate.stats.mode, "helper_ruleset");
  assert.equal(gate.stats.datasetLoaded, false);
  assert.equal(gate.stats.srsCount, 2);
  assert.equal(gate.stats.srsActiveCount, 2);
  assert.equal(gate.activeRules.length, 3);
  assert.deepEqual(Array.from(gate.activeLemmas).sort(), ["alpha", "beta"]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
