# en-es Semantic Source Margin Policy Sweep

- Status: `ok`
- Decision: `margin_candidate_found`
- Generated: `2026-04-27T22:45:07Z`
- Base dataset: `en_es_source_non_v10_wave2_admission_selected_v1`
- Evidence batch: `en-es:wordnet-def-ex-non-v10-wave2-selected-v1:source-admission-cycle:sense-admitted`
- Recommended min margin: `0`
- Passing margins: `0, 0.001, 0.005, 0.01, 0.02, 0.05`

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
| `non_v10_wave2_selected_active` | `heldout` | `0` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_active` | `heldout` | `0.001` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_active` | `heldout` | `0.005` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_active` | `heldout` | `0.01` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_active` | `heldout` | `0.02` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_active` | `heldout` | `0.05` | `true` | 16 | 0 | 0 | 100.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0.001` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0.005` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0.01` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0.02` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |
| `non_v10_wave2_selected_phrase` | `heldout` | `0.05` | `true` | 8 | 0 | 0 | 0.0% | 100.0% |

## Blockers By Margin

No blockers.

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `margin_candidate_requires_non_v10_stress_before_runtime_default`
- `does_not_replace_phrase_source_or_pattern_provenance`
