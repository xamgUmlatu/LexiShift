# en-es Semantic LLM Prototype Admission Probe

- Status: `ok`
- Generated: `2026-04-24T22:03:03Z`
- Scope: `prompt_queue`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Scorer: `sentence_transformer_cosine`
- Decision contract: `binary_replace_or_abstain`
- Runtime publishable: `False`

## Prototype Results

| Config | Phrase Guard | Evidence Mode | Cases | Harmful | False Abstain | Replace Recall | Decision Acc. | Runtime Phrase Hits | Containment Hits |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Prototype reverse_aux_plus_llm_example_frame_missing_rows, family phrase guard` | `family_all` | `runtime_phrase_guard_only` | 40 | 5 | 11 | 31.2% | 60.0% | 1 | 0 |
| `Prototype reverse_aux_plus_llm_example_frame_missing_rows, active phrase guard` | `active_only` | `runtime_phrase_guard_only` | 40 | 2 | 11 | 31.2% | 67.5% | 12 | 0 |
| `Prototype reverse_aux_plus_llm_example_frame_missing_rows, phrase-control containment guard` | `active_only` | `local_containment_patterns` | 40 | 2 | 11 | 31.2% | 67.5% | 12 | 2 |
| `Prototype reverse_aux_plus_llm_example_frame_missing_rows, phrase-control prototype guard` | `active_only` | `semantic_prototype_competition` | 40 | 2 | 13 | 18.8% | 62.5% | 12 | 0 |

## Residual Case Matrix

| Case | Gold | Family Guard | Active Guard | Phrase Containment Guard | Phrase Prototype Guard |
| --- | --- | --- | --- | --- | --- |
| `en-es:sentence-veto:check:001` | `replace` | `abstain` m=-0.0595 a=0.5195 s=0.5791 p=0.0 pc=false | `abstain` m=-0.0595 a=0.5195 s=0.5791 p=0.0 pc=false | `abstain` m=-0.0595 a=0.5195 s=0.5791 p=0.0 pc=false | `abstain` m=-0.0595 a=0.5195 s=0.5791 p=0.5893 pc=false |
| `en-es:sentence-veto:check:002` | `replace` | `abstain` m=-0.0176 a=0.5539 s=0.5715 p=0.0 pc=false | `abstain` m=-0.0176 a=0.5539 s=0.5715 p=0.0 pc=false | `abstain` m=-0.0176 a=0.5539 s=0.5715 p=0.0 pc=false | `abstain` m=-0.0176 a=0.5539 s=0.5715 p=0.7021 pc=false |
| `en-es:sentence-veto:check:003` | `abstain` | `replace` m=0.0892 a=0.6148 s=0.5256 p=0.0 pc=false | `abstain` m=0.0892 a=0.6148 s=0.5256 p=0.0 pc=false | `abstain` m=0.0892 a=0.6148 s=0.5256 p=0.0 pc=false | `abstain` m=0.0892 a=0.6148 s=0.5256 p=0.5369 pc=false |
| `en-es:sentence-veto:check:005` | `abstain` | `replace` m=0.0643 a=0.5859 s=0.5216 p=0.0 pc=false | `abstain` m=0.0643 a=0.5859 s=0.5216 p=0.0 pc=false | `abstain` m=0.0643 a=0.5859 s=0.5216 p=0.0 pc=false | `abstain` m=0.0643 a=0.5859 s=0.5216 p=0.5463 pc=false |
| `en-es:sentence-veto:order:001` | `replace` | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 pc=false | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 pc=false | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 pc=false | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.6877 pc=false |
| `en-es:sentence-veto:order:002` | `replace` | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 pc=false | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 pc=false | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 pc=false | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.7301 pc=false |
| `en-es:sentence-veto:plant:001` | `replace` | `abstain` m=-0.0485 a=0.521 s=0.5696 p=0.0 pc=false | `abstain` m=-0.0485 a=0.521 s=0.5696 p=0.0 pc=false | `abstain` m=-0.0485 a=0.521 s=0.5696 p=0.0 pc=false | `abstain` m=-0.0485 a=0.521 s=0.5696 p=0.5596 pc=false |
| `en-es:sentence-veto:plant:002` | `replace` | `abstain` m=-0.0405 a=0.6169 s=0.6574 p=0.0 pc=false | `abstain` m=-0.0405 a=0.6169 s=0.6574 p=0.0 pc=false | `abstain` m=-0.0405 a=0.6169 s=0.6574 p=0.0 pc=false | `abstain` m=-0.0405 a=0.6169 s=0.6574 p=0.6915 pc=false |
| `en-es:sentence-veto:play:001` | `replace` | `abstain` m=-0.0116 a=0.5151 s=0.5267 p=0.0 pc=false | `abstain` m=-0.0116 a=0.5151 s=0.5267 p=0.0 pc=false | `abstain` m=-0.0116 a=0.5151 s=0.5267 p=0.0 pc=false | `abstain` m=-0.0116 a=0.5151 s=0.5267 p=0.519 pc=false |
| `en-es:sentence-veto:play:002` | `replace` | `replace` m=0.0387 a=0.5262 s=0.4875 p=0.0 pc=false | `replace` m=0.0387 a=0.5262 s=0.4875 p=0.0 pc=false | `replace` m=0.0387 a=0.5262 s=0.4875 p=0.0 pc=false | `abstain` m=0.0387 a=0.5262 s=0.4875 p=0.5713 pc=false |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.0677 a=0.5657 s=0.4981 p=0.0 pc=false | `abstain` m=0.0677 a=0.5657 s=0.4981 p=0.0 pc=false | `abstain` m=0.0677 a=0.5657 s=0.4981 p=0.0 pc=false | `abstain` m=0.0677 a=0.5657 s=0.4981 p=0.5522 pc=false |
| `en-es:sentence-veto:report:001` | `replace` | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 pc=false | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 pc=false | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 pc=false | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.6423 pc=false |
| `en-es:sentence-veto:report:002` | `replace` | `replace` m=0.07 a=0.5679 s=0.4978 p=0.0 pc=false | `replace` m=0.07 a=0.5679 s=0.4978 p=0.0 pc=false | `replace` m=0.07 a=0.5679 s=0.4978 p=0.0 pc=false | `abstain` m=0.07 a=0.5679 s=0.4978 p=0.5914 pc=false |
| `en-es:sentence-veto:report:003` | `abstain` | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 pc=false | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 pc=false | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 pc=false | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.5594 pc=false |
| `en-es:sentence-veto:report:004` | `abstain` | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 pc=false | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 pc=false | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 pc=false | `replace` m=0.0174 a=0.567 s=0.5495 p=0.5087 pc=false |
| `en-es:sentence-veto:trip:001` | `replace` | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 pc=false | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 pc=false | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 pc=false | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.5751 pc=false |
| `en-es:sentence-veto:trip:002` | `replace` | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 pc=false | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 pc=false | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 pc=false | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.6765 pc=false |
| `en-es:sentence-veto:watch:001` | `replace` | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 pc=false | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 pc=false | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 pc=false | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.5679 pc=false |

## Recommendation

- Keep the user-facing UX binary, but move the internal experiment from a single evidence string toward prototype admission: context competes against active and shadow example frames, while phrase-control evidence can only abstain through local containment-pattern matches. The phrase-control containment guard still leaves residual cases on this evaluation slice (`67.5%` accuracy / `31.2%` recall / `2` harmful / `11` false abstains) on `prompt_queue`; keep broad phrase-control prototype scoring as an overreach control only. The `reverse_aux_plus_llm_example_frame_missing_rows` batch `en-es:example-frame-composite:reverse-aux-plus-llm-missing-rows-latest` is source evidence, but it should clear the required-family contract gate before any promotion or runtime publication claim.
