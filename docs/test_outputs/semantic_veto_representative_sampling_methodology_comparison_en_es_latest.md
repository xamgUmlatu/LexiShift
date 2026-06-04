# en-es Semantic Veto Sampling Methodology Comparison

- Status: `ok`
- Decision: `sampling_methodology_comparison_established`
- Generated: `2026-05-05T21:16:20+00:00`

## Main Comparison

| Metric | Old heuristic-group pilot | Representative sampler | Delta / Read |
| --- | ---: | ---: | --- |
| selected/source sampled triggers | 24 primary + 5 sentinel | 255 | 10.625x sampled vs old primary |
| candidate universe | 4112 | 4112 | same eligible pool |
| represented non-empty fine cells | 10 / 39 | 39 / 39 | representative sampler covers all non-empty cells |
| source-ready target families | not measured on old pilot | 7 / 255 | construction coverage, not accuracy |

The old lane selected four words per coarse primary group. It was not random: within each group it sorted by source rank, then by high WordNet sense/POS counts. The new lane samples inside every non-empty fine cell and records weights so universe-level means do not treat rare cells as common cells.

## Old Group Bias

| Group | Eligible | Selected | Selected share | Selected rank mean | Eligible rank mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `core_high_polysemy` | 30 | 4 | 0.1333 | 122.5 | 495.6667 |
| `core_low_polysemy_control` | 12 | 4 | 0.3333 | 247.5 | 574.1667 |
| `mid_high_polysemy` | 82 | 4 | 0.0488 | 1027.5 | 2531.2195 |
| `mid_low_polysemy_control` | 138 | 4 | 0.029 | 1180.0 | 3369.9275 |
| `tail_high_polysemy` | 120 | 4 | 0.0333 | 5052.5 | 14544.3333 |
| `tail_low_polysemy_control` | 2759 | 4 | 0.0014 | 5097.5 | 30300.357 |

## Source Sampling Stability

| Sample per cell | Runs | Sample count range | Cell coverage | Mean pairwise overlap | Max weighted rank TVD |
| ---: | ---: | --- | --- | ---: | ---: |
| 4 | 5 | 140.0-140.0 | 1.0-1.0 | 0.1837 | 0.0 |
| 8 | 5 | 255.0-255.0 | 1.0-1.0 | 0.2514 | 0.0 |
| 16 | 5 | 444.0-444.0 | 1.0-1.0 | 0.3393 | 0.0 |
| 32 | 5 | 732.0-732.0 | 1.0-1.0 | 0.4345 | 0.0 |

Weighted rank/polysemy/POS distributions match the candidate universe for the cell-defining features whenever every non-empty cell has a sample. That does not prove downstream source-ready or scoring rates; it only means the source-band frame is no longer the old hard-case slice.

## Construction Stability

| Sample per cell | Runs | Source-ready rate range | Source-ready count range | Weak count range | Blocked count range |
| ---: | ---: | --- | --- | --- | --- |
| 4 | 3 | 0.0357-0.05 | 5.0-7.0 | 37.0-43.0 | 92.0-96.0 |
| 8 | 3 | 0.0314-0.0471 | 8.0-12.0 | 71.0-82.0 | 164.0-172.0 |
| 16 | 3 | 0.0293-0.0428 | 13.0-19.0 | 135.0-137.0 | 288.0-296.0 |

This is still construction coverage, not final allow/abstain accuracy. It tests whether the low source-ready rate is tied to one unlucky seed.

## Sweep Rerun Status

| Sweep | Status | Reason |
| --- | --- | --- |
| `heuristic_difficulty_surface` | `blocked_until_representative_case_traces_exist` | The prior sweep consumes authored/scored case traces, while the representative lane currently has source-trigger and target-family coverage only. |
| `formula_shape_bakeoff` | `blocked_until_representative_case_traces_exist` | Formula cells require observed positive/shadow/phrase outcomes; no representative scored contexts exist yet. |
| `formula_weight_surface` | `blocked_until_representative_case_traces_exist` | Continuous weight surfaces need observed failure rates by cell, not just sampled source triggers. |
| `curve_guided_expansion_plan` | `rerun_after_representative_surface_exists` | The current curve-guided queue came from the old authored stress lane; rerun it after representative cases are scored. |
| `source_sampling_seed_scale_stability` | `rerun_now` | This report reruns the source sampling side for multiple sample sizes and seeds. |

## Guardrails

| Check | Value |
| --- | --- |
| `old_pilot_primary_rows_detected` | `True` |
| `representative_sample_rows_detected` | `True` |
| `representative_cells_cover_all_nonempty_cells` | `True` |
| `stability_runs_cover_all_nonempty_cells` | `True` |

## Limitations

- `new_sampler_improves_source_band_representation_not_final_accuracy_by_itself`
- `target_family_construction_stability_is_coverage_not_final_scoring_accuracy`
- `old_formula_and_weight_sweeps_need_representative_case_traces_before_true_rerun`
- `equal_cell_sampling_requires_weights_for_candidate_universe_mean_estimates`

## Next Steps

- Broaden or diagnose the missing_noun_or_verb_translation blocker before spending on LLM rows.
- After representative target/shadow families and fixed contexts exist, rerun heuristic difficulty surface, formula-shape bakeoff, formula-weight surface, and curve-guided expansion against the representative lane.
