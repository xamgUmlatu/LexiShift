# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-06-09T18:08:41Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_ja_sentence_veto_breadth_v1.json`
- Pair: `en-ja`
- Grid size: `10240`
- Scorers: `token_jaccard, tfidf_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `sense_label, gloss_text, sense_gloss_bundle, all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`
- Phrase guard POS scopes: `family_all, active_only`
- Active rescue modes: `off, sense_label_near_tie_active_rescue`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=off:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=sense_label_near_tie_active_rescue:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

- Budget: `harmful_replace_count <= 1`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=sense_label_near_tie_active_rescue:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

- Budget: `harmful_replace_count <= 2`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=sense_label_near_tie_active_rescue:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

- Budget: `harmful_replace_count <= 5`
- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=sense_label_near_tie_active_rescue:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

## Best Objective

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=sense_label_near_tie_active_rescue:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `sense_label_near_tie_active_rescue`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`


## Best By Scorer

- Config: `token_jaccard:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=off:a=0.10:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `16`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `83.2%` / `0.0%` / `42.1%`
- Replace precision / recall: `100.0%` / `57.9%`
- Winner accuracy / shadow-winner accuracy: `96.1%` / `92.1%`

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:g=active_only:r=off:a=0.00:m=0.02`
- Phrase control mode: `noun_family_frame_guard`
- Phrase guard POS scope: `active_only`
- Active rescue mode: `off`
- Harmful replace count / false abstain count: `0` / `3`
- Phrase preemption hit count / precision: `28` / `100.0%`
- Active rescue hit count / precision: `0` / `n/a`
- Decision accuracy / harmful replace / false abstain: `96.8%` / `0.0%` / `7.9%`
- Replace precision / recall: `100.0%` / `92.1%`
- Winner accuracy / shadow-winner accuracy: `98.7%` / `97.4%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | POS Scope | Rescue Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Rescue Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.00 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 98.7% |
| 2 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.01 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 98.7% |
| 3 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | sense_label_near_tie_active_rescue | 0.00 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 98.7% |
| 4 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | sense_label_near_tie_active_rescue | 0.01 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 98.7% |
| 5 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | active_only | off | 0.00 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 97.4% |
| 6 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | active_only | off | 0.01 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 97.4% |
| 7 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | active_only | sense_label_near_tie_active_rescue | 0.00 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 97.4% |
| 8 | tfidf_cosine | masked_window | all_evidence_text | noun_family_frame_guard | active_only | sense_label_near_tie_active_rescue | 0.01 | 0.02 | 0 | 28 | 0 | 96.8% | 0.0% | 7.9% | 97.4% |
| 9 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.00 | 0.05 | 0 | 28 | 0 | 91.6% | 0.0% | 21.1% | 98.7% |
| 10 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.01 | 0.05 | 0 | 28 | 0 | 91.6% | 0.0% | 21.1% | 98.7% |
| 11 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.05 | 0.00 | 0 | 28 | 0 | 91.6% | 0.0% | 21.1% | 98.7% |
| 12 | tfidf_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | active_only | off | 0.05 | 0.02 | 0 | 28 | 0 | 91.6% | 0.0% | 21.1% | 98.7% |
