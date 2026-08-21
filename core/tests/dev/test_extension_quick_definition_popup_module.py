from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUICK_DEFINITION_MODULE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/ui/popup_modules/quick_definition_module.js"
)
QUICK_DEFINITION_STRUCTURED_CONTENT_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/content/ui/popup_modules/quick_definition_structured_content.js"
)
POPUP_MODULES_REGISTRY_JS = (
    PROJECT_ROOT / "apps/chrome-extension/shared/srs/popup_modules_registry.js"
)
LOCALES_ROOT = PROJECT_ROOT / "apps/chrome-extension/_locales"


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
            "Node quick definition popup module test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionQuickDefinitionPopupModule(unittest.TestCase):
    def test_quick_definition_module_renders_word_info_api_result(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(QUICK_DEFINITION_MODULE_JS))};
const structuredContentPath = {json.dumps(str(QUICK_DEFINITION_STRUCTURED_CONTENT_JS))};

class FakeElement {{
  constructor(tagName) {{
    this.tagName = String(tagName || "").toUpperCase();
    this.children = [];
    this.childNodes = this.children;
    this.dataset = {{}};
    this.attributes = {{}};
    this.style = {{}};
    this.className = "";
    this.href = "";
    this.target = "";
    this.rel = "";
    this._textContent = "";
  }}
  appendChild(child) {{
    this.children.push(child);
    this.childNodes = this.children;
    return child;
  }}
  setAttribute(name, value) {{
    this.attributes[name] = String(value);
  }}
  addEventListener() {{}}
  set textContent(value) {{
    this._textContent = String(value || "");
    this.children = [];
    this.childNodes = this.children;
  }}
  get textContent() {{
    return this._textContent;
  }}
}}

const document = {{
  createElement(tagName) {{
    return new FakeElement(tagName);
  }}
}};

function collectText(node) {{
  if (!node) {{
    return "";
  }}
  const chunks = [];
  if (node._textContent) {{
    chunks.push(node._textContent);
  }}
  for (const child of node.children || []) {{
    const childText = collectText(child);
    if (childText) {{
      chunks.push(childText);
    }}
  }}
  return chunks.join(" ");
}}

function findByTag(node, tagName) {{
  if (!node) {{
    return null;
  }}
  if (node.tagName === String(tagName).toUpperCase()) {{
    return node;
  }}
  for (const child of node.children || []) {{
    const found = findByTag(child, tagName);
    if (found) {{
      return found;
    }}
  }}
  return null;
}}

function findByAttribute(node, name, value) {{
  if (!node) {{
    return null;
  }}
  if (node.attributes && node.attributes[name] === value) {{
    return node;
  }}
  for (const child of node.children || []) {{
    const found = findByAttribute(child, name, value);
    if (found) {{
      return found;
    }}
  }}
  return null;
}}

const messages = {{
  popup_definition_loading: "Loading definition...",
  popup_definition_unavailable: "No definition available.",
  popup_definition_missing: "Definition data is not installed for this word.",
  popup_definition_error: "Failed to load definition."
}};
const context = vm.createContext({{
  console,
  document,
  chrome: {{
    i18n: {{
      getMessage(key, substitutions) {{
        let message = messages[key] || "";
        if (Array.isArray(substitutions)) {{
          substitutions.forEach((value, index) => {{
            message = message.replace(`$${{index + 1}}`, String(value));
          }});
        }}
        return message;
      }}
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(
  fs.readFileSync(structuredContentPath, "utf8"),
  context,
  {{ filename: structuredContentPath }}
);
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const calls = [];
const target = document.createElement("span");
target.textContent = "perro";
target.dataset = {{
  languagePair: "en-es",
  replacement: "perro",
  displayReplacement: "perro",
  origin: "srs",
  source: "dog",
  wordPackage: JSON.stringify({{
    version: 1,
    surface: "perro",
    language_tag: "es",
    reading: "perro",
    script_forms: {{ kanji: "perro" }},
    source: {{ provider: "test" }}
  }})
}};

const moduleNode = context.LexiShift.uiQuickDefinitionModule.build(
  target,
  () => {{}},
  {{
    profileId: "suisui",
    wordInfoApi: {{
      async lookup(request, options) {{
        calls.push({{ request, options }});
        return {{
          status: "ok",
          display: "perro",
          pos: {{ label: "noun" }},
          dictionary: {{
            provider: "yomitan",
            title: "User-owned Spanish Dictionary"
          }},
          senses: [
            {{
              glosses: [{{ text: "dog" }}, {{ text: "domestic dog" }}],
              details: [
                "dog (the species Canis familiaris)",
                "犬 signifies a domestic dog; 狗 signifies a dog in older writing"
              ],
              structured_notes: [
                {{
                  kind: "orthography_variants",
                  source_text: "犬 signifies a domestic dog; 狗 signifies a dog in older writing",
                  items: [
                    {{ written_form: "犬", text: "a domestic dog" }},
                    {{ written_form: "狗", text: "a dog in older writing" }}
                  ]
                }}
              ],
              labels: ["common"],
              examples: [{{ text: "perro callejero", translation: "stray dog" }}]
            }},
            {{ glosses: [{{ text: "hound" }}], details: ["hunting dog"] }},
            {{ glosses: [{{ text: "canine" }}, {{ text: "male dog" }}] }}
          ],
          glosses: [
            {{
              text: "dog",
              details: ["dog (the species Canis familiaris)"],
              examples: [{{ text: "perro callejero", translation: "stray dog" }}]
            }},
            {{ text: "hound", raw_glosses: ["hunting dog"] }},
            {{ text: "canine" }},
            {{ text: "domestic dog" }},
            {{ text: "male dog" }},
            {{ text: "sixth gloss should not render" }}
          ],
          source_phrases: ["dog"],
          external_links: [
            {{ label: "Wiktionary", url: "https://en.wiktionary.org/wiki/perro#Spanish" }}
          ]
        }};
      }}
    }}
  }}
);

assert.ok(moduleNode);
assert.match(collectText(moduleNode), /Loading definition/);

(async () => {{
  await Promise.resolve();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(calls.length, 1);
  assert.equal(JSON.stringify(calls[0]), JSON.stringify({{
    request: {{
      languagePair: "en-es",
      profileId: "suisui",
      replacement: "perro",
      displayReplacement: "perro",
      origin: "srs",
      sourcePhrase: "dog",
      wordPackage: {{
        version: 1,
        surface: "perro",
        language_tag: "es",
        reading: "perro",
        script_forms: {{ kanji: "perro" }},
        source: {{ provider: "test" }}
      }}
    }},
    options: {{ timeoutMs: 4000, bypassCache: true }}
  }}));
  const rendered = collectText(moduleNode);
  assert.match(rendered, /perro/);
  assert.match(rendered, /noun/);
  assert.match(rendered, /User-owned Spanish Dictionary/);
  assert.doesNotMatch(rendered, /Matches:/);
  assert.ok(findByTag(moduleNode, "ol"));
  assert.match(rendered, /dog · domestic dog/);
  assert.match(rendered, /common/);
  assert.match(rendered, /dog/);
  assert.match(rendered, /Canis familiaris/);
  assert.match(rendered, /《犬》 a domestic dog/);
  assert.match(rendered, /《狗》 a dog in older writing/);
  assert.doesNotMatch(rendered, /犬 signifies/);
  assert.match(rendered, /perro callejero \\/ stray dog/);
  assert.match(rendered, /hound/);
  assert.match(rendered, /hunting dog/);
  assert.match(rendered, /canine/);
  assert.match(rendered, /domestic dog/);
  assert.match(rendered, /male dog/);
  assert.doesNotMatch(rendered, /sixth gloss should not render/);
  assert.match(rendered, /Wiktionary/);
  assert.match(rendered, /Wiktionary ↗/);
  const anchor = findByTag(moduleNode, "a");
  assert.equal(anchor.href, "https://en.wiktionary.org/wiki/perro#Spanish");

  const fallbackTarget = document.createElement("span");
  fallbackTarget.textContent = "Hund";
  fallbackTarget.dataset = {{ languagePair: "en-de", replacement: "Hund" }};
  const fallbackNode = context.LexiShift.uiQuickDefinitionModule.build(
    fallbackTarget,
    () => {{}},
    {{
      wordInfoApi: {{
        async lookup() {{
          return {{ status: "ok", display: "Hund", glosses: [{{ text: "dog" }}] }};
        }}
      }}
    }}
  );
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(findByTag(fallbackNode, "ul"));
  assert.match(collectText(fallbackNode), /dog/);

  const structuredTarget = document.createElement("span");
  structuredTarget.textContent = "時";
  structuredTarget.dataset = {{ languagePair: "en-ja", replacement: "時" }};
  const structuredNode = context.LexiShift.uiQuickDefinitionModule.build(
    structuredTarget,
    () => {{}},
    {{
      wordInfoApi: {{
        async lookup() {{
          return {{
            status: "ok",
            display: "時",
            dictionary: {{ title: "Local Japanese Dictionary" }},
            senses: [{{
              glosses: [{{ text: "fallback text should not be duplicated" }}],
              structured_content: [
                {{
                  type: "element",
                  tag: "div",
                  role: "sense",
                  children: [
                    {{
                      type: "element",
                      tag: "span",
                      role: "sense-number",
                      children: [{{ type: "text", text: "①" }}]
                    }},
                    {{
                      type: "element",
                      tag: "span",
                      role: "definition",
                      children: [{{ type: "text", text: "ある時点。" }}]
                    }},
                    {{
                      type: "element",
                      tag: "div",
                      role: "subsense",
                      children: [
                        {{ type: "image-fallback", text: "一" }},
                        {{ type: "text", text: "時刻。" }}
                      ]
                    }}
                  ]
                }}
              ]
            }}],
            external_links: []
          }};
        }}
      }}
    }}
  );
  await new Promise((resolve) => setImmediate(resolve));
  const structuredText = collectText(structuredNode);
  assert.match(structuredText, /①/);
  assert.match(structuredText, /ある時点/);
  assert.match(structuredText, /時刻/);
  assert.doesNotMatch(structuredText, /fallback text should not be duplicated/);
  assert.ok(findByAttribute(structuredNode, "data-yomitan-role", "sense"));
  assert.ok(findByAttribute(structuredNode, "data-yomitan-role", "subsense"));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_quick_definition_module_handles_missing_api_without_throwing(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(QUICK_DEFINITION_MODULE_JS))};

class FakeElement {{
  constructor(tagName) {{
    this.tagName = String(tagName || "").toUpperCase();
    this.children = [];
    this.childNodes = this.children;
    this.dataset = {{}};
    this.style = {{}};
    this.className = "";
    this._textContent = "";
  }}
  appendChild(child) {{
    this.children.push(child);
    this.childNodes = this.children;
    return child;
  }}
  set textContent(value) {{
    this._textContent = String(value || "");
    this.children = [];
    this.childNodes = this.children;
  }}
  get textContent() {{
    return this._textContent;
  }}
}}

const document = {{
  createElement(tagName) {{
    return new FakeElement(tagName);
  }}
}};
function collectText(node) {{
  return [
    node && node._textContent ? node._textContent : "",
    ...(node && node.children ? node.children.map(collectText) : [])
  ].filter(Boolean).join(" ");
}}
const context = vm.createContext({{ console, document }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const target = document.createElement("span");
target.textContent = "perro";
target.dataset = {{ languagePair: "en-es", replacement: "perro", displayReplacement: "perro" }};
const moduleNode = context.LexiShift.uiQuickDefinitionModule.build(target, () => {{}}, {{}});

(async () => {{
  await Promise.resolve();
  assert.match(collectText(moduleNode), /No definition available/);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_popup_registry_exposes_quick_definition_as_default_on_first_module(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const registryPath = {json.dumps(str(POPUP_MODULES_REGISTRY_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(registryPath, "utf8"), context, {{ filename: registryPath }});

const registry = context.LexiShift.popupModulesRegistry;
const definition = registry.getModuleDefinition("quick-definition");
assert.equal(definition.control, "toggle");
assert.equal(definition.defaultEnabled, true);
assert.equal(definition.themeEnabled, true);
assert.equal(registry.supportsThemeTuning("quick-definition"), true);

const normalized = registry.normalizeModulePrefs({{}}, {{}});
assert.equal(normalized.byId["quick-definition"].enabled, true);
assert.equal(normalized.order[0], "quick-definition");
assert.ok(registry.resolveVisibleSettingModules("es").some((item) => item.id === "quick-definition"));
"""
        _run_node(script)

    def test_quick_definition_locale_keys_exist_for_supported_locales(self) -> None:
        required_keys = {
            "module_quick_definition",
            "module_quick_definition_desc",
            "popup_definition_loading",
            "popup_definition_unavailable",
            "popup_definition_missing",
            "popup_definition_error",
        }
        for locale in ("en", "ja", "zh", "de"):
            with self.subTest(locale=locale):
                payload = json.loads((LOCALES_ROOT / locale / "messages.json").read_text())
                self.assertLessEqual(required_keys, set(payload))
                for key in required_keys:
                    self.assertTrue(str(payload[key].get("message", "")).strip())
