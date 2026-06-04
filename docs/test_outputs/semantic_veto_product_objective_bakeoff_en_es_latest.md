# en-es Semantic Veto Product Objective Bakeoff

- Status: `review`
- Decision: `historical_product_target_not_met`
- Generated: `2026-05-01T01:03:28Z`
- Policy: `docs/test_inputs/semantic_veto_product_quality_policy_en_es.json`
- Sources: `2`
- Rows ranked: `3098`
- Product target pass rows: `0`

## E2E Checks

| Check | Value |
| --- | --- |
| `calculus_source` | `scripts/testing/semantic_veto_product_quality_en_es.py::score_product_outcome_counts` |
| `source_artifacts_read` | `2` |
| `input_rows_read` | `3098` |
| `product_rows_emitted` | `3098` |
| `all_source_rows_read` | `True` |
| `issue_count` | `0` |

## Sources

| Source | Type | Input rows | Product rows | Target pass | Best config | Best pos allow | Best neg abstain | Best utility |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| semantic_routing_sentence_veto_sweep | sentence_veto_sweep | 3072 | 3072 | 0 | tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | 34.2% | 100.0% | 48.6 |
| semantic_decision_rule_matrix_en_es | decision_rule_matrix | 26 | 26 | 0 | control_st_masked_all_margin_phrase_override | 68.4% | 98.2% | 65.4 |

## Best Product Rank Rows

| Source | Config | Scorer | Evidence | Rule | Pos allow | Neg abstain | Utility | Target | Distance |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| semantic_decision_rule_matrix_en_es | control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | all_evidence_text | active_minus_strongest_shadow | 68.4% | 98.2% | 65.4 | fail | 0.1158 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 34.2% | 100.0% | 48.6 | fail | 0.4579 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | tfidf_cosine | all_evidence_text | off | 34.2% | 100.0% | 48.6 | fail | 0.4579 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.05 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05 | tfidf_cosine | all_evidence_text | off | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.05 | tfidf_cosine | all_evidence_text | off | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_window:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_window:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | tfidf_cosine | all_evidence_text | off | 31.6% | 100.0% | 47.2 | fail | 0.4842 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_window:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 28.9% | 100.0% | 45.8 | fail | 0.5105 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_window:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.05 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 28.9% | 100.0% | 45.8 | fail | 0.5105 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_window:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05 | tfidf_cosine | all_evidence_text | off | 28.9% | 100.0% | 45.8 | fail | 0.5105 |

## Closest Target Shape Rows

| Source | Config | Scorer | Evidence | Rule | Pos allow | Neg abstain | Utility | Target | Distance |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:raw_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 81.6% | 49.1% | 33.2 | fail | 0.0088 |
| semantic_decision_rule_matrix_en_es | context_raw_sentence_tfidf_all_margin | tfidf_cosine | all_evidence_text | active_minus_strongest_shadow | 79.0% | 49.1% | 31.8 | fail | 0.0193 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:raw_sentence:all_evidence_text:p=noun_family_frame_guard:r=off:a=0.00:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 79.0% | 49.1% | 31.8 | fail | 0.0193 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:raw_window:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 81.6% | 47.4% | 31.8 | fail | 0.0263 |
| semantic_decision_rule_matrix_en_es | context_raw_window_tfidf_all_margin | tfidf_cosine | all_evidence_text | active_minus_strongest_shadow | 79.0% | 47.4% | 30.4 | fail | 0.0368 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:raw_window:all_evidence_text:p=noun_family_frame_guard:r=off:a=0.00:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 79.0% | 47.4% | 30.4 | fail | 0.0368 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_sentence:sense_label:p=noun_family_frame_guard:r=off:a=0.00:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_sentence:sense_label:p=noun_family_frame_guard:r=off:a=0.05:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_sentence:sense_label:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_sentence:sense_label:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_window:sense_label:p=noun_family_frame_guard:r=off:a=0.00:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |
| semantic_routing_sentence_veto_sweep | token_jaccard:raw_window:sense_label:p=noun_family_frame_guard:r=off:a=0.05:m=0.00 | token_jaccard | sense_label | noun_family_frame_guard | 76.3% | 49.1% | 30.4 | fail | 0.0456 |

## Best By Source

| Source | Config | Scorer | Evidence | Rule | Pos allow | Neg abstain | Utility | Target | Distance |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| semantic_decision_rule_matrix_en_es | control_st_masked_all_margin_phrase_override | sentence_transformer_cosine | all_evidence_text | active_minus_strongest_shadow | 68.4% | 98.2% | 65.4 | fail | 0.1158 |
| semantic_routing_sentence_veto_sweep | tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00 | tfidf_cosine | all_evidence_text | noun_family_frame_guard | 34.2% | 100.0% | 48.6 | fail | 0.4579 |

## Recommendation

- No historical sweep or matrix row meets the configured product target.
- Treat the incumbent as a baseline under the old objective, not as proven best for product acceptance.
- Use the closest-target rows to decide whether the next expansion should prioritize permissive decision rules, source evidence, or broader representative data.
