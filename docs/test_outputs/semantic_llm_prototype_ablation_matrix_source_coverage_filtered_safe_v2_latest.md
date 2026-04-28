# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-25T00:11:57Z`
- Queue: `semantic_prompt_bakeoff_en_es_v10`
- Runtime dataset: `en_es_sentence_veto_v10`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `2240`
- Prototype report runs: `448`

## Best Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |

## Candidate Source Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_composite` | `all_dataset_families` | `token_jaccard` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 8 | 79.0% | 91.6% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |

## Best by Source Mode

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `empty_batch` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 40 | 0 | 16 | 0.0% | 60.0% |
| `generated_active_only` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 40 | 0 | 16 | 0.0% | 60.0% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_no_phrase` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_no_shadow` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 40 | 0 | 16 | 0.0% | 60.0% |
| `reverse_aux` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 4 | 75.0% | 90.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |

## Candidate by Decision Shape

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_active_only` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 40 | 0 | 16 | 0.0% | 60.0% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_active_only` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 40 | 0 | 16 | 0.0% | 60.0% |
| `generated_active_only` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 40 | 0 | 16 | 0.0% | 60.0% |
| `generated_active_only` | `prompt_queue` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 40 | 0 | 16 | 0.0% | 60.0% |

## Candidate by Context View

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `generated_composite` | `prompt_queue` | `token_jaccard` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `raw_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |
| `generated_composite` | `prompt_queue` | `tfidf_cosine` | `raw_window` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 40 | 0 | 1 | 93.8% | 97.5% |

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 95 | 0 | 0 | 100.0% | 100.0% |
| `reviewed_dataset` | `all_dataset_families` | `tfidf_cosine` | `masked_window` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 95 | 0 | 0 | 100.0% | 100.0% |

## Assumption Audit

- best_oracle_row: `reviewed_dataset` / `all_dataset_families` / `tfidf_cosine` / `masked_sentence` / `active_shadow_phrase_semantic_prototypes` -> 0 harmful, 0 false abstain, 100.0% recall
- best_candidate_source_row: `generated_composite` / `prompt_queue` / `tfidf_cosine` / `masked_window` / `active_shadow_containment_surface_pos` -> 0 harmful, 1 false abstain, 93.8% recall
- best_empty_baseline_row: `empty_batch` / `prompt_queue` / `tfidf_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 16 false abstain, 0.0% recall
- best_without_surface_pos_row: `generated_active_only` / `prompt_queue` / `tfidf_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 16 false abstain, 0.0% recall
- best_viable_without_surface_pos_row: `generated_active_only` / `all_dataset_families` / `tfidf_cosine` / `raw_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 37 false abstain, 2.6% recall
- best_without_phrase_control_row: `generated_active_only` / `prompt_queue` / `tfidf_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 16 false abstain, 0.0% recall
- best_generated_composite_row: `generated_composite` / `prompt_queue` / `tfidf_cosine` / `masked_window` / `active_shadow_containment_surface_pos` -> 0 harmful, 1 false abstain, 93.8% recall
- best_generated_active_only_row: `generated_active_only` / `prompt_queue` / `tfidf_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 16 false abstain, 0.0% recall
- best_generated_no_phrase_row: `generated_no_phrase` / `prompt_queue` / `tfidf_cosine` / `masked_window` / `active_shadow_containment_surface_pos` -> 0 harmful, 1 false abstain, 93.8% recall
- best_generated_no_shadow_row: `generated_no_shadow` / `prompt_queue` / `tfidf_cosine` / `masked_sentence` / `active_shadow_active_pos_guard` -> 0 harmful, 16 false abstain, 0.0% recall

## Recommendation

- candidate source rows can preserve the zero-harm constraint; there is still an oracle-vs-source gap, so source coverage remains a first-order node; the current best still depends on the richer guard stack.
