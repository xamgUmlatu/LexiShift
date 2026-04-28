# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-25T01:42:40Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `20`
- Prototype report runs: `4`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 16 | 57.9% | 80.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 16 | 57.9% | 81.0% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 2 | 7 | 81.6% | 90.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 2 | 16 | 57.9% | 81.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 3 | 2 | 94.7% | 94.7% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 3 | 2 | 94.7% | 94.7% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 3 | 7 | 81.6% | 89.5% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 16 | 57.9% | 80.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 95 | 3 | 16 | 57.9% | 80.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_family_pos_guard` | 95 | 6 | 7 | 81.6% | 86.3% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 6 | 7 | 81.6% | 86.3% |

## Assumption Audit

- best_candidate_source_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_containment_surface_pos` -> 2 harmful, 7 false abstain, 81.6% recall
- best_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 16 false abstain, 57.9% recall
- best_viable_without_surface_pos_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 16 false abstain, 57.9% recall
- best_without_phrase_control_row: `cycle_merged` / `all_dataset_families` / `sentence_transformer_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 2 harmful, 16 false abstain, 57.9% recall

## Recommendation

- candidate source rows still leak harmful replacements; the current best still depends on the richer guard stack.
