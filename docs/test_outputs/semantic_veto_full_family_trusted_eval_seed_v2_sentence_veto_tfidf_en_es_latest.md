# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T22:45:42Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_trusted_eval_seed_v2.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `59.5%`
- Replace precision / recall: `100.0%` / `15.0%`
- Harmful replace / false abstain: `0.0%` / `85.0%`
- Winner accuracy / shadow-winner accuracy: `56.2%` / `8.3%`
- Predicted replace rate: `7.1%`
- Phrase preemption hit rate / precision: `2.4%` / `0.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| bar -> cercar vs taberna, barra | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| crack -> grieta vs broma, chasquido | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| offset -> distancia vs compensar, compensación | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| bouillon -> caldo | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| break -> quebrar vs interrumpir, oportunidad | 5 | 80.0% | 50.0% | 0.0% | 50.0% |
| bridle -> reprimir vs ofenderse, brida | 5 | 60.0% | 0.0% | 0.0% | 25.0% |
| control -> gobernar vs controlar, grupo de control | 5 | 60.0% | 0.0% | 0.0% | 50.0% |
| december -> diciembre | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| dentist -> dentista | 3 | 33.3% | 0.0% | 0.0% | 100.0% |
| emotion -> emoción | 3 | 66.7% | 50.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 20 | 15.0% | 15.0% | n/a | 85.0% |
| shadow | 12 | 100.0% | n/a | 0.0% | 8.3% |
| none | 10 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| approved_by_user | 42 | 59.5% | 15.0% | 0.0% | 56.2% |
| en_es_full_family_trusted_eval_seed_v2 | 42 | 59.5% | 15.0% | 0.0% | 56.2% |
| trusted | 42 | 59.5% | 15.0% | 0.0% | 56.2% |
| trusted_eval_seed_v2 | 42 | 59.5% | 15.0% | 0.0% | 56.2% |
| no_winner_subtype:not_applicable | 32 | 46.9% | 15.0% | 0.0% | 56.2% |
| pos_shape:cross_pos_polysemy | 30 | 66.7% | 16.7% | 0.0% | 41.7% |
| carried_forward_from_v1 | 27 | 55.6% | 14.3% | 0.0% | 65.0% |
| polysemy:high_10_plus | 25 | 68.0% | 20.0% | 0.0% | 45.0% |
| target_zipf:zipf_3_to_4_mid | 21 | 61.9% | 20.0% | 0.0% | 56.2% |
| positive_active | 20 | 15.0% | 15.0% | n/a | 85.0% |
| active_sense_corrected | 15 | 66.7% | 16.7% | 0.0% | 41.7% |
| newly_approved_deferred_fix | 15 | 66.7% | 16.7% | 0.0% | 41.7% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:full-family-repaired-pilot:break:quebrar:001` `abstain` vs `replace` | trigger `break` | margin `0.000`
  sentence: The plate began to break along the rim.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.070`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `0.000`
  sentence: The manager had to bridle his frustration after the call.
- `en-es:full-family-repaired-pilot:december:diciembre:001` `abstain` vs `replace` | trigger `december` | margin `0.033`
  phrase preemption: `infinitive_trigger_frame` | `to december`
  sentence: The conference moved to December after the venue delay.
- `en-es:full-family-repaired-pilot:december:diciembre:002` `abstain` vs `replace` | trigger `december` | margin `0.000`
  sentence: Their lease expires in December.
- `en-es:full-family-repaired-pilot:emotion:emoci-n:002` `abstain` vs `replace` | trigger `emotion` | margin `0.000`
  sentence: She hid every emotion during the interview.

### Winner errors

- `en-es:full-family-repaired-pilot:break:quebrar:003` `abstain` vs `abstain` | trigger `break` | margin `0.000`
  sentence: A news alert can break the broadcast without warning.
- `en-es:full-family-repaired-pilot:break:quebrar:004` `abstain` vs `abstain` | trigger `break` | margin `0.000`
  sentence: Her internship became the big break that launched her career.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.070`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:003` `abstain` vs `abstain` | trigger `bridle` | margin `0.000`
  sentence: She began to bridle at the suggestion that the project had failed.
- `en-es:full-family-repaired-pilot:bridle:reprimir:004` `abstain` vs `abstain` | trigger `bridle` | margin `0.000`
  sentence: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-pilot:control:gobernar:002` `abstain` vs `replace` | trigger `control` | margin `-0.001`
  sentence: A small council continued to control the territory after the coup.
