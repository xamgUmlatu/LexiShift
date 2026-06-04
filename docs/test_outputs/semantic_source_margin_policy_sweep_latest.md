# en-es Semantic Source Margin Policy Sweep

- Status: `ok`
- Decision: `margin_candidate_found`
- Generated: `2026-04-26T03:28:08Z`
- Base dataset: `en_es_sentence_veto_v10`
- Evidence batch: `en-es:example-frame-composite:reverse-aux-wordnet-wiktextract-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1:sense-admitted`
- Recommended min margin: `0.005`
- Passing margins: `0.005, 0.01`

## Configured Lane

- source_mode: `promotion_candidate_composite`
- scorer_id: `sentence_transformer_cosine`
- context_view: `masked_sentence`
- min_active_score: `0.0`
- decision_shape: `active_shadow_containment_surface_pos`

## Recommendation

- Decision: `candidate_margin`
- Reason: `smallest_passing_margin`
- Next step: stress the candidate margin on non-v10 and broader phrase held-out suites

## Rows

| Suite | Type | Margin | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `active_shadow_v2` | `heldout` | `0` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow_v2` | `heldout` | `0.001` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow_v2` | `heldout` | `0.005` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow_v2` | `heldout` | `0.01` | `true` | 38 | 0 | 0 | 100.0% | 100.0% |
| `active_shadow_v2` | `heldout` | `0.02` | `false` | 38 | 0 | 2 | 89.5% | 94.7% |
| `active_shadow_v2` | `heldout` | `0.05` | `false` | 38 | 0 | 2 | 89.5% | 94.7% |
| `phrase_v1` | `heldout` | `0` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v1` | `heldout` | `0.001` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v1` | `heldout` | `0.005` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v1` | `heldout` | `0.01` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v1` | `heldout` | `0.02` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v1` | `heldout` | `0.05` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v2` | `heldout` | `0` | `false` | 38 | 1 | 0 | 0.0% | 97.4% |
| `phrase_v2` | `heldout` | `0.001` | `false` | 38 | 1 | 0 | 0.0% | 97.4% |
| `phrase_v2` | `heldout` | `0.005` | `true` | 38 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v2` | `heldout` | `0.01` | `true` | 38 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v2` | `heldout` | `0.02` | `true` | 38 | 0 | 0 | 0.0% | 100.0% |
| `phrase_v2` | `heldout` | `0.05` | `true` | 38 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0.001` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0.005` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0.01` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0.02` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_challenge_v1` | `heldout` | `0.05` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0.001` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0.005` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0.01` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0.02` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `phrase_stress_v1` | `heldout` | `0.05` | `true` | 19 | 0 | 0 | 0.0% | 100.0% |
| `full_v10_ablation` | `full_dataset_ablation` | `0` | `true` | 95 | 0 | 0 | 100.0% | 100.0% |
| `full_v10_ablation` | `full_dataset_ablation` | `0.001` | `true` | 95 | 0 | 0 | 100.0% | 100.0% |
| `full_v10_ablation` | `full_dataset_ablation` | `0.005` | `true` | 95 | 0 | 0 | 100.0% | 100.0% |
| `full_v10_ablation` | `full_dataset_ablation` | `0.01` | `true` | 95 | 0 | 0 | 100.0% | 100.0% |
| `full_v10_ablation` | `full_dataset_ablation` | `0.02` | `false` | 95 | 0 | 2 | 94.7% | 97.9% |
| `full_v10_ablation` | `full_dataset_ablation` | `0.05` | `false` | 95 | 0 | 4 | 89.5% | 95.8% |

## Blockers By Margin

| Margin | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| ---: | --- | ---: | ---: | --- | --- |
| `0` | `phrase_v2` | 1 | 0 | `en-es:source-phrase-heldout:v2:board:002` | `none` |
| `0.001` | `phrase_v2` | 1 | 0 | `en-es:source-phrase-heldout:v2:board:002` | `none` |
| `0.02` | `active_shadow_v2` | 0 | 2 | `none` | `en-es:source-heldout:v2:bank:001, en-es:source-heldout:v2:seal:001` |
| `0.02` | `full_v10_ablation` | 0 | 2 | `none` | `en-es:sentence-veto:ball:002, en-es:sentence-veto:table:001` |
| `0.05` | `active_shadow_v2` | 0 | 2 | `none` | `en-es:source-heldout:v2:bank:001, en-es:source-heldout:v2:seal:001` |
| `0.05` | `full_v10_ablation` | 0 | 4 | `none` | `en-es:sentence-veto:ball:002, en-es:sentence-veto:plant:002, en-es:sentence-veto:file:002, en-es:sentence-veto:table:001` |

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `margin_candidate_requires_non_v10_stress_before_runtime_default`
- `does_not_replace_phrase_source_or_pattern_provenance`
