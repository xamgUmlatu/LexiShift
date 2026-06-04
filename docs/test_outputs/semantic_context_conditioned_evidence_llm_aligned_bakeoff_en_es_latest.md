# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:04:33Z`
- Matrix: `en_es_semantic_context_conditioned_evidence_llm_aligned_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_context_conditioned_evidence_llm_aligned_bakeoff_en_es.json`
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
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v1-20260429a_cycle_sense_admitted_normalized_evidence.json | 123 | 123 | 5193f48b98027c64871fa826d4a04d1ed0e5945605da6ae26ecc19dd61d98a0f |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control:rows_max | 1 | context_conditioned_control_rows_max | context_conditioned_control_rows_max | 0 | 45 | 60.53% | 450.6316 |
| context_selected:before_after | 18 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:dependency_role | 18 | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:masked_sentence | 18 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:raw_window | 18 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:surface_frame | 18 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| source_rows:max | 12 | source_rows_max_tfidf:a0_1__m0 | source_rows_max_tfidf:a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected_definition_source:before_after | 24 | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_1__m0 | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_1__m0 | 0 | 53 | 53.51% | 530.7439 |
| context_selected_definition_source:surface_frame | 24 | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0 | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0 | 0 | 54 | 52.63% | 540.7579 |
| control:current_all | 1 | context_conditioned_control_current_all |  | 1 | 46 | 58.77% | 1460.6596 |
| source_plus_definition:max | 12 | source_plus_definition_rows_max_tfidf:a0_1__m0 |  | 1 | 47 | 57.89% | 1470.6737 |
| sentence_transformer:context_selected_before_after | 4 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |  | 8 | 19 | 79.82% | 8190.3439 |
| sentence_transformer:source_rows_max | 4 | sentence_transformer_source_rows_max:a0_1__m0_05 |  | 9 | 19 | 78.95% | 9190.3579 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| context_conditioned_control_rows_max | frozen_v10 | 95 | 0 | 27 | 71.58% |
| context_conditioned_control_rows_max | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |

## Decision Signature Clusters

- Unique replace signatures: `86`
- Largest replace-signature cluster: `28` configs
- `c468b43b03b6b2c9`: `28` configs, sample `context_selected_source_before_after:selection_top_k1__a0_1__m0, context_selected_source_before_after:selection_top_k1__a0_1__m0_005, context_selected_source_before_after:selection_top_k2__a0_1__m0, context_selected_source_before_after:selection_top_k2__a0_1__m0_005, context_selected_source_before_after:selection_top_k3__a0_1__m0`
- `658f27bdfedc1c9c`: `6` configs, sample `context_selected_source_masked_sentence:selection_top_k1__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k2__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k3__a0_05__m0_005, context_selected_source_surface_frame:selection_top_k3__a0_05__m0, context_selected_source_surface_frame:selection_top_k3__a0_05__m0_005`
- `e2f3ee4a42455dee`: `6` configs, sample `context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0, context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005, context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0, context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005, source_plus_definition_rows_max_tfidf:a0_1__m0`
- `fb6e5acb323b8f2f`: `5` configs, sample `context_selected_source_masked_sentence:selection_top_k1__a0__m0_005, context_selected_source_masked_sentence:selection_top_k2__a0__m0_005, context_selected_source_masked_sentence:selection_top_k3__a0__m0_005, context_selected_source_raw_window:selection_top_k3__a0__m0_005, source_rows_max_tfidf:a0__m0_005`
- `009aa3cbfd1f742d`: `4` configs, sample `context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0_005, context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_1__m0_005`

## Headline Metric Ties

- Tied primary-metric groups: `37`
- Largest tied group: `28` configs
- `harm=0|false=48|decision=0.747368|winner=0.578947`: `28` configs, unique replace signatures `1`, ROC AUC `0.6556..0.6957`, Avg Prec. `0.5102..0.5630`
- `harm=39|false=18|decision=0.700000|winner=0.657895`: `6` configs, unique replace signatures `3`, ROC AUC `0.6800..0.6957`, Avg Prec. `0.5387..0.5630`
- `harm=1|false=47|decision=0.747368|winner=0.578947`: `6` configs, unique replace signatures `1`, ROC AUC `0.6952..0.7082`, Avg Prec. `0.5564..0.5711`
- `harm=9|false=41|decision=0.736842|winner=0.596491`: `6` configs, unique replace signatures `1`, ROC AUC `0.6826..0.6855`, Avg Prec. `0.5452..0.5481`
- `harm=0|false=49|decision=0.742105|winner=0.570175`: `5` configs, unique replace signatures `2`, ROC AUC `0.6562..0.6855`, Avg Prec. `0.5226..0.5452`
- `harm=1|false=48|decision=0.742105|winner=0.570175`: `5` configs, unique replace signatures `2`, ROC AUC `0.6945..0.7033`, Avg Prec. `0.5506..0.5564`
- `harm=23|false=31|decision=0.715789|winner=0.614035`: `5` configs, unique replace signatures `1`, ROC AUC `0.6855..0.6944`, Avg Prec. `0.5452..0.5575`
- `harm=0|false=53|decision=0.721053|winner=0.535088`: `4` configs, unique replace signatures `1`, ROC AUC `0.6873..0.7043`, Avg Prec. `0.5380..0.5412`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_before_after:selection_top_k1__a0_05__m0 |
| context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 |
| context_selected:raw_window | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_raw_window:selection_top_k1__a0_05__m0 |
| context_selected:surface_frame | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 |
| source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0 | 1 | 32 | 0 | 15 | 150.6554 | source_plus_definition_rows_max_tfidf:a0_1__m0 |
| source_rows:max | source_rows_max_tfidf:a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | source_rows_max_tfidf:a0_1__m0 |
| context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 16 | 160.6991 | context_selected_source_dependency_role:selection_top_k3__a0_05__m0 |
| context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_1__m0 | 0 | 37 | 0 | 16 | 160.6991 | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 |
| context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0 | 0 | 38 | 0 | 16 | 160.6991 | context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0_1__m0 |
| control:rows_max | context_conditioned_control_rows_max | 0 | 28 | 0 | 17 | 170.7428 | context_conditioned_control_rows_max |
| sentence_transformer:source_rows_max | sentence_transformer_source_rows_max:a0_1__m0_05 | 8 | 15 | 1 | 4 | 1040.2185 | sentence_transformer_source_rows_max:a0_1__m0_05 |
| control:current_all | context_conditioned_control_current_all | 0 | 28 | 1 | 18 | 1180.8302 | context_conditioned_control_current_all |
| sentence_transformer:context_selected_before_after | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 | 6 | 14 | 2 | 5 | 2050.2788 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |

## Incumbent Case Deltas

- Incumbent config: `context_conditioned_control_current_all`
- Configs identical to incumbent decisions: `0`
- `context_selected_source_surface_frame:selection_top_k1__a0__m0`: decisions changed `81`, false abstains fixed/introduced `34`/`3`, harmful fixed/introduced `0`/`44`
- `context_selected_source_raw_window:selection_top_k1__a0__m0`: decisions changed `80`, false abstains fixed/introduced `32`/`3`, harmful fixed/introduced `0`/`45`
- `context_selected_source_dependency_role:selection_top_k1__a0__m0`: decisions changed `79`, false abstains fixed/introduced `32`/`1`, harmful fixed/introduced `0`/`46`
- `context_selected_source_surface_frame:selection_top_k2__a0__m0`: decisions changed `77`, false abstains fixed/introduced `33`/`3`, harmful fixed/introduced `0`/`41`
- `context_selected_source_before_after:selection_top_k1__a0__m0`: decisions changed `77`, false abstains fixed/introduced `32`/`3`, harmful fixed/introduced `0`/`42`
- `context_selected_source_dependency_role:selection_top_k2__a0__m0`: decisions changed `74`, false abstains fixed/introduced `31`/`2`, harmful fixed/introduced `0`/`41`
- `context_selected_source_surface_frame:selection_top_k3__a0__m0`: decisions changed `72`, false abstains fixed/introduced `32`/`3`, harmful fixed/introduced `0`/`37`
- `context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0__m0`: decisions changed `72`, false abstains fixed/introduced `32`/`2`, harmful fixed/introduced `0`/`38`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | control:rows_max | context_conditioned_control_rows_max | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 2 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6653 | 0.5228 | 480.6737 |
| 3 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6653 | 0.5228 | 480.6737 |
| 4 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6913 | 0.5579 | 480.6737 |
| 5 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6913 | 0.5579 | 480.6737 |
| 6 | context_selected:before_after | context_selected_source_before_after:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6912 | 0.5562 | 480.6737 |
| 7 | context_selected:before_after | context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6912 | 0.5562 | 480.6737 |
| 8 | context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6957 | 0.5630 | 480.6737 |
| 9 | context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6957 | 0.5630 | 480.6737 |
| 10 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 11 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 12 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 13 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 14 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 15 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6855 | 0.5452 | 480.6737 |
| 16 | context_selected:raw_window | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6556 | 0.5102 | 480.6737 |
| 17 | context_selected:raw_window | context_selected_source_raw_window:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6556 | 0.5102 | 480.6737 |
| 18 | context_selected:raw_window | context_selected_source_raw_window:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6800 | 0.5387 | 480.6737 |
| 19 | context_selected:raw_window | context_selected_source_raw_window:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6800 | 0.5387 | 480.6737 |
| 20 | context_selected:raw_window | context_selected_source_raw_window:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6944 | 0.5575 | 480.6737 |

## Negative Controls

- `context_conditioned_negative_active_only`: `failed_as_expected` (over_replace; harmful `99`, false abstain `0`, accuracy `47.89%`)
- `context_conditioned_negative_target_lemma`: `failed_as_expected` (lexical_leakage; harmful `99`, false abstain `0`, accuracy `47.89%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `context_selected_source_before_after:selection_top_k2__a0_05__m0_005`: discovery objective `6290.6978`, locked objective `120.5243`, worst leave-one-family objective `6410.6631`
- `context_selected_source_raw_window:selection_top_k2__a0_05__m0_005`: discovery objective `6300.7185`, locked objective `120.5243`, worst leave-one-family objective `6420.6776`
- `context_selected_source_raw_window:selection_top_k1__a0_05__m0`: discovery objective `6320.7469`, locked objective `120.5243`, worst leave-one-family objective `6440.6975`
- `context_selected_source_raw_window:selection_top_k1__a0_05__m0_005`: discovery objective `6320.7469`, locked objective `120.5243`, worst leave-one-family objective `6440.6975`
- `context_selected_source_dependency_role:selection_top_k3__a0_05__m0`: discovery objective `7290.6925`, locked objective `120.5243`, worst leave-one-family objective `7410.6595`
- `context_selected_source_dependency_role:selection_top_k3__a0_05__m0_005`: discovery objective `7290.6925`, locked objective `120.5243`, worst leave-one-family objective `7410.6595`
- `context_selected_source_before_after:selection_top_k2__a0_05__m0`: discovery objective `7290.7055`, locked objective `120.5243`, worst leave-one-family objective `7410.6686`
- `context_selected_source_raw_window:selection_top_k2__a0_05__m0`: discovery objective `7300.7262`, locked objective `120.5243`, worst leave-one-family objective `7420.6830`
- `context_selected_source_before_after:selection_top_k1__a0_05__m0`: discovery objective `7310.7469`, locked objective `120.5243`, worst leave-one-family objective `7430.6975`
- `context_selected_source_before_after:selection_top_k1__a0_05__m0_005`: discovery objective `7310.7469`, locked objective `120.5243`, worst leave-one-family objective `7430.6975`
