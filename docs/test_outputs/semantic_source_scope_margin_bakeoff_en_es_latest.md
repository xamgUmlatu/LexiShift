# en-es Semantic Decision Rule Matrix

- Status: `ok`
- Generated: `2026-04-28T21:41:05Z`
- Matrix: `en_es_semantic_source_scope_margin_bakeoff_v1`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Manifest: `docs/test_inputs/semantic_source_scope_margin_bakeoff_en_es.json`
- Evaluation suites: `4`
- Config rows: `61`
- Case score traces: `11590`
- Case traces included in JSON: `False`
- Negative-control sanity: `not_applicable`

## Recommendation

Best promotable candidate is `combined_definition_example_plus_source_max:a0_1__m0`; with harmful `0`; and false abstain `37`; against incumbent `source_scope_definition_example_row_control`; with negative controls delegated to the companion broad matrix.

## Best By Constraint

- incumbent_control: `source_scope_definition_example_row_control`
  - Harmful / false abstain: `0` / `44`
  - Decision / winner accuracy: `76.84%` / `61.40%`
  - Shape: `tfidf_cosine:masked_sentence:definition_and_example_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`
  - Source scope: `no_source` (`0` attached rows)

- best_overall: `combined_definition_example_plus_source_max:a0_1__m0`
  - Harmful / false abstain: `0` / `37`
  - Decision / winner accuracy: `80.53%` / `67.54%`
  - Shape: `tfidf_cosine:masked_sentence:definition_example_plus_source_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`
  - Source scope: `llm_v2_plus_wordnet_reference` (`259` attached rows)

- best_zero_harm: `combined_definition_example_plus_source_max:a0_1__m0`
  - Harmful / false abstain: `0` / `37`
  - Decision / winner accuracy: `80.53%` / `67.54%`
  - Shape: `tfidf_cosine:masked_sentence:definition_example_plus_source_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`
  - Source scope: `llm_v2_plus_wordnet_reference` (`259` attached rows)

- best_promotable_candidate: `combined_definition_example_plus_source_max:a0_1__m0`
  - Harmful / false abstain: `0` / `37`
  - Decision / winner accuracy: `80.53%` / `67.54%`
  - Shape: `tfidf_cosine:masked_sentence:definition_example_plus_source_rows_separate:max_row_score:active_minus_strongest_shadow:phrase_override`
  - Source scope: `llm_v2_plus_wordnet_reference` (`259` attached rows)

## Source Evidence Scopes

| Scope | Paths | Attached Rows | Mask | Window |
| ---: | --- | ---: | --- | ---: |
| 1 |  | 0 | ___ | 4 |
| 2 | /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json | 126 | ___ | 4 |
| 4 | /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-def-example-plus-llm-aligned-frame-gap-v2-20260429a_cycle_sense_admitted_normalized_evidence.json<br>/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json | 259 | ___ | 4 |
| 3 | /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/experiments/semantic_example_frame_batches/en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json | 133 | ___ | 4 |

## Algorithm Family Winners

| Family | Rows | Best Config | Zero-Harm Config | Harmful | False Abstain | Winner Acc. | Objective |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| combined:definition_example_plus_source:max | 6 | combined_definition_example_plus_source_max:a0_1__m0 | combined_definition_example_plus_source_max:a0_1__m0 | 0 | 37 | 67.54% | 370.5193 |
| llm_v2:definition_example_plus_source:max | 6 | llm_v2_definition_example_plus_source_max:a0_1__m0 | llm_v2_definition_example_plus_source_max:a0_1__m0 | 0 | 39 | 65.79% | 390.5474 |
| reference:definition_example_plus_source:max | 6 | reference_definition_example_plus_source_max:a0_1__m0_005 | reference_definition_example_plus_source_max:a0_1__m0_005 | 0 | 41 | 64.04% | 410.5754 |
| control:definition_example_rows | 1 | source_scope_definition_example_row_control | source_scope_definition_example_row_control | 0 | 44 | 61.40% | 440.6175 |
| combined:source_plus_definition:max | 6 | combined_source_plus_definition_max:a0_1__m0 | combined_source_plus_definition_max:a0_1__m0 | 0 | 45 | 60.53% | 450.6316 |
| combined:context_selected_definition_source:before_after | 18 | combined_context_selected_definition_source:selection_top_k2__a0_1__m0 | combined_context_selected_definition_source:selection_top_k2__a0_1__m0 | 0 | 47 | 58.77% | 470.6596 |
| llm_v2:source_plus_definition:max | 6 | llm_v2_source_plus_definition_max:a0_1__m0 | llm_v2_source_plus_definition_max:a0_1__m0 | 0 | 47 | 58.77% | 470.6596 |
| llm_v2:source_rows:max | 6 | llm_v2_source_rows_max:a0_1__m0 | llm_v2_source_rows_max:a0_1__m0 | 0 | 48 | 57.89% | 480.6737 |
| reference:source_plus_definition:max | 6 | reference_source_plus_definition_max:a0_1__m0_005 | reference_source_plus_definition_max:a0_1__m0_005 | 0 | 52 | 54.39% | 520.7298 |

## Evaluation Suite Breakdown

| Config | Suite | Cases | Harmful | False Abstain | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| combined_definition_example_plus_source_max:a0_1__m0 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| combined_definition_example_plus_source_max:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0 | source_heldout_v2 | 38 | 0 | 12 | 68.42% |
| combined_definition_example_plus_source_max:a0_1__m0_005 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| combined_definition_example_plus_source_max:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 12 | 68.42% |
| combined_definition_example_plus_source_max:a0_1__m0_02 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| combined_definition_example_plus_source_max:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| combined_definition_example_plus_source_max:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 13 | 65.79% |
| llm_v2_definition_example_plus_source_max:a0_1__m0 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| llm_v2_definition_example_plus_source_max:a0_1__m0 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0 | source_heldout_v2 | 38 | 0 | 14 | 63.16% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_005 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 14 | 63.16% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_02 | frozen_v10 | 95 | 0 | 25 | 73.68% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| llm_v2_definition_example_plus_source_max:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| reference_definition_example_plus_source_max:a0_1__m0_005 | frozen_v10 | 95 | 0 | 26 | 72.63% |
| reference_definition_example_plus_source_max:a0_1__m0_005 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| reference_definition_example_plus_source_max:a0_1__m0_005 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| reference_definition_example_plus_source_max:a0_1__m0_005 | source_heldout_v2 | 38 | 0 | 15 | 60.53% |
| reference_definition_example_plus_source_max:a0_1__m0_02 | frozen_v10 | 95 | 0 | 26 | 72.63% |
| reference_definition_example_plus_source_max:a0_1__m0_02 | phrase_challenge_v1 | 19 | 0 | 0 | 100.00% |
| reference_definition_example_plus_source_max:a0_1__m0_02 | phrase_heldout_v2 | 38 | 0 | 0 | 100.00% |
| reference_definition_example_plus_source_max:a0_1__m0_02 | source_heldout_v2 | 38 | 0 | 16 | 57.89% |

## Decision Signature Clusters

- Unique replace signatures: `44`
- Largest replace-signature cluster: `6` configs
- `0343bb3927f6429a`: `6` configs, sample `combined_context_selected_definition_source:selection_top_k2__a0_1__m0, combined_context_selected_definition_source:selection_top_k2__a0_1__m0_005, combined_context_selected_definition_source:selection_top_k3__a0_1__m0, combined_context_selected_definition_source:selection_top_k3__a0_1__m0_005, llm_v2_source_plus_definition_max:a0_1__m0`
- `18f5fb43265d0291`: `2` configs, sample `llm_v2_definition_example_plus_source_max:a0_05__m0, llm_v2_definition_example_plus_source_max:a0_05__m0_005`
- `31da06ba8c998d17`: `2` configs, sample `llm_v2_source_plus_definition_max:a0_05__m0, llm_v2_source_plus_definition_max:a0_05__m0_005`
- `330777ad68034b2c`: `2` configs, sample `combined_source_plus_definition_max:a0_1__m0, combined_source_plus_definition_max:a0_1__m0_005`
- `7435159e5a5fc8b9`: `2` configs, sample `combined_source_plus_definition_max:a0_05__m0, combined_source_plus_definition_max:a0_05__m0_005`

## Headline Metric Ties

- Tied primary-metric groups: `13`
- Largest tied group: `6` configs
- `harm=0|false=47|decision=0.752632|winner=0.587719`: `6` configs, unique replace signatures `1`, ROC AUC `0.6994..0.7235`, Avg Prec. `0.5727..0.5821`
- `harm=0|false=48|decision=0.747368|winner=0.578947`: `3` configs, unique replace signatures `2`, ROC AUC `0.7102..0.7235`, Avg Prec. `0.5695..0.5821`
- `harm=0|false=37|decision=0.805263|winner=0.675439`: `2` configs, unique replace signatures `1`, ROC AUC `0.7607..0.7607`, Avg Prec. `0.6710..0.6710`
- `harm=0|false=39|decision=0.794737|winner=0.657895`: `2` configs, unique replace signatures `1`, ROC AUC `0.7746..0.7746`, Avg Prec. `0.6724..0.6724`
- `harm=0|false=45|decision=0.763158|winner=0.605263`: `2` configs, unique replace signatures `1`, ROC AUC `0.7138..0.7138`, Avg Prec. `0.5938..0.5938`
- `harm=1|false=47|decision=0.747368|winner=0.578947`: `2` configs, unique replace signatures `1`, ROC AUC `0.6733..0.6733`, Avg Prec. `0.5464..0.5464`
- `harm=6|false=38|decision=0.768421|winner=0.640351`: `2` configs, unique replace signatures `1`, ROC AUC `0.6994..0.6994`, Avg Prec. `0.5727..0.5727`
- `harm=6|false=39|decision=0.763158|winner=0.631579`: `2` configs, unique replace signatures `1`, ROC AUC `0.6733..0.6733`, Avg Prec. `0.5464..0.5464`

## Discovery Selection vs Locked Eval

- Policy: select the best config inside each algorithm family using discovery-split objective only; report locked-eval metrics after selection
| Family | Selected On Discovery | Discovery Harmful | Discovery False Abstain | Locked Harmful | Locked False Abstain | Locked Objective | Locked Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| combined:definition_example_plus_source:max | combined_definition_example_plus_source_max:a0_1__m0 | 0 | 25 | 0 | 12 | 120.5243 | combined_definition_example_plus_source_max:a0_1__m0 |
| combined:source_plus_definition:max | combined_source_plus_definition_max:a0_1__m0 | 0 | 31 | 0 | 14 | 140.6117 | combined_source_plus_definition_max:a0_1__m0 |
| llm_v2:definition_example_plus_source:max | llm_v2_definition_example_plus_source_max:a0_1__m0 | 0 | 25 | 0 | 14 | 140.6117 | llm_v2_definition_example_plus_source_max:a0_1__m0 |
| combined:context_selected_definition_source:before_after | combined_context_selected_definition_source:selection_top_k2__a0_1__m0 | 0 | 32 | 0 | 15 | 150.6554 | combined_context_selected_definition_source:selection_top_k1__a0_05__m0 |
| llm_v2:source_plus_definition:max | llm_v2_source_plus_definition_max:a0_1__m0 | 0 | 32 | 0 | 15 | 150.6554 | llm_v2_source_plus_definition_max:a0_1__m0 |
| llm_v2:source_rows:max | llm_v2_source_rows_max:a0_1__m0 | 0 | 33 | 0 | 15 | 150.6554 | llm_v2_source_rows_max:a0_05__m0 |
| reference:definition_example_plus_source:max | reference_definition_example_plus_source_max:a0_1__m0_005 | 0 | 26 | 0 | 15 | 150.6554 | reference_definition_example_plus_source_max:a0_1__m0 |
| control:definition_example_rows | source_scope_definition_example_row_control | 0 | 28 | 0 | 16 | 160.6991 | source_scope_definition_example_row_control |
| reference:source_plus_definition:max | reference_source_plus_definition_max:a0_1__m0_005 | 0 | 35 | 0 | 17 | 170.7428 | reference_source_plus_definition_max:a0_1__m0 |

## Incumbent Case Deltas

- Incumbent config: `source_scope_definition_example_row_control`
- Configs identical to incumbent decisions: `0`
- `combined_context_selected_definition_source:selection_top_k1__a0_02__m0`: decisions changed `45`, false abstains fixed/introduced `15`/`4`, harmful fixed/introduced `0`/`26`
- `combined_context_selected_definition_source:selection_top_k3__a0_02__m0`: decisions changed `44`, false abstains fixed/introduced `18`/`4`, harmful fixed/introduced `0`/`22`
- `combined_context_selected_definition_source:selection_top_k2__a0_02__m0`: decisions changed `42`, false abstains fixed/introduced `16`/`4`, harmful fixed/introduced `0`/`22`
- `combined_context_selected_definition_source:selection_top_k1__a0_02__m0_005`: decisions changed `41`, false abstains fixed/introduced `14`/`5`, harmful fixed/introduced `0`/`22`
- `combined_context_selected_definition_source:selection_top_k3__a0_02__m0_005`: decisions changed `38`, false abstains fixed/introduced `15`/`5`, harmful fixed/introduced `0`/`18`
- `combined_context_selected_definition_source:selection_top_k2__a0_02__m0_005`: decisions changed `37`, false abstains fixed/introduced `14`/`5`, harmful fixed/introduced `0`/`18`
- `llm_v2_source_rows_max:a0_05__m0`: decisions changed `27`, false abstains fixed/introduced `11`/`8`, harmful fixed/introduced `0`/`8`
- `llm_v2_source_rows_max:a0_05__m0_005`: decisions changed `26`, false abstains fixed/introduced `11`/`8`, harmful fixed/introduced `0`/`7`

## Top Candidate Configs

| Rank | Family | Config | Scorer | Context | Evidence | Aggregation | Decision | Phrase | Control | Harmful | False Abstain | Winner Acc. | ROC AUC | Avg Prec. | Objective |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | combined:definition_example_plus_source:max | combined_definition_example_plus_source_max:a0_1__m0 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 37 | 67.54% | 0.7607 | 0.6710 | 370.5193 |
| 2 | combined:definition_example_plus_source:max | combined_definition_example_plus_source_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 37 | 67.54% | 0.7607 | 0.6710 | 370.5193 |
| 3 | combined:definition_example_plus_source:max | combined_definition_example_plus_source_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 38 | 66.67% | 0.7607 | 0.6710 | 380.5333 |
| 4 | llm_v2:definition_example_plus_source:max | llm_v2_definition_example_plus_source_max:a0_1__m0 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 39 | 65.79% | 0.7746 | 0.6724 | 390.5474 |
| 5 | llm_v2:definition_example_plus_source:max | llm_v2_definition_example_plus_source_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 39 | 65.79% | 0.7746 | 0.6724 | 390.5474 |
| 6 | llm_v2:definition_example_plus_source:max | llm_v2_definition_example_plus_source_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 40 | 64.91% | 0.7746 | 0.6724 | 400.5614 |
| 7 | reference:definition_example_plus_source:max | reference_definition_example_plus_source_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 41 | 64.04% | 0.6800 | 0.5891 | 410.5754 |
| 8 | reference:definition_example_plus_source:max | reference_definition_example_plus_source_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | definition_example_plus_source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 42 | 63.16% | 0.6800 | 0.5891 | 420.5895 |
| 9 | control:definition_example_rows | source_scope_definition_example_row_control | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 44 | 61.40% | 0.6575 | 0.5874 | 440.6175 |
| 10 | combined:source_plus_definition:max | combined_source_plus_definition_max:a0_1__m0 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.7138 | 0.5938 | 450.6316 |
| 11 | combined:source_plus_definition:max | combined_source_plus_definition_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 45 | 60.53% | 0.7138 | 0.5938 | 450.6316 |
| 12 | combined:source_plus_definition:max | combined_source_plus_definition_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 46 | 59.65% | 0.7138 | 0.5938 | 460.6456 |
| 13 | combined:context_selected_definition_source:before_after | combined_context_selected_definition_source:selection_top_k2__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.6994 | 0.5727 | 470.6596 |
| 14 | combined:context_selected_definition_source:before_after | combined_context_selected_definition_source:selection_top_k2__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.6994 | 0.5727 | 470.6596 |
| 15 | combined:context_selected_definition_source:before_after | combined_context_selected_definition_source:selection_top_k3__a0_1__m0 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7074 | 0.5773 | 470.6596 |
| 16 | combined:context_selected_definition_source:before_after | combined_context_selected_definition_source:selection_top_k3__a0_1__m0_005 | tfidf_cosine | masked_sentence | contextualized_source_plus_definition_rows | context_selected_top_k_mean | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7074 | 0.5773 | 470.6596 |
| 17 | llm_v2:source_plus_definition:max | llm_v2_source_plus_definition_max:a0_1__m0 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7235 | 0.5821 | 470.6596 |
| 18 | llm_v2:source_plus_definition:max | llm_v2_source_plus_definition_max:a0_1__m0_005 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 47 | 58.77% | 0.7235 | 0.5821 | 470.6596 |
| 19 | llm_v2:source_plus_definition:max | llm_v2_source_plus_definition_max:a0_1__m0_02 | tfidf_cosine | masked_sentence | source_plus_definition_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7235 | 0.5821 | 480.6737 |
| 20 | llm_v2:source_rows:max | llm_v2_source_rows_max:a0_1__m0 | tfidf_cosine | masked_sentence | source_rows_separate | max_row_score | active_minus_strongest_shadow | phrase_override | normal | 0 | 48 | 57.89% | 0.7102 | 0.5695 | 480.6737 |

## Overfitting Checks

- Split policy: `deterministic_case_id_hash_modulo` (locked remainders `[0]`)
- `combined_definition_example_plus_source_max:a0_1__m0`: discovery objective `250.5170`, locked objective `120.5243`, worst leave-one-family objective `370.5364`
- `combined_definition_example_plus_source_max:a0_1__m0_005`: discovery objective `250.5170`, locked objective `120.5243`, worst leave-one-family objective `370.5364`
- `combined_definition_example_plus_source_max:a0_1__m0_02`: discovery objective `260.5377`, locked objective `120.5243`, worst leave-one-family objective `380.5509`
- `combined_context_selected_definition_source:selection_top_k1__a0_05__m0`: discovery objective `6270.6435`, locked objective `120.5243`, worst leave-one-family objective `6390.6251`
- `combined_context_selected_definition_source:selection_top_k1__a0_05__m0_005`: discovery objective `6270.6435`, locked objective `120.5243`, worst leave-one-family objective `6390.6251`
- `llm_v2_source_rows_max:a0_05__m0_005`: discovery objective `7290.6925`, locked objective `120.5243`, worst leave-one-family objective `7410.6595`
- `llm_v2_source_rows_max:a0_05__m0`: discovery objective `8290.7002`, locked objective `120.5243`, worst leave-one-family objective `8410.6649`
- `llm_v2_definition_example_plus_source_max:a0_1__m0`: discovery objective `250.5170`, locked objective `140.6117`, worst leave-one-family objective `390.5654`
- `llm_v2_definition_example_plus_source_max:a0_1__m0_005`: discovery objective `250.5170`, locked objective `140.6117`, worst leave-one-family objective `390.5654`
- `llm_v2_definition_example_plus_source_max:a0_1__m0_02`: discovery objective `260.5377`, locked objective `140.6117`, worst leave-one-family objective `400.5799`
