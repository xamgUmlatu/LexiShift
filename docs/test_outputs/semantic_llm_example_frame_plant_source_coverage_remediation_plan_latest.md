# en-es LLM Example-Frame Remediation Plan

- Status: `ready`
- Generated: `2026-04-25T00:06:08Z`
- Dataset: `en_es_sentence_veto_v10`
- Required families: `en_es_sentence_veto_v10`
- Prototype config: `prototype_reviewed_examples_surface_pos_rescue_guard`
- Prompt version: `example-frame-residual-remediation-v1`
- Selected model: `gpt-5.4-mini`
- Decision contract: `binary_replace_or_abstain`
- Review leakage policy: `do_not_include_sentence_veto_case_sentences_in_prompts`

## Summary

- Requests: `1`
- Families: `1`
- False-abstain cases: `2`
- Harmful-replace cases: `0`
- Estimated input tokens: `407`
- Expected output tokens: `50`
- Max output tokens: `180`
- Requests by target: `{"remediation_active_example": 1}`

## Request Rows

| Request | Target | Family | Candidate | Failure Mode | Cases | Input Tokens |
| --- | --- | --- | --- | --- | ---: | ---: |
| `en-es:example-frame-remediation:active:en-es-sentence-veto-plant-planta` | `remediation_active_example` | `en-es:sentence-veto:plant:planta` | `planta` | `false_abstain_active_example_gap` | 2 | 407 |

## Recommendation

- Execute this plan only after reviewing the request rows: it targets active examples for false abstains and shadow examples for harmful replaces while leaving phrase-control evidence on the containment-only path.
