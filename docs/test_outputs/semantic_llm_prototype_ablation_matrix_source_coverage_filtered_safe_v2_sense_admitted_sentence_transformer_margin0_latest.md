# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-25T00:54:40Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `20`
- Prototype report runs: `4`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 12 | 68.4% | 84.2% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 9 | 76.3% | 88.4% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 6 | 84.2% | 91.6% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 9 | 76.3% | 88.4% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 9 | 76.3% | 88.4% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 12 | 68.4% | 85.3% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 12 | 68.4% | 84.2% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 12 | 68.4% | 84.2% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_family_pos_guard` | 95 | 5 | 6 | 84.2% | 88.4% |
| `custom_1` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 5 | 6 | 84.2% | 88.4% |

## Assumption Audit

- best_candidate_source_row: `custom_1` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 0 false abstain, 100.0% recall
- best_without_surface_pos_row: `custom_1` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 6 false abstain, 84.2% recall
- best_viable_without_surface_pos_row: `custom_1` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 6 false abstain, 84.2% recall
- best_without_phrase_control_row: `custom_1` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 6 false abstain, 84.2% recall

## Recommendation

- candidate source rows can preserve the zero-harm constraint; the current best still depends on the richer guard stack.
