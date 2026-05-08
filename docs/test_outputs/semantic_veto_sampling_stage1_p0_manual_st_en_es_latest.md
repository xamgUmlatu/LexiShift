# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-05T15:31:11Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_p0_manual_v1.json`
- Pair: `en-es`
- Scorer: `sentence_transformer_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `70.0%`
- Replace precision / recall: `33.3%` / `50.0%`
- Harmful replace / false abstain: `25.0%` / `50.0%`
- Winner accuracy / shadow-winner accuracy: `50.0%` / `n/a`
- Predicted replace rate: `30.0%`
- Phrase preemption hit rate / precision: `20.0%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| help -> ayuda vs servicio | 12 | 75.0% | 50.0% | 12.5% | 50.0% |
| particular -> específico vs quisquilloso, detalles | 8 | 62.5% | n/a | 37.5% | n/a |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 4 | 50.0% | 50.0% | n/a | 50.0% |
| none | 16 | 75.0% | n/a | 25.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| curve_priority:P0 | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| discovery | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| en_es_sampling_stage1_p0_manual_v1 | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| manual_draft_v1 | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| pre_outcome | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| targeted_curve_mechanism_lane | 20 | 70.0% | 50.0% | 25.0% | 50.0% |
| phrase_no_winner | 16 | 75.0% | n/a | 25.0% | n/a |
| core_high_polysemy | 12 | 75.0% | 50.0% | 12.5% | 50.0% |
| polysemy:high_10_plus | 12 | 75.0% | 50.0% | 12.5% | 50.0% |
| rank_bin:1-500 | 12 | 75.0% | 50.0% | 12.5% | 50.0% |
| scorer:tfidf_cosine | 12 | 75.0% | 50.0% | 12.5% | 50.0% |
| shadow_contract:limited | 12 | 75.0% | 50.0% | 12.5% | 50.0% |

## Failure Samples

### Harmful replace

- `en-es:sampling-stage1-p0:help:04:002` `replace` vs `abstain` | trigger `help` | margin `0.020`
  sentence: The child shouted help from the locked bathroom.
- `en-es:sampling-stage1-p0:particular:03:004` `replace` vs `abstain` | trigger `particular` | margin `0.074`
  sentence: One example in particular changed my mind.
- `en-es:sampling-stage1-p0:particular:05:002` `replace` vs `abstain` | trigger `particular` | margin `0.001`
  sentence: No rule in particular explains that result.
- `en-es:sampling-stage1-p0:particular:05:003` `replace` vs `abstain` | trigger `particular` | margin `0.002`
  sentence: This season in particular has been unpredictable.

### False abstain

- `en-es:sampling-stage1-p0:help:02:001` `abstain` vs `replace` | trigger `help` | margin `-0.055`
  sentence: Her help made the move much easier.
- `en-es:sampling-stage1-p0:help:02:003` `abstain` vs `replace` | trigger `help` | margin `-0.017`
  sentence: We need help carrying these boxes upstairs.

### Winner errors

- `en-es:sampling-stage1-p0:help:02:001` `abstain` vs `replace` | trigger `help` | margin `-0.055`
  sentence: Her help made the move much easier.
- `en-es:sampling-stage1-p0:help:02:003` `abstain` vs `replace` | trigger `help` | margin `-0.017`
  sentence: We need help carrying these boxes upstairs.
