# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:30:23Z`
- Matrix: `en_es_semantic_cell_failure_trace_reference_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_cell_failure_trace_reference_en_es.json`
- Evaluation suites: `1`
- Config rows: `4`
- Case score traces: `152`
- Case traces included in JSON: `True`
- Negative-control sanity: `not_applicable`

## Recommendation

No candidate cleared the incumbent-aware promotability screen; treat the matrix as evidence for source coverage or representation work before policy promotion.

## Best By Constraint

- incumbent_control: `cell_reference_source_plus_definition_max`
  - Harmful / false abstain: `1` / `17`
  - Decision / winner accuracy: `52.63%` / `52.63%`
  - Shape: `tfidf_cosine:masked_sentence:source_plus_definition_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_overall: `cell_reference_context_selected_definition_source`
  - Harmful / false abstain: `0` / `18`
  - Decision / winner accuracy: `52.63%` / `52.63%`
  - Shape: `tfidf_cosine:masked_sentence:contextualized_source_plus_definition_rows:context_selected_top_k_mean:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `cell_reference_context_selected_definition_source`
  - Harmful / false abstain: `0` / `18`
  - Decision / winner accuracy: `52.63%` / `52.63%`
  - Shape: `tfidf_cosine:masked_sentence:contextualized_source_plus_definition_rows:context_selected_top_k_mean:active_minus_strongest_shadow:phrase_override`

## Source Evidence Batches

| Path | Rows | Attached Rows | SHA-256 |
| --- | ---: | ---: | --- |
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json | 133 | 133 | 3a7e43969a88db83a76ec945c5c649224e7b3da518986d25ce983210f101e740 |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| reference_context_selected_definition_source:before_after | 1 | cell_reference_context_selected_definition_source | cell_reference_context_selected_definition_source | 0 | 18 | 52.63% | 180.9474 |
| reference_source_plus_definition:max | 1 | cell_reference_source_plus_definition_max |  | 1 | 17 | 52.63% | 1170.9474 |
| reference_source_rows:max | 1 | cell_reference_source_rows_max |  | 1 | 17 | 52.63% | 1170.9474 |
| reference_sentence_transformer:source_rows | 1 | cell_reference_sentence_transformer_source_rows |  | 3 | 2 | 86.84% | 3020.2632 |

## Decision Signature Clusters

- Unique replace signatures: `3`
- Largest replace-signature cluster: `2` configs
- `044c87f3d6956174`: `2` configs, sample `cell_reference_source_plus_definition_max, cell_reference_source_rows_max`
- `6ffbe836593adcb3`: `1` configs, sample `cell_reference_context_selected_definition_source`
- `7b4ebb32a09308b4`: `1` configs, sample `cell_reference_sentence_transformer_source_rows`

## Headline Metric Ties

- Tied primary-metric groups: `1`
- Largest tied group: `2` configs
- `harm=1|false=17|decision=0.526316|winner=0.526316`: `2` configs, unique replace signatures `1`, ROC AUC `0.5499..0.5817`, Avg Prec. `0.5548..0.5779`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| reference_source_plus_definition:max | cell_reference_source_plus_definition_max | 1 | 9 | 0 | 8 | 81.1429 | cell_reference_source_plus_definition_max |
| reference_source_rows:max | cell_reference_source_rows_max | 1 | 9 | 0 | 8 | 81.1429 | cell_reference_source_rows_max |
| reference_context_selected_definition_source:before_after | cell_reference_context_selected_definition_source | 0 | 9 | 0 | 9 | 91.2857 | cell_reference_context_selected_definition_source |
| reference_sentence_transformer:source_rows | cell_reference_sentence_transformer_source_rows | 2 | 2 | 1 | 0 | 1000.1429 | cell_reference_sentence_transformer_source_rows |

## Incumbent Case Deltas

- Incumbent config: `cell_reference_source_plus_definition_max`
- Configs identical to incumbent decisions: `1`
- `cell_reference_sentence_transformer_source_rows`: decisions changed `19`, false abstains fixed/introduced `15`/`0`, harmful fixed/introduced `1`/`3`
- `cell_reference_context_selected_definition_source`: decisions changed `2`, false abstains fixed/introduced `0`/`1`, harmful fixed/introduced `1`/`0`
- `cell_reference_source_rows_max`: decisions changed `0`, false abstains fixed/introduced `0`/`0`, harmful fixed/introduced `0`/`0`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | reference_context_selected_definition_source:before_after | cell_reference_context_selected_definition_source | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 18 | 52.63% | 0.6122 | 0.5534 | 180.9474 |
| 2 | reference_source_plus_definition:max | cell_reference_source_plus_definition_max | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 17 | 52.63% | 0.5817 | 0.5779 | 1170.9474 |
| 3 | reference_source_rows:max | cell_reference_source_rows_max | tfidf_cosine | masked_sentence | source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 17 | 52.63% | 0.5499 | 0.5548 | 1170.9474 |
| 4 | reference_sentence_transformer:source_rows | cell_reference_sentence_transformer_source_rows | sentence_transformer_cosine | masked_sentence | source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 3 | 2 | 86.84% | 0.9003 | 0.8824 | 3020.2632 |

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `cell_reference_source_plus_definition_max`: discovery objective `1090.8333`, locked objective `81.1429`, worst leave-one-family objective `1171.0000`
- `cell_reference_source_rows_max`: discovery objective `1090.8333`, locked objective `81.1429`, worst leave-one-family objective `1171.0000`
- `cell_reference_context_selected_definition_source`: discovery objective `90.7500`, locked objective `91.2857`, worst leave-one-family objective `181.0000`
- `cell_reference_sentence_transformer_source_rows`: discovery objective `2020.3333`, locked objective `1000.1429`, worst leave-one-family objective `3020.2778`
