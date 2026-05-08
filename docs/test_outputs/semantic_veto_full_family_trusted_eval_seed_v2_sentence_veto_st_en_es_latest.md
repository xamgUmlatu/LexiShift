# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T22:45:42Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v2.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `69.0%`
- Replace precision / recall: `65.2%` / `75.0%`
- Harmful replace / false abstain: `36.4%` / `25.0%`
- Winner accuracy / shadow-winner accuracy: `81.2%` / `91.7%`
- Predicted replace rate: `54.8%`
- Phrase preemption hit rate / precision: `2.4%` / `0.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| bar -> cercar vs taberna, barra | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| crack -> grieta vs broma, chasquido | 5 | 40.0% | 0.0% | 33.3% | 50.0% |
| offset -> distancia vs compensar, compensación | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| bouillon -> caldo | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| break -> quebrar vs interrumpir, oportunidad | 5 | 60.0% | 50.0% | 33.3% | 75.0% |
| bridle -> reprimir vs ofenderse, brida | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| control -> gobernar vs controlar, grupo de control | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| december -> diciembre | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| dentist -> dentista | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| emotion -> emoción | 3 | 66.7% | 100.0% | 100.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 20 | 75.0% | 75.0% | n/a | 75.0% |
| shadow | 12 | 100.0% | n/a | 0.0% | 91.7% |
| none | 10 | 20.0% | n/a | 80.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| approved_by_user | 42 | 69.0% | 75.0% | 36.4% | 81.2% |
| en_es_full_family_trusted_eval_seed_v2 | 42 | 69.0% | 75.0% | 36.4% | 81.2% |
| trusted | 42 | 69.0% | 75.0% | 36.4% | 81.2% |
| trusted_eval_seed_v2 | 42 | 69.0% | 75.0% | 36.4% | 81.2% |
| no_winner_subtype:not_applicable | 32 | 84.4% | 75.0% | 0.0% | 81.2% |
| pos_shape:cross_pos_polysemy | 30 | 70.0% | 58.3% | 22.2% | 75.0% |
| carried_forward_from_v1 | 27 | 70.4% | 78.6% | 38.5% | 85.0% |
| polysemy:high_10_plus | 25 | 72.0% | 70.0% | 26.7% | 80.0% |
| target_zipf:zipf_3_to_4_mid | 21 | 57.1% | 50.0% | 36.4% | 68.8% |
| positive_active | 20 | 75.0% | 75.0% | n/a | 75.0% |
| active_sense_corrected | 15 | 73.3% | 50.0% | 11.1% | 75.0% |
| newly_approved_deferred_fix | 15 | 66.7% | 66.7% | 33.3% | 75.0% |

## Failure Samples

### Harmful replace

- `en-es:full-family-repaired-pilot:break:quebrar:005` `replace` vs `abstain` | trigger `break` | margin `0.013`
  sentence: The keyboard shortcut was labeled Break on the settings page.
- `en-es:full-family-repaired-pilot:december:diciembre:003` `replace` vs `abstain` | trigger `december` | margin `0.562`
  sentence: The album December stayed on the playlist for weeks.
- `en-es:full-family-repaired-pilot:emotion:emoci-n:003` `replace` vs `abstain` | trigger `emotion` | margin `0.491`
  sentence: The startup Emotion released a new design tool.
- `en-es:full-family-repaired-pilot:dentist:dentista:003` `replace` vs `abstain` | trigger `dentist` | margin `0.482`
  sentence: The game Dentist Pro appeared in the app store.
- `en-es:full-family-repaired-pilot:bouillon:caldo:003` `replace` vs `abstain` | trigger `bouillon` | margin `0.568`
  sentence: The restaurant Bouillon opened a second location downtown.
- `en-es:full-family-deferred-review-fix:bar:cercar:005` `replace` vs `abstain` | trigger `bar` | margin `0.040`
  sentence: The settings page showed bar as the value of the layout test.

### False abstain

- `en-es:full-family-repaired-pilot:break:quebrar:002` `abstain` vs `replace` | trigger `break` | margin `-0.078`
  sentence: A cheap lock can break under sudden force.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.085`
  sentence: The manager had to bridle his frustration after the call.
- `en-es:full-family-deferred-review-fix:crack:grieta:001` `abstain` vs `replace` | trigger `crack` | margin `-0.049`
  sentence: A thin crack ran across the windshield.
- `en-es:full-family-deferred-review-fix:crack:grieta:002` `abstain` vs `replace` | trigger `crack` | margin `-0.021`
  sentence: Moisture seeped through a crack in the basement wall.

### Winner errors

- `en-es:full-family-repaired-pilot:break:quebrar:002` `abstain` vs `replace` | trigger `break` | margin `-0.078`
  sentence: A cheap lock can break under sudden force.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.085`
  sentence: The manager had to bridle his frustration after the call.
- `en-es:full-family-deferred-review-fix:offset:distancia:003` `abstain` vs `abstain` | trigger `offset` | margin `-0.165`
  sentence: The rebate can offset the cost of the repairs.
- `en-es:full-family-deferred-review-fix:crack:grieta:001` `abstain` vs `replace` | trigger `crack` | margin `-0.049`
  sentence: A thin crack ran across the windshield.
- `en-es:full-family-deferred-review-fix:crack:grieta:002` `abstain` vs `replace` | trigger `crack` | margin `-0.021`
  sentence: Moisture seeped through a crack in the basement wall.
