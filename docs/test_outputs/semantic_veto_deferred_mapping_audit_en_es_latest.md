# en-es Semantic Veto Deferred Mapping Audit

- Status: `ok`
- Decision: `deferred_mapping_audit_complete`
- Generated: `2026-05-06T22:22:12Z`
- Mappings audited: `3`
- Salvageable with corrected active sense: `2`
- Rejected source-target mismatch: `1`

## Methodology

For each deferred mapping, determine whether the source-target pair is supported by independent dictionary/sense evidence and whether it can be rewritten into a coherent pending-review test family.

This audit does not make new rows trusted. Salvageable mappings need fresh row authoring and user review before they enter any trusted lane.

## Checks

| Check | Value |
| --- | --- |
| `all_mappings_present_in_repaired_deferred_families` | `True` |
| `all_deferred_mappings_excluded_from_trusted_seed` | `True` |
| `all_mappings_trace_to_srs_source_target_bridge` | `True` |
| `all_mappings_have_installed_dictionary_evidence` | `True` |
| `no_mapping_promoted_to_trusted` | `True` |

## Mapping Decisions

| Mapping | Status | Confidence | Evidence Summary | Recommended Action |
| --- | --- | --- | --- | --- |
| `bar->cercar` | `salvageable_with_corrected_active_sense` | `medium` | source->target exact not found; target->source exact found; source sense hits: obstruct, passage, lock, bolt; target gloss hits: corral, fence, fence off | Do not revive the alcohol-bar draft rows. Author a fresh pending-review family around verb contexts such as 'bar the entrance' or 'bar the way', with shadows for pub/counter/legal-bar senses. |
| `offset->distancia` | `salvageable_with_corrected_active_sense` | `medium_low` | source->target exact not found; target->source exact found; source sense hits: distance by which, out of alignment; target gloss hits: distance | Author fresh pending-review technical/spatial rows only if the product accepts the broad target 'distancia' for this sense; otherwise replace the target with a more specific Spanish competitor such as 'desfase'. |
| `demand->deducción` | `reject_mapping_source_target_mismatch` | `high` | source->target exact not found; target->source exact found; source sense hits: request, claim, purchase goods, summons; target gloss hits: deduction | Keep excluded from trusted evaluation. Treat the reverse FreeDict mapping as insufficient or erroneous unless an independent source proves a valid sense; sample a replacement family for this cell instead. |

## Evidence Details

| Mapping | Draft Active Gloss | Corrected Active Gloss | Source Evidence | Target Evidence |
| --- | --- | --- | --- | --- |
| `bar->cercar` | a room or establishment where alcoholic drinks are served over a counter | bar as a verb: obstruct, block, or fence off passage | barrear: to obstruct the passage of; embarrar: to lock or bolt with a bar; barretear: to lock or bolt with a bar | to corral, fence, fence off: (transitive) to corral, fence, fence off |
| `offset->distancia` | the time at which something is supposed to begin | offset as a noun: the distance or displacement by which one thing is out of alignment with another | desfase: distance by which one thing is out of alignment with another; excentricidad: distance by which one thing is out of alignment with another; desfasaje: distance by which one thing is out of alignment with another | distance:  |
| `demand->deducción` | an urgent or peremptory request |  | demanda: desire to purchase goods and services; demanda económica: desire to purchase goods and services; intimación: forceful claim for something | deduction:  |

## Next Steps

- Keep demand -> deducción excluded unless an independent source disproves the mismatch.
- If desired, author pending-review repaired rows for bar -> cercar and offset -> distancia from corrected active senses only.
- User-review any newly authored rows before adding them to the trusted eval seed.
- Replace the rejected demand-family slot with a fresh representative family from the same sampling cell.
