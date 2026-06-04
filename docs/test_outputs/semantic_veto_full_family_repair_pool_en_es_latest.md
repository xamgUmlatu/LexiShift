# en-es Semantic Veto Full-Family Repair Pool

- Status: `ok`
- Decision: `full_family_repair_pool_user_approved_for_exploratory_sweeps`
- Generated: `2026-05-07T19:46:39Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json`
- Repaired families: `49`
- Repaired cases: `189`
- Excluded families: `9`
- Trusted rows: `189`

## Methodology

Materialize every repair-pool family from the full 58-family agent review, exclude rejected/artifact mappings, rewrite active contexts independently, keep source tokens standalone, use real Spanish shadow competitor targets only when a true competitor was authored, and mark the repaired rows as user-approved for exploratory sweeps.

Draft same-target POS shadows are dropped. Shadow-negative rows are included only when the repaired spec names a distinct Spanish competitor.

Rows are repaired for semantic coherence and user-approved for exploratory sweeps.

## Summary

| Key | Value |
| --- | --- |
| `issues` | `[]` |
| `reviewed_family_count` | `58` |
| `repaired_family_count` | `49` |
| `repaired_case_count` | `189` |
| `excluded_family_count` | `9` |
| `shadow_evidence_count` | `42` |
| `trusted_case_count` | `189` |
| `case_type_counts` | `{"phrase_no_winner": 49, "positive_active": 98, "shadow_negative": 42}` |
| `source_band_case_counts` | `{"zipf_3_to_4_mid": 57, "zipf_4_to_5_common": 42, "zipf_5_plus_very_common": 60, "zipf_below_3_rare": 30}` |
| `family_disposition_counts` | `{"aligned_mapping_rewrite_contexts": 18, "aligned_mapping_shadow_rows_not_competitors": 16, "salvage_with_corrected_active_sense": 15}` |
| `active_sense_status_counts` | `{"aligned": 34, "corrected_active_sense_required": 15}` |

## Checks

| Check | Value |
| --- | --- |
| `all_expected_repair_families_materialized` | `True` |
| `has_repaired_families` | `True` |
| `has_positive_shadow_and_no_winner_cases` | `True` |
| `every_family_has_positive_and_no_winner` | `True` |
| `all_rows_approved_by_user` | `True` |
| `all_approved_rows_trusted` | `True` |
| `no_placeholder_shadow_targets` | `True` |
| `all_shadow_targets_are_real` | `True` |
| `all_cases_have_standalone_source_token` | `True` |
| `no_definition_fallback_templates` | `True` |
| `all_trusted_rows_have_approval_id` | `True` |
| `rejected_families_excluded` | `True` |

## Repaired Families

| Source | Target | Disposition | Cases | Positive | Shadow | No-Winner |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `break` | `quebrar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `bar` | `cercar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `offset` | `distancia` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `bridle` | `reprimir` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `december` | `diciembre` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `emotion` | `emoción` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `dentist` | `dentista` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `bouillon` | `caldo` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `control` | `gobernar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `stall` | `cuadra` | `aligned_mapping_rewrite_contexts` | 5 | 2 | 2 | 1 |
| `rumanian` | `rumano` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `june` | `junio` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `pub` | `taberna` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `salesman` | `vendedor` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `handiwork` | `artesanía` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `continue` | `durar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `begin` | `comenzar` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `chic` | `elegante` | `aligned_mapping_rewrite_contexts` | 4 | 2 | 1 | 1 |
| `billow` | `oleaje` | `aligned_mapping_rewrite_contexts` | 5 | 2 | 2 | 1 |
| `among` | `entre` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `recover` | `sanar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `adjoining` | `contiguo` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `argentinean` | `argentino` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `heart` | `corazón` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `cite` | `mencionar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `snore` | `roncar` | `salvage_with_corrected_active_sense` | 4 | 2 | 1 | 1 |
| `upon` | `sobre` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `adjoining` | `vecino` | `aligned_mapping_rewrite_contexts` | 3 | 2 | 0 | 1 |
| `current` | `contemporáneo` | `aligned_mapping_rewrite_contexts` | 5 | 2 | 2 | 1 |
| `parrot` | `loro` | `aligned_mapping_rewrite_contexts` | 5 | 2 | 2 | 1 |
| `american` | `americano` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `german` | `alemán` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `rebate` | `descuento` | `aligned_mapping_rewrite_contexts` | 5 | 2 | 2 | 1 |
| `adder` | `víbora` | `salvage_with_corrected_active_sense` | 4 | 2 | 1 | 1 |
| `tomorrow` | `mañana` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `pair` | `par` | `aligned_mapping_shadow_rows_not_competitors` | 4 | 2 | 1 | 1 |
| `endure` | `durar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `russian` | `ruso` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `smile` | `sonreír` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `govern` | `gobernar` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `brother` | `hermano` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `acceptable` | `razonable` | `aligned_mapping_shadow_rows_not_competitors` | 5 | 2 | 2 | 1 |
| `altitude` | `elevación` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `health` | `salud` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `shortage` | `falta` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `except` | `excepto` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `entirely` | `enteramente` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |
| `region` | `comarca` | `salvage_with_corrected_active_sense` | 5 | 2 | 2 | 1 |
| `owe` | `deber` | `aligned_mapping_shadow_rows_not_competitors` | 3 | 2 | 0 | 1 |

## Excluded Families

| Source | Target | Disposition | Reason |
| --- | --- | --- | --- |
| `demand` | `deducción` | `source_target_mapping_rejected` | Demand/request/economic demand does not match deducción. |
| `grow` | `acontecer` | `source_target_mapping_rejected` | Grow does not naturally map to acontecer, which means happen/occur. |
| `turnon` | `poner` | `source_form_artifact_rejected` | Unspaced trigger turnon is not a normal browser-facing source token for this target. |
| `shed` | `puesto` | `source_target_mapping_rejected` | Draft caducous, outbuilding, and remove senses do not justify puesto as a trusted target. |
| `aberration` | `equivocación` | `questionable_mapping_rejected` | Aberration as deviation/disorder/optical flaw is not reliably equivocación. |
| `sale` | `deducción` | `source_target_mapping_rejected` | Sale/selling/discount event does not reliably map to deducción. |
| `conversance` | `notoriedad` | `source_target_mapping_rejected` | Conversance means familiarity/knowledge, not notoriety/fame. |
| `femalejournalist` | `periodista` | `source_form_artifact_rejected` | Unspaced source form is an artifact; use journalist/female journalist only in a separate source-form lane. |
| `mosaicwork` | `mosaico` | `source_form_artifact_rejected` | Unspaced source form is an artifact, even though mosaic work can map to mosaico. |

## Issues

- `none`

## Next Steps

- Run sentence-veto diagnostics on this repaired-full candidate.
- Rerun band-formula and Zipf-boundary sweeps on this larger approved denominator.
- Use any promising ranking only for LLM data allocation until a locked-eval split confirms it.
