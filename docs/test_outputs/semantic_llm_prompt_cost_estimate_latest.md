# en-es Semantic LLM Prompt Cost Estimate

- Status: `ok`
- Generated: `2026-04-24T18:13:21Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Prompt spec: `semantic_prompt_spec_en_es_v10`
- Prompt version: `semantic_prompt_bakeoff_v3`
- Stage: `target`
- Selected model: `gpt-5.4`
- Input-token heuristic: `ceil(characters / 4.0)`

## Summary

- Selected requests: `6`
- Estimated input tokens: `3155`
- Estimated output tokens (expected): `540`
- Output token ceiling: `1800`
- Input rate per 1M: `2.5`
- Output rate per 1M: `15.0`
- Estimated cost (expected): `0.015987`
- Estimated cost (ceiling): `0.034888`

## Request Estimates

| Request | Slot | Input Tokens | Expected Output | Output Ceiling |
| --- | --- | ---: | ---: | ---: |
| `en-es:target:cue-contrastive-overlap-v1:plant:fabrica` | `cue_contrastive_overlap_v1` | 491 | 90 | 300 |
| `en-es:target:cue-contrastive-overlap-v1:drink:beber` | `cue_contrastive_overlap_v1` | 488 | 90 | 300 |
| `en-es:target:cue-cross-pos-overlap-v1:check:revisar` | `cue_cross_pos_overlap_v1` | 552 | 90 | 300 |
| `en-es:target:cue-cross-pos-overlap-v1:order:ordenar` | `cue_cross_pos_overlap_v1` | 547 | 90 | 300 |
| `en-es:target:cue-cross-pos-overlap-v1:trip:tropezar` | `cue_cross_pos_overlap_v1` | 527 | 90 | 300 |
| `en-es:target:cue-cross-pos-overlap-v1:report:informar` | `cue_cross_pos_overlap_v1` | 550 | 90 | 300 |
