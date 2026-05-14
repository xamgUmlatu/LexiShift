from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORMATTERS_JS = PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/formatters.js"


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
            f"Node formatter test failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


class TestExtensionSrsActionFormatters(unittest.TestCase):
    def test_preflight_and_runtime_diagnostics_show_frequency_pack_identity(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(FORMATTERS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const formatters = context.LexiShift.optionsSrsActionFormatters;
const helperData = {{
  requirements: {{
    supports_rulegen: true,
    requires_jmdict_for_seed: false,
    requires_jmdict_for_rulegen: false,
    requires_translation_dictionary_for_rulegen: true
  }},
  pair_policy: {{
    bootstrap_top_n_default: 800,
    refresh_top_n_default: 400,
    feedback_window_size_default: 50,
    initial_active_count_default: 40
  }},
  set_source_db: "/packs/freq-en-coca/main.sqlite",
  set_source_db_exists: true,
  frequency_pack_path: "/packs/freq-en-coca/main.sqlite",
  frequency_pack_exists: true,
  frequency_pack_id: "freq-en-coca",
  frequency_pack_provider: "wordfrequency",
  frequency_pos_source_profile: "compact-latin",
  jmdict_path: null,
  jmdict_exists: false,
  translation_dict_path: "/packs/wiktionary-es-en/main.sqlite",
  translation_dict_exists: true,
  translation_dict_provider: "wiktionary",
  stopwords_path: "/packs/stopwords-es.json",
  stopwords_exists: true,
  missing_inputs: []
}};

const preflightText = formatters.buildPreflightBlockedLines({{
  actionLabel: "Initialize SRS",
  pair: "en-es",
  profileId: "default",
  helperData
}}).join("\\n");

assert.match(preflightText, /frequency_pack_id: freq-en-coca/);
assert.match(preflightText, /frequency_pack_provider: wordfrequency/);
assert.match(preflightText, /frequency_pos_source_profile: compact-latin/);
assert.match(preflightText, /frequency_pack_path: .*main\\.sqlite \\(exists=true\\)/);
assert.match(
  preflightText,
  /set_source_db \\(execution field\\): .*main\\.sqlite \\(exists=true; same as frequency_pack_path\\)/
);

const diagnosticsText = formatters.buildRuntimeDiagnosticsOutput({{
  srsPair: "en-es",
  selectedProfileId: "default",
  diagnostics: {{
    helper: {{
      ...helperData,
      store_items_for_pair: 12,
      ruleset_rules_count: 34,
      semantic_runtime_capability: "active",
      semantic_runtime_reason_code: "ready_rules_available",
      ruleset_rules_with_semantic_admission: 9,
      ruleset_rules_semantic_ready: 4,
      ruleset_rules_semantic_unavailable: 5,
      snapshot_target_count: 7,
      store_path: "/tmp/store.json",
      ruleset_path: "/tmp/rules.json"
    }},
    cache: {{
      ruleset_rules_count: 3,
      snapshot_target_count: 2,
      snapshot_generation_id: "en-es:default:abc123",
      semantic_inventory_schema_version: 1,
      semantic_inventory_generation_id: "en-es:default:abc123",
      snapshot_semantic_generation_aligned: true
    }},
    runtime_state: {{
      ts: "2026-04-19T05:00:00Z",
      pair: "en-es",
      profile_id: "default",
      srs_enabled: true,
      rules_source: "helper",
      rules_local_enabled: 0,
      rules_srs_enabled: 18,
      active_rules_total: 18,
      active_rules_srs: 18,
      semantic_admission_enabled: true,
      semantic_runtime_capability: "active",
      semantic_runtime_reason_code: "ready_rules_available",
      semantic_pointer_rule_count: 9,
      semantic_ready_rule_count: 4,
      semantic_fallback_policy: "abstain_on_unavailable",
      semantic_inventory_loaded: true,
      semantic_inventory_source: "helper",
      semantic_matches_eligible: 6,
      semantic_matches_ready: 4,
      semantic_policy_replaces: 2,
      semantic_policy_abstains: 1,
      semantic_policy_soft_affordances: 1,
      semantic_fallback_replaces: 0,
      semantic_fallback_abstains: 1,
      semantic_fallback_soft_affordances: 1,
      semantic_fallback_reason_counts: {{
        decision_service_error: 1,
        semantic_status_pending: 1
      }},
      semantic_decision_policy_id: "en_es_sentence_veto_v3",
      semantic_inventory_error: "",
      helper_rules_error: "",
      frame_type: "top"
    }}
  }}
}});

assert.match(diagnosticsText, /frequency_pack_id: freq-en-coca/);
assert.match(diagnosticsText, /frequency_pack_provider: wordfrequency/);
assert.match(diagnosticsText, /frequency_pos_source_profile: compact-latin/);
assert.match(
  diagnosticsText,
  /set_source_db \\(execution field\\): .*main\\.sqlite \\(exists=true; same as frequency_pack_path\\)/
);
assert.match(diagnosticsText, /semantic_runtime_capability: active/);
assert.match(diagnosticsText, /semantic_runtime_reason_code: ready_rules_available/);
assert.match(diagnosticsText, /ruleset_rules_with_semantic_admission: 9/);
assert.match(diagnosticsText, /ruleset_rules_semantic_ready: 4/);
assert.match(diagnosticsText, /ruleset_rules_semantic_unavailable: 5/);
assert.match(diagnosticsText, /cached_snapshot_generation_id: en-es:default:abc123/);
assert.match(diagnosticsText, /cached_semantic_inventory_schema_version: 1/);
assert.match(diagnosticsText, /cached_semantic_inventory_generation_id: en-es:default:abc123/);
assert.match(diagnosticsText, /cached_snapshot_semantic_generation_aligned: true/);
assert.match(diagnosticsText, /semantic_pointer_rule_count: 9/);
assert.match(diagnosticsText, /semantic_ready_rule_count: 4/);
assert.match(diagnosticsText, /semantic_matches_ready: 4/);
assert.match(diagnosticsText, /semantic_policy_soft_affordances: 1/);
assert.match(diagnosticsText, /semantic_fallback_soft_affordances: 1/);
assert.match(
  diagnosticsText,
  /semantic_fallback_reason_counts: \\{{"decision_service_error":1,"semantic_status_pending":1\\}}/
);
assert.match(diagnosticsText, /semantic_decision_policy_id: en_es_sentence_veto_v3/);
"""
        _run_node(script)

    def test_sampled_rulegen_empty_output_shows_frequency_pack_identity(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(FORMATTERS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{
  optionsTranslateResolver: {{
    resolveTranslate(translate) {{
      return typeof translate === "function"
        ? translate
        : ((_key, _args, fallback) => fallback);
    }}
  }}
}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const formatters = context.LexiShift.optionsSrsActionFormatters;
const text = formatters.buildSampledRulegenEmptyOutput({{
  header: "Sampled rulegen",
  samplingLines: ["- sample_count_effective: 5"],
  srsPair: "en-es",
  diagnostics: {{
    pair: "en-es",
    jmdict_path: null,
    jmdict_exists: false,
    translation_dict_path: "/packs/wiktionary-es-en/main.sqlite",
    translation_dict_exists: true,
    translation_dict_provider: "wiktionary",
    set_source_db: "/packs/freq-en-coca/main.sqlite",
    set_source_db_exists: true,
    frequency_pack_path: "/packs/freq-en-coca/main.sqlite",
    frequency_pack_exists: true,
    frequency_pack_id: "freq-en-coca",
    frequency_pack_provider: "wordfrequency",
    frequency_pos_source_profile: "compact-latin",
    store_items: 0,
    store_items_for_pair: 0,
    store_sample: []
  }}
}});

assert.match(text, /frequency_pack_id: freq-en-coca/);
assert.match(text, /frequency_pack_provider: wordfrequency/);
assert.match(text, /frequency_pos_source_profile: compact-latin/);
assert.match(text, /frequency_pack_path: .*main\\.sqlite \\(exists=true\\)/);
assert.match(
  text,
  /set_source_db \\(execution field\\): .*main\\.sqlite \\(exists=true; same as frequency_pack_path\\)/
);
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()
