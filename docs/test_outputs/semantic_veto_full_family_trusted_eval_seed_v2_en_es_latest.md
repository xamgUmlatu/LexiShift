# en-es Semantic Veto Full-Family Trusted Eval Seed v2

- Status: `ok`
- Decision: `full_family_trusted_eval_seed_v2_ready_for_scoring`
- Generated: `2026-05-06T22:45:33Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v2.json`
- Trusted families: `10`
- Trusted cases: `42`
- Newly approved cases: `15`

## Approval Boundary

v2 records two explicit approval ids: the original repaired pilot approval and the deferred mapping review-fix approval. It does not make a runtime policy change.

This is trusted data, not an untouched locked-eval split. It can be used for near-term diagnostics and data-quality scoring, but threshold promotion still needs a discovery/locked split.

## Summary

| Key | Value |
| --- | --- |
| `trusted_family_count` | `10` |
| `trusted_case_count` | `42` |
| `carried_forward_family_count` | `7` |
| `newly_approved_family_count` | `3` |
| `newly_approved_case_count` | `15` |
| `rejected_mapping_count` | `1` |
| `manual_review_state` | `approved_by_user` |
| `row_quality_status` | `trusted` |
| `case_type_counts` | `{"phrase_no_winner": 10, "positive_active": 20, "shadow_negative": 12}` |
| `approval_case_counts` | `{"user_step7_repaired_pilot_approval_2026_05_07": 27, "user_step8_deferred_mapping_review_fix_approval_2026_05_07": 15}` |
| `family_repair_status_counts` | `{"active_sense_corrected": 3, "aligned_mapping_contexts_rewritten": 4, "deferred_mapping_fixed_corrected_active_sense": 2, "representative_slot_replacement_for_rejected_mapping": 1}` |

## Checks

| Check | Value |
| --- | --- |
| `has_trusted_families` | `True` |
| `all_rows_approved_by_user` | `True` |
| `all_rows_trusted` | `True` |
| `no_pending_review_rows` | `True` |
| `has_original_repaired_seed_rows` | `True` |
| `has_deferred_fix_approval_rows` | `True` |
| `has_repaired_deferred_families` | `True` |
| `rejected_demand_mapping_absent` | `True` |
| `has_active_shadow_and_no_winner_cases` | `True` |

## Trusted Families

| Source | Target | Status | v2 Status | Cases | Positive | Shadow | No-Winner |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `break` | `quebrar` | `active_sense_corrected` | `carried_forward_from_v1` | 5 | 2 | 2 | 1 |
| `bridle` | `reprimir` | `active_sense_corrected` | `carried_forward_from_v1` | 5 | 2 | 2 | 1 |
| `december` | `diciembre` | `aligned_mapping_contexts_rewritten` | `carried_forward_from_v1` | 3 | 2 | 0 | 1 |
| `emotion` | `emoción` | `aligned_mapping_contexts_rewritten` | `carried_forward_from_v1` | 3 | 2 | 0 | 1 |
| `dentist` | `dentista` | `aligned_mapping_contexts_rewritten` | `carried_forward_from_v1` | 3 | 2 | 0 | 1 |
| `bouillon` | `caldo` | `aligned_mapping_contexts_rewritten` | `carried_forward_from_v1` | 3 | 2 | 0 | 1 |
| `control` | `gobernar` | `active_sense_corrected` | `carried_forward_from_v1` | 5 | 2 | 2 | 1 |
| `bar` | `cercar` | `deferred_mapping_fixed_corrected_active_sense` | `newly_approved_deferred_fix` | 5 | 2 | 2 | 1 |
| `offset` | `distancia` | `deferred_mapping_fixed_corrected_active_sense` | `newly_approved_deferred_fix` | 5 | 2 | 2 | 1 |
| `crack` | `grieta` | `representative_slot_replacement_for_rejected_mapping` | `newly_approved_deferred_fix` | 5 | 2 | 2 | 1 |

## Rejected Mappings

| Mapping | Status | Replacement |
| --- | --- | --- |
| `demand->deducción` | `reject_mapping_source_target_mismatch` | `crack->grieta` |

## Next Steps

- Score this v2 trusted seed with TF-IDF and sentence-transformer diagnostics.
- Use the v2 seed as the near-term trusted data lane for scorer bakeoffs.
- Create or refresh a discovery/locked split before any threshold promotion claim.
