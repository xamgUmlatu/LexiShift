from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKGROUND_JS = PROJECT_ROOT / "apps/chrome-extension/background.js"
HELPER_TRANSPORT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_transport_extension.js"
)
HELPER_CLIENT_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_client.js"
HELPER_FEEDBACK_PRIMITIVES_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_feedback_sync_primitives.js"
)
HELPER_FEEDBACK_SYNC_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_feedback_sync.js"
)
FEEDBACK_RUNTIME_CONTROLLER_JS = (
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
            "Node feedback auto-refresh bridge contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionFeedbackAutoRefreshBridgeContract(unittest.TestCase):
    def test_synced_feedback_routes_auto_refresh_to_native_host(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const backgroundPath = {json.dumps(str(BACKGROUND_JS))};
const transportPath = {json.dumps(str(HELPER_TRANSPORT_JS))};
const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const primitivesPath = {json.dumps(str(HELPER_FEEDBACK_PRIMITIVES_JS))};
const syncPath = {json.dumps(str(HELPER_FEEDBACK_SYNC_JS))};
const feedbackRuntimePath = {json.dumps(str(FEEDBACK_RUNTIME_CONTROLLER_JS))};

let bridgeListener = null;
const nativeRequests = [];
const bridgeMessages = [];

const backgroundChrome = {{
  runtime: {{
    lastError: null,
    sendNativeMessage(host, request, callback) {{
      nativeRequests.push({{ host, request }});
      callback({{ ok: true, data: {{ type: request.type, stored: true }} }});
    }},
    onMessage: {{
      addListener(fn) {{
        bridgeListener = fn;
      }}
    }}
  }}
}};
const backgroundContext = vm.createContext({{
  console,
  chrome: backgroundChrome,
  setTimeout: () => 1,
  clearTimeout: () => {{}},
  Date,
  Math
}});
backgroundContext.globalThis = backgroundContext;
vm.runInContext(
  fs.readFileSync(backgroundPath, "utf8"),
  backgroundContext,
  {{ filename: backgroundPath }}
);
assert.equal(typeof bridgeListener, "function");

const storage = {{}};
const contentChrome = {{
  runtime: {{
    lastError: null,
    sendMessage(message, callback) {{
      bridgeMessages.push(message);
      const keepAlive = bridgeListener(message, null, callback);
      assert.equal(keepAlive, true);
    }}
  }},
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
}};
const contentContext = vm.createContext({{
  console,
  chrome: contentChrome,
  Date,
  Math,
  Promise,
  Set,
  Map,
  Object,
  JSON,
  setTimeout: () => 1,
  clearTimeout: () => {{}}
}});
contentContext.globalThis = contentContext;
contentContext.LexiShift = {{}};
for (const path of [
  transportPath,
  clientPath,
  primitivesPath,
  syncPath,
  feedbackRuntimePath
]) {{
  vm.runInContext(fs.readFileSync(path, "utf8"), contentContext, {{ filename: path }});
}}

const HelperClient = contentContext.LexiShift.helperClient;
const helperClient = new HelperClient(contentContext.LexiShift.helperTransportExtension);
const logs = [];
const settings = {{
  srsEnabled: true,
  srsAutoRefreshEnabled: true,
  srsPair: "en-ja",
  srsProfileId: "alpha profile",
  srsBootstrapTopN: 900,
  srsMaxActive: 50,
  srsAutoRefreshMinFeedbackEvents: 8,
  srsAutoRefreshMinGoodEasy: 6,
  srsAutoRefreshRepeatMinGoodEasy: 12,
  srsAutoRefreshCooldownMinutes: 45,
  srsProfileContext: {{
    interests: ["animals"],
    topic_weights: {{ animals: 0.75 }}
  }},
  debugEnabled: true
}};
const controller = contentContext.LexiShift.contentFeedbackRuntimeController.createController({{
  helperFeedbackSyncModule: contentContext.LexiShift.helperFeedbackSync,
  getHelperClient: () => helperClient,
  getCurrentSettings: () => settings,
  normalizeProfileId: (value) => String(value || "").trim() || "default",
  isTopFrameWindow: () => true,
  log: (...args) => logs.push(args)
}});

(async () => {{
  const sync = controller.ensureSync();
  assert.ok(sync);
  await sync.enqueue({{
    pair: "en-ja",
    profile_id: "alpha profile",
    lemma: "neko",
    rating: "good",
    source_type: "extension",
    ts: "2026-05-27T00:00:00.000Z"
  }});
  const flushed = await sync.flushNow("unit");
  assert.equal(flushed, true);

  assert.equal(nativeRequests.length, 2);
  assert.equal(nativeRequests[0].host, "com.lexishift.helper");
  assert.equal(nativeRequests[0].request.type, "record_feedback");
  assert.deepEqual(JSON.parse(JSON.stringify(nativeRequests[0].request.payload)), {{
    pair: "en-ja",
    profile_id: "alpha profile",
    lemma: "neko",
    rating: "good",
    source_type: "extension",
    ts: "2026-05-27T00:00:00.000Z"
  }});

  assert.equal(nativeRequests[1].host, "com.lexishift.helper");
  assert.equal(nativeRequests[1].request.type, "srs_auto_refresh");
  assert.deepEqual(JSON.parse(JSON.stringify(nativeRequests[1].request.payload)), {{
    pair: "en-ja",
    profile_id: "alpha profile",
    strategy: "profile_growth",
    set_top_n: 900,
    max_active_items: 50,
    auto_refresh_enabled: true,
    auto_refresh_min_feedback_events: 8,
    auto_refresh_min_good_easy: 6,
    auto_refresh_repeat_min_good_easy: 12,
    auto_refresh_cooldown_minutes: 45,
    profile_context: {{
      interests: ["animals"],
      topic_weights: {{ animals: 0.75 }}
    }},
    trigger: "auto_feedback_threshold"
  }});
  assert.equal(bridgeMessages[0].kind, "lexishift_helper_request_v1");
  assert.equal(bridgeMessages[0].requestType, "record_feedback");
  assert.equal(bridgeMessages[1].kind, "lexishift_helper_request_v1");
  assert.equal(bridgeMessages[1].requestType, "srs_auto_refresh");
  assert.equal(bridgeMessages[1].timeoutMs, 60000);
  assert.ok(logs.some((entry) => String(entry[0]).includes("SRS auto-refresh checked")));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
