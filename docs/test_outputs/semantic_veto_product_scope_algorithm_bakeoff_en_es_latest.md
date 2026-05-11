# en-es Semantic Veto Product-Scope Algorithm Bakeoff

- Status: `ok`
- Decision: `product_scope_algorithm_candidate_found`
- Generated: `2026-05-09T04:44:05Z`
- Product-scope rows retained: `140`
- Diagnostic label rows excluded: `49`
- Candidate rows: `1056`
- Product target pass rows: `460`

## E2E Checks

| Check | Value |
| --- | --- |
| `product_scope_filter_applied` | `True` |
| `diagnostic_label_rows_excluded` | `49` |
| `product_scope_rows_retained` | `140` |
| `trace_sources_read` | `2` |
| `candidate_rows_emitted` | `1056` |
| `score_product_outcome_counts_used` | `True` |
| `active_rescue_backup_scores_available` | `True` |
| `issue_count` | `0` |

## Best Rows

| Config | Scorer | Phrase | Rescue | min active | margin | Pos allow | Neg abstain | Harm share | Utility | vs no veto | Target |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.000:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.0 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.005:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.005 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.010:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.01 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.015:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.015 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.020:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.02 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.025:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.025 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.030:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.03 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.035:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.035 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.040:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.04 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.050:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.05 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.075:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.075 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.100:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.1 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.000:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.0 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.005:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.005 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.010:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.01 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.015:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.015 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.020:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.02 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.025:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.025 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.030:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.03 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.035:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.035 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |

## Current Policy-Like Rows

| Config | Scorer | Phrase | Rescue | min active | margin | Pos allow | Neg abstain | Harm share | Utility | vs no veto | Target |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.000:m=0.000 | sentence_transformer_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.0 | 0.0 | 85.7% | 92.9% | 3.5% | 107.8 | 35.0 | pass |
| tfidf_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=sense_label_near_tie_active_rescue:a=0.050:m=0.000 | tfidf_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.0 | 5.1% | 97.6% | 16.7% | 0.0 | -72.8 | fail |

## Best By Scorer

| Config | Scorer | Phrase | Rescue | min active | margin | Pos allow | Neg abstain | Harm share | Utility | vs no veto | Target |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.000:m=-0.025 | sentence_transformer_cosine | noun_family_frame_guard | off | 0.0 | -0.025 | 92.9% | 88.1% | 5.2% | 114.8 | 42.0 | pass |
| tfidf_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.000:m=-0.005 | tfidf_cosine | noun_family_frame_guard | off | 0.0 | -0.005 | 91.8% | 50.0% | 18.9% | 91.0 | 18.2 | pass |

## Failure Samples

### `sentence_transformer_cosine:masked_sentence:all_evidence_text:phrase=noun_family_frame_guard:rescue=off:a=0.000:m=-0.025`

| Case | Outcome | Scores | Sentence |
| --- | --- | --- | --- |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `positive_abstain` | `a=0.6005; s=0.7619; m=-0.1613` | She tried to bridle her anger during the meeting. |
| `en-es:full-family-repaired-full:bridle:reprimir:002` | `positive_abstain` | `a=0.5967; s=0.6994; m=-0.1026` | The lawyer had to bridle his frustration after the ruling. |
| `en-es:full-family-repaired-full:december:diciembre:001` | `positive_abstain` | `a=0.5546; s=0.0; m=0.5546` | The conference moved to December after the venue delay. |
| `en-es:full-family-repaired-full:continue:durar:003` | `negative_allow` | `a=0.6773; s=0.6743; m=0.0029` | Please continue reading the next section. |
| `en-es:full-family-repaired-full:continue:durar:004` | `negative_allow` | `a=0.6803; s=0.667; m=0.0132` | The teams will continue play after the delay. |
| `en-es:full-family-repaired-full:chic:elegante:003` | `negative_allow` | `a=0.6094; s=0.6336; m=-0.0242` | The advertisement promised effortless Parisian chic. |
| `en-es:full-family-repaired-full:cite:mencionar:003` | `negative_allow` | `a=0.6115; s=0.6121; m=-0.0006` | The officer may cite the driver for speeding. |
| `en-es:full-family-repaired-full:snore:roncar:002` | `positive_abstain` | `a=0.5895; s=0.6276; m=-0.0381` | She could hear her roommate snore through the wall. |
| `en-es:full-family-repaired-full:current:contempor-neo:002` | `positive_abstain` | `a=0.5644; s=0.636; m=-0.0716` | Current research focuses on smaller batteries. |
| `en-es:full-family-repaired-full:parrot:loro:002` | `positive_abstain` | `a=0.6259; s=0.6878; m=-0.0618` | The parrot repeated the visitor's greeting. |
| `en-es:full-family-repaired-full:acceptable:razonable:004` | `negative_allow` | `a=0.6174; s=0.5902; m=0.0271` | The sample was acceptable for laboratory testing. |
| `en-es:full-family-repaired-full:health:salud:002` | `positive_abstain` | `a=0.5694; s=0.0; m=0.5694` | The clinic tracks each patient's health over time. |

### `tfidf_cosine:masked_sentence:all_evidence_text:phrase=off:rescue=off:a=0.000:m=-0.050`

| Case | Outcome | Scores | Sentence |
| --- | --- | --- | --- |
| `en-es:full-family-repaired-full:break:quebrar:003` | `negative_allow` | `a=0.0; s=0.0107; m=-0.0107` | A news alert can break the broadcast without warning. |
| `en-es:full-family-repaired-full:bar:cercar:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | They met at the bar after work. |
| `en-es:full-family-repaired-full:bar:cercar:004` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The violin enters on the second bar of the song. |
| `en-es:full-family-repaired-full:offset:distancia:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The rebate helped offset the higher shipping cost. |
| `en-es:full-family-repaired-full:offset:distancia:004` | `negative_allow` | `a=0.0185; s=0.0349; m=-0.0164` | The invoice showed a small offset for the returned item. |
| `en-es:full-family-repaired-full:bridle:reprimir:001` | `positive_abstain` | `a=0.0; s=0.0791; m=-0.0791` | She tried to bridle her anger during the meeting. |
| `en-es:full-family-repaired-full:bridle:reprimir:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The rider checked the bridle before the parade. |
| `en-es:full-family-repaired-full:bridle:reprimir:004` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | He began to bridle at the accusation. |
| `en-es:full-family-repaired-full:control:gobernar:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | Use the slider to control the volume. |
| `en-es:full-family-repaired-full:control:gobernar:004` | `negative_allow` | `a=0.1121; s=0.1045; m=0.0076` | The study included a control group and a treatment group. |
| `en-es:full-family-repaired-full:stall:cuadra:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The committee tried to stall the vote until Friday. |
| `en-es:full-family-repaired-full:stall:cuadra:004` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The old truck may stall on the hill. |
| `en-es:full-family-repaired-full:continue:durar:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | Please continue reading the next section. |
| `en-es:full-family-repaired-full:continue:durar:004` | `negative_allow` | `a=0.0; s=0.0399; m=-0.0399` | The teams will continue play after the delay. |
| `en-es:full-family-repaired-full:chic:elegante:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The advertisement promised effortless Parisian chic. |
| `en-es:full-family-repaired-full:billow:oleaje:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | Smoke began to billow from the warehouse. |
| `en-es:full-family-repaired-full:billow:oleaje:004` | `negative_allow` | `a=0.0; s=0.0385; m=-0.0385` | The curtain started to billow in the wind. |
| `en-es:full-family-repaired-full:recover:sanar:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The technician helped recover the deleted file. |
| `en-es:full-family-repaired-full:recover:sanar:004` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | They hired a shop to recover the old chair. |
| `en-es:full-family-repaired-full:cite:mencionar:003` | `negative_allow` | `a=0.0; s=0.0; m=0.0` | The officer may cite the driver for speeding. |

## Limitations

- `product_scope_filter_only_removes_the_current_synthetic_internal_project_code_template`
- `filtered_repaired_full_is_still_not_a_final_browsing_distribution`
- `threshold_selection_here_is_discovery_research_not_runtime_promotion`
- `band_and_llm_allocation_sweeps_must_be_rerun_after_selecting_candidate_rows`

## Next Steps

- Use the top product-scope candidate rows as inputs to the corrected band and heuristic sweeps.
- Carry at least one conservative row and one high-recall soft-assist row forward as comparators.
- Do not spend on broad LLM generation until the corrected band read is regenerated.
