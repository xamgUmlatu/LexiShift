# en-es LLM Example-Frame Generation Plan

- Status: `ready`
- Generated: `2026-04-24T20:55:00Z`
- Dataset: `en_es_sentence_veto_v10`
- Required families: `semantic_prompt_bakeoff_en_es_v10`
- Base batch: `en-es:reverse-aux-example-frames:reverse-aux-example-frames-v10-20260425a`
- Prompt version: `example-frame-missing-rows-v1`
- Selected model: `gpt-5.4-mini`
- Decision contract: `binary_replace_or_abstain`
- Review leakage policy: `do_not_include_sentence_veto_case_sentences_in_prompts`

## Summary

- Requests: `11`
- Families: `8`
- Estimated input tokens: `3802`
- Expected output tokens: `550`
- Max output tokens: `1980`
- Requests by target: `{"active_example": 1, "phrase_control_example": 8, "shadow_example": 2}`

## Request Rows

| Request | Target | Family | Candidate | Input Tokens |
| --- | --- | --- | --- | ---: |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 348 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-plant-planta` | `phrase_control_example` | `en-es:sentence-veto:plant:planta` | `phrase_control` | 351 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-drink-bebida` | `phrase_control_example` | `en-es:sentence-veto:drink:bebida` | `phrase_control` | 346 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 353 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-check-cheque` | `phrase_control_example` | `en-es:sentence-veto:check:cheque` | `phrase_control` | 351 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-order-pedido` | `phrase_control_example` | `en-es:sentence-veto:order:pedido` | `phrase_control` | 346 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-trip-viaje` | `phrase_control_example` | `en-es:sentence-veto:trip:viaje` | `phrase_control` | 336 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-report-informe` | `phrase_control_example` | `en-es:sentence-veto:report:informe` | `phrase_control` | 350 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 322 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-play-obra` | `phrase_control_example` | `en-es:sentence-veto:play:obra` | `phrase_control` | 345 |
| `en-es:example-frame-missing:phrase-control:en-es-sentence-veto-watch-reloj` | `phrase_control_example` | `en-es:sentence-veto:watch:reloj` | `phrase_control` | 354 |

## Recommendation

- Execute only these missing-row requests, then merge accepted rows with the base reverse-aux batch and rerun the required-family contract plus prototype-admission probe.
