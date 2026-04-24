# en-es Semantic LLM Prototype Admission Probe

- Status: `ok`
- Generated: `2026-04-24T20:16:54Z`
- Scope: `all_dataset_families`
- Queue: `en_es_sentence_veto_v10_all_family_prototype_probe`
- Runtime dataset: `en_es_sentence_veto_v10`
- Scorer: `sentence_transformer_cosine`
- Decision contract: `binary_replace_or_abstain`
- Runtime publishable: `False`

## Prototype Results

| Config | Phrase Guard | Cases | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Prototype reviewed examples, family phrase guard` | `family_all` | 95 | 5 | 0 | 100.0% | 94.7% | 7 |
| `Prototype reviewed examples, active phrase guard` | `active_only` | 95 | 2 | 0 | 100.0% | 97.9% | 21 |
| `Prototype reviewed examples, phrase-control prototype guard` | `active_only` | 95 | 0 | 0 | 100.0% | 100.0% | 21 |

## Residual Case Matrix

| Case | Gold | Family Guard | Active Guard | Phrase Prototype Guard |
| --- | --- | --- | --- | --- |
| `en-es:sentence-veto:ball:005` | `abstain` | `replace` m=0.0572 a=0.6015 s=0.5442 p=0.0 | `replace` m=0.0572 a=0.6015 s=0.5442 p=0.0 | `abstain` m=0.0572 a=0.6015 s=0.5442 p=1.0 |
| `en-es:sentence-veto:drink:005` | `abstain` | `replace` m=0.1034 a=0.6474 s=0.5441 p=0.0 | `abstain` m=0.1034 a=0.6474 s=0.5441 p=0.0 | `abstain` m=0.1034 a=0.6474 s=0.5441 p=1.0 |
| `en-es:sentence-veto:match:005` | `abstain` | `replace` m=0.0055 a=0.5496 s=0.5441 p=0.0 | `replace` m=0.0055 a=0.5496 s=0.5441 p=0.0 | `abstain` m=0.0055 a=0.5496 s=0.5441 p=1.0 |
| `en-es:sentence-veto:order:005` | `abstain` | `replace` m=0.0115 a=0.6208 s=0.6094 p=0.0 | `abstain` m=0.0115 a=0.6208 s=0.6094 p=0.0 | `abstain` m=0.0115 a=0.6208 s=0.6094 p=1.0 |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.0056 a=0.5728 s=0.5672 p=0.0 | `abstain` m=0.0056 a=0.5728 s=0.5672 p=0.0 | `abstain` m=0.0056 a=0.5728 s=0.5672 p=1.0 |

## Recommendation

- Keep the user-facing UX binary, but move the internal experiment from a single evidence string toward prototype admission: context competes against active, shadow, and phrase-control example frames, then resolves to replace or abstain. The phrase-control prototype guard clears this evaluation slice (`100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains) on `all_dataset_families`. The reviewed examples are internal oracle data, not runtime-publishable evidence; use this as the acceptance target for external or generated example-frame sources.
