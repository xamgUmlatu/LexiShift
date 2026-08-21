from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXT_ROOT = PROJECT_ROOT / "apps/chrome-extension"
PROMPT_JS = EXT_ROOT / "content/ui/manual_source_prompt.js"
MANIFEST_JSON = EXT_ROOT / "manifest.json"
LOCALE_ROOT = EXT_ROOT / "_locales"


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
            "Node manual-source prompt contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionManualSourcePromptContract(unittest.TestCase):
    def test_prompt_registry_matches_approved_source_pages_without_downloads_permission(
        self,
    ) -> None:
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        scripts = manifest["content_scripts"][0]["js"]

        self.assertIn("content/ui/manual_source_prompt.js", scripts)
        self.assertLess(
            scripts.index("content/ui/manual_source_prompt.js"),
            scripts.index("content_script.js"),
        )
        self.assertNotIn("downloads", manifest.get("permissions", []))
        self.assertNotIn("mediafire.com", PROMPT_JS.read_text(encoding="utf-8").lower())

        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PROMPT_JS))};
const context = vm.createContext({{ console, URL }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const prompt = context.LexiShift.manualSourcePrompt;
assert.ok(prompt);
const dictionaryEntry = prompt.findEntryForUrl(
  "https://github.com/MarvNC/yomitan-dictionaries#daijirin-fourth-edition"
);
assert.equal(dictionaryEntry.packId, "lookup-dictionary-directory");
assert.equal(dictionaryEntry.mode, "dictionary-directory");
assert.equal(dictionaryEntry.downloadUrl, undefined);
const entry = prompt.findEntryForUrl("https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html#freq-list");
assert.equal(entry.packId, "freq-ja-bccwj");
assert.equal(entry.mode, "manual-download");
assert.equal(entry.pair, "en-ja");
assert.equal(entry.expectedFilename, "BCCWJ_frequencylist_suw_ver1_0.zip");
assert.equal(
  entry.licenseUrl,
  "https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html#freq-list"
);
assert.equal(
  entry.downloadUrl,
  "https://repository.ninjal.ac.jp/record/3234/files/BCCWJ_frequencylist_suw_ver1_0.zip"
);
assert.equal(prompt.findEntryForUrl("https://en.wikipedia.org/wiki/BCCWJ"), null);
"""
        _run_node(script)

    def test_prompt_i18n_keys_exist_in_all_locale_catalogs(self) -> None:
        required_keys = {
            "dictionary_source_prompt_title",
            "dictionary_source_prompt_body",
            "dictionary_source_prompt_after_download",
            "manual_source_prompt_title",
            "manual_source_prompt_body",
            "manual_source_prompt_file",
            "manual_source_prompt_terms",
            "manual_source_prompt_download",
            "manual_source_prompt_after_download",
            "manual_source_prompt_download_opened",
            "manual_source_prompt_dismiss",
        }
        missing_by_locale: dict[str, list[str]] = {}
        for path in sorted(LOCALE_ROOT.glob("*/messages.json")):
            messages = json.loads(path.read_text(encoding="utf-8"))
            missing = sorted(required_keys.difference(messages))
            if missing:
                missing_by_locale[path.parent.name] = missing

        self.assertEqual(missing_by_locale, {})


if __name__ == "__main__":
    unittest.main()
