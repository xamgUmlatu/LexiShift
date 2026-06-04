# en-es Semantic LLM Prototype Admission Probe

- Status: `ok`
- Generated: `2026-04-24T20:16:54Z`
- Scope: `prompt_queue`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Scorer: `sentence_transformer_cosine`
- Decision contract: `binary_replace_or_abstain`
- Runtime publishable: `False`

## Prototype Results

| Config | Phrase Guard | Cases | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Prototype reviewed examples, family phrase guard` | `family_all` | 40 | 3 | 0 | 100.0% | 92.5% | 1 |
| `Prototype reviewed examples, active phrase guard` | `active_only` | 40 | 0 | 0 | 100.0% | 100.0% | 12 |
| `Prototype reviewed examples, phrase-control prototype guard` | `active_only` | 40 | 0 | 0 | 100.0% | 100.0% | 12 |

## Residual Case Matrix

| Case | Gold | Family Guard | Active Guard | Phrase Prototype Guard |
| --- | --- | --- | --- | --- |
| `en-es:sentence-veto:drink:005` | `abstain` | `replace` m=0.1034 a=0.6474 s=0.5441 p=0.0 | `abstain` m=0.1034 a=0.6474 s=0.5441 p=0.0 | `abstain` m=0.1034 a=0.6474 s=0.5441 p=1.0 |
| `en-es:sentence-veto:order:005` | `abstain` | `replace` m=0.0115 a=0.6208 s=0.6094 p=0.0 | `abstain` m=0.0115 a=0.6208 s=0.6094 p=0.0 | `abstain` m=0.0115 a=0.6208 s=0.6094 p=1.0 |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.0056 a=0.5728 s=0.5672 p=0.0 | `abstain` m=0.0056 a=0.5728 s=0.5672 p=0.0 | `abstain` m=0.0056 a=0.5728 s=0.5672 p=1.0 |

## Recommendation

- Keep the user-facing UX binary, but move the internal experiment from a single evidence string toward prototype admission: context competes against active, shadow, and phrase-control example frames, then resolves to replace or abstain. The phrase-control prototype guard clears this evaluation slice (`100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains) on `prompt_queue`. The reviewed examples are internal oracle data, not runtime-publishable evidence; use this as the acceptance target for external or generated example-frame sources.
