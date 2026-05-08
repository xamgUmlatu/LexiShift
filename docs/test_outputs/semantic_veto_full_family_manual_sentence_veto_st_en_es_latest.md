# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T20:20:21Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_representative_manual_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `72.8%`
- Replace precision / recall: `58.1%` / `83.6%`
- Harmful replace / false abstain: `33.1%` / `16.4%`
- Winner accuracy / shadow-winner accuracy: `84.5%` / `85.3%`
- Predicted replace rate: `51.0%`
- Phrase preemption hit rate / precision: `0.0%` / `n/a`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| aberration -> equivocación vs aberration alternate sense 1, aberration alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| acceptable -> razonable vs acceptable alternate sense 1, acceptable alternate sense 2 | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| adder -> víbora vs adder alternate sense 1, adder alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| adjoining -> contiguo | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| adjoining -> vecino | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| altitude -> elevación vs altitude alternate sense 1, altitude alternate sense 2 | 4 | 50.0% | 0.0% | 33.3% | 66.7% |
| american -> americano vs american alternate sense 1, american alternate sense 2 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| among -> entre | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| argentinean -> argentino | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| bar -> cercar vs bar alternate sense 1, bar alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| begin -> comenzar vs begin alternate sense 1, begin alternate sense 2 | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| billow -> oleaje vs billow alternate sense 1, billow alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| bouillon -> caldo | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| break -> quebrar vs break alternate sense 1, break alternate sense 2 | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| bridle -> reprimir vs bridle alternate sense 1, bridle alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 66.7% |
| brother -> hermano vs brother alternate sense 1, brother alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| chic -> elegante vs chic alternate sense 1 | 4 | 75.0% | 100.0% | 50.0% | 100.0% |
| cite -> mencionar vs cite alternate sense 1, cite alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| continue -> durar vs continue alternate sense 1, continue alternate sense 2 | 5 | 40.0% | 0.0% | 33.3% | 25.0% |
| control -> gobernar vs control alternate sense 1, control alternate sense 2 | 4 | 50.0% | 0.0% | 33.3% | 66.7% |
| conversance -> notoriedad | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| current -> contemporáneo vs current alternate sense 1, current alternate sense 2 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| december -> diciembre | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| demand -> deducción vs demand alternate sense 1, demand alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| dentist -> dentista | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| emotion -> emoción | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| endure -> durar vs endure alternate sense 1, endure alternate sense 2 | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| entirely -> enteramente vs entirely alternate sense 1 | 4 | 75.0% | 100.0% | 50.0% | 100.0% |
| except -> excepto vs except alternate sense 1 | 3 | 100.0% | 100.0% | 0.0% | 100.0% |
| femalejournalist -> periodista | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| german -> alemán vs german alternate sense 1, german alternate sense 2 | 5 | 60.0% | 50.0% | 33.3% | 75.0% |
| govern -> gobernar vs govern alternate sense 1, govern alternate sense 2 | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| grow -> acontecer vs grow alternate sense 1, grow alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| handiwork -> artesanía | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| health -> salud vs health alternate sense 1 | 3 | 100.0% | 100.0% | 0.0% | 100.0% |
| heart -> corazón vs heart alternate sense 1, heart alternate sense 2 | 5 | 60.0% | 50.0% | 33.3% | 50.0% |
| june -> junio | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| mosaicwork -> mosaico | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| offset -> distancia vs offset alternate sense 1, offset alternate sense 2 | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| owe -> deber vs owe alternate sense 1, owe alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| pair -> par vs pair alternate sense 1, pair alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| parrot -> loro vs parrot alternate sense 1, parrot alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| pub -> taberna | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| rebate -> descuento vs rebate alternate sense 1, rebate alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| recover -> sanar | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| region -> comarca vs region alternate sense 1, region alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| rumanian -> rumano vs rumanian alternate sense 1, rumanian alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| russian -> ruso vs russian alternate sense 1, russian alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| sale -> deducción vs sale alternate sense 1, sale alternate sense 2 | 5 | 20.0% | 50.0% | 100.0% | 25.0% |
| salesman -> vendedor | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| shed -> puesto vs shed alternate sense 1, shed alternate sense 2 | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| shortage -> falta vs shortage alternate sense 1 | 3 | 66.7% | 100.0% | 50.0% | 100.0% |
| smile -> sonreír vs smile alternate sense 1, smile alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| snore -> roncar vs snore alternate sense 1, snore alternate sense 2 | 4 | 75.0% | 100.0% | 33.3% | 100.0% |
| stall -> cuadra vs stall alternate sense 1, stall alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| tomorrow -> mañana vs tomorrow alternate sense 1, tomorrow alternate sense 2 | 4 | 50.0% | 100.0% | 66.7% | 66.7% |
| turnon -> poner | 2 | 50.0% | 100.0% | 100.0% | 100.0% |
| upon -> sobre | 2 | 50.0% | 100.0% | 100.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 73 | 83.6% | 83.6% | n/a | 83.6% |
| shadow | 75 | 94.7% | n/a | 5.3% | 85.3% |
| none | 58 | 31.0% | n/a | 69.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_draft_human_review_pending | 206 | 72.8% | 83.6% | 33.1% | 84.5% |
| en_es_full_family_representative_manual_v1 | 206 | 72.8% | 83.6% | 33.1% | 84.5% |
| full_family_representative_manual_v1 | 206 | 72.8% | 83.6% | 33.1% | 84.5% |
| shadow_contract:candidate_polysemic | 170 | 77.6% | 78.2% | 22.6% | 82.3% |
| pos_shape:cross_pos_polysemy | 94 | 80.9% | 86.2% | 21.5% | 87.5% |
| target_zipf:zipf_3_to_4_mid | 82 | 68.3% | 82.1% | 38.9% | 83.1% |
| polysemy:low_1_to_3 | 80 | 72.5% | 89.3% | 36.5% | 92.7% |
| pos_shape:same_pos_polysemy | 76 | 73.7% | 69.2% | 24.0% | 75.9% |
| shadow_negative | 75 | 94.7% | n/a | 5.3% | 85.3% |
| positive_active | 73 | 83.6% | 83.6% | n/a | 83.6% |
| target_zipf:zipf_4_to_5_common | 72 | 79.2% | 81.5% | 22.2% | 84.9% |
| polysemy:medium_4_to_9 | 63 | 79.4% | 90.5% | 26.2% | 85.7% |

## Failure Samples

### Harmful replace

- `en-es:full-family-representative:june:junio:002` `replace` vs `abstain` | trigger `june` | margin `0.566`
  sentence: The download list included a file named "june_notes.txt".
- `en-es:full-family-representative:december:diciembre:002` `replace` vs `abstain` | trigger `december` | margin `0.553`
  sentence: The spreadsheet column was titled "december" in the exported report.
- `en-es:full-family-representative:tomorrow:manana:002` `replace` vs `abstain` | trigger `tomorrow` | margin `0.001`
  sentence: In this sentence, tomorrow referred to the next day, the day after, following the present day, not the target replacement.
- `en-es:full-family-representative:tomorrow:manana:004` `replace` vs `abstain` | trigger `tomorrow` | margin `0.023`
  sentence: A navigation tab labeled "tomorrow" opened an empty archive page.
- `en-es:full-family-representative:region:comarca:004` `replace` vs `abstain` | trigger `region` | margin `0.030`
  sentence: A navigation tab labeled "region" opened an empty archive page.
- `en-es:full-family-representative:heart:corazon:005` `replace` vs `abstain` | trigger `heart` | margin `0.033`
  sentence: The download list included a file named "heart_notes.txt".

### False abstain

- `en-es:full-family-representative:heart:corazon:001` `abstain` vs `replace` | trigger `heart` | margin `-0.010`
  sentence: in your heart you know it is true
- `en-es:full-family-representative:continue:durar:001` `abstain` vs `replace` | trigger `continue` | margin `-0.008`
  sentence: continue on working!
- `en-es:full-family-representative:continue:durar:002` `abstain` vs `replace` | trigger `continue` | margin `-0.047`
  sentence: continue smiling
- `en-es:full-family-representative:control:gobernar:001` `abstain` vs `replace` | trigger `control` | margin `-0.011`
  sentence: under control
- `en-es:full-family-representative:german:aleman:001` `abstain` vs `replace` | trigger `german` | margin `-0.037`
  sentence: German philosophers
- `en-es:full-family-representative:sale:deduccion:001` `abstain` vs `replace` | trigger `sale` | margin `-0.031`
  sentence: he has just made his first sale

### Winner errors

- `en-es:full-family-representative:tomorrow:manana:002` `replace` vs `abstain` | trigger `tomorrow` | margin `0.001`
  sentence: In this sentence, tomorrow referred to the next day, the day after, following the present day, not the target replacement.
- `en-es:full-family-representative:heart:corazon:001` `abstain` vs `replace` | trigger `heart` | margin `-0.010`
  sentence: in your heart you know it is true
- `en-es:full-family-representative:heart:corazon:003` `abstain` vs `abstain` | trigger `heart` | margin `-0.039`
  sentence: he stood still, his heart thumping wildly
- `en-es:full-family-representative:continue:durar:001` `abstain` vs `replace` | trigger `continue` | margin `-0.008`
  sentence: continue on working!
- `en-es:full-family-representative:continue:durar:002` `abstain` vs `replace` | trigger `continue` | margin `-0.047`
  sentence: continue smiling
- `en-es:full-family-representative:continue:durar:004` `abstain` vs `abstain` | trigger `continue` | margin `-0.109`
  sentence: continue the peace in the family
