# en-es Semantic Veto Repaired-Full Band Formula Sweep

- Status: `ok`
- Decision: `repaired_full_band_formula_sweep_established`
- Generated: `2026-05-09T19:32:30Z`
- Families: `49`
- Observations: `245`
- Fixed formulas: `10`
- Sweep formulas: `3124`
- Split counts: `{"discovery_proxy": 175, "locked_eval_proxy": 70}`

## Methodology

Compare programmatic family-level heuristics for ranking the source-target families most likely to benefit from LLM-generated semantic evidence.

Formula inputs are family-level signals that can be computed before seeing the test outcomes. Gold labels and predicted outcomes are used only for evaluation.

## Best Formula By Scope

| scope | formula | family | scorer | discovery rho | locked rho | top-k lift | brier | top triggers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_formulas::best_product_rank_sentence_transformer_a0000_mneg0025 | shadow_coverage_only | fixed_single_signal | best_product_rank_sentence_transformer_a0000_mneg0025 | 0.4093 | 0.0000 | 2.5057 | 0.2931 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| fixed_formulas::best_product_rank_sentence_transformer_a0000_mneg0025 | shadow_coverage_only | fixed_single_signal | best_product_rank_sentence_transformer_a0000_mneg0025 | 0.4093 | 0.0000 | 2.5057 | 0.2931 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::current_v3_like_sentence_transformer_a0000_m0000 | shadow_coverage_only | fixed_single_signal | current_v3_like_sentence_transformer_a0000_m0000 | 0.5579 | 0.0000 | 2.4500 | 0.2691 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| fixed_formulas::current_v3_like_sentence_transformer_a0000_m0000 | shadow_coverage_only | fixed_single_signal | current_v3_like_sentence_transformer_a0000_m0000 | 0.5579 | 0.0000 | 2.4500 | 0.2691 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::high_recall_soft_assist_tfidf_a0000_mneg0050 | shadow_coverage_only | fixed_single_signal | high_recall_soft_assist_tfidf_a0000_mneg0050 | 0.9697 | 0.8269 | 2.3358 | 0.1279 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| fixed_formulas::high_recall_soft_assist_tfidf_a0000_mneg0050 | shadow_coverage_only | fixed_single_signal | high_recall_soft_assist_tfidf_a0000_mneg0050 | 0.9697 | 0.8269 | 2.3358 | 0.1279 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::safest_80pct_positive_sentence_transformer_a0000_m0015 | shadow_coverage_only | fixed_single_signal | safest_80pct_positive_sentence_transformer_a0000_m0015 | 0.6197 | -0.0258 | 2.4500 | 0.2666 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| fixed_formulas::safest_80pct_positive_sentence_transformer_a0000_m0015 | shadow_coverage_only | fixed_single_signal | safest_80pct_positive_sentence_transformer_a0000_m0015 | 0.6197 | -0.0258 | 2.4500 | 0.2666 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| all_formulas::tfidf_best_by_scorer_tfidf_a0000_mneg0005 | shadow_coverage_only | fixed_single_signal | tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 0.7082 | 0.2188 | 2.2273 | 0.2092 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |
| fixed_formulas::tfidf_best_by_scorer_tfidf_a0000_mneg0005 | shadow_coverage_only | fixed_single_signal | tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 0.7082 | 0.2188 | 2.2273 | 0.2092 | acceptable->razonable, bar->cercar, billow->oleaje, break->quebrar, bridle->reprimir |

## Top Need Rows

| scorer | rank | trigger | target | need | observed failure | cases | formula |
| --- | --- | --- | --- | --- | --- | --- | --- |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 1 | acceptable | razonable | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 2 | bar | cercar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 3 | billow | oleaje | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 4 | break | quebrar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 5 | bridle | reprimir | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 6 | cite | mencionar | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 7 | continue | durar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| best_product_rank_sentence_transformer_a0000_mneg0025 | 8 | control | gobernar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 1 | acceptable | razonable | 0.8500 | 75.0% | 3 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 2 | bar | cercar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 3 | billow | oleaje | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 4 | break | quebrar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 5 | bridle | reprimir | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 6 | cite | mencionar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 7 | continue | durar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| current_v3_like_sentence_transformer_a0000_m0000 | 8 | control | gobernar | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 1 | acceptable | razonable | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 2 | bar | cercar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 3 | billow | oleaje | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 4 | break | quebrar | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 5 | bridle | reprimir | 0.8500 | 75.0% | 3 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 6 | cite | mencionar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 7 | continue | durar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| high_recall_soft_assist_tfidf_a0000_mneg0050 | 8 | control | gobernar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 1 | acceptable | razonable | 0.8500 | 75.0% | 3 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 2 | bar | cercar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 3 | billow | oleaje | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 4 | break | quebrar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 5 | bridle | reprimir | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 6 | cite | mencionar | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 7 | continue | durar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| safest_80pct_positive_sentence_transformer_a0000_m0015 | 8 | control | gobernar | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 1 | acceptable | razonable | 0.8500 | 25.0% | 1 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 2 | bar | cercar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 3 | billow | oleaje | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 4 | break | quebrar | 0.8500 | 0.0% | 0 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 5 | bridle | reprimir | 0.8500 | 75.0% | 3 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 6 | cite | mencionar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 7 | continue | durar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |
| tfidf_best_by_scorer_tfidf_a0000_mneg0005 | 8 | control | gobernar | 0.8500 | 50.0% | 2 / 4 | sweep_linear_0001_selected |

## Formula Definitions

| Formula family | Description |
| --- | --- |
| `fixed_single_signal` | One feature at a time: source band, target band, polysemy, POS shape, or shadow coverage. |
| `fixed_linear` | Hand-authored additive formulas to compare intuitive compositions. |
| `fixed_max` | Risk is the largest single warning signal. |
| `fixed_interaction` | Additive formula with a source-frequency by polysemy product term. |
| `sweep_linear` | Discrete normalized weight sweep across the five family-level signals. |

## Limitations

- `only_49_user_approved_repaired_families_so_correlation_is_still_fragile`
- `zipf_values_are_bands_not_exact_frequency_ranks_in_this_lane`
- `internal_locked_eval_proxy_is_not_a_future_heldout_set`
- `shadow_coverage_is_available_for_this_dataset_but_needs_full_inventory_equivalent`
- `ranking_quality_must_be_rechecked_after_llm_evidence_generation`

## Next Steps

- Use the best stable formula family to choose a small top-N LLM evidence pilot.
- Include low-ranked controls in that pilot so the ranking can be falsified.
- Do not tune runtime thresholds from this report alone.
