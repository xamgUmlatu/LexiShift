from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER_BASE_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/base_methods.js"
HELPER_SRS_SET_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/srs_set_methods.js"
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
            "status_helper_native_host_exited",
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

const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const messages = {{
  status_helper_missing: "Helper unavailable.",
  status_helper_failed: "Helper error.",
  status_helper_native_messaging_failed: "Localized bridge failure.",
  status_helper_native_host_exited: "Localized host exited.",
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

    def test_srs_helper_actions_throw_localized_browser_native_errors(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperBasePath = {json.dumps(str(HELPER_BASE_JS))};
const helperSrsSetPath = {json.dumps(str(HELPER_SRS_SET_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(helperBasePath, "utf8"), context, {{ filename: helperBasePath }});
vm.runInContext(fs.readFileSync(helperSrsSetPath, "utf8"), context, {{ filename: helperSrsSetPath }});

const installHelperBaseMethods = context.LexiShift.installHelperBaseMethods;
const installHelperSrsSetMethods = context.LexiShift.installHelperSrsSetMethods;
const messages = {{
  status_helper_missing: "Helper unavailable.",
  status_srs_admission_preview_failed: "Admission preview failed.",
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


if __name__ == "__main__":
    unittest.main()
