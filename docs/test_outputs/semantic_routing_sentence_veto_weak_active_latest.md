# Semantic Routing Sentence Veto Weak-Active Probe

- Status: `ok`
- Generated: `2026-04-23T05:06:53Z`
- Dataset: `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v9.json`
- Pair: `en-es`
- Focus slice tags: `weak_active_support`
- Focus cases: `en-es:sentence-veto:park:001, en-es:sentence-veto:park:002, en-es:sentence-veto:drink:001, en-es:sentence-veto:drink:002, en-es:sentence-veto:play:001, en-es:sentence-veto:play:002, en-es:sentence-veto:watch:001, en-es:sentence-veto:watch:002, en-es:sentence-veto:check:001, en-es:sentence-veto:check:002, en-es:sentence-veto:order:001, en-es:sentence-veto:order:002, en-es:sentence-veto:trip:002, en-es:sentence-veto:ball:002, en-es:sentence-veto:plant:002`
- Base scorer: `sentence_transformer_cosine`
- Base context / evidence: `masked_sentence` / `all_evidence_text`
- Selected overlay: `Best bounded rescue overlay`
- Zero-harm overlay available: `no`

## Configuration Summary

| Config | Kind | Harmful | False Abstain | Replace Recall | Decision Acc. | Winner Acc. | Rescue Cases |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Current default runtime row | runtime_row | 1 | 7 | 80.6% | 91.1% | 90.3% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:play:001` |
| Masked sentence plus sense-label primary | runtime_row | 4 | 8 | 77.8% | 86.7% | 87.5% | none |
| Raw sentence plus all-evidence primary | runtime_row | 5 | 0 | 100.0% | 94.4% | 97.2% | none |
| Raw window plus all-evidence primary | runtime_row | 5 | 1 | 97.2% | 93.3% | 95.8% | none |
| Best bounded rescue overlay | simulated_rescue_overlay | 1 | 4 | 88.9% | 94.4% | 94.4% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |

## Overlay Sweep

| Rank | Primary Margin Floor | Backup Margin Floor | Harmful | False Abstain | Replace Recall | Decision Acc. | Rescue Cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | -0.05 | 0.02 | 1 | 4 | 88.9% | 94.4% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |
| 2 | -0.03 | 0.02 | 1 | 5 | 86.1% | 93.3% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |
| 3 | -0.04 | 0.02 | 1 | 5 | 86.1% | 93.3% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:001` |
| 4 | -0.02 | 0.02 | 1 | 7 | 80.6% | 91.1% | `en-es:sentence-veto:ball:002`, `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:play:001` |

## Focus Case Outcomes

| Config | Case | Gold | Predicted | Margin | Backup Margin | Rescue |
| --- | --- | --- | --- | ---: | ---: | --- |
| current_default | en-es:sentence-veto:park:001 | replace | abstain | -0.042 | n/a | no |
| current_default | en-es:sentence-veto:park:002 | replace | replace | 0.008 | n/a | no |
| current_default | en-es:sentence-veto:drink:001 | replace | replace | -0.012 | 0.058 | yes |
| current_default | en-es:sentence-veto:drink:002 | replace | abstain | -0.021 | n/a | no |
| current_default | en-es:sentence-veto:play:001 | replace | replace | -0.017 | 0.049 | yes |
| current_default | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | n/a | no |
| current_default | en-es:sentence-veto:watch:001 | replace | replace | 0.001 | n/a | no |
| current_default | en-es:sentence-veto:watch:002 | replace | replace | 0.095 | n/a | no |
| current_default | en-es:sentence-veto:check:001 | replace | replace | 0.106 | n/a | no |
| current_default | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | n/a | no |
| current_default | en-es:sentence-veto:order:001 | replace | replace | 0.065 | n/a | no |
| current_default | en-es:sentence-veto:order:002 | replace | abstain | -0.011 | -0.049 | no |
| current_default | en-es:sentence-veto:trip:002 | replace | abstain | -0.013 | -0.034 | no |
| current_default | en-es:sentence-veto:ball:002 | replace | replace | -0.012 | 0.021 | yes |
| current_default | en-es:sentence-veto:plant:002 | replace | abstain | -0.020 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:park:001 | replace | replace | 0.068 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:park:002 | replace | replace | 0.055 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:drink:001 | replace | replace | 0.058 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:drink:002 | replace | replace | 0.050 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:play:001 | replace | replace | 0.049 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:play:002 | replace | abstain | -0.022 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:watch:001 | replace | abstain | -0.074 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:watch:002 | replace | abstain | -0.051 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:check:001 | replace | replace | 0.077 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:check:002 | replace | abstain | -0.007 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:order:001 | replace | abstain | -0.003 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:order:002 | replace | abstain | -0.049 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:trip:002 | replace | abstain | -0.034 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:ball:002 | replace | replace | 0.021 | n/a | no |
| masked_sense_label_primary | en-es:sentence-veto:plant:002 | replace | replace | 0.036 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:park:001 | replace | replace | 0.083 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:park:002 | replace | replace | 0.090 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:drink:001 | replace | replace | 0.021 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:drink:002 | replace | replace | 0.010 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:play:001 | replace | replace | 0.060 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:play:002 | replace | replace | 0.058 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:watch:001 | replace | replace | 0.075 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:watch:002 | replace | replace | 0.168 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:check:001 | replace | replace | 0.158 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:check:002 | replace | replace | 0.062 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:order:001 | replace | replace | 0.114 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:order:002 | replace | replace | 0.039 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:trip:002 | replace | replace | 0.042 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:ball:002 | replace | replace | 0.165 | n/a | no |
| raw_sentence_primary | en-es:sentence-veto:plant:002 | replace | replace | 0.085 | n/a | no |
| raw_window_primary | en-es:sentence-veto:park:001 | replace | replace | 0.091 | n/a | no |
| raw_window_primary | en-es:sentence-veto:park:002 | replace | replace | 0.139 | n/a | no |
| raw_window_primary | en-es:sentence-veto:drink:001 | replace | replace | 0.021 | n/a | no |
| raw_window_primary | en-es:sentence-veto:drink:002 | replace | replace | 0.010 | n/a | no |
| raw_window_primary | en-es:sentence-veto:play:001 | replace | replace | 0.060 | n/a | no |
| raw_window_primary | en-es:sentence-veto:play:002 | replace | replace | 0.058 | n/a | no |
| raw_window_primary | en-es:sentence-veto:watch:001 | replace | replace | 0.075 | n/a | no |
| raw_window_primary | en-es:sentence-veto:watch:002 | replace | replace | 0.162 | n/a | no |
| raw_window_primary | en-es:sentence-veto:check:001 | replace | replace | 0.158 | n/a | no |
| raw_window_primary | en-es:sentence-veto:check:002 | replace | replace | 0.069 | n/a | no |
| raw_window_primary | en-es:sentence-veto:order:001 | replace | replace | 0.114 | n/a | no |
| raw_window_primary | en-es:sentence-veto:order:002 | replace | replace | 0.039 | n/a | no |
| raw_window_primary | en-es:sentence-veto:trip:002 | replace | replace | 0.042 | n/a | no |
| raw_window_primary | en-es:sentence-veto:ball:002 | replace | replace | 0.165 | n/a | no |
| raw_window_primary | en-es:sentence-veto:plant:002 | replace | replace | 0.097 | n/a | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:park:001 | replace | replace | -0.042 | 0.068 | yes |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:park:002 | replace | replace | 0.008 | 0.055 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:drink:001 | replace | replace | -0.012 | 0.058 | yes |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:drink:002 | replace | replace | -0.021 | 0.050 | yes |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:play:001 | replace | replace | -0.017 | 0.049 | yes |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | -0.022 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:watch:001 | replace | replace | 0.001 | -0.074 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:watch:002 | replace | replace | 0.095 | -0.051 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:check:001 | replace | replace | 0.106 | 0.077 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | -0.007 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:order:001 | replace | replace | 0.065 | -0.003 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:order:002 | replace | abstain | -0.011 | -0.049 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:trip:002 | replace | abstain | -0.013 | -0.034 | no |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:ball:002 | replace | replace | -0.012 | 0.021 | yes |
| overlay:p=-0.05:b=0.02 | en-es:sentence-veto:plant:002 | replace | replace | -0.020 | 0.036 | yes |

## Configuration Notes

### Current default runtime row

- Description: Masked sentence plus all-evidence primary, phrase guard, and the current near-tie sense-label rescue.
- Harmful replace cases: `en-es:sentence-veto:play:005`
- False abstain cases: `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:park:001`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:check:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

### Masked sentence plus sense-label primary

- Description: Swaps the primary evidence surface to sense labels while keeping the same masked context and hard thresholds.
- Harmful replace cases: `en-es:sentence-veto:ball:005`, `en-es:sentence-veto:park:003`, `en-es:sentence-veto:drink:005`, `en-es:sentence-veto:play:005`
- False abstain cases: `en-es:sentence-veto:match:001`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:watch:001`, `en-es:sentence-veto:watch:002`, `en-es:sentence-veto:check:002`, `en-es:sentence-veto:order:001`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`

### Raw sentence plus all-evidence primary

- Description: Broadens the primary context view to the full raw sentence while leaving the evidence surface unchanged.
- Harmful replace cases: `en-es:sentence-veto:ball:004`, `en-es:sentence-veto:ball:005`, `en-es:sentence-veto:park:003`, `en-es:sentence-veto:play:005`, `en-es:sentence-veto:order:005`
- False abstain cases: none

### Raw window plus all-evidence primary

- Description: Uses a local raw-context window as the primary view to test whether the park-like misses are recoverable via broader lexical context.
- Harmful replace cases: `en-es:sentence-veto:ball:004`, `en-es:sentence-veto:ball:005`, `en-es:sentence-veto:park:003`, `en-es:sentence-veto:play:005`, `en-es:sentence-veto:order:005`
- False abstain cases: `en-es:sentence-veto:table:001`

### Best bounded rescue overlay

- Description: Keeps the current masked all-evidence primary, then widens the rescue trigger floor while requiring an active winner from the sense-label backup.
- Harmful replace cases: `en-es:sentence-veto:play:005`
- False abstain cases: `en-es:sentence-veto:play:002`, `en-es:sentence-veto:check:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002`
