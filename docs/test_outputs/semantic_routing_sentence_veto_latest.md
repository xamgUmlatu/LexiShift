# Semantic Routing Sentence Veto Harness

- Status: `ok`
- Generated: `2026-04-11T03:28:50Z`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v1.json`
- Pair: `en-es`
- Scorer: `tfidf_cosine`
- Model: `n/a`
- Context view: `raw_sentence`
- Evidence view: `all_evidence_text`
- Thresholds: `min_active=0.35`, `min_margin=0.05`

## Summary

- Decision accuracy: `60.0%`
- Replace precision / recall: `n/a` / `0.0%`
- Harmful replace / false abstain: `0.0%` / `100.0%`
- Winner accuracy / shadow-winner accuracy: `68.8%` / `75.0%`
- Predicted replace rate: `0.0%`

## Failure Samples

### Harmful replace

- none

### False abstain

- `en-es:sentence-veto:ball:001` `abstain` vs `replace` | trigger `ball` | margin `0.021`
  sentence: The goalkeeper punched the ball over the bar.
- `en-es:sentence-veto:ball:002` `abstain` vs `replace` | trigger `ball` | margin `0.021`
  sentence: The child kicked the ball into the street.
- `en-es:sentence-veto:bank:001` `abstain` vs `replace` | trigger `bank` | margin `-0.004`
  sentence: She deposited the cash at the bank before lunch.
- `en-es:sentence-veto:bank:002` `abstain` vs `replace` | trigger `bank` | margin `-0.005`
  sentence: The bank approved our mortgage application.
- `en-es:sentence-veto:plant:001` `abstain` vs `replace` | trigger `plant` | margin `-0.003`
  sentence: She watered the plant on the windowsill.
- `en-es:sentence-veto:plant:002` `abstain` vs `replace` | trigger `plant` | margin `0.018`
  sentence: The plant needs more sunlight in the afternoon.

### Winner errors

- `en-es:sentence-veto:ball:003` `abstain` vs `abstain` | trigger `ball` | margin `0.022`
  sentence: They danced at the royal ball until dawn.
- `en-es:sentence-veto:ball:004` `abstain` vs `abstain` | trigger `ball` | margin `0.023`
  sentence: The charity ball raised thousands of dollars.
- `en-es:sentence-veto:bank:001` `abstain` vs `replace` | trigger `bank` | margin `-0.004`
  sentence: She deposited the cash at the bank before lunch.
- `en-es:sentence-veto:bank:002` `abstain` vs `replace` | trigger `bank` | margin `-0.005`
  sentence: The bank approved our mortgage application.
- `en-es:sentence-veto:plant:001` `abstain` vs `replace` | trigger `plant` | margin `-0.003`
  sentence: She watered the plant on the windowsill.
