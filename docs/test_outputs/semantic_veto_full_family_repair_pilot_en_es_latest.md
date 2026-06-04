# en-es Semantic Veto Full-Family Repaired Pilot

- Status: `ok`
- Decision: `full_family_repaired_pilot_ready_for_user_review`
- Generated: `2026-05-06T21:59:45Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_pilot_v1.json`
- Repaired families: `7`
- Repaired cases: `27`
- Deferred families: `3`
- Trusted rows: `0`

## Methodology

Keep only aligned or salvageable pilot families; correct active senses where salvageable; defer questionable source-target mappings; use real Spanish shadow targets; use standalone source tokens; replace definition fallbacks with independent contexts.

Rows are semantically repaired, but they are not user-approved gold data.

## Summary

| Key | Value |
| --- | --- |
| `repaired_family_count` | `7` |
| `repaired_case_count` | `27` |
| `deferred_family_count` | `3` |
| `trusted_family_count` | `0` |
| `trusted_case_count` | `0` |
| `manual_review_state` | `agent_repaired_user_review_pending` |
| `case_type_counts` | `{"phrase_no_winner": 7, "positive_active": 14, "shadow_negative": 6}` |
| `family_repair_status_counts` | `{"active_sense_corrected": 3, "aligned_mapping_contexts_rewritten": 4}` |
| `source_band_case_counts` | `{"zipf_3_to_4_mid": 3, "zipf_4_to_5_common": 3, "zipf_5_plus_very_common": 13, "zipf_below_3_rare": 8}` |

## Checks

| Check | Value |
| --- | --- |
| `has_repaired_families` | `True` |
| `has_active_shadow_and_no_winner_cases` | `True` |
| `all_rows_pending_user_review` | `True` |
| `no_placeholder_shadow_targets` | `True` |
| `all_cases_have_standalone_source_token` | `True` |
| `no_definition_fallback_templates` | `True` |
| `no_trusted_rows_claimed` | `True` |

## Repaired Families

| Source | Target | Status | Cases | Positive | Shadow | No-Winner |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `break` | `quebrar` | `active_sense_corrected` | 5 | 2 | 2 | 1 |
| `bridle` | `reprimir` | `active_sense_corrected` | 5 | 2 | 2 | 1 |
| `december` | `diciembre` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `emotion` | `emoción` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `dentist` | `dentista` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `bouillon` | `caldo` | `aligned_mapping_contexts_rewritten` | 3 | 2 | 0 | 1 |
| `control` | `gobernar` | `active_sense_corrected` | 5 | 2 | 2 | 1 |

## Deferred Families

| Source | Target | Reason | Notes |
| --- | --- | --- | --- |
| `bar` | `cercar` | `source_target_mapping_audit_required` | The draft active sense was an alcohol bar; cercar needs separate dictionary-source confirmation before repair. |
| `offset` | `distancia` | `source_target_mapping_audit_required` | The draft active sense was onset/outset; distancia needs a technical offset/distance mapping audit before repair. |
| `demand` | `deducción` | `source_target_mapping_audit_required` | The draft active sense was demand/request, which does not match deducción without unexpected source evidence. |

## Next Steps

- User reviews the repaired packet before any row is counted as trusted.
- Run sentence-veto scoring as a diagnostic comparison against the unrepaired pilot.
- Audit deferred mappings before spending LLM generation or manual rewrite effort on them.
- If approved, split the repaired packet into discovery and locked-eval lanes before scorer tuning.
