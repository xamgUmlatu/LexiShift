# en-es Semantic Veto Formula-Shape Bakeoff

- Status: `ok`
- Decision: `formula_shape_bakeoff_established`
- Generated: `2026-05-05T03:49:00Z`
- Cells: `48`
- Primary cells / sentinel cells: `42` / `6`
- Formula count: `9`

## Methodology

This report compares formula shapes for ranking cells that need more manual or LLM data. It does not change runtime policy. Sentinel cells are excluded from primary validation, and missing rank is represented as its own indicator instead of being silently imputed.

## Best Formula By Scope

| Formula | Scope | Cells | Spearman | Kendall | Brier | Top-k lift | Priority lift | Locked Spearman |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `rank_aggregation` | `all_including_sentinel::sentence_transformer_cosine` | 24 | 0.4310 | 0.3571 | 0.1737 | 1.0342 | 2.2407 | 0.1966 |
| `max_risk` | `all_including_sentinel::tfidf_cosine` | 24 | -0.1810 | -0.1399 | 0.3523 | 1.2264 | 1.4535 |  |
| `rank_aggregation` | `primary::sentence_transformer_cosine` | 21 | 0.3581 | 0.3016 | 0.1653 | 1.2800 | 1.9200 | 0.1595 |
| `max_risk` | `primary::tfidf_cosine` | 21 | -0.1692 | -0.1250 | 0.3496 | 1.1613 | 1.3763 |  |
| `sweep_gated_phrase_shadow_positive_weight_sweep_selected` | `primary_all_scorers` | 42 | 0.2599 | 0.1877 | 0.0915 | 1.5918 | 1.0286 | 0.2516 |

## Primary Formula Comparison

| Formula | Scope | Cells | Spearman | Kendall | Brier | Top-k lift | Priority lift | Locked Spearman |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `monotone_rule_table` | `primary_all_scorers` | 42 | 0.3056 | 0.2376 | 0.1787 | 1.2632 | 0.7347 | 0.2919 |
| `sweep_gated_phrase_shadow_positive_weight_sweep_selected` | `primary_all_scorers` | 42 | 0.2599 | 0.1877 | 0.0915 | 1.5918 | 1.0286 | 0.2516 |
| `sweep_linear_simplex_weight_sweep_selected` | `primary_all_scorers` | 42 | 0.2191 | 0.2174 | 0.1025 | 0.2857 | 0.7912 | 0.2650 |
| `linear_baseline` | `primary_all_scorers` | 42 | 0.1344 | 0.1048 | 0.1238 | 1.1429 | 0.7347 | 0.3252 |
| `rank_aggregation` | `primary_all_scorers` | 42 | 0.0986 | 0.0934 | 0.1874 | 0.6234 | 0.4034 | 0.1558 |
| `probabilistic_product` | `primary_all_scorers` | 42 | 0.0945 | 0.0554 | 0.1323 | 0.7792 | 0.7347 | 0.2025 |
| `normalized_dot_signal` | `primary_all_scorers` | 42 | 0.0843 | 0.0532 | 0.3269 | 0.9796 | 0.4571 | 0.1043 |
| `logistic_signal` | `primary_all_scorers` | 42 | 0.0759 | 0.0578 | 0.2337 | 0.3429 | 0.7347 | 0.2270 |
| `multiplicative_interaction` | `primary_all_scorers` | 42 | 0.0364 | 0.0259 | 0.1568 | 1.0159 | 0.7347 | 0.0429 |
| `max_risk` | `primary_all_scorers` | 42 | -0.0569 | -0.0291 | 0.3260 | 0.8571 | 0.3810 | -0.2598 |
| `gated_by_failure_class` | `primary_all_scorers` | 42 | -0.1462 | -0.1144 | 0.1815 | 0.5042 | 0.5275 | 0.2147 |

## Parameter Sweeps

| Sweep | Samples | Selected Formula | Discovery Spearman | Discovery Brier | Locked Spearman | Primary Spearman | Top weights |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `linear_simplex_weight_sweep` | 205 | `sweep_linear_simplex_weight_sweep_selected` | 0.2447 | 0.0929 | 0.2650 | 0.2191 | coverage_gap=1.00, active_low_rate=0.00, case_type_prior=0.00, fixability=0.00 |
| `gated_phrase_shadow_positive_weight_sweep` | 161 | `sweep_gated_phrase_shadow_positive_weight_sweep_selected` | 0.2921 | 0.0925 | 0.2516 | 0.2599 | shadow_negative.underfilled_rate=0.56, positive_active.active_low_rate=0.37, phrase_no_winner.rank_risk=0.30, phrase_no_winner.rank_missing_rate=0.28 |

## Negative Controls

| Control | Cells | Spearman | Brier | Top-k lift | Priority lift |
| --- | ---: | ---: | ---: | ---: | ---: |
| `random_seeded` | 42 | -0.0303 | 0.2038 | 0.3117 | 0.7218 |
| `source_rank_only` | 42 | 0.0602 | 0.1948 | 0.8571 | 0.3810 |
| `target_lemma_length` | 42 | 0.0068 | 0.1342 | 1.0714 | 0.6050 |
| `shuffled_observed_order` | 42 | 0.2039 | 0.1183 | 1.1429 | 0.7347 |

## Calibration

| Formula | Scorer | Bucket | Cells | Predicted | Observed | Abs error |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `gated_by_failure_class` | `sentence_transformer_cosine` | `low` | 2 | 0.2766 | 0.0556 | 0.2210 |
| `gated_by_failure_class` | `sentence_transformer_cosine` | `mid` | 17 | 0.5261 | 0.3987 | 0.1274 |
| `gated_by_failure_class` | `sentence_transformer_cosine` | `high` | 2 | 0.6936 | 0.2321 | 0.4615 |
| `gated_by_failure_class` | `tfidf_cosine` | `low` | 1 | 0.3286 | 0.2778 | 0.0508 |
| `gated_by_failure_class` | `tfidf_cosine` | `mid` | 11 | 0.5721 | 0.3865 | 0.1856 |
| `gated_by_failure_class` | `tfidf_cosine` | `high` | 9 | 0.7927 | 0.2806 | 0.5120 |
| `linear_baseline` | `sentence_transformer_cosine` | `low` | 1 | 0.2960 | 0.0556 | 0.2404 |
| `linear_baseline` | `sentence_transformer_cosine` | `mid` | 19 | 0.5268 | 0.3644 | 0.1625 |
| `linear_baseline` | `sentence_transformer_cosine` | `high` | 1 | 0.7119 | 0.3750 | 0.3369 |
| `linear_baseline` | `tfidf_cosine` | `low` | 1 | 0.3010 | 0.2778 | 0.0232 |
| `linear_baseline` | `tfidf_cosine` | `mid` | 18 | 0.5294 | 0.3557 | 0.1737 |
| `linear_baseline` | `tfidf_cosine` | `high` | 2 | 0.7049 | 0.1875 | 0.5174 |
| `logistic_signal` | `sentence_transformer_cosine` | `mid` | 9 | 0.5419 | 0.3067 | 0.2352 |
| `logistic_signal` | `sentence_transformer_cosine` | `high` | 12 | 0.7580 | 0.3827 | 0.3752 |
| `logistic_signal` | `tfidf_cosine` | `mid` | 3 | 0.5281 | 0.4630 | 0.0652 |
| `logistic_signal` | `tfidf_cosine` | `high` | 18 | 0.8018 | 0.3148 | 0.4871 |
| `max_risk` | `sentence_transformer_cosine` | `low` | 1 | 0.2625 | 0.0556 | 0.2069 |
| `max_risk` | `sentence_transformer_cosine` | `mid` | 11 | 0.6401 | 0.3693 | 0.2708 |
| `max_risk` | `sentence_transformer_cosine` | `high` | 9 | 0.9778 | 0.3595 | 0.6183 |
| `max_risk` | `tfidf_cosine` | `low` | 1 | 0.2625 | 0.2778 | 0.0153 |
| `max_risk` | `tfidf_cosine` | `mid` | 4 | 0.6395 | 0.5948 | 0.0448 |
| `max_risk` | `tfidf_cosine` | `high` | 16 | 0.9000 | 0.2749 | 0.6251 |
| `monotone_rule_table` | `sentence_transformer_cosine` | `low` | 2 | 0.2100 | 0.0556 | 0.1544 |
| `monotone_rule_table` | `sentence_transformer_cosine` | `mid` | 10 | 0.5380 | 0.3102 | 0.2278 |

## Top Data-Help Cells

| Formula | Cell | Type | Group | Scorer | Risk | Observed | Priority | Rows | Triggers |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `max_risk` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `phrase_no_winner` | `core_high_polysemy` | `tfidf_cosine` | 1.0000 | 0.2500 | 1.0000 | 1 | help |
| `max_risk` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `positive_active` | `core_high_polysemy` | `tfidf_cosine` | 1.0000 | 0.5000 | 0.7776 | 2 | help |
| `sweep_gated_phrase_shadow_positive_weight_sweep_selected` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=shadow_negative::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `shadow_negative` | `core_high_polysemy` | `tfidf_cosine` | 0.6972 | 0.1667 | 0.7122 | 2 | help |
| `sweep_linear_simplex_weight_sweep_selected` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9` | `phrase_no_winner` | `mid_high_polysemy` | `tfidf_cosine` | 0.6125 | 0.2500 | 0.6500 | 1 | particular |
| `normalized_dot_signal` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `phrase_no_winner` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.8994 | 0.2500 | 0.6279 | 1 | help |
| `normalized_dot_signal` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus` | `phrase_no_winner` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.9243 | 0.3750 | 0.5841 | 3 | call, man, work |
| `max_risk` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `positive_active` | `core_high_polysemy` | `sentence_transformer_cosine` | 1.0000 | 0.1667 | 0.5666 | 2 | help |
| `normalized_dot_signal` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus` | `phrase_no_winner` | `core_high_polysemy` | `tfidf_cosine` | 0.9243 | 0.1250 | 0.5591 | 3 | call, man, work |
| `sweep_linear_simplex_weight_sweep_selected` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9` | `phrase_no_winner` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.6125 | 0.7500 | 0.5461 | 1 | particular |
| `max_risk` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_low_polysemy_control::manual_case_type=phrase_no_winner::shadow_contract=not_applicable::source_rank_bin=1-500::polysemy_band=low_1_to_3` | `phrase_no_winner` | `core_low_polysemy_control` | `tfidf_cosine` | 1.0000 | 0.1000 | 0.5204 | 4 | money, often, percent, yes |
| `max_risk` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=shadow_negative::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus` | `shadow_negative` | `core_high_polysemy` | `sentence_transformer_cosine` | 1.0000 | 0.1667 | 0.4770 | 2 | help |
| `normalized_dot_signal` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus` | `positive_active` | `core_high_polysemy` | `tfidf_cosine` | 0.8837 | 0.7857 | 0.4239 | 6 | call, man, work |
| `normalized_dot_signal` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus` | `positive_active` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.8837 | 0.3571 | 0.3950 | 6 | call, man, work |
| `normalized_dot_signal` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=high_10_plus` | `phrase_no_winner` | `mid_high_polysemy` | `tfidf_cosine` | 0.8815 | 0.6250 | 0.3917 | 3 | deep, green, trade |
| `normalized_dot_signal` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=shadow_negative::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9` | `shadow_negative` | `mid_high_polysemy` | `tfidf_cosine` | 0.8300 | 0.1667 | 0.3697 | 2 | particular |
| `sweep_linear_simplex_weight_sweep_selected` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=positive_active::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9` | `positive_active` | `mid_high_polysemy` | `tfidf_cosine` | 0.5750 | 0.8333 | 0.3692 | 2 | particular |
| `normalized_dot_signal` | `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=positive_active::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9` | `positive_active` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.8354 | 0.1667 | 0.3485 | 2 | particular |
| `max_risk` | `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_low_polysemy_control::manual_case_type=positive_active::shadow_contract=not_applicable::source_rank_bin=1-500::polysemy_band=low_1_to_3` | `positive_active` | `core_low_polysemy_control` | `tfidf_cosine` | 1.0000 | 0.7222 | 0.3374 | 8 | money, often, percent, yes |

## Recommendations

- `P0` `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus`: add_phrase_no_winner_and_order_sensitive_mention_rows
- `P0` `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus`: review_active_evidence_then_add_positive_context_rows
- `P1` `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=shadow_negative::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus`: add_real_shadow_negative_rows_and_review_shadow_evidence
- `P1` `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=mid_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1001-2000::polysemy_band=medium_4_to_9`: add_phrase_no_winner_and_order_sensitive_mention_rows
- `P1` `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus`: add_phrase_no_winner_and_order_sensitive_mention_rows
- `P1` `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus`: add_phrase_no_winner_and_order_sensitive_mention_rows
- `P1` `scorer_id=sentence_transformer_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=positive_active::shadow_contract=limited::source_rank_bin=1-500::polysemy_band=high_10_plus`: review_active_evidence_then_add_positive_context_rows
- `P1` `scorer_id=tfidf_cosine::selection_mode=pre_outcome::heuristic_group=core_high_polysemy::manual_case_type=phrase_no_winner::shadow_contract=full::source_rank_bin=1-500::polysemy_band=high_10_plus`: add_phrase_no_winner_and_order_sensitive_mention_rows

## Limitations

- `internal_split_is_advisory_not_true_locked_eval`
- `agent_authored_heuristic_group_cases_need_human_review`
- `formula_parameters_are_hand_specified_defaults_not_trained_coefficients`
- `rank_aggregation_can_only_compare_formulas_available_in_this_manifest`
- `runtime_policy_remains_unchanged`

## Next Steps

- Inspect top data-help cells before generating more LLM rows.
- Promote no runtime behavior from this report alone.
- Use the top phrase/no-winner and underfilled cells as the next manual/LLM expansion queue.
- After expansion, rerun this report and compare discovery-versus-locked stability.
