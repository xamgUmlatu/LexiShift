from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER_CLIENT_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_client.js"
WORD_INFO_API_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/word_info_api.js"
HELPER_ERROR_COPY_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/helper_error_copy.js"
HELPER_BASE_METHODS_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper/base_methods.js"
HELPER_DIAGNOSTICS_METHODS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/helper/diagnostics_methods.js"
)
HELPER_SRS_SET_METHODS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/helper/srs_set_methods.js"
)
HELPER_MANAGER_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/helper_manager.js"
TRANSLATE_RESOLVER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/core/bootstrap/translate_resolver.js"
)
HELPER_ACTIONS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/helper/actions_controller.js"
)
PAGE_INIT_JS = PROJECT_ROOT / "apps/chrome-extension/options/controllers/page/init_controller.js"


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
            "Node helper status profile contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionHelperStatusProfileContract(unittest.TestCase):
    def test_helper_client_status_includes_profile_id_when_provided(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
const normalize = (value) => JSON.parse(JSON.stringify(value));
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload) {{
    calls.push({{ type, payload }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.getStatus("suisui");
  await client.getStatus();
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{ type: "status", payload: {{ profile_id: "suisui" }} }},
    {{ type: "status", payload: {{}} }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_client_routes_srs_admission_suppression(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload) {{
    calls.push({{ type, payload }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.suppressSrsAdmission({{
    pair: "en-es",
    profile_id: "default",
    lemma: "perro",
    reason: "user_blocked"
  }});
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], {{
    type: "srs_admission_suppress",
    payload: {{
      pair: "en-es",
      profile_id: "default",
      lemma: "perro",
      reason: "user_blocked"
    }}
  }});
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_client_routes_srs_items_list(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload) {{
    calls.push({{ type, payload }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.listSrsItems("en-es", "default");
  await client.listSrsItems("en-ja", "suisui", {{ compact: true }});
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{
      type: "srs_items_list",
      payload: {{ pair: "en-es", profile_id: "default" }}
    }},
    {{
      type: "srs_items_list",
      payload: {{ pair: "en-ja", profile_id: "suisui", compact: true }}
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_client_routes_srs_item_rule_details(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload) {{
    calls.push({{ type, payload }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.getSrsItemRuleDetails("en-es", "default", "perro", 3);
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{
      type: "srs_item_rule_details",
      payload: {{ pair: "en-es", profile_id: "default", lemma: "perro", limit: 3 }}
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_client_routes_word_info_lookup(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload, timeoutMs) {{
    calls.push({{ type, payload, timeoutMs }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.lookupWordInfo({{
    pair: "en-es",
    profile_id: "default",
    lemma: "perro",
    display: "perro"
  }}, 1234);
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{
      type: "word_info_lookup",
      payload: {{
        pair: "en-es",
        profile_id: "default",
        lemma: "perro",
        display: "perro"
      }},
      timeoutMs: 1234
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_word_info_api_normalizes_and_caches_lookup_requests(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const apiPath = {json.dumps(str(WORD_INFO_API_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(apiPath, "utf8"), context, {{ filename: apiPath }});

const calls = [];
const api = context.LexiShift.wordInfoApi.create({{
  helperClient: {{
    async lookupWordInfo(payload, timeoutMs) {{
      calls.push({{ payload, timeoutMs }});
      return {{
        ok: true,
        data: {{
          status: "ok",
          pair: payload.pair,
          profile_id: payload.profile_id,
          lemma: payload.lemma,
          glosses: [{{ text: "dog" }}]
        }}
      }};
    }}
  }}
}});

(async () => {{
  const request = {{
    languagePair: "EN-ES",
    profileId: "alpha",
    replacement: " perro ",
    displayReplacement: "Perro",
    origin: "SRS",
    sourcePhrase: "dog",
    wordPackage: {{ surface: "perro" }}
  }};
  const first = await api.lookup(request, {{ timeoutMs: 1234 }});
  const second = await api.lookup(request, {{ timeoutMs: 9999 }});
  assert.equal(first.glosses[0].text, "dog");
  assert.deepEqual(first, second);
  assert.equal(calls.length, 1);
  assert.equal(JSON.stringify(calls[0]), JSON.stringify({{
    payload: {{
      pair: "en-es",
      profile_id: "alpha",
      lemma: "perro",
      display: "Perro",
      origin: "srs",
      source_phrase: "dog",
      word_package: {{ surface: "perro" }}
    }},
    timeoutMs: 1234
  }}));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_manager_lookup_word_info_uses_shared_api(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const helperErrorCopyPath = {json.dumps(str(HELPER_ERROR_COPY_JS))};
const wordInfoApiPath = {json.dumps(str(WORD_INFO_API_JS))};
const baseMethodsPath = {json.dumps(str(HELPER_BASE_METHODS_JS))};
const srsSetMethodsPath = {json.dumps(str(HELPER_SRS_SET_METHODS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
for (const scriptPath of [
  helperErrorCopyPath,
  wordInfoApiPath,
  baseMethodsPath,
  srsSetMethodsPath
]) {{
  vm.runInContext(fs.readFileSync(scriptPath, "utf8"), context, {{ filename: scriptPath }});
}}

function Manager() {{
  this.i18n = {{ t: (_key, _subs, fallback) => fallback }};
  this.logger = () => {{}};
}}
context.LexiShift.installHelperBaseMethods(Manager.prototype);
context.LexiShift.installHelperSrsSetMethods(Manager.prototype);

const calls = [];
const manager = new Manager();
manager.getClient = () => ({{
  async lookupWordInfo(payload, timeoutMs) {{
    calls.push({{ payload, timeoutMs }});
    return {{ ok: true, data: {{ status: "ok", pair: payload.pair, profile_id: payload.profile_id }} }};
  }}
}});

(async () => {{
  const result = await manager.lookupWordInfo(
    {{
      pair: "en-es",
      lemma: "perro",
      display: "perro",
      sourcePhrase: "dog"
    }},
    {{ profileId: "alpha", timeoutMs: 1234 }}
  );
  assert.equal(result.status, "ok");
  assert.equal(JSON.stringify(calls), JSON.stringify([
    {{
      payload: {{
        pair: "en-es",
        profile_id: "alpha",
        lemma: "perro",
        display: "perro",
        origin: "",
        source_phrase: "dog"
      }},
      timeoutMs: 1234
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_client_routes_semantic_pack_install_with_long_timeout(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientPath = {json.dumps(str(HELPER_CLIENT_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(clientPath, "utf8"), context, {{ filename: clientPath }});

const HelperClient = context.LexiShift.helperClient;
const calls = [];
const client = new HelperClient({{
  async send(type, payload, timeoutMs) {{
    calls.push({{ type, payload, timeoutMs }});
    return {{ ok: true, data: null }};
  }}
}});

(async () => {{
  await client.installSemanticPack({{
    pair: "en-es",
    profile_id: "semantic-alpha",
    semantic_inventory_path: "/tmp/inventory.json",
    data_root: "/tmp/lexishift-data"
  }});
  assert.equal(calls.length, 1);
  assert.equal(calls[0].type, "install_semantic_pack");
  assert.equal(calls[0].payload.profile_id, "semantic-alpha");
  assert.equal(calls[0].timeoutMs, 60000);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_manager_lists_srs_items_with_profile_id(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const files = [
  {json.dumps(str(HELPER_ERROR_COPY_JS))},
  {json.dumps(str(HELPER_CLIENT_JS))},
  {json.dumps(str(HELPER_BASE_METHODS_JS))},
  {json.dumps(str(HELPER_DIAGNOSTICS_METHODS_JS))},
  {json.dumps(str(HELPER_SRS_SET_METHODS_JS))},
  {json.dumps(str(HELPER_MANAGER_JS))}
];
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  helperTransportExtension: {{
    calls: [],
    async send(type, payload, timeoutMs) {{
      this.calls.push({{ type, payload, timeoutMs }});
      return {{
        ok: true,
        data: {{
          status: "ok",
          summary: {{ total: 1 }},
          items: [{{ lemma: "perro" }}]
        }}
      }};
    }}
  }}
}};
for (const file of files) {{
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(
    file === {json.dumps(str(HELPER_MANAGER_JS))}
      ? `${{source}}\nthis.__HelperManager = HelperManager;`
      : source,
    context,
    {{ filename: file }}
  );
}}

const manager = new context.__HelperManager({{
  t: (_key, _args, fallback) => fallback || ""
}}, () => {{}});

(async () => {{
  const result = await manager.listSrsItems("en-es", {{ profileId: "alpha" }});
  assert.equal(result.summary.total, 1);
  assert.equal(JSON.stringify(context.LexiShift.helperTransportExtension.calls), JSON.stringify([
    {{
      type: "srs_items_list",
      payload: {{ pair: "en-es", profile_id: "alpha" }},
      timeoutMs: 4000
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_manager_loads_srs_rule_details_with_profile_id(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const files = [
  {json.dumps(str(HELPER_ERROR_COPY_JS))},
  {json.dumps(str(HELPER_CLIENT_JS))},
  {json.dumps(str(HELPER_BASE_METHODS_JS))},
  {json.dumps(str(HELPER_DIAGNOSTICS_METHODS_JS))},
  {json.dumps(str(HELPER_SRS_SET_METHODS_JS))},
  {json.dumps(str(HELPER_MANAGER_JS))}
];
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  helperTransportExtension: {{
    calls: [],
    async send(type, payload, timeoutMs) {{
      this.calls.push({{ type, payload, timeoutMs }});
      return {{
        ok: true,
        data: {{
          status: "ok",
          lemma: payload.lemma,
          rule_count: 1,
          rules: [{{ source_phrase: "dog", replacement: payload.lemma }}]
        }}
      }};
    }}
  }}
}};
for (const file of files) {{
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(
    file === {json.dumps(str(HELPER_MANAGER_JS))}
      ? `${{source}}\nthis.__HelperManager = HelperManager;`
      : source,
    context,
    {{ filename: file }}
  );
}}

const manager = new context.__HelperManager({{
  t: (_key, _args, fallback) => fallback || ""
}}, () => {{}});

(async () => {{
  const result = await manager.getSrsItemRuleDetails("en-es", " perro ", {{
    profileId: "alpha",
    limit: 5
  }});
  assert.equal(result.rules[0].replacement, "perro");
  assert.equal(JSON.stringify(context.LexiShift.helperTransportExtension.calls), JSON.stringify([
    {{
      type: "srs_item_rule_details",
      payload: {{ pair: "en-es", profile_id: "alpha", lemma: "perro", limit: 5 }},
      timeoutMs: 4000
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_manager_discards_srs_item_through_suppression_route(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const files = [
  {json.dumps(str(HELPER_ERROR_COPY_JS))},
  {json.dumps(str(HELPER_CLIENT_JS))},
  {json.dumps(str(HELPER_BASE_METHODS_JS))},
  {json.dumps(str(HELPER_DIAGNOSTICS_METHODS_JS))},
  {json.dumps(str(HELPER_SRS_SET_METHODS_JS))},
  {json.dumps(str(HELPER_MANAGER_JS))}
];
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  helperTransportExtension: {{
    calls: [],
    async send(type, payload, timeoutMs) {{
      this.calls.push({{ type, payload, timeoutMs }});
      return {{
        ok: true,
        data: {{
          status: "ok",
          lemma: payload.lemma,
          reason: payload.reason,
          active_item_removed: true
        }}
      }};
    }}
  }}
}};
for (const file of files) {{
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(
    file === {json.dumps(str(HELPER_MANAGER_JS))}
      ? `${{source}}\nthis.__HelperManager = HelperManager;`
      : source,
    context,
    {{ filename: file }}
  );
}}

const manager = new context.__HelperManager({{
  t: (_key, _args, fallback) => fallback || ""
}}, () => {{}});

(async () => {{
  const result = await manager.discardSrsItem("en-es", " perro ", {{ profileId: "alpha" }});
  assert.equal(result.reason, "user_blocked");
  assert.equal(JSON.stringify(context.LexiShift.helperTransportExtension.calls), JSON.stringify([
    {{
      type: "srs_admission_suppress",
      payload: {{
        pair: "en-es",
        profile_id: "alpha",
        lemma: "perro",
        reason: "user_blocked",
        note: "srs_words_dashboard_discard"
      }},
      timeoutMs: 4000
    }}
  ]));
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_manager_installs_semantic_pack_and_clears_pair_cache(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const files = [
  {json.dumps(str(HELPER_ERROR_COPY_JS))},
  {json.dumps(str(HELPER_CLIENT_JS))},
  {json.dumps(str(HELPER_BASE_METHODS_JS))},
  {json.dumps(str(HELPER_DIAGNOSTICS_METHODS_JS))},
  {json.dumps(str(HELPER_SRS_SET_METHODS_JS))},
  {json.dumps(str(HELPER_MANAGER_JS))}
];
const context = vm.createContext({{ console }});
const normalize = (value) => JSON.parse(JSON.stringify(value));
context.globalThis = context;
context.LexiShift = {{
  helperCache: {{
    clearCalls: [],
    async clearPair(pair, options) {{
      this.clearCalls.push({{ pair, options }});
    }}
  }},
  helperTransportExtension: {{
    calls: [],
    async send(type, payload, timeoutMs) {{
      this.calls.push({{ type, payload, timeoutMs }});
      return {{
        ok: true,
        data: {{
          status: "ok",
          pack_id: payload.pack_id,
          profile_id: payload.profile_id,
          summary: {{ rule_count: 49, competition_set_count: 49 }}
        }}
      }};
    }}
  }}
}};
for (const file of files) {{
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(
    file === {json.dumps(str(HELPER_MANAGER_JS))}
      ? `${{source}}\nthis.__HelperManager = HelperManager;`
      : source,
    context,
    {{ filename: file }}
  );
}}

const manager = new context.__HelperManager({{
  t: (_key, _args, fallback) => fallback || ""
}}, () => {{}});

(async () => {{
  const result = await manager.installSemanticPack("en-es", {{
    profileId: "semantic-alpha",
    packId: "en-es-pack-v1",
    allowDefaultDataRoot: false,
    dataRoot: "/tmp/lexishift-data"
  }});
  assert.equal(result.status, "ok");
  const call = context.LexiShift.helperTransportExtension.calls[0];
  assert.equal(call.type, "install_semantic_pack");
  assert.equal(call.timeoutMs, 60000);
  assert.deepEqual(normalize(call.payload), {{
    pair: "en-es",
    profile_id: "semantic-alpha",
    pack_id: "en-es-pack-v1",
    data_root: "/tmp/lexishift-data",
    allow_default_data_root: false,
    dry_run: false,
    no_pack_copy: false
  }});
  assert.deepEqual(normalize(context.LexiShift.helperCache.clearCalls), [
    {{ pair: "en-es", options: {{ profileId: "semantic-alpha" }} }}
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_helper_actions_refresh_status_forwards_profile_id(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const translateResolverPath = {json.dumps(str(TRANSLATE_RESOLVER_JS))};
const actionsPath = {json.dumps(str(HELPER_ACTIONS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(translateResolverPath, "utf8"), context, {{ filename: translateResolverPath }});
vm.runInContext(fs.readFileSync(actionsPath, "utf8"), context, {{ filename: actionsPath }});

const createController = context.LexiShift.optionsHelperActions.createController;
const statusUpdates = [];
let capturedProfileId = null;
const controller = createController({{
  t: (_key, _subs, fallback) => fallback || "",
  helperManager: {{
    async getStatus(profileId) {{
      capturedProfileId = profileId;
      return {{ message: "Helper connected.", lastRun: "2026-04-22T00:00:00Z" }};
    }}
  }},
  setHelperStatus(message, lastRun) {{
    statusUpdates.push([message, lastRun]);
  }}
}});

(async () => {{
  await controller.refreshStatus("suisui");
  assert.equal(capturedProfileId, "suisui");
  assert.deepEqual(statusUpdates, [
    ["Connecting…", ""],
    ["Helper connected.", "2026-04-22T00:00:00Z"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_page_init_refreshes_helper_status_for_selected_profile(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const translateResolverPath = {json.dumps(str(TRANSLATE_RESOLVER_JS))};
const pageInitPath = {json.dumps(str(PAGE_INIT_JS))};
const scheduledTasks = [];
const context = vm.createContext({{
  console,
  setTimeout(callback) {{
    scheduledTasks.push(callback);
    return scheduledTasks.length;
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(translateResolverPath, "utf8"), context, {{ filename: translateResolverPath }});
vm.runInContext(fs.readFileSync(pageInitPath, "utf8"), context, {{ filename: pageInitPath }});

const createController = context.LexiShift.optionsPageInit.createController;
let refreshedProfileId = null;
const calls = [];
const srsBrowsingAdmissionSignalsInput = {{ checked: false }};
const controller = createController({{
  settingsManager: {{
    defaults: {{
      highlightColor: "#ffcc00",
      maxReplacementsPerPage: 20,
      maxReplacementsPerLemmaPerPage: 2
    }},
    currentRules: [],
    async load() {{
      return {{
        enabled: true,
        highlightEnabled: true,
        highlightColor: "#ffcc00",
        maxOnePerTextBlock: false,
        allowAdjacentReplacements: false,
        maxReplacementsPerPage: 20,
        maxReplacementsPerLemmaPerPage: 2,
        debugEnabled: false,
        debugFocusWord: "",
        uiLanguage: "system",
        rules: [],
        rulesSource: "editor",
        rulesUpdatedAt: "",
        rulesFileName: "",
        customRulesetEnabled: true,
        srsBrowsingAdmissionSignalsEnabled: true,
        srsSelectedProfileId: "suisui"
      }};
    }},
    getSelectedSrsProfileId(items) {{
      return items.srsSelectedProfileId || "default";
    }},
    getProfileLanguagePrefs(_items, _options) {{
      return {{ sourceLanguage: "en", targetLanguage: "es" }};
    }},
    getProfileUiPrefs(_items, options) {{
      return {{
        profileId: options.profileId,
        backgroundBackdropColor: "#4455aa",
        backgroundAssetId: "asset-1"
      }};
    }},
    async publishProfileLanguagePrefs() {{}}
  }},
  i18n: {{
    async load() {{
      calls.push(["i18n"]);
    }}
  }},
  helperActionsController: {{
    async refreshStatus(profileId) {{
      calls.push(["helper", profileId]);
      refreshedProfileId = profileId;
    }}
  }},
  applyLanguagePrefsToInputs() {{
    return "en-es";
  }},
  applyProfileBackgroundFromPrefs: async (uiPrefs, options) => {{
    calls.push([
      "theme",
      uiPrefs.profileId,
      uiPrefs.backgroundBackdropColor,
      options.eagerBackdrop,
      options.skipImageAsset
    ]);
  }},
  loadSrsProfileForPair: async (_items, pairKey, options) => {{
    calls.push([
      "profile",
      pairKey,
      options && options.visualOnly === true,
      options && options.skipHelperProfiles === true,
      options && options.backgroundSync === true,
      options && options.skipPageImageAsset === true
    ]);
  }},
  updateRulesSourceUI: () => {{}},
  updateRulesMeta: () => {{}},
  applyTargetLanguagePrefsLocalization: () => {{}},
  renderSrsProfileStatus: () => {{}},
  renderProfileBackgroundStatus: () => {{}},
  setSrsProfileStatusLocalized: () => {{}},
  setHelperStatus: () => {{}},
  elements: {{
    enabledInput: {{ checked: false }},
    highlightEnabledInput: {{ checked: false }},
    highlightColorInput: {{ value: "" }},
    highlightColorText: {{ value: "", disabled: false }},
    maxOnePerBlockInput: {{ checked: false }},
    allowAdjacentInput: {{ checked: false }},
    maxReplacementsPerPageInput: {{ value: "" }},
    maxReplacementsPerLemmaPageInput: {{ value: "" }},
    debugEnabledInput: {{ checked: false }},
    debugFocusInput: {{ value: "", disabled: false }},
    srsRulegenOutput: {{ textContent: "stale" }},
    debugHelperTestOutput: {{ textContent: "stale" }},
    debugOpenDataDirOutput: {{ textContent: "stale" }},
    languageSelect: {{ value: "" }},
    rulesInput: {{ value: "" }},
    fileStatus: {{ textContent: "" }},
    customRulesetEnabledInput: {{ checked: false }},
    srsBrowsingAdmissionSignalsInput
  }}
}});

(async () => {{
  await controller.load();
  assert.equal(refreshedProfileId, null);
  assert.equal(srsBrowsingAdmissionSignalsInput.checked, true);
  assert.deepEqual(calls, [
    ["theme", "suisui", "#4455aa", true, true],
    ["i18n"],
    ["profile", "en-es", true, true, false, false]
  ]);
  while (scheduledTasks.length) {{
    await scheduledTasks.shift()();
  }}
  assert.equal(refreshedProfileId, "suisui");
  assert.deepEqual(calls, [
    ["theme", "suisui", "#4455aa", true, true],
    ["i18n"],
    ["profile", "en-es", true, true, false, false],
    ["theme", "suisui", "#4455aa", true, undefined],
    ["profile", "en-es", false, false, true, true],
    ["helper", "suisui"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
