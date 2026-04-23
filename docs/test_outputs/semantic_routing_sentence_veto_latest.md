# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-04-23T05:06:43Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v9.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `71.1%`
- Replace precision / recall: `100.0%` / `27.8%`
- Harmful replace / false abstain: `0.0%` / `72.2%`
- Winner accuracy / shadow-winner accuracy: `63.9%` / `33.3%`
- Predicted replace rate: `11.1%`
- Phrase preemption hit rate / precision: `7.8%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| ball -> pelota vs baile | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| bank -> banco vs orilla | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| board -> tablero vs junta | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| branch -> sucursal vs rama | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| cell -> célula vs celda | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| check -> cheque vs revisar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| drink -> bebida vs beber | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| file -> archivo vs lima | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| match -> partido vs cerilla | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| order -> pedido vs ordenar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| park -> parque vs aparcar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| plant -> planta vs fábrica | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| play -> obra vs jugar | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| seal -> sello vs foca | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| spring -> primavera vs resorte | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| table -> mesa vs tabla | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| trip -> viaje vs tropezar | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| watch -> reloj vs vigilar | 5 | 80.0% | 50.0% | 0.0% | 50.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 36 | 27.8% | 27.8% | n/a | 94.4% |
| shadow | 36 | 100.0% | n/a | 0.0% | 33.3% |
| none | 18 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| clear_shadow | 36 | 100.0% | n/a | 0.0% | 33.3% |
| clear_active | 35 | 28.6% | 28.6% | n/a | 94.3% |
| cross_pos | 31 | 64.5% | 8.3% | 0.0% | 45.8% |
| verb | 23 | 100.0% | n/a | 0.0% | 8.3% |
| phrase_control | 18 | 100.0% | n/a | 0.0% | n/a |
| weak_active_support | 13 | 7.7% | 7.7% | n/a | 84.6% |
| lexicalized_expression | 7 | 100.0% | n/a | 0.0% | n/a |
| idiom | 5 | 100.0% | n/a | 0.0% | n/a |
| beverage | 4 | 50.0% | 0.0% | 0.0% | 50.0% |
| document | 4 | 100.0% | 100.0% | 0.0% | 75.0% |
| finance | 4 | 0.0% | 0.0% | n/a | 100.0% |
| home | 4 | 25.0% | 25.0% | n/a | 100.0% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:sentence-veto:ball:001` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The goalkeeper punched the ball over the bar.
- `en-es:sentence-veto:ball:002` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The child kicked the ball into the street.
- `en-es:sentence-veto:bank:001` `abstain` vs `replace` | trigger `bank` | margin `0.000`
  sentence: She deposited the cash at the bank before lunch.
- `en-es:sentence-veto:bank:002` `abstain` vs `replace` | trigger `bank` | margin `0.000`
  sentence: The bank approved our mortgage application.
- `en-es:sentence-veto:plant:001` `abstain` vs `replace` | trigger `plant` | margin `0.000`
  sentence: She watered the plant on the windowsill.
- `en-es:sentence-veto:plant:002` `abstain` vs `replace` | trigger `plant` | margin `0.020`
  sentence: The plant needs more sunlight in the afternoon.

### Winner errors

- `en-es:sentence-veto:ball:003` `abstain` vs `abstain` | trigger `ball` | margin `0.000`
  sentence: They danced at the royal ball until dawn.
- `en-es:sentence-veto:ball:004` `abstain` vs `abstain` | trigger `ball` | margin `0.000`
  sentence: The charity ball raised thousands of dollars.
- `en-es:sentence-veto:bank:004` `abstain` vs `abstain` | trigger `bank` | margin `0.000`
  sentence: Wildflowers grew along the muddy bank.
- `en-es:sentence-veto:plant:003` `abstain` vs `abstain` | trigger `plant` | margin `0.000`
  sentence: The steel plant closed after the strike.
- `en-es:sentence-veto:plant:004` `abstain` vs `abstain` | trigger `plant` | margin `0.000`
  sentence: Hundreds of workers left the chemical plant at noon.
- `en-es:sentence-veto:spring:003` `abstain` vs `abstain` | trigger `spring` | margin `0.000`
  sentence: The spring inside the lock snapped suddenly.
