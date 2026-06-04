# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-05T15:31:10Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `80.0%`
- Replace precision / recall: `n/a` / `0.0%`
- Harmful replace / false abstain: `0.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `50.0%` / `n/a`
- Predicted replace rate: `0.0%`
- Phrase preemption hit rate / precision: `20.0%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| help -> ayuda vs servicio | 12 | 66.7% | 0.0% | 0.0% | 50.0% |
| particular -> específico vs quisquilloso, detalles | 8 | 100.0% | n/a | 0.0% | n/a |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 4 | 0.0% | 0.0% | n/a | 50.0% |
| none | 16 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| curve_priority:P0 | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| discovery | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| en_es_sampling_stage1_p0_manual_v1 | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| manual_draft_v1 | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| pre_outcome | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| targeted_curve_mechanism_lane | 20 | 80.0% | 0.0% | 0.0% | 50.0% |
| phrase_no_winner | 16 | 100.0% | n/a | 0.0% | n/a |
| core_high_polysemy | 12 | 66.7% | 0.0% | 0.0% | 50.0% |
| polysemy:high_10_plus | 12 | 66.7% | 0.0% | 0.0% | 50.0% |
| rank_bin:1-500 | 12 | 66.7% | 0.0% | 0.0% | 50.0% |
| scorer:tfidf_cosine | 12 | 66.7% | 0.0% | 0.0% | 50.0% |
| shadow_contract:limited | 12 | 66.7% | 0.0% | 0.0% | 50.0% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:sampling-stage1-p0:help:02:001` `abstain` vs `replace` | trigger `help` | margin `-0.009`
  sentence: Her help made the move much easier.
- `en-es:sampling-stage1-p0:help:02:002` `abstain` vs `replace` | trigger `help` | margin `-0.009`
  sentence: The guide offers help with password resets.
- `en-es:sampling-stage1-p0:help:02:003` `abstain` vs `replace` | trigger `help` | margin `0.043`
  sentence: We need help carrying these boxes upstairs.
- `en-es:sampling-stage1-p0:help:02:004` `abstain` vs `replace` | trigger `help` | margin `0.028`
  sentence: Thank you for the help you gave my sister.

### Winner errors

- `en-es:sampling-stage1-p0:help:02:001` `abstain` vs `replace` | trigger `help` | margin `-0.009`
  sentence: Her help made the move much easier.
- `en-es:sampling-stage1-p0:help:02:002` `abstain` vs `replace` | trigger `help` | margin `-0.009`
  sentence: The guide offers help with password resets.
