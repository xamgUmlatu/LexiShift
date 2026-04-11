# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-11T04:00:41Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Grid size: `768`
- Scorers: `token_jaccard, tfidf_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `sense_label, gloss_text, all_evidence_text`

## Best Overall

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Decision accuracy / harmful replace / false abstain: `77.5%` / `0.0%` / `56.2%`
- Replace precision / recall: `100.0%` / `43.8%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`

## Best By Scorer

- Config: `token_jaccard:raw_sentence:all_evidence_text:a=0.15:m=0.00`
- Decision accuracy / harmful replace / false abstain: `67.5%` / `0.0%` / `81.2%`
- Replace precision / recall: `100.0%` / `18.8%`
- Winner accuracy / shadow-winner accuracy: `71.9%` / `68.8%`

- Config: `tfidf_cosine:masked_sentence:all_evidence_text:a=0.05:m=0.00`
- Decision accuracy / harmful replace / false abstain: `77.5%` / `0.0%` / `56.2%`
- Replace precision / recall: `100.0%` / `43.8%`
- Winner accuracy / shadow-winner accuracy: `75.0%` / `50.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | min_active | min_margin | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.00 | 77.5% | 0.0% | 56.2% | 75.0% |
| 2 | tfidf_cosine | masked_sentence | all_evidence_text | 0.00 | 0.05 | 75.0% | 0.0% | 62.5% | 75.0% |
| 3 | tfidf_cosine | masked_sentence | all_evidence_text | 0.05 | 0.05 | 75.0% | 0.0% | 62.5% | 75.0% |
| 4 | tfidf_cosine | masked_window | all_evidence_text | 0.05 | 0.00 | 75.0% | 0.0% | 62.5% | 68.8% |
| 5 | tfidf_cosine | masked_window | all_evidence_text | 0.00 | 0.05 | 72.5% | 0.0% | 68.8% | 68.8% |
| 6 | tfidf_cosine | masked_window | all_evidence_text | 0.05 | 0.05 | 72.5% | 0.0% | 68.8% | 68.8% |
| 7 | tfidf_cosine | raw_sentence | all_evidence_text | 0.00 | 0.10 | 67.5% | 0.0% | 81.2% | 75.0% |
| 8 | tfidf_cosine | raw_sentence | all_evidence_text | 0.05 | 0.10 | 67.5% | 0.0% | 81.2% | 75.0% |
| 9 | tfidf_cosine | raw_sentence | all_evidence_text | 0.10 | 0.00 | 67.5% | 0.0% | 81.2% | 75.0% |
| 10 | tfidf_cosine | raw_sentence | all_evidence_text | 0.10 | 0.05 | 67.5% | 0.0% | 81.2% | 75.0% |
| 11 | tfidf_cosine | raw_sentence | all_evidence_text | 0.10 | 0.10 | 67.5% | 0.0% | 81.2% | 75.0% |
| 12 | tfidf_cosine | raw_window | all_evidence_text | 0.00 | 0.10 | 67.5% | 0.0% | 81.2% | 75.0% |
