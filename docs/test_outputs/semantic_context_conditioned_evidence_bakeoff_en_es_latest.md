# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T20:35:33Z`
- Matrix: `en_es_semantic_context_conditioned_evidence_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_context_conditioned_evidence_bakeoff_en_es.json`
- Evaluation suites: `4`
- Config rows: `174`
- Case score traces: `33060`
- Case traces included in JSON: `False`
- Negative-control sanity: `ok`

## Recommendation

Best promotable candidate is `context_conditioned_control_rows_max`; with harmful `0`; and false abstain `45`; against incumbent `context_conditioned_control_current_all`; and negative controls failed as expected.

## Best By Constraint

- incumbent_control: `context_conditioned_control_current_all`
  - Harmful / false abstain: `1` / `46`
  - Decision / winner accuracy: `75.26%` / `58.77%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `context_conditioned_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `context_conditioned_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_promotable_candidate: `context_conditioned_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

## Source Evidence Batches

| Path | Rows | Attached Rows | SHA-256 |
| --- | ---: | ---: | --- |
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-reverse-aux-wordnet-def-example-all-v10-20260425a_cycle_sense_admitted_normalized_evidence.json | 87 | 87 | 790fc2dd96588d1a083f727ee4b120439110c2416e7dfd754bbe91df07492954 |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control:rows_max | 1 | context_conditioned_control_rows_max | context_conditioned_control_rows_max | 0 | 45 | 60.53% | 450.6316 |
| context_selected_definition_source:before_after | 24 | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | 0 | 53 | 53.51% | 530.7439 |
| context_selected_definition_source:surface_frame | 24 | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | 0 | 53 | 53.51% | 530.7439 |
| source_plus_definition:max | 12 | source_plus_definition_rows_max_tfidf:a0_1__m0 | source_plus_definition_rows_max_tfidf:a0_1__m0 | 0 | 54 | 52.63% | 540.7579 |
| context_selected:before_after | 18 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| context_selected:dependency_role | 18 | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| context_selected:masked_sentence | 18 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| context_selected:raw_window | 18 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| context_selected:surface_frame | 18 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| source_rows:max | 12 | source_rows_max_tfidf:a0_1__m0 | source_rows_max_tfidf:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| control:current_all | 1 | context_conditioned_control_current_all |  | 1 | 46 | 58.77% | 1460.6596 |
| sentence_transformer:context_selected_before_after | 4 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |  | 9 | 24 | 74.56% | 9240.4281 |
| sentence_transformer:source_rows_max | 4 | sentence_transformer_source_rows_max:a0_1__m0_05 |  | 9 | 25 | 73.68% | 9250.4421 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| context_conditioned_control_rows_max | frozen_v10 | 95 | 0 | 27 | 71.58% |
| context_conditioned_control_rows_max | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005 | frozen_v10 | 95 | 0 | 35 | 63.16% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |

## Decision Signature Clusters

- Unique replace signatures: `78`
- Largest replace-signature cluster: `34` configs
- `40bcd460411b340b`: `34` configs, sample `context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0, context_selected_source_before_after:selection_top_k1__a0_1__m0, context_selected_source_before_after:selection_top_k1__a0_1__m0_005, context_selected_source_before_after:selection_top_k2__a0_1__m0`
- `e3b0c44298fc1c14`: `8` configs, sample `context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_1__m0, context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_1__m0_005, context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_1__m0, context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_1__m0_005, context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0`
- `18fcfd763ba3066c`: `4` configs, sample `context_selected_source_masked_sentence:selection_top_k1__a0__m0, context_selected_source_masked_sentence:selection_top_k2__a0__m0, context_selected_source_masked_sentence:selection_top_k3__a0__m0, source_rows_max_tfidf:a0__m0`
- `4c135828b8d57e37`: `4` configs, sample `context_selected_source_masked_sentence:selection_top_k1__a0__m0_005, context_selected_source_masked_sentence:selection_top_k2__a0__m0_005, context_selected_source_masked_sentence:selection_top_k3__a0__m0_005, source_rows_max_tfidf:a0__m0_005`
- `611fbd0f90220316`: `4` configs, sample `context_selected_source_masked_sentence:selection_top_k1__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k2__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k3__a0_05__m0_005, source_rows_max_tfidf:a0_05__m0_005`

## Headline Metric Ties

- Tied primary-metric groups: `32`
- Largest tied group: `38` configs
- `harm=0|false=55|decision=0.710526|winner=0.517544`: `38` configs, unique replace signatures `2`, ROC AUC `0.5233..0.5901`, Avg Prec. `0.3523..0.4125`
- `harm=0|false=57|decision=0.700000|winner=0.500000`: `8` configs, unique replace signatures `1`, ROC AUC `0.5693..0.5806`, Avg Prec. `0.3862..0.3966`
- `harm=0|false=53|decision=0.721053|winner=0.535088`: `6` configs, unique replace signatures `2`, ROC AUC `0.5693..0.5806`, Avg Prec. `0.3902..0.3966`
- `harm=7|false=53|decision=0.684211|winner=0.517544`: `6` configs, unique replace signatures `2`, ROC AUC `0.5233..0.5337`, Avg Prec. `0.3523..0.3616`
- `harm=0|false=54|decision=0.715789|winner=0.526316`: `5` configs, unique replace signatures `2`, ROC AUC `0.5770..0.5901`, Avg Prec. `0.3862..0.4125`
- `harm=9|false=49|decision=0.694737|winner=0.535088`: `4` configs, unique replace signatures `3`, ROC AUC `0.5722..0.5901`, Avg Prec. `0.3978..0.4125`
- `harm=7|false=52|decision=0.689474|winner=0.517544`: `4` configs, unique replace signatures `2`, ROC AUC `0.5379..0.5580`, Avg Prec. `0.3645..0.3879`
- `harm=8|false=50|decision=0.694737|winner=0.526316`: `4` configs, unique replace signatures `2`, ROC AUC `0.5722..0.5901`, Avg Prec. `0.3978..0.4125`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control:rows_max | context_conditioned_control_rows_max | 0 | 28 | 0 | 17 | 170.7428 | context_conditioned_control_rows_max |
| context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_source_before_after:selection_top_k1__a0_1__m0 |
| context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 |
| context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 |
| context_selected:raw_window | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 |
| context_selected:surface_frame | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 |
| context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | 0 | 36 | 0 | 18 | 180.7865 | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 |
| context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 |
| source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0 | 0 | 36 | 0 | 18 | 180.7865 | source_plus_definition_rows_max_tfidf:a0_1__m0 |
| source_rows:max | source_rows_max_tfidf:a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | source_rows_max_tfidf:a0_1__m0 |
| control:current_all | context_conditioned_control_current_all | 0 | 28 | 1 | 18 | 1180.8302 | context_conditioned_control_current_all |
| sentence_transformer:context_selected_before_after | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 | 7 | 18 | 2 | 6 | 2060.3225 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |
| sentence_transformer:source_rows_max | sentence_transformer_source_rows_max:a0_1__m0_05 | 7 | 19 | 2 | 6 | 2060.3225 | sentence_transformer_source_rows_max:a0_1__m0_05 |

## Incumbent Case Deltas

- Incumbent config: `context_conditioned_control_current_all`
- Configs identical to incumbent decisions: `0`
- `context_selected_source_dependency_role:selection_top_k1__a0__m0`: decisions changed `91`, false abstains fixed/introduced `32`/`2`, harmful fixed/introduced `0`/`57`
- `context_selected_source_raw_window:selection_top_k1__a0__m0`: decisions changed `91`, false abstains fixed/introduced `30`/`2`, harmful fixed/introduced `0`/`59`
- `context_selected_source_surface_frame:selection_top_k1__a0__m0`: decisions changed `90`, false abstains fixed/introduced `31`/`2`, harmful fixed/introduced `0`/`57`
- `context_selected_source_before_after:selection_top_k1__a0__m0`: decisions changed `90`, false abstains fixed/introduced `30`/`2`, harmful fixed/introduced `0`/`58`
- `context_selected_source_raw_window:selection_top_k2__a0__m0`: decisions changed `88`, false abstains fixed/introduced `29`/`2`, harmful fixed/introduced `0`/`57`
- `context_selected_source_raw_window:selection_top_k3__a0__m0`: decisions changed `88`, false abstains fixed/introduced `29`/`2`, harmful fixed/introduced `0`/`57`
- `context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0__m0`: decisions changed `87`, false abstains fixed/introduced `31`/`3`, harmful fixed/introduced `0`/`53`
- `context_selected_source_dependency_role:selection_top_k2__a0__m0`: decisions changed `87`, false abstains fixed/introduced `30`/`2`, harmful fixed/introduced `0`/`55`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | control:rows_max | context_conditioned_control_rows_max | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 2 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5751 | 0.3902 | 530.7439 |
| 3 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5751 | 0.3902 | 530.7439 |
| 4 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5806 | 0.3966 | 530.7439 |
| 5 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5806 | 0.3966 | 530.7439 |
| 6 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5693 | 0.3944 | 530.7439 |
| 7 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5693 | 0.3944 | 530.7439 |
| 8 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 54 | 52.63% | 0.5834 | 0.4069 | 540.7579 |
| 9 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 54 | 52.63% | 0.5901 | 0.4125 | 540.7579 |
| 10 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_05__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 54 | 52.63% | 0.5770 | 0.3862 | 540.7579 |
| 11 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_05__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 54 | 52.63% | 0.5770 | 0.3862 | 540.7579 |
| 12 | source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 54 | 52.63% | 0.5877 | 0.4109 | 540.7579 |
| 13 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5834 | 0.4069 | 550.7719 |
| 14 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5901 | 0.4125 | 550.7719 |
| 15 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5722 | 0.3978 | 550.7719 |
| 16 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5774 | 0.3909 | 550.7719 |
| 17 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5337 | 0.3551 | 550.7719 |
| 18 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5337 | 0.3551 | 550.7719 |
| 19 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5246 | 0.3525 | 550.7719 |
| 20 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5246 | 0.3525 | 550.7719 |

## Negative Controls

- `context_conditioned_negative_active_only`: `failed_as_expected` (over_replace; harmful `99`, false abstain `0`, accuracy `47.89%`)
- `context_conditioned_negative_target_lemma`: `failed_as_expected` (lexical_leakage; harmful `99`, false abstain `0`, accuracy `47.89%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0`: discovery objective `370.7651`, locked objective `160.6991`, worst leave-one-family objective `530.7551`
- `context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_05__m0_005`: discovery objective `370.7651`, locked objective `160.6991`, worst leave-one-family objective `530.7551`
- `context_conditioned_control_rows_max`: discovery objective `280.5790`, locked objective `170.7428`, worst leave-one-family objective `450.6523`
- `context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0`: discovery objective `360.7445`, locked objective `170.7428`, worst leave-one-family objective `530.7551`
- `context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0_005`: discovery objective `360.7445`, locked objective `170.7428`, worst leave-one-family objective `530.7551`
- `context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0`: discovery objective `360.7445`, locked objective `170.7428`, worst leave-one-family objective `530.7551`
- `context_selected_definition_source_before_after:selection_top_k3__top_k2__a0_05__m0_005`: discovery objective `360.7445`, locked objective `170.7428`, worst leave-one-family objective `530.7551`
- `context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_05__m0`: discovery objective `370.7651`, locked objective `170.7428`, worst leave-one-family objective `540.7694`
- `context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_05__m0_005`: discovery objective `370.7651`, locked objective `170.7428`, worst leave-one-family objective `540.7694`
- `context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0`: discovery objective `360.7445`, locked objective `180.7865`, worst leave-one-family objective `540.7694`
