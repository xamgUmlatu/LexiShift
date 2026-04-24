# en-es Semantic LLM Prompt Bakeoff

- Status: `ok`
- Generated: `2026-04-24T01:35:52Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v2`
- Stage: `proxy`
- Execution mode: `live`
- Batch id: `en-es:proxy:prompt-proxy-v2-repeat-20260424a`
- Source id: `semantic_prompt_bakeoff_en_es_v10:proxy`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`

## Summary

- Selected requests: `6`
- Accepted items: `6`
- API errors: `0`
- Invalid outputs: `0`
- Normalized rows: `6`
- Input tokens: `2545`
- Output tokens: `226`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v2-repeat-20260424a_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v2-repeat-20260424a_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v2-repeat-20260424a_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v2-repeat-20260424a_normalized_evidence.json`

## Request Outcomes

| Request | Slot | Family | Status | Output |
| --- | --- | --- | --- | --- |
| `en-es:proxy:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | `en-es:sentence-veto:plant:planta` | `accepted` | Rooted organism with leaves, stems, or flowers; not a building or workplace. |
| `en-es:proxy:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | `en-es:sentence-veto:drink:bebida` | `accepted` | Noun for a served liquid, often on a menu or in a glass. |
| `en-es:proxy:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:check:cheque` | `accepted` | determiner or possessive before check, often followed by amount or bank context |
| `en-es:proxy:cue-cross-pos-frame-v1:order:ordenar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:order:pedido` | `accepted` | appears after a determiner or possessive, often with of or for |
| `en-es:proxy:cue-cross-pos-frame-v1:trip:tropezar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:trip:viaje` | `accepted` | determiner or possessive before trip, with after or on following it |
| `en-es:proxy:cue-cross-pos-frame-v1:report:informar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:report:informe` | `accepted` | follows a determiner or adjective and names a document with findings |
