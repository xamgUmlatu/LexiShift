# en-es Semantic LLM Source/Insertion Probe

- Status: `ok`
- Generated: `2026-04-24T19:26:57Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- LLM batch: `en-es:target:prompt-target-overlap-v3-20260425a`
- Scorer: `sentence_transformer_cosine`

## Insertion Matrix

| Config | Category | Phrase Guard | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced Harmful |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `Hard current default runtime row` | `baseline` | `family_all` | 1 | 8 | 50.0% | 77.5% | none | none |
| `Hard reverse aux active-only` | `source_ablation` | `family_all` | 1 | 7 | 56.2% | 80.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:plant:002` | none |
| `Hard reverse aux shadow-only` | `source_ablation` | `family_all` | 2 | 7 | 56.2% | 77.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002` | `en-es:sentence-veto:report:005` |
| `Hard reverse aux symmetric` | `source_control` | `family_all` | 1 | 6 | 62.5% | 82.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | none |
| `Hard LLM active cue with base shadows` | `llm_insertion_probe` | `family_all` | 3 | 8 | 50.0% | 72.5% | `en-es:sentence-veto:order:002` | `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:005` |
| `Hard LLM active cue with reverse shadows` | `mixed_insertion_probe` | `family_all` | 4 | 7 | 56.2% | 72.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002` | `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:004`, `en-es:sentence-veto:report:005` |
| `Hard reviewed example frames` | `reviewed_source_oracle` | `family_all` | 3 | 0 | 100.0% | 92.5% | `en-es:sentence-veto:check:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:report:001`, `en-es:sentence-veto:report:002`, `en-es:sentence-veto:trip:002` | `en-es:sentence-veto:drink:005`, `en-es:sentence-veto:order:005` |
| `Active-guard reviewed example frames` | `reviewed_source_oracle` | `active_only` | 0 | 0 | 100.0% | 100.0% | `en-es:sentence-veto:check:002`, `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:play:002`, `en-es:sentence-veto:report:001`, `en-es:sentence-veto:report:002`, `en-es:sentence-veto:trip:002` | none |
| `Hard reverse aux plus LLM cue` | `combined_source_probe` | `family_all` | 1 | 6 | 62.5% | 82.5% | none | none |

## Focus Case Matrix

| Case | Gold | Baseline | Reverse active | Reverse shadow | Reverse full | LLM active + reverse shadow | Reviewed active guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `en-es:sentence-veto:check:002` | `replace` | `abstain` m=-0.0448 a=0.5522 s=0.597 | `abstain` m=-0.0436 a=0.5534 s=0.597 | `abstain` m=-0.0448 a=0.5522 s=0.597 | `abstain` m=-0.0436 a=0.5534 s=0.597 | `abstain` m=-0.0521 a=0.5448 s=0.597 | `replace` m=0.2229 a=0.7834 s=0.5605 |
| `en-es:sentence-veto:drink:001` | `replace` | `replace` m=-0.0118 a=0.631 s=0.6428 | `replace` m=0.0006 a=0.6434 s=0.6428 | `replace` m=0.0086 a=0.631 s=0.6224 | `replace` m=0.021 a=0.6434 s=0.6224 | `replace` m=-0.0153 a=0.6071 s=0.6224 | `replace` m=0.4312 a=0.9032 s=0.4719 |
| `en-es:sentence-veto:drink:002` | `replace` | `abstain` m=-0.0208 a=0.6423 s=0.6631 | `replace` m=0.004 a=0.667 s=0.6631 | `replace` m=-0.0084 a=0.6423 s=0.6507 | `replace` m=0.0163 a=0.667 s=0.6507 | `replace` m=-0.0199 a=0.6308 s=0.6507 | `replace` m=0.3255 a=0.9046 s=0.5791 |
| `en-es:sentence-veto:drink:005` | `abstain` | `abstain` m=-0.0338 a=0.5637 s=0.5974 | `abstain` m=-0.024 a=0.5734 s=0.5974 | `abstain` m=-0.046 a=0.5637 s=0.6097 | `abstain` m=-0.0362 a=0.5734 s=0.6097 | `abstain` m=-0.0388 a=0.5709 s=0.6097 | `abstain` m=0.1366 a=0.6692 s=0.5326 |
| `en-es:sentence-veto:order:002` | `replace` | `abstain` m=-0.0108 a=0.6104 s=0.6212 | `abstain` m=-0.0163 a=0.6049 s=0.6212 | `replace` m=0.0098 a=0.6104 s=0.6006 | `replace` m=0.0043 a=0.6049 s=0.6006 | `replace` m=0.04 a=0.6406 s=0.6006 | `replace` m=0.3679 a=0.9531 s=0.5852 |
| `en-es:sentence-veto:order:005` | `abstain` | `abstain` m=-0.0366 a=0.5463 s=0.583 | `abstain` m=-0.0468 a=0.5362 s=0.583 | `abstain` m=-0.038 a=0.5463 s=0.5843 | `abstain` m=-0.0482 a=0.5362 s=0.5843 | `replace` m=0.0085 a=0.5928 s=0.5843 | `abstain` m=0.0211 a=0.6348 s=0.6137 |
| `en-es:sentence-veto:plant:002` | `replace` | `abstain` m=-0.0202 a=0.5818 s=0.602 | `replace` m=0.0048 a=0.6068 s=0.602 | `abstain` m=-0.0202 a=0.5818 s=0.602 | `replace` m=0.0048 a=0.6068 s=0.602 | `abstain` m=-0.0256 a=0.5764 s=0.602 | `replace` m=0.2062 a=0.8567 s=0.6505 |
| `en-es:sentence-veto:play:002` | `replace` | `abstain` m=-0.0295 a=0.4924 s=0.5219 | `abstain` m=-0.0295 a=0.4924 s=0.5219 | `abstain` m=-0.0008 a=0.4924 s=0.4933 | `abstain` m=-0.0008 a=0.4924 s=0.4933 | `abstain` m=-0.0008 a=0.4924 s=0.4933 | `replace` m=0.2844 a=0.8392 s=0.5549 |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.0654 a=0.5591 s=0.4937 | `replace` m=0.0654 a=0.5591 s=0.4937 | `replace` m=0.0834 a=0.5591 s=0.4758 | `replace` m=0.0834 a=0.5591 s=0.4758 | `replace` m=0.0834 a=0.5591 s=0.4758 | `abstain` m=0.0023 a=0.5486 s=0.5462 |
| `en-es:sentence-veto:report:001` | `replace` | `abstain` m=-0.0479 a=0.5676 s=0.6155 | `abstain` m=-0.0442 a=0.5714 s=0.6155 | `abstain` m=-0.0369 a=0.5676 s=0.6045 | `abstain` m=-0.0331 a=0.5714 s=0.6045 | `abstain` m=-0.0444 a=0.56 s=0.6045 | `replace` m=0.2749 a=0.8497 s=0.5748 |
| `en-es:sentence-veto:report:002` | `replace` | `abstain` m=-0.0705 a=0.5044 s=0.5749 | `abstain` m=-0.0551 a=0.5199 s=0.5749 | `abstain` m=-0.0601 a=0.5044 s=0.5646 | `abstain` m=-0.0447 a=0.5199 s=0.5646 | `abstain` m=-0.0441 a=0.5205 s=0.5646 | `replace` m=0.3313 a=0.9108 s=0.5795 |
| `en-es:sentence-veto:report:004` | `abstain` | `abstain` m=-0.017 a=0.6038 s=0.6208 | `abstain` m=-0.0268 a=0.594 s=0.6208 | `abstain` m=-0.0041 a=0.6038 s=0.6079 | `abstain` m=-0.0139 a=0.594 s=0.6079 | `replace` m=0.0053 a=0.6132 s=0.6079 | `abstain` m=-0.2691 a=0.5811 s=0.8502 |
| `en-es:sentence-veto:report:005` | `abstain` | `abstain` m=-0.0119 a=0.6365 s=0.6484 | `abstain` m=-0.0288 a=0.6196 s=0.6484 | `replace` m=0.0014 a=0.6365 s=0.6351 | `abstain` m=-0.0155 a=0.6196 s=0.6351 | `replace` m=0.0197 a=0.6548 s=0.6351 | `abstain` m=-0.0202 a=0.6294 s=0.6496 |
| `en-es:sentence-veto:trip:002` | `replace` | `abstain` m=-0.0134 a=0.5669 s=0.5803 | `abstain` m=-0.0187 a=0.5616 s=0.5803 | `abstain` m=-0.0155 a=0.5669 s=0.5824 | `abstain` m=-0.0208 a=0.5616 s=0.5824 | `abstain` m=-0.0457 a=0.5368 s=0.5824 | `replace` m=0.3323 a=0.9003 s=0.568 |
| `en-es:sentence-veto:watch:001` | `replace` | `replace` m=0.0009 a=0.5722 s=0.5713 | `abstain` m=-0.0157 a=0.5556 s=0.5713 | `abstain` m=-0.0194 a=0.5722 s=0.5916 | `abstain` m=-0.036 a=0.5556 s=0.5916 | `abstain` m=-0.0194 a=0.5722 s=0.5916 | `replace` m=0.369 a=0.896 s=0.527 |

## Recommendation

- Keep the next step source/insertion-shaped. Full reverse-aux evidence is `82.5%` accuracy / `62.5%` recall / `1` harmful / `6` false abstains, while active-only reverse is `80.0%` accuracy / `56.2%` recall / `1` harmful / `7` false abstains and shadow-only reverse is `77.5%` accuracy / `56.2%` recall / `2` harmful / `7` false abstains. The mixed LLM-active plus reverse-shadow probe is `72.5%` accuracy / `56.2%` recall / `4` harmful / `7` false abstains, so shadow calibration alone does not salvage active-only LLM cue insertion. The internal reviewed example-frame oracle with the active-sense phrase guard is `100.0%` accuracy / `100.0%` recall / `0` harmful / `0` false abstains, which shows the next viable path is competition-symmetric example/frame evidence plus phrase-leak containment. It is not runtime-publishable evidence; use it as an upper-bound target for external source ingestion or future paid generation.
