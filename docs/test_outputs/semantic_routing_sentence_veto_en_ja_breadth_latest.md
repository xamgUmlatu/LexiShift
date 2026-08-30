# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-06-09T18:13:03Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_breadth_v1.json`
- Pair: `en-ja`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `masked_sentence`
- Evidence view: `all_evidence_text`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Thresholds: `min_active=0.0`, `min_margin=0.02`

## Summary

- Decision accuracy: `96.8%`
- Replace precision / recall: `100.0%` / `92.1%`
- Harmful replace / false abstain: `0.0%` / `7.9%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`
- Predicted replace rate: `36.8%`
- Phrase preemption hit rate / precision: `29.5%` / `100.0%`
- Active rescue applied rate / precision: `0.0%` / `n/a`

## Family Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| ball -> ボール vs 舞踏会 | 5 | 60.0% | 0.0% | 0.0% | 100.0% |
| bank -> 銀行 vs 岸 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| board -> 盤 vs 取締役会 | 5 | 100.0% | 100.0% | 0.0% | 75.0% |
| branch -> 支店 vs 枝 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| cell -> 細胞 vs 独房 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| check -> 小切手 vs 確認する | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| drink -> 飲み物 vs 飲む | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| file -> ファイル vs やすり | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| match -> 試合 vs マッチ | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| order -> 注文 vs 命令する | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| park -> 公園 vs 駐車する | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| plant -> 植物 vs 工場 | 5 | 80.0% | 50.0% | 0.0% | 100.0% |
| play -> 劇 vs 遊ぶ | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| report -> 報告書 vs 報告する | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| seal -> 印章 vs アザラシ | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| spring -> 春 vs ばね | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| table -> テーブル vs 表 | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| trip -> 旅行 vs つまずく | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| watch -> 腕時計 vs 見守る | 5 | 100.0% | 100.0% | 0.0% | 100.0% |

## Gold Winner Type Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| active | 38 | 92.1% | 92.1% | n/a | 100.0% |
| shadow | 38 | 100.0% | n/a | 0.0% | 97.4% |
| none | 19 | 100.0% | n/a | 0.0% | n/a |

## Slice Tag Breakdown

| Slice | Cases | Decision Acc. | Replace Recall | Harmful Replace | Winner Acc. |
| --- | ---: | ---: | ---: | ---: | ---: |
| clear_shadow | 38 | 100.0% | n/a | 0.0% | 97.4% |
| clear_active | 37 | 91.9% | 91.9% | n/a | 100.0% |
| cross_pos | 35 | 100.0% | 100.0% | 0.0% | 100.0% |
| verb | 27 | 100.0% | n/a | 0.0% | 100.0% |
| phrase_control | 19 | 100.0% | n/a | 0.0% | n/a |
| weak_active_support | 15 | 100.0% | 100.0% | n/a | 100.0% |
| lexicalized_expression | 7 | 100.0% | n/a | 0.0% | n/a |
| nature | 6 | 83.3% | 50.0% | 0.0% | 100.0% |
| beverage | 4 | 100.0% | 100.0% | 0.0% | 100.0% |
| document | 4 | 100.0% | 100.0% | n/a | 100.0% |
| finance | 4 | 100.0% | 100.0% | n/a | 100.0% |
| idiom | 4 | 100.0% | n/a | 0.0% | n/a |

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-ja:sentence-veto:ball:001` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The goalkeeper punched the ball over the bar.
- `en-ja:sentence-veto:ball:002` `abstain` vs `replace` | trigger `ball` | margin `0.000`
  sentence: The child kicked the ball into the street.
- `en-ja:sentence-veto:plant:001` `abstain` vs `replace` | trigger `plant` | margin `0.000`
  sentence: She watered the plant on the windowsill.

### Winner errors

- `en-ja:sentence-veto:board:003` `abstain` vs `abstain` | trigger `board` | margin `0.015`
  sentence: The board approved the merger on Tuesday.
