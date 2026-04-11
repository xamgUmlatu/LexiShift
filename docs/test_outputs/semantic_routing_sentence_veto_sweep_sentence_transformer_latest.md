# Semantic Routing Sentence Veto Sweep

- Status: `ok`
- Generated: `2026-04-11T03:29:26Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v1.json`
- Pair: `en-es`
- Grid size: `64`
- Scorers: `sentence_transformer_cosine`
- Context views: `raw_sentence, masked_sentence, raw_window, masked_window`
- Evidence views: `all_evidence_text`

## Best Overall

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.05`
- Decision accuracy / harmful replace / false abstain: `85.0%` / `0.0%` / `37.5%`
- Replace precision / recall: `100.0%` / `62.5%`
- Winner accuracy / shadow-winner accuracy: `87.5%` / `100.0%`

## Best By Scorer

- Config: `sentence_transformer_cosine:masked_sentence:all_evidence_text:a=0.00:m=0.05`
- Decision accuracy / harmful replace / false abstain: `85.0%` / `0.0%` / `37.5%`
- Replace precision / recall: `100.0%` / `62.5%`
- Winner accuracy / shadow-winner accuracy: `87.5%` / `100.0%`

## Top Configs

| Rank | Scorer | Context | Evidence | min_active | min_margin | Decision Acc. | Harmful Replace | False Abstain | Winner Acc. |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.00 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 2 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.05 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 3 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.10 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 4 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.15 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 5 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.00 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 6 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.05 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 7 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.10 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 8 | sentence_transformer_cosine | masked_window | all_evidence_text | 0.15 | 0.05 | 85.0% | 0.0% | 37.5% | 87.5% |
| 9 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.00 | 0.10 | 75.0% | 0.0% | 62.5% | 87.5% |
| 10 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.05 | 0.10 | 75.0% | 0.0% | 62.5% | 87.5% |
| 11 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.10 | 0.10 | 75.0% | 0.0% | 62.5% | 87.5% |
| 12 | sentence_transformer_cosine | masked_sentence | all_evidence_text | 0.15 | 0.10 | 75.0% | 0.0% | 62.5% | 87.5% |
