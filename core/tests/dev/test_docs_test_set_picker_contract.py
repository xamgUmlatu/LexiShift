from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PICKER_SCRIPT = ROOT / "docs" / "assets" / "js" / "test-set-picker.js"
PICKER_PAGE = ROOT / "docs" / "test-sets" / "index.md"
RULES_MANAGER_SCRIPT = ROOT / "apps" / "chrome-extension" / "options" / "core" / "rules_manager.js"
RULES_MANAGER_BASE_METHODS = (
    ROOT / "apps" / "chrome-extension" / "options" / "core" / "rules_manager" / "base_methods.js"
)
RULESET_METHODS = (
    ROOT / "apps" / "chrome-extension" / "options" / "core" / "rules_manager" / "ruleset_methods.js"
)


def _load_generated_catalog() -> dict[str, object]:
    node_script = f"""
const picker = require({json.dumps(str(PICKER_SCRIPT))});
const pairs = [];
for (const source of picker.LANGUAGES) {{
  for (const target of picker.LANGUAGES) {{
    const envelope = picker.buildRuleset(source.id, target.id);
    pairs.push({{
      source: source.id,
      target: target.id,
      filename: picker.buildFilename(source.id, target.id),
      envelope
    }});
  }}
}}
process.stdout.write(JSON.stringify({{ languages: picker.LANGUAGES, samples: picker.SAMPLE_TEXTS, pairs }}));
"""
    completed = subprocess.run(
        ["node", "-e", node_script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_picker_generates_importable_rulesets_for_every_exposed_pair() -> None:
    catalog = _load_generated_catalog()
    languages = catalog["languages"]
    samples = catalog["samples"]
    pairs = catalog["pairs"]

    assert [language["id"] for language in languages] == ["en", "es", "ja", "zh", "de"]
    assert len(pairs) == len(languages) ** 2

    for item in pairs:
        source = item["source"]
        target = item["target"]
        envelope = item["envelope"]
        assert item["filename"] == f"lexishift-test-set-{source}-{target}-v1.json"
        assert envelope["lexishift_share"] == {"version": 2, "scope": "ruleset"}

        ruleset = envelope["data"]["ruleset"]
        assert ruleset["metadata"]["languagePair"] == f"{source}-{target}"
        assert ruleset["metadata"]["purpose"] == "public_test_fixture"
        assert ruleset["metadata"]["rulesCount"] == 5
        assert len(ruleset["rules"]) == 5

        source_phrases = set()
        for rule in ruleset["rules"]:
            assert rule["enabled"] is True
            assert rule["case_policy"] == "as-is"
            assert rule["metadata"]["language_pair"] == f"{source}-{target}"
            assert rule["source_phrase"]
            assert rule["replacement"]
            source_phrases.add(rule["source_phrase"].lower())
            if target == "ja":
                package = rule["metadata"]["word_package"]
                assert package["language_tag"] == "ja"
                assert package["surface"] == rule["replacement"]
                assert package["reading"]
                assert package["script_forms"]["kana"]
                assert package["script_forms"]["romaji"]
                assert package["source"]["provider"] == "lexishift-public-test-set"

        sample_text = samples[source]
        assert all(phrase in sample_text.lower() for phrase in source_phrases)


def test_picker_page_keeps_controls_out_of_extension_scanning() -> None:
    page = PICKER_PAGE.read_text(encoding="utf-8")

    assert "permalink: /test-sets/" in page
    assert "data-test-set-source" in page
    assert "data-test-set-target" in page
    assert "data-test-set-download" in page
    assert "data-test-set-copy-json" in page
    assert "data-test-set-copy-sample" in page
    assert 'data-lexishift-scan-skip="true"' in page
    assert "<p data-test-set-sample></p>" in page
    assert '<p data-test-set-sample data-lexishift-scan-skip="true">' not in page
    assert "/assets/js/test-set-picker.js" in page


def test_generated_envelope_decodes_through_the_extension_import_contract() -> None:
    node_script = f"""
const fs = require("fs");
const vm = require("vm");
const picker = require({json.dumps(str(PICKER_SCRIPT))});
const managerSource = fs.readFileSync({json.dumps(str(RULES_MANAGER_SCRIPT))}, "utf8");
vm.runInThisContext(`${{managerSource}}\nglobalThis.RulesManager = RulesManager;`);
vm.runInThisContext(fs.readFileSync({json.dumps(str(RULES_MANAGER_BASE_METHODS))}, "utf8"));
vm.runInThisContext(fs.readFileSync({json.dumps(str(RULESET_METHODS))}, "utf8"));

const manager = new globalThis.RulesManager(null, {{ t: (_key, _substitutions, fallback) => fallback }});
for (const source of picker.LANGUAGES) {{
  for (const target of picker.LANGUAGES) {{
    const envelope = picker.buildRuleset(source.id, target.id);
    const decoded = manager._decodePayload(JSON.stringify(envelope), false);
    const imported = manager._unwrapShareEnvelope(decoded);
    if (imported.scope !== "ruleset") throw new Error("Unexpected scope");
    const normalized = manager._normalizeImportedRulesetPayload(imported.data);
    if (normalized.rules.length !== 5) throw new Error("Unexpected rule count");
  }}
}}
"""
    subprocess.run(["node", "-e", node_script], check=True)
