from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORD_INFO_API_JS = PROJECT_ROOT / "apps/chrome-extension/shared/helper/word_info_api.js"


@unittest.skipUnless(shutil.which("node"), "node is required")
class TestExtensionWordInfoApiContract(unittest.TestCase):
    def test_cache_keeps_same_surface_readings_separate(self) -> None:
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
    async lookupWordInfo(payload) {{
      calls.push(payload);
      return {{ ok: true, data: {{ reading: payload.word_package.reading }} }};
    }}
  }}
}});

(async () => {{
  const tokiRequest = {{
    languagePair: "en-ja",
    profileId: "alpha",
    replacement: "時",
    displayReplacement: "時",
    wordPackage: {{ surface: "時", reading: "とき" }}
  }};
  const jiRequest = {{
    ...tokiRequest,
    wordPackage: {{ surface: "時", reading: "じ" }}
  }};
  const toki = await api.lookup(tokiRequest);
  const ji = await api.lookup(jiRequest);
  const cachedToki = await api.lookup(tokiRequest);
  assert.equal(toki.reading, "とき");
  assert.equal(ji.reading, "じ");
  assert.deepEqual(cachedToki, toki);
  assert.equal(calls.length, 2);
  assert.equal(calls[0].word_package.reading, "とき");
  assert.equal(calls[1].word_package.reading, "じ");
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
        subprocess.run(
            ["node", "-e", script],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
