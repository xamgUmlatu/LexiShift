# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-24T23:39:49Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `5`
- Prototype report runs: `1`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 40 | 2 | 7 | 56.2% | 77.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 40 | 6 | 7 | 56.2% | 67.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 40 | 2 | 7 | 56.2% | 77.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 40 | 2 | 9 | 43.8% | 72.5% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 2 | 87.5% | 95.0% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 40 | 2 | 7 | 56.2% | 77.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 40 | 2 | 7 | 56.2% | 77.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 40 | 2 | 9 | 43.8% | 72.5% |
| `generated_composite` | `prompt_queue` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 40 | 6 | 7 | 56.2% | 67.5% |

## Assumption Audit

- best_candidate_source_row: `generated_composite` / `prompt_queue` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 2 false abstain, 87.5% recall
- best_without_surface_pos_row: `generated_composite` / `prompt_queue` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 56.2% recall
- best_viable_without_surface_pos_row: `generated_composite` / `prompt_queue` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 56.2% recall
- best_without_phrase_control_row: `generated_composite` / `prompt_queue` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 56.2% recall
- best_generated_composite_row: `generated_composite` / `prompt_queue` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 2 false abstain, 87.5% recall

## Recommendation

- candidate source rows can preserve the zero-harm constraint; the current best still depends on the richer guard stack.
