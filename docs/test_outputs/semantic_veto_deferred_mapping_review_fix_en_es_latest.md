# en-es Semantic Veto Deferred Mapping Review Fix

- Status: `ok`
- Decision: `deferred_mapping_review_fix_ready_for_user_review`
- Generated: `2026-05-06T22:37:34Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_deferred_mapping_review_fix_v1.json`
- Fixed families: `3`
- Fixed cases: `15`
- Rejected mappings: `1`
- Trusted rows: `0`

## Methodology

Repair only mappings the audit marked salvageable with corrected active sense; reject mismatched mappings; preserve the representative cell by adding a fresh replacement family from the same source-band/polysemy/POS shape; use independent contexts and real Spanish shadow targets.

Rows are agent-reviewed and repaired, but they are not user-approved gold data.

## Summary

| Key | Value |
| --- | --- |
| `fixed_family_count` | `3` |
| `fixed_case_count` | `15` |
| `salvaged_mapping_count` | `2` |
| `replacement_family_count` | `1` |
| `rejected_mapping_count` | `1` |
| `trusted_case_count` | `0` |
| `manual_review_state` | `agent_reviewed_user_review_pending` |
| `case_type_counts` | `{"phrase_no_winner": 3, "positive_active": 6, "shadow_negative": 6}` |
| `family_repair_status_counts` | `{"deferred_mapping_fixed_corrected_active_sense": 2, "representative_slot_replacement_for_rejected_mapping": 1}` |
| `source_cell_case_counts` | `{"source_zipf=zipf_3_to_4_mid::polysemy=high_10_plus::pos_shape=cross_pos_polysemy": 5, "source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy": 10}` |

## Checks

| Check | Value |
| --- | --- |
| `has_fixed_families` | `True` |
| `salvageable_audit_rows_repaired` | `True` |
| `rejected_mapping_not_repaired_as_same_pair` | `True` |
| `replacement_family_same_source_cell` | `True` |
| `has_active_shadow_and_no_winner_cases` | `True` |
| `all_rows_pending_user_review` | `True` |
| `no_placeholder_shadow_targets` | `True` |
| `all_cases_have_standalone_source_token` | `True` |
| `no_definition_fallback_templates` | `True` |
| `no_trusted_rows_claimed` | `True` |

## Fixed Families

| Source | Target | Status | Cases | Positive | Shadow | No-Winner | Review Note |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `bar` | `cercar` | `deferred_mapping_fixed_corrected_active_sense` | 5 | 2 | 2 | 1 | The draft alcohol-bar active sense was rejected. This fixed family tests only the verb/blockage sense supported by the audit. |
| `offset` | `distancia` | `deferred_mapping_fixed_corrected_active_sense` | 5 | 2 | 2 | 1 | The draft outset active sense was rejected. This fixed family tests only the spatial/technical distance sense; broad target adequacy remains a review question. |
| `crack` | `grieta` | `representative_slot_replacement_for_rejected_mapping` | 5 | 2 | 2 | 1 | This family replaces demand -> deducción in the same source-band, polysemy, and POS-shape cell because demand -> deducción failed the source-target audit. |

## Rejected Mappings

| Mapping | Status | Replacement |
| --- | --- | --- |
| `demand->deducción` | `reject_mapping_source_target_mismatch` | `crack->grieta` |

## Next Steps

- User reviews this fixed packet before any row enters trusted evaluation.
- Run sentence-veto diagnostics as a data-quality smoke test only.
- If approved, append these rows to a separate trusted addendum or rerun the trusted-seed builder with an explicit approval id.
