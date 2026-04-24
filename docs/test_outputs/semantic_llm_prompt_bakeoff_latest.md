# en-es Semantic LLM Prompt Bakeoff

- Status: `ok`
- Generated: `2026-04-24T02:44:39Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v3`
- Stage: `proxy`
- Execution mode: `live`
- Batch id: `en-es:proxy:prompt-proxy-v3-20260424a`
- Source id: `semantic_prompt_bakeoff_en_es_v10:proxy`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`

## Summary

- Selected requests: `12`
- Accepted items: `12`
- API errors: `0`
- Invalid outputs: `0`
- Normalized rows: `12`
- Input tokens: `5370`
- Output tokens: `414`

## Artifacts

- Journal: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v3-20260424a_journal.jsonl`
- Raw responses: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v3-20260424a_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v3-20260424a_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-prompt-proxy-v3-20260424a_normalized_evidence.json`

## Request Outcomes

| Request | Slot | Family | Status | Output |
| --- | --- | --- | --- | --- |
| `en-es:proxy:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | `en-es:sentence-veto:plant:planta` | `accepted` | Rooted organism with leaves, stems, or flowers; grows in soil or water. |
| `en-es:proxy:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | `en-es:sentence-veto:drink:bebida` | `accepted` | Noun for a served liquid, often cold or alcoholic, not the act of swallowing. |
| `en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica` | `cue_contrastive_overlap_v1` | `en-es:sentence-veto:plant:planta` | `accepted` | soil, water, leaves, roots, sunlight |
| `en-es:proxy:cue-contrastive-overlap-v1:drink:beber` | `cue_contrastive_overlap_v1` | `en-es:sentence-veto:drink:bebida` | `accepted` | cold beverage, soft drink, glass, bottle |
| `en-es:proxy:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:check:cheque` | `accepted` | article or amount before check, with bank payment context and no action verb |
| `en-es:proxy:cue-cross-pos-frame-v1:order:ordenar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:order:pedido` | `accepted` | preceded by a determiner or possessive, often with of or for |
| `en-es:proxy:cue-cross-pos-frame-v1:trip:tropezar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:trip:viaje` | `accepted` | Determiner or possessive before trip, often with adjectives like short or long. |
| `en-es:proxy:cue-cross-pos-frame-v1:report:informar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:report:informe` | `accepted` | preceded by a determiner and followed by findings, results, or document details |
| `en-es:proxy:cue-cross-pos-overlap-v1:check:revisar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:check:cheque` | `accepted` | write a check for the rent payment |
| `en-es:proxy:cue-cross-pos-overlap-v1:order:ordenar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:order:pedido` | `accepted` | your online order for delivery |
| `en-es:proxy:cue-cross-pos-overlap-v1:trip:tropezar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:trip:viaje` | `accepted` | a short trip to the city |
| `en-es:proxy:cue-cross-pos-overlap-v1:report:informar` | `cue_cross_pos_overlap_v1` | `en-es:sentence-veto:report:informe` | `accepted` | annual report with findings, results, and recommendations |
