# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-23T04:38:24Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v8.json`
- Pair: `en-es`
- Grid size: `96`
- Scorers: `tfidf_cosine, sentence_transformer_cosine`
- Context views: `masked_sentence`
- Evidence views: `all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `19`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `77.6%` / `0.0%` / `55.9%`
- Replace precision / recall: `100.0%` / `44.1%`
- Winner accuracy / shadow-winner accuracy: `86.8%` / `100.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `19`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `77.6%` / `0.0%` / `55.9%`
- Replace precision / recall: `100.0%` / `44.1%`
- Winner accuracy / shadow-winner accuracy: `86.8%` / `100.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `6`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `91.8%` / `2.0%` / `17.6%`
- Replace precision / recall: `96.6%` / `82.4%`
- Winner accuracy / shadow-winner accuracy: `91.2%` / `100.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `6`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `91.8%` / `2.0%` / `17.6%`
- Replace precision / recall: `96.6%` / `82.4%`
- Winner accuracy / shadow-winner accuracy: `91.2%` / `100.0%`

## Best Objective

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `1` / `6`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `91.8%` / `2.0%` / `17.6%`
- Replace precision / recall: `96.6%` / `82.4%`
- Winner accuracy / shadow-winner accuracy: `91.2%` / `100.0%`


## Best By Scorer

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `22`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `74.1%` / `0.0%` / `64.7%`
- Replace precision / recall: `100.0%` / `35.3%`
- Winner accuracy / shadow-winner accuracy: `64.7%` / `35.3%`

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.00:m=0.10`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `19`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `2` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `77.6%` / `0.0%` / `55.9%`
- Replace precision / recall: `100.0%` / `44.1%`
- Winner accuracy / shadow-winner accuracy: `86.8%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.10 | 0 | 7 | 2 | 77.6% | 0.0% | 55.9% | 86.8% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.10 | 0 | 7 | 2 | 77.6% | 0.0% | 55.9% | 86.8% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.10 | 0.10 | 0 | 7 | 2 | 77.6% | 0.0% | 55.9% | 86.8% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.15 | 0.10 | 0 | 7 | 2 | 77.6% | 0.0% | 55.9% | 86.8% |
| 5 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.00 | 0.10 | 0 | 7 | 0 | 75.3% | 0.0% | 61.8% | 86.8% |
| 6 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.05 | 0.10 | 0 | 7 | 0 | 75.3% | 0.0% | 61.8% | 86.8% |
| 7 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.10 | 0.10 | 0 | 7 | 0 | 75.3% | 0.0% | 61.8% | 86.8% |
| 8 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.15 | 0.10 | 0 | 7 | 0 | 75.3% | 0.0% | 61.8% | 86.8% |
| 9 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 7 | 2 | 74.1% | 0.0% | 64.7% | 64.7% |
| 10 | tfidf_cosine | masked_sentence | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 7 | 2 | 74.1% | 0.0% | 64.7% | 64.7% |
| 11 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 7 | 2 | 72.9% | 0.0% | 67.6% | 64.7% |
| 12 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 7 | 2 | 72.9% | 0.0% | 67.6% | 64.7% |
