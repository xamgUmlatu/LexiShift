# en-es Semantic LLM Prompt Cost Estimate

- Status: `ok`
- Generated: `2026-04-24T02:41:17Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v3`
- Stage: `proxy`
- Selected model: `gpt-5.4-mini`
- Input-token heuristic: `ceil(characters / 4.0)`

## Summary

- Selected requests: `12`
- Estimated input tokens: `5969`
- Estimated output tokens (expected): `1080`
- Output token ceiling: `3600`
- Pricing rates: `not supplied`

## Request Estimates

| Request | Slot | Input Tokens | Expected Output | Output Ceiling |
| --- | --- | ---: | ---: | ---: |
| `en-es:proxy:cue-contrastive-general-v1:plant:fabrica` | `cue_contrastive_general_v1` | 416 | 90 | 300 |
| `en-es:proxy:cue-contrastive-general-v1:drink:beber` | `cue_contrastive_general_v1` | 414 | 90 | 300 |
| `en-es:proxy:cue-contrastive-overlap-v1:plant:fabrica` | `cue_contrastive_overlap_v1` | 491 | 90 | 300 |
| `en-es:proxy:cue-contrastive-overlap-v1:drink:beber` | `cue_contrastive_overlap_v1` | 488 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-frame-v1:check:revisar` | `cue_cross_pos_frame_v1` | 504 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-frame-v1:order:ordenar` | `cue_cross_pos_frame_v1` | 499 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-frame-v1:trip:tropezar` | `cue_cross_pos_frame_v1` | 479 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-frame-v1:report:informar` | `cue_cross_pos_frame_v1` | 502 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-overlap-v1:check:revisar` | `cue_cross_pos_overlap_v1` | 552 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-overlap-v1:order:ordenar` | `cue_cross_pos_overlap_v1` | 547 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-overlap-v1:trip:tropezar` | `cue_cross_pos_overlap_v1` | 527 | 90 | 300 |
| `en-es:proxy:cue-cross-pos-overlap-v1:report:informar` | `cue_cross_pos_overlap_v1` | 550 | 90 | 300 |
