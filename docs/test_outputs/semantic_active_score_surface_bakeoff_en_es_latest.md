# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T18:36:58Z`
- Matrix: `en_es_semantic_active_score_surface_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_active_score_surface_bakeoff_en_es.json`
- Evaluation suites: `4`
- Config rows: `171`
- Case score traces: `32490`
- Case traces included in JSON: `False`
- Negative-control sanity: `ok`

## Recommendation

Best promotable candidate is `surface_rows_max:a0_1__m0`; with harmful `0`; and false abstain `45`; against incumbent `surface_control_tfidf_masked_all`; and negative controls failed as expected.

## Best By Constraint

- incumbent_control: `surface_control_tfidf_masked_all`
  - Harmful / false abstain: `1` / `46`
  - Decision / winner accuracy: `75.26%` / `58.77%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `surface_rows_max:a0_1__m0`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `surface_rows_max:a0_1__m0`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_promotable_candidate: `surface_rows_max:a0_1__m0`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| rows:max | 12 | surface_rows_max:a0_1__m0 | surface_rows_max:a0_1__m0 | 0 | 45 | 60.53% | 450.6316 |
| rows:top_k_mean | 12 | surface_rows_topk:a0_05__m0 | surface_rows_topk:a0_05__m0 | 0 | 45 | 60.53% | 450.6316 |
| context:raw_window | 12 | surface_context_raw_window_all:a0_1__m0 | surface_context_raw_window_all:a0_1__m0 | 0 | 47 | 58.77% | 470.6596 |
| rows:source_weighted_top_k | 12 | surface_rows_source_weighted_topk:a0_05__m0 | surface_rows_source_weighted_topk:a0_05__m0 | 0 | 48 | 57.89% | 480.6737 |
| context:raw_sentence | 12 | surface_context_raw_sentence_all:a0_1__m0 | surface_context_raw_sentence_all:a0_1__m0 | 0 | 49 | 57.02% | 490.6877 |
| rows:mean | 12 | surface_rows_mean:a0_05__m0 | surface_rows_mean:a0_05__m0 | 0 | 52 | 54.39% | 520.7298 |
| evidence:sense_label | 12 | surface_evidence_sense_label:a0_05__m0 | surface_evidence_sense_label:a0_05__m0 | 0 | 53 | 53.51% | 530.7439 |
| evidence:sense_gloss_bundle | 12 | surface_evidence_sense_gloss_bundle:a0_05__m0 | surface_evidence_sense_gloss_bundle:a0_05__m0 | 0 | 54 | 52.63% | 540.7579 |
| scorer:token_jaccard | 12 | surface_scorer_token_jaccard:a0_1__m0 | surface_scorer_token_jaccard:a0_1__m0 | 0 | 54 | 52.63% | 540.7579 |
| context:masked_sentence | 12 | surface_context_masked_sentence_all:a0_1__m0 | surface_context_masked_sentence_all:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| context:masked_window | 12 | surface_context_masked_window_all:a0_1__m0 | surface_context_masked_window_all:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| evidence:all_evidence_text | 12 | surface_evidence_all:a0_1__m0 | surface_evidence_all:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| rows:definition_example_agreement | 12 | surface_rows_definition_example_agreement:a0_05__m0 | surface_rows_definition_example_agreement:a0_05__m0 | 0 | 56 | 50.88% | 560.7860 |
| evidence:gloss_text | 12 | surface_evidence_gloss:a0_1__m0 | surface_evidence_gloss:a0_1__m0 | 0 | 57 | 50.00% | 570.8000 |
| control:tfidf_masked_all | 1 | surface_control_tfidf_masked_all |  | 1 | 46 | 58.77% | 1460.6596 |
| scorer:sentence_transformer_cosine | 1 | surface_scorer_sentence_transformer_fixed |  | 6 | 15 | 85.96% | 6150.2509 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| surface_rows_max:a0_1__m0 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_max:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_rows_max:a0_1__m0_005 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_max:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_rows_max:a0_1__m0_02 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_max:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_max:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_rows_topk:a0_05__m0 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_topk:a0_05__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_rows_topk:a0_05__m0_005 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_topk:a0_05__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0_005 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_rows_topk:a0_05__m0_02 | frozen_v10 | 95 | 0 | 27 | 71.58% |
| surface_rows_topk:a0_05__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_rows_topk:a0_05__m0_02 | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| surface_context_raw_window_all:a0_1__m0 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| surface_context_raw_window_all:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_context_raw_window_all:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_context_raw_window_all:a0_1__m0 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| surface_context_raw_window_all:a0_1__m0_005 | frozen_v10 | 95 | 0 | 28 | 70.53% |
| surface_context_raw_window_all:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| surface_context_raw_window_all:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| surface_context_raw_window_all:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |

## Decision Signature Clusters

- Unique replace signatures: `69`
- Largest replace-signature cluster: `12` configs
- `25a2e7fcdd9d9477`: `12` configs, sample `surface_context_masked_sentence_all:a0_1__m0, surface_context_masked_sentence_all:a0_1__m0_005, surface_context_masked_sentence_all:a0_1__m0_02, surface_context_masked_window_all:a0_1__m0, surface_context_masked_window_all:a0_1__m0_005`
- `a87e241f0aff4c8b`: `9` configs, sample `surface_rows_mean:a0_1__m0, surface_rows_mean:a0_1__m0_005, surface_rows_mean:a0_1__m0_02, surface_rows_source_weighted_topk:a0_1__m0, surface_rows_source_weighted_topk:a0_1__m0_005`
- `b637f4024f2b6ab3`: `7` configs, sample `surface_context_masked_sentence_all:a0_05__m0, surface_context_masked_sentence_all:a0_05__m0_005, surface_context_masked_sentence_all:a0_05__m0_02, surface_control_tfidf_masked_all, surface_evidence_all:a0_05__m0`
- `903aff07f98c4590`: `6` configs, sample `surface_context_masked_sentence_all:a0__m0, surface_evidence_all:a0__m0, surface_rows_max:a0__m0, surface_rows_mean:a0__m0, surface_rows_source_weighted_topk:a0__m0`
- `c21c89eb6be04896`: `6` configs, sample `surface_rows_max:a0_1__m0, surface_rows_max:a0_1__m0_005, surface_rows_max:a0_1__m0_02, surface_rows_topk:a0_05__m0, surface_rows_topk:a0_05__m0_005`

## Headline Metric Ties

- Tied primary-metric groups: `40`
- Largest tied group: `15` configs
- `harm=0|false=55|decision=0.710526|winner=0.517544`: `15` configs, unique replace signatures `2`, ROC AUC `0.5594..0.6560`, Avg Prec. `0.4986..0.5790`
- `harm=0|false=56|decision=0.705263|winner=0.508772`: `12` configs, unique replace signatures `2`, ROC AUC `0.5319..0.6570`, Avg Prec. `0.4278..0.5861`
- `harm=1|false=46|decision=0.752632|winner=0.587719`: `7` configs, unique replace signatures `1`, ROC AUC `0.6560..0.6560`, Avg Prec. `0.5790..0.5790`
- `harm=0|false=54|decision=0.715789|winner=0.526316`: `6` configs, unique replace signatures `2`, ROC AUC `0.5594..0.6213`, Avg Prec. `0.5047..0.5333`
- `harm=0|false=45|decision=0.763158|winner=0.605263`: `6` configs, unique replace signatures `1`, ROC AUC `0.6570..0.6570`, Avg Prec. `0.5861..0.5861`
- `harm=0|false=57|decision=0.700000|winner=0.500000`: `6` configs, unique replace signatures `1`, ROC AUC `0.4552..0.5319`, Avg Prec. `0.3108..0.4278`
- `harm=80|false=4|decision=0.557895|winner=0.614035`: `6` configs, unique replace signatures `1`, ROC AUC `0.6554..0.6570`, Avg Prec. `0.5743..0.5861`
- `harm=1|false=50|decision=0.731579|winner=0.561404`: `5` configs, unique replace signatures `1`, ROC AUC `0.5594..0.5594`, Avg Prec. `0.5047..0.5047`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| evidence:sense_label | surface_evidence_sense_label:a0_05__m0 | 0 | 38 | 0 | 15 | 150.6554 | surface_evidence_sense_label:a0_02__m0 |
| context:raw_window | surface_context_raw_window_all:a0_1__m0 | 0 | 31 | 0 | 16 | 160.6991 | surface_context_raw_window_all:a0_1__m0 |
| context:raw_sentence | surface_context_raw_sentence_all:a0_1__m0 | 0 | 32 | 0 | 17 | 170.7428 | surface_context_raw_sentence_all:a0_1__m0 |
| evidence:sense_gloss_bundle | surface_evidence_sense_gloss_bundle:a0_05__m0 | 0 | 37 | 0 | 17 | 170.7428 | surface_evidence_sense_gloss_bundle:a0_02__m0 |
| rows:top_k_mean | surface_rows_topk:a0_05__m0 | 0 | 28 | 0 | 17 | 170.7428 | surface_rows_topk:a0_05__m0 |
| evidence:gloss_text | surface_evidence_gloss:a0_1__m0 | 0 | 39 | 0 | 18 | 180.7865 | surface_evidence_gloss:a0_1__m0 |
| rows:definition_example_agreement | surface_rows_definition_example_agreement:a0_05__m0 | 0 | 38 | 0 | 18 | 180.7865 | surface_rows_definition_example_agreement:a0_02__m0 |
| rows:mean | surface_rows_mean:a0_05__m0 | 0 | 34 | 0 | 18 | 180.7865 | surface_rows_mean:a0_05__m0 |
| rows:source_weighted_top_k | surface_rows_source_weighted_topk:a0_05__m0 | 0 | 30 | 0 | 18 | 180.7865 | surface_rows_source_weighted_topk:a0_05__m0 |
| scorer:token_jaccard | surface_scorer_token_jaccard:a0_1__m0 | 0 | 36 | 0 | 18 | 180.7865 | surface_scorer_token_jaccard:a0_1__m0 |
| context:masked_sentence | surface_context_masked_sentence_all:a0_05__m0 | 0 | 28 | 1 | 18 | 1180.8302 | surface_context_masked_sentence_all:a0_1__m0 |
| context:masked_window | surface_context_masked_window_all:a0_05__m0 | 0 | 29 | 1 | 18 | 1180.8302 | surface_context_masked_window_all:a0_1__m0 |
| control:tfidf_masked_all | surface_control_tfidf_masked_all | 0 | 28 | 1 | 18 | 1180.8302 | surface_control_tfidf_masked_all |
| evidence:all_evidence_text | surface_evidence_all:a0_05__m0 | 0 | 28 | 1 | 18 | 1180.8302 | surface_evidence_all:a0_1__m0 |
| rows:max | surface_rows_max:a0_05__m0_02 | 0 | 28 | 2 | 15 | 2150.7158 | surface_rows_max:a0_1__m0 |
| scorer:sentence_transformer_cosine | surface_scorer_sentence_transformer_fixed | 3 | 10 | 3 | 5 | 3050.2955 | surface_scorer_sentence_transformer_fixed |

## Incumbent Case Deltas

- Incumbent config: `surface_control_tfidf_masked_all`
- Configs identical to incumbent decisions: `6`
- `surface_evidence_sense_gloss_bundle:a0__m0`: decisions changed `140`, false abstains fixed/introduced `45`/`0`, harmful fixed/introduced `0`/`95`
- `surface_evidence_sense_label:a0__m0`: decisions changed `139`, false abstains fixed/introduced `46`/`0`, harmful fixed/introduced `0`/`93`
- `surface_rows_definition_example_agreement:a0__m0`: decisions changed `139`, false abstains fixed/introduced `46`/`0`, harmful fixed/introduced `0`/`93`
- `surface_evidence_gloss:a0__m0`: decisions changed `127`, false abstains fixed/introduced `39`/`2`, harmful fixed/introduced `0`/`86`
- `surface_context_masked_window_all:a0__m0`: decisions changed `124`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`82`
- `surface_scorer_token_jaccard:a0__m0`: decisions changed `121`, false abstains fixed/introduced `42`/`1`, harmful fixed/introduced `0`/`78`
- `surface_context_masked_sentence_all:a0__m0`: decisions changed `121`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`79`
- `surface_evidence_all:a0__m0`: decisions changed `121`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`79`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | rows:max | surface_rows_max:a0_1__m0 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 2 | rows:max | surface_rows_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 3 | rows:max | surface_rows_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 4 | rows:top_k_mean | surface_rows_topk:a0_05__m0 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 5 | rows:top_k_mean | surface_rows_topk:a0_05__m0_005 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 6 | rows:top_k_mean | surface_rows_topk:a0_05__m0_02 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 7 | context:raw_window | surface_context_raw_window_all:a0_1__m0 | tfidf_cosine | raw_window | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.6250 | 0.4872 | 470.6596 |
| 8 | context:raw_window | surface_context_raw_window_all:a0_1__m0_005 | tfidf_cosine | raw_window | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.6250 | 0.4872 | 470.6596 |
| 9 | context:raw_window | surface_context_raw_window_all:a0_1__m0_02 | tfidf_cosine | raw_window | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.6250 | 0.4872 | 470.6596 |
| 10 | rows:source_weighted_top_k | surface_rows_source_weighted_topk:a0_05__m0 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6554 | 0.5743 | 480.6737 |
| 11 | rows:source_weighted_top_k | surface_rows_source_weighted_topk:a0_05__m0_005 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6554 | 0.5743 | 480.6737 |
| 12 | rows:source_weighted_top_k | surface_rows_source_weighted_topk:a0_05__m0_02 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.6554 | 0.5743 | 480.6737 |
| 13 | context:raw_sentence | surface_context_raw_sentence_all:a0_1__m0 | tfidf_cosine | raw_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 49 | 57.02% | 0.6379 | 0.5045 | 490.6877 |
| 14 | context:raw_sentence | surface_context_raw_sentence_all:a0_1__m0_005 | tfidf_cosine | raw_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 49 | 57.02% | 0.6379 | 0.5045 | 490.6877 |
| 15 | context:raw_sentence | surface_context_raw_sentence_all:a0_1__m0_02 | tfidf_cosine | raw_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 49 | 57.02% | 0.6379 | 0.5045 | 490.6877 |
| 16 | rows:mean | surface_rows_mean:a0_05__m0 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | mean_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 52 | 54.39% | 0.6570 | 0.5861 | 520.7298 |
| 17 | rows:mean | surface_rows_mean:a0_05__m0_005 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | mean_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 52 | 54.39% | 0.6570 | 0.5861 | 520.7298 |
| 18 | rows:mean | surface_rows_mean:a0_05__m0_02 | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | mean_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 52 | 54.39% | 0.6570 | 0.5861 | 520.7298 |
| 19 | evidence:sense_label | surface_evidence_sense_label:a0_05__m0 | tfidf_cosine | masked_sentence | sense_label | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5660 | 0.4986 | 530.7439 |
| 20 | evidence:sense_label | surface_evidence_sense_label:a0_05__m0_005 | tfidf_cosine | masked_sentence | sense_label | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 53 | 53.51% | 0.5660 | 0.4986 | 530.7439 |

## Negative Controls

- `surface_negative_target_lemma_only`: `failed_as_expected` (lexical_leakage; harmful `99`, false abstain `0`, accuracy `47.89%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `surface_evidence_sense_label:a0_05__m0`: discovery objective `380.7858`, locked objective `150.6554`, worst leave-one-family objective `530.7683`
- `surface_evidence_sense_label:a0_05__m0_005`: discovery objective `380.7858`, locked objective `150.6554`, worst leave-one-family objective `530.7683`
- `surface_evidence_sense_label:a0_05__m0_02`: discovery objective `380.7858`, locked objective `150.6554`, worst leave-one-family objective `530.7683`
- `surface_evidence_sense_gloss_bundle:a0_02__m0`: discovery objective `1350.7315`, locked objective `150.6554`, worst leave-one-family objective `1500.7302`
- `surface_evidence_sense_gloss_bundle:a0_02__m0_005`: discovery objective `1350.7315`, locked objective `150.6554`, worst leave-one-family objective `1500.7302`
- `surface_evidence_sense_gloss_bundle:a0_02__m0_02`: discovery objective `1350.7315`, locked objective `150.6554`, worst leave-one-family objective `1500.7302`
- `surface_evidence_sense_gloss_bundle:a0__m0_005`: discovery objective `1350.7315`, locked objective `150.6554`, worst leave-one-family objective `1500.7302`
- `surface_evidence_sense_gloss_bundle:a0__m0_02`: discovery objective `1350.7315`, locked objective `150.6554`, worst leave-one-family objective `1500.7302`
- `surface_evidence_sense_label:a0_02__m0`: discovery objective `1360.7521`, locked objective `150.6554`, worst leave-one-family objective `1510.7447`
- `surface_evidence_sense_label:a0_02__m0_005`: discovery objective `1360.7521`, locked objective `150.6554`, worst leave-one-family objective `1510.7447`

## Source-Family Dropout

- `surface_rows_source_weighted_topk:a0__m0` drop `sense_label`: harmful `81`, false abstain `7`, objective `81070.8842`
- `surface_rows_source_weighted_topk:a0__m0` drop `definition`: harmful `86`, false abstain `0`, objective `86000.8474`
- `surface_rows_source_weighted_topk:a0__m0` drop `auxiliary`: harmful `86`, false abstain `6`, objective `86060.9404`
- `surface_rows_source_weighted_topk:a0__m0` drop `qualifier`: harmful `80`, false abstain `4`, objective `80040.8281`
- `surface_rows_source_weighted_topk:a0__m0` drop `target_lemma`: harmful `80`, false abstain `4`, objective `80040.8281`
- `surface_rows_source_weighted_topk:a0__m0_005` drop `sense_label`: harmful `15`, false abstain `39`, objective `15390.6877`
- `surface_rows_source_weighted_topk:a0__m0_005` drop `definition`: harmful `1`, false abstain `40`, objective `1400.5667`
- `surface_rows_source_weighted_topk:a0__m0_005` drop `auxiliary`: harmful `17`, false abstain `48`, objective `17480.8421`
- `surface_rows_source_weighted_topk:a0__m0_005` drop `qualifier`: harmful `15`, false abstain `38`, objective `15380.6737`
- `surface_rows_source_weighted_topk:a0__m0_005` drop `target_lemma`: harmful `15`, false abstain `38`, objective `15380.6737`
- `surface_rows_source_weighted_topk:a0__m0_02` drop `sense_label`: harmful `9`, false abstain `45`, objective `9450.7053`
- `surface_rows_source_weighted_topk:a0__m0_02` drop `definition`: harmful `1`, false abstain `40`, objective `1400.5667`
- `surface_rows_source_weighted_topk:a0__m0_02` drop `auxiliary`: harmful `5`, false abstain `54`, objective `5540.8105`
- `surface_rows_source_weighted_topk:a0__m0_02` drop `qualifier`: harmful `6`, false abstain `43`, objective `6430.6614`
- `surface_rows_source_weighted_topk:a0__m0_02` drop `target_lemma`: harmful `6`, false abstain `43`, objective `6430.6614`
- `surface_rows_source_weighted_topk:a0_02__m0` drop `sense_label`: harmful `10`, false abstain `43`, objective `10430.6912`
- `surface_rows_source_weighted_topk:a0_02__m0` drop `definition`: harmful `1`, false abstain `40`, objective `1400.5667`
- `surface_rows_source_weighted_topk:a0_02__m0` drop `auxiliary`: harmful `7`, false abstain `53`, objective `7530.8158`
- `surface_rows_source_weighted_topk:a0_02__m0` drop `qualifier`: harmful `8`, false abstain `41`, objective `8410.6526`
- `surface_rows_source_weighted_topk:a0_02__m0` drop `target_lemma`: harmful `8`, false abstain `41`, objective `8410.6526`
