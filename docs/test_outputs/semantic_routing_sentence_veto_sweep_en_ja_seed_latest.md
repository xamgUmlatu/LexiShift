# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-06-09T17:16:12Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_seed_v1.json`
- Pair: `en-ja`
- Grid size: `5120`
- Scorers: `token_jaccard, tfidf_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `sense_label, gloss_text, sense_gloss_bundle, all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=off:a=0.00:m=0.05`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

- Budget: `harmful_replace_count <= 5`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

## Best Objective

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=off:r=sense_label_near_tie_active_rescue:a=0.00:m=0.05`
- Phrase control mode: `off`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`


## Best By Scorer

- Config: `token_jaccard:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=off:a=0.10:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `8`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `84.0%` / `0.0%` / `40.0%`
- Replace precision / recall: `100.0%` / `60.0%`
- Winner accuracy / shadow-winner accuracy: `92.5%` / `85.0%`

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:r=off:a=0.00:m=0.05`
- Phrase control mode: `noun_family_frame_guard`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `4`
- Phrase preemption hit count / precision: `7` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `92.0%` / `0.0%` / `20.0%`
- Replace precision / recall: `100.0%` / `80.0%`
- Winner accuracy / shadow-winner accuracy: `97.5%` / `95.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.00 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 2 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.01 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 3 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.05 | 0.00 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 4 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.05 | 0.02 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 5 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | off | 0.05 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 6 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.00 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 7 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.01 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 8 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.00 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 9 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.02 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 10 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | sense_label_near_tie_active_rescue | 0.05 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 11 | tfidf_cosine | masked_sentence | all_evidence_text | off | off | 0.00 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
| 12 | tfidf_cosine | masked_sentence | all_evidence_text | off | off | 0.01 | 0.05 | 0 | 7 | 0 | 92.0% | 0.0% | 20.0% | 97.5% |
