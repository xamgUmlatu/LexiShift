# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T22:37:49Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_deferred_mapping_review_fix_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `66.7%`
- Replace precision / recall: `66.7%` / `33.3%`
- Harmful replace / false abstain: `11.1%` / `66.7%`
- Winner accuracy / shadow-winner accuracy: `41.7%` / `0.0%`
- Predicted replace rate: `20.0%`
- Phrase preemption hit rate / precision: `0.0%` / `n/a`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| bar -> cercar vs taberna, barra | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| crack -> grieta vs broma, chasquido | 5 | 100.0% | 100.0% | 0.0% | 50.0% |
| offset -> distancia vs compensar, compensación | 5 | 40.0% | 0.0% | 33.3% | 50.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 6 | 33.3% | 33.3% | n/a | 83.3% |
| shadow | 6 | 83.3% | n/a | 16.7% | 0.0% |
| none | 3 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_reviewed_user_review_pending | 15 | 66.7% | 33.3% | 11.1% | 41.7% |
| en_es_full_family_deferred_mapping_review_fix_v1 | 15 | 66.7% | 33.3% | 11.1% | 41.7% |
| polysemy:high_10_plus | 15 | 66.7% | 33.3% | 11.1% | 41.7% |
| pos_shape:cross_pos_polysemy | 15 | 66.7% | 33.3% | 11.1% | 41.7% |
| no_winner_subtype:not_applicable | 12 | 58.3% | 33.3% | 16.7% | 41.7% |
| deferred_mapping_fixed_corrected_active_sense | 10 | 50.0% | 0.0% | 16.7% | 37.5% |
| source_cell:source_zipf=zipf_4_to_5_common::polysemy=high_10_plus::pos_shape=cross_pos_polysemy | 10 | 80.0% | 50.0% | 0.0% | 37.5% |
| source_zipf:zipf_4_to_5_common | 10 | 80.0% | 50.0% | 0.0% | 37.5% |
| positive_active | 6 | 33.3% | 33.3% | n/a | 83.3% |
| shadow_negative | 6 | 83.3% | n/a | 16.7% | 0.0% |
| representative_slot_replacement_for_rejected_mapping | 5 | 100.0% | 100.0% | 0.0% | 50.0% |
| source_cell:source_zipf=zipf_3_to_4_mid::polysemy=high_10_plus::pos_shape=cross_pos_polysemy | 5 | 40.0% | 0.0% | 33.3% | 50.0% |

## Failure Samples

### Harmful replace

- `en-es:full-family-deferred-review-fix:offset:distancia:003` `replace` vs `abstain` | trigger `offset` | margin `0.051`
  sentence: The rebate can offset the cost of the repairs.

### False abstain

- `en-es:full-family-deferred-review-fix:bar:cercar:001` `abstain` vs `replace` | trigger `bar` | margin `0.000`
  sentence: The crew will bar the service entrance with temporary fencing.
- `en-es:full-family-deferred-review-fix:bar:cercar:002` `abstain` vs `replace` | trigger `bar` | margin `-0.002`
  sentence: A locked gate can bar the narrow path to the reservoir.
- `en-es:full-family-deferred-review-fix:offset:distancia:001` `abstain` vs `replace` | trigger `offset` | margin `0.017`
  sentence: Measure the offset from the centerline before drilling.
- `en-es:full-family-deferred-review-fix:offset:distancia:002` `abstain` vs `replace` | trigger `offset` | margin `0.005`
  sentence: A small offset between the sensor and the marker caused the error.

### Winner errors

- `en-es:full-family-deferred-review-fix:bar:cercar:002` `abstain` vs `replace` | trigger `bar` | margin `-0.002`
  sentence: A locked gate can bar the narrow path to the reservoir.
- `en-es:full-family-deferred-review-fix:bar:cercar:003` `abstain` vs `abstain` | trigger `bar` | margin `0.000`
  sentence: She ordered mineral water at the bar after dinner.
- `en-es:full-family-deferred-review-fix:bar:cercar:004` `abstain` vs `abstain` | trigger `bar` | margin `-0.003`
  sentence: The mechanic welded a steel bar across the frame.
- `en-es:full-family-deferred-review-fix:offset:distancia:003` `replace` vs `abstain` | trigger `offset` | margin `0.051`
  sentence: The rebate can offset the cost of the repairs.
- `en-es:full-family-deferred-review-fix:offset:distancia:004` `abstain` vs `abstain` | trigger `offset` | margin `0.015`
  sentence: The refund acted as an offset against the unpaid balance.
- `en-es:full-family-deferred-review-fix:crack:grieta:003` `abstain` vs `abstain` | trigger `crack` | margin `-0.049`
  sentence: His crack about the budget made the room laugh.
