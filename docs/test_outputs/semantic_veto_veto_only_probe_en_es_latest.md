# en-es Semantic Veto Veto-Only Probe

- Status: `ok`
- Decision: `veto_only_product_target_pass_found`
- Generated: `2026-05-01T01:41:49Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Matrix: `docs/test_outputs/semantic_decision_rule_matrix_en_es_latest.json`
- Rows evaluated: `7722`
- Product target pass rows: `117`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `input_case_results_read` | `2470` |
| `selected_config_count` | `26` |
| `policy_rows_emitted` | `7722` |
| `phrase_modes` | `shadow_only, shadow_or_phrase, shadow_or_phrase_score` |
| `shadow_lead_grid` | `-0.05, -0.02, 0.0, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2` |
| `shadow_score_grid` | `0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65` |

## Top Veto-Only Rows

| Config | Scorer | Context | Evidence | Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.0 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.0 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.02 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.02 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.05 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.05 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.1 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.1 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.2 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.2 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.35 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.35 | 81.6% | 94.7% | 69.6 | pass |

## Passing Rows

| Config | Scorer | Context | Evidence | Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.0 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.0 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.02 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.02 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.05 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.05 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.1 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.1 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.2 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.2 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.35 | 81.6% | 94.7% | 69.6 | pass |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase_score | 0.02 | 0.35 | 81.6% | 94.7% | 69.6 | pass |

## Best By Source Config

| Config | Scorer | Context | Evidence | Phrase mode | Shadow lead | Shadow score | Pos allow | Neg abstain | Utility | Target |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| context_masked_window_tfidf_all_margin | tfidf_cosine | masked_window | all_evidence_text | shadow_only | -0.05 | 0.0 | 21.1% | 100.0% | 41.6 | fail |
| context_raw_sentence_tfidf_all_margin | tfidf_cosine | raw_sentence | all_evidence_text | shadow_or_phrase | -0.05 | 0.02 | 31.6% | 93.0% | 41.6 | fail |
| context_raw_window_tfidf_all_margin | tfidf_cosine | raw_window | all_evidence_text | shadow_or_phrase | -0.05 | 0.02 | 34.2% | 93.0% | 43.0 | fail |
| control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.02 | 0.0 | 81.6% | 94.7% | 69.6 | pass |
| control_tfidf_masked_all_margin_phrase_override | tfidf_cosine | masked_sentence | all_evidence_text | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| decision_pairwise_all_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| decision_pairwise_most_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| decision_ratio_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| decision_softmax_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| negative_active_only_over_replace | tfidf_cosine | masked_sentence | all_evidence_text | shadow_only | -0.05 | 0.0 | 26.3% | 100.0% | 44.4 | fail |
| negative_no_shadow_over_replace | tfidf_cosine | masked_sentence | all_evidence_text | shadow_only | -0.05 | 0.0 | 26.3% | 100.0% | 44.4 | fail |
| negative_shadow_only_over_abstain | tfidf_cosine | masked_sentence | all_evidence_text | shadow_only | -0.05 | 0.0 | 0.0% | 100.0% | 30.4 | fail |
| negative_shuffled_labels_collapse | tfidf_cosine | masked_sentence | all_evidence_text | shadow_only | -0.05 | 0.0 | 0.0% | 86.0% | 19.2 | fail |
| negative_target_lemma_lexical_leakage | tfidf_cosine | masked_sentence | target_lemma_only | shadow_only | -0.05 | 0.0 | 0.0% | 100.0% | 30.4 | fail |
| phrase_as_shadow_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_only | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| phrase_first_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| phrase_semantic_only_weighted_topk | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| repr_gloss_text_tfidf_margin | tfidf_cosine | masked_sentence | gloss_text | shadow_only | -0.05 | 0.0 | 2.6% | 98.2% | 30.4 | fail |
| repr_sense_gloss_bundle_tfidf_margin | tfidf_cosine | masked_sentence | sense_gloss_bundle | shadow_only | -0.02 | 0.0 | 15.8% | 98.2% | 37.4 | fail |
| repr_sense_label_tfidf_margin | tfidf_cosine | masked_sentence | sense_label | shadow_only | -0.02 | 0.0 | 13.2% | 98.2% | 36.0 | fail |
| repr_separate_rows_tfidf_definition_agreement_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_only | -0.02 | 0.0 | 5.3% | 98.2% | 31.8 | fail |
| repr_separate_rows_tfidf_max_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_only | -0.05 | 0.0 | 31.6% | 98.2% | 45.8 | fail |
| repr_separate_rows_tfidf_mean_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| repr_separate_rows_tfidf_topk_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| repr_separate_rows_tfidf_weighted_topk_margin | tfidf_cosine | masked_sentence | definition_and_example_rows_separate | shadow_or_phrase | 0.0 | 0.0 | 42.1% | 89.5% | 44.4 | fail |
| scorer_token_masked_all_margin | token_jaccard | masked_sentence | all_evidence_text | shadow_or_phrase | -0.02 | 0.0 | 34.2% | 91.2% | 41.6 | fail |

## Failure Samples For Best Row

| Case | Trigger | Gold | Winner | Outcome | Reason | Active | Shadow | Lead | Sentence |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| en-es:sentence-veto:plant:002 | plant | replace | active | positive_abstain | shadow_lead | 0.5818 | 0.602 | 0.0202 | The plant needs more sunlight in the afternoon. |
| en-es:sentence-veto:park:001 | park | replace | active | positive_abstain | shadow_lead | 0.5444 | 0.586 | 0.0417 | The children ran through the park after school. |
| en-es:sentence-veto:drink:002 | drink | replace | active | positive_abstain | shadow_lead | 0.6423 | 0.6631 | 0.0208 | I ordered a drink at the bar. |
| en-es:sentence-veto:play:002 | play | replace | active | positive_abstain | shadow_lead | 0.4924 | 0.5219 | 0.0295 | The play opened last night. |
| en-es:sentence-veto:play:005 | play | abstain | none | negative_allow |  | 0.5591 | 0.4937 | -0.0654 | The scandal will play out over several weeks. |
| en-es:sentence-veto:check:002 | check | replace | active | positive_abstain | shadow_lead | 0.5522 | 0.597 | 0.0448 | The check cleared after the holiday weekend. |
| en-es:sentence-veto:report:001 | report | replace | active | positive_abstain | shadow_lead | 0.5676 | 0.6155 | 0.0479 | The report arrived this morning. |
| en-es:sentence-veto:report:002 | report | replace | active | positive_abstain | shadow_lead | 0.5044 | 0.5749 | 0.0705 | The report was delayed until Friday. |
| en-es:sentence-veto:report:004 | report | abstain | shadow | negative_allow |  | 0.6038 | 0.6208 | 0.017 | Analysts report slower growth this quarter. |
| en-es:sentence-veto:report:005 | report | abstain | none | negative_allow |  | 0.6365 | 0.6484 | 0.0119 | Please report back after the conference. |

## Recommendation

- The allow-by-default veto-only framing found rows that meet the configured product target on frozen v10 matrix traces.
- Before runtime promotion, validate the best row on stress lanes and a broader representative lane.
- Inspect negative allows in the best row to decide which blocker evidence should be expanded next.
