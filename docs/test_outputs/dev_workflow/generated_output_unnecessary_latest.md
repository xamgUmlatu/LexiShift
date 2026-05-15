# Generated Output Unnecessary File Audit

Status: generated evidence
Role: Generated evidence
Last updated: 2026-05-15
Purpose: identify generated-output groups that are mechanically safe to prune.

This audit is intentionally conservative. `definite_prune` means the rule found no exact non-output references and no retained generated-output provenance references.

## Summary

| Metric | Count |
| --- | ---: |
| `group_count` | 1 |
| `definite_prune_group_count` | 0 |
| `definite_prune_file_count` | 0 |
| `definite_prune_bytes` | 0 |
| `review_only_group_count` | 0 |
| `retain_group_count` | 1 |

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

## Rules

| Rule | Posture | Description |
| --- | --- | --- |
| `unreferenced_root_dated_report_view_with_json_counterpart` | definite_prune | A root-level dated `.html` or `.md` generated report view has no references and a same-stem JSON evidence file remains. |
| `unreferenced_semantic_repair_report_bundle` | definite_prune | A dated semantic-veto LLM pilot repair admission/generation-run report bundle has no references. Generated-row payloads are not included. |
| `unreferenced_semantic_install_root_with_retained_source_evidence` | definite_prune | A copied semantic install-root fixture has no references and matching top-level normalized evidence plus semantic inventory remain. |
| `unreferenced_root_dated_primary_or_provenance_output` | review_only | A dated root generated output has no references, but may be primary JSON evidence or provenance data. |
| `install_root_missing_retained_source_evidence` | review_only | An unreferenced install-root fixture lacks the retained source-evidence counterparts required for automatic pruning. |
| `referenced_generated_output` | retain | The path is still referenced by docs, tests, scripts, or retained outputs. |
