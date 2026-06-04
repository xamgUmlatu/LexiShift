from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAGE_BACKGROUND_MANAGER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/profile/background/page_background_manager.js"
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
            "Node profile-background page-manager test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionProfileBackgroundPageManager(unittest.TestCase):
    def test_background_manager_skips_duplicate_backdrop_and_image_writes(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PAGE_BACKGROUND_MANAGER_JS))};
const context = vm.createContext({{ console, Blob, URL }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const removals = [];
const style = {{
  removeProperty(name) {{
    removals.push(name);
    delete this[name];
  }}
}};
let urlCounter = 0;
const createdUrls = [];
const revokedUrls = [];
const manager = context.LexiShift.optionsProfileBackgroundPageBackgroundManager.createManager({{
  documentRef: {{
    body: {{ style }}
  }},
  normalizeBackdropColor: (value) => String(value || "").trim(),
  clampOpacity: (value) => Number(value),
  hexColorToRgb: () => ({{ r: 17, g: 34, b: 51 }}),
  urlApi: {{
    createObjectURL(blob) {{
      urlCounter += 1;
      const url = `blob:test-${{urlCounter}}`;
      createdUrls.push([url, blob.size]);
      return url;
    }},
    revokeObjectURL(url) {{
      revokedUrls.push(url);
    }}
  }}
}});

manager.applyBackdropOnly("#112233");
manager.applyBackdropOnly("#112233");
assert.equal(style.backgroundColor, "#112233");
assert.equal(style.backgroundImage, "none");
assert.equal(removals.length, 4);

const blob = new Blob(["image"]);
manager.applyBackgroundFromBlob(blob, 0.25, "#112233", 50, 60);
manager.applyBackgroundFromBlob(blob, 0.25, "#112233", 50, 60);
assert.equal(createdUrls.length, 1);
assert.equal(revokedUrls.length, 0);
assert.match(style.backgroundImage, /blob:test-1/);

manager.setBackgroundPosition(50, 60);
assert.equal(style.backgroundPosition, "50% 60%");
manager.setBackgroundPosition(70, 80);
assert.equal(style.backgroundPosition, "70% 80%");
assert.equal(createdUrls.length, 1);
assert.equal(revokedUrls.length, 0);

manager.applyBackdropOnly("#445566");
assert.equal(style.backgroundColor, "#445566");
assert.equal(style.backgroundImage, "none");
assert.deepEqual(revokedUrls, ["blob:test-1"]);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
