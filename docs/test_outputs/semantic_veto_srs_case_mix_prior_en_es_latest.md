# en-es Semantic Veto SRS Case-Mix Prior

- Status: `ok`
- Decision: `srs_case_mix_prior_established`
- Generated: `2026-05-07T20:24:42Z`
- Source-target pairs: `570`
- Unique sources: `536`
- WordNet-profile known pairs: `540`

## Methodology

Estimate real-SRS active/shadow/no-winner proportions by source band from programmatic static features, then multiply those proportions by approved repaired-full conditional veto performance.

The report does not claim to know true browser sentence labels. It estimates case-type priors from static SRS source-target metadata, then applies those priors to the approved repaired-full conditional veto rates.

## Base Prior By Source Band

| source band | pairs | SRS share | active prior | shadow prior | no-winner prior | shadow risk | no-winner risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| zipf_5_plus_very_common | 109 | 19.1% | 65.1% | 19.6% | 15.3% | 38.7% | 68.4% |
| zipf_4_to_5_common | 235 | 41.2% | 72.1% | 16.1% | 11.8% | 26.9% | 45.6% |
| zipf_3_to_4_mid | 152 | 26.7% | 79.4% | 11.7% | 8.8% | 12.4% | 25.7% |
| zipf_below_3_rare | 52 | 9.1% | 82.8% | 10.3% | 6.9% | 7.6% | 12.9% |
| missing | 22 | 3.9% | 75.5% | 14.8% | 9.7% | 22.7% | 31.2% |

## Base Weighted Success

| scorer | source band | estimated success | active rate | shadow rate | no-winner rate | SRS share |
| --- | --- | --- | --- | --- | --- | --- |
| sentence_transformer_cosine | zipf_5_plus_very_common | 77.3% | 90.6% | 83.3% | 12.5% | 19.1% |
| sentence_transformer_cosine | zipf_4_to_5_common | 85.2% | 90.9% | 88.9% | 45.5% | 41.2% |
| sentence_transformer_cosine | zipf_3_to_4_mid | 83.8% | 89.3% | 93.3% | 21.4% | 26.7% |
| sentence_transformer_cosine | zipf_below_3_rare | 75.8% | 75.0% | 100.0% | 50.0% | 9.1% |
| sentence_transformer_cosine | missing | 82.0% | 86.5% | 91.4% | 32.4% | 3.9% |
| tfidf_cosine | zipf_5_plus_very_common | 37.3% | 6.2% | 91.7% | 100.0% | 19.1% |
| tfidf_cosine | zipf_4_to_5_common | 31.2% | 4.5% | 100.0% | 100.0% | 41.2% |
| tfidf_cosine | zipf_3_to_4_mid | 26.2% | 7.1% | 100.0% | 100.0% | 26.7% |
| tfidf_cosine | zipf_below_3_rare | 17.2% | 0.0% | 100.0% | 100.0% | 9.1% |
| tfidf_cosine | missing | 27.6% | 4.5% | 97.9% | 100.0% | 3.9% |

## Scenario Comparison

| scenario | scorer | estimated overall SRS-weighted success |
| --- | --- | ---: |
| `low_no_winner_product_prior` | `sentence_transformer_cosine` | 85.7% |
| `low_no_winner_product_prior` | `tfidf_cosine` | 19.1% |
| `base_product_prior` | `sentence_transformer_cosine` | 82.3% |
| `base_product_prior` | `tfidf_cosine` | 29.6% |
| `high_no_winner_product_prior` | `sentence_transformer_cosine` | 77.1% |
| `high_no_winner_product_prior` | `tfidf_cosine` | 38.3% |

## Sensitivity Read

For sentence-transformer, estimated SRS-weighted success ranges from `77.1%` to `85.7%` across the no-winner prior scenarios. A wide range means no-winner exposure must be measured with real contexts before promotion claims.

## Limitations

- `case_type_proportions_are_static_priors_not_observed_browser_labels`
- `no_winner_rate_cannot_be_known_without_contexts`
- `source_target_pairs_are_current_rulegen_outputs_not_every_possible_runtime_trigger`
- `wordnet_polysemy_can_overstate_or_understate practical translation ambiguity`
- `weighted_success_uses_repaired_full_conditional_performance_not final locked eval`

## Next Steps

- Use this report to choose plausible product-mix priors before spending LLM budget.
- Add real or corpus-like SRS-trigger contexts to replace static priors with observed case-type rates.
- Track no-winner sensitivity separately because it dominates sentence-transformer product success.
