# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T20:20:11Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_representative_manual_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `80.6%`
- Replace precision / recall: `100.0%` / `45.2%`
- Harmful replace / false abstain: `0.0%` / `54.8%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `62.7%`
- Predicted replace rate: `16.0%`
- Phrase preemption hit rate / precision: `0.0%` / `n/a`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| aberration -> equivocación vs aberration alternate sense 1, aberration alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| acceptable -> razonable vs acceptable alternate sense 1, acceptable alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| adder -> víbora vs adder alternate sense 1, adder alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| adjoining -> contiguo | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| adjoining -> vecino | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| altitude -> elevación vs altitude alternate sense 1, altitude alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| american -> americano vs american alternate sense 1, american alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| among -> entre | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| argentinean -> argentino | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| bar -> cercar vs bar alternate sense 1, bar alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| begin -> comenzar vs begin alternate sense 1, begin alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| billow -> oleaje vs billow alternate sense 1, billow alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| bouillon -> caldo | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| break -> quebrar vs break alternate sense 1, break alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| bridle -> reprimir vs bridle alternate sense 1, bridle alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| brother -> hermano vs brother alternate sense 1, brother alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| chic -> elegante vs chic alternate sense 1 | 4 | 50.0% | 0.0% | 0.0% | 66.7% |
| cite -> mencionar vs cite alternate sense 1, cite alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| continue -> durar vs continue alternate sense 1, continue alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| control -> gobernar vs control alternate sense 1, control alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| conversance -> notoriedad | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| current -> contemporáneo vs current alternate sense 1, current alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| december -> diciembre | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| demand -> deducción vs demand alternate sense 1, demand alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| dentist -> dentista | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| emotion -> emoción | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| endure -> durar vs endure alternate sense 1, endure alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| entirely -> enteramente vs entirely alternate sense 1 | 4 | 50.0% | 0.0% | 0.0% | 66.7% |
| except -> excepto vs except alternate sense 1 | 3 | 100.0% | 100.0% | 0.0% | 50.0% |
| femalejournalist -> periodista | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| german -> alemán vs german alternate sense 1, german alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| govern -> gobernar vs govern alternate sense 1, govern alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| grow -> acontecer vs grow alternate sense 1, grow alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 33.3% |
| handiwork -> artesanía | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| health -> salud vs health alternate sense 1 | 3 | 66.7% | 0.0% | 0.0% | 0.0% |
| heart -> corazón vs heart alternate sense 1, heart alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| june -> junio | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| mosaicwork -> mosaico | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| offset -> distancia vs offset alternate sense 1, offset alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| owe -> deber vs owe alternate sense 1, owe alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| pair -> par vs pair alternate sense 1, pair alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| parrot -> loro vs parrot alternate sense 1, parrot alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| pub -> taberna | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| rebate -> descuento vs rebate alternate sense 1, rebate alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| recover -> sanar | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| region -> comarca vs region alternate sense 1, region alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| rumanian -> rumano vs rumanian alternate sense 1, rumanian alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 100.0% |
| russian -> ruso vs russian alternate sense 1, russian alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 100.0% |
| sale -> deducción vs sale alternate sense 1, sale alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| salesman -> vendedor | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| shed -> puesto vs shed alternate sense 1, shed alternate sense 2 | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| shortage -> falta vs shortage alternate sense 1 | 3 | 66.7% | 0.0% | 0.0% | 100.0% |
| smile -> sonreír vs smile alternate sense 1, smile alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| snore -> roncar vs snore alternate sense 1, snore alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| stall -> cuadra vs stall alternate sense 1, stall alternate sense 2 | 4 | 100.0% | 100.0% | 0.0% | 66.7% |
| tomorrow -> mañana vs tomorrow alternate sense 1, tomorrow alternate sense 2 | 4 | 75.0% | 0.0% | 0.0% | 66.7% |
| turnon -> poner | 2 | 100.0% | 100.0% | 0.0% | 100.0% |
| upon -> sobre | 2 | 100.0% | 100.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 73 | 45.2% | 45.2% | n/a | 87.7% |
| shadow | 75 | 100.0% | n/a | 0.0% | 62.7% |
| none | 58 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_draft_human_review_pending | 206 | 80.6% | 45.2% | 0.0% | 75.0% |
| en_es_full_family_representative_manual_v1 | 206 | 80.6% | 45.2% | 0.0% | 75.0% |
| full_family_representative_manual_v1 | 206 | 80.6% | 45.2% | 0.0% | 75.0% |
| shadow_contract:candidate_polysemic | 170 | 76.5% | 27.3% | 0.0% | 71.5% |
| pos_shape:cross_pos_polysemy | 94 | 78.7% | 31.0% | 0.0% | 77.8% |
| target_zipf:zipf_3_to_4_mid | 82 | 85.4% | 57.1% | 0.0% | 76.3% |
| polysemy:low_1_to_3 | 80 | 85.0% | 57.1% | 0.0% | 85.5% |
| pos_shape:same_pos_polysemy | 76 | 73.7% | 23.1% | 0.0% | 63.8% |
| shadow_negative | 75 | 100.0% | n/a | 0.0% | 62.7% |
| positive_active | 73 | 45.2% | 45.2% | n/a | 87.7% |
| target_zipf:zipf_4_to_5_common | 72 | 73.6% | 29.6% | 0.0% | 73.6% |
| polysemy:medium_4_to_9 | 63 | 76.2% | 28.6% | 0.0% | 71.4% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:full-family-representative:health:salud:001` `abstain` vs `replace` | trigger `health` | margin `-0.006`
  sentence: physicians should be held responsible for the health of their patients
- `en-es:full-family-representative:russian:ruso:001` `abstain` vs `replace` | trigger `russian` | margin `0.000`
  sentence: Russian dancing
- `en-es:full-family-representative:tomorrow:manana:001` `abstain` vs `replace` | trigger `tomorrow` | margin `0.000`
  sentence: what are our tasks for tomorrow?
- `en-es:full-family-representative:american:americano:001` `abstain` vs `replace` | trigger `american` | margin `0.000`
  sentence: American citizens
- `en-es:full-family-representative:american:americano:002` `abstain` vs `replace` | trigger `american` | margin `0.000`
  sentence: American English
- `en-es:full-family-representative:current:contemporaneo:001` `abstain` vs `replace` | trigger `current` | margin `0.000`
  sentence: current events

### Winner errors

- `en-es:full-family-representative:except:excepto:002` `abstain` vs `abstain` | trigger `except` | margin `0.000`
  sentence: except the top piece
- `en-es:full-family-representative:health:salud:001` `abstain` vs `replace` | trigger `health` | margin `-0.006`
  sentence: physicians should be held responsible for the health of their patients
- `en-es:full-family-representative:health:salud:002` `abstain` vs `abstain` | trigger `health` | margin `0.000`
  sentence: his delicate health
- `en-es:full-family-representative:tomorrow:manana:003` `abstain` vs `abstain` | trigger `tomorrow` | margin `0.000`
  sentence: tomorrow's world
- `en-es:full-family-representative:region:comarca:002` `abstain` vs `abstain` | trigger `region` | margin `-0.009`
  sentence: in the abdominal region
- `en-es:full-family-representative:brother:hermano:003` `abstain` vs `abstain` | trigger `brother` | margin `0.000`
  sentence: Greetings, brother!
