# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:58:03Z`
- Matrix: `en_es_semantic_sentence_transformer_row_level_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_sentence_transformer_row_level_bakeoff_en_es.json`
- Evaluation suites: `4`
- Config rows: `77`
- Case score traces: `14630`
- Case traces included in JSON: `False`
- Negative-control sanity: `ok`

## Recommendation

No candidate cleared the incumbent-aware promotability screen; treat the matrix as evidence for source coverage or representation work before policy promotion.

## Best By Constraint

- incumbent_control: `st_definition_example_row_control:a0_35__m0_08`
  - Harmful / false abstain: `1` / `31`
  - Decision / winner accuracy: `83.16%` / `71.93%`
  - Shape: `sentence_transformer_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`
  - Source scope: `no_source` (`0` attached rows)

- best_overall: `st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1`
  - Harmful / false abstain: `1` / `31`
  - Decision / winner accuracy: `83.16%` / `71.93%`
  - Shape: `sentence_transformer_cosine:masked_sentence:definition_example_plus_source_rows_separate:top_k_mean:active_minus_strongest_shadow:phrase_override`
  - Source scope: `llm_v2_plus_wordnet_reference` (`259` attached rows)

## Source Evidence Scopes

| Scope | Paths | Attached Rows | Mask | Window |
| ---: | --- | ---: | --- | ---: |
| 1 |  | 0 | ___ | 4 |
| 2 | /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json<br>/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json | 259 | ___ | 4 |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| st_combined:definition_example_plus_source:top_k_mean | 12 | st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 |  | 1 | 31 | 71.93% | 1310.4491 |
| st_control:definition_example_rows:max | 15 | st_definition_example_row_control:a0_35__m0_08 |  | 1 | 31 | 71.93% | 1310.4491 |
| st_combined:definition_example_plus_source:source_weighted_top_k | 12 | st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 |  | 1 | 33 | 70.18% | 1330.4772 |
| st_combined:source_plus_definition:max | 9 | st_combined_source_plus_definition_max:a0_35__m0_1 |  | 2 | 34 | 69.30% | 2340.4965 |
| st_combined:definition_example_plus_source:max | 15 | st_combined_definition_example_plus_source_max:a0_35__m0_12 |  | 2 | 35 | 68.42% | 2350.5105 |
| st_combined:source_rows:max | 9 | st_combined_source_rows_max:a0_35__m0_1 |  | 2 | 35 | 68.42% | 2350.5105 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | frozen_v10 | 95 | 0 | 23 | 75.79% |
| st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | source_heldout_v2 | 38 | 1 | 8 | 76.32% |
| st_combined_definition_example_plus_source_topk:top_k3__a0__m0_1 | frozen_v10 | 95 | 0 | 23 | 75.79% |
| st_combined_definition_example_plus_source_topk:top_k3__a0__m0_1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k3__a0__m0_1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k3__a0__m0_1 | source_heldout_v2 | 38 | 1 | 8 | 76.32% |
| st_definition_example_row_control:a0_35__m0_08 | frozen_v10 | 95 | 0 | 20 | 78.95% |
| st_definition_example_row_control:a0_35__m0_08 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0_35__m0_08 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0_35__m0_08 | source_heldout_v2 | 38 | 1 | 11 | 68.42% |
| st_definition_example_row_control:a0_5__m0_08 | frozen_v10 | 95 | 0 | 20 | 78.95% |
| st_definition_example_row_control:a0_5__m0_08 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0_5__m0_08 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0_5__m0_08 | source_heldout_v2 | 38 | 1 | 11 | 68.42% |
| st_definition_example_row_control:a0__m0_08 | frozen_v10 | 95 | 0 | 20 | 78.95% |
| st_definition_example_row_control:a0__m0_08 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0__m0_08 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_definition_example_row_control:a0__m0_08 | source_heldout_v2 | 38 | 1 | 11 | 68.42% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | frozen_v10 | 95 | 0 | 24 | 74.74% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | source_heldout_v2 | 38 | 1 | 9 | 73.68% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0__m0_1 | frozen_v10 | 95 | 0 | 24 | 74.74% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0__m0_1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0__m0_1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_weighted_topk:top_k3__a0__m0_1 | source_heldout_v2 | 38 | 1 | 9 | 73.68% |
| st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1 | source_heldout_v2 | 38 | 1 | 9 | 73.68% |

## Decision Signature Clusters

- Unique replace signatures: `25`
- Largest replace-signature cluster: `6` configs
- `2dfaa3eeca7f10ed`: `6` configs, sample `st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0, st_combined_definition_example_plus_source_topk:top_k2__a0__m0, st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0, st_combined_definition_example_plus_source_topk:top_k3__a0__m0, st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0`
- `252c6f835487e2a0`: `4` configs, sample `st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1, st_combined_definition_example_plus_source_topk:top_k2__a0__m0_1, st_combined_definition_example_plus_source_weighted_topk:top_k2__a0_35__m0_1, st_combined_definition_example_plus_source_weighted_topk:top_k2__a0__m0_1`
- `114ae31e93a6c3e8`: `3` configs, sample `st_combined_definition_example_plus_source_max:a0_35__m0_08, st_combined_definition_example_plus_source_max:a0_5__m0_08, st_combined_definition_example_plus_source_max:a0__m0_08`
- `1323566590598bce`: `3` configs, sample `st_combined_definition_example_plus_source_max:a0_35__m0_02, st_combined_definition_example_plus_source_max:a0_5__m0_02, st_combined_definition_example_plus_source_max:a0__m0_02`
- `18423f1b0e9c9c1e`: `3` configs, sample `st_combined_definition_example_plus_source_max:a0_35__m0_12, st_combined_definition_example_plus_source_max:a0_5__m0_12, st_combined_definition_example_plus_source_max:a0__m0_12`

## Headline Metric Ties

- Tied primary-metric groups: `21`
- Largest tied group: `7` configs
- `harm=4|false=21|decision=0.868421|winner=0.798246`: `7` configs, unique replace signatures `3`, ROC AUC `0.8900..0.9011`, Avg Prec. `0.7963..0.8069`
- `harm=2|false=35|decision=0.805263|winner=0.684211`: `6` configs, unique replace signatures `2`, ROC AUC `0.8660..0.8900`, Avg Prec. `0.7308..0.8001`
- `harm=11|false=8|decision=0.900000|winner=0.885965`: `6` configs, unique replace signatures `1`, ROC AUC `0.8983..0.9011`, Avg Prec. `0.7963..0.8069`
- `harm=1|false=31|decision=0.831579|winner=0.719298`: `5` configs, unique replace signatures `2`, ROC AUC `0.8839..0.8983`, Avg Prec. `0.8015..0.8022`
- `harm=1|false=34|decision=0.815789|winner=0.692982`: `4` configs, unique replace signatures `1`, ROC AUC `0.9008..0.9011`, Avg Prec. `0.8034..0.8069`
- `harm=11|false=10|decision=0.889474|winner=0.868421`: `3` configs, unique replace signatures `1`, ROC AUC `0.8900..0.8900`, Avg Prec. `0.8001..0.8001`
- `harm=11|false=7|decision=0.905263|winner=0.894737`: `3` configs, unique replace signatures `1`, ROC AUC `0.8904..0.8904`, Avg Prec. `0.7642..0.7642`
- `harm=14|false=9|decision=0.878947|winner=0.868421`: `3` configs, unique replace signatures `1`, ROC AUC `0.8660..0.8660`, Avg Prec. `0.7308..0.7308`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| st_combined:definition_example_plus_source:top_k_mean | st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | 0 | 22 | 1 | 9 | 1090.4369 | st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_05 |
| st_combined:definition_example_plus_source:source_weighted_top_k | st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | 0 | 23 | 1 | 10 | 1100.4806 | st_combined_definition_example_plus_source_weighted_topk:top_k2__a0_35__m0_05 |
| st_combined:source_plus_definition:max | st_combined_source_plus_definition_max:a0_35__m0_1 | 1 | 24 | 1 | 10 | 1100.4806 | st_combined_source_plus_definition_max:a0_35__m0_05 |
| st_combined:source_rows:max | st_combined_source_rows_max:a0_35__m0_1 | 1 | 25 | 1 | 10 | 1100.4806 | st_combined_source_rows_max:a0_35__m0_05 |
| st_combined:definition_example_plus_source:max | st_combined_definition_example_plus_source_max:a0_35__m0_12 | 1 | 23 | 1 | 12 | 1120.5680 | st_combined_definition_example_plus_source_max:a0_35__m0_02 |
| st_control:definition_example_rows:max | st_definition_example_row_control:a0_35__m0_08 | 0 | 19 | 1 | 12 | 1120.5680 | st_definition_example_row_control:a0_35__m0_05 |

## Incumbent Case Deltas

- Incumbent config: `st_definition_example_row_control:a0_35__m0_08`
- Configs identical to incumbent decisions: `2`
- `st_combined_source_rows_max:a0_35__m0`: decisions changed `37`, false abstains fixed/introduced `23`/`1`, harmful fixed/introduced `0`/`13`
- `st_combined_source_rows_max:a0_5__m0`: decisions changed `37`, false abstains fixed/introduced `23`/`1`, harmful fixed/introduced `0`/`13`
- `st_combined_source_rows_max:a0__m0`: decisions changed `37`, false abstains fixed/introduced `23`/`1`, harmful fixed/introduced `0`/`13`
- `st_combined_source_plus_definition_max:a0_35__m0`: decisions changed `34`, false abstains fixed/introduced `24`/`0`, harmful fixed/introduced `0`/`10`
- `st_combined_source_plus_definition_max:a0_5__m0`: decisions changed `34`, false abstains fixed/introduced `24`/`0`, harmful fixed/introduced `0`/`10`
- `st_combined_source_plus_definition_max:a0__m0`: decisions changed `34`, false abstains fixed/introduced `24`/`0`, harmful fixed/introduced `0`/`10`
- `st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0`: decisions changed `33`, false abstains fixed/introduced `23`/`0`, harmful fixed/introduced `0`/`10`
- `st_combined_definition_example_plus_source_topk:top_k2__a0__m0`: decisions changed `33`, false abstains fixed/introduced `23`/`0`, harmful fixed/introduced `0`/`10`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | st_combined:definition_example_plus_source:top_k_mean | st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 1 | 31 | 71.93% | 0.8983 | 0.8022 | 1310.4491 |
| 2 | st_combined:definition_example_plus_source:top_k_mean | st_combined_definition_example_plus_source_topk:top_k3__a0__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 1 | 31 | 71.93% | 0.8983 | 0.8022 | 1310.4491 |
| 3 | st_control:definition_example_rows:max | st_definition_example_row_control:a0_35__m0_08 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 31 | 71.93% | 0.8839 | 0.8015 | 1310.4491 |
| 4 | st_control:definition_example_rows:max | st_definition_example_row_control:a0_5__m0_08 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 31 | 71.93% | 0.8839 | 0.8015 | 1310.4491 |
| 5 | st_control:definition_example_rows:max | st_definition_example_row_control:a0__m0_08 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 31 | 71.93% | 0.8839 | 0.8015 | 1310.4491 |
| 6 | st_combined:definition_example_plus_source:source_weighted_top_k | st_combined_definition_example_plus_source_weighted_topk:top_k3__a0_35__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 1 | 33 | 70.18% | 0.8991 | 0.7963 | 1330.4772 |
| 7 | st_combined:definition_example_plus_source:source_weighted_top_k | st_combined_definition_example_plus_source_weighted_topk:top_k3__a0__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 1 | 33 | 70.18% | 0.8991 | 0.7963 | 1330.4772 |
| 8 | st_combined:definition_example_plus_source:top_k_mean | st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 1 | 34 | 69.30% | 0.9011 | 0.8069 | 1340.4912 |
| 9 | st_combined:definition_example_plus_source:top_k_mean | st_combined_definition_example_plus_source_topk:top_k2__a0__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 1 | 34 | 69.30% | 0.9011 | 0.8069 | 1340.4912 |
| 10 | st_combined:definition_example_plus_source:source_weighted_top_k | st_combined_definition_example_plus_source_weighted_topk:top_k2__a0_35__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 1 | 34 | 69.30% | 0.9008 | 0.8034 | 1340.4912 |
| 11 | st_combined:definition_example_plus_source:source_weighted_top_k | st_combined_definition_example_plus_source_weighted_topk:top_k2__a0__m0_1 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 1 | 34 | 69.30% | 0.9008 | 0.8034 | 1340.4912 |
| 12 | st_control:definition_example_rows:max | st_definition_example_row_control:a0_35__m0_12 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 38 | 65.79% | 0.8839 | 0.8015 | 1380.5474 |
| 13 | st_control:definition_example_rows:max | st_definition_example_row_control:a0_5__m0_12 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 38 | 65.79% | 0.8839 | 0.8015 | 1380.5474 |
| 14 | st_control:definition_example_rows:max | st_definition_example_row_control:a0__m0_12 | sentence_transformer_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 1 | 38 | 65.79% | 0.8839 | 0.8015 | 1380.5474 |
| 15 | st_combined:source_plus_definition:max | st_combined_source_plus_definition_max:a0_35__m0_1 | sentence_transformer_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 34 | 69.30% | 0.8904 | 0.7642 | 2340.4965 |
| 16 | st_combined:source_plus_definition:max | st_combined_source_plus_definition_max:a0_5__m0_1 | sentence_transformer_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 34 | 69.30% | 0.8904 | 0.7642 | 2340.4965 |
| 17 | st_combined:source_plus_definition:max | st_combined_source_plus_definition_max:a0__m0_1 | sentence_transformer_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 34 | 69.30% | 0.8904 | 0.7642 | 2340.4965 |
| 18 | st_combined:definition_example_plus_source:max | st_combined_definition_example_plus_source_max:a0_35__m0_12 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 35 | 68.42% | 0.8900 | 0.8001 | 2350.5105 |
| 19 | st_combined:definition_example_plus_source:max | st_combined_definition_example_plus_source_max:a0_5__m0_12 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 35 | 68.42% | 0.8900 | 0.8001 | 2350.5105 |
| 20 | st_combined:definition_example_plus_source:max | st_combined_definition_example_plus_source_max:a0__m0_12 | sentence_transformer_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 2 | 35 | 68.42% | 0.8900 | 0.8001 | 2350.5105 |

## Negative Controls

- `st_negative_target_lemma_only_additive_source`: `failed_as_expected` (lexical_leakage; harmful `2`, false abstain `40`, accuracy `77.89%`)
- `st_negative_shadow_only_additive_source`: `failed_as_expected` (over_abstain; harmful `4`, false abstain `26`, accuracy `84.21%`)
- `st_negative_shuffled_labels_additive_source`: `failed_as_expected` (collapse; harmful `64`, false abstain `54`, accuracy `37.89%`)
- `st_negative_active_only_additive_source`: `failed_as_expected` (over_replace; harmful `99`, false abstain `0`, accuracy `47.89%`)
- `st_negative_no_shadow_additive_source`: `failed_as_expected` (over_replace; harmful `99`, false abstain `0`, accuracy `47.89%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `st_negative_target_lemma_only_additive_source`: discovery objective `2260.5660`, locked objective `140.6117`, worst leave-one-family objective `2400.5998`
- `st_combined_definition_example_plus_source_max:a0_35__m0_02`: discovery objective `6100.2919`, locked objective `1020.1311`, worst leave-one-family objective `7120.2482`
- `st_combined_definition_example_plus_source_max:a0_5__m0_02`: discovery objective `6100.2919`, locked objective `1020.1311`, worst leave-one-family objective `7120.2482`
- `st_combined_definition_example_plus_source_max:a0__m0_02`: discovery objective `6100.2919`, locked objective `1020.1311`, worst leave-one-family objective `7120.2482`
- `st_combined_definition_example_plus_source_topk:top_k3__a0_35__m0_05`: discovery objective `2180.4006`, locked objective `1040.2185`, worst leave-one-family objective `3220.3533`
- `st_combined_definition_example_plus_source_topk:top_k3__a0__m0_05`: discovery objective `2180.4006`, locked objective `1040.2185`, worst leave-one-family objective `3220.3533`
- `st_combined_definition_example_plus_source_weighted_topk:top_k2__a0_35__m0_05`: discovery objective `3160.3669`, locked objective `1040.2185`, worst leave-one-family objective `4200.3297`
- `st_combined_definition_example_plus_source_weighted_topk:top_k2__a0__m0_05`: discovery objective `3160.3669`, locked objective `1040.2185`, worst leave-one-family objective `4200.3297`
- `st_combined_definition_example_plus_source_topk:top_k2__a0_35__m0_05`: discovery objective `3170.3876`, locked objective `1040.2185`, worst leave-one-family objective `4210.3442`
- `st_combined_definition_example_plus_source_topk:top_k2__a0__m0_05`: discovery objective `3170.3876`, locked objective `1040.2185`, worst leave-one-family objective `4210.3442`
