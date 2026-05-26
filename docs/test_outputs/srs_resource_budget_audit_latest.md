# SRS Resource Budget Audit

- Status: `review`
- Decision: `srs_resource_budget_needs_review`
- Generated: `2026-05-26T18:25:10.802044+00:00`
- Pair: `en-es`
- Profile: `default`
- Data root exists: `True`

## Summary

- Code budget rows: `16`
- Bounded code rows: `13`
- Helper artifact rows: `8`
- Helper artifact bytes: `683716`
- Active SRS items: `40`
- Zero-exposure active items: `40`
- Zero-feedback active items: `40`

## Code Budgets

| Surface | Budget | Cap | Current | Status | Notes |
| --- | --- | ---: | ---: | --- | --- |
| `helper_srs_settings` | `max_active_items` | 40 | 40 | `bounded` | Default active S capacity for a pair/profile. |
| `helper_srs_settings` | `max_new_items_per_day` | 8 | 8 | `bounded` | Current code treats this as a per-refresh admission cap. |
| `extension_srs_store` | `max_items` | 8000 | source_constant | `bounded` | Extension-local projection store prune cap. |
| `extension_srs_store` | `max_history_per_item` | 50 | source_constant | `bounded` | Extension-local history clamp per item. |
| `extension_exposure_log` | `max_entries` | 2000 | source_constant | `bounded` | Extension exposure telemetry ring buffer. |
| `extension_browsing_admission_sender` | `max_pending_scopes` | 8 | source_constant | `bounded` | In-memory pending browsing-signal scopes before flush. |
| `extension_browsing_admission_sender` | `max_signals_per_packet` | 50 | source_constant | `bounded` | Extension packet construction cap. |
| `extension_browsing_admission_sender` | `max_count_per_signal` | 5 | source_constant | `bounded` | Extension-side per-packet signal count cap. |
| `helper_browsing_signal_ingest` | `max_signals_per_packet` | 200 | 200 | `bounded` | Helper ingest packet cap. |
| `helper_browsing_signal_ingest` | `max_items_per_store` | 5000 | 5000 | `bounded` | Decayed browsing aggregate store cap per pair/profile. |
| `helper_signal_queue` | `max_events` | 5000 | source_default | `bounded` | Signal queue save/append event cap. |
| `runtime_page_budget` | `max_replacements_per_page` | 20 | source_default | `bounded` | Standard replacement density cap. |
| `runtime_page_budget` | `max_replacements_per_lemma_per_page` | 2 | source_default | `bounded` | Standard repeated-lemma density cap. |
| `extension_helper_cache` | `helperRulesetCache` |  | chrome.storage.local | `needs_policy` | Profile/pair helper cache exists but no explicit prune/TTL source constant was found. |
| `extension_helper_cache` | `helperSnapshotCache` |  | chrome.storage.local | `needs_policy` | Profile/pair helper cache exists but no explicit prune/TTL source constant was found. |
| `extension_helper_cache` | `helperSemanticInventoryCache` |  | chrome.storage.local | `needs_policy` | Profile/pair helper cache exists but no explicit prune/TTL source constant was found. |

## Helper Artifacts

| Artifact | Exists | Bytes | Key Counts | Status |
| --- | --- | ---: | --- | --- |
| `srs_store` | `True` | 75340 | pair_items=40, active_inventory_items=40, active_lifecycle_items=40, discarded_items=0, cleared_items=0, zero_exposure_items=40, zero_feedback_items=40 | `ok` |
| `srs_inventory` | `False` | 0 | resolved_active_item_ids=40, inventory_file_active_item_ids=0 | `missing` |
| `srs_ruleset` | `True` | 156802 | rule_count=224, enabled_rule_count=224, lemmas_with_rules=175 | `ok` |
| `srs_rulegen_snapshot` | `True` | 15720 | stats_count=3, targets_count=175 | `ok` |
| `srs_semantic_inventory` | `True` | 434937 | capability_count=6, competition_sets_count=224, phrase_sets_count=0, senses_count=266, triggers_count=224 | `ok` |
| `srs_signal_queue` | `True` | 917 | events=4, pair_events=0, feedback_events=0, exposure_events=0 | `ok` |
| `srs_browsing_signal_store` | `False` | 0 |  | `missing` |
| `srs_admission_suppression` | `False` | 0 |  | `missing` |

## Encounter-Starvation Preview

| Lemma | Exposures | Reviews | Rule Count | Source Phrases |
| --- | ---: | ---: | ---: | ---: |
| `crear` | 0 | 0 | 0 | 0 |
| `el` | 0 | 0 | 0 | 0 |
| `ese` | 0 | 0 | 0 | 0 |
| `hasta` | 0 | 0 | 0 | 0 |
| `junto` | 0 | 0 | 0 | 0 |
| `mayor` | 0 | 0 | 0 | 0 |
| `movimiento` | 0 | 0 | 0 | 0 |
| `no` | 0 | 0 | 0 | 0 |
| `ocurrir` | 0 | 0 | 0 | 0 |
| `presentar` | 0 | 0 | 0 | 0 |
| `pues` | 0 | 0 | 0 | 0 |
| `sacar` | 0 | 0 | 0 | 0 |
| `según` | 0 | 0 | 0 | 0 |
| `dentro` | 0 | 0 | 1 | 1 |
| `fondo` | 0 | 0 | 1 | 1 |
| `hermano` | 0 | 0 | 1 | 1 |
| `leer` | 0 | 0 | 1 | 1 |
| `llamar` | 0 | 0 | 1 | 1 |
| `luz` | 0 | 0 | 1 | 1 |
| `mayoría` | 0 | 0 | 1 | 1 |
| `mil` | 0 | 0 | 1 | 1 |
| `millón` | 0 | 0 | 1 | 1 |
| `más` | 0 | 0 | 1 | 1 |
| `música` | 0 | 0 | 1 | 1 |
| `nacional` | 0 | 0 | 1 | 1 |

## Findings

- `REVIEW` `cache_budget_policy_missing`: One or more cache/storage surfaces do not expose an explicit source-level cap or TTL.
- `REVIEW` `encounter_starvation_candidates`: 40 active item(s) have zero exposure and zero feedback in the audited store.

## Limitations

- The audit reads helper artifacts from disk but does not inspect live chrome.storage.local values.
- Chrome storage usage is represented by source constants until a browser-profile export path is added.
- File-size thresholds are advisory MVP review thresholds, not Chrome or OS hard limits.
- Encounter-starvation diagnostics are based on stored exposure/review counters; they cannot prove future page encounter frequency.
