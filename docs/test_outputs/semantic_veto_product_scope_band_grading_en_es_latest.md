# en-es Semantic Veto Product-Scope Band Grading

- Status: `ok`
- Decision: `product_scope_band_grading_established`
- Generated: `2026-05-09T19:33:42Z`
- Formula scopes: `15670`
- Score-surface rows: `700`

## Methodology

Evaluate each family-level heuristic by the actual low/middle/high bands it creates, then compare raw band success to success normalized against explicit case-type target mixes.

If a target case type has no cases in a band, the strict normalized score is null and the missing target weight is reported. The measured-only score renormalizes over observed target mass so we do not pretend to have no-winner evidence when the product-scope suite lacks it.

## Normalization Targets

| target | positive | shadow | phrase/no-winner | source |
| --- | --- | --- | --- | --- |
| global_test_case_mix | 70.0% | 30.0% | 0.0% | score_surface_row_results |
| balanced_measured_case_mix | 50.0% | 50.0% | n/a | score_surface_row_results |
| low_no_winner_product_prior | 85.0% | 9.7% | 5.3% | srs_case_mix_prior |
| base_product_prior | 73.8% | 15.0% | 11.2% | srs_case_mix_prior |
| high_no_winner_product_prior | 64.7% | 15.0% | 20.3% | srs_case_mix_prior |

## Best By Primary Band Grade

| scorer | formula | raw high-low | SRS high-low | order | measured min | unmeasured max | grade | bands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2169 | +14.6% | +24.8% | 1.0000 | 88.8% | 11.2% | 0.2202 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1268 | +14.7% | +24.6% | 1.0000 | 88.8% | 11.2% | 0.2187 | {"high_need": 17, "low_need": 15, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1293 | +14.7% | +24.6% | 1.0000 | 88.8% | 11.2% | 0.2187 | {"high_need": 17, "low_need": 15, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2074 | +14.4% | +23.9% | 1.0000 | 88.8% | 11.2% | 0.2125 | {"high_need": 16, "low_need": 16, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0751 | +14.5% | +23.0% | 1.0000 | 88.8% | 11.2% | 0.2041 | {"high_need": 18, "low_need": 14, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1502 | +14.5% | +23.0% | 1.0000 | 88.8% | 11.2% | 0.2041 | {"high_need": 18, "low_need": 14, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2253 | +14.5% | +23.0% | 1.0000 | 88.8% | 11.2% | 0.2041 | {"high_need": 18, "low_need": 14, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_3004 | +14.5% | +23.0% | 1.0000 | 88.8% | 11.2% | 0.2041 | {"high_need": 18, "low_need": 14, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0772 | +16.4% | +27.5% | 1.0000 | 73.8% | 26.2% | 0.2032 | {"high_need": 15, "low_need": 17, "middle_need": 17} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0667 | +13.9% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1989 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0697 | +13.9% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1989 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1323 | +13.9% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1989 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1448 | +13.9% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1989 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2073 | +13.9% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1989 | {"high_need": 17, "low_need": 16, "middle_need": 16} |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1443 | +13.4% | +22.4% | 1.0000 | 88.8% | 11.2% | 0.1986 | {"high_need": 17, "low_need": 16, "middle_need": 16} |

## Representative Comparison

| scorer | formula | raw high-low | SRS high-low | order | measured min | unmeasured max | grade | bands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | shadow_coverage_only | +11.9% | +20.6% | 0.6667 | 73.8% | 26.2% | 0.1016 | {"high_need": 19, "low_need": 26, "middle_need": 4} |
| current_v3_like_sentence_transformer_a0000_m0000 | shadow_coverage_only | +11.9% | +17.2% | 0.6667 | 73.8% | 26.2% | 0.0845 | {"high_need": 19, "low_need": 26, "middle_need": 4} |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | shadow_coverage_only | +44.7% | +16.9% | 0.6667 | 73.8% | 26.2% | 0.0830 | {"high_need": 19, "low_need": 26, "middle_need": 4} |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | shadow_coverage_only | +23.8% | +9.0% | 0.6667 | 73.8% | 26.2% | 0.0441 | {"high_need": 19, "low_need": 26, "middle_need": 4} |
| best_product_rank_sentence_transformer_a0000_mneg0025 | shadow_coverage_only | +6.7% | +6.7% | 0.6667 | 73.8% | 26.2% | 0.0329 | {"high_need": 19, "low_need": 26, "middle_need": 4} |

## Top Band Details

| scorer | formula | band | families | cases | raw failure | SRS measured failure | SRS unmeasured | case-type counts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2169 | high_need | 17 | 68 | 17.6% | 27.4% | 11.2% | positive_active:34, shadow_negative:34, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2169 | middle_need | 16 | 39 | 10.3% | 10.4% | 11.2% | positive_active:32, shadow_negative:7, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2169 | low_need | 16 | 33 | 3.0% | 2.6% | 11.2% | positive_active:32, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1268 | high_need | 17 | 67 | 17.9% | 27.4% | 11.2% | positive_active:34, shadow_negative:33, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1268 | middle_need | 17 | 42 | 9.5% | 9.8% | 11.2% | positive_active:34, shadow_negative:8, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1268 | low_need | 15 | 31 | 3.2% | 2.8% | 11.2% | positive_active:30, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1293 | high_need | 17 | 67 | 17.9% | 27.4% | 11.2% | positive_active:34, shadow_negative:33, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1293 | middle_need | 17 | 42 | 9.5% | 9.8% | 11.2% | positive_active:34, shadow_negative:8, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1293 | low_need | 15 | 31 | 3.2% | 2.8% | 11.2% | positive_active:30, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2074 | high_need | 16 | 63 | 17.5% | 26.5% | 11.2% | positive_active:32, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2074 | middle_need | 17 | 44 | 11.4% | 12.2% | 11.2% | positive_active:34, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2074 | low_need | 16 | 33 | 3.0% | 2.6% | 11.2% | positive_active:32, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0751 | high_need | 18 | 67 | 17.9% | 25.9% | 11.2% | positive_active:36, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0751 | middle_need | 17 | 44 | 9.1% | 9.8% | 11.2% | positive_active:34, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0751 | low_need | 14 | 29 | 3.5% | 3.0% | 11.2% | positive_active:28, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1502 | high_need | 18 | 67 | 17.9% | 25.9% | 11.2% | positive_active:36, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1502 | middle_need | 17 | 44 | 9.1% | 9.8% | 11.2% | positive_active:34, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1502 | low_need | 14 | 29 | 3.5% | 3.0% | 11.2% | positive_active:28, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2253 | high_need | 18 | 67 | 17.9% | 25.9% | 11.2% | positive_active:36, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2253 | middle_need | 17 | 44 | 9.1% | 9.8% | 11.2% | positive_active:34, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_2253 | low_need | 14 | 29 | 3.5% | 3.0% | 11.2% | positive_active:28, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_3004 | high_need | 18 | 67 | 17.9% | 25.9% | 11.2% | positive_active:36, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_3004 | middle_need | 17 | 44 | 9.1% | 9.8% | 11.2% | positive_active:34, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_3004 | low_need | 14 | 29 | 3.5% | 3.0% | 11.2% | positive_active:28, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0772 | high_need | 15 | 57 | 19.3% | 30.5% | 11.2% | positive_active:30, shadow_negative:27, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0772 | middle_need | 17 | 49 | 10.2% | 10.9% | 11.2% | positive_active:34, shadow_negative:15, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0772 | low_need | 17 | 34 | 2.9% | 2.9% | 26.2% | positive_active:34, shadow_negative:0, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0667 | high_need | 17 | 65 | 16.9% | 25.0% | 11.2% | positive_active:34, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0667 | middle_need | 16 | 42 | 11.9% | 13.0% | 11.2% | positive_active:32, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0667 | low_need | 16 | 33 | 3.0% | 2.6% | 11.2% | positive_active:32, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0697 | high_need | 17 | 65 | 16.9% | 25.0% | 11.2% | positive_active:34, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0697 | middle_need | 16 | 42 | 11.9% | 13.0% | 11.2% | positive_active:32, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_0697 | low_need | 16 | 33 | 3.0% | 2.6% | 11.2% | positive_active:32, shadow_negative:1, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1323 | high_need | 17 | 65 | 16.9% | 25.0% | 11.2% | positive_active:34, shadow_negative:31, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1323 | middle_need | 16 | 42 | 11.9% | 13.0% | 11.2% | positive_active:32, shadow_negative:10, phrase_no_winner:0 |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | sweep_linear_1323 | low_need | 16 | 33 | 3.0% | 2.6% | 11.2% | positive_active:32, shadow_negative:1, phrase_no_winner:0 |

## Limitations

- `product_scope_surface_currently_has_no_phrase_no_winner_rows_so_srs_prior_normalization_is_measured_only_for_that_mass`
- `srs_case_mix_priors_are_static_estimates_not_observed_browser_sentence_labels`
- `49_repaired_families_are_still_small_for_formula_selection`
- `band_grade_is_for_llm_data_allocation_research_not_runtime_policy_promotion`

## Next Steps

- Use the band grade to choose a small LLM follow-through batch plus low-band controls.
- Add or restore product-relevant phrase/no-winner rows before making full SRS-normalized claims.
- Re-run this report after any new LLM evidence admission so the allocation heuristic can be falsified.
