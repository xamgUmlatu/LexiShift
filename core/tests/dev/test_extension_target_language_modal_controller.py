from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODAL_UTILS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/ui/target_language_modal/utils.js"
)
MODAL_CONTROLLER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/ui/target_language_modal_controller.js"
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
            "Node target language modal controller test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionTargetLanguageModalController(unittest.TestCase):
    def test_sync_visibility_clears_hidden_attribute_for_supported_language(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const utilsPath = {json.dumps(str(MODAL_UTILS_JS))};
const controllerPath = {json.dumps(str(MODAL_CONTROLLER_JS))};

function createClassList() {{
  const values = new Set();
  return {{
    values,
    toggle(name, force) {{
      if (force) {{
        values.add(name);
      }} else {{
        values.delete(name);
      }}
    }},
    contains(name) {{
      return values.has(name);
    }}
  }};
}}

function createElement() {{
  return {{
    hidden: false,
    classList: createClassList(),
    attributes: {{}},
    textContent: "",
    setAttribute(name, value) {{
      this.attributes[name] = String(value);
    }},
    removeAttribute(name) {{
      delete this.attributes[name];
    }},
    addEventListener() {{}}
  }};
}}

const triggerButton = createElement();
triggerButton.hidden = true;
const modalBackdrop = createElement();
modalBackdrop.classList.values.add("hidden");
const optionsMainContent = createElement();
const modulesList = createElement();
const modalRoot = createElement();

const context = vm.createContext({{
  console,
  document: {{
    body: createElement()
  }},
  Node: function Node() {{}},
  HTMLElement: function HTMLElement() {{}},
  HTMLButtonElement: function HTMLButtonElement() {{}}
}});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(fn) {{
      return typeof fn === "function" ? fn : ((_key, _subs, fallback) => String(fallback || ""));
    }}
  }},
  popupModulesRegistry: {{
    resolveVisibleSettingModules(language) {{
      return language === "es" ? [{{ id: "quick-definition" }}] : [];
    }},
    resolveModuleThemeDefaults() {{
      return {{
        hueDeg: 0,
        saturationPercent: 100,
        brightnessPercent: 100,
        transparencyPercent: 100
      }};
    }},
    normalizeModulePrefs(modulePrefs) {{
      return modulePrefs && typeof modulePrefs === "object" ? modulePrefs : {{ byId: {{}}, order: [] }};
    }}
  }},
  optionsTargetLanguageModalRenderer: {{
    createRenderer() {{
      return {{
        renderModuleControls() {{}},
        syncOpenColorDrawerDomState() {{}}
      }};
    }}
  }}
}};

vm.runInContext(fs.readFileSync(utilsPath, "utf8"), context, {{ filename: utilsPath }});
vm.runInContext(fs.readFileSync(controllerPath, "utf8"), context, {{ filename: controllerPath }});

const controller = context.LexiShift.optionsTargetLanguageModal.createController({{
  settingsManager: {{
    async load() {{
      return {{}};
    }},
    getProfileModulePrefs() {{
      return {{ byId: {{}}, order: [] }};
    }}
  }},
  resolveTargetLanguage: () => "es",
  resolveSelectedProfileId: () => "default",
  optionsMainContent,
  triggerButton,
  modalBackdrop,
  modalRoot,
  modulesList
}});

controller.syncVisibility("es");
assert.equal(triggerButton.hidden, false);
assert.equal(triggerButton.classList.contains("hidden"), false);
assert.equal(triggerButton.attributes["aria-expanded"], "false");

controller.syncVisibility("de");
assert.equal(triggerButton.hidden, true);
assert.equal(triggerButton.classList.contains("hidden"), true);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
