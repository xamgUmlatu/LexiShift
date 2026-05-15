# Generated Output Unnecessary File Audit

Status: generated evidence
Role: Generated evidence
Last updated: 2026-05-15
Purpose: identify generated-output groups that are mechanically safe to prune.

This audit is intentionally conservative. `definite_prune` means the rule found no exact non-output references and no retained generated-output provenance references.

## Summary

| Metric | Count |
| --- | ---: |
| `group_count` | 16 |
| `definite_prune_group_count` | 0 |
| `definite_prune_file_count` | 0 |
| `definite_prune_bytes` | 0 |
| `review_only_group_count` | 0 |
| `retain_group_count` | 16 |

## Definite Prune Groups

| Rule | Files | Bytes | Reason | Sample Paths | Reference Samples |
| --- | ---: | ---: | --- | --- | --- |
| _None detected._ | 0 | 0 |  |  |  |

## Review-Only Groups

| Rule | Files | Bytes | Reason | Sample Paths | Reference Samples |
| --- | ---: | ---: | --- | --- | --- |
| _None detected._ | 0 | 0 |  |  |  |

## Retained Groups

| Rule | Files | Bytes | Reason | Sample Paths | Reference Samples |
| --- | ---: | ---: | --- | --- | --- |
| `referenced_generated_output` | 7 | 2021577 | The install root or one of its files is still referenced. | `docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-011/manifest.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-011/semantic_inventory.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root/srs/profiles/default/srs_publication_manifest_en-es.json`<br>`docs/test_outputs/experiments/semantic_veto_source_packaging/en-es-active-only-combined-full-v1-tranche-011-product-install-data-root/srs/profiles/default/srs_rulegen_snapshot_en-es.json` | `docs/rulegen/semantic_veto_active_only_tranche_runbook.md`<br>`docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_live_page_scan_en_es_latest.json`<br>`docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_live_page_scan_en_es_latest.md`<br>`docs/test_outputs/semantic_veto_active_only_combined_full_v1_tranche_011_pack_install_en_es_latest.json` |
| `referenced_generated_output` | 1 | 190979 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | `docs/language_pairs/lp_state_and_onboarding_research_2026-05-06.md`<br>`docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |
| `referenced_generated_output` | 1 | 1024 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_all_pairs_summary_2026-03-21.md` | `docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |
| `referenced_generated_output` | 1 | 28899 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json` | `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`<br>`docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`<br>`docs/developer/feature_state_matrix.md` |
| `referenced_generated_output` | 1 | 14296 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_triage_all_pairs_2026-03-21.json` | `docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |
| `referenced_generated_output` | 1 | 1843 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_triage_all_pairs_summary_2026-03-21.md` | `docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |
| `referenced_generated_output` | 1 | 2927 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.json` | `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md` |
| `referenced_generated_output` | 1 | 78511 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_probe_en_es_expansion_selected_rev_off_2026-03-13.json` | `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md` |
| `referenced_generated_output` | 1 | 72140 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_probe_en_es_expansion_selected_rev_on_2026-03-13.json` | `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md` |
| `referenced_generated_output` | 1 | 45960 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json` | `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`<br>`docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`<br>`docs/developer/feature_state_matrix.md` |
| `referenced_generated_output` | 1 | 6468 | Dated root generated output is still referenced. | `docs/test_outputs/rulegen_quality_gate_all_pairs_2026-03-21.json` | `docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |
| `referenced_generated_output` | 1 | 3903 | Dated root generated output is still referenced. | `docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_001.json` | `docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_latest.json`<br>`docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.json`<br>`docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.md` |
| `referenced_generated_output` | 1 | 2254 | Dated root generated output is still referenced. | `docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_repair_20260505_003.json` | `docs/test_outputs/semantic_veto_llm_pilot_generated_rows_en_es_latest.json`<br>`docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.json`<br>`docs/test_outputs/semantic_veto_llm_pilot_generated_rows_merge_en_es_latest.md` |
| `referenced_generated_output` | 1 | 719 | Dated root report view has a same-stem JSON file but is still referenced. | `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.md` | `docs/developer/feature_state_matrix.md` |
| `referenced_generated_output` | 1 | 1836 | Dated root report view has a same-stem JSON file but is still referenced. | `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md` | `docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`<br>`docs/developer/feature_state_matrix.md` |
| `referenced_generated_output` | 1 | 2173 | Dated root report view has a same-stem JSON file but is still referenced. | `docs/test_outputs/rulegen_quality_gate_all_pairs_2026-03-21.md` | `docs/rulegen/rulegen_pair_stability_snapshot_2026-03-21.md` |

## Rules

| Rule | Posture | Description |
| --- | --- | --- |
| `unreferenced_root_dated_report_view_with_json_counterpart` | definite_prune | A root-level dated `.html` or `.md` generated report view has no references and a same-stem JSON evidence file remains. |
| `unreferenced_semantic_repair_report_bundle` | definite_prune | A dated semantic-veto LLM pilot repair admission/generation-run report bundle has no references. Generated-row payloads are not included. |
| `unreferenced_semantic_install_root_with_retained_source_evidence` | definite_prune | A copied semantic install-root fixture has no references and matching top-level normalized evidence plus semantic inventory remain. |
| `unreferenced_root_dated_primary_or_provenance_output` | review_only | A dated root generated output has no references, but may be primary JSON evidence or provenance data. |
| `install_root_missing_retained_source_evidence` | review_only | An unreferenced install-root fixture lacks the retained source-evidence counterparts required for automatic pruning. |
| `referenced_generated_output` | retain | The path is still referenced by docs, tests, scripts, or retained outputs. |
