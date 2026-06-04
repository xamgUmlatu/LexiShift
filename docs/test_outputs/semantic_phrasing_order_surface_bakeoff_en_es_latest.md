# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T19:24:52Z`
- Matrix: `en_es_semantic_phrasing_order_surface_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_phrasing_order_surface_bakeoff_en_es.json`
- Evaluation suites: `4`
- Config rows: `137`
- Case score traces: `26030`
- Case traces included in JSON: `False`
- Negative-control sanity: `ok`

## Recommendation

Best promotable candidate is `phrasing_control_rows_max`; with harmful `0`; and false abstain `45`; against incumbent `phrasing_control_current_all`; and negative controls failed as expected.

## Best By Constraint

- incumbent_control: `phrasing_control_current_all`
  - Harmful / false abstain: `1` / `46`
  - Decision / winner accuracy: `75.26%` / `58.77%`
  - Shape: `tfidf_cosine:masked_sentence:all_evidence_text:single_concatenated_text:active_minus_strongest_shadow:phrase_override`

- best_overall: `phrasing_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_zero_harm: `phrasing_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

- best_promotable_candidate: `phrasing_control_rows_max`
  - Harmful / false abstain: `0` / `45`
  - Decision / winner accuracy: `76.32%` / `60.53%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| control:rows_max | 1 | phrasing_control_rows_max | phrasing_control_rows_max | 0 | 45 | 60.53% | 450.6316 |
| evidence:paraphrase_variants | 12 | phrasing_evidence_paraphrase_variants:a0_1__m0 | phrasing_evidence_paraphrase_variants:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| phrasing:dependency_role | 12 | phrasing_context_dependency_role_template:a0_1__m0 | phrasing_context_dependency_role_template:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| phrasing:surface_frame | 12 | phrasing_context_surface_frame_template:a0_1__m0 | phrasing_context_surface_frame_template:a0_1__m0 | 0 | 55 | 51.75% | 550.7719 |
| evidence:canonical_template | 12 | phrasing_evidence_canonical_template:a0_1__m0 | phrasing_evidence_canonical_template:a0_1__m0 | 0 | 56 | 50.88% | 560.7860 |
| phrasing:before_after_slots | 12 | phrasing_context_before_after_ordered_evidence:a0_1__m0 | phrasing_context_before_after_ordered_evidence:a0_1__m0 | 0 | 56 | 50.88% | 560.7860 |
| phrasing:lexical_only_without_frame | 12 | phrasing_context_lexical_only_ordered_evidence:a0_1__m0 | phrasing_context_lexical_only_ordered_evidence:a0_1__m0 | 0 | 56 | 50.88% | 560.7860 |
| phrasing:skipgram | 12 | phrasing_context_skipgram_ordered_evidence:a0_1__m0 | phrasing_context_skipgram_ordered_evidence:a0_1__m0 | 0 | 56 | 50.88% | 560.7860 |
| phrasing:frame_only_without_lexical_content | 12 | phrasing_context_frame_only_template:a0_02__m0 | phrasing_context_frame_only_template:a0_02__m0 | 0 | 57 | 50.00% | 570.8000 |
| phrasing:negation_modal | 12 | phrasing_context_negation_modal_template:a0_02__m0_02 | phrasing_context_negation_modal_template:a0_02__m0_02 | 0 | 57 | 50.00% | 570.8000 |
| phrasing:pos_frame | 12 | phrasing_context_pos_frame_template:a0_02__m0 | phrasing_context_pos_frame_template:a0_02__m0 | 0 | 57 | 50.00% | 570.8000 |
| control:current_all | 1 | phrasing_control_current_all |  | 1 | 46 | 58.77% | 1460.6596 |
| phrasing:ordered_ngram | 12 | phrasing_context_ordered_ngram_ordered_evidence:a0_1__m0 |  | 3 | 54 | 50.88% | 3540.7912 |
| negative:reversed_context | 1 | phrasing_negative_reversed_context |  | 83 | 4 | 58.77% | 83040.8702 |
| negative:shuffled_context | 1 | phrasing_negative_shuffled_context |  | 83 | 4 | 58.77% | 83040.8702 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| phrasing_control_rows_max | frozen_v10 | 95 | 0 | 27 | 71.58% |
| phrasing_control_rows_max | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_control_rows_max | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_control_rows_max | source_heldout_v2 | 38 | 0 | 18 | 52.63% |
| phrasing_context_dependency_role_template:a0_1__m0 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_dependency_role_template:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_context_dependency_role_template:a0_1__m0_005 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_dependency_role_template:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_context_dependency_role_template:a0_1__m0_02 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_dependency_role_template:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_dependency_role_template:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_context_surface_frame_template:a0_1__m0 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_surface_frame_template:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_context_surface_frame_template:a0_1__m0_005 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_surface_frame_template:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_context_surface_frame_template:a0_1__m0_02 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_context_surface_frame_template:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_context_surface_frame_template:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |
| phrasing_evidence_paraphrase_variants:a0_1__m0 | frozen_v10 | 95 | 0 | 36 | 62.11% |
| phrasing_evidence_paraphrase_variants:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| phrasing_evidence_paraphrase_variants:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| phrasing_evidence_paraphrase_variants:a0_1__m0 | source_heldout_v2 | 38 | 0 | 19 | 50.00% |

## Decision Signature Clusters

- Unique replace signatures: `66`
- Largest replace-signature cluster: `30` configs
- `e3b0c44298fc1c14`: `30` configs, sample `phrasing_context_frame_only_template:a0_02__m0, phrasing_context_frame_only_template:a0_02__m0_005, phrasing_context_frame_only_template:a0_02__m0_02, phrasing_context_frame_only_template:a0_05__m0, phrasing_context_frame_only_template:a0_05__m0_005`
- `e8c8e2d6f80050a7`: `9` configs, sample `phrasing_context_before_after_ordered_evidence:a0_1__m0, phrasing_context_before_after_ordered_evidence:a0_1__m0_005, phrasing_context_before_after_ordered_evidence:a0_1__m0_02, phrasing_context_lexical_only_ordered_evidence:a0_1__m0, phrasing_context_lexical_only_ordered_evidence:a0_1__m0_005`
- `25a2e7fcdd9d9477`: `6` configs, sample `phrasing_context_dependency_role_template:a0_1__m0, phrasing_context_dependency_role_template:a0_1__m0_005, phrasing_context_dependency_role_template:a0_1__m0_02, phrasing_context_surface_frame_template:a0_1__m0, phrasing_context_surface_frame_template:a0_1__m0_005`
- `155a8995c17d47ba`: `3` configs, sample `phrasing_evidence_paraphrase_variants:a0_1__m0, phrasing_evidence_paraphrase_variants:a0_1__m0_005, phrasing_evidence_paraphrase_variants:a0_1__m0_02`
- `2089d85b1c8b4cac`: `3` configs, sample `phrasing_context_lexical_only_ordered_evidence:a0__m0, phrasing_negative_reversed_context, phrasing_negative_shuffled_context`

## Headline Metric Ties

- Tied primary-metric groups: `21`
- Largest tied group: `30` configs
- `harm=0|false=57|decision=0.700000|winner=0.500000`: `30` configs, unique replace signatures `1`, ROC AUC `0.4868..0.5000`, Avg Prec. `0.3487..0.4004`
- `harm=0|false=56|decision=0.705263|winner=0.508772`: `12` configs, unique replace signatures `2`, ROC AUC `0.5088..0.6254`, Avg Prec. `0.3589..0.4940`
- `harm=0|false=55|decision=0.710526|winner=0.517544`: `9` configs, unique replace signatures `2`, ROC AUC `0.4724..0.5193`, Avg Prec. `0.3404..0.3757`
- `harm=2|false=54|decision=0.705263|winner=0.508772`: `6` configs, unique replace signatures `2`, ROC AUC `0.4724..0.5193`, Avg Prec. `0.3404..0.3757`
- `harm=11|false=43|decision=0.715789|winner=0.570175`: `3` configs, unique replace signatures `2`, ROC AUC `0.6076..0.6254`, Avg Prec. `0.4553..0.4940`
- `harm=11|false=44|decision=0.710526|winner=0.561404`: `3` configs, unique replace signatures `2`, ROC AUC `0.5733..0.6254`, Avg Prec. `0.4203..0.4940`
- `harm=11|false=46|decision=0.700000|winner=0.543860`: `3` configs, unique replace signatures `1`, ROC AUC `0.5733..0.5733`, Avg Prec. `0.4203..0.4203`
- `harm=1|false=54|decision=0.710526|winner=0.517544`: `3` configs, unique replace signatures `1`, ROC AUC `0.5088..0.5088`, Avg Prec. `0.3589..0.3589`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control:rows_max | phrasing_control_rows_max | 0 | 28 | 0 | 17 | 170.7428 | phrasing_control_rows_max |
| evidence:paraphrase_variants | phrasing_evidence_paraphrase_variants:a0_1__m0 | 0 | 38 | 0 | 17 | 170.7428 | phrasing_evidence_paraphrase_variants:a0_1__m0 |
| phrasing:before_after_slots | phrasing_context_before_after_ordered_evidence:a0_1__m0 | 0 | 38 | 0 | 18 | 180.7865 | phrasing_context_before_after_ordered_evidence:a0_1__m0 |
| phrasing:dependency_role | phrasing_context_dependency_role_template:a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | phrasing_context_dependency_role_template:a0_1__m0 |
| phrasing:frame_only_without_lexical_content | phrasing_context_frame_only_template:a0_02__m0 | 0 | 39 | 0 | 18 | 180.7865 | phrasing_context_frame_only_template:a0_02__m0 |
| phrasing:lexical_only_without_frame | phrasing_context_lexical_only_ordered_evidence:a0_1__m0 | 0 | 38 | 0 | 18 | 180.7865 | phrasing_context_lexical_only_ordered_evidence:a0_1__m0 |
| phrasing:negation_modal | phrasing_context_negation_modal_template:a0_02__m0_02 | 0 | 39 | 0 | 18 | 180.7865 | phrasing_context_negation_modal_template:a0_02__m0_02 |
| phrasing:pos_frame | phrasing_context_pos_frame_template:a0_02__m0 | 0 | 39 | 0 | 18 | 180.7865 | phrasing_context_pos_frame_template:a0_02__m0 |
| phrasing:skipgram | phrasing_context_skipgram_ordered_evidence:a0_1__m0 | 0 | 38 | 0 | 18 | 180.7865 | phrasing_context_skipgram_ordered_evidence:a0_1__m0 |
| phrasing:surface_frame | phrasing_context_surface_frame_template:a0_1__m0 | 0 | 37 | 0 | 18 | 180.7865 | phrasing_context_surface_frame_template:a0_1__m0 |
| evidence:canonical_template | phrasing_evidence_canonical_template:a0_05__m0 | 0 | 37 | 1 | 17 | 1170.7865 | phrasing_evidence_canonical_template:a0_1__m0 |
| control:current_all | phrasing_control_current_all | 0 | 28 | 1 | 18 | 1180.8302 | phrasing_control_current_all |
| phrasing:ordered_ngram | phrasing_context_ordered_ngram_ordered_evidence:a0_1__m0 | 1 | 36 | 2 | 18 | 2180.8739 | phrasing_context_ordered_ngram_ordered_evidence:a0_1__m0 |
| negative:reversed_context | phrasing_negative_reversed_context | 57 | 2 | 26 | 2 | 26020.8450 | phrasing_negative_reversed_context |
| negative:shuffled_context | phrasing_negative_shuffled_context | 57 | 2 | 26 | 2 | 26020.8450 | phrasing_negative_shuffled_context |

## Incumbent Case Deltas

- Incumbent config: `phrasing_control_current_all`
- Configs identical to incumbent decisions: `0`
- `phrasing_context_frame_only_template:a0__m0`: decisions changed `144`, false abstains fixed/introduced `46`/`0`, harmful fixed/introduced `0`/`98`
- `phrasing_context_pos_frame_template:a0__m0`: decisions changed `144`, false abstains fixed/introduced `46`/`0`, harmful fixed/introduced `0`/`98`
- `phrasing_context_before_after_ordered_evidence:a0__m0`: decisions changed `126`, false abstains fixed/introduced `42`/`1`, harmful fixed/introduced `0`/`83`
- `phrasing_context_skipgram_ordered_evidence:a0__m0`: decisions changed `125`, false abstains fixed/introduced `42`/`1`, harmful fixed/introduced `0`/`82`
- `phrasing_context_lexical_only_ordered_evidence:a0__m0`: decisions changed `124`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`82`
- `phrasing_negative_reversed_context`: decisions changed `124`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`82`
- `phrasing_negative_shuffled_context`: decisions changed `124`, false abstains fixed/introduced `42`/`0`, harmful fixed/introduced `0`/`82`
- `phrasing_context_ordered_ngram_ordered_evidence:a0__m0`: decisions changed `107`, false abstains fixed/introduced `36`/`2`, harmful fixed/introduced `0`/`69`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | control:rows_max | phrasing_control_rows_max | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.6570 | 0.5861 | 450.6316 |
| 2 | phrasing:dependency_role | phrasing_context_dependency_role_template:a0_1__m0 | tfidf_cosine | dependency_role_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4724 | 0.3404 | 550.7719 |
| 3 | phrasing:dependency_role | phrasing_context_dependency_role_template:a0_1__m0_005 | tfidf_cosine | dependency_role_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4724 | 0.3404 | 550.7719 |
| 4 | phrasing:dependency_role | phrasing_context_dependency_role_template:a0_1__m0_02 | tfidf_cosine | dependency_role_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4724 | 0.3404 | 550.7719 |
| 5 | phrasing:surface_frame | phrasing_context_surface_frame_template:a0_1__m0 | tfidf_cosine | surface_frame_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5193 | 0.3757 | 550.7719 |
| 6 | phrasing:surface_frame | phrasing_context_surface_frame_template:a0_1__m0_005 | tfidf_cosine | surface_frame_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5193 | 0.3757 | 550.7719 |
| 7 | phrasing:surface_frame | phrasing_context_surface_frame_template:a0_1__m0_02 | tfidf_cosine | surface_frame_context | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.5193 | 0.3757 | 550.7719 |
| 8 | evidence:paraphrase_variants | phrasing_evidence_paraphrase_variants:a0_1__m0 | tfidf_cosine | masked_sentence | paraphrase_variant_evidence | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4916 | 0.3605 | 550.7719 |
| 9 | evidence:paraphrase_variants | phrasing_evidence_paraphrase_variants:a0_1__m0_005 | tfidf_cosine | masked_sentence | paraphrase_variant_evidence | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4916 | 0.3605 | 550.7719 |
| 10 | evidence:paraphrase_variants | phrasing_evidence_paraphrase_variants:a0_1__m0_02 | tfidf_cosine | masked_sentence | paraphrase_variant_evidence | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 55 | 51.75% | 0.4916 | 0.3605 | 550.7719 |
| 11 | phrasing:before_after_slots | phrasing_context_before_after_ordered_evidence:a0_1__m0 | tfidf_cosine | before_after_slot_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.5733 | 0.4203 | 560.7860 |
| 12 | phrasing:before_after_slots | phrasing_context_before_after_ordered_evidence:a0_1__m0_005 | tfidf_cosine | before_after_slot_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.5733 | 0.4203 | 560.7860 |
| 13 | phrasing:before_after_slots | phrasing_context_before_after_ordered_evidence:a0_1__m0_02 | tfidf_cosine | before_after_slot_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.5733 | 0.4203 | 560.7860 |
| 14 | phrasing:lexical_only_without_frame | phrasing_context_lexical_only_ordered_evidence:a0_1__m0 | tfidf_cosine | lexical_only_without_frame | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6254 | 0.4940 | 560.7860 |
| 15 | phrasing:lexical_only_without_frame | phrasing_context_lexical_only_ordered_evidence:a0_1__m0_005 | tfidf_cosine | lexical_only_without_frame | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6254 | 0.4940 | 560.7860 |
| 16 | phrasing:lexical_only_without_frame | phrasing_context_lexical_only_ordered_evidence:a0_1__m0_02 | tfidf_cosine | lexical_only_without_frame | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6254 | 0.4940 | 560.7860 |
| 17 | phrasing:skipgram | phrasing_context_skipgram_ordered_evidence:a0_1__m0 | tfidf_cosine | skipgram_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6076 | 0.4553 | 560.7860 |
| 18 | phrasing:skipgram | phrasing_context_skipgram_ordered_evidence:a0_1__m0_005 | tfidf_cosine | skipgram_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6076 | 0.4553 | 560.7860 |
| 19 | phrasing:skipgram | phrasing_context_skipgram_ordered_evidence:a0_1__m0_02 | tfidf_cosine | skipgram_context | ordered_evidence_phrase | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.6076 | 0.4553 | 560.7860 |
| 20 | evidence:canonical_template | phrasing_evidence_canonical_template:a0_1__m0 | tfidf_cosine | masked_sentence | canonical_template_evidence | single_concatenated_text | active_minus_strongest_shadow | phrase_override | normal | 0 | 56 | 50.88% | 0.5088 | 0.3589 | 560.7860 |

## Negative Controls

- `phrasing_negative_shuffled_evidence`: `failed_as_expected` (lexical_leakage; harmful `80`, false abstain `7`, accuracy `54.21%`)

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `phrasing_control_rows_max`: discovery objective `280.5790`, locked objective `170.7428`, worst leave-one-family objective `450.6523`
- `phrasing_evidence_paraphrase_variants:a0_1__m0`: discovery objective `380.7858`, locked objective `170.7428`, worst leave-one-family objective `550.7750`
- `phrasing_evidence_paraphrase_variants:a0_1__m0_005`: discovery objective `380.7858`, locked objective `170.7428`, worst leave-one-family objective `550.7750`
- `phrasing_evidence_paraphrase_variants:a0_1__m0_02`: discovery objective `380.7858`, locked objective `170.7428`, worst leave-one-family objective `550.7750`
- `phrasing_context_dependency_role_template:a0_1__m0`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
- `phrasing_context_dependency_role_template:a0_1__m0_005`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
- `phrasing_context_dependency_role_template:a0_1__m0_02`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
- `phrasing_context_surface_frame_template:a0_1__m0`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
- `phrasing_context_surface_frame_template:a0_1__m0_005`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
- `phrasing_context_surface_frame_template:a0_1__m0_02`: discovery objective `370.7651`, locked objective `180.7865`, worst leave-one-family objective `550.7750`
