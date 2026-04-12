# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-12T20:43:59Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Grid size: `32`
- Scorers: `sentence_transformer_cosine`
- Context views: `masked_sentence`
- Evidence views: `all_evidence_text`
- Phrase control modes: `off, noun_family_frame_guard`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Best Objective

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`


## Best By Scorer

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:p=noun_family_frame_guard:a=0.00:m=0.00`
- Phrase control mode: `noun_family_frame_guard`
- Harmful replace count / false abstain count: `0` / `2`
- Phrase preemption hit count / precision: `5` / `100.0%`
- Decision accuracy / harmful replace / false abstain: `95.0%` / `0.0%` / `12.5%`
- Replace precision / recall: `100.0%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | Phrase Mode | min_active | min_margin | Harmful Cnt | Phrase Hits | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.00 | 0.00 | 0 | 5 | 95.0% | 0.0% | 12.5% | 93.8% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.05 | 0.00 | 0 | 5 | 95.0% | 0.0% | 12.5% | 93.8% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.10 | 0.00 | 0 | 5 | 95.0% | 0.0% | 12.5% | 93.8% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.15 | 0.00 | 0 | 5 | 95.0% | 0.0% | 12.5% | 93.8% |
| 5 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.00 | 0.05 | 0 | 5 | 87.5% | 0.0% | 31.2% | 93.8% |
| 6 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.05 | 0.05 | 0 | 5 | 87.5% | 0.0% | 31.2% | 93.8% |
| 7 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.10 | 0.05 | 0 | 5 | 87.5% | 0.0% | 31.2% | 93.8% |
| 8 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.15 | 0.05 | 0 | 5 | 87.5% | 0.0% | 31.2% | 93.8% |
| 9 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.00 | 0.10 | 0 | 5 | 80.0% | 0.0% | 50.0% | 93.8% |
| 10 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.05 | 0.10 | 0 | 5 | 80.0% | 0.0% | 50.0% | 93.8% |
| 11 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.10 | 0.10 | 0 | 5 | 80.0% | 0.0% | 50.0% | 93.8% |
| 12 | sentence_transformer_cosine | masked_sentence | all_evidence_text | noun_family_frame_guard | 0.15 | 0.10 | 0 | 5 | 80.0% | 0.0% | 50.0% | 93.8% |
