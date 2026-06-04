# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-12T21:04:05Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Grid size: `32`
- Scorers: `sentence_transformer_cosine`
- Context views: `masked_sentence`
- Evidence views: `gloss_text`
- Phrase control modes: `noun_family_frame_guard`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`

## Best Objective

- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`


## Best By Scorer

- Config: `sentence_transformer_cosine:masked_sentence:gloss_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `0`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Active rescue hit count / precision: `1` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `100.0%` / `0.0%` / `0.0%`
- Replace precision / recall: `100.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `100.0%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.00 | 0 | 5 | 1 | 100.0% | 0.0% | 0.0% | 100.0% |
| 2 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 5 | 1 | 100.0% | 0.0% | 0.0% | 100.0% |
| 3 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.10 | 0.00 | 0 | 5 | 1 | 100.0% | 0.0% | 0.0% | 100.0% |
| 4 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.15 | 0.00 | 0 | 5 | 1 | 100.0% | 0.0% | 0.0% | 100.0% |
| 5 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | off | 0.00 | 0.00 | 0 | 5 | 0 | 97.5% | 0.0% | 6.2% | 96.9% |
| 6 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | off | 0.05 | 0.00 | 0 | 5 | 0 | 97.5% | 0.0% | 6.2% | 96.9% |
| 7 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | off | 0.10 | 0.00 | 0 | 5 | 0 | 97.5% | 0.0% | 6.2% | 96.9% |
| 8 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | off | 0.15 | 0.00 | 0 | 5 | 0 | 97.5% | 0.0% | 6.2% | 96.9% |
| 9 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 5 | 1 | 87.5% | 0.0% | 31.2% | 96.9% |
| 10 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 5 | 1 | 87.5% | 0.0% | 31.2% | 96.9% |
| 11 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.10 | 0.05 | 0 | 5 | 1 | 87.5% | 0.0% | 31.2% | 96.9% |
| 12 | sentence_transformer_cosine | masked_sentence | gloss_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.15 | 0.05 | 0 | 5 | 1 | 87.5% | 0.0% | 31.2% | 96.9% |
