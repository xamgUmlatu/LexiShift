from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKGROUND_JS = PROJECT_ROOT / "apps/chrome-extension/background.js"
HELPER_ERROR_COPY_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_error_copy.js"
HELPER_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/base_methods.js"
HELPER_SRS_SET_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/srs_set_methods.js"
HELPER_TRANSPORT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_transport_extension.js"
)
LOCALE_FILES = {
    "en": PROJECT_ROOT / "apps/chrome-extension/_locales/en/messages.json",
    "de": PROJECT_ROOT / "apps/chrome-extension/_locales/de/messages.json",
    "ja": PROJECT_ROOT / "apps/chrome-extension/_locales/ja/messages.json",
    "zh": PROJECT_ROOT / "apps/chrome-extension/_locales/zh/messages.json",
}


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
            "Node helper localization contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperErrorLocalizationContract(unittest.TestCase):
    def test_locale_catalogs_define_helper_native_error_copy(self) -> None:
        required_keys = (
            "status_helper_native_messaging_failed",
            "status_helper_native_messaging_forbidden",
            "status_helper_native_host_exited",
            "status_helper_timeout",
            "status_srs_admission_preview_running",
            "status_srs_admission_preview_failed",
            "status_srs_admission_preview_header",
            "status_srs_admission_preview_plan_only",
            "status_srs_admission_preview_empty",
            "note_srs_admission_preview_sample_only",
            "label_srs_admission_preview_sampled_words",
            "label_srs_admission_preview_sample_details",
            "label_srs_admission_preview_effective_profile_context",
            "label_srs_admission_preview_topic_overlay",
            "label_srs_admission_preview_neutral_topic_support",
            "label_srs_admission_preview_plan_notes",
            "label_srs_admission_preview_advanced_details",
            "summary_srs_admission_preview_selected_topics",
            "summary_srs_admission_preview_sampled_topic_words",
            "summary_srs_admission_preview_matched_candidates",
            "summary_srs_admission_preview_no_topic_candidates",
            "summary_srs_admission_preview_overlay_status",
            "summary_srs_admission_preview_no_topic_priorities",
            "summary_srs_admission_preview_showing",
        )

        for locale, path in LOCALE_FILES.items():
            with self.subTest(locale=locale):
                messages = json.loads(path.read_text(encoding="utf-8"))
                for key in required_keys:
                    self.assertIn(key, messages)
                    self.assertTrue(str(messages[key].get("message") or "").strip())

    def test_helper_status_and_test_connection_localize_browser_native_errors(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const messages = {{
  status_helper_missing: "Helper unavailable.",
  status_helper_failed: "Helper error.",
  status_helper_native_messaging_failed: "Localized bridge failure.",
  status_helper_native_messaging_forbidden: "Localized forbidden.",
  status_helper_native_host_exited: "Localized host exited.",
  status_helper_timeout: "Localized timeout.",
  status_helper_test_failed: "Connection failed: $1"
}};
const proto = {{
  i18n: {{
    t: (key, arg, fallback) => {{
      const template = messages[key] || fallback;
      return typeof arg === "string" ? template.replace("$1", arg) : template;
    }}
  }},
  logger: () => {{}}
}};
installHelperBaseMethods(proto);
proto.getClient = function getClient() {{
  return {{
    async getStatus() {{
      return {{
        ok: false,
        error: {{
          code: "native_error",
          message: "Error when communicating with the native messaging host."
        }}
      }};
    }},
    async hello() {{
      return {{
        ok: false,
        error: {{
          code: "native_error",
          message: "Native host has exited."
        }}
      }};
    }}
  }};
}};

(async () => {{
  const status = await proto.getStatus();
  assert.equal(status.message, "Localized bridge failure.");
  const testMessage = await proto.testConnection();
  assert.equal(testMessage, "Connection failed: Localized host exited.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_methods_localize_timeout_forbidden_and_thrown_bridge_errors(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const messages = {{
  status_helper_missing: "Helper unavailable.",
  status_helper_failed: "Helper error.",
  status_helper_native_messaging_failed: "Localized bridge failure.",
  status_helper_native_messaging_forbidden: "Localized forbidden.",
  status_helper_native_host_exited: "Localized host exited.",
  status_helper_timeout: "Localized timeout.",
  status_helper_test_failed: "Connection failed: $1",
  status_helper_open_failed: "Open failed: $1"
}};
const proto = {{
  i18n: {{
    t: (key, arg, fallback) => {{
      const template = messages[key] || fallback;
      return typeof arg === "string" ? template.replace("$1", arg) : template;
    }}
  }},
  logger: () => {{}}
}};
installHelperBaseMethods(proto);
let helloCalls = 0;
let openCalls = 0;
proto.getClient = function getClient() {{
  return {{
    async hello() {{
      helloCalls += 1;
      if (helloCalls === 1) {{
        return {{
          ok: false,
          error: {{
            code: "timeout",
            message: "Helper request timed out."
          }}
        }};
      }}
      throw {{
        code: "bridge_unavailable",
        message: "Could not establish connection. Receiving end does not exist."
      }};
    }},
    async openDataDir() {{
      openCalls += 1;
      if (openCalls === 1) {{
        return {{
          ok: false,
          error: {{
            code: "native_forbidden",
            message: "Access to the specified native messaging host is forbidden."
          }}
        }};
      }}
      throw {{
        code: "timeout",
        message: "Helper request timed out."
      }};
    }}
  }};
}};

(async () => {{
  const timedOut = await proto.testConnection();
  assert.equal(timedOut, "Connection failed: Localized timeout.");

  const thrownBridge = await proto.testConnection();
  assert.equal(thrownBridge, "Connection failed: Helper unavailable.");

  const forbidden = await proto.openDataDir();
  assert.equal(forbidden, "Open failed: Localized forbidden.");

  const thrownTimeout = await proto.openDataDir();
  assert.equal(thrownTimeout, "Open failed: Localized timeout.");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_srs_helper_actions_throw_localized_browser_native_errors(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const helperSrsSetPath = {json.dumps(str(HELPER_SRS_SET_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperErrorCopyPath, "utf8"), context, {{ filename: helperErrorCopyPath }});
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});
vm.runInContext(fs.readFileSync(helperSrsSetPath, "utf8"), context, {{ filename: helperSrsSetPath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const installHelperSrsSetMethods = context.LexiShift.installHelperSrsSetMethods;
const messages = {{
  status_helper_missing: "Helper unavailable.",
  status_srs_admission_preview_failed: "Word sample failed.",
  status_helper_native_messaging_failed: "Localized bridge failure."
}};
const proto = {{
  i18n: {{
    t: (key, _arg, fallback) => messages[key] || fallback
  }},
  logger: () => {{}}
}};
installHelperBaseMethods(proto);
installHelperSrsSetMethods(proto);
proto.getClient = function getClient() {{
  return {{
    async previewSrsAdmission() {{
      return {{
        ok: false,
        error: {{
          code: "native_error",
          message: "Error when communicating with the native messaging host."
        }}
      }};
    }}
  }};
}};

(async () => {{
  await assert.rejects(
    () => proto.previewSrsAdmission("en-ja", 800, {{ profileId: "default" }}),
    /Localized bridge failure\\./
  );
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_transport_layers_classify_raw_browser_errors(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const backgroundPath = {json.dumps(str(BACKGROUND_JS))};
const transportPath = {json.dumps(str(HELPER_TRANSPORT_JS))};

async function testBackgroundClassification() {{
  let listener = null;
  const chrome = {{
    runtime: {{
      lastError: null,
      sendNativeMessage(_host, _request, callback) {{
        this.lastError = {{ message: "Access to the specified native messaging host is forbidden." }};
        callback(undefined);
        this.lastError = null;
      }},
      onMessage: {{
        addListener(fn) {{
          listener = fn;
        }}
      }}
    }}
  }};
  const context = vm.createContext({{
    console,
    chrome,
    setTimeout,
    clearTimeout,
    Date,
    Math
  }});
  context.globalThis = context;
  vm.runInContext(fs.readFileSync(backgroundPath, "utf8"), context, {{ filename: backgroundPath }});
  const response = await new Promise((resolve) => {{
    const keepAlive = listener(
      {{ kind: "lexishift_helper_request_v1", requestType: "hello", payload: {{}}, timeoutMs: 1000 }},
      null,
      resolve
    );
    assert.equal(keepAlive, true);
  }});
  assert.equal(response.ok, false);
  assert.equal(response.error.code, "native_forbidden");
  assert.equal(response.error.message, "Native messaging access is blocked.");
  assert.equal(
    response.error.detail,
    "Access to the specified native messaging host is forbidden."
  );
}}

async function testBridgeClassification() {{
  const chrome = {{
    runtime: {{
      lastError: null,
      sendMessage(_message, callback) {{
        this.lastError = {{
          message: "Could not establish connection. Receiving end does not exist."
        }};
        callback(undefined);
        this.lastError = null;
      }}
    }}
  }};
  const context = vm.createContext({{
    console,
    chrome,
    setTimeout,
    clearTimeout
  }});
  context.globalThis = context;
  context.LexiShift = {{}};
  vm.runInContext(fs.readFileSync(transportPath, "utf8"), context, {{ filename: transportPath }});
  const response = await context.LexiShift.helperTransportExtension.send("hello", {{}}, 1000);
  assert.equal(response.ok, false);
  assert.equal(response.error.code, "bridge_unavailable");
  assert.equal(response.error.message, "Helper bridge unavailable.");
  assert.equal(
    response.error.detail,
    "Could not establish connection. Receiving end does not exist."
  );
}}

(async () => {{
  await testBackgroundClassification();
  await testBridgeClassification();
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
