from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHARE_CENTER_SELECTION_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/rules/share_center/selection.js"
)
SHARE_CENTER_WORKFLOWS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/rules/share_center/workflows.js"
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
            "Node share-center workflow contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionShareCenterWorkflowContract(unittest.TestCase):
    def test_export_forwards_full_profile_and_selection_bundle_targets(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const selectionPath = {json.dumps(str(SHARE_CENTER_SELECTION_JS))};
const workflowsPath = {json.dumps(str(SHARE_CENTER_WORKFLOWS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(selectionPath, "utf8"), context, {{ filename: selectionPath }});
vm.runInContext(fs.readFileSync(workflowsPath, "utf8"), context, {{ filename: workflowsPath }});

const createWorkflows = context.LexiShift.optionsShareCenterWorkflows.createWorkflows;
const shareCenterSelection = context.LexiShift.optionsShareCenterSelection;
const normalize = (value) => JSON.parse(JSON.stringify(value));

let fullMode = true;
let selectedEntries = [];
const helperManager = {{ tag: "helper" }};
const payloadCalls = [];
const downloadCalls = [];
const exportStatuses = [];
let summaryCount = 0;

const workflows = createWorkflows({{
  rulesShareController: {{
    async generateSharePayloadWithOptions(options) {{
      payloadCalls.push(options);
      return {{
        lexishift_share: {{ version: 3, scope: options.scope }},
        data: {{
          scope: options.scope,
          profileId: options.profileId || null
        }}
      }};
    }}
  }},
  helperManager,
  shareCenterSelection,
  isFullMode: () => fullMode,
  getCurrentProfileId: () => "travel",
  getSelectedLeafEntries: () => selectedEntries,
  normalizePath: (value) => String(value || "").trim(),
  resolveExportFileName: (scope, profileId) => `${{scope}}-${{profileId}}.json`,
  formatByteSize: (size) => `${{size}} B`,
  downloadJsonFile: (content, fileName) => {{
    downloadCalls.push({{
      content: JSON.parse(content),
      fileName
    }});
    return content.length;
  }},
  setExportStatus: (message, color) => {{
    exportStatuses.push({{ message, color }});
  }},
  setImportStatus: () => {{}},
  updateSummary: () => {{
    summaryCount += 1;
  }},
  syncForProfile: async () => null,
  tr: (_key, fallback) => fallback || "",
  colors: {{ SUCCESS: "#3c5a2a", ERROR: "#b42318" }}
}});

(async () => {{
  await workflows.generateShareCode();

  assert.equal(payloadCalls.length, 1);
  assert.deepEqual(normalize(payloadCalls[0]), {{
    scope: "profile",
    profileId: "travel"
  }});
  assert.equal(downloadCalls.length, 1);
  assert.equal(downloadCalls[0].fileName, "profile-travel.json");
  assert.equal(downloadCalls[0].content.lexishift_share.scope, "profile");
  assert.equal(summaryCount, 1);
  assert.match(exportStatuses[0].message, /Exported profile-travel\\.json/);

  fullMode = false;
  payloadCalls.length = 0;
  downloadCalls.length = 0;
  exportStatuses.length = 0;
  selectedEntries = [
    {{
      meta: {{
        kind: "profile_settings",
        scope: "srs",
        enabled: true,
        label: "Profile settings",
        path: "Profile > Configuration"
      }}
    }},
    {{
      meta: {{
        kind: "ruleset_item",
        scope: "ruleset",
        enabled: true,
        label: "travel.json",
        rulesetPath: "shared/imported/travel.json",
        rulesetName: "travel.json",
        path: "Profile > Rulesets > travel.json"
      }}
    }},
    {{
      meta: {{
        kind: "srs_pair_item",
        scope: "srs_pair",
        enabled: true,
        label: "en-ja",
        srsPair: "en-ja",
        path: "Profile > SRS data > en-ja"
      }}
    }},
    {{
      meta: {{
        kind: "appearance_theme",
        scope: "appearance_theme",
        enabled: true,
        label: "Theme/colors",
        path: "Profile > Appearance > Theme/colors"
      }}
    }},
    {{
      meta: {{
        kind: "module_item",
        scope: "module_item",
        enabled: true,
        label: "Kana helper",
        moduleId: "kana_helper",
        moduleTargetLanguage: "ja",
        path: "Profile > Modules > Kana helper"
      }}
    }}
  ];

  await workflows.generateShareCode();

  assert.equal(payloadCalls.length, 1);
  assert.equal(payloadCalls[0].scope, "bundle");
  assert.equal(payloadCalls[0].profileId, "travel");
  assert.equal(payloadCalls[0].helperManager, helperManager);
  assert.deepEqual(normalize(payloadCalls[0].bundleTargets), [
    {{ kind: "profile_settings" }},
    {{
      kind: "ruleset",
      rulesetPath: "shared/imported/travel.json",
      rulesetName: "travel.json"
    }},
    {{
      kind: "srs_pair",
      pair: "en-ja"
    }},
    {{ kind: "appearance_theme" }},
    {{
      kind: "module_item",
      moduleId: "kana_helper",
      targetLanguage: "ja"
    }}
  ]);
  assert.equal(downloadCalls.length, 1);
  assert.equal(downloadCalls[0].fileName, "bundle-travel.json");
  assert.equal(downloadCalls[0].content.lexishift_share.scope, "bundle");
  assert.equal(summaryCount, 2);
  assert.match(exportStatuses[0].message, /Exported bundle-travel\\.json/);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_import_forwards_payload_context_and_only_reloads_when_needed(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const selectionPath = {json.dumps(str(SHARE_CENTER_SELECTION_JS))};
const workflowsPath = {json.dumps(str(SHARE_CENTER_WORKFLOWS_JS))};
const timers = [];
const context = vm.createContext({{
  console,
  setTimeout(handler, delay) {{
    timers.push({{ handler, delay }});
    return timers.length;
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(selectionPath, "utf8"), context, {{ filename: selectionPath }});
vm.runInContext(fs.readFileSync(workflowsPath, "utf8"), context, {{ filename: workflowsPath }});

const createWorkflows = context.LexiShift.optionsShareCenterWorkflows.createWorkflows;
const shareCenterSelection = context.LexiShift.optionsShareCenterSelection;
const normalize = (value) => JSON.parse(JSON.stringify(value));

let importPayload = '{{"lexishift_share":{{"version":2,"scope":"ruleset"}},"data":{{}}}}';
const helperManager = {{ tag: "helper" }};
const importCalls = [];
const importStatuses = [];
const syncCalls = [];
let reloadCount = 0;
const importFileNameOutput = {{ textContent: "" }};
const nextResults = [
  {{
    scope: "ruleset",
    ruleset: {{ name: "Travel deck" }}
  }},
  {{
    scope: "bundle",
    rulesets: [{{ name: "Travel deck" }}],
    modules: [{{ moduleId: "kana_helper" }}],
    srsPairs: [],
    appliedProfileSettings: false,
    requiresReload: false
  }},
  {{
    scope: "bundle",
    rulesets: [],
    modules: [],
    srsPairs: [{{ pair: "en-ja" }}],
    appliedProfileSettings: true,
    requiresReload: true
  }}
];

const workflows = createWorkflows({{
  rulesShareController: {{
    async importShareCodeWithOptions(options) {{
      importCalls.push(options);
      return nextResults.shift();
    }}
  }},
  helperManager,
  shareCenterSelection,
  isFullMode: () => false,
  getCurrentProfileId: () => "travel",
  getSelectedLeafEntries: () => [],
  normalizePath: (value) => String(value || "").trim(),
  resolveExportFileName: () => "unused.json",
  formatByteSize: () => "0 B",
  downloadJsonFile: () => 0,
  setExportStatus: () => {{}},
  setImportStatus: (message, color) => {{
    importStatuses.push({{ message, color }});
  }},
  updateSummary: () => {{}},
  syncForProfile: async (options) => {{
    syncCalls.push(options);
    return null;
  }},
  tr: (_key, fallback) => fallback || "",
  colors: {{ SUCCESS: "#3c5a2a", ERROR: "#b42318" }},
  importFileInput: {{
    files: [{{
      name: "import.json",
      async text() {{
        return importPayload;
      }}
    }}]
  }},
  importFileNameOutput,
  reloadPage: () => {{
    reloadCount += 1;
  }}
}});

(async () => {{
  await workflows.importShareCode();

  assert.equal(importCalls.length, 1);
  assert.equal(importCalls[0].code, importPayload);
  assert.equal(importCalls[0].useCjk, false);
  assert.equal(importCalls[0].profileId, "travel");
  assert.equal(importCalls[0].helperManager, helperManager);
  assert.deepEqual(normalize(syncCalls[0]), {{ profileId: "travel" }});
  assert.equal(importFileNameOutput.textContent, "import.json");
  assert.equal(reloadCount, 0);
  assert.equal(timers.length, 0);
  assert.equal(
    importStatuses[0].message,
    "Imported Travel deck and enabled it for this profile."
  );

  importPayload = '{{"lexishift_share":{{"version":3,"scope":"bundle"}},"data":{{"kind":"rulesets_modules"}}}}';
  await workflows.importShareCode();

  assert.equal(importCalls.length, 2);
  assert.equal(importCalls[1].code, importPayload);
  assert.deepEqual(normalize(syncCalls[1]), {{ profileId: "travel" }});
  assert.equal(reloadCount, 0);
  assert.equal(timers.length, 0);
  assert.equal(
    importStatuses[1].message,
    "Imported 1 rulesets and 1 module settings."
  );

  importPayload = '{{"lexishift_share":{{"version":3,"scope":"bundle"}},"data":{{"kind":"profile_settings"}}}}';
  await workflows.importShareCode();

  assert.equal(importCalls.length, 3);
  assert.equal(importCalls[2].code, importPayload);
  assert.equal(syncCalls.length, 2);
  assert.equal(reloadCount, 0);
  assert.equal(timers.length, 1);
  assert.equal(timers[0].delay, 120);
  assert.match(
    importStatuses[2].message,
    /Imported: profile settings \\/ 1 SRS pairs\\. Reloading options…/
  );

  timers[0].handler();
  assert.equal(reloadCount, 1);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
