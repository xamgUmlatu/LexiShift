# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-11T04:46:10Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Grid size: `32`
- Scorers: `tfidf_cosine, sentence_transformer_cosine`
- Context views: `masked_sentence`
- Evidence views: `all_evidence_text`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Harmful replace count / false abstain count: `0` / `9`
- Decision accuracy / harmful replace / false abstain: `77.5%` / `0.0%` / `56.2%`
- Replace precision / recall: `100.0%` / `43.8%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`

## Best By Harmful-Replace Budget

- Budget: `harmful_replace_count <= 0`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.15`
- Harmful replace count / false abstain count: `0` / `10`
- Decision accuracy / harmful replace / false abstain: `75.0%` / `0.0%` / `62.5%`
- Replace precision / recall: `100.0%` / `37.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

- Budget: `harmful_replace_count <= 1`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.10`
- Harmful replace count / false abstain count: `1` / `8`
- Decision accuracy / harmful replace / false abstain: `77.5%` / `4.2%` / `50.0%`
- Replace precision / recall: `88.9%` / `50.0%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

- Budget: `harmful_replace_count <= 2`
- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.05`
- Harmful replace count / false abstain count: `2` / `5`
- Decision accuracy / harmful replace / false abstain: `82.5%` / `8.3%` / `31.2%`
- Replace precision / recall: `84.6%` / `68.8%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Best Objective

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.00`
- Harmful replace count / false abstain count: `3` / `2`
- Decision accuracy / harmful replace / false abstain: `87.5%` / `12.5%` / `12.5%`
- Replace precision / recall: `82.4%` / `87.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`


## Best By Scorer

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Harmful replace count / false abstain count: `0` / `9`
- Decision accuracy / harmful replace / false abstain: `77.5%` / `0.0%` / `56.2%`
- Replace precision / recall: `100.0%` / `43.8%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.15`
- Harmful replace count / false abstain count: `0` / `10`
- Decision accuracy / harmful replace / false abstain: `75.0%` / `0.0%` / `62.5%`
- Replace precision / recall: `100.0%` / `37.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | min_active | min_margin | Harmful Cnt | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.00 | 0 | 77.5% | 0.0% | 56.2% | 75.0% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.00 | 0.15 | 0 | 75.0% | 0.0% | 62.5% | 93.8% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.05 | 0.15 | 0 | 75.0% | 0.0% | 62.5% | 93.8% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.10 | 0.15 | 0 | 75.0% | 0.0% | 62.5% | 93.8% |
| 5 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.15 | 0.15 | 0 | 75.0% | 0.0% | 62.5% | 93.8% |
| 6 | tfidf_cosine | masked_sentence | all_evidence_text | 0.00 | 0.05 | 0 | 75.0% | 0.0% | 62.5% | 75.0% |
| 7 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.05 | 0 | 75.0% | 0.0% | 62.5% | 75.0% |
| 8 | tfidf_cosine | masked_sentence | all_evidence_text | 0.00 | 0.10 | 0 | 62.5% | 0.0% | 93.8% | 75.0% |
| 9 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.10 | 0 | 62.5% | 0.0% | 93.8% | 75.0% |
| 10 | tfidf_cosine | masked_sentence | all_evidence_text | 0.10 | 0.00 | 0 | 62.5% | 0.0% | 93.8% | 75.0% |
| 11 | tfidf_cosine | masked_sentence | all_evidence_text | 0.10 | 0.05 | 0 | 62.5% | 0.0% | 93.8% | 75.0% |
| 12 | tfidf_cosine | masked_sentence | all_evidence_text | 0.10 | 0.10 | 0 | 62.5% | 0.0% | 93.8% | 75.0% |
