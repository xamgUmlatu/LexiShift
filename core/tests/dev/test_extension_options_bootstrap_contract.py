from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPTIONS_JS = PROJECT_ROOT / "apps/chrome-extension/options.js"
CONTROLLER_GRAPH_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/bootstrap/controller_graph.js"
)
LOCALIZATION_SERVICE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/localization_service.js"
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
            "Node options-bootstrap contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionOptionsBootstrapContract(unittest.TestCase):
    def test_localization_service_preserves_static_text_when_explicit_empty_fallback_is_requested(
        self,
    ) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(LOCALIZATION_SERVICE_JS))};
const heading = {{
  textContent: "New-word preferences",
  getAttribute(name) {{
    return name === "data-i18n" ? "section_srs_admission_preferences" : null;
  }}
}};
const placeholderNode = {{
  attributes: {{}},
  getAttribute(name) {{
    return name === "data-i18n-placeholder" ? "label_srs_topic_interests" : null;
  }},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }}
}};
const context = vm.createContext({{
  console,
  navigator: {{ language: "en-US" }},
  document: {{
    title: "Options",
    querySelectorAll(selector) {{
      if (selector === "[data-i18n]") {{
        return [heading];
      }}
      if (selector === "[data-i18n-placeholder]") {{
        return [placeholderNode];
      }}
      return [];
    }}
  }}
}});
context.globalThis = context;
vm.runInContext(
  `${{fs.readFileSync(modulePath, "utf8")}}\\nthis.__LocalizationService = LocalizationService;`,
  context,
  {{ filename: modulePath }}
);

const LocalizationService = context.__LocalizationService;
const i18n = new LocalizationService();

assert.equal(i18n.t("missing_key", null, ""), "");
assert.equal(i18n.t("missing_key", null, "Fallback"), "Fallback");
assert.equal(i18n.t("missing_key"), "missing_key");

i18n.apply();

assert.equal(heading.textContent, "New-word preferences");
assert.deepEqual(placeholderNode.attributes, {{}});
assert.equal(context.document.title, "Options");
"""
        _run_node(script)

    def test_options_root_fails_fast_when_controller_graph_module_is_missing(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(OPTIONS_JS))};
const context = vm.createContext({{
  console,
  SettingsManager: function SettingsManager() {{}},
  LocalizationService: function LocalizationService() {{
    this.t = (_key, _subs, fallback) => fallback || "";
    this.apply = () => {{}};
  }},
  RulesManager: function RulesManager() {{}},
  UIManager: function UIManager() {{ this.dom = {{}}; }},
  HelperManager: function HelperManager() {{}}
}});
context.globalThis = context;
context.LexiShift = {{
  optionsUiBridge: {{
    createUiBridge() {{
      return {{
        setStatus() {{}},
        setHelperStatus() {{}},
        updateRulesSourceUI() {{}},
        updateRulesMeta() {{}}
      }};
    }}
  }},
  optionsControllerFactoryResolver: {{
    createResolver() {{
      return {{ requireControllerFactory() {{ return () => ({{}}); }} }};
    }}
  }},
  optionsDomAliases: {{
    createDomAliases(dom) {{
      return dom || {{}};
    }}
  }},
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return translate;
    }}
  }},
  optionsLanguagePrefsAdapter: {{
    createAdapter() {{
      return {{
        resolvePairFromInputs() {{ return "en-ja"; }},
        resolveCurrentTargetLanguage() {{ return "ja"; }},
        applyLanguagePrefsToInputs() {{}}
      }};
    }}
  }},
  optionsControllerAdapters: {{
    createControllerAdapters() {{
      return {{}};
    }}
  }}
}};

assert.throws(
  () => {{
    vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});
  }},
  /Missing required bootstrap module: optionsControllerGraph/
);
"""
        _run_node(script)

    def test_options_root_binds_events_before_page_init_after_bootstrap(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(OPTIONS_JS))};
const calls = [];
const context = vm.createContext({{
  console,
  SettingsManager: function SettingsManager() {{
    calls.push("settingsManager");
  }},
  LocalizationService: function LocalizationService() {{
    this.t = (_key, _subs, fallback) => fallback || "";
    this.apply = () => calls.push("i18n.apply");
  }},
  RulesManager: function RulesManager(settingsManager, i18n) {{
    calls.push(["rulesManager", Boolean(settingsManager), Boolean(i18n)]);
  }},
  UIManager: function UIManager() {{
    this.dom = {{ root: true }};
    this.COLORS = {{}};
    calls.push("uiManager");
  }},
  HelperManager: function HelperManager(_i18n, logOptions) {{
    calls.push(["helperManager", typeof logOptions]);
  }}
}});
context.globalThis = context;
context.LexiShift = {{
  optionsUiBridge: {{
    createUiBridge({{ ui }}) {{
      calls.push(["uiBridge", Boolean(ui && ui.dom && ui.dom.root)]);
      return {{
        setStatus() {{}},
        setHelperStatus() {{}},
        updateRulesSourceUI() {{}},
        updateRulesMeta() {{}}
      }};
    }}
  }},
  optionsControllerFactoryResolver: {{
    createResolver() {{
      calls.push("controllerFactoryResolver");
      return {{ requireControllerFactory() {{ return () => ({{}}); }} }};
    }}
  }},
  optionsDomAliases: {{
    createDomAliases(dom) {{
      calls.push(["domAliases", Boolean(dom && dom.root)]);
      return {{ aliasReady: true }};
    }}
  }},
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      calls.push(["translateResolver", typeof translate]);
      return translate;
    }}
  }},
  optionsControllerGraph: {{
    createControllerGraph(options) {{
      calls.push([
        "controllerGraph",
        Boolean(options.settingsManager),
        Boolean(options.uiBridge),
        typeof options.requireControllerFactory,
        typeof options.languagePrefsAdapterFactory,
        typeof options.controllerAdaptersFactory,
        Boolean(options.dom && options.dom.aliasReady)
      ]);
      return {{
        eventWiringController: {{
          bind() {{
            calls.push("event.bind");
          }}
        }},
        pageInitController: {{
          load() {{
            calls.push("page.load");
          }}
        }}
      }};
    }}
  }},
  optionsLanguagePrefsAdapter: {{
    createAdapter() {{
      calls.push("languagePrefsAdapterFactory");
      return {{
        resolvePairFromInputs() {{ return "en-ja"; }},
        resolveCurrentTargetLanguage() {{ return "ja"; }},
        applyLanguagePrefsToInputs() {{}}
      }};
    }}
  }},
  optionsControllerAdapters: {{
    createControllerAdapters() {{
      calls.push("controllerAdaptersFactory");
      return {{}};
    }}
  }}
}};

vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const bindIndex = calls.indexOf("event.bind");
const loadIndex = calls.indexOf("page.load");
assert.notEqual(bindIndex, -1);
assert.notEqual(loadIndex, -1);
assert.ok(bindIndex < loadIndex);

const graphCall = calls.find((entry) => Array.isArray(entry) && entry[0] === "controllerGraph");
assert.deepEqual(
  graphCall,
  ["controllerGraph", true, true, "function", "function", "function", true]
);
"""
        _run_node(script)

    def test_controller_graph_fails_fast_when_graph_elements_module_is_missing(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(CONTROLLER_GRAPH_JS))};
const context = vm.createContext({{
  console
}});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return translate;
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createControllerGraph = context.LexiShift.optionsControllerGraph.createControllerGraph;
assert.throws(
  () => createControllerGraph({{
    settingsManager: {{}},
    i18n: {{}},
    t: (_key, _subs, fallback) => fallback || "",
    rulesManager: {{}},
    ui: {{}},
    helperManager: {{}},
    uiBridge: {{}},
    requireControllerFactory: () => () => ({{}}),
    languagePrefsAdapterFactory: () => ({{}}),
    controllerAdaptersFactory: () => ({{}}),
    dom: {{}}
  }}),
  /Missing controller graph elements bootstrap module/
);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
