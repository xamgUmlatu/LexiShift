from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BROWSING_SIGNALS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/srs_browsing_admission_signals.js"
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
      raw_text: "raw text should not travel"
    }},
    {{ language_pair: "en-es", lemma: "salud" }},
    {{ language_pair: "all", lemma: "ignored" }},
    {{ language_pair: "", lemma: "" }}
  ],
  {{ srsProfileId: "alpha", srsPair: "en-es" }},
  {{ maxCountPerSignal: 5 }}
);
const payloads = signals.buildPacketPayloads(pending, {{
  nowIso: () => "2026-05-23T00:00:00.000Z"
}});

assert.equal(accepted, 3);
assert.equal(payloads.length, 1);
assert.equal(payloads[0].pair, "en-es");
assert.equal(payloads[0].profile_id, "alpha");
assert.equal(payloads[0].opt_in, true);
assert.deepEqual(normalize(payloads[0].signals), [
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
  assert.deepEqual(normalize(calls[0].payload.signals), [
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

    def test_manifest_and_content_script_wire_dev_only_signal_module(self) -> None:
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        script_paths = manifest["content_scripts"][0]["js"]
        self.assertIn("shared/srs/srs_browsing_admission_signals.js", script_paths)
        self.assertLess(
            script_paths.index("shared/srs/srs_browsing_admission_signals.js"),
            script_paths.index("content/runtime/dom_scan/text_node_processor.js"),
        )

        content_script = CONTENT_SCRIPT_JS.read_text(encoding="utf-8")
        self.assertIn("srsBrowsingAdmissionSignals.createSender", content_script)
        self.assertIn("browsingAdmissionSignals: browsingAdmissionSignalSender", content_script)


if __name__ == "__main__":
    unittest.main()
