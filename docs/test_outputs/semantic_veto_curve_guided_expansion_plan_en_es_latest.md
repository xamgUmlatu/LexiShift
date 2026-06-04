# en-es Semantic Veto Curve-Guided Expansion Plan

- Status: `ok`
- Decision: `curve_guided_expansion_plan_established`
- Generated: `2026-05-05T05:28:39Z`
- Primary cells: `42`
- Queued cells: `24`
- Sentinel cells excluded from queue: `6`

## Strongest Curve Signals

| Sweep | Curve | Gate | Features | Best discovery | Best locked | Shape |
| --- | --- | --- | --- | ---: | ---: | --- |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_missing_rate_vs_underfilled_rate` | `phrase_no_winner` | `rank_missing_rate, underfilled_rate` | 0.4524 | 0.6646 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk_vs_underfilled_rate` | `phrase_no_winner` | `rank_risk, underfilled_rate` | 0.4497 | 0.5583 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.underfilled_rate_vs_near_tie_rate` | `shadow_negative` | `underfilled_rate, near_tie_rate` | 0.4263 | 0.2638 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.underfilled_rate` | `phrase_no_winner` | `underfilled_rate` | 0.4246 | 0.6646 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk_vs_rank_missing_rate` | `phrase_no_winner` | `rank_risk, rank_missing_rate` | 0.4161 | 0.3754 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.near_tie_rate` | `shadow_negative` | `near_tie_rate` | 0.4145 | 0.2638 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `shadow_negative.near_tie_rate_vs_active_low_rate` | `shadow_negative` | `near_tie_rate, active_low_rate` | 0.4145 | 0.2638 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.rank_risk` | `phrase_no_winner` | `rank_risk` | 0.4097 | 0.5108 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate_vs_rank_risk` | `positive_active` | `active_low_rate, rank_risk` | 0.3952 | 0.3333 | `broad_plateau` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate` | `positive_active` | `active_low_rate` | 0.3880 | 0.5461 | `interior_peak` |
| `gated_phrase_shadow_positive_weight_sweep` | `positive_active.active_low_rate_vs_rank_missing_rate` | `positive_active` | `active_low_rate, rank_missing_rate` | 0.3825 | 0.4811 | `edge_maximum` |
| `gated_phrase_shadow_positive_weight_sweep` | `phrase_no_winner.active_low_rate` | `phrase_no_winner` | `active_low_rate` | 0.3810 | 0.4356 | `edge_maximum` |

## Expansion Queue

| Priority | Case type | Group | Scorer | Score | Reasons | Manual | LLM | Locked |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| `P0` | `phrase_no_winner` | `core_high_polysemy` | `tfidf_cosine` | 0.9087 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 4 | 16 | 8 |
| `P0` | `positive_active` | `core_high_polysemy` | `tfidf_cosine` | 0.7916 | high_uncertainty, positive_active_low_score, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `mid_high_polysemy` | `tfidf_cosine` | 0.7687 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.7599 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 4 | 16 | 8 |
| `P0` | `phrase_no_winner` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.7521 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 4 | 16 | 8 |
| `P1` | `shadow_negative` | `core_high_polysemy` | `tfidf_cosine` | 0.7353 | high_uncertainty, near_tie_shadow, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.7111 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `positive_active` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.6599 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `core_high_polysemy` | `tfidf_cosine` | 0.6547 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `mid_high_polysemy` | `tfidf_cosine` | 0.6466 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `shadow_negative` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.6412 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `positive_active` | `mid_high_polysemy` | `tfidf_cosine` | 0.6143 | high_uncertainty, positive_active_low_score, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `core_low_polysemy_control` | `tfidf_cosine` | 0.6111 | phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `shadow_negative` | `mid_high_polysemy` | `tfidf_cosine` | 0.5983 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.5916 | high_uncertainty, phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `positive_active` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.5726 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `shadow_negative` | `mid_high_polysemy` | `sentence_transformer_cosine` | 0.5670 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `core_low_polysemy_control` | `sentence_transformer_cosine` | 0.5660 | phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P1` | `positive_active` | `core_high_polysemy` | `tfidf_cosine` | 0.5589 | high_uncertainty, positive_active_low_score, strong_surface_curve_signal, top_shape_data_help_cell | 3 | 10 | 5 |
| `P1` | `positive_active` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.5399 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell | 3 | 10 | 5 |
| `P1` | `phrase_no_winner` | `mid_low_polysemy_control` | `tfidf_cosine` | 0.5205 | phrase_no_winner_priority, strong_surface_curve_signal, top_shape_data_help_cell, underfilled_cell | 3 | 10 | 5 |
| `P2` | `positive_active` | `core_low_polysemy_control` | `tfidf_cosine` | 0.4933 | high_uncertainty, positive_active_low_score, strong_surface_curve_signal, top_shape_data_help_cell | 2 | 6 | 3 |
| `P2` | `shadow_negative` | `core_high_polysemy` | `sentence_transformer_cosine` | 0.4926 | high_uncertainty, strong_surface_curve_signal, top_shape_data_help_cell | 2 | 6 | 3 |
| `P2` | `shadow_negative` | `core_high_polysemy` | `tfidf_cosine` | 0.4594 | near_tie_shadow, strong_surface_curve_signal, top_shape_data_help_cell | 2 | 6 | 3 |

## Case-Type Summary

| Case type | Cells | P0 cells | Manual | LLM | Locked | Mean score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `phrase_no_winner` | 11 | 4 | 37 | 134 | 67 | 0.6810 |
| `positive_active` | 7 | 1 | 21 | 72 | 36 | 0.6044 |
| `shadow_negative` | 6 | 0 | 16 | 52 | 26 | 0.5823 |

## Authoring Guidance

- `phrase_no_winner`: Write sentences where the source surface form appears, but the target replacement should not appear; include word-order, punctuation, short utterance, and idiom-like variants.
- `shadow_negative`: Write real alternate-sense contexts with a clearly better shadow meaning; avoid fake shadows that merely contain contrastive keywords.
- `positive_active`: Write natural contexts where the replacement is correct, especially cases where current active evidence is weak, short, or near the threshold.

## Methodology

- `objective`: Use observed formula-shape data-help priority plus weight-surface curve signals to choose cells that will reveal the shape of veto difficulty with the fewest manual and LLM rows.
- `selection_scope`: primary pre_outcome cells only
- `expansion_score_formula`: 0.40*shape_data_help_priority + 0.25*curve_signal_strength + 0.20*uncertainty_width + 0.10*underfilled_rate + 0.05*posterior_failure_rate
- `curve_signal_normalization`: divide by strongest positive surface signal in report
- `priority_policy`: P0 >= 0.75, P1 >= 0.50, otherwise P2

## Limitations

- `queue_is_based_on_current_draft_cells_not_representative_browsing`
- `curve_signals_describe_where_scores_move_not_which_runtime_policy_to_promote`
- `internal_locked_eval_split_is_advisory_until_more_cells_exist`
- `recommended_llm_rows_still_need_contract_validation_before_locked_eval`
- `sentinel_cells_are_not_used_for_primary_queue_selection`

## Next Steps

- Author P0 manual discovery rows first, then rerun difficulty surface and curve reports.
- Generate P0 LLM rows only after manual rows confirm the cell contract is real.
- Keep locked-eval rows separate from discovery rows before making any promotion claim.
- Use the updated curve shape to decide whether the next expansion should target phrase, shadow, or positive-active cells.
