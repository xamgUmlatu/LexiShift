# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-23T19:15:19Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Pair: `en-es`
- Grid size: `128`
- Scorers: `sentence_transformer_cosine`
- Context views: `masked_sentence`
- Evidence views: `all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `23`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `75.8%` / `0.0%` / `60.5%`
- Replace precision / recall: `100.0%` / `39.5%`
- Winner accuracy / shadow-winner accuracy: `84.2%` / `100.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `23`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `75.8%` / `0.0%` / `60.5%`
- Replace precision / recall: `100.0%` / `39.5%`
- Winner accuracy / shadow-winner accuracy: `84.2%` / `100.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `9`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `89.5%` / `1.8%` / `23.7%`
- Replace precision / recall: `96.7%` / `76.3%`
- Winner accuracy / shadow-winner accuracy: `88.2%` / `100.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `9`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `89.5%` / `1.8%` / `23.7%`
- Replace precision / recall: `96.7%` / `76.3%`
- Winner accuracy / shadow-winner accuracy: `88.2%` / `100.0%`

## Best Objective

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `9`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `89.5%` / `1.8%` / `23.7%`
- Replace precision / recall: `96.7%` / `76.3%`
- Winner accuracy / shadow-winner accuracy: `88.2%` / `100.0%`


## Best By Scorer

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `23`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `75.8%` / `0.0%` / `60.5%`
- Replace precision / recall: `100.0%` / `39.5%`
- Winner accuracy / shadow-winner accuracy: `84.2%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.10 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.15 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 5 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.25 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 6 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.35 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 7 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.45 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 8 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.55 | 0.10 | 0 | 7 | 2 | 75.8% | 0.0% | 60.5% | 84.2% |
| 9 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.00 | 0.10 | 0 | 7 | 0 | 73.7% | 0.0% | 65.8% | 84.2% |
| 10 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.05 | 0.10 | 0 | 7 | 0 | 73.7% | 0.0% | 65.8% | 84.2% |
| 11 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.10 | 0.10 | 0 | 7 | 0 | 73.7% | 0.0% | 65.8% | 84.2% |
| 12 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.15 | 0.10 | 0 | 7 | 0 | 73.7% | 0.0% | 65.8% | 84.2% |
