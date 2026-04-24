# en-es Semantic LLM Prompt Bakeoff

- Status: `partial`
- Generated: `2026-04-23T23:51:40Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v2`
- Stage: `proxy`
- Execution mode: `replay`
- Batch id: `en-es:proxy:20260423T235140Z:replay`
- Source id: `semantic_prompt_bakeoff_en_es_v10:proxy:replay`
- Selected model: `gpt-5.4-mini`
- Temperature: `0.2`
- Replay source: `docs/test_inputs/semantic_routing/semantic_prompt_replay_fixture_en_es_v10.json`

## Summary

- Selected requests: `3`
- Accepted items: `1`
- API errors: `1`
- Invalid outputs: `1`
- Normalized rows: `1`
- Input tokens: `244`
- Output tokens: `45`

## Artifacts

- Journal: ``
- Raw responses: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-20260423t235140z-replay_raw_responses.json`
- Intake batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-20260423t235140z-replay_intake_batch.json`
- Normalized batch: `docs/test_outputs/experiments/semantic_llm_prompt_batches/en-es-proxy-20260423t235140z-replay_normalized_evidence.json`

## Request Outcomes

| Request | Slot | Family | Status | Output |
| --- | --- | --- | --- | --- |
| `en-es:proxy:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | `en-es:sentence-veto:plant:planta` | `accepted` | living organism with leaves or roots, not an industrial facility |
| `en-es:proxy:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | `en-es:sentence-veto:drink:bebida` | `api_error` | RuntimeError: Replay plumbing rehearsal forced API failure |
| `en-es:proxy:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | `en-es:sentence-veto:check:cheque` | `invalid_output` | ValueError: unexpected item keys: ['extra_key'] |
