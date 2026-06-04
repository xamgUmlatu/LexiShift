# en-es Semantic LLM Prototype Ablation Matrix

- Status: `ok`
- Generated: `2026-04-27T22:53:31Z`
- Queue: `semantic_source_non_v10_wave2_admission_selected_queue_en_es_v1`
- Runtime dataset: `en_es_source_non_v10_wave2_admission_selected_v1`
- Decision contract: `binary_replace_or_abstain`
- Matrix rows: `20`
- Prototype report runs: `4`

## Best Rows

No best rows.

## Candidate Source Rows

No candidate source rows.

## Best by Source Mode

No sources.

## Candidate by Decision Shape

No decision shapes.

## Candidate by Context View

No contexts.

## Top Matrix Rows

| Source | Scope | Scorer | Context | Active | Margin | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_active_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_family_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_containment` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.0 | `active_shadow_containment_surface_pos` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_active_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_family_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_containment` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.0 | 0.05 | `active_shadow_containment_surface_pos` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_active_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_family_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_containment` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_phrase_semantic_prototypes` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.0 | `active_shadow_containment_surface_pos` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_active_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_family_pos_guard` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_containment` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_phrase_semantic_prototypes` | 0 | 0 | 0 | 0.0% | 0.0% |
| `cycle_merged` | `all_dataset_families` | `sentence_transformer_cosine` | `masked_sentence` | 0.35 | 0.05 | `active_shadow_containment_surface_pos` | 0 | 0 | 0 | 0.0% | 0.0% |

## Assumption Audit


## Recommendation

- No candidate source row was available; resolve source inputs before tuning.
