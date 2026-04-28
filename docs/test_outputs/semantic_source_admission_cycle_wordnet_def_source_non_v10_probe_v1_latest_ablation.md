# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-26T03:25:23Z`
- Queue: `semantic_source_non_v10_probe_en_es_v1`
- Runtime dataset: `en_es_source_non_v10_probe_v1`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `30`
- Prototype report runs: `6`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 24 | 0 | 7 | 53.3% | 70.8% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.005 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.005 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.005 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.005 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 24 | 0 | 6 | 60.0% | 75.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 24 | 0 | 7 | 53.3% | 70.8% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 24 | 0 | 7 | 53.3% | 70.8% |

## Assumption Audit

- best_candidate_source_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 4 false abstain, 73.3% recall
- best_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 4 false abstain, 73.3% recall
- best_viable_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 4 false abstain, 73.3% recall
- best_without_phrase_control_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 4 false abstain, 73.3% recall

### Simplification Candidates

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.005 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 24 | 0 | 4 | 73.3% | 83.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.005 | `active_shadow_active_pos_guard` | 24 | 0 | 4 | 73.3% | 83.3% |

## Recommendation

- candidate source rows can preserve the zero-harm constraint; a simplified no-surface-POS candidate matches or beats the current best.
