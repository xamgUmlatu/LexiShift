from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEEDBACK_RUNTIME_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/feedback/feedback_runtime_controller.js"
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
            "Node extension feedback runtime contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionFeedbackRuntimeContract(unittest.TestCase):
    def test_srs_hide_action_writes_admission_suppression_without_feedback(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const runtimePath = {json.dumps(str(FEEDBACK_RUNTIME_JS))};
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout
}});
context.globalThis = context;
context.window = {{ location: {{ href: "https://example.invalid/article" }} }};
context.document = {{
  createTextNode(text) {{
    return {{ nodeType: 3, textContent: text }};
  }}
}};
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(runtimePath, "utf8"), context, {{ filename: runtimePath }});

const helperCalls = [];
const feedbackCalls = [];
const controller = context.LexiShift.contentFeedbackRuntimeController.createController({{
  srsFeedback: {{
    recordFeedback() {{
      feedbackCalls.push("recorded");
      return Promise.resolve(null);
    }}
  }},
  getHelperClient: () => ({{
    async suppressSrsAdmission(payload) {{
      helperCalls.push(payload);
      return {{ ok: true, data: {{ status: "ok" }} }};
    }}
  }}),
  getCurrentSettings: () => ({{
    srsProfileId: "learner",
    srsPair: "en-es",
    debugEnabled: true
  }}),
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  log: () => {{}}
}});

(async () => {{
  const target = {{
    dataset: {{
      origin: "srs",
      replacement: "Perro",
      languagePair: "en-es",
      original: "dog"
    }},
    textContent: "Perro",
    replaceWith(node) {{
      this.replacedWith = node;
    }}
  }};
  await controller.handleFeedback({{
    action: "suppress_admission",
    reason: "manual_cooldown",
    target
  }});

  assert.equal(JSON.stringify(helperCalls), JSON.stringify([{{
    pair: "en-es",
    profile_id: "learner",
    lemma: "perro",
    reason: "manual_cooldown",
    source_type: "extension",
    note: "feedback_popup_hide_for_now"
  }}]));
  assert.equal(feedbackCalls.length, 0);
  assert.equal(target.replacedWith.textContent, "dog");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
