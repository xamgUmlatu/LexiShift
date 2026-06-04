# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-05-06T21:56:09Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_full_family_repaired_pilot_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `off`
- Active rescue mode: `off`
- Thresholds: `min_active=0.05`, `min_margin=0.0`

## Summary

- Decision accuracy: `55.6%`
- Replace precision / recall: `100.0%` / `14.3%`
- Harmful replace / false abstain: `0.0%` / `85.7%`
- Winner accuracy / shadow-winner accuracy: `65.0%` / `16.7%`
- Predicted replace rate: `7.4%`
- Phrase preemption hit rate / precision: `3.7%` / `0.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
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
| active | 14 | 14.3% | 14.3% | n/a | 85.7% |
| shadow | 6 | 100.0% | n/a | 0.0% | 16.7% |
| none | 7 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent_repaired_user_review_pending | 27 | 55.6% | 14.3% | 0.0% | 65.0% |
| en_es_full_family_repaired_pilot_v1 | 27 | 55.6% | 14.3% | 0.0% | 65.0% |
| no_winner_subtype:not_applicable | 20 | 40.0% | 14.3% | 0.0% | 65.0% |
| target_zipf:zipf_3_to_4_mid | 16 | 56.2% | 12.5% | 0.0% | 58.3% |
| active_sense_corrected | 15 | 66.7% | 16.7% | 0.0% | 41.7% |
| pos_shape:cross_pos_polysemy | 15 | 66.7% | 16.7% | 0.0% | 41.7% |
| positive_active | 14 | 14.3% | 14.3% | n/a | 85.7% |
| source_zipf:zipf_5_plus_very_common | 13 | 61.5% | 16.7% | 0.0% | 60.0% |
| aligned_mapping_contexts_rewritten | 12 | 41.7% | 12.5% | 0.0% | 100.0% |
| polysemy:low_1_to_3 | 12 | 41.7% | 12.5% | 0.0% | 100.0% |
| pos_shape:single_sense | 12 | 41.7% | 12.5% | 0.0% | 100.0% |
| polysemy:high_10_plus | 10 | 70.0% | 25.0% | 0.0% | 50.0% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:full-family-repaired-pilot:break:quebrar:001` `abstain` vs `replace` | trigger `break` | margin `0.000`
  sentence: The plate began to break along the rim.
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.068`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:002` `abstain` vs `replace` | trigger `bridle` | margin `0.000`
  sentence: The manager had to bridle his frustration after the call.
- `en-es:full-family-repaired-pilot:december:diciembre:001` `abstain` vs `replace` | trigger `december` | margin `0.039`
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
- `en-es:full-family-repaired-pilot:bridle:reprimir:001` `abstain` vs `replace` | trigger `bridle` | margin `-0.068`
  sentence: She tried to bridle her anger during the meeting.
- `en-es:full-family-repaired-pilot:bridle:reprimir:003` `abstain` vs `abstain` | trigger `bridle` | margin `0.000`
  sentence: She began to bridle at the suggestion that the project had failed.
- `en-es:full-family-repaired-pilot:bridle:reprimir:004` `abstain` vs `abstain` | trigger `bridle` | margin `0.000`
  sentence: The rider checked the bridle before the parade.
- `en-es:full-family-repaired-pilot:control:gobernar:002` `abstain` vs `replace` | trigger `control` | margin `-0.001`
  sentence: A small council continued to control the territory after the coup.
