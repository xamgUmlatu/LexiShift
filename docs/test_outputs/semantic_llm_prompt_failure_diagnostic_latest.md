# en-es Semantic LLM Prompt Failure Diagnostic

- Status: `ok`
- Generated: `2026-04-24T19:26:57Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- LLM batch: `en-es:target:prompt-target-overlap-v3-20260425a`
- Scorer: `sentence_transformer_cosine`

## Configuration Summary

| Config | Category | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced Harmful |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `Hard current default runtime row` | `baseline` | 1 | 8 | 50.0% | 77.5% | none | none |
| `Hard reverse aux plus all evidence` | `source_control` | 1 | 6 | 62.5% | 82.5% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | none |
| `Hard reverse aux active-only` | `source_ablation` | 1 | 7 | 56.2% | 80.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:plant:002` | none |
| `Hard LLM cue text only` | `llm_diagnostic` | 5 | 5 | 68.8% | 75.0% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:plant:002` | `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:003`, `en-es:sentence-veto:report:004`, `en-es:sentence-veto:report:005` |
| `Hard LLM cue plus all evidence` | `llm_safe_additive` | 3 | 8 | 50.0% | 72.5% | `en-es:sentence-veto:order:002` | `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:005` |
| `Hard reverse aux plus LLM cue` | `combined_source_probe` | 1 | 6 | 62.5% | 82.5% | none | none |

## LLM Rescue Probe

| Backup Config | Primary Margin Floor | Harmful | False Abstain | Replace Recall | Rescue Cases |
| --- | ---: | ---: | ---: | ---: | --- |
| `hard_llm_cue_text` | -0.1 | 5 | 5 | 68.8% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:report:003`, `en-es:sentence-veto:report:004`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_text` | -0.05 | 5 | 5 | 68.8% | `en-es:sentence-veto:drink:002`, `en-es:sentence-veto:order:002`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:plant:002`, `en-es:sentence-veto:report:003`, `en-es:sentence-veto:report:004`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_text` | -0.02 | 3 | 7 | 56.2% | `en-es:sentence-veto:order:002`, `en-es:sentence-veto:report:004`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_text` | 0.0 | 1 | 8 | 50.0% | none |
| `hard_llm_cue_plus_all_evidence` | -0.1 | 3 | 7 | 56.2% | `en-es:sentence-veto:order:002`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_plus_all_evidence` | -0.05 | 3 | 7 | 56.2% | `en-es:sentence-veto:order:002`, `en-es:sentence-veto:order:005`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_plus_all_evidence` | -0.02 | 2 | 7 | 56.2% | `en-es:sentence-veto:order:002`, `en-es:sentence-veto:report:005` |
| `hard_llm_cue_plus_all_evidence` | 0.0 | 1 | 8 | 50.0% | none |

## Case Diagnostics

| Case | Gold | Baseline | Reverse Aux | LLM + All | Reverse + LLM |
| --- | --- | --- | --- | --- | --- |
| `en-es:sentence-veto:check:002` | `replace` | `abstain` m=-0.0448 a=0.5522 s=0.597 | `abstain` m=-0.0436 a=0.5534 s=0.597 | `abstain` m=-0.0521 a=0.5448 s=0.597 | `abstain` m=-0.0577 a=0.5393 s=0.597 |
| `en-es:sentence-veto:drink:001` | `replace` | `replace` m=-0.0118 a=0.631 s=0.6428 | `replace` m=0.021 a=0.6434 s=0.6224 | `abstain` m=-0.0357 a=0.6071 s=0.6428 | `replace` m=-0.0072 a=0.6152 s=0.6224 |
| `en-es:sentence-veto:drink:002` | `replace` | `abstain` m=-0.0208 a=0.6423 s=0.6631 | `replace` m=0.0163 a=0.667 s=0.6507 | `abstain` m=-0.0322 a=0.6308 s=0.6631 | `replace` m=-0.0111 a=0.6396 s=0.6507 |
| `en-es:sentence-veto:order:002` | `replace` | `abstain` m=-0.0108 a=0.6104 s=0.6212 | `replace` m=0.0043 a=0.6049 s=0.6006 | `replace` m=0.0194 a=0.6406 s=0.6212 | `replace` m=0.0277 a=0.6283 s=0.6006 |
| `en-es:sentence-veto:order:005` | `abstain` | `abstain` m=-0.0366 a=0.5463 s=0.583 | `abstain` m=-0.0482 a=0.5362 s=0.5843 | `replace` m=0.0098 a=0.5928 s=0.583 | `abstain` m=-0.0047 a=0.5797 s=0.5843 |
| `en-es:sentence-veto:plant:002` | `replace` | `abstain` m=-0.0202 a=0.5818 s=0.602 | `replace` m=0.0048 a=0.6068 s=0.602 | `abstain` m=-0.0256 a=0.5764 s=0.602 | `replace` m=-0.0195 a=0.5825 s=0.602 |
| `en-es:sentence-veto:play:002` | `replace` | `abstain` m=-0.0295 a=0.4924 s=0.5219 | `abstain` m=-0.0008 a=0.4924 s=0.4933 | `abstain` m=-0.0295 a=0.4924 s=0.5219 | `abstain` m=-0.0008 a=0.4924 s=0.4933 |
| `en-es:sentence-veto:play:005` | `abstain` | `replace` m=0.0654 a=0.5591 s=0.4937 | `replace` m=0.0834 a=0.5591 s=0.4758 | `replace` m=0.0654 a=0.5591 s=0.4937 | `replace` m=0.0834 a=0.5591 s=0.4758 |
| `en-es:sentence-veto:report:001` | `replace` | `abstain` m=-0.0479 a=0.5676 s=0.6155 | `abstain` m=-0.0331 a=0.5714 s=0.6045 | `abstain` m=-0.0555 a=0.56 s=0.6155 | `abstain` m=-0.0426 a=0.5618 s=0.6045 |
| `en-es:sentence-veto:report:002` | `replace` | `abstain` m=-0.0705 a=0.5044 s=0.5749 | `abstain` m=-0.0447 a=0.5199 s=0.5646 | `abstain` m=-0.0545 a=0.5205 s=0.5749 | `abstain` m=-0.0366 a=0.528 s=0.5646 |
| `en-es:sentence-veto:report:003` | `abstain` | `abstain` m=-0.0281 a=0.5607 s=0.5888 | `abstain` m=-0.0215 a=0.562 s=0.5835 | `abstain` m=-0.0364 a=0.5524 s=0.5888 | `abstain` m=-0.0366 a=0.5469 s=0.5835 |
| `en-es:sentence-veto:report:004` | `abstain` | `abstain` m=-0.017 a=0.6038 s=0.6208 | `abstain` m=-0.0139 a=0.594 s=0.6079 | `abstain` m=-0.0076 a=0.6132 s=0.6208 | `abstain` m=-0.0063 a=0.6016 s=0.6079 |
| `en-es:sentence-veto:report:005` | `abstain` | `abstain` m=-0.0119 a=0.6365 s=0.6484 | `abstain` m=-0.0155 a=0.6196 s=0.6351 | `replace` m=0.0064 a=0.6548 s=0.6484 | `abstain` m=-0.0028 a=0.6323 s=0.6351 |
| `en-es:sentence-veto:trip:002` | `replace` | `abstain` m=-0.0134 a=0.5669 s=0.5803 | `abstain` m=-0.0208 a=0.5616 s=0.5824 | `abstain` m=-0.0435 a=0.5368 s=0.5803 | `abstain` m=-0.0511 a=0.5313 s=0.5824 |
| `en-es:sentence-veto:watch:001` | `replace` | `replace` m=0.0009 a=0.5722 s=0.5713 | `abstain` m=-0.036 a=0.5556 s=0.5916 | `replace` m=0.0009 a=0.5722 s=0.5713 | `abstain` m=-0.036 a=0.5556 s=0.5916 |

## Recommendation

- Stop prompt-only iteration. The accepted LLM overlap cues are valid text, but the safe additive lane is `72.5%` accuracy / `50.0%` recall / `3` harmful / `8` false abstains, while reverse auxiliary evidence is `82.5%` accuracy / `62.5%` recall / `1` harmful / `6` false abstains. Adding LLM cues on top of reverse auxiliary evidence is `82.5%` accuracy / `62.5%` recall / `1` harmful / `6` false abstains, so the cue text adds no incremental value once the source-derived active/shadow evidence is present. The best rescue-only LLM probe is `hard_llm_cue_text` at margin floor `0.0`: 77.5% accuracy / 50.0% recall / 1 harmful / 8 false abstains, which still does not beat the reverse-aux control. The next path should be source/insertion work: build or ingest competition-symmetric evidence for active and shadow senses, then rerun this diagnostic before any paid generation.
