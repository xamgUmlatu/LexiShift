# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T18:04:13Z`
- Matrix: `en_es_semantic_decision_rule_matrix_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_decision_rule_matrix_en_es.json`
- Evaluation suites: `1`
- Config rows: `26`
- Case score traces: `2470`
- Case traces included in JSON: `True`
- Negative-control sanity: `ok`

## Recommendation

No candidate cleared the incumbent-aware promotability screen; treat the matrix as evidence for source coverage or representation work before policy promotion.

## Best By Constraint

- incumbent_control: `control_st_masked_all_margin_phrase_override`
  - Harmful / false abstain: `1` / `12`
  - Decision / winner accuracy: `86.32%` / `84.21%`
  - Shape: `sentence_transformer_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `control_tfidf_masked_all_margin_phrase_override`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `control_tfidf_masked_all_margin_phrase_override`
  - Harmful / false abstain: `0` / `28`
  - Decision / winner accuracy: `70.53%` / `63.16%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| active_minus_strongest_shadow | 17 | control_tfidf_masked_all_margin_phrase_override | control_tfidf_masked_all_margin_phrase_override | 0 | 28 | 63.16% | 280.6632 |
| softmax_probability | 1 | decision_softmax_weighted_topk |  | 2 | 26 | 65.79% | 2260.6368 |
| active_ratio_strongest_shadow | 1 | decision_ratio_weighted_topk |  | 6 | 22 | 67.11% | 6220.6237 |
| pairwise_active_beats_all_shadows | 1 | decision_pairwise_all_weighted_topk |  | 36 | 2 | 63.16% | 36020.7684 |
| pairwise_active_beats_most_shadows | 1 | decision_pairwise_most_weighted_topk |  | 36 | 2 | 63.16% | 36020.7684 |

## Decision Signature Clusters

- Unique replace signatures: `14`
- Largest replace-signature cluster: `8` configs
- `4df472f64266c828`: `8` configs, sample `decision_pairwise_all_weighted_topk, decision_pairwise_most_weighted_topk, phrase_as_shadow_weighted_topk, phrase_first_weighted_topk, repr_separate_rows_tfidf_max_margin`
- `1a8568ea84246cbc`: `1` configs, sample `repr_sense_label_tfidf_margin`
- `20e9cd00defccc19`: `1` configs, sample `control_st_masked_all_margin_phrase_override`
- `271e673f54f13fb8`: `1` configs, sample `context_raw_sentence_tfidf_all_margin`
- `37fc7c2d85c252c4`: `1` configs, sample `context_masked_window_tfidf_all_margin`

## Headline Metric Ties

- Tied primary-metric groups: `1`
- Largest tied group: `8` configs
- `harm=36|false=2|decision=0.600000|winner=0.631579`: `8` configs, unique replace signatures `1`, ROC AUC `0.5877..0.7627`, Avg Prec. `0.5224..0.7383`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| active_ratio_strongest_shadow | decision_ratio_weighted_topk | 6 | 17 | 0 | 5 | 50.5506 | decision_ratio_weighted_topk |
| softmax_probability | decision_softmax_weighted_topk | 2 | 19 | 0 | 7 | 70.7708 | decision_softmax_weighted_topk |
| active_minus_strongest_shadow | control_tfidf_masked_all_margin_phrase_override | 0 | 20 | 0 | 8 | 80.8810 | control_st_masked_all_margin_phrase_override |
| pairwise_active_beats_all_shadows | decision_pairwise_all_weighted_topk | 26 | 2 | 10 | 0 | 10000.9137 | decision_pairwise_all_weighted_topk |
| pairwise_active_beats_most_shadows | decision_pairwise_most_weighted_topk | 26 | 2 | 10 | 0 | 10000.9137 | decision_pairwise_most_weighted_topk |

## Incumbent Case Deltas

- Incumbent config: `control_st_masked_all_margin_phrase_override`
- Configs identical to incumbent decisions: `0`
- `repr_sense_gloss_bundle_tfidf_margin`: decisions changed `59`, false abstains fixed/introduced `12`/`0`, harmful fixed/introduced `0`/`47`
- `repr_sense_label_tfidf_margin`: decisions changed `58`, false abstains fixed/introduced `12`/`0`, harmful fixed/introduced `0`/`46`
- `repr_separate_rows_tfidf_definition_agreement_margin`: decisions changed `57`, false abstains fixed/introduced `12`/`0`, harmful fixed/introduced `0`/`45`
- `phrase_semantic_only_weighted_topk`: decisions changed `55`, false abstains fixed/introduced `11`/`1`, harmful fixed/introduced `0`/`43`
- `repr_gloss_text_tfidf_margin`: decisions changed `54`, false abstains fixed/introduced `9`/`3`, harmful fixed/introduced `0`/`42`
- `context_masked_window_tfidf_all_margin`: decisions changed `50`, false abstains fixed/introduced `11`/`1`, harmful fixed/introduced `0`/`38`
- `scorer_token_masked_all_margin`: decisions changed `47`, false abstains fixed/introduced `11`/`2`, harmful fixed/introduced `0`/`34`
- `decision_pairwise_all_weighted_topk`: decisions changed `47`, false abstains fixed/introduced `11`/`1`, harmful fixed/introduced `0`/`35`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | active_minus_strongest_shadow | control_tfidf_masked_all_margin_phrase_override | tfidf_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 28 | 63.16% | 0.7119 | 0.7065 | 280.6632 |
| 2 | active_minus_strongest_shadow | control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 1 | 12 | 84.21% | 0.9104 | 0.8634 | 1120.2947 |
| 3 | softmax_probability | decision_softmax_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | softmax_probability | phrase_override | normal | 2 | 26 | 65.79% | 0.7124 | 0.7075 | 2260.6368 |
| 4 | active_ratio_strongest_shadow | decision_ratio_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_ratio_strongest_shadow | phrase_override | normal | 6 | 22 | 67.11% | 0.6477 | 0.5795 | 6220.6237 |
| 5 | active_minus_strongest_shadow | context_raw_sentence_tfidf_all_margin | tfidf_cosine | raw_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 29 | 8 | 63.16% | 0.6861 | 0.6573 | 29080.7579 |
| 6 | active_minus_strongest_shadow | context_raw_window_tfidf_all_margin | tfidf_cosine | raw_window | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 30 | 8 | 61.84% | 0.6634 | 0.6403 | 30080.7816 |
| 7 | active_minus_strongest_shadow | scorer_token_masked_all_margin | token_jaccard | masked_sentence | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 35 | 3 | 63.16% | 0.6747 | 0.6445 | 35030.7684 |
| 8 | pairwise_active_beats_all_shadows | decision_pairwise_all_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | pairwise_active_beats_all_shadows | phrase_override | normal | 36 | 2 | 63.16% | 0.5877 | 0.5224 | 36020.7684 |
| 9 | pairwise_active_beats_most_shadows | decision_pairwise_most_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | pairwise_active_beats_most_shadows | phrase_override | normal | 36 | 2 | 63.16% | 0.5877 | 0.5224 | 36020.7684 |
| 10 | active_minus_strongest_shadow | phrase_as_shadow_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_as_shadow | normal | 36 | 2 | 63.16% | 0.7627 | 0.7383 | 36020.7684 |
| 11 | active_minus_strongest_shadow | phrase_first_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_first | normal | 36 | 2 | 63.16% | 0.7124 | 0.7075 | 36020.7684 |
| 12 | active_minus_strongest_shadow | repr_separate_rows_tfidf_max_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 36 | 2 | 63.16% | 0.7138 | 0.7121 | 36020.7684 |
| 13 | active_minus_strongest_shadow | repr_separate_rows_tfidf_mean_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | mean_row_score | active_minus_strongest_shadow | phrase_override | normal | 36 | 2 | 63.16% | 0.7138 | 0.7121 | 36020.7684 |
| 14 | active_minus_strongest_shadow | repr_separate_rows_tfidf_topk_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 36 | 2 | 63.16% | 0.7138 | 0.7121 | 36020.7684 |
| 15 | active_minus_strongest_shadow | repr_separate_rows_tfidf_weighted_topk_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | phrase_override | normal | 36 | 2 | 63.16% | 0.7124 | 0.7075 | 36020.7684 |
| 16 | active_minus_strongest_shadow | context_masked_window_tfidf_all_margin | tfidf_cosine | masked_window | all_evidence_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 39 | 2 | 59.21% | 0.6685 | 0.6643 | 39020.8395 |
| 17 | active_minus_strongest_shadow | repr_gloss_text_tfidf_margin | tfidf_cosine | masked_sentence | gloss_text | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 43 | 6 | 48.68% | 0.4460 | 0.3975 | 43061.0289 |
| 18 | active_minus_strongest_shadow | phrase_semantic_only_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | source_weighted_top_k | active_minus_strongest_shadow | semantic_only | normal | 44 | 2 | 63.16% | 0.7124 | 0.7075 | 44020.8526 |
| 19 | active_minus_strongest_shadow | repr_separate_rows_tfidf_definition_agreement_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | definition_example_agreement | active_minus_strongest_shadow | phrase_override | normal | 46 | 0 | 53.95% | 0.5425 | 0.4987 | 46000.9447 |
| 20 | active_minus_strongest_shadow | repr_sense_label_tfidf_margin | tfidf_cosine | masked_sentence | sense_label | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 47 | 0 | 52.63% | 0.5734 | 0.5782 | 47000.9684 |

## Negative Controls

- `negative_shadow_only_over_abstain`: `failed_as_expected` (over_abstain; harmful `0`, false abstain `38`, accuracy `60.00%`)
- `negative_shuffled_labels_collapse`: `failed_as_expected` (collapse; harmful `43`, false abstain `16`, accuracy `37.89%`)
- `negative_no_shadow_over_replace`: `failed_as_expected` (over_replace; harmful `49`, false abstain `0`, accuracy `48.42%`)
- `negative_target_lemma_lexical_leakage`: `failed_as_expected` (lexical_leakage; harmful `49`, false abstain `0`, accuracy `48.42%`)
- `negative_active_only_over_replace`: `failed_as_expected` (over_replace; harmful `57`, false abstain `0`, accuracy `40.00%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `control_st_masked_all_margin_phrase_override`: discovery objective `1090.2851`, locked objective `30.3304`, worst leave-one-family objective `1120.3111`
- `decision_ratio_weighted_topk`: discovery objective `6170.6441`, locked objective `50.5506`, worst leave-one-family objective `6220.6583`
- `decision_softmax_weighted_topk`: discovery objective `2190.6004`, locked objective `70.7708`, worst leave-one-family objective `2260.6722`
- `control_tfidf_masked_all_margin_phrase_override`: discovery objective `200.6036`, locked objective `80.8810`, worst leave-one-family objective `280.7000`
- `negative_shadow_only_over_abstain`: discovery objective `300.9054`, locked objective `80.8810`, worst leave-one-family objective `360.9000`
- `context_raw_sentence_tfidf_all_margin`: discovery objective `25070.8491`, locked objective `4010.4256`, worst leave-one-family objective `29080.8000`
- `context_raw_window_tfidf_all_margin`: discovery objective `26070.8793`, locked objective `4010.4256`, worst leave-one-family objective `30080.8250`
- `scorer_token_masked_all_margin`: discovery objective `25030.7284`, locked objective `10000.9137`, worst leave-one-family objective `35030.8111`
- `decision_pairwise_all_weighted_topk`: discovery objective `26020.7284`, locked objective `10000.9137`, worst leave-one-family objective `36020.8111`
- `decision_pairwise_most_weighted_topk`: discovery objective `26020.7284`, locked objective `10000.9137`, worst leave-one-family objective `36020.8111`

## Threshold Sensitivity

- `control_st_masked_all_margin_phrase_override` a0_m0: harmful `1`, false abstain `12`, objective `1120.2947`
- `control_st_masked_all_margin_phrase_override` a0_m005: harmful `1`, false abstain `13`, objective `1130.3184`
- `control_st_masked_all_margin_phrase_override` a005_m0: harmful `1`, false abstain `12`, objective `1120.2947`
- `control_st_masked_all_margin_phrase_override` a035_m005: harmful `1`, false abstain `19`, objective `1190.4605`
- `repr_separate_rows_tfidf_weighted_topk_margin` a0_m0: harmful `36`, false abstain `2`, objective `36020.7684`
- `repr_separate_rows_tfidf_weighted_topk_margin` a0_m005: harmful `6`, false abstain `24`, objective `6240.6711`
- `repr_separate_rows_tfidf_weighted_topk_margin` a005_m0: harmful `0`, false abstain `29`, objective `290.6868`
- `repr_separate_rows_tfidf_weighted_topk_margin` a035_m005: harmful `0`, false abstain `38`, objective `380.9000`
- `decision_ratio_weighted_topk` ratio_1_00: harmful `6`, false abstain `22`, objective `6220.6237`
- `decision_ratio_weighted_topk` ratio_1_03: harmful `6`, false abstain `22`, objective `6220.6237`
- `decision_ratio_weighted_topk` ratio_1_08: harmful `6`, false abstain `24`, objective `6240.6711`
- `decision_softmax_weighted_topk` softmax_0_50: harmful `36`, false abstain `2`, objective `36020.7684`
- `decision_softmax_weighted_topk` softmax_0_55: harmful `2`, false abstain `26`, objective `2260.6368`
- `decision_softmax_weighted_topk` softmax_0_65: harmful `0`, false abstain `36`, objective `360.8526`

## Source-Family Dropout

- `repr_separate_rows_tfidf_weighted_topk_margin` drop `sense_label`: harmful `37`, false abstain `4`, objective `37040.8395`
- `repr_separate_rows_tfidf_weighted_topk_margin` drop `definition`: harmful `39`, false abstain `0`, objective `39000.7789`
- `repr_separate_rows_tfidf_weighted_topk_margin` drop `auxiliary`: harmful `42`, false abstain `4`, objective `42040.9579`
- `repr_separate_rows_tfidf_weighted_topk_margin` drop `qualifier`: harmful `36`, false abstain `2`, objective `36020.7684`
- `repr_separate_rows_tfidf_weighted_topk_margin` drop `target_lemma`: harmful `36`, false abstain `2`, objective `36020.7684`
