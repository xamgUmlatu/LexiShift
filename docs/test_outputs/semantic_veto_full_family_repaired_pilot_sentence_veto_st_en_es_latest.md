# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T21:56:09Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_pilot_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `70.4%`
- Replace precision / recall: `68.8%` / `78.6%`
- Harmful replace / false abstain: `38.5%` / `21.4%`
- Winner accuracy / shadow-winner accuracy: `85.0%` / `100.0%`
- Predicted replace rate: `59.3%`
- Phrase preemption hit rate / precision: `3.7%` / `0.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
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
| active | 14 | 78.6% | 78.6% | n/a | 78.6% |
| shadow | 6 | 100.0% | n/a | 0.0% | 100.0% |
| none | 7 | 28.6% | n/a | 71.4% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_repaired_user_review_pending | 27 | 70.4% | 78.6% | 38.5% | 85.0% |
| en_es_full_family_repaired_pilot_v1 | 27 | 70.4% | 78.6% | 38.5% | 85.0% |
| no_winner_subtype:not_applicable | 20 | 85.0% | 78.6% | 0.0% | 85.0% |
| target_zipf:zipf_3_to_4_mid | 16 | 62.5% | 62.5% | 37.5% | 75.0% |
| active_sense_corrected | 15 | 73.3% | 50.0% | 11.1% | 75.0% |
| pos_shape:cross_pos_polysemy | 15 | 73.3% | 50.0% | 11.1% | 75.0% |
| positive_active | 14 | 78.6% | 78.6% | n/a | 78.6% |
| source_zipf:zipf_5_plus_very_common | 13 | 76.9% | 83.3% | 28.6% | 90.0% |
| aligned_mapping_contexts_rewritten | 12 | 66.7% | 100.0% | 100.0% | 100.0% |
| polysemy:low_1_to_3 | 12 | 66.7% | 100.0% | 100.0% | 100.0% |
| pos_shape:single_sense | 12 | 66.7% | 100.0% | 100.0% | 100.0% |
| polysemy:high_10_plus | 10 | 80.0% | 75.0% | 16.7% | 87.5% |

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

### False abstain

- `en-es:full-family-repaired-pilot:break:quebrar:002` `abstain` vs `replace` | trigger `break` | margin `-0.078`
  sentence: A cheap lock can break under sudden force.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.085`
  sentence: The manager had to bridle his frustration after the call.

### Winner errors

- `en-es:full-family-repaired-pilot:break:quebrar:002` `abstain` vs `replace` | trigger `break` | margin `-0.078`
  sentence: A cheap lock can break under sudden force.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.085`
  sentence: The manager had to bridle his frustration after the call.
