# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-07T19:46:48Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_full_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `50.3%`
- Replace precision / recall: `83.3%` / `5.1%`
- Harmful replace / false abstain: `1.1%` / `94.9%`
- Winner accuracy / shadow-winner accuracy: `69.3%` / `23.8%`
- Predicted replace rate: `3.2%`
- Phrase preemption hit rate / precision: `5.3%` / `80.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| acceptable -> razonable vs correcto, apto | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| adder -> víbora vs sumador | 4 | 50.0% | 0.0% | 0.0% | 66.7% |
| adjoining -> contiguo | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| adjoining -> vecino | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| altitude -> elevación | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| american -> americano | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| among -> entre | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| argentinean -> argentino | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| bar -> cercar vs taberna, compás | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| begin -> comenzar | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| billow -> oleaje vs elevarse, hincharse | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| bouillon -> caldo | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| break -> quebrar vs interrumpir, oportunidad | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| bridle -> reprimir vs brida, ofenderse | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| brother -> hermano | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| chic -> elegante vs elegancia | 4 | 50.0% | 0.0% | 0.0% | 0.0% |
| cite -> mencionar vs multar, elogiar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| continue -> durar vs seguir, reanudar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| control -> gobernar vs ajustar, grupo de control | 5 | 40.0% | 0.0% | 33.3% | 25.0% |
| current -> contemporáneo vs corriente eléctrica, corriente | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| december -> diciembre | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| dentist -> dentista | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| emotion -> emoción | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| endure -> durar vs soportar, aguantar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| entirely -> enteramente | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| except -> excepto vs objetar, excluir | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| german -> alemán | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| govern -> gobernar vs regular, regir | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| handiwork -> artesanía | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| health -> salud | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| heart -> corazón | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| june -> junio | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| offset -> distancia vs compensar, reembolso | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| owe -> deber | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| pair -> par vs emparejar | 4 | 50.0% | 0.0% | 0.0% | 66.7% |
| parrot -> loro vs repetir, imitador | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| pub -> taberna | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| rebate -> descuento vs ranura, reembolsar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| recover -> sanar vs recuperar, retapizar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| region -> comarca vs zona, alrededor de | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| rumanian -> rumano | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| russian -> ruso | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| salesman -> vendedor | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| shortage -> falta | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| smile -> sonreír vs sonrisa, agradecer con una sonrisa | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| snore -> roncar vs ronquido | 4 | 50.0% | 0.0% | 0.0% | 33.3% |
| stall -> cuadra vs retrasar, calarse | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| tomorrow -> mañana | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| upon -> sobre | 3 | 33.3% | 0.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 98 | 5.1% | 5.1% | n/a | 88.8% |
| shadow | 42 | 97.6% | n/a | 2.4% | 23.8% |
| none | 49 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| approval_id:user_approved_full_repaired_dataset_2026_05_08 | 189 | 50.3% | 5.1% | 1.1% | 69.3% |
| approved_by_user | 189 | 50.3% | 5.1% | 1.1% | 69.3% |
| en_es_full_family_repaired_full_v1 | 189 | 50.3% | 5.1% | 1.1% | 69.3% |
| trusted | 189 | 50.3% | 5.1% | 1.1% | 69.3% |
| no_winner_subtype:not_applicable | 140 | 32.9% | 5.1% | 2.4% | 69.3% |
| active_sense_status:aligned | 116 | 44.0% | 4.4% | 0.0% | 81.7% |
| positive_active | 98 | 5.1% | 5.1% | n/a | 88.8% |
| pos_shape:cross_pos_polysemy | 87 | 56.3% | 7.5% | 2.1% | 53.7% |
| polysemy:low_1_to_3 | 78 | 42.3% | 2.2% | 0.0% | 80.0% |
| target_zipf:zipf_3_to_4_mid | 75 | 53.3% | 2.8% | 0.0% | 63.2% |
| active_sense_status:corrected_active_sense_required | 73 | 60.3% | 6.7% | 2.3% | 51.7% |
| family_disposition:salvage_with_corrected_active_sense | 73 | 60.3% | 6.7% | 2.3% | 51.7% |

## Failure Samples

### Harmful replace

- `en-es:full-family-repaired-full:control:gobernar:004` `replace` vs `abstain` | trigger `control` | margin `0.008`
  sentence: The study included a control group and a treatment group.

### False abstain

- `en-es:full-family-repaired-full:break:quebrar:001` `abstain` vs `replace` | trigger `break` | margin `0.000`
  sentence: The old plate began to break along the rim.
- `en-es:full-family-repaired-full:bar:cercar:001` `abstain` vs `replace` | trigger `bar` | margin `0.029`
  sentence: Workers will bar the storage yard with temporary fencing.
- `en-es:full-family-repaired-full:bar:cercar:002` `abstain` vs `replace` | trigger `bar` | margin `0.000`
  sentence: The rancher used wire panels to bar the cattle inside the field.
- `en-es:full-family-repaired-full:offset:distancia:001` `abstain` vs `replace` | trigger `offset` | margin `0.031`
  sentence: Set the image offset to twelve pixels from the left edge.
- `en-es:full-family-repaired-full:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.079`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-full:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `0.000`
  sentence: The lawyer had to bridle his frustration after the ruling.

### Winner errors

- `en-es:full-family-repaired-full:break:quebrar:003` `abstain` vs `abstain` | trigger `break` | margin `-0.011`
  sentence: A news alert can break the broadcast without warning.
- `en-es:full-family-repaired-full:bar:cercar:003` `abstain` vs `abstain` | trigger `bar` | margin `0.000`
  sentence: They met at the bar after work.
- `en-es:full-family-repaired-full:bar:cercar:004` `abstain` vs `abstain` | trigger `bar` | margin `0.000`
  sentence: The violin enters on the second bar of the song.
- `en-es:full-family-repaired-full:offset:distancia:003` `abstain` vs `abstain` | trigger `offset` | margin `0.000`
  phrase preemption: `subject_trigger_object_frame` | `helped offset the`
  sentence: The rebate helped offset the higher shipping cost.
- `en-es:full-family-repaired-full:offset:distancia:004` `abstain` vs `abstain` | trigger `offset` | margin `-0.016`
  sentence: The invoice showed a small offset for the returned item.
- `en-es:full-family-repaired-full:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.079`
  sentence: She tried to bridle her anger during the meeting.
