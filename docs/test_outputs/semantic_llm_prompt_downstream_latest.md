# en-es Semantic LLM Prompt Downstream Bakeoff

- Status: `ok`
- Generated: `2026-04-24T02:18:23Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Scorer: `sentence_transformer_cosine`
- Min active / margin: `0.0` / `0.0`

## LLM Batch

- Batch id: `en-es:target:prompt-target-v2-20260424a`
- Source id: `semantic_prompt_bakeoff_en_es_v10:target`
- Prompt version: `semantic_prompt_bakeoff_v2`
- Model: `gpt-5.4`
- Batch review state: `unreviewed`
- Runtime publishable rows: `0` / `6`

## Coverage

- Target families: `6`
- Target families with LLM cues: `6`
- Negative controls with LLM cues: `0`

| Family | Role | LLM Cue Rows | Prompt Slots | Sample Cue |
| --- | --- | ---: | --- | --- |
| `plant -> planta` | `target` | 1 | `cue_contrastive_general_v1` | Refers to something rooted that grows leaves, stems, or flowers. |
| `drink -> bebida` | `target` | 1 | `cue_contrastive_general_v1` | Refers to the liquid itself, often countable or ordered, not the act. |
| `play -> obra` | `negative_control` | 0 | n/a | n/a |
| `watch -> reloj` | `negative_control` | 0 | n/a | n/a |
| `check -> cheque` | `target` | 1 | `cue_cross_pos_frame_v1` | Preceded by a determiner or amount, often written, signed, deposited, or cashed. |
| `order -> pedido` | `target` | 1 | `cue_cross_pos_frame_v1` | Preceded by a determiner or quantity and followed by for goods or delivery. |
| `trip -> viaje` | `target` | 1 | `cue_cross_pos_frame_v1` | A determiner or adjective before trip signals a planned journey noun. |
| `report -> informe` | `target` | 1 | `cue_cross_pos_frame_v1` | Preceded by a determiner or adjective, especially followed by on/about findings. |

## Configuration Summary

| Config | Scope | Evidence View | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced False Abstains |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `Hard current default runtime row` | `family_all` | `all_evidence_text` | 1 | 8 | 50.0% | 77.5% | none | none |
| `Hard reverse aux plus all evidence` | `family_all` | `reverse_aux_plus_all_evidence` | 1 | 6 | 62.5% | 82.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | `en-es:sentence-veto:watch:001` |
| `Hard LLM cue text only` | `family_all` | `llm_cue_text` | 5 | 8 | 50.0% | 67.5% | `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002` | `en-es:sentence-veto:drink:001`, `en-es:sentence-veto:trip:001` |
| `Hard LLM cue plus sense label` | `family_all` | `llm_cue_plus_sense_label` | 3 | 6 | 62.5% | 77.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | `en-es:sentence-veto:drink:001` |
| `Hard LLM cue plus gloss` | `family_all` | `llm_cue_plus_gloss` | 3 | 6 | 62.5% | 77.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:trip:002` | `en-es:sentence-veto:drink:001` |
| `Hard LLM cue plus all evidence` | `family_all` | `llm_cue_plus_all_evidence` | 1 | 8 | 50.0% | 77.5% | `en-es:sentence-veto:drink:002` | `en-es:sentence-veto:drink:001` |
| `Active-sense overlay reference` | `active_only` | `all_evidence_text` | 0 | 8 | 50.0% | 80.0% | none | none |
| `Active-sense overlay reverse aux plus all evidence` | `active_only` | `reverse_aux_plus_all_evidence` | 0 | 6 | 62.5% | 85.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | `en-es:sentence-veto:watch:001` |
| `Active-sense overlay LLM cue plus all evidence` | `active_only` | `llm_cue_plus_all_evidence` | 0 | 8 | 50.0% | 80.0% | `en-es:sentence-veto:drink:002` | `en-es:sentence-veto:drink:001` |

## Focus Case Outcomes

| Config | Case | Gold | Predicted | Margin | Phrase | Rescue |
| --- | --- | --- | --- | ---: | --- | --- |
| hard_current_default | en-es:sentence-veto:check:001 | replace | replace | 0.106 | no | no |
| hard_current_default | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | no | no |
| hard_current_default | en-es:sentence-veto:drink:001 | replace | replace | -0.012 | no | yes |
| hard_current_default | en-es:sentence-veto:drink:002 | replace | abstain | -0.021 | no | no |
| hard_current_default | en-es:sentence-veto:order:001 | replace | replace | 0.065 | no | no |
| hard_current_default | en-es:sentence-veto:order:002 | replace | abstain | -0.011 | no | no |
| hard_current_default | en-es:sentence-veto:plant:001 | replace | replace | 0.047 | no | no |
| hard_current_default | en-es:sentence-veto:plant:002 | replace | abstain | -0.020 | no | no |
| hard_current_default | en-es:sentence-veto:report:001 | replace | abstain | -0.048 | no | no |
| hard_current_default | en-es:sentence-veto:report:002 | replace | abstain | -0.071 | no | no |
| hard_current_default | en-es:sentence-veto:trip:001 | replace | replace | 0.048 | no | no |
| hard_current_default | en-es:sentence-veto:trip:002 | replace | abstain | -0.013 | no | no |
| hard_current_default | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| hard_current_default | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| hard_current_default | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:check:001 | replace | replace | 0.071 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:check:002 | replace | abstain | -0.044 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:drink:001 | replace | replace | 0.021 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:drink:002 | replace | replace | 0.016 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:order:001 | replace | replace | 0.063 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:order:002 | replace | replace | 0.004 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:plant:001 | replace | replace | 0.016 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:plant:002 | replace | replace | 0.005 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:report:001 | replace | abstain | -0.033 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:report:002 | replace | abstain | -0.045 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:trip:001 | replace | replace | 0.040 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:trip:002 | replace | abstain | -0.021 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:play:005 | abstain | replace | 0.083 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:watch:005 | abstain | abstain | -0.079 | no | no |
| hard_reverse_aux_plus_all_evidence | en-es:sentence-veto:play:002 | replace | abstain | -0.001 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:check:001 | replace | replace | 0.123 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:drink:001 | replace | abstain | -0.112 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:drink:002 | replace | abstain | -0.059 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:order:001 | replace | replace | 0.063 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:order:002 | replace | replace | 0.002 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:plant:001 | replace | replace | 0.032 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:plant:002 | replace | abstain | -0.037 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:report:001 | replace | abstain | -0.016 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:report:002 | replace | abstain | -0.051 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:trip:001 | replace | abstain | -0.023 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:trip:002 | replace | replace | 0.007 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| hard_llm_cue_text | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:check:001 | replace | replace | 0.088 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:check:002 | replace | abstain | -0.023 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:drink:001 | replace | abstain | -0.035 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:drink:002 | replace | replace | 0.013 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:order:001 | replace | replace | 0.063 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:order:002 | replace | replace | 0.001 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:plant:001 | replace | replace | 0.017 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:plant:002 | replace | replace | -0.020 | no | yes |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:report:001 | replace | abstain | -0.010 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:report:002 | replace | abstain | -0.044 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:trip:001 | replace | replace | 0.013 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:trip:002 | replace | abstain | -0.007 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| hard_llm_cue_plus_sense_label | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:check:001 | replace | replace | 0.139 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:check:002 | replace | abstain | -0.100 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:drink:001 | replace | abstain | -0.066 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:drink:002 | replace | replace | -0.017 | no | yes |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:order:001 | replace | replace | 0.072 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:order:002 | replace | replace | 0.021 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:plant:001 | replace | replace | 0.010 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:plant:002 | replace | abstain | -0.076 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:report:001 | replace | abstain | -0.034 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:report:002 | replace | abstain | -0.040 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:trip:001 | replace | replace | 0.013 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:trip:002 | replace | replace | 0.010 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| hard_llm_cue_plus_gloss | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:check:001 | replace | replace | 0.107 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:check:002 | replace | abstain | -0.059 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:drink:001 | replace | abstain | -0.045 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:drink:002 | replace | replace | -0.003 | no | yes |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:order:001 | replace | replace | 0.065 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:order:002 | replace | abstain | -0.003 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:plant:001 | replace | replace | 0.018 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:plant:002 | replace | abstain | -0.064 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:report:001 | replace | abstain | -0.033 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:report:002 | replace | abstain | -0.053 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:trip:001 | replace | replace | 0.013 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:trip:002 | replace | abstain | -0.002 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:play:005 | abstain | replace | 0.065 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | no | no |
| hard_llm_cue_plus_all_evidence | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| active_only_current_default | en-es:sentence-veto:check:001 | replace | replace | 0.106 | no | no |
| active_only_current_default | en-es:sentence-veto:check:002 | replace | abstain | -0.045 | no | no |
| active_only_current_default | en-es:sentence-veto:drink:001 | replace | replace | -0.012 | no | yes |
| active_only_current_default | en-es:sentence-veto:drink:002 | replace | abstain | -0.021 | no | no |
| active_only_current_default | en-es:sentence-veto:order:001 | replace | replace | 0.065 | no | no |
| active_only_current_default | en-es:sentence-veto:order:002 | replace | abstain | -0.011 | no | no |
| active_only_current_default | en-es:sentence-veto:plant:001 | replace | replace | 0.047 | no | no |
| active_only_current_default | en-es:sentence-veto:plant:002 | replace | abstain | -0.020 | no | no |
| active_only_current_default | en-es:sentence-veto:report:001 | replace | abstain | -0.048 | no | no |
| active_only_current_default | en-es:sentence-veto:report:002 | replace | abstain | -0.071 | no | no |
| active_only_current_default | en-es:sentence-veto:trip:001 | replace | replace | 0.048 | no | no |
| active_only_current_default | en-es:sentence-veto:trip:002 | replace | abstain | -0.013 | no | no |
| active_only_current_default | en-es:sentence-veto:play:005 | abstain | abstain | 0.065 | yes | no |
| active_only_current_default | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | yes | no |
| active_only_current_default | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:check:001 | replace | replace | 0.071 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:check:002 | replace | abstain | -0.044 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:drink:001 | replace | replace | 0.021 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:drink:002 | replace | replace | 0.016 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:order:001 | replace | replace | 0.063 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:order:002 | replace | replace | 0.004 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:plant:001 | replace | replace | 0.016 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:plant:002 | replace | replace | 0.005 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:report:001 | replace | abstain | -0.033 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:report:002 | replace | abstain | -0.045 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:trip:001 | replace | replace | 0.040 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:trip:002 | replace | abstain | -0.021 | no | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:play:005 | abstain | abstain | 0.083 | yes | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:watch:005 | abstain | abstain | -0.079 | yes | no |
| active_only_reverse_aux_plus_all_evidence | en-es:sentence-veto:play:002 | replace | abstain | -0.001 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:check:001 | replace | replace | 0.107 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:check:002 | replace | abstain | -0.059 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:drink:001 | replace | abstain | -0.045 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:drink:002 | replace | replace | -0.003 | no | yes |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:order:001 | replace | replace | 0.065 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:order:002 | replace | abstain | -0.003 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:plant:001 | replace | replace | 0.018 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:plant:002 | replace | abstain | -0.064 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:report:001 | replace | abstain | -0.033 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:report:002 | replace | abstain | -0.053 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:trip:001 | replace | replace | 0.013 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:trip:002 | replace | abstain | -0.002 | no | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:play:005 | abstain | abstain | 0.065 | yes | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:watch:005 | abstain | abstain | -0.067 | yes | no |
| active_only_llm_cue_plus_all_evidence | en-es:sentence-veto:play:002 | replace | abstain | -0.030 | no | no |

## Recommendation

- `Hard LLM cue plus all evidence` is not yet promotion-ready on the frozen queue slice. On the hard reference it stays at `1` harmful and `8` false abstains against the baseline `1` / `8`, fixing `en-es:sentence-veto:drink:002` but introducing `en-es:sentence-veto:drink:001`. The active-sense overlay lane is also flat at `8` false abstains versus the overlay baseline `8` and still behind the reverse-aux control (`6` hard false abstains, `6` overlay false abstains). `Hard LLM cue plus gloss` shows some signal, but it widens harmful replace to `3` while only reducing false abstains to `6`.