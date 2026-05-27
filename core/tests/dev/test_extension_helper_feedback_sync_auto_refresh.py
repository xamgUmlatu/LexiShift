from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRIMITIVES_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_feedback_sync_primitives.js"
)
SYNC_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_feedback_sync.js"


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
            "Node helper-feedback sync auto-refresh contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperFeedbackSyncAutoRefresh(unittest.TestCase):
    def test_successful_helper_feedback_sync_triggers_auto_refresh_check(self) -> None:
        script = _script(
            """
const sent = [];
const refreshes = [];
const sync = context.LexiShift.helperFeedbackSync.create({
  isFlushWorker: true,
  batchSize: 4,
  sendFeedback: async (payload) => {
    sent.push(payload);
    return { ok: true, data: { stored: true } };
  },
  maybeAutoRefresh: async (payload) => {
    refreshes.push(payload);
    return { ok: true, data: { attempted: true, auto_refresh: { reason_code: "normal" } } };
  },
  log: () => {}
});

await sync.enqueue({
  pair: "en-ja",
  profile_id: "default",
  lemma: "alpha",
  rating: "good",
  source_type: "extension"
});
const flushed = await sync.flushNow("unit");

assert.equal(flushed, true);
assert.equal(sent.length, 1);
assert.deepEqual(
  JSON.parse(JSON.stringify(refreshes)),
  [{ reason: "unit", handled: 1, synced: 1 }]
);
assert.deepEqual(JSON.parse(JSON.stringify(storage.helperFeedbackSyncQueue)), []);
"""
        )
        _run_node(script)

    def test_failed_helper_feedback_retry_does_not_trigger_auto_refresh_check(self) -> None:
        script = _script(
            """
const sent = [];
const refreshes = [];
const sync = context.LexiShift.helperFeedbackSync.create({
  isFlushWorker: true,
  batchSize: 4,
  sendFeedback: async (payload) => {
    sent.push(payload);
    return { ok: false, error: { code: "helper_offline", message: "offline" } };
  },
  maybeAutoRefresh: async (payload) => {
    refreshes.push(payload);
    return { ok: true, data: { attempted: true } };
  },
  log: () => {}
});

await sync.enqueue({
  pair: "en-ja",
  profile_id: "default",
  lemma: "alpha",
  rating: "good",
  source_type: "extension"
});
const flushed = await sync.flushNow("unit");

assert.equal(flushed, true);
assert.equal(sent.length, 1);
assert.deepEqual(JSON.parse(JSON.stringify(refreshes)), []);
assert.equal(storage.helperFeedbackSyncQueue.length, 1);
assert.equal(storage.helperFeedbackSyncQueue[0].attempts, 1);
assert.equal(storage.helperFeedbackSyncQueue[0].last_error.code, "helper_offline");
"""
        )
        _run_node(script)


def _script(body: str) -> str:
    return f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const primitivesPath = {json.dumps(str(PRIMITIVES_JS))};
const syncPath = {json.dumps(str(SYNC_JS))};
const storage = {{}};
const context = vm.createContext({{
  console,
  Date,
  Math,
  Promise,
  Set,
  Map,
  Object,
  JSON,
  setTimeout: () => 1,
  clearTimeout: () => {{}},
  chrome: {{
    storage: {{
      local: {{
        get(defaults, callback) {{
          const result = Object.assign({{}}, defaults || {{}});
          for (const key of Object.keys(storage)) {{
            result[key] = storage[key];
          }}
          callback(result);
        }},
        set(payload, callback) {{
          Object.assign(storage, payload || {{}});
          if (callback) {{
            callback();
          }}
        }},
        remove(keys, callback) {{
          const list = Array.isArray(keys) ? keys : [keys];
          for (const key of list) {{
            delete storage[key];
          }}
          if (callback) {{
            callback();
          }}
        }}
      }},
      onChanged: {{
        addListener() {{}},
        removeListener() {{}}
      }}
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(primitivesPath, "utf8"), context, {{ filename: primitivesPath }});
vm.runInContext(fs.readFileSync(syncPath, "utf8"), context, {{ filename: syncPath }});

(async () => {{
{body}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""


if __name__ == "__main__":
    unittest.main()
