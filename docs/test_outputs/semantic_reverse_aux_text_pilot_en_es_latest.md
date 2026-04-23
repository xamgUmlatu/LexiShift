# en-es Reverse Aux Text Pilot

- Status: `ok`
- Generated: `2026-04-23T20:37:51Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Selected candidate: `Reverse aux text plus all evidence`

## Coverage

- Target families: `6`
- Target families with active reverse aux text: `6`
- Target families with any shadow reverse aux text: `4`

| Family | Role | Active Aux | Shadow Aux Count | Active Aux Sample |
| --- | --- | ---: | ---: | --- |
| `plant -> planta` | `target` | 1 | 0 | `organism capable of photosynthesis` |
| `drink -> bebida` | `target` | 1 | 1 | `served beverage` |
| `play -> obra` | `negative_control` | 0 | 1 | `n/a` |
| `watch -> reloj` | `negative_control` | 1 | 1 | `portable or wearable timepiece` |
| `check -> cheque` | `target` | 1 | 0 | `mark used as an indicator` |
| `order -> pedido` | `target` | 1 | 1 | `request for some product or service` |
| `trip -> viaje` | `target` | 1 | 1 | `journey` |
| `report -> informe` | `target` | 1 | 1 | `information describing events` |

## Configuration Summary

| Config | Evidence View | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced False Abstains |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `Current default runtime row` | `all_evidence_text` | 1 | 8 | 50.0% | 77.5% | none | none |
| `Reverse aux text only` | `reverse_aux_text` | 4 | 8 | 50.0% | 70.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:report:002` | `en-es:sentence-veto:check:001`, `en-es:sentence-veto:order:001`, `en-es:sentence-veto:trip:001`, `en-es:sentence-veto:watch:001` |
| `Reverse aux text plus sense label` | `reverse_aux_plus_sense_label` | 3 | 7 | 56.2% | 75.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:report:002` | `en-es:sentence-veto:watch:001`, `en-es:sentence-veto:watch:002` |
| `Reverse aux text plus all evidence` | `reverse_aux_plus_all_evidence` | 1 | 6 | 62.5% | 82.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | `en-es:sentence-veto:watch:001` |

## Focus Case Outcomes

| Config | Case | Gold | Predicted | Margin | Phrase | Rescue |
| --- | --- | --- | --- | ---: | --- | --- |
| current_default | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| current_default | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| current_default | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | no | no |
| current_default | en-es:sentence-veto:plant:002 | replace | abstain | -0.020 | no | no |
| current_default | en-es:sentence-veto:report:001 | replace | abstain | -0.048 | no | no |
| current_default | en-es:sentence-veto:trip:002 | replace | abstain | -0.013 | no | no |
| current_default | en-es:sentence-veto:order:002 | replace | abstain | -0.011 | no | no |
| current_default | en-es:sentence-veto:drink:002 | replace | abstain | -0.021 | no | no |
| current_default | en-es:sentence-veto:report:002 | replace | abstain | -0.071 | no | no |
| current_default | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:play:005 | abstain | replace | 0.061 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:play:002 | replace | replace | 0.005 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:check:002 | replace | abstain | -0.043 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:plant:002 | replace | replace | 0.015 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:report:001 | replace | abstain | -0.012 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:trip:002 | replace | abstain | -0.063 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:order:002 | replace | abstain | -0.032 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:drink:002 | replace | replace | 0.140 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:report:002 | replace | replace | 0.070 | no | no |
| reverse_aux_text_primary | en-es:sentence-veto:watch:005 | abstain | abstain | -0.100 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:play:005 | abstain | replace | 0.082 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:play:002 | replace | abstain | -0.008 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:check:002 | replace | abstain | -0.005 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:plant:002 | replace | replace | 0.039 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:report:001 | replace | abstain | -0.002 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:trip:002 | replace | abstain | -0.029 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:order:002 | replace | abstain | -0.015 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:drink:002 | replace | replace | 0.089 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:report:002 | replace | replace | 0.004 | no | no |
| reverse_aux_plus_sense_label | en-es:sentence-veto:watch:005 | abstain | abstain | -0.104 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:play:005 | abstain | replace | 0.083 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:play:002 | replace | abstain | -0.001 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:check:002 | replace | abstain | -0.044 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:plant:002 | replace | replace | 0.005 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:report:001 | replace | abstain | -0.033 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:trip:002 | replace | abstain | -0.021 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:order:002 | replace | replace | 0.004 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:drink:002 | replace | replace | 0.016 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:report:002 | replace | abstain | -0.045 | no | no |
| reverse_aux_plus_all_evidence | en-es:sentence-veto:watch:005 | abstain | abstain | -0.079 | no | no |

## Recommendation

- `Reverse aux text plus all evidence` is a credible last non-LLM control for the frozen prompt queue: it improves the queue-slice point read without widening the current harmful-replace count.
