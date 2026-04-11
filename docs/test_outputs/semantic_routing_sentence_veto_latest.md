# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-04-11T04:00:41Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `77.5%`
- Replace precision / recall: `100.0%` / `43.8%`
- Harmful replace / false abstain: `0.0%` / `56.2%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`
- Predicted replace rate: `17.5%`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| ball -> pelota vs baile | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| bank -> banco vs orilla | 5 | 60.0% | 0.0% | 0.0% | 75.0% |
| cell -> célula vs celda | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| file -> archivo vs lima | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| match -> partido vs cerilla | 5 | 80.0% | 50.0% | 0.0% | 75.0% |
| plant -> planta vs fábrica | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| seal -> sello vs foca | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| spring -> primavera vs resorte | 5 | 60.0% | 0.0% | 0.0% | 50.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 16 | 43.8% | 43.8% | n/a | 100.0% |
| shadow | 16 | 100.0% | n/a | 0.0% | 50.0% |
| none | 8 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| clear_active | 16 | 43.8% | 43.8% | n/a | 100.0% |
| clear_shadow | 16 | 100.0% | n/a | 0.0% | 50.0% |
| phrase_control | 8 | 100.0% | n/a | 0.0% | n/a |
| verb | 5 | 100.0% | n/a | 0.0% | n/a |
| sports | 4 | 25.0% | 25.0% | n/a | 100.0% |
| animal | 2 | 100.0% | n/a | 0.0% | 100.0% |
| biology | 2 | 100.0% | 100.0% | n/a | 100.0% |
| digital | 2 | 100.0% | 100.0% | n/a | 100.0% |
| document | 2 | 100.0% | 100.0% | n/a | 100.0% |
| event | 2 | 100.0% | n/a | 0.0% | 0.0% |
| finance | 2 | 0.0% | 0.0% | n/a | 100.0% |
| fire | 2 | 100.0% | n/a | 0.0% | 50.0% |

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
- `en-es:sentence-veto:plant:002` `abstain` vs `replace` | trigger `plant` | margin `0.022`
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
