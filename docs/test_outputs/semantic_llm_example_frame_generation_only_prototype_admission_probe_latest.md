# en-es Semantic LLM Prototype Admission Probe

- Status: `ok`
- Generated: `2026-04-24T21:33:32Z`
- Scope: `prompt_queue`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Scorer: `sentence_transformer_cosine`
- Decision contract: `binary_replace_or_abstain`
- Runtime publishable: `False`

## Prototype Results

| Config | Phrase Guard | Cases | Harmful | False Abstain | Replace Recall | Decision Acc. | Phrase Hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Prototype llm_example_frame_missing_rows, family phrase guard` | `family_all` | 40 | 3 | 14 | 12.5% | 57.5% | 1 |
| `Prototype llm_example_frame_missing_rows, active phrase guard` | `active_only` | 40 | 1 | 14 | 12.5% | 62.5% | 12 |
| `Prototype llm_example_frame_missing_rows, phrase-control prototype guard` | `active_only` | 40 | 1 | 16 | 0.0% | 57.5% | 12 |

## Residual Case Matrix

| Case | Gold | Family Guard | Active Guard | Phrase Prototype Guard |
| --- | --- | --- | --- | --- |
| `en-es:sentence-veto:check:001` | `replace` | `abstain` m=-0.5791 a=0.0 s=0.5791 p=0.0 | `abstain` m=-0.5791 a=0.0 s=0.5791 p=0.0 | `abstain` m=-0.5791 a=0.0 s=0.5791 p=0.5893 |
| `en-es:sentence-veto:check:002` | `replace` | `abstain` m=-0.5715 a=0.0 s=0.5715 p=0.0 | `abstain` m=-0.5715 a=0.0 s=0.5715 p=0.0 | `abstain` m=-0.5715 a=0.0 s=0.5715 p=0.7021 |
| `en-es:sentence-veto:drink:001` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.6265 |
| `en-es:sentence-veto:drink:002` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.5672 |
| `en-es:sentence-veto:order:001` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.6877 |
| `en-es:sentence-veto:order:002` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.7301 |
| `en-es:sentence-veto:plant:001` | `replace` | `abstain` m=-0.5696 a=0.0 s=0.5696 p=0.0 | `abstain` m=-0.5696 a=0.0 s=0.5696 p=0.0 | `abstain` m=-0.5696 a=0.0 s=0.5696 p=0.5596 |
| `en-es:sentence-veto:plant:002` | `replace` | `abstain` m=-0.6574 a=0.0 s=0.6574 p=0.0 | `abstain` m=-0.6574 a=0.0 s=0.6574 p=0.0 | `abstain` m=-0.6574 a=0.0 s=0.6574 p=0.6915 |
| `en-es:sentence-veto:play:001` | `replace` | `replace` m=0.5151 a=0.5151 s=0.0 p=0.0 | `replace` m=0.5151 a=0.5151 s=0.0 p=0.0 | `abstain` m=0.5151 a=0.5151 s=0.0 p=0.519 |
| `en-es:sentence-veto:play:002` | `replace` | `replace` m=0.5262 a=0.5262 s=0.0 p=0.0 | `replace` m=0.5262 a=0.5262 s=0.0 p=0.0 | `abstain` m=0.5262 a=0.5262 s=0.0 p=0.5713 |
| `en-es:sentence-veto:play:003` | `abstain` | `replace` m=0.634 a=0.634 s=0.0 p=0.0 | `replace` m=0.634 a=0.634 s=0.0 p=0.0 | `replace` m=0.634 a=0.634 s=0.0 p=0.5901 |
| `en-es:sentence-veto:play:004` | `abstain` | `replace` m=0.5132 a=0.5132 s=0.0 p=0.0 | `abstain` m=0.5132 a=0.5132 s=0.0 p=0.0 | `abstain` m=0.5132 a=0.5132 s=0.0 p=0.6101 |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.5657 a=0.5657 s=0.0 p=0.0 | `abstain` m=0.5657 a=0.5657 s=0.0 p=0.0 | `abstain` m=0.5657 a=0.5657 s=0.0 p=0.5522 |
| `en-es:sentence-veto:report:001` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.6423 |
| `en-es:sentence-veto:report:002` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.5914 |
| `en-es:sentence-veto:trip:001` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.5751 |
| `en-es:sentence-veto:trip:002` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.6765 |
| `en-es:sentence-veto:watch:001` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.5679 |
| `en-es:sentence-veto:watch:002` | `replace` | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.0 | `abstain` m=0.0 a=0.0 s=0.0 p=0.55 |

## Recommendation

- Keep the user-facing UX binary, but move the internal experiment from a single evidence string toward prototype admission: context competes against active, shadow, and phrase-control example frames, then resolves to replace or abstain. The phrase-control prototype guard still leaves residual cases on this evaluation slice (`57.5%` accuracy / `0.0%` recall / `1` harmful / `16` false abstains) on `prompt_queue`. The `llm_example_frame_missing_rows` batch `en-es:example-frame-missing-rows:example-frame-missing-rows-v1-20260425a` is source evidence, but it should clear the required-family contract gate before any promotion or runtime publication claim.
