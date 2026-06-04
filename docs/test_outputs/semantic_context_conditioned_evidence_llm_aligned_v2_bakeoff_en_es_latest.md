# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:10:30Z`
- Matrix: `en_es_semantic_context_conditioned_evidence_llm_aligned_bakeoff_v2`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_context_conditioned_evidence_llm_aligned_v2_bakeoff_en_es.json`
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
| /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json | 126 | 126 | efd217419778dae331058696abb2accb2d7901cafdb097f3322083f58465576c |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control:rows_max | 1 | context_conditioned_control_rows_max | context_conditioned_control_rows_max | 0 | 45 | 60.53% | 450.6316 |
| context_selected_definition_source:before_after | 24 | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | 0 | 47 | 58.77% | 470.6596 |
| source_plus_definition:max | 12 | source_plus_definition_rows_max_tfidf:a0_1__m0 | source_plus_definition_rows_max_tfidf:a0_1__m0 | 0 | 47 | 58.77% | 470.6596 |
| context_selected:before_after | 18 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:dependency_role | 18 | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:masked_sentence | 18 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:raw_window | 18 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected:surface_frame | 18 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| context_selected_definition_source:surface_frame | 24 | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| source_rows:max | 12 | source_rows_max_tfidf:a0_1__m0 | source_rows_max_tfidf:a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| control:current_all | 1 | context_conditioned_control_current_all |  | 1 | 46 | 58.77% | 1460.6596 |
| sentence_transformer:context_selected_before_after | 4 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |  | 9 | 20 | 78.07% | 9200.3719 |
| sentence_transformer:source_rows_max | 4 | sentence_transformer_source_rows_max:a0_1__m0_05 |  | 9 | 20 | 78.07% | 9200.3719 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| context_conditioned_control_rows_max | frozen_v10 | 95 | 0 | 27 | 71.58% |
| context_conditioned_control_rows_max | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_conditioned_control_rows_max | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| source_plus_definition_rows_max_tfidf:a0_1__m0 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| source_plus_definition_rows_max_tfidf:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| source_plus_definition_rows_max_tfidf:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| source_plus_definition_rows_max_tfidf:a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| source_plus_definition_rows_max_tfidf:a0_1__m0_005 | frozen_v10 | 95 | 0 | 32 | 66.32% |
| source_plus_definition_rows_max_tfidf:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| source_plus_definition_rows_max_tfidf:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| source_plus_definition_rows_max_tfidf:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | frozen_v10 | 95 | 0 | 33 | 65.26% |
| context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |

## Decision Signature Clusters

- Unique replace signatures: `85`
- Largest replace-signature cluster: `30` configs
- `c468b43b03b6b2c9`: `30` configs, sample `context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0_005, context_selected_source_before_after:selection_top_k1__a0_1__m0, context_selected_source_before_after:selection_top_k1__a0_1__m0_005, context_selected_source_before_after:selection_top_k2__a0_1__m0`
- `ae1c70731b2a8762`: `8` configs, sample `context_selected_source_before_after:selection_top_k3__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k1__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k2__a0_05__m0_005, context_selected_source_masked_sentence:selection_top_k3__a0_05__m0_005, context_selected_source_raw_window:selection_top_k3__a0_05__m0_005`
- `0343bb3927f6429a`: `6` configs, sample `context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0, context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005, context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0, context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005, source_plus_definition_rows_max_tfidf:a0_1__m0`
- `07373689d7b389ef`: `6` configs, sample `context_selected_source_before_after:selection_top_k3__a0_05__m0, context_selected_source_masked_sentence:selection_top_k1__a0_05__m0, context_selected_source_masked_sentence:selection_top_k2__a0_05__m0, context_selected_source_masked_sentence:selection_top_k3__a0_05__m0, context_selected_source_raw_window:selection_top_k3__a0_05__m0`
- `009aa3cbfd1f742d`: `4` configs, sample `context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k2__top_k2__a0_1__m0_005, context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_1__m0, context_selected_definition_source_surface_frame:selection_top_k3__top_k2__a0_1__m0_005`

## Headline Metric Ties

- Tied primary-metric groups: `33`
- Largest tied group: `31` configs
- `harm=0|false=48|decision=0.747368|winner=0.578947`: `31` configs, unique replace signatures `2`, ROC AUC `0.6729..0.7156`, Avg Prec. `0.5289..0.5794`
- `harm=7|false=41|decision=0.747368|winner=0.614035`: `8` configs, unique replace signatures `1`, ROC AUC `0.7010..0.7113`, Avg Prec. `0.5590..0.5704`
- `harm=0|false=47|decision=0.752632|winner=0.587719`: `6` configs, unique replace signatures `1`, ROC AUC `0.7136..0.7234`, Avg Prec. `0.5746..0.5820`
- `harm=8|false=41|decision=0.742105|winner=0.614035`: `6` configs, unique replace signatures `1`, ROC AUC `0.7037..0.7113`, Avg Prec. `0.5590..0.5704`
- `harm=0|false=49|decision=0.742105|winner=0.570175`: `5` configs, unique replace signatures `2`, ROC AUC `0.6665..0.7037`, Avg Prec. `0.5321..0.5590`
- `harm=9|false=20|decision=0.847368|winner=0.780702`: `4` configs, unique replace signatures `2`, ROC AUC `0.8587..0.8635`, Avg Prec. `0.6885..0.7205`
- `harm=0|false=53|decision=0.721053|winner=0.535088`: `4` configs, unique replace signatures `1`, ROC AUC `0.7120..0.7254`, Avg Prec. `0.5549..0.5619`
- `harm=0|false=54|decision=0.715789|winner=0.526316`: `4` configs, unique replace signatures `1`, ROC AUC `0.7197..0.7204`, Avg Prec. `0.5492..0.5597`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_before_after:selection_top_k1__a0_05__m0 |
| context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_masked_sentence:selection_top_k1__a0_05__m0 |
| context_selected:raw_window | context_selected_source_raw_window:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_raw_window:selection_top_k1__a0_05__m0 |
| context_selected:surface_frame | context_selected_source_surface_frame:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_source_surface_frame:selection_top_k3__a0_05__m0 |
| context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0_1__m0 |
| source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0 | 0 | 32 | 0 | 15 | 150.6554 | source_plus_definition_rows_max_tfidf:a0_1__m0 |
| source_rows:max | source_rows_max_tfidf:a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | source_rows_max_tfidf:a0_05__m0 |
| context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k1__a0_1__m0 | 0 | 33 | 0 | 16 | 160.6991 | context_selected_source_dependency_role:selection_top_k3__a0_05__m0 |
| control:rows_max | context_conditioned_control_rows_max | 0 | 28 | 0 | 17 | 170.7428 | context_conditioned_control_rows_max |
| sentence_transformer:source_rows_max | sentence_transformer_source_rows_max:a0_1__m0_05 | 8 | 15 | 1 | 5 | 1050.2622 | sentence_transformer_source_rows_max:a0_1__m0_05 |
| context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k2__a0_05__m0 | 0 | 30 | 1 | 13 | 1130.6117 | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 |
| control:current_all | context_conditioned_control_current_all | 0 | 28 | 1 | 18 | 1180.8302 | context_conditioned_control_current_all |
| sentence_transformer:context_selected_before_after | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 | 7 | 14 | 2 | 6 | 2060.3225 | sentence_transformer_context_selected_source_before_after:a0_1__m0_05 |

## Incumbent Case Deltas

- Incumbent config: `context_conditioned_control_current_all`
- Configs identical to incumbent decisions: `0`
- `context_selected_source_surface_frame:selection_top_k1__a0__m0`: decisions changed `79`, false abstains fixed/introduced `34`/`3`, harmful fixed/introduced `0`/`42`
- `context_selected_source_dependency_role:selection_top_k1__a0__m0`: decisions changed `78`, false abstains fixed/introduced `32`/`1`, harmful fixed/introduced `0`/`45`
- `context_selected_source_raw_window:selection_top_k1__a0__m0`: decisions changed `77`, false abstains fixed/introduced `32`/`3`, harmful fixed/introduced `0`/`42`
- `context_selected_source_before_after:selection_top_k1__a0__m0`: decisions changed `76`, false abstains fixed/introduced `32`/`3`, harmful fixed/introduced `0`/`41`
- `context_selected_source_surface_frame:selection_top_k2__a0__m0`: decisions changed `74`, false abstains fixed/introduced `33`/`3`, harmful fixed/introduced `0`/`38`
- `context_selected_source_dependency_role:selection_top_k2__a0__m0`: decisions changed `71`, false abstains fixed/introduced `30`/`2`, harmful fixed/introduced `0`/`39`
- `context_selected_definition_source_surface_frame:selection_top_k2__top_k1__a0__m0`: decisions changed `69`, false abstains fixed/introduced `32`/`2`, harmful fixed/introduced `0`/`35`
- `context_selected_source_raw_window:selection_top_k2__a0__m0`: decisions changed `69`, false abstains fixed/introduced `31`/`3`, harmful fixed/introduced `0`/`35`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | control:rows_max | context_conditioned_control_rows_max | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 2 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7136 | 0.5786 | 470.6596 |
| 3 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k2__top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7136 | 0.5786 | 470.6596 |
| 4 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7234 | 0.5820 | 470.6596 |
| 5 | context_selected_definition_source:before_after | context_selected_definition_source_before_after:selection_top_k3__top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7234 | 0.5820 | 470.6596 |
| 6 | source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7156 | 0.5746 | 470.6596 |
| 7 | source_plus_definition:max | source_plus_definition_rows_max_tfidf:a0_1__m0_005 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7156 | 0.5746 | 470.6596 |
| 8 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7109 | 0.5640 | 480.6737 |
| 9 | context_selected_definition_source:surface_frame | context_selected_definition_source_surface_frame:selection_top_k3__top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7109 | 0.5640 | 480.6737 |
| 10 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6739 | 0.5318 | 480.6737 |
| 11 | context_selected:before_after | context_selected_source_before_after:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6739 | 0.5318 | 480.6737 |
| 12 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7097 | 0.5712 | 480.6737 |
| 13 | context_selected:before_after | context_selected_source_before_after:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7097 | 0.5712 | 480.6737 |
| 14 | context_selected:before_after | context_selected_source_before_after:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7102 | 0.5695 | 480.6737 |
| 15 | context_selected:before_after | context_selected_source_before_after:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7102 | 0.5695 | 480.6737 |
| 16 | context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7151 | 0.5794 | 480.6737 |
| 17 | context_selected:dependency_role | context_selected_source_dependency_role:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7151 | 0.5794 | 480.6737 |
| 18 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7037 | 0.5590 | 480.6737 |
| 19 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k1__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7037 | 0.5590 | 480.6737 |
| 20 | context_selected:masked_sentence | context_selected_source_masked_sentence:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_rows | context_selected_max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7037 | 0.5590 | 480.6737 |

## Negative Controls

- `context_conditioned_negative_active_only`: `failed_as_expected` (over_replace; harmful `99`, false abstain `0`, accuracy `47.89%`)
- `context_conditioned_negative_target_lemma`: `failed_as_expected` (lexical_leakage; harmful `99`, false abstain `0`, accuracy `47.89%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `context_selected_source_raw_window:selection_top_k2__a0_05__m0_005`: discovery objective `4300.6771`, locked objective `120.5243`, worst leave-one-family objective `4420.6486`
- `context_selected_source_before_after:selection_top_k2__a0_05__m0_005`: discovery objective `5290.6771`, locked objective `120.5243`, worst leave-one-family objective `5410.6486`
- `context_selected_source_raw_window:selection_top_k2__a0_05__m0`: discovery objective `5300.6848`, locked objective `120.5243`, worst leave-one-family objective `5420.6541`
- `context_selected_source_raw_window:selection_top_k1__a0_05__m0`: discovery objective `5320.7262`, locked objective `120.5243`, worst leave-one-family objective `5440.6830`
- `context_selected_source_raw_window:selection_top_k1__a0_05__m0_005`: discovery objective `5320.7262`, locked objective `120.5243`, worst leave-one-family objective `5440.6830`
- `context_selected_source_dependency_role:selection_top_k3__a0_05__m0`: discovery objective `6290.6718`, locked objective `120.5243`, worst leave-one-family objective `6410.6450`
- `context_selected_source_dependency_role:selection_top_k3__a0_05__m0_005`: discovery objective `6290.6718`, locked objective `120.5243`, worst leave-one-family objective `6410.6450`
- `context_selected_source_before_after:selection_top_k2__a0_05__m0`: discovery objective `6290.6848`, locked objective `120.5243`, worst leave-one-family objective `6410.6541`
- `context_selected_source_before_after:selection_top_k3__a0_05__m0_005`: discovery objective `7290.6925`, locked objective `120.5243`, worst leave-one-family objective `7410.6595`
- `context_selected_source_masked_sentence:selection_top_k1__a0_05__m0_005`: discovery objective `7290.6925`, locked objective `120.5243`, worst leave-one-family objective `7410.6595`
