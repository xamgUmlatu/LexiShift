# en-es LLM Example-Frame Generation Plan

- Status: `ready`
- Generated: `2026-04-25T00:44:42Z`
- Dataset: `en_es_sentence_veto_v10`
- Required families: `semantic_prompt_bakeoff_en_es_v10`
- Base batch: `en-es:reverse-aux-example-frames:reverse-aux-example-frames-v10-20260425a`
- Prompt version: `example-frame-missing-rows-v1`
- Selected model: `gpt-5.4-mini`
- Decision contract: `binary_replace_or_abstain`
- Review leakage policy: `do_not_include_sentence_veto_case_sentences_in_prompts`
- Generation targets: `active_example, shadow_example`
- Candidate defaults: `{"hard_semantic_candidates_per_row": 10, "hard_semantic_condition": "active_and_candidate_sense_share_canonical_pos", "phrase_candidates_per_row": 1, "semantic_candidates_per_row": 5}`

## Summary

- Requests: `20`
- Families: `3`
- Candidate slots: `3`
- Planned raw candidates: `20`
- Planned semantic candidates: `20`
- Planned phrase candidates: `0`
- Estimated input tokens: `7470`
- Expected output tokens: `1000`
- Max output tokens: `3600`
- Requests by target: `{"active_example": 5, "shadow_example": 15}`
- Requests by strategy: `{"same_pos_hard_semantic": 10, "standard_semantic": 10}`

## Request Rows

| Request | Target | Family | Candidate | Attempt | Strategy | Input Tokens |
| --- | --- | --- | --- | ---: | --- | ---: |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-01` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 1 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-02` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 2 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-03` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 3 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-04` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 4 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-05` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 5 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-06` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 6 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-07` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 7 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-08` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 8 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-09` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 9 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-plant-planta:en-es-sentence-veto-plant-fabrica-shadow:candidate-10` | `shadow_example` | `en-es:sentence-veto:plant:planta` | `fábrica` | 10 | `same_pos_hard_semantic` | 379 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow:candidate-01` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 1 | `standard_semantic` | 384 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow:candidate-02` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 2 | `standard_semantic` | 384 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow:candidate-03` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 3 | `standard_semantic` | 384 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow:candidate-04` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 4 | `standard_semantic` | 384 |
| `en-es:example-frame-missing:shadow:en-es-sentence-veto-check-cheque:en-es-sentence-veto-check-revisar-shadow:candidate-05` | `shadow_example` | `en-es:sentence-veto:check:cheque` | `revisar` | 5 | `standard_semantic` | 384 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra:candidate-01` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 1 | `standard_semantic` | 352 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra:candidate-02` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 2 | `standard_semantic` | 352 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra:candidate-03` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 3 | `standard_semantic` | 352 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra:candidate-04` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 4 | `standard_semantic` | 352 |
| `en-es:example-frame-missing:active:en-es-sentence-veto-play-obra:candidate-05` | `active_example` | `en-es:sentence-veto:play:obra` | `obra` | 5 | `standard_semantic` | 352 |

## Recommendation

- Execute only these selected candidate requests, preserve raw generated count separately from structurally accepted, leakage-kept, and admitted counts, then merge admitted rows with the base evidence batch and rerun the split contract plus prototype-admission ablation matrix.
