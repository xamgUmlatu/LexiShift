# en-es Semantic Source Margin Policy Sweep

- Status: `review`
- Decision: `margin_review`
- Generated: `2026-04-29T01:48:33Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Evidence batch: `en-es:wordnet-def-ex-non-v10-wave6-wiktextract-supported:source-admission-cycle-latest:sense-admitted`
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
| `wave6_active` | `heldout` | `0` | `false` | 38 | 2 | 1 | 93.8% | 92.1% |
| `wave6_active` | `heldout` | `0.001` | `false` | 38 | 2 | 1 | 93.8% | 92.1% |
| `wave6_active` | `heldout` | `0.005` | `false` | 38 | 2 | 1 | 93.8% | 92.1% |
| `wave6_active` | `heldout` | `0.01` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `wave6_active` | `heldout` | `0.02` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `wave6_active` | `heldout` | `0.05` | `false` | 38 | 1 | 3 | 81.2% | 89.5% |
| `wave6_phrase` | `heldout` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `wave6_phrase` | `heldout` | `0.001` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `wave6_phrase` | `heldout` | `0.005` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `wave6_phrase` | `heldout` | `0.01` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `wave6_phrase` | `heldout` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `wave6_phrase` | `heldout` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |

## Blockers By Margin

| Margin | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| ---: | --- | ---: | ---: | --- | --- |
| `0` | `wave6_active` | 2 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `0` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |
| `0.001` | `wave6_active` | 2 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `0.001` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |
| `0.005` | `wave6_active` | 2 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `0.005` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |
| `0.01` | `wave6_active` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `0.01` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |
| `0.02` | `wave6_active` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `0.02` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |
| `0.05` | `wave6_active` | 1 | 3 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:low:001` |
| `0.05` | `wave6_phrase` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:fair:001` | `none` |

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `no_scalar_margin_policy_passed_current_suites`
- `does_not_replace_phrase_source_or_pattern_provenance`
