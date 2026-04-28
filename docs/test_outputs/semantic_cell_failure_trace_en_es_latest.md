# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:29:19Z`
- Matrix: `en_es_semantic_cell_failure_trace_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_cell_failure_trace_en_es.json`
- Evaluation suites: `1`
- Config rows: `7`
- Case score traces: `266`
- Case traces included in JSON: `True`
- Negative-control sanity: `not_applicable`

## Recommendation

Best promotable candidate is `cell_trace_context_selected_definition_source`; with harmful `0`; and false abstain `15`; against incumbent `cell_trace_row_control`; with negative controls delegated to the companion broad matrix.

## Best By Constraint

- incumbent_control: `cell_trace_row_control`
  - Harmful / false abstain: `0` / `17`
  - Decision / winner accuracy: `55.26%` / `55.26%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_overall: `cell_trace_context_selected_definition_source`
  - Harmful / false abstain: `0` / `15`
  - Decision / winner accuracy: `60.53%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:contextualized_source_plus_definition_rows:context_selected_top_k_mean:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `cell_trace_context_selected_definition_source`
  - Harmful / false abstain: `0` / `15`
  - Decision / winner accuracy: `60.53%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:contextualized_source_plus_definition_rows:context_selected_top_k_mean:active_minus_strongest_shadow:phrase_override`

- best_promotable_candidate: `cell_trace_context_selected_definition_source`
  - Harmful / false abstain: `0` / `15`
  - Decision / winner accuracy: `60.53%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:contextualized_source_plus_definition_rows:context_selected_top_k_mean:active_minus_strongest_shadow:phrase_override`

## Source Evidence Batches

| Path | Rows | Attached Rows | SHA-256 |
| --- | ---: | ---: | --- |
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json | 126 | 126 | efd217419778dae331058696abb2accb2d7901cafdb097f3322083f58465576c |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| context_selected_definition_source:before_after | 1 | cell_trace_context_selected_definition_source | cell_trace_context_selected_definition_source | 0 | 15 | 60.53% | 150.7895 |
| source_plus_definition:max | 1 | cell_trace_source_plus_definition_max | cell_trace_source_plus_definition_max | 0 | 15 | 60.53% | 150.7895 |
| source_rows:max | 1 | cell_trace_source_rows_max | cell_trace_source_rows_max | 0 | 15 | 60.53% | 150.7895 |
| control:definition_rows | 1 | cell_trace_row_control | cell_trace_row_control | 0 | 17 | 55.26% | 170.8947 |
| source_plus_definition:source_weighted_top2 | 1 | cell_trace_source_weighted_top2 | cell_trace_source_weighted_top2 | 0 | 17 | 55.26% | 170.8947 |
| source_plus_definition:top2 | 1 | cell_trace_source_plus_definition_top2 | cell_trace_source_plus_definition_top2 | 0 | 17 | 55.26% | 170.8947 |
| sentence_transformer:source_rows | 1 | cell_trace_sentence_transformer_source_max |  | 3 | 5 | 78.95% | 3050.4211 |

## Decision Signature Clusters

- Unique replace signatures: `4`
- Largest replace-signature cluster: `3` configs
- `00d196f441898af8`: `3` configs, sample `cell_trace_context_selected_definition_source, cell_trace_source_plus_definition_max, cell_trace_source_rows_max`
- `c187e9ec23768e47`: `2` configs, sample `cell_trace_source_plus_definition_top2, cell_trace_source_weighted_top2`
- `4a9c0d15b4eb194a`: `1` configs, sample `cell_trace_row_control`
- `ae6ca5e4e85e7622`: `1` configs, sample `cell_trace_sentence_transformer_source_max`

## Headline Metric Ties

- Tied primary-metric groups: `2`
- Largest tied group: `3` configs
- `harm=0|false=17|decision=0.552632|winner=0.552632`: `3` configs, unique replace signatures `2`, ROC AUC `0.6066..0.7175`, Avg Prec. `0.6293..0.7088`
- `harm=0|false=15|decision=0.605263|winner=0.605263`: `3` configs, unique replace signatures `1`, ROC AUC `0.6898..0.7285`, Avg Prec. `0.7253..0.7293`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| context_selected_definition_source:before_after | cell_trace_context_selected_definition_source | 0 | 9 | 0 | 6 | 60.8571 | cell_trace_context_selected_definition_source |
| source_plus_definition:max | cell_trace_source_plus_definition_max | 0 | 9 | 0 | 6 | 60.8571 | cell_trace_source_plus_definition_max |
| source_rows:max | cell_trace_source_rows_max | 0 | 9 | 0 | 6 | 60.8571 | cell_trace_source_rows_max |
| source_plus_definition:source_weighted_top2 | cell_trace_source_weighted_top2 | 0 | 10 | 0 | 7 | 71.0000 | cell_trace_source_weighted_top2 |
| source_plus_definition:top2 | cell_trace_source_plus_definition_top2 | 0 | 10 | 0 | 7 | 71.0000 | cell_trace_source_plus_definition_top2 |
| control:definition_rows | cell_trace_row_control | 0 | 9 | 0 | 8 | 81.1429 | cell_trace_row_control |
| sentence_transformer:source_rows | cell_trace_sentence_transformer_source_max | 2 | 4 | 1 | 1 | 1010.2857 | cell_trace_sentence_transformer_source_max |

## Incumbent Case Deltas

- Incumbent config: `cell_trace_row_control`
- Configs identical to incumbent decisions: `0`
- `cell_trace_sentence_transformer_source_max`: decisions changed `15`, false abstains fixed/introduced `12`/`0`, harmful fixed/introduced `0`/`3`
- `cell_trace_context_selected_definition_source`: decisions changed `6`, false abstains fixed/introduced `4`/`2`, harmful fixed/introduced `0`/`0`
- `cell_trace_source_plus_definition_max`: decisions changed `6`, false abstains fixed/introduced `4`/`2`, harmful fixed/introduced `0`/`0`
- `cell_trace_source_rows_max`: decisions changed `6`, false abstains fixed/introduced `4`/`2`, harmful fixed/introduced `0`/`0`
- `cell_trace_source_plus_definition_top2`: decisions changed `4`, false abstains fixed/introduced `2`/`2`, harmful fixed/introduced `0`/`0`
- `cell_trace_source_weighted_top2`: decisions changed `4`, false abstains fixed/introduced `2`/`2`, harmful fixed/introduced `0`/`0`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | context_selected_definition_source:before_after | cell_trace_context_selected_definition_source | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 15 | 60.53% | 0.7285 | 0.7253 | 150.7895 |
| 2 | source_plus_definition:max | cell_trace_source_plus_definition_max | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 15 | 60.53% | 0.7285 | 0.7293 | 150.7895 |
| 3 | source_rows:max | cell_trace_source_rows_max | tfidf_cosine | masked_sentence | source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 15 | 60.53% | 0.6898 | 0.7262 | 150.7895 |
| 4 | control:definition_rows | cell_trace_row_control | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 17 | 55.26% | 0.6066 | 0.6293 | 170.8947 |
| 5 | source_plus_definition:top2 | cell_trace_source_plus_definition_top2 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 17 | 55.26% | 0.7147 | 0.6953 | 170.8947 |
| 6 | source_plus_definition:source_weighted_top2 | cell_trace_source_weighted_top2 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 0 | 17 | 55.26% | 0.7175 | 0.7088 | 170.8947 |
| 7 | sentence_transformer:source_rows | cell_trace_sentence_transformer_source_max | sentence_transformer_cosine | masked_sentence | source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 3 | 5 | 78.95% | 0.8975 | 0.8537 | 3050.4211 |

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `cell_trace_context_selected_definition_source`: discovery objective `90.7500`, locked objective `60.8571`, worst leave-one-family objective `150.8333`
- `cell_trace_source_plus_definition_max`: discovery objective `90.7500`, locked objective `60.8571`, worst leave-one-family objective `150.8333`
- `cell_trace_source_rows_max`: discovery objective `90.7500`, locked objective `60.8571`, worst leave-one-family objective `150.8333`
- `cell_trace_source_plus_definition_top2`: discovery objective `100.8333`, locked objective `71.0000`, worst leave-one-family objective `170.9444`
- `cell_trace_source_weighted_top2`: discovery objective `100.8333`, locked objective `71.0000`, worst leave-one-family objective `170.9444`
- `cell_trace_row_control`: discovery objective `90.7500`, locked objective `81.1429`, worst leave-one-family objective `170.9444`
- `cell_trace_sentence_transformer_source_max`: discovery objective `2040.5000`, locked objective `1010.2857`, worst leave-one-family objective `3050.4444`
