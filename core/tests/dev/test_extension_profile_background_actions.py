from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKGROUND_ACTIONS_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/profile/background/actions.js"
)
BACKGROUND_RUNTIME_BRIDGE_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/profile/background/runtime_bridge.js"
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
            "Node profile-background action test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionProfileBackgroundActions(unittest.TestCase):
    def test_runtime_bridge_can_skip_page_image_without_skipping_preview(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const bridgePath = {json.dumps(str(BACKGROUND_RUNTIME_BRIDGE_JS))};
const context = vm.createContext({{ console, Blob }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _subs, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(bridgePath, "utf8"), context, {{ filename: bridgePath }});

const imageBlob = new Blob(["image"], {{ type: "image/png" }});
const calls = [];
const bridge = context.LexiShift.optionsProfileBackgroundRuntimeBridge.createBridge({{
  profileMediaStore: {{
    async getAsset(assetId) {{
      calls.push(["getAsset", assetId]);
      return {{ blob: imageBlob, mime_type: "image/png", byte_size: imageBlob.size }};
    }}
  }},
  previewManager: {{
    clearPreview() {{
      calls.push(["previewClear"]);
    }},
    setPreviewFromBlob(blob) {{
      calls.push(["previewBlob", blob === imageBlob]);
    }},
    setPreviewPosition(x, y) {{
      calls.push(["previewPosition", x, y]);
    }}
  }},
  pageBackgroundManager: {{
    applyBackdropOnly(color) {{
      calls.push(["backdrop", color]);
    }},
    applyBackgroundFromBlob() {{
      calls.push(["backgroundBlob"]);
    }}
  }},
  cardThemeManager: {{
    applyCardThemeFromPrefs() {{
      calls.push(["cardTheme"]);
    }}
  }},
  normalizeProfileBackgroundBackdropColor(value) {{
    return String(value || "").trim();
  }},
  updateProfileBgOpacityLabel() {{}},
  updateProfileCardThemeLabels() {{}},
  setProfileBgStatus(message) {{
    calls.push(["status", message]);
  }},
  clearFileInput() {{}}
}});

(async () => {{
  await bridge.syncForLoadedPrefs({{
    backgroundAssetId: "asset-1",
    backgroundBackdropColor: "#4455aa",
    backgroundOpacity: 0.2,
    backgroundPositionX: 25,
    backgroundPositionY: 75
  }}, {{
    skipPageImageAsset: true
  }});
  assert.deepEqual(calls, [
    ["previewPosition", 25, 75],
    ["previewPosition", 25, 75],
    ["getAsset", "asset-1"],
    ["previewBlob", true],
    ["previewPosition", 25, 75],
    ["status", "Asset: image/png, 5 B."],
    ["cardTheme"],
    ["backdrop", "#4455aa"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_runtime_bridge_reuses_preview_blob_for_page_background(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const bridgePath = {json.dumps(str(BACKGROUND_RUNTIME_BRIDGE_JS))};
const context = vm.createContext({{ console, Blob }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _subs, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(bridgePath, "utf8"), context, {{ filename: bridgePath }});

const imageBlob = new Blob(["image"], {{ type: "image/png" }});
const calls = [];
const bridge = context.LexiShift.optionsProfileBackgroundRuntimeBridge.createBridge({{
  profileMediaStore: {{
    async getAsset(assetId) {{
      calls.push(["getAsset", assetId]);
      return {{ blob: imageBlob, mime_type: "image/png", byte_size: imageBlob.size }};
    }}
  }},
  previewManager: {{
    clearPreview() {{
      calls.push(["previewClear"]);
    }},
    setPreviewFromBlob(blob) {{
      calls.push(["previewBlob", blob === imageBlob]);
    }},
    setPreviewPosition(x, y) {{
      calls.push(["previewPosition", x, y]);
    }}
  }},
  pageBackgroundManager: {{
    applyBackdropOnly(color) {{
      calls.push(["backdrop", color]);
    }},
    applyBackgroundFromBlob(blob, opacity, backdropColor, x, y) {{
      calls.push(["backgroundBlob", blob === imageBlob, opacity, backdropColor, x, y]);
    }}
  }},
  cardThemeManager: {{
    applyCardThemeFromPrefs() {{
      calls.push(["cardTheme"]);
    }}
  }},
  normalizeProfileBackgroundBackdropColor(value) {{
    return String(value || "").trim();
  }},
  updateProfileBgOpacityLabel() {{}},
  updateProfileCardThemeLabels() {{}},
  setProfileBgStatus(message) {{
    calls.push(["status", message]);
  }},
  clearFileInput() {{}}
}});

(async () => {{
  await bridge.syncForLoadedPrefs({{
    backgroundAssetId: "asset-1",
    backgroundBackdropColor: "#4455aa",
    backgroundOpacity: 0.2,
    backgroundPositionX: 25,
    backgroundPositionY: 75
  }});
  assert.deepEqual(calls, [
    ["previewPosition", 25, 75],
    ["previewPosition", 25, 75],
    ["getAsset", "asset-1"],
    ["previewBlob", true],
    ["previewPosition", 25, 75],
    ["status", "Asset: image/png, 5 B."],
    ["cardTheme"],
    ["backgroundBlob", true, 0.2, "#4455aa", 25, 75]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_runtime_bridge_can_skip_image_asset_for_fast_options_first_paint(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const bridgePath = {json.dumps(str(BACKGROUND_RUNTIME_BRIDGE_JS))};
const context = vm.createContext({{ console, Blob }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _subs, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(bridgePath, "utf8"), context, {{ filename: bridgePath }});

const calls = [];
const bridge = context.LexiShift.optionsProfileBackgroundRuntimeBridge.createBridge({{
  profileMediaStore: {{
    async getAsset(assetId) {{
      calls.push(["getAsset", assetId]);
      return {{ blob: new Blob(["image"], {{ type: "image/png" }}) }};
    }}
  }},
  previewManager: {{
    clearPreview() {{
      calls.push(["previewClear"]);
    }},
    setPreviewFromBlob() {{
      calls.push(["previewBlob"]);
    }},
    setPreviewPosition(x, y) {{
      calls.push(["previewPosition", x, y]);
    }}
  }},
  pageBackgroundManager: {{
    applyBackdropOnly(color) {{
      calls.push(["backdrop", color]);
    }},
    applyBackgroundFromBlob() {{
      calls.push(["backgroundBlob"]);
    }}
  }},
  cardThemeManager: {{
    applyCardThemeFromPrefs(prefs) {{
      calls.push(["cardTheme", prefs.cardThemeHueDeg]);
    }}
  }},
  normalizeProfileBackgroundBackdropColor(value) {{
    return String(value || "").trim();
  }},
  updateProfileBgOpacityLabel(value) {{
    calls.push(["opacityLabel", value]);
  }},
  updateProfileCardThemeLabels(values) {{
    calls.push(["cardLabels", values.hueDeg]);
  }},
  clearFileInput() {{
    calls.push(["clearFile"]);
  }}
}});

(async () => {{
  await bridge.syncForLoadedPrefs({{
    backgroundAssetId: "asset-1",
    backgroundBackdropColor: "#4455aa",
    backgroundOpacity: 0.2,
    backgroundPositionX: 25,
    backgroundPositionY: 75,
    cardThemeHueDeg: 42
  }}, {{
    eagerBackdrop: true,
    skipImageAsset: true,
    skipPreviewAsset: true
  }});
  assert.deepEqual(calls, [
    ["clearFile"],
    ["opacityLabel", 20],
    ["previewPosition", 25, 75],
    ["cardLabels", 42],
    ["previewPosition", 25, 75],
    ["cardTheme", 42],
    ["backdrop", "#4455aa"]
  ]);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_first_image_selection_commits_profile_background_immediately(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const actionsPath = {json.dumps(str(BACKGROUND_ACTIONS_JS))};
const context = vm.createContext({{ console, Blob }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _subs, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(actionsPath, "utf8"), context, {{ filename: actionsPath }});

const statuses = [];
const backgroundStatuses = [];
const previews = [];
const saves = [];
const publishes = [];
const applies = [];
const upserts = [];

const imageFile = new Blob(["fake image"], {{ type: "image/png" }});
imageFile.name = "background.png";

const opacityInput = {{ value: "22" }};
const backdropInput = {{ value: "#123456" }};
const fileInput = {{
  files: [imageFile],
  value: "C:\\\\fakepath\\\\background.png"
}};
const removeButton = {{ disabled: true }};

const actions = context.LexiShift.optionsProfileBackgroundActions.createActions({{
  colors: {{
    SUCCESS: "success",
    ERROR: "error",
    DEFAULT: "default"
  }},
  profileBgBackdropColorInput: backdropInput,
  profileBgOpacityInput: opacityInput,
  profileBgFileInput: fileInput,
  profileBgRemoveButton: removeButton,
  profileMediaStore: {{
    async upsertProfileBackground(profileId, blob, options) {{
      upserts.push({{ profileId, blob, options }});
      return {{
        asset_id: "suisui:profile_background:asset",
        mime_type: blob.type,
        byte_size: blob.size
      }};
    }}
  }},
  setStatus(message, color) {{
    statuses.push([message, color]);
  }},
  setProfileBgStatus(message) {{
    backgroundStatuses.push(message);
  }},
  clampProfileBackgroundOpacity(value) {{
    return Math.min(1, Math.max(0, Number(value)));
  }},
  normalizeProfileBackgroundBackdropColor(value) {{
    return String(value || "").trim();
  }},
  formatBytes(bytes) {{
    return `${{bytes}} B`;
  }},
  previewManager: {{
    setPreviewFromBlob(blob) {{
      previews.push(blob);
    }},
    getPreviewPosition() {{
      return {{ x: 42, y: 61 }};
    }},
    setPreviewPosition(x, y) {{
      return {{ x, y }};
    }}
  }},
  resolveBackgroundPositionFromSource() {{
    return {{ x: 42, y: 61 }};
  }},
  loadActiveProfileUiPrefs: async () => ({{
    profileId: "suisui",
    uiPrefs: {{
      backgroundEnabled: false,
      backgroundAssetId: "",
      backgroundOpacity: 0.18,
      backgroundBackdropColor: "#fbf7f0",
      backgroundPositionX: 50,
      backgroundPositionY: 50
    }}
  }}),
  saveProfileUiPrefsForCurrentProfile: async (prefs, options) => {{
    saves.push({{ prefs, options }});
    return prefs;
  }},
  publishProfileUiPrefsForCurrentProfile: async (prefs, options) => {{
    publishes.push({{ prefs, options }});
  }},
  applyOptionsPageBackgroundFromPrefs: async (prefs, options) => {{
    applies.push({{ prefs, options }});
  }},
}});

(async () => {{
  await actions.onFileChange();
  assert.equal(fileInput.value, "");
  assert.equal(fileInput.disabled, false);
  assert.equal(upserts.length, 1);
  assert.equal(upserts[0].profileId, "suisui");
  assert.equal(upserts[0].blob, imageFile);
  assert.equal(saves.length, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(saves[0].options)), {{
    profileId: "suisui",
    publishRuntime: false
  }});
  assert.equal(saves[0].prefs.backgroundAssetId, "suisui:profile_background:asset");
  assert.equal(saves[0].prefs.backgroundEnabled, true);
  assert.equal(saves[0].prefs.backgroundOpacity, 0.22);
  assert.equal(saves[0].prefs.backgroundBackdropColor, "#123456");
  assert.equal(saves[0].prefs.backgroundPositionX, 42);
  assert.equal(saves[0].prefs.backgroundPositionY, 61);
  assert.equal(publishes.length, 1);
  assert.equal(publishes[0].options.profileId, "suisui");
  assert.equal(applies.length, 1);
  assert.equal(applies[0].options.preferredBlob, imageFile);
  assert.equal(previews.length, 1);
  assert.equal(previews[0], imageFile);
  assert.match(backgroundStatuses.at(-1), /Asset: image\\/png, 10 B/);
  assert.match(statuses.at(-1)[0], /saved/);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_invalid_image_selection_clears_file_and_shows_inline_status(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const actionsPath = {json.dumps(str(BACKGROUND_ACTIONS_JS))};
const context = vm.createContext({{ console, Blob }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _subs, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(actionsPath, "utf8"), context, {{ filename: actionsPath }});

const statuses = [];
const backgroundStatuses = [];
const fileInput = {{
  files: [new Blob(["not image"], {{ type: "text/plain" }})],
  value: "C:\\\\fakepath\\\\notes.txt"
}};

const actions = context.LexiShift.optionsProfileBackgroundActions.createActions({{
  colors: {{
    SUCCESS: "success",
    ERROR: "error",
    DEFAULT: "default"
  }},
  profileBgFileInput: fileInput,
  setStatus(message, color) {{
    statuses.push([message, color]);
  }},
  setProfileBgStatus(message) {{
    backgroundStatuses.push(message);
  }}
}});

actions.onFileChange();
assert.equal(fileInput.value, "");
assert.match(backgroundStatuses.at(-1), /Only image files/);
assert.deepEqual(statuses.at(-1), ["Only image files are supported.", "error"]);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
