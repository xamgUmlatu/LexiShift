# en-es Non-v10 Source Portfolio Materialization

- Status: `ok`
- Decision: `source_portfolio_materialized`
- Generated: `2026-04-28T22:34:17Z`
- Selected families: `16`
- Materialized families: `16`
- Candidate rows: `51`
- Final admitted rows: `51`
- Semantic contract: `16` / `16`
- Phrase contract: `0` / `16`
- Supporting variants used: `2`

## Family Selection

| Family | Trigger | Supporting Variant | Rows |
| --- | --- | --- | ---: |
| `en-es:sentence-veto:dry:seco` | `dry` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:use:uso` | `use` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:plain:llano` | `plain` | `min0p12-extract0-definition_and_example-rows2` | 4 |
| `en-es:sentence-veto:fast:r-pido` | `fast` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:train:tren` | `train` | `min0p12-extract0-definition_and_example-rows2` | 4 |
| `en-es:sentence-veto:land:tierra` | `land` | `min0p12-extract0-definition_and_example-rows2` | 5 |
| `en-es:sentence-veto:mean:medio` | `mean` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:offer:oferta` | `offer` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:present:presente` | `present` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:sign:se-al` | `sign` | `min0p12-extract0-definition_and_example-rows2` | 5 |
| `en-es:sentence-veto:quiet:silencio` | `quiet` | `min0p12-extract0-definition_and_example-rows2` | 2 |
| `en-es:sentence-veto:change:cambio` | `change` | `min0p12-extract0-definition_and_example-rows2` | 2 |
| `en-es:sentence-veto:look:aspecto` | `look` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:rest:reposo` | `rest` | `min0p12-definition_and_example-rows2` | 2 |
| `en-es:sentence-veto:answer:respuesta` | `answer` | `min0p12-extract0-definition_and_example-rows2` | 3 |
| `en-es:sentence-veto:end:fin` | `end` | `min0p12-extract0-definition_and_example-rows2` | 3 |

## Limitations

- `draft_wave_is_unreviewed_and_not_a_promotion_candidate`
- `materialized_rows_are_external_wordnet_evidence_only`
- `phrase_containment_rows_are_not_generated_by_this_lane`
- `independent_active_shadow_and_phrase_heldout_cases_are_still_required`

## Next Steps

- add independent active/shadow held-out cases for the selected 16 families
- add independent phrase/no-winner held-out cases for the same selected families
- run held-out validation against this exact materialized source batch
- only then compare scoring or runtime-policy promotion claims

## Artifacts

- selected_dataset_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave5_anypos_source_portfolio_materialized_v1_dataset.json`
- selected_queue_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_non_v10_wave_drafts/semantic_source_non_v10_wave5_anypos_source_portfolio_materialized_queue_en_es_v1.json`
- candidate_batch_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_normalized_evidence.json`
- cycle_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest.json`
- cycle_markdown: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_source_admission_cycle_non_v10_wave5_source_portfolio_latest.md`
- cycle_sense_batch_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_cycle_sense_admitted_normalized_evidence.json`
- cycle_candidate_admitted_batch_json: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-source-portfolio-non-v10-wave5-anypos-v1-latest_admitted_delta_normalized_evidence.json`
