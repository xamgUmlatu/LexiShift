from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROFILE_SELECTOR_JS = (
    PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/profile_selector_controller.js"
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
            "Node profile-selector contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionProfileSelectorContract(unittest.TestCase):
    def test_sync_selected_can_skip_helper_profiles_for_fast_local_first_paint(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PROFILE_SELECTOR_JS))};
const context = vm.createContext({{
  console,
  document: {{
    createElement() {{
      return {{ value: "", textContent: "" }};
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createController = context.LexiShift.optionsSrsProfileSelector.createController;
const profileSelect = {{
  _options: [],
  _value: "",
  disabled: false,
  set innerHTML(_value) {{
    this._options = [];
    this._value = "";
  }},
  appendChild(option) {{
    this._options.push({{ value: option.value, textContent: option.textContent }});
    if (!this._value) {{
      this._value = option.value;
    }}
  }},
  set value(value) {{
    this._value = value;
  }},
  get value() {{
    return this._value;
  }}
}};

let helperCalls = 0;
const itemsState = {{
  srsSelectedProfileId: "suisui",
  srsProfileId: "suisui",
  optionsSelectedProfileId: "suisui"
}};

const controller = createController({{
  settingsManager: {{
    DEFAULT_PROFILE_ID: "default",
    getSelectedSrsProfileId(items) {{
      return String(items.srsSelectedProfileId || items.srsProfileId || "default");
    }},
    getSelectedUiProfileId(items) {{
      return String(items.optionsSelectedProfileId || items.srsSelectedProfileId || "default");
    }},
    async updateSelectedSrsProfileId() {{
      throw new Error("should not update SRS profile during local-only sync");
    }},
    async updateSelectedUiProfileId() {{
      throw new Error("should not update UI profile during local-only sync");
    }},
    async load() {{
      return {{ ...itemsState }};
    }}
  }},
  helperManager: {{
    async getProfiles() {{
      helperCalls += 1;
      throw new Error("helper profile fetch should be skipped");
    }}
  }},
  profileSelect,
  setProfileStatusMessage() {{}}
}});

(async () => {{
  const result = await controller.syncSelected({{ ...itemsState }}, {{ skipHelperProfiles: true }});
  assert.equal(helperCalls, 0);
  assert.equal(result.profileId, "suisui");
  assert.equal(result.uiProfileId, "suisui");
  assert.equal(result.helperProfilesPayload, null);
  assert.deepEqual(profileSelect._options, [
    {{ value: "suisui", textContent: "suisui" }},
    {{ value: "default", textContent: "default" }}
  ]);
  assert.equal(profileSelect.value, "suisui");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)

    def test_sync_selected_uses_real_helper_profiles_without_fabricating_default(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PROFILE_SELECTOR_JS))};
const context = vm.createContext({{
  console,
  document: {{
    createElement() {{
      return {{ value: "", textContent: "" }};
    }}
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const createController = context.LexiShift.optionsSrsProfileSelector.createController;
const profileSelect = {{
  _options: [],
  _value: "",
  disabled: false,
  set innerHTML(_value) {{
    this._options = [];
    this._value = "";
  }},
  appendChild(option) {{
    this._options.push({{ value: option.value, textContent: option.textContent }});
    if (!this._value) {{
      this._value = option.value;
    }}
  }},
  set value(value) {{
    this._value = value;
  }},
  get value() {{
    return this._value;
  }}
}};

const captured = {{
  updates: [],
  profileSyncCalls: [],
  statusMessages: [],
  localizedCalls: []
}};

let itemsState = {{
  srsSelectedProfileId: "default",
  srsProfileId: "default",
  optionsSelectedProfileId: "default"
}};

const controller = createController({{
  settingsManager: {{
    DEFAULT_PROFILE_ID: "default",
    getSelectedSrsProfileId(items) {{
      return String(items.srsSelectedProfileId || items.srsProfileId || "default");
    }},
    getSelectedUiProfileId(items) {{
      return String(items.optionsSelectedProfileId || items.srsSelectedProfileId || "default");
    }},
    async updateSelectedSrsProfileId(profileId) {{
      captured.updates.push(["srs", profileId]);
      itemsState = {{
        ...itemsState,
        srsSelectedProfileId: profileId,
        srsProfileId: profileId
      }};
    }},
    async updateSelectedUiProfileId(profileId) {{
      captured.updates.push(["ui", profileId]);
      itemsState = {{
        ...itemsState,
        optionsSelectedProfileId: profileId
      }};
    }},
    async load() {{
      return {{ ...itemsState }};
    }}
  }},
  helperManager: {{
    async getProfiles() {{
      return {{
        ok: true,
        data: {{
          profiles: [
            {{ profile_id: "suisui", name: "suisui" }},
            {{ profile_id: "travel", name: "Travel" }}
          ]
        }}
      }};
    }}
  }},
  profileSelect,
  setProfileStatusMessage(message) {{
    captured.statusMessages.push(String(message));
  }},
  setProfileStatusLocalized(key, substitutions, fallback) {{
    captured.localizedCalls.push([key, substitutions, fallback]);
  }},
  async onProfileLanguagePrefsSync(payload) {{
    captured.profileSyncCalls.push(payload.profileId);
  }}
}});

(async () => {{
  const result = await controller.syncSelected({{ ...itemsState }});
  assert.equal(result.profileId, "suisui");
  assert.equal(result.uiProfileId, "suisui");
  assert.deepEqual(captured.updates, [
    ["srs", "suisui"],
    ["ui", "suisui"]
  ]);
  assert.deepEqual(captured.profileSyncCalls, ["suisui"]);
  assert.deepEqual(profileSelect._options, [
    {{ value: "suisui", textContent: "suisui" }},
    {{ value: "travel", textContent: "Travel (travel)" }}
  ]);
  assert.equal(profileSelect.value, "suisui");
  assert.equal(profileSelect.disabled, false);
  assert.deepEqual(captured.statusMessages, [""]);
  assert.deepEqual(captured.localizedCalls, []);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
