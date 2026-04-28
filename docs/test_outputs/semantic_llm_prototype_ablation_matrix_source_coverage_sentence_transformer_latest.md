# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-25T00:04:53Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `20`
- Prototype report runs: `4`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 13 | 65.8% | 82.1% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 1 | 13 | 65.8% | 85.3% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 2 | 94.7% | 97.9% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 1 | 13 | 65.8% | 85.3% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 8 | 79.0% | 89.5% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 8 | 79.0% | 89.5% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 8 | 79.0% | 89.5% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 8 | 79.0% | 89.5% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 10 | 73.7% | 87.4% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 10 | 73.7% | 87.4% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 13 | 65.8% | 82.1% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 13 | 65.8% | 82.1% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_family_pos_guard` | 95 | 7 | 8 | 79.0% | 84.2% |
| `generated_composite` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 7 | 8 | 79.0% | 84.2% |

## Assumption Audit

- best_candidate_source_row: `generated_composite` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 2 false abstain, 94.7% recall
- best_without_surface_pos_row: `generated_composite` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 1 harmful, 13 false abstain, 65.8% recall
- best_viable_without_surface_pos_row: `generated_composite` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 1 harmful, 13 false abstain, 65.8% recall
- best_without_phrase_control_row: `generated_composite` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 1 harmful, 13 false abstain, 65.8% recall
- best_generated_composite_row: `generated_composite` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 2 false abstain, 94.7% recall

## Recommendation

- candidate source rows can preserve the zero-harm constraint; the current best still depends on the richer guard stack.
