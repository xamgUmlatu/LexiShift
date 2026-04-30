# en-es Semantic Source Margin Policy Sweep

- Status: `review`
- Decision: `margin_review`
- Generated: `2026-04-29T03:55:59Z`
- Base dataset: `en_es_source_non_v10_wave6_anypos_unsupported_upper_bound_selected_v1`
- Evidence batch: `en-es:wordnet-translation-plus-alt-phrase:non-v10-wave6-wiktextract-supported-v1:cycle:sense-admitted`
- Recommended min margin: `none`
- Recommended phrase margin: `none`
- Passing policies: `none`

## Configured Lane

- source_mode: `promotion_candidate_composite`
- scorer_id: `sentence_transformer_cosine`
- context_view: `raw_sentence`
- min_active_score: `0.0`
- decision_shape: `active_shadow_phrase_semantic_surface_pos`

## Recommendation

- Decision: `review`
- Reason: `no_policy_passed`
- Next step: diagnose phrase challenge misses and test phrase-source or pattern policy before promoting any margin

## Rows

| Suite | Type | Margin | Phrase Margin | Pass | Cases | Harmful | False Abstain | Recall | Accuracy |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `active_shadow_wave6` | `heldout` | `0` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0` | `0.02` | `false` | 38 | 0 | 1 | 93.8% | 97.4% |
| `active_shadow_wave6` | `heldout` | `0` | `0.05` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0` | `0.075` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0` | `0.1` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0` | `0.15` | `false` | 38 | 2 | 1 | 93.8% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0` | `0.2` | `false` | 38 | 2 | 1 | 93.8% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.02` | `false` | 38 | 0 | 1 | 93.8% | 97.4% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.05` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.075` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.1` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.15` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.01` | `0.2` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.02` | `false` | 38 | 0 | 1 | 93.8% | 97.4% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.05` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.075` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.1` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.15` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.02` | `0.2` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.02` | `false` | 38 | 0 | 1 | 93.8% | 97.4% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.05` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.075` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.1` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.15` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.03` | `0.2` | `false` | 38 | 1 | 1 | 93.8% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.02` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.05` | `false` | 38 | 1 | 2 | 87.5% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.075` | `false` | 38 | 1 | 2 | 87.5% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.1` | `false` | 38 | 1 | 2 | 87.5% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.15` | `false` | 38 | 1 | 2 | 87.5% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.04` | `0.2` | `false` | 38 | 1 | 2 | 87.5% | 92.1% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.02` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.05` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.075` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.1` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.15` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `active_shadow_wave6` | `heldout` | `0.05` | `0.2` | `false` | 38 | 0 | 2 | 87.5% | 94.7% |
| `phrase_wave6` | `heldout` | `0` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.01` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.02` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.03` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.04` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.02` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.05` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.075` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.1` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.15` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |
| `phrase_wave6` | `heldout` | `0.05` | `0.2` | `false` | 16 | 2 | 0 | 0.0% | 87.5% |

## Blockers By Margin

| Policy | Suite | Harmful | False Abstain | Harmful Cases | False Abstain Cases |
| --- | --- | ---: | ---: | --- | --- |
| `m=0;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.02` | `active_shadow_wave6` | 0 | 1 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.05` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.075` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.1` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.15` | `active_shadow_wave6` | 2 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0;phrase=0.2` | `active_shadow_wave6` | 2 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:002, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.01;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.02` | `active_shadow_wave6` | 0 | 1 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.05` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.075` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.1` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.15` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.01;phrase=0.2` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.01;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.02;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.02` | `active_shadow_wave6` | 0 | 1 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.05` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.075` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.1` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.15` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.02;phrase=0.2` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.02;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.03;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.02` | `active_shadow_wave6` | 0 | 1 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.05` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.075` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.1` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.15` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.03;phrase=0.2` | `active_shadow_wave6` | 1 | 1 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001` |
| `m=0.03;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.02` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.05` | `active_shadow_wave6` | 1 | 2 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.075` | `active_shadow_wave6` | 1 | 2 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.1` | `active_shadow_wave6` | 1 | 2 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.15` | `active_shadow_wave6` | 1 | 2 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.04;phrase=0.2` | `active_shadow_wave6` | 1 | 2 | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:piece:002` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.04;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.02` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.02` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.05` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.05` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.075` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.075` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.1` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.1` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.15` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.15` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |
| `m=0.05;phrase=0.2` | `active_shadow_wave6` | 0 | 2 | `none` | `en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:leave:001, en-es:source-non-v10-wave6-wiktextract-supported-heldout:v1:black:001` |
| `m=0.05;phrase=0.2` | `phrase_wave6` | 2 | 0 | `en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:low:001, en-es:source-non-v10-wave6-wiktextract-supported-phrase:v1:bear:001` | `none` |

## Limitations

- `bounded_current_suite_not_full_en_es_proof`
- `no_scalar_margin_policy_passed_current_suites`
- `does_not_replace_phrase_source_or_pattern_provenance`
