from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FORMATTERS_JS = PROJECT_ROOT / "apps/chrome-extension/options/controllers/srs/actions/formatters.js"
REFRESH_RESULT_FORMATTER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/refresh_result_formatter.js"
)
ADMISSION_PREVIEW_FORMATTER_JS = (
    PROJECT_ROOT
    / "apps/chrome-extension/options/controllers/srs/actions/admission_preview_formatter.js"
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
            f"Node formatter test failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


class TestExtensionSrsActionFormatters(unittest.TestCase):
    def test_refresh_result_output_shows_budget_and_browsing_diagnostics(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const refreshFormatterPath = {json.dumps(str(REFRESH_RESULT_FORMATTER_JS))};
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
vm.runInContext(fs.readFileSync(refreshFormatterPath, "utf8"), context, {{ filename: refreshFormatterPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const output = context.LexiShift.optionsSrsActionFormatters.buildRefreshResultOutput({{
  translate: null,
  applied: true,
  added: 2,
  srsPair: "en-es",
  result: {{
    total_items_for_pair: 22,
    max_active_items: 40,
    max_new_items_per_day: 8,
    browsing_admission_preview: {{
      status: "ok",
      matching_signal_count: 2,
      aggregate_item_count: 5,
      neutral_selected_lemmas: ["perro", "gato"],
      simulations: {{
        balanced: {{ selected_lemmas: ["perro", "ave"] }},
        strong: {{ selected_lemmas: ["perro", "hipoteca"] }}
      }}
    }}
  }},
  admission: {{
    active_count: 20,
    active_zero_exposure_zero_feedback: 2,
    active_stale_zero_exposure_zero_feedback: 1,
    stale_active_age_days: 7,
    due_count: 3,
    due_pressure: 0.075,
    capacity_budget: 20,
    base_admission_budget: 8,
    admission_budget: 2,
    reason_code: "normal",
    selected_preferred_topic: {{
      selected_count: 2,
      preferred_count: 1,
      share: 0.5,
      lemmas: ["perro"]
    }},
    selected_lemmas: ["perro", "gato"],
    feedback_window: {{
      feedback_count: 12,
      retention_ratio: 0.83
    }}
  }},
  publishedRulegen: {{
    published: true,
    targets: 22,
    rules: 31,
    ruleset_path: "/tmp/rules.json"
  }}
}});

assert.equal(output.includes("- active_count: 20"), true);
assert.equal(output.includes("- active_unseen_no_feedback: 2"), true);
assert.equal(output.includes("- active_stale_unseen_no_feedback: 1 >7d"), true);
assert.equal(output.includes("- due_count: 3"), true);
assert.equal(output.includes("- capacity_budget: 20"), true);
assert.equal(output.includes("- admission_budget: 2"), true);
assert.equal(output.includes("- selected_preferred_topic_share: 0.5 (1/2)"), true);
assert.equal(output.includes("- selected_lemmas: perro, gato"), true);
assert.equal(output.includes("- browsing_preview_status: ok"), true);
assert.equal(output.includes("- browsing_signal_matches: 2 / 5"), true);
assert.equal(output.includes("- browsing_balanced_selected: perro, ave"), true);
assert.equal(output.includes("- browsing_strong_selected: perro, hipoteca"), true);
"""
        _run_node(script)

    def test_admission_preview_output_shows_profile_topic_overlay(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(ADMISSION_PREVIEW_FORMATTER_JS))};
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

const formatter = context.LexiShift.optionsSrsAdmissionPreviewFormatter;
const text = formatter.buildAdmissionPreviewOutput({{
  srsPair: "en-es",
  profileId: "default",
  plan: {{
    can_execute: true,
    strategy_requested: "profile_bootstrap",
    strategy_effective: "profile_bootstrap",
    execution_mode: "profile_bootstrap"
  }},
  preview: {{
    sample_count_requested: 1,
    sample_count_effective: 1,
    selected_unique_count: 3,
    admitted_count: 1,
    sampling_mode: "ranked",
    profile_bootstrap: {{
      profile_context: {{
        active_signals: ["interests"],
        raw_profile_keys: ["interests"],
        interests: ["animals"],
        explicit_topic_weights: {{ animals: 1 }},
        topic_weights: {{ animals: 1 }},
        signal_sources: {{ animals: "interests" }}
      }},
      profile_topic_overlay: {{
        status: "active",
        application_status: "applied",
        runtime_scope: "admission_preview_only",
        active_topics: ["animals"],
        applied_seed_count: 1,
        applied_row_count: 1,
        source_path: "/tmp/topic-overlays/animals-plants.json"
      }}
    }},
    admitted_words: [
      {{
        lemma: "beta",
        pos_bucket: "noun",
        profile_score: 0.689,
        rank_delta: 1,
        signals: {{ topic_affinity_source: "topic_hint:animals" }},
        explanation: "Boosted by topic_affinity."
      }}
    ]
  }}
}});

assert.match(text, /Topic overlay:/);
assert.match(text, /Sampled words:\\n- beta \\[noun, topic=animals, score=0\\.689, delta=\\+1\\]/);
assert.ok(text.indexOf("Sampled words:") < text.indexOf("Sample details:"));
assert.ok(text.indexOf("Sampled words:") < text.indexOf("Topic overlay:"));
assert.match(text, /status: active/);
assert.match(text, /application_status: applied/);
assert.match(text, /scope: admission_preview_only/);
assert.match(text, /active_topics: animals/);
assert.match(text, /applied_seed_count: 1/);
assert.match(text, /applied_row_count: 1/);
assert.match(text, /source_path: \\/tmp\\/topic-overlays\\/animals-plants\\.json/);
"""
        _run_node(script)

    def test_preflight_and_runtime_diagnostics_show_frequency_pack_identity(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const refreshFormatterPath = {json.dumps(str(REFRESH_RESULT_FORMATTER_JS))};
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
vm.runInContext(fs.readFileSync(refreshFormatterPath, "utf8"), context, {{ filename: refreshFormatterPath }});
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

const refreshFormatterPath = {json.dumps(str(REFRESH_RESULT_FORMATTER_JS))};
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
vm.runInContext(fs.readFileSync(refreshFormatterPath, "utf8"), context, {{ filename: refreshFormatterPath }});
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
