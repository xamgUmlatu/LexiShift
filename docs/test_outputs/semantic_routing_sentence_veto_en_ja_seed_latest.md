# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-06-09T17:17:14Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_seed_v1.json`
- Pair: `en-ja`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Thresholds: `min_active=0.0`, `min_margin=0.05`

## Summary

- Decision accuracy: `92.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Harmful replace / false abstain: `0.0%` / `20.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`
- Predicted replace rate: `32.0%`
- Phrase preemption hit rate / precision: `14.0%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| ball -> ボール vs 舞踏会 | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| bank -> 銀行 vs 岸 | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| board -> 盤 vs 取締役会 | 5 | 100.0% | 100.0% | 0.0% | 75.0% |
| cell -> 細胞 vs 独房 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| file -> ファイル vs やすり | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| match -> 試合 vs マッチ | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| plant -> 植物 vs 工場 | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| seal -> 印章 vs アザラシ | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| spring -> 春 vs ばね | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| table -> テーブル vs 表 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 20 | 80.0% | 80.0% | n/a | 100.0% |
| shadow | 20 | 100.0% | n/a | 0.0% | 95.0% |
| none | 10 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| clear_active | 20 | 80.0% | 80.0% | n/a | 100.0% |
| clear_shadow | 20 | 100.0% | n/a | 0.0% | 95.0% |
| phrase_control | 10 | 100.0% | n/a | 0.0% | n/a |
| verb | 6 | 100.0% | n/a | 0.0% | n/a |
| nature | 4 | 75.0% | 50.0% | 0.0% | 100.0% |
| sports | 4 | 50.0% | 50.0% | n/a | 100.0% |
| tool | 4 | 100.0% | n/a | 0.0% | 100.0% |
| animal | 2 | 100.0% | n/a | 0.0% | 100.0% |
| biology | 2 | 100.0% | 100.0% | n/a | 100.0% |
| data | 2 | 100.0% | n/a | 0.0% | 100.0% |
| document | 2 | 100.0% | 100.0% | n/a | 100.0% |
| event | 2 | 100.0% | n/a | 0.0% | 100.0% |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-ja:sentence-veto:ball:001` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The goalkeeper punched the ball over the bar.
- `en-ja:sentence-veto:ball:002` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The child kicked the ball into the street.
- `en-ja:sentence-veto:bank:001` `abstain` vs `replace` | trigger `bank` | margin `0.046`
  sentence: She deposited the cash at the bank before lunch.
- `en-ja:sentence-veto:plant:001` `abstain` vs `replace` | trigger `plant` | margin `0.000`
  sentence: She watered the plant on the windowsill.

### Winner errors

- `en-ja:sentence-veto:board:003` `abstain` vs `abstain` | trigger `board` | margin `0.018`
  sentence: The board approved the merger on Tuesday.
