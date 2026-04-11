# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-11T04:01:14Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v2.json`
- Pair: `en-es`
- Grid size: `64`
- Scorers: `sentence_transformer_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `all_evidence_text`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.15`
- Decision accuracy / harmful replace / false abstain: `75.0%` / `0.0%` / `62.5%`
- Replace precision / recall: `100.0%` / `37.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Best By Scorer

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.15`
- Decision accuracy / harmful replace / false abstain: `75.0%` / `0.0%` / `62.5%`
- Replace precision / recall: `100.0%` / `37.5%`
- Winner accuracy / shadow-winner accuracy: `93.8%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | min_active | min_margin | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.00 | 0.15 | 75.0% | 0.0% | 62.5% | 93.8% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.05 | 0.15 | 75.0% | 0.0% | 62.5% | 93.8% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.10 | 0.15 | 75.0% | 0.0% | 62.5% | 93.8% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.15 | 0.15 | 75.0% | 0.0% | 62.5% | 93.8% |
| 5 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.00 | 0.15 | 72.5% | 0.0% | 68.8% | 93.8% |
| 6 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.05 | 0.15 | 72.5% | 0.0% | 68.8% | 93.8% |
| 7 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.10 | 0.15 | 72.5% | 0.0% | 68.8% | 93.8% |
| 8 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.15 | 0.15 | 72.5% | 0.0% | 68.8% | 93.8% |
| 9 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.00 | 0.10 | 77.5% | 4.2% | 50.0% | 93.8% |
| 10 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.05 | 0.10 | 77.5% | 4.2% | 50.0% | 93.8% |
| 11 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.10 | 0.10 | 77.5% | 4.2% | 50.0% | 93.8% |
| 12 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.15 | 0.10 | 77.5% | 4.2% | 50.0% | 93.8% |
