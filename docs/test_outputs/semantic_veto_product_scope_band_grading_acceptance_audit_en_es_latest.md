# en-es Semantic Veto Product-Scope Band Grading Acceptance Audit

- Status: `ok`
- Decision: `accept_band_grading_v1_for_next_research_stage`
- Generated: `2026-05-09T19:59:14Z`
- Candidate scorer/config: `safest_80pct_positive_sentence_transformer_a0000_m0015`
- Candidate formula: `sweep_linear_2169`

## Checks

| Check | Pass | Rationale |
| --- | --- | --- |
| `candidate_detail_available` | `true` | Candidate row has top-band detail rows with per-target normalized metrics. |
| `normalization_targets_all_positive` | `true` | High-need failure is higher than low-need failure under every normalization target. |
| `normalization_order_all_monotonic` | `true` | High, middle, and low bands are monotonic under every normalization target. |
| `sentence_transformer_configs_positive` | `true` | The candidate formula remains positive across sentence-transformer candidate configs. |
| `near_neighbor_family_available` | `true` | At least five near-neighbor formulas are within the configured grade threshold. |
| `candidate_beats_fixed_controls` | `true` | The candidate beats the best fixed single/hand-authored control on the same scorer config. |

## Normalization Sensitivity

| target | high | middle | low | high-low | order | measured | unmeasured |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_measured_case_mix | 17.6% | 6.2% | 1.6% | +16.1% | 1.0000 | 100.0% | 0.0% |
| base_product_prior | 27.4% | 10.4% | 2.6% | +24.8% | 1.0000 | 88.8% | 11.2% |
| global_test_case_mix | 23.5% | 8.8% | 2.2% | +21.3% | 1.0000 | 100.0% | 0.0% |
| high_no_winner_product_prior | 26.8% | 10.2% | 2.5% | +24.3% | 1.0000 | 79.7% | 20.3% |
| low_no_winner_product_prior | 29.3% | 11.2% | 2.8% | +26.5% | 1.0000 | 94.7% | 5.3% |

## Scorer Sensitivity

| scorer | backend | grade | SRS high-low | order | raw high-low |
| --- | --- | --- | --- | --- | --- |
| best_product_rank_sentence_transformer_a0000_mneg0025 | sentence_transformer | 0.0815 | +9.2% | 1.0000 | +8.7% |
| current_v3_like_sentence_transformer_a0000_m0000 | sentence_transformer | 0.1857 | +20.9% | 1.0000 | +14.6% |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sentence_transformer | 0.2202 | +24.8% | 1.0000 | +14.6% |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | tfidf | 0.0057 | +1.0% | 0.6667 | +44.0% |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | tfidf | 0.0000 | -6.2% | 0.3333 | +21.9% |

## Near-Neighbor Stability

- Near-neighbor threshold: `0.1982`
- Near-neighbor count: `17`
- Formula family counts: `{"sweep_linear": 17}`

| feature | mean | min | max | nonzero |
| --- | --- | --- | --- | --- |
| `polysemy_risk` | 0.1000 | 0.0000 | 0.2222 | 64.7% |
| `pos_shape_risk` | 0.2464 | 0.0000 | 0.5000 | 76.5% |
| `shadow_coverage_risk` | 0.2977 | 0.2222 | 0.3750 | 100.0% |
| `source_zipf_risk` | 0.2277 | 0.1111 | 0.3333 | 100.0% |
| `target_zipf_risk` | 0.1281 | 0.0000 | 0.3333 | 70.6% |

## Fixed Controls

- Candidate beats best fixed control: `true`

| formula | grade | SRS high-low | order | raw high-low |
| --- | --- | --- | --- | --- |
| `pos_shape_only` | 0.1766 | +19.9% | 1.0000 | +13.1% |
| `linear_equal` | 0.1430 | +16.1% | 1.0000 | +8.4% |
| `linear_polysemy_shadow` | 0.1174 | +15.9% | 1.0000 | +9.2% |
| `shadow_coverage_only` | 0.1016 | +20.6% | 0.6667 | +11.9% |
| `polysemy_only` | 0.0390 | +6.6% | 0.6667 | +1.4% |
| `max_signal` | 0.0230 | +3.9% | 0.6667 | +1.9% |
| `target_zipf_only` | 0.0211 | +3.6% | 0.6667 | -0.4% |
| `source_polysemy_interaction` | 0.0134 | +2.3% | 0.6667 | +0.0% |
| `linear_source_polysemy` | 0.0016 | +0.3% | 0.6667 | -1.4% |
| `source_zipf_only` | 0.0000 | -4.0% | 0.3333 | -2.5% |

## Limitations

- `acceptance_is_for_next_research_stage_not_runtime_policy`
- `tfidf_backend_does_not_consistently_support_the_same_candidate_formula`
- `phrase_no_winner_mass_remains_visible_but_unmeasured_in_the_product_scope_surface`
- `the_49_family_denominator_is_still_small`

## Next Steps

- Freeze this as product_scope_band_grading_v1 for the next LLM follow-through batch.
- Select high/middle/low batches from the v1 heuristic and include low-band controls.
- After generation and admission, rerun band grading and this acceptance audit to falsify the heuristic.
