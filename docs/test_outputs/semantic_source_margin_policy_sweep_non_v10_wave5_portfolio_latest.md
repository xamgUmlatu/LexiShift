# en-es Semantic Source Margin Policy Sweep

- Status: `review`
- Decision: `margin_review`
- Generated: `2026-04-28T23:34:51Z`
- Base dataset: `en_es_source_non_v10_wave5_anypos_ranked_slate_selected_v1`
- Evidence batch: `en-es:wordnet-source-portfolio:non-v10-wave5-anypos-v1:cycle:sense-admitted`
- Recommended min margin: `none`
- Passing margins: `none`

## Configured Lane

- source_mode: `promotion_candidate_composite`
- scorer_id: `sentence_transformer_cosine`
- context_view: `masked_sentence`
- min_active_score: `0.0`
- decision_shape: `active_shadow_containment_surface_pos`

## Recommendation

- Decision: `review`
- Reason: `no_margin_passed`
- Next step: diagnose phrase challenge misses and test phrase-source or pattern policy before promoting any margin

## Rows

| Suite | Type | Margin | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `wave5_active` | `heldout` | `0` | `false` | 32 | 1 | 0 | 100.0% | 96.9% |
| `wave5_active` | `heldout` | `0.001` | `false` | 32 | 1 | 0 | 100.0% | 96.9% |
| `wave5_active` | `heldout` | `0.005` | `false` | 32 | 1 | 0 | 100.0% | 96.9% |
| `wave5_active` | `heldout` | `0.01` | `false` | 32 | 1 | 0 | 100.0% | 96.9% |
| `wave5_active` | `heldout` | `0.02` | `false` | 32 | 1 | 0 | 100.0% | 96.9% |
| `wave5_active` | `heldout` | `0.05` | `false` | 32 | 1 | 1 | 93.8% | 93.8% |
| `wave5_active` | `heldout` | `0.08` | `false` | 32 | 0 | 1 | 93.8% | 96.9% |
| `wave5_active` | `heldout` | `0.1` | `false` | 32 | 0 | 1 | 93.8% | 96.9% |
| `wave5_phrase` | `heldout` | `0` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.001` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.005` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.01` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.02` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.05` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.08` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |
| `wave5_phrase` | `heldout` | `0.1` | `false` | 16 | 1 | 0 | 0.0% | 93.8% |

## Blockers By Margin

| Margin | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| ---: | --- | ---: | ---: | --- | --- |
| `0` | `wave5_active` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `none` |
| `0` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.001` | `wave5_active` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `none` |
| `0.001` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.005` | `wave5_active` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `none` |
| `0.005` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.01` | `wave5_active` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `none` |
| `0.01` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.02` | `wave5_active` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `none` |
| `0.02` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.05` | `wave5_active` | 1 | 1 | `en-es:source-non-v10-wave5-portfolio-heldout:v1:present:002` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |
| `0.05` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.08` | `wave5_active` | 0 | 1 | `none` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |
| `0.08` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |
| `0.1` | `wave5_active` | 0 | 1 | `none` | `en-es:source-non-v10-wave5-portfolio-heldout:v1:rest:001` |
| `0.1` | `wave5_phrase` | 1 | 0 | `en-es:source-non-v10-wave5-portfolio-phrase:v1:end:001` | `none` |

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `no_scalar_margin_policy_passed_current_suites`
- `does_not_replace_phrase_source_or_pattern_provenance`
