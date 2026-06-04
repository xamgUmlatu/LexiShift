# en-es Semantic Veto Formula Weight Surface

- Status: `ok`
- Decision: `formula_weight_surface_established`
- Generated: `2026-05-05T05:27:06Z`
- Cells: `48`
- Primary cells: `42`
- Sweeps: `2`

## Sweep Maxima

| Sweep | Samples | Discovery rho | Locked rho | Primary rho | Top-k lift | Plateau | Discovery-locked gap | Shape |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `linear_simplex_weight_sweep` | 205 | 0.2447 | 0.2650 | 0.2191 | 1.0234 | 0.0098 | -0.0203 | `sharp_sampled_peak` |
| `gated_phrase_shadow_positive_weight_sweep` | 161 | 0.2921 | 0.2516 | 0.2599 | 1.4255 | 0.0124 | 0.0405 | `sharp_sampled_peak` |

## Feature Curves

| Sweep | Curve | Selected alpha | Best alpha | Best discovery rho | Best locked rho | Shape |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.underfilled_rate` | 0.1906 | 1.0000 | 0.4246 | 0.6646 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.near_tie_rate` | 0.2764 | 1.0000 | 0.4145 | 0.2638 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk` | 0.3046 | 1.0000 | 0.4097 | 0.5108 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate` | 0.3692 | 0.9000 | 0.3880 | 0.5461 | `interior_peak` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.active_low_rate` | 0.1344 | 0.0000 | 0.3810 | 0.4356 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.rank_missing_rate` | 0.2244 | 0.0000 | 0.3720 | 0.0798 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.rank_risk` | 0.2297 | 0.6000 | 0.3174 | -0.2147 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_missing_rate` | 0.2844 | 0.0000 | 0.3169 | 0.4111 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.sense_risk` | 0.0409 | 0.0000 | 0.3081 | 0.2516 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.active_low_rate` | 0.0577 | 0.0000 | 0.3066 | 0.2270 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.near_tie_rate` | 0.1212 | 0.0000 | 0.3005 | 0.2638 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.underfilled_rate` | 0.5604 | 0.2000 | 0.2950 | 0.3129 | `broad_plateau` |
| `linear_simplex_weight_sweep` | `near_tie_rate` | 0.0000 | 0.2000 | 0.2612 | -0.0677 | `broad_plateau` |
| `linear_simplex_weight_sweep` | `active_low_rate` | 0.0000 | 0.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `case_type_prior` | 0.0000 | 0.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `coverage_gap` | 1.0000 | 1.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `fixability` | 0.0000 | 0.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `phrase_surface_pattern_rate` | 0.0000 | 0.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `pos_risk` | 0.0000 | 0.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `rank_missing_rate` | 0.0000 | 0.2000 | 0.2447 | 0.2650 | `broad_plateau` |

## Pairwise Probes

| Sweep | Pair | Best left alpha | Best discovery rho | Best locked rho | Shape |
| --- | --- | ---: | ---: | ---: | --- |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_missing_rate_vs_underfilled_rate` | 0.2000 | 0.4524 | 0.6646 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk_vs_underfilled_rate` | 0.3000 | 0.4497 | 0.5583 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.underfilled_rate_vs_near_tie_rate` | 0.1000 | 0.4263 | 0.2638 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk_vs_rank_missing_rate` | 0.9000 | 0.4161 | 0.3754 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.near_tie_rate_vs_active_low_rate` | 1.0000 | 0.4145 | 0.2638 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate_vs_rank_risk` | 0.8000 | 0.3952 | 0.3333 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate_vs_rank_missing_rate` | 1.0000 | 0.3825 | 0.4811 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.underfilled_rate_vs_active_low_rate` | 1.0000 | 0.2760 | 0.2025 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `coverage_gap_vs_near_tie_rate` | 0.8000 | 0.2612 | -0.0677 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.rank_risk_vs_rank_missing_rate` | 1.0000 | 0.2507 | -0.4486 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `coverage_gap_vs_active_low_rate` | 1.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `coverage_gap_vs_case_type_prior` | 1.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `coverage_gap_vs_fixability` | 1.0000 | 0.2447 | 0.2650 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `case_type_prior_vs_fixability` | 0.4000 | 0.1709 | 0.5354 | `interior_peak` |
| `linear_simplex_weight_sweep` | `active_low_rate_vs_near_tie_rate` | 0.0000 | 0.1237 | -0.1411 | `edge_maximum` |
| `linear_simplex_weight_sweep` | `active_low_rate_vs_case_type_prior` | 0.2000 | 0.0843 | 0.5003 | `interior_peak` |
| `linear_simplex_weight_sweep` | `active_low_rate_vs_fixability` | 0.0000 | 0.0295 | 0.1539 | `edge_maximum` |

## Interpretation

- `linear_simplex_weight_sweep`: `sharp_sampled_peak`; discovery-locked gap `-0.0203`; plateau fraction `0.0098`.
- `gated_phrase_shadow_positive_weight_sweep`: `sharp_sampled_peak`; discovery-locked gap `0.0405`; plateau fraction `0.0124`.

## Limitations

- `surface_is_over_current_draft_heuristic_cells_not_representative_browsing`
- `internal_locked_eval_split_is_advisory`
- `one_dimensional_curves_hold_other_weights_at_selected_relative_shares`
- `sampled_maximum_is_not_a_proof_of_global_optimum`
- `runtime_policy_remains_unchanged`

## Next Steps

- Expand top high-uncertainty cells, then rerun surface analysis.
- Treat sharp or unstable maxima as curve-sensitivity signals; use them to choose expansion cells, not to lock coefficients.
- Prefer broad plateaus that survive internal locked-eval checks after expansion.
