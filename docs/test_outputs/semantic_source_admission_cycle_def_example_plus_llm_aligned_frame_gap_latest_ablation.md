# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-28T21:03:11Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `20`
- Prototype report runs: `4`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 14 | 63.2% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 7 | 81.6% | 90.5% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 1 | 97.4% | 99.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 4 | 89.5% | 95.8% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 4 | 89.5% | 95.8% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 14 | 63.2% | 83.2% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 14 | 63.2% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 95 | 4 | 14 | 63.2% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_family_pos_guard` | 95 | 5 | 7 | 81.6% | 87.4% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 5 | 7 | 81.6% | 87.4% |

## Assumption Audit

- best_candidate_source_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 0 harmful, 1 false abstain, 97.4% recall
- best_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 81.6% recall
- best_viable_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 81.6% recall
- best_without_phrase_control_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 7 false abstain, 81.6% recall

## Recommendation

- candidate source rows can preserve the zero-harm constraint; the current best still depends on the richer guard stack.
