# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-05T02:16:08Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_heuristic_group_pilot_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `69.4%`
- Replace precision / recall: `92.0%` / `39.7%`
- Harmful replace / false abstain: `3.2%` / `60.3%`
- Winner accuracy / shadow-winner accuracy: `84.8%` / `85.3%`
- Predicted replace rate: `20.7%`
- Phrase preemption hit rate / precision: `0.8%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| call -> llamada vs decisión, llamar | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| check -> cheque vs revisar, inspección | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| crisis -> crisis | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| deep -> profundo vs grave, intenso | 5 | 60.0% | 50.0% | 33.3% | 100.0% |
| green -> verde vs novato, ecológico, green | 5 | 60.0% | 50.0% | 33.3% | 50.0% |
| hammer -> martillo vs martillar, mazo | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| help -> ayuda vs servicio | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| low -> bajo vs mínimo, mugir | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| man -> hombre vs dotar, ser humano | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| money -> dinero | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| often -> a menudo | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| order -> pedido vs orden | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| participant -> participante | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| particular -> específico vs quisquilloso, detalles | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| percent -> por ciento | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| plant -> plantar vs planta, fábrica | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| play -> jugar vs obra, holgura | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| prosecute -> enjuiciar | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| purely -> puramente | 3 | 100.0% | 100.0% | 0.0% | 100.0% |
| report -> informe vs informar, estallido | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| senate -> senado | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| suitable -> adecuado | 3 | 100.0% | 100.0% | 0.0% | 100.0% |
| therefore -> por lo tanto | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| trade -> comercio vs intercambiar, oficio | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| unnecessary -> innecesario | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| upgrade -> actualización vs mejora, mejorar | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| work -> trabajo vs funcionar, obra | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| yes -> sí | 3 | 66.7% | 50.0% | 0.0% | 100.0% |
| yield -> rendimiento vs ceder, producir | 5 | 100.0% | 100.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 58 | 39.7% | 39.7% | n/a | 84.5% |
| shadow | 34 | 100.0% | n/a | 0.0% | 85.3% |
| none | 29 | 93.1% | n/a | 6.9% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic_group_pilot_v1 | 121 | 69.4% | 39.7% | 3.2% | 84.8% |
| manual_draft_v1 | 121 | 69.4% | 39.7% | 3.2% | 84.8% |
| pre_outcome | 96 | 67.7% | 39.6% | 4.2% | 87.5% |
| polysemy:high_10_plus | 80 | 72.5% | 37.5% | 4.2% | 78.1% |
| shadow_contract:full | 80 | 71.2% | 34.4% | 4.2% | 78.1% |
| positive_active | 58 | 39.7% | 39.7% | n/a | 84.5% |
| polysemy:low_1_to_3 | 36 | 63.9% | 45.8% | 0.0% | 100.0% |
| shadow_contract:not_applicable | 36 | 63.9% | 45.8% | 0.0% | 100.0% |
| shadow_negative | 34 | 100.0% | n/a | 0.0% | 85.3% |
| rank_bin:1-500 | 32 | 62.5% | 25.0% | 0.0% | 79.2% |
| rank_bin:1001-2000 | 32 | 59.4% | 31.2% | 12.5% | 91.7% |
| rank_bin:>5000 | 32 | 81.2% | 62.5% | 0.0% | 91.7% |

## Failure Samples

### Harmful replace

- `en-es:heuristic-group:green:verde:005` `replace` vs `abstain` | trigger `green` | margin `0.038`
  sentence: The driver waited for the green light.
- `en-es:heuristic-group:deep:profundo:005` `replace` vs `abstain` | trigger `deep` | margin `0.058`
  sentence: Deep down, he knew the answer.

### False abstain

- `en-es:heuristic-group:man:hombre:001` `abstain` vs `replace` | trigger `man` | margin `0.036`
  sentence: The old man waited by the bus stop.
- `en-es:heuristic-group:work:trabajo:001` `abstain` vs `replace` | trigger `work` | margin `-0.006`
  sentence: She left work early to catch the train.
- `en-es:heuristic-group:work:trabajo:002` `abstain` vs `replace` | trigger `work` | margin `-0.004`
  sentence: The repair work took all afternoon.
- `en-es:heuristic-group:call:llamada:001` `abstain` vs `replace` | trigger `call` | margin `0.044`
  sentence: I missed your call during the meeting.
- `en-es:heuristic-group:call:llamada:002` `abstain` vs `replace` | trigger `call` | margin `-0.004`
  sentence: The call lasted only five minutes.
- `en-es:heuristic-group:help:ayuda:001` `abstain` vs `replace` | trigger `help` | margin `0.018`
  sentence: Thanks for your help with the boxes.

### Winner errors

- `en-es:heuristic-group:man:hombre:004` `abstain` vs `abstain` | trigger `man` | margin `0.001`
  sentence: Two guards man the front gate after dark.
- `en-es:heuristic-group:work:trabajo:001` `abstain` vs `replace` | trigger `work` | margin `-0.006`
  sentence: She left work early to catch the train.
- `en-es:heuristic-group:work:trabajo:002` `abstain` vs `replace` | trigger `work` | margin `-0.004`
  sentence: The repair work took all afternoon.
- `en-es:heuristic-group:work:trabajo:004` `abstain` vs `abstain` | trigger `work` | margin `0.025`
  sentence: The museum displayed a late work by the painter.
- `en-es:heuristic-group:call:llamada:002` `abstain` vs `replace` | trigger `call` | margin `-0.004`
  sentence: The call lasted only five minutes.
- `en-es:heuristic-group:green:verde:001` `abstain` vs `replace` | trigger `green` | margin `-0.018`
  sentence: She wore a green jacket to school.
