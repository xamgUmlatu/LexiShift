# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-11T03:34:04Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v1.json`
- Pair: `en-es`
- Grid size: `768`
- Scorers: `token_jaccard, tfidf_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `sense_label, gloss_text, all_evidence_text`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Decision accuracy / harmful replace / false abstain: `70.0%` / `0.0%` / `75.0%`
- Replace precision / recall: `100.0%` / `25.0%`
- Winner accuracy / shadow-winner accuracy: `68.8%` / `37.5%`

## Best By Scorer

- Config: `token_jaccard:raw_sentence:all_evidence_text:a=0.15:m=0.00`
- Decision accuracy / harmful replace / false abstain: `65.0%` / `0.0%` / `87.5%`
- Replace precision / recall: `100.0%` / `12.5%`
- Winner accuracy / shadow-winner accuracy: `62.5%` / `75.0%`

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Decision accuracy / harmful replace / false abstain: `70.0%` / `0.0%` / `75.0%`
- Replace precision / recall: `100.0%` / `25.0%`
- Winner accuracy / shadow-winner accuracy: `68.8%` / `37.5%`

## Top Configs

| Rank | Scorer | Context | Evidence | min_active | min_margin | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.00 | 70.0% | 0.0% | 75.0% | 68.8% |
| 2 | tfidf_cosine | masked_window | all_evidence_text | 0.05 | 0.00 | 70.0% | 0.0% | 75.0% | 62.5% |
| 3 | tfidf_cosine | masked_sentence | all_evidence_text | 0.00 | 0.05 | 65.0% | 0.0% | 87.5% | 68.8% |
| 4 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.05 | 65.0% | 0.0% | 87.5% | 68.8% |
| 5 | token_jaccard | raw_sentence | all_evidence_text | 0.15 | 0.00 | 65.0% | 0.0% | 87.5% | 62.5% |
| 6 | token_jaccard | raw_sentence | all_evidence_text | 0.15 | 0.05 | 65.0% | 0.0% | 87.5% | 62.5% |
| 7 | token_jaccard | raw_window | all_evidence_text | 0.15 | 0.00 | 65.0% | 0.0% | 87.5% | 62.5% |
| 8 | token_jaccard | raw_window | all_evidence_text | 0.15 | 0.05 | 65.0% | 0.0% | 87.5% | 62.5% |
| 9 | token_jaccard | masked_sentence | all_evidence_text | 0.10 | 0.00 | 65.0% | 0.0% | 87.5% | 62.5% |
| 10 | token_jaccard | masked_sentence | all_evidence_text | 0.10 | 0.05 | 65.0% | 0.0% | 87.5% | 62.5% |
| 11 | tfidf_cosine | masked_window | all_evidence_text | 0.00 | 0.05 | 65.0% | 0.0% | 87.5% | 62.5% |
| 12 | tfidf_cosine | masked_window | all_evidence_text | 0.05 | 0.05 | 65.0% | 0.0% | 87.5% | 62.5% |
