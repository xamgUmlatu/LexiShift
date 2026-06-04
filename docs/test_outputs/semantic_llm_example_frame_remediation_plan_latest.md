# en-es LLM Example-Frame Remediation Plan

- Status: `ready`
- Generated: `2026-04-24T22:06:18Z`
- Dataset: `en_es_sentence_veto_v10`
- Required families: `semantic_prompt_bakeoff_en_es_v10`
- Prototype config: `prototype_reviewed_examples_phrase_containment_guard`
- Prompt version: `example-frame-residual-remediation-v1`
- Selected model: `gpt-5.4-mini`
- Decision contract: `binary_replace_or_abstain`
- Review leakage policy: `do_not_include_sentence_veto_case_sentences_in_prompts`

## Summary

- Requests: `8`
- Families: `7`
- False-abstain cases: `11`
- Harmful-replace cases: `2`
- Estimated input tokens: `3259`
- Expected output tokens: `400`
- Max output tokens: `1440`
- Requests by target: `{"remediation_active_example": 7, "remediation_shadow_example": 1}`

## Request Rows

| Request | Target | Family | Candidate | Failure Mode | Cases | Input Tokens |
| --- | --- | --- | --- | --- | ---: | ---: |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-check-cheque` | `remediation_active_example` | `en-es:sentence-veto:check:cheque` | `cheque` | `false_abstain_active_example_gap` | 2 | 412 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-order-pedido` | `remediation_active_example` | `en-es:sentence-veto:order:pedido` | `pedido` | `false_abstain_active_example_gap` | 2 | 408 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-plant-planta` | `remediation_active_example` | `en-es:sentence-veto:plant:planta` | `planta` | `false_abstain_active_example_gap` | 2 | 403 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-play-obra` | `remediation_active_example` | `en-es:sentence-veto:play:obra` | `obra` | `false_abstain_active_example_gap` | 1 | 397 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-report-informe` | `remediation_active_example` | `en-es:sentence-veto:report:informe` | `informe` | `false_abstain_active_example_gap` | 1 | 405 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-trip-viaje` | `remediation_active_example` | `en-es:sentence-veto:trip:viaje` | `viaje` | `false_abstain_active_example_gap` | 2 | 392 |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-watch-reloj` | `remediation_active_example` | `en-es:sentence-veto:watch:reloj` | `reloj` | `false_abstain_active_example_gap` | 1 | 408 |
| `en-es:example-frame-remediation:shadow:en-es-sentence-veto-report-informe:en-es-sentence-veto-report-informar-shadow` | `remediation_shadow_example` | `en-es:sentence-veto:report:informe` | `informar` | `harmful_replace_shadow_example_gap` | 2 | 434 |

## Recommendation

- Execute this plan only after reviewing the request rows: it targets active examples for false abstains and shadow examples for harmful replaces while leaving phrase-control evidence on the containment-only path.
