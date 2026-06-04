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
| `Prototype reverse_aux_example_frames, family phrase guard` | `family_all` | 40 | 7 | 8 | 50.0% | 62.5% | 1 |
| `Prototype reverse_aux_example_frames, active phrase guard` | `active_only` | 40 | 5 | 8 | 50.0% | 67.5% | 12 |
| `Prototype reverse_aux_example_frames, phrase-control prototype guard` | `active_only` | 40 | 5 | 8 | 50.0% | 67.5% | 12 |

## Residual Case Matrix

| Case | Gold | Family Guard | Active Guard | Phrase Prototype Guard |
| --- | --- | --- | --- | --- |
| `en-es:sentence-veto:check:003` | `abstain` | `replace` m=0.6148 a=0.6148 s=0.0 p=0.0 | `abstain` m=0.6148 a=0.6148 s=0.0 p=0.0 | `abstain` m=0.6148 a=0.6148 s=0.0 p=0.0 |
| `en-es:sentence-veto:check:004` | `abstain` | `replace` m=0.5797 a=0.5797 s=0.0 p=0.0 | `replace` m=0.5797 a=0.5797 s=0.0 p=0.0 | `replace` m=0.5797 a=0.5797 s=0.0 p=0.0 |
| `en-es:sentence-veto:check:005` | `abstain` | `replace` m=0.5859 a=0.5859 s=0.0 p=0.0 | `abstain` m=0.5859 a=0.5859 s=0.0 p=0.0 | `abstain` m=0.5859 a=0.5859 s=0.0 p=0.0 |
| `en-es:sentence-veto:order:001` | `replace` | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 | `abstain` m=-0.0076 a=0.5595 s=0.5671 p=0.0 |
| `en-es:sentence-veto:order:002` | `replace` | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 | `abstain` m=-0.0321 a=0.5323 s=0.5645 p=0.0 |
| `en-es:sentence-veto:plant:003` | `abstain` | `replace` m=0.4406 a=0.4406 s=0.0 p=0.0 | `replace` m=0.4406 a=0.4406 s=0.0 p=0.0 | `replace` m=0.4406 a=0.4406 s=0.0 p=0.0 |
| `en-es:sentence-veto:plant:004` | `abstain` | `replace` m=0.5029 a=0.5029 s=0.0 p=0.0 | `replace` m=0.5029 a=0.5029 s=0.0 p=0.0 | `replace` m=0.5029 a=0.5029 s=0.0 p=0.0 |
| `en-es:sentence-veto:play:001` | `replace` | `abstain` m=-0.5267 a=0.0 s=0.5267 p=0.0 | `abstain` m=-0.5267 a=0.0 s=0.5267 p=0.0 | `abstain` m=-0.5267 a=0.0 s=0.5267 p=0.0 |
| `en-es:sentence-veto:play:002` | `replace` | `abstain` m=-0.4875 a=0.0 s=0.4875 p=0.0 | `abstain` m=-0.4875 a=0.0 s=0.4875 p=0.0 | `abstain` m=-0.4875 a=0.0 s=0.4875 p=0.0 |
| `en-es:sentence-veto:report:001` | `replace` | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 | `abstain` m=-0.0117 a=0.5755 s=0.5872 p=0.0 |
| `en-es:sentence-veto:report:003` | `abstain` | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 | `replace` m=0.0226 a=0.6607 s=0.6381 p=0.0 |
| `en-es:sentence-veto:report:004` | `abstain` | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 | `replace` m=0.0174 a=0.567 s=0.5495 p=0.0 |
| `en-es:sentence-veto:trip:001` | `replace` | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 | `abstain` m=-0.0423 a=0.5481 s=0.5904 p=0.0 |
| `en-es:sentence-veto:trip:002` | `replace` | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 | `abstain` m=-0.0634 a=0.5277 s=0.5912 p=0.0 |
| `en-es:sentence-veto:watch:001` | `replace` | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 | `abstain` m=-0.0291 a=0.5806 s=0.6098 p=0.0 |

## Recommendation

- Keep the user-facing UX binary, but move the internal experiment from a single evidence string toward prototype admission: context competes against active, shadow, and phrase-control example frames, then resolves to replace or abstain. The phrase-control prototype guard still leaves residual cases on this evaluation slice (`67.5%` accuracy / `50.0%` recall / `5` harmful / `8` false abstains) on `prompt_queue`. The `reverse_aux_example_frames` batch `en-es:reverse-aux-example-frames:reverse-aux-example-frames-v10-20260425a` is source evidence, but it should clear the required-family contract gate before any promotion or runtime publication claim.
