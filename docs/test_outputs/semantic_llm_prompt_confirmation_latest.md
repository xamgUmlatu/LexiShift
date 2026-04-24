# en-es Semantic LLM Prompt Bakeoff

- Status: `ok`
- Generated: `2026-04-24T01:38:58Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v2`
- Stage: `target`
- Execution mode: `live`
- Batch id: `en-es:target:prompt-target-v2-20260424a`
- Source id: `semantic_prompt_bakeoff_en_es_v10:target`
- Selected model: `gpt-5.4`
- Temperature: `0.2`

## Summary

- Selected requests: `6`
- Accepted items: `6`
- API errors: `0`
- Invalid outputs: `0`
- Normalized rows: `6`
- Input tokens: `2545`
- Output tokens: `231`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-target-prompt-target-v2-20260424a_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-target-prompt-target-v2-20260424a_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-target-prompt-target-v2-20260424a_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-target-prompt-target-v2-20260424a_normalized_evidence.json`

## Request Outcomes

| Request | Slot | Family | Status | Output |
| --- | --- | --- | --- | --- |
| `en-es:target:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | `en-es:sentence-veto:plant:planta` | `accepted` | Refers to something rooted that grows leaves, stems, or flowers. |
| `en-es:target:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | `en-es:sentence-veto:drink:bebida` | `accepted` | Refers to the liquid itself, often countable or ordered, not the act. |
| `en-es:target:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:check:cheque` | `accepted` | Preceded by a determiner or amount, often written, signed, deposited, or cashed. |
| `en-es:target:cue-cross-pos-frame-v1:order:ordenar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:order:pedido` | `accepted` | Preceded by a determiner or quantity and followed by for goods or delivery. |
| `en-es:target:cue-cross-pos-frame-v1:trip:tropezar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:trip:viaje` | `accepted` | A determiner or adjective before trip signals a planned journey noun. |
| `en-es:target:cue-cross-pos-frame-v1:report:informar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:report:informe` | `accepted` | Preceded by a determiner or adjective, especially followed by on/about findings. |
