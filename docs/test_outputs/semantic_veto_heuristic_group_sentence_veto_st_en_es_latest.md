# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-05T02:16:08Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Thresholds: `min_active=0.0`, `min_margin=0.0`

## Summary

- Decision accuracy: `77.7%`
- Replace precision / recall: `71.2%` / `89.7%`
- Harmful replace / false abstain: `33.3%` / `10.3%`
- Winner accuracy / shadow-winner accuracy: `89.1%` / `88.2%`
- Predicted replace rate: `60.3%`
- Phrase preemption hit rate / precision: `0.8%` / `100.0%`
- Active rescue applied rate / precision: `3.3%` / `50.0%`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| call -> llamada vs decisión, llamar | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| check -> cheque vs revisar, inspección | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| crisis -> crisis | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| deep -> profundo vs grave, intenso | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| green -> verde vs novato, ecológico, green | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| hammer -> martillo vs martillar, mazo | 5 | 60.0% | 50.0% | 33.3% | 50.0% |
| help -> ayuda vs servicio | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| low -> bajo vs mínimo, mugir | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| man -> hombre vs dotar, ser humano | 5 | 60.0% | 100.0% | 66.7% | 75.0% |
| money -> dinero | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| often -> a menudo | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| order -> pedido vs orden | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| participant -> participante | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| particular -> específico vs quisquilloso, detalles | 5 | 80.0% | 100.0% | 33.3% | 100.0% |
| percent -> por ciento | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| plant -> plantar vs planta, fábrica | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| play -> jugar vs obra, holgura | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| prosecute -> enjuiciar | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| purely -> puramente | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| report -> informe vs informar, estallido | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| senate -> senado | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| suitable -> adecuado | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| therefore -> por lo tanto | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| trade -> comercio vs intercambiar, oficio | 5 | 80.0% | 100.0% | 33.3% | 75.0% |
| unnecessary -> innecesario | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| upgrade -> actualización vs mejora, mejorar | 5 | 60.0% | 50.0% | 33.3% | 75.0% |
| work -> trabajo vs funcionar, obra | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| yes -> sí | 3 | 66.7% | 100.0% | 100.0% | 100.0% |
| yield -> rendimiento vs ceder, producir | 5 | 80.0% | 50.0% | 0.0% | 75.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 58 | 89.7% | 89.7% | n/a | 89.7% |
| shadow | 34 | 94.1% | n/a | 5.9% | 88.2% |
| none | 29 | 34.5% | n/a | 65.5% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic_group_pilot_v1 | 121 | 77.7% | 89.7% | 33.3% | 89.1% |
| manual_draft_v1 | 121 | 77.7% | 89.7% | 33.3% | 89.1% |
| pre_outcome | 96 | 74.0% | 89.6% | 41.7% | 88.9% |
| polysemy:high_10_plus | 80 | 82.5% | 81.2% | 16.7% | 84.4% |
| shadow_contract:full | 80 | 81.2% | 81.2% | 18.8% | 84.4% |
| positive_active | 58 | 89.7% | 89.7% | n/a | 89.7% |
| polysemy:low_1_to_3 | 36 | 66.7% | 100.0% | 100.0% | 100.0% |
| shadow_contract:not_applicable | 36 | 66.7% | 100.0% | 100.0% | 100.0% |
| shadow_negative | 34 | 94.1% | n/a | 5.9% | 88.2% |
| rank_bin:1-500 | 32 | 75.0% | 87.5% | 37.5% | 87.5% |
| rank_bin:1001-2000 | 32 | 75.0% | 100.0% | 50.0% | 95.8% |
| rank_bin:>5000 | 32 | 71.9% | 81.2% | 37.5% | 83.3% |

## Failure Samples

### Harmful replace

- `en-es:heuristic-group:man:hombre:004` `replace` vs `abstain` | trigger `man` | margin `0.031`
  sentence: Two guards man the front gate after dark.
- `en-es:heuristic-group:man:hombre:005` `replace` vs `abstain` | trigger `man` | margin `0.038`
  sentence: Man, that was a close call at the end.
- `en-es:heuristic-group:yes:si:003` `replace` vs `abstain` | trigger `yes` | margin `0.487`
  sentence: The button label reads yes in lowercase letters.
- `en-es:heuristic-group:money:dinero:003` `replace` vs `abstain` | trigger `money` | margin `0.644`
  sentence: Money talks in that old proverb.
- `en-es:heuristic-group:percent:por_ciento:003` `replace` vs `abstain` | trigger `percent` | margin `0.570`
  sentence: The percent sign appeared in every spreadsheet cell.
- `en-es:heuristic-group:often:a_menudo:003` `replace` vs `abstain` | trigger `often` | margin `0.571`
  sentence: Little and often is his training motto.

### False abstain

- `en-es:heuristic-group:work:trabajo:002` `abstain` vs `replace` | trigger `work` | margin `-0.002`
  sentence: The repair work took all afternoon.
- `en-es:heuristic-group:call:llamada:002` `abstain` vs `replace` | trigger `call` | margin `-0.005`
  sentence: The call lasted only five minutes.
- `en-es:heuristic-group:upgrade:actualizacion:002` `abstain` vs `replace` | trigger `upgrade` | margin `-0.006`
  sentence: The phone upgrade fixed the battery issue.
- `en-es:heuristic-group:yield:rendimiento:002` `abstain` vs `replace` | trigger `yield` | margin `-0.001`
  sentence: The bond yield fell again today.
- `en-es:heuristic-group:hammer:martillo:001` `abstain` vs `replace` | trigger `hammer` | margin `-0.023`
  sentence: He borrowed a hammer from the garage.
- `en-es:heuristic-group:report:informe:002` `abstain` vs `replace` | trigger `report` | margin `-0.009`
  sentence: She filed a report after the accident.

### Winner errors

- `en-es:heuristic-group:man:hombre:004` `replace` vs `abstain` | trigger `man` | margin `0.031`
  sentence: Two guards man the front gate after dark.
- `en-es:heuristic-group:work:trabajo:002` `abstain` vs `replace` | trigger `work` | margin `-0.002`
  sentence: The repair work took all afternoon.
- `en-es:heuristic-group:call:llamada:002` `abstain` vs `replace` | trigger `call` | margin `-0.005`
  sentence: The call lasted only five minutes.
- `en-es:heuristic-group:trade:comercio:003` `abstain` vs `abstain` | trigger `trade` | margin `-0.022`
  sentence: The children trade cards after school.
- `en-es:heuristic-group:upgrade:actualizacion:002` `abstain` vs `replace` | trigger `upgrade` | margin `-0.006`
  sentence: The phone upgrade fixed the battery issue.
- `en-es:heuristic-group:yield:rendimiento:002` `abstain` vs `replace` | trigger `yield` | margin `-0.001`
  sentence: The bond yield fell again today.
