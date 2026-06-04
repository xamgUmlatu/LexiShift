# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-28T18:07:13Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- Pair: `en-es`
- Grid size: `3072`
- Scorers: `token_jaccard, tfidf_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `sense_label, gloss_text, all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`

- Budget: `harmful_replace_count <= 1`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`

- Budget: `harmful_replace_count <= 2`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`

## Best Objective

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`


## Best By Scorer

- Config: `token_jaccard:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.10:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `32`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `66.3%` / `0.0%` / `84.2%`
- Replace precision / recall: `100.0%` / `15.8%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `34.2%`

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=sense_label_near_tie_active_rescue:a=0.05:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `25`
- Phrase preemption hit count / precision: `8` / `100.0%`
- Active rescue hit count / precision: `3` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `73.7%` / `0.0%` / `65.8%`
- Replace precision / recall: `100.0%` / `34.2%`
- Winner accuracy / shadow-winner accuracy: `63.2%` / `31.6%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 8 | 3 | 73.7% | 0.0% | 65.8% | 63.2% |
| 2 | tfidf_cosine | masked_sentence | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 8 | 3 | 73.7% | 0.0% | 65.8% | 63.2% |
| 3 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 63.2% |
| 4 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 63.2% |
| 5 | tfidf_cosine | masked_sentence | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 63.2% |
| 6 | tfidf_cosine | masked_sentence | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 63.2% |
| 7 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 59.2% |
| 8 | tfidf_cosine | masked_window | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 8 | 3 | 72.6% | 0.0% | 68.4% | 59.2% |
| 9 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 8 | 3 | 71.6% | 0.0% | 71.1% | 59.2% |
| 10 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 8 | 3 | 71.6% | 0.0% | 71.1% | 59.2% |
| 11 | tfidf_cosine | masked_window | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 8 | 3 | 71.6% | 0.0% | 71.1% | 59.2% |
| 12 | tfidf_cosine | masked_window | all_evidence_text | off | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 8 | 3 | 71.6% | 0.0% | 71.1% | 59.2% |
