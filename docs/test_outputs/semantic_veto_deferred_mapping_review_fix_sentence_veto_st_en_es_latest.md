# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T22:37:49Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_deferred_mapping_review_fix_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `66.7%`
- Replace precision / recall: `57.1%` / `66.7%`
- Harmful replace / false abstain: `33.3%` / `33.3%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `83.3%`
- Predicted replace rate: `46.7%`
- Phrase preemption hit rate / precision: `0.0%` / `n/a`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| bar -> cercar vs taberna, barra | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| crack -> grieta vs broma, chasquido | 5 | 40.0% | 0.0% | 33.3% | 50.0% |
| offset -> distancia vs compensar, compensación | 5 | 80.0% | 100.0% | 33.3% | 75.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 6 | 66.7% | 66.7% | n/a | 66.7% |
| shadow | 6 | 100.0% | n/a | 0.0% | 83.3% |
| none | 3 | 0.0% | n/a | 100.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_reviewed_user_review_pending | 15 | 66.7% | 66.7% | 33.3% | 75.0% |
| en_es_full_family_deferred_mapping_review_fix_v1 | 15 | 66.7% | 66.7% | 33.3% | 75.0% |
| polysemy:high_10_plus | 15 | 66.7% | 66.7% | 33.3% | 75.0% |
| pos_shape:cross_pos_polysemy | 15 | 66.7% | 66.7% | 33.3% | 75.0% |
| no_winner_subtype:not_applicable | 12 | 83.3% | 66.7% | 0.0% | 75.0% |
| deferred_mapping_fixed_corrected_active_sense | 10 | 80.0% | 100.0% | 33.3% | 87.5% |
| source_cell:source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy | 10 | 60.0% | 50.0% | 33.3% | 75.0% |
| source_zipf:zipf_4_to_5_common | 10 | 60.0% | 50.0% | 33.3% | 75.0% |
| positive_active | 6 | 66.7% | 66.7% | n/a | 66.7% |
| shadow_negative | 6 | 100.0% | n/a | 0.0% | 83.3% |
| representative_slot_replacement_for_rejected_mapping | 5 | 40.0% | 0.0% | 33.3% | 50.0% |
| source_cell:source_zipf=zipf_3_to_4_mid::polysemy=high_10_plus::pos_shape=cross_pos_polysemy | 5 | 80.0% | 100.0% | 33.3% | 75.0% |

## Failure Samples

### Harmful replace

- `en-es:full-family-deferred-review-fix:bar:cercar:005` `replace` vs `abstain` | trigger `bar` | margin `0.040`
  sentence: The settings page showed bar as the value of the layout test.
- `en-es:full-family-deferred-review-fix:offset:distancia:005` `replace` vs `abstain` | trigger `offset` | margin `0.023`
  sentence: The debug field named offset stayed empty after import.
- `en-es:full-family-deferred-review-fix:crack:grieta:005` `replace` vs `abstain` | trigger `crack` | margin `0.002`
  sentence: The saved search tag crack appeared in the sidebar.

### False abstain

- `en-es:full-family-deferred-review-fix:crack:grieta:001` `abstain` vs `replace` | trigger `crack` | margin `-0.049`
  sentence: A thin crack ran across the windshield.
- `en-es:full-family-deferred-review-fix:crack:grieta:002` `abstain` vs `replace` | trigger `crack` | margin `-0.021`
  sentence: Moisture seeped through a crack in the basement wall.

### Winner errors

- `en-es:full-family-deferred-review-fix:offset:distancia:003` `abstain` vs `abstain` | trigger `offset` | margin `-0.165`
  sentence: The rebate can offset the cost of the repairs.
- `en-es:full-family-deferred-review-fix:crack:grieta:001` `abstain` vs `replace` | trigger `crack` | margin `-0.049`
  sentence: A thin crack ran across the windshield.
- `en-es:full-family-deferred-review-fix:crack:grieta:002` `abstain` vs `replace` | trigger `crack` | margin `-0.021`
  sentence: Moisture seeped through a crack in the basement wall.
