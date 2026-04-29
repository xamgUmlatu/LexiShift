# en-es Semantic Source Margin Policy Sweep

- Status: `ok`
- Decision: `margin_candidate_found`
- Generated: `2026-04-29T00:13:38Z`
- Base dataset: `en_es_source_non_v10_wave5_anypos_ranked_slate_selected_v1`
- Evidence batch: `en-es:wordnet-source-portfolio:non-v10-wave5-phrase-probe-cycle:sense-admitted`
- Recommended min margin: `0`
- Passing margins: `0, 0.001, 0.005, 0.01, 0.02`

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
| `wave5_active` | `heldout` | `0` | `true` | 32 | 0 | 0 | 100.0% | 100.0% |
| `wave5_active` | `heldout` | `0.001` | `true` | 32 | 0 | 0 | 100.0% | 100.0% |
| `wave5_active` | `heldout` | `0.005` | `true` | 32 | 0 | 0 | 100.0% | 100.0% |
| `wave5_active` | `heldout` | `0.01` | `true` | 32 | 0 | 0 | 100.0% | 100.0% |
| `wave5_active` | `heldout` | `0.02` | `true` | 32 | 0 | 0 | 100.0% | 100.0% |
| `wave5_active` | `heldout` | `0.05` | `false` | 32 | 0 | 1 | 94.1% | 96.9% |
| `wave5_active` | `heldout` | `0.08` | `false` | 32 | 0 | 2 | 88.2% | 93.8% |
| `wave5_active` | `heldout` | `0.1` | `false` | 32 | 0 | 2 | 88.2% | 93.8% |
| `wave5_phrase` | `heldout` | `0` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.001` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.005` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.01` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.02` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.05` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.08` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |
| `wave5_phrase` | `heldout` | `0.1` | `true` | 16 | 0 | 0 | 0.0% | 100.0% |

## Blockers By Margin

| Margin | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| ---: | --- | ---: | ---: | --- | --- |
| `0.05` | `wave5_active` | 0 | 1 | `none` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |
| `0.08` | `wave5_active` | 0 | 2 | `none` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002, en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |
| `0.1` | `wave5_active` | 0 | 2 | `none` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002, en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `margin_candidate_requires_non_v10_stress_before_runtime_default`
- `does_not_replace_phrase_source_or_pattern_provenance`
