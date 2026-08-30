from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXT_ROOT = PROJECT_ROOT / "apps/chrome-extension"
GUIDANCE_JS = EXT_ROOT / "content/ui/manual_source_dictionary_guidance.js"
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
        self.assertIn("content/ui/manual_source_dictionary_guidance.js", scripts)
        self.assertLess(
            scripts.index("content/ui/manual_source_dictionary_guidance.js"),
            scripts.index("content/ui/manual_source_prompt.js"),
        )
        self.assertLess(
            scripts.index("content/ui/manual_source_prompt.js"),
            scripts.index("content_script.js"),
        )
        self.assertNotIn("downloads", manifest.get("permissions", []))
        source_text = "\n".join(
            path.read_text(encoding="utf-8") for path in (GUIDANCE_JS, PROMPT_JS)
        ).lower()
        self.assertNotIn("mediafire.com", source_text)

        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(PROMPT_JS))};
const guidancePath = {json.dumps(str(GUIDANCE_JS))};
const context = vm.createContext({{ console, URL }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(guidancePath, "utf8"), context, {{ filename: guidancePath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const prompt = context.LexiShift.manualSourcePrompt;
assert.ok(prompt);
const japaneseDictionaryEntry = prompt.findEntryForUrl(
  "https://github.com/MarvNC/yomitan-dictionaries"
  + "#daijirin-fourth-edition"
);
assert.equal(japaneseDictionaryEntry.packId, "lookup-dictionary-directory-ja");
assert.equal(japaneseDictionaryEntry.mode, "dictionary-directory");
assert.equal(japaneseDictionaryEntry.recommendedSectionId, "daijirin-fourth-edition");
assert.equal(japaneseDictionaryEntry.downloadUrl, undefined);
const dictionaryEntry = prompt.findEntryForUrl(
  "https://github.com/MarvNC/yomitan-dictionaries"
);
assert.equal(dictionaryEntry.packId, "lookup-dictionary-directory");
assert.equal(dictionaryEntry.mode, "dictionary-directory");
assert.equal(dictionaryEntry.recommendedName, undefined);
assert.equal(dictionaryEntry.downloadUrl, undefined);
const legacyTextFragmentEntry = prompt.findEntryForUrl(
  "https://github.com/MarvNC/yomitan-dictionaries#:~:text=Daijirin"
);
assert.equal(legacyTextFragmentEntry.packId, "lookup-dictionary-directory");

let scrollOptions = null;
let restoreHighlight = null;
const heading = {{
  matches: (selector) => selector.includes("h4"),
  scrollIntoView: (options) => {{ scrollOptions = options; }},
  style: {{}}
}};
context.document = {{
  getElementById: (id) => id === "daijirin-fourth-edition" ? heading : null,
  querySelector: () => null,
  querySelectorAll: () => []
}};
context.setTimeout = (callback, delay) => {{
  assert.equal(delay, 4000);
  restoreHighlight = callback;
  return 1;
}};
assert.equal(prompt.focusRecommendedEntry(japaneseDictionaryEntry), true);
assert.equal(scrollOptions.behavior, "smooth");
assert.equal(scrollOptions.block, "center");
assert.match(heading.style.outline, /solid/);
assert.equal(typeof restoreHighlight, "function");
restoreHighlight();
assert.equal(heading.style.outline, undefined);
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
            "dictionary_source_prompt_recommended",
            "dictionary_source_prompt_format",
            "dictionary_source_prompt_show_entry",
            "dictionary_source_prompt_entry_found",
            "dictionary_source_prompt_entry_missing",
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
