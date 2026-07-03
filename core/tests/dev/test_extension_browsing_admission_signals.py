from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BROWSING_SIGNALS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js"
)
METRICS_JS = PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_metrics.js"
SETTINGS_ROUTER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/runtime/settings_change_router.js"
)
HELPER_CLIENT_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_client.js"
MANIFEST_JSON = PROJECT_ROOT / "apps/chrome-extension/manifest.json"
CONTENT_SCRIPT_JS = PROJECT_ROOT / "apps/chrome-extension/content_script.js"


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
            "Node browsing-admission signal test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionBrowsingAdmissionSignals(unittest.TestCase):
    def test_packet_builder_groups_replacement_exposures_without_private_fields(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(BROWSING_SIGNALS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const signals = context.LexiShift.srsBrowsingAdmissionSignals;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const pending = new Map();
const accepted = signals.addExposureBatchToPending(
  pending,
  [
    {{
      language_pair: "en-es",
      lemma: "Hipoteca",
      target_key: "hipoteca",
      url: "https://example.invalid/private",
      source_phrase: "mortgage",
      original: "mortgage"
    }},
    {{
      language_pair: "en-es",
      lemma: "hipoteca",
      replacement: "hipoteca",
      url: "https://example.invalid/private",
      raw_text: "raw text should not travel"
    }},
    {{ language_pair: "en-es", lemma: "salud" }},
    {{ language_pair: "all", lemma: "ignored" }},
    {{ language_pair: "", lemma: "" }}
  ],
  {{ srsProfileId: "alpha", srsPair: "en-es" }},
  {{ maxCountPerSignal: 5, pageContextKey: "test-page-context", nowMs: () => 0 }}
);
const payloads = signals.buildPacketPayloads(pending, {{
  nowIso: () => "2026-05-23T00:00:00.000Z"
}});

assert.equal(accepted, 3);
assert.equal(payloads.length, 1);
assert.equal(payloads[0].pair, "en-es");
assert.equal(payloads[0].profile_id, "alpha");
assert.equal(payloads[0].opt_in, true);
const rows = normalize(payloads[0].signals);
assert.equal(rows[0].context_key.startsWith("pageh:"), true);
assert.equal(rows[1].context_key.startsWith("pageh:"), true);
assert.equal(rows[0].context_key, rows[1].context_key);
const explicitContext = signals.contextKeyForExposure(
  {{ document_id: "rabbit-summary-1", url: "https://example.invalid/private" }},
  {{ nowMs: () => 0 }}
);
assert.equal(explicitContext.startsWith("ctxh:"), true);
assert.equal(explicitContext.includes("rabbit-summary-1"), false);
const comparableRows = rows.map((row) => {{
  const copy = {{ ...row }};
  delete copy.context_key;
  return copy;
}});
assert.deepEqual(comparableRows, [
  {{
    target_key: "hipoteca",
    target_lemma: "hipoteca",
    target_reading: "",
    side: "replacement_exposure",
    count: 2,
    reading_confidence: 1,
    observation_source: "replacement_exposure",
    source_mapping_confidence: 1
  }},
  {{
    target_key: "salud",
    target_lemma: "salud",
    target_reading: "",
    side: "replacement_exposure",
    count: 1,
    reading_confidence: 1,
    observation_source: "replacement_exposure",
    source_mapping_confidence: 1
  }}
]);
const serialized = JSON.stringify(payloads);
assert.equal(serialized.includes("example.invalid"), false);
assert.equal(serialized.includes("mortgage"), false);
assert.equal(serialized.includes("raw text"), false);
"""
        _run_node(script)

    def test_sender_requires_enabled_setting_and_uses_helper_client_route(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const modulePath = {json.dumps(str(BROWSING_SIGNALS_JS))};
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const calls = [];
const HelperClient = context.LexiShift.helperClient;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const helperClient = new HelperClient({{
  async send(type, payload, timeoutMs) {{
    calls.push({{ type, payload, timeoutMs }});
    return {{ ok: true, data: {{ status: "ok" }} }};
  }}
}});
const sender = context.LexiShift.srsBrowsingAdmissionSignals.createSender({{
  getHelperClient: () => helperClient,
  getCurrentSettings: () => ({{}}),
  flushDelayMs: 100000,
  pageContextKey: "sender-page-context",
  nowMs: () => 0,
  nowIso: () => "2026-05-23T00:00:00.000Z"
}});

(async () => {{
  const skipped = await sender.recordExposureBatch(
    [{{ language_pair: "en-es", lemma: "viaje" }}],
    {{
      srsPair: "en-es",
      srsProfileId: "default",
      srsBrowsingAdmissionSignalsEnabled: false
    }}
  );
  assert.equal(skipped.status, "skipped");
  assert.equal(calls.length, 0);

  const queued = await sender.recordExposureBatch(
    [{{ language_pair: "en-es", lemma: "salud", url: "https://example.invalid/private" }}],
    {{
      srsPair: "en-es",
      srsProfileId: "default",
      srsBrowsingAdmissionSignalsEnabled: true
    }}
  );
  assert.equal(queued.status, "queued");
  const flushed = await sender.flush();
  assert.equal(flushed.status, "sent");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].type, "srs_browsing_signal_ingest");
  assert.equal(calls[0].payload.opt_in, true);
  const rows = normalize(calls[0].payload.signals);
  assert.equal(rows[0].context_key.startsWith("pageh:"), true);
  const comparableRows = rows.map((row) => {{
    const copy = {{ ...row }};
    delete copy.context_key;
    return copy;
  }});
  assert.deepEqual(comparableRows, [
    {{
      target_key: "salud",
      target_lemma: "salud",
      target_reading: "",
      side: "replacement_exposure",
      count: 1,
      reading_confidence: 1,
      observation_source: "replacement_exposure",
      source_mapping_confidence: 1
    }}
  ]);
  assert.equal(JSON.stringify(calls[0].payload).includes("example.invalid"), false);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_packet_builder_preserves_target_surface_side_and_count(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(BROWSING_SIGNALS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const signals = context.LexiShift.srsBrowsingAdmissionSignals;
const normalize = (value) => JSON.parse(JSON.stringify(value));
const pending = new Map();
const accepted = signals.addExposureBatchToPending(
  pending,
  [
    {{
      language_pair: "en-ja",
      lemma: "発酵",
      target_key: "発酵|はっこう",
      target_reading: "はっこう",
      side: "target",
      count: 4,
      observation_source: "target_surface",
      url: "https://example.invalid/private"
    }}
  ],
  {{ srsProfileId: "alpha", srsPair: "en-ja" }},
  {{ pageContextKey: "target-page-context", nowMs: () => 0 }}
);
const payloads = signals.buildPacketPayloads(pending, {{
  nowIso: () => "2026-05-23T00:00:00.000Z"
}});

assert.equal(accepted, 4);
assert.equal(payloads.length, 1);
const row = normalize(payloads[0].signals[0]);
assert.equal(row.target_key, "発酵|はっこう");
assert.equal(row.target_lemma, "発酵");
assert.equal(row.target_reading, "はっこう");
assert.equal(row.side, "target");
assert.equal(row.observation_source, "target_surface");
assert.equal(row.count, 4);
assert.equal(row.reading_confidence, 1);
assert.equal(row.source_mapping_confidence, 1);
assert.equal(JSON.stringify(payloads).includes("example.invalid"), false);
"""
        _run_node(script)

    def test_sender_can_clear_pending_packets_before_flush(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(BROWSING_SIGNALS_JS))};
const context = vm.createContext({{
  console,
  setTimeout,
  clearTimeout
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const calls = [];
const logs = [];
const normalize = (value) => JSON.parse(JSON.stringify(value));
const sender = context.LexiShift.srsBrowsingAdmissionSignals.createSender({{
  getHelperClient: () => ({{
    ingestBrowsingAdmissionSignals(payload) {{
      calls.push(payload);
      return Promise.resolve({{ ok: true }});
    }}
  }}),
  getCurrentSettings: () => ({{}}),
  flushDelayMs: 100000,
  log: (message) => logs.push(String(message)),
  pageContextKey: "sender-page-context",
  nowMs: () => 0,
  nowIso: () => "2026-05-23T00:00:00.000Z"
}});

(async () => {{
  const queued = await sender.recordExposureBatch(
    [{{ language_pair: "en-es", lemma: "salud" }}],
    {{
      srsPair: "en-es",
      srsProfileId: "default",
      srsBrowsingAdmissionSignalsEnabled: true
    }}
  );
  assert.equal(queued.status, "queued");
  assert.equal(sender._pendingByScope.size, 1);
  const cleared = sender.clearPending("test_scope_change");
  assert.deepEqual(normalize(cleared), {{
    status: "cleared",
    reason: "test_scope_change",
    scope_count: 1,
    signal_count: 1
  }});
  assert.equal(sender._pendingByScope.size, 0);
  assert.equal(logs.some((message) => message.includes("test_scope_change")), true);
  const flushed = await sender.flush();
  assert.equal(flushed.status, "empty");
  assert.equal(calls.length, 0);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_metrics_can_queue_browsing_signals_without_local_exposure_log(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(METRICS_JS))};
let storageSetCalls = 0;
const storeCalls = [];
const browsingCalls = [];
const normalize = (value) => JSON.parse(JSON.stringify(value));
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  srsStore: {{
    recordExposureBatch(payload) {{
      storeCalls.push(payload);
    }}
  }}
}};
context.chrome = {{
  runtime: {{ id: "test-extension" }},
  storage: {{
    local: {{
      get(defaults, callback) {{
        callback(defaults);
      }},
      set(_items, callback) {{
        storageSetCalls += 1;
        if (callback) callback();
      }}
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

(async () => {{
  const saved = await context.LexiShift.srsMetrics.recordExposureBatch(
    [
      {{
        lemma: "salud",
        replacement: "salud",
        language_pair: "en-es"
      }}
    ],
    {{
      recordLocalExposureLog: false,
      settings: {{
        srsBrowsingAdmissionSignalsEnabled: true,
        debugEnabled: true
      }},
      browsingAdmissionSignals: {{
        recordExposureBatch(payload, settings) {{
          browsingCalls.push({{ payload, settings }});
          return Promise.resolve({{ status: "queued", accepted: payload.length }});
        }}
      }},
      log: () => {{}}
    }}
  );
  assert.deepEqual(normalize(saved), []);
  assert.equal(storageSetCalls, 0);
  assert.equal(storeCalls.length, 0);
  assert.equal(browsingCalls.length, 1);
  assert.equal(browsingCalls[0].payload.length, 1);
  assert.equal(browsingCalls[0].payload[0].lemma, "salud");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_settings_router_clears_browsing_queue_on_toggle_and_scope_change(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(SETTINGS_ROUTER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

let currentSettings = {{
  debugEnabled: true,
  srsBrowsingAdmissionSignalsEnabled: true,
  srsPair: "en-ja",
  srsProfileId: "alpha"
}};
const applied = [];
const cleared = [];
const logs = [];
const router = context.LexiShift.contentSettingsChangeRouter.createRouter({{
  getCurrentSettings: () => currentSettings,
  setCurrentSettings: (next) => {{
    currentSettings = {{ ...next }};
  }},
  browsingAdmissionSignals: {{
    clearPending(reason) {{
      cleared.push(reason);
    }}
  }},
  applySettings: (next) => {{
    applied.push({{ ...next }});
  }},
  log: (message) => logs.push(String(message))
}});

router.handleStorageChange(
  {{
    srsBrowsingAdmissionSignalsEnabled: {{ oldValue: true, newValue: false }}
  }},
  "local"
);
assert.equal(currentSettings.srsBrowsingAdmissionSignalsEnabled, false);
assert.deepEqual(cleared, ["browsing_admission_setting_changed"]);
assert.equal(logs.some((message) => message.includes("browsing-admission signals disabled")), true);

router.handleStorageChange(
  {{
    srsPair: {{ oldValue: "en-ja", newValue: "en-de" }}
  }},
  "local"
);
assert.deepEqual(cleared, [
  "browsing_admission_setting_changed",
  "browsing_admission_scope_changed"
]);
assert.equal(applied.length, 1);
assert.equal(applied[0].srsPair, "en-de");
"""
        _run_node(script)

    def test_manifest_and_content_script_wire_dev_only_signal_module(self) -> None:
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        script_paths = manifest["content_scripts"][0]["js"]
        self.assertIn("shared/srs/srs_browsing_admission_signals.js", script_paths)
        self.assertIn("shared/srs/srs_browsing_source_morphology.js", script_paths)
        self.assertIn("shared/srs/srs_browsing_source_mining.js", script_paths)
        self.assertIn("shared/srs/srs_browsing_page_mining.js", script_paths)
        self.assertIn("content/runtime/rules/browsing_source_index_runtime.js", script_paths)
        self.assertLess(
            script_paths.index("shared/srs/srs_browsing_admission_signals.js"),
            script_paths.index("shared/srs/srs_browsing_source_morphology.js"),
        )
        self.assertLess(
            script_paths.index("shared/srs/srs_browsing_source_morphology.js"),
            script_paths.index("shared/srs/srs_browsing_source_mining.js"),
        )
        self.assertLess(
            script_paths.index("shared/srs/srs_browsing_source_mining.js"),
            script_paths.index("shared/srs/srs_browsing_page_mining.js"),
        )
        self.assertLess(
            script_paths.index("shared/srs/srs_browsing_page_mining.js"),
            script_paths.index("content/runtime/dom_scan/text_node_processor.js"),
        )
        self.assertLess(
            script_paths.index("content/runtime/rules/helper_rules_runtime.js"),
            script_paths.index("content/runtime/rules/browsing_source_index_runtime.js"),
        )
        self.assertLess(
            script_paths.index("content/runtime/rules/browsing_source_index_runtime.js"),
            script_paths.index("content/runtime/rules/active_rules_runtime.js"),
        )

        content_script = CONTENT_SCRIPT_JS.read_text(encoding="utf-8")
        self.assertIn("srsBrowsingAdmissionSignals.createSender", content_script)
        self.assertIn("browsingAdmissionSignals: browsingAdmissionSignalSender", content_script)
        self.assertIn("root.srsBrowsingSourceMining", content_script)
        self.assertIn("srsBrowsingPageMining.createMiner", content_script)
        self.assertIn("getCurrentRules: () => currentActiveRules", content_script)
        self.assertIn("getSourceMiningRules", content_script)
        self.assertIn("contentBrowsingSourceIndexRuntime", content_script)
        self.assertIn("setActiveRules", content_script)
        browsing_source_index_runtime = (
            PROJECT_ROOT
            / "apps/chrome-extension/content/runtime/rules/browsing_source_index_runtime.js"
        ).read_text(encoding="utf-8")
        self.assertIn("resolveBrowsingSourceIndex", browsing_source_index_runtime)
        self.assertIn("sourceRulesFor", browsing_source_index_runtime)
        settings_router = SETTINGS_ROUTER_JS.read_text(encoding="utf-8")
        self.assertIn("srsBrowsingAdmissionSignalsEnabled", settings_router)
        self.assertIn("srsBrowsingSourceMiningOptions", settings_router)
        self.assertIn("srsBrowsingSourceIndexOptions", settings_router)
        self.assertIn("clearPending", settings_router)


if __name__ == "__main__":
    unittest.main()
