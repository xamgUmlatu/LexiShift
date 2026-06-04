# en-es Semantic Veto Full-Family Trusted Eval Seed

- Status: `ok`
- Decision: `full_family_trusted_eval_seed_ready_for_scoring`
- Generated: `2026-05-06T22:08:25Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v1.json`
- Trusted families: `7`
- Trusted cases: `27`
- Excluded families: `3`

## Approval Boundary

User approval applies only to repaired pilot rows. Deferred source-target mapping audit rows remain excluded.

This is a trusted seed, not a discovery/locked split. Do not tune thresholds on it and then claim locked-eval performance.

## Summary

| Key | Value |
| --- | --- |
| `trusted_family_count` | `7` |
| `trusted_case_count` | `27` |
| `excluded_family_count` | `3` |
| `manual_review_state` | `approved_by_user` |
| `row_quality_status` | `trusted` |
| `case_type_counts` | `{"phrase_no_winner": 7, "positive_active": 14, "shadow_negative": 6}` |
| `source_band_case_counts` | `{"zipf_3_to_4_mid": 3, "zipf_4_to_5_common": 3, "zipf_5_plus_very_common": 13, "zipf_below_3_rare": 8}` |
| `family_repair_status_counts` | `{"active_sense_corrected": 3, "aligned_mapping_contexts_rewritten": 4}` |

## Checks

| Check | Value |
| --- | --- |
| `has_trusted_families` | `True` |
| `all_rows_approved_by_user` | `True` |
| `all_rows_trusted` | `True` |
| `no_deferred_families_in_trusted_rows` | `True` |
| `has_active_shadow_and_no_winner_cases` | `True` |

## Trusted Families

| Source | Target | Status | Cases | Positive | Shadow | No-Winner |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `break` | `quebrar` | `active_sense_corrected` | 5 | 2 | 2 | 1 |
| `bridle` | `reprimir` | `active_sense_corrected` | 5 | 2 | 2 | 1 |
| `december` | `diciembre` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `emotion` | `emoción` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `dentist` | `dentista` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `bouillon` | `caldo` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `control` | `gobernar` | `active_sense_corrected` | 5 | 2 | 2 | 1 |

## Excluded Families

| Source | Target | Reason | Notes |
| --- | --- | --- | --- |
| `bar` | `cercar` | `source_target_mapping_audit_required` | The draft active sense was an alcohol bar; cercar needs separate dictionary-source confirmation before repair. |
| `offset` | `distancia` | `source_target_mapping_audit_required` | The draft active sense was onset/outset; distancia needs a technical offset/distance mapping audit before repair. |
| `demand` | `deducción` | `source_target_mapping_audit_required` | The draft active sense was demand/request, which does not match deducción without unexpected source evidence. |

## Next Steps

- Score this trusted seed to establish the post-approval baseline.
- Create a separate discovery/locked split before threshold or scorer tuning.
- Audit excluded source-target mappings before adding them to any trusted lane.
