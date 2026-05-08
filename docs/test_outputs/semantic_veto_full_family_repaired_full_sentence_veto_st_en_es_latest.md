# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-07T19:46:48Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `73.0%`
- Replace precision / recall: `68.8%` / `87.8%`
- Harmful replace / false abstain: `42.9%` / `12.2%`
- Winner accuracy / shadow-winner accuracy: `85.7%` / `81.0%`
- Predicted replace rate: `66.1%`
- Phrase preemption hit rate / precision: `5.3%` / `80.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| acceptable -> razonable vs correcto, apto | 5 | 40.0% | 0.0% | 33.3% | 25.0% |
| adder -> víbora vs sumador | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| adjoining -> contiguo | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| adjoining -> vecino | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| altitude -> elevación | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| american -> americano | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| among -> entre | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| argentinean -> argentino | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| bar -> cercar vs taberna, compás | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| begin -> comenzar | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| billow -> oleaje vs elevarse, hincharse | 5 | 100.0% | 100.0% | 0.0% | 75.0% |
| bouillon -> caldo | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| break -> quebrar vs interrumpir, oportunidad | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| bridle -> reprimir vs brida, ofenderse | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| brother -> hermano | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| chic -> elegante vs elegancia | 4 | 50.0% | 50.0% | 50.0% | 66.7% |
| cite -> mencionar vs multar, elogiar | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| continue -> durar vs seguir, reanudar | 5 | 60.0% | 100.0% | 66.7% | 50.0% |
| control -> gobernar vs ajustar, grupo de control | 5 | 60.0% | 50.0% | 33.3% | 75.0% |
| current -> contemporáneo vs corriente eléctrica, corriente | 5 | 60.0% | 50.0% | 33.3% | 75.0% |
| december -> diciembre | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| dentist -> dentista | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| emotion -> emoción | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| endure -> durar vs soportar, aguantar | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| entirely -> enteramente | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| except -> excepto vs objetar, excluir | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| german -> alemán | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| govern -> gobernar vs regular, regir | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| handiwork -> artesanía | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| health -> salud | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| heart -> corazón | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| june -> junio | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| offset -> distancia vs compensar, reembolso | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| owe -> deber | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| pair -> par vs emparejar | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| parrot -> loro vs repetir, imitador | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| pub -> taberna | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| rebate -> descuento vs ranura, reembolsar | 5 | 60.0% | 50.0% | 33.3% | 50.0% |
| recover -> sanar vs recuperar, retapizar | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| region -> comarca vs zona, alrededor de | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| rumanian -> rumano | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| russian -> ruso | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| salesman -> vendedor | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| shortage -> falta | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| smile -> sonreír vs sonrisa, agradecer con una sonrisa | 5 | 100.0% | 100.0% | 0.0% | 75.0% |
| snore -> roncar vs ronquido | 4 | 50.0% | 0.0% | 0.0% | 33.3% |
| stall -> cuadra vs retrasar, calarse | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| tomorrow -> mañana | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| upon -> sobre | 3 | 66.7% | 100.0% | 100.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 98 | 87.8% | 87.8% | n/a | 87.8% |
| shadow | 42 | 90.5% | n/a | 9.5% | 81.0% |
| none | 49 | 28.6% | n/a | 71.4% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| approval_id:user_approved_full_repaired_dataset_2026_05_08 | 189 | 73.0% | 87.8% | 42.9% | 85.7% |
| approved_by_user | 189 | 73.0% | 87.8% | 42.9% | 85.7% |
| en_es_full_family_repaired_full_v1 | 189 | 73.0% | 87.8% | 42.9% | 85.7% |
| trusted | 189 | 73.0% | 87.8% | 42.9% | 85.7% |
| no_winner_subtype:not_applicable | 140 | 88.6% | 87.8% | 9.5% | 85.7% |
| active_sense_status:aligned | 116 | 68.1% | 91.2% | 64.6% | 89.0% |
| positive_active | 98 | 87.8% | 87.8% | n/a | 87.8% |
| pos_shape:cross_pos_polysemy | 87 | 74.7% | 77.5% | 27.7% | 79.1% |
| polysemy:low_1_to_3 | 78 | 70.5% | 89.1% | 56.2% | 89.1% |
| target_zipf:zipf_3_to_4_mid | 75 | 80.0% | 91.7% | 30.8% | 87.7% |
| active_sense_status:corrected_active_sense_required | 73 | 80.8% | 80.0% | 18.6% | 81.0% |
| family_disposition:salvage_with_corrected_active_sense | 73 | 80.8% | 80.0% | 18.6% | 81.0% |

## Failure Samples

### Harmful replace

- `en-es:full-family-repaired-full:break:quebrar:005` `replace` vs `abstain` | trigger `break` | margin `0.007`
  sentence: The dashboard listed Break as an internal project code.
- `en-es:full-family-repaired-full:offset:distancia:005` `replace` vs `abstain` | trigger `offset` | margin `0.014`
  sentence: The dashboard listed Offset as an internal project code.
- `en-es:full-family-repaired-full:december:diciembre:003` `replace` vs `abstain` | trigger `december` | margin `0.529`
  sentence: The dashboard listed December as an internal project code.
- `en-es:full-family-repaired-full:emotion:emoci-n:003` `replace` vs `abstain` | trigger `emotion` | margin `0.558`
  sentence: The dashboard listed Emotion as an internal project code.
- `en-es:full-family-repaired-full:dentist:dentista:003` `replace` vs `abstain` | trigger `dentist` | margin `0.486`
  sentence: The dashboard listed Dentist as an internal project code.
- `en-es:full-family-repaired-full:bouillon:caldo:003` `replace` vs `abstain` | trigger `bouillon` | margin `0.530`
  sentence: The dashboard listed Bouillon as an internal project code.

### False abstain

- `en-es:full-family-repaired-full:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-full:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.103`
  sentence: The lawyer had to bridle his frustration after the ruling.
- `en-es:full-family-repaired-full:control:gobernar:001` `abstain` vs `replace` | trigger `control` | margin `-0.003`
  sentence: The coalition hoped to control parliament after the election.
- `en-es:full-family-repaired-full:chic:elegante:001` `abstain` vs `replace` | trigger `chic` | margin `-0.003`
  sentence: She chose a chic black coat for the dinner.
- `en-es:full-family-repaired-full:snore:roncar:001` `abstain` vs `replace` | trigger `snore` | margin `-0.008`
  sentence: He started to snore as soon as the flight took off.
- `en-es:full-family-repaired-full:snore:roncar:002` `abstain` vs `replace` | trigger `snore` | margin `-0.038`
  sentence: She could hear her roommate snore through the wall.

### Winner errors

- `en-es:full-family-repaired-full:offset:distancia:003` `abstain` vs `abstain` | trigger `offset` | margin `-0.127`
  phrase preemption: `subject_trigger_object_frame` | `helped offset the`
  sentence: The rebate helped offset the higher shipping cost.
- `en-es:full-family-repaired-full:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.161`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-full:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `-0.103`
  sentence: The lawyer had to bridle his frustration after the ruling.
- `en-es:full-family-repaired-full:control:gobernar:001` `abstain` vs `replace` | trigger `control` | margin `-0.003`
  sentence: The coalition hoped to control parliament after the election.
- `en-es:full-family-repaired-full:continue:durar:003` `replace` vs `abstain` | trigger `continue` | margin `0.003`
  sentence: Please continue reading the next section.
- `en-es:full-family-repaired-full:continue:durar:004` `replace` vs `abstain` | trigger `continue` | margin `0.013`
  sentence: The teams will continue play after the delay.
