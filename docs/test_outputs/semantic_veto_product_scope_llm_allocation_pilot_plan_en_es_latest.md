# en-es Semantic Veto Product-Scope LLM Allocation Pilot Plan

- Status: `ok`
- Decision: `product_scope_llm_allocation_pilot_plan_established`
- Generated: `2026-05-09T05:10:07Z`
- Candidate families: `49`
- Selected families: `20`
- Planned generation slots: `60`
- Expected generated items: `100`

## Methodology

Choose a smallest meaningful high/middle/low family batch to test whether the corrected shadow-coverage band actually predicts where generated semantic evidence improves veto quality.

Families are assigned to bands by the selected formula's predicted need. Within tied bands, selection uses a deterministic seed hash over family_id. Observed failures are attached after selection for diagnosis only.

## Band Availability

| Band | Predicted need | Available families |
| --- | ---: | ---: |
| `high_need` | 0.8500 | 19 |
| `middle_control` | 0.6500 | 4 |
| `low_control` | 0.3000 | 26 |

## Arm Summary

| Arm | Families | Mean need | Historical failure | Harmful share | False abstains |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 8 | 0.8500 | 27.5% | 14.4% | 21 |
| `middle_control` | 4 | 0.6500 | 30.0% | 11.7% | 11 |
| `low_control` | 8 | 0.3000 | 5.0% | 0.0% | 4 |

## Selected Families

| Arm | Rank | Trigger | Target | Need | Shadow count | Slots | Historical fail |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| `high_need` | 1 | `acceptable` | `razonable` | 0.8500 | 2 | 3 | 45.0% |
| `high_need` | 2 | `billow` | `oleaje` | 0.8500 | 2 | 3 | 15.0% |
| `high_need` | 3 | `bridle` | `reprimir` | 0.8500 | 2 | 3 | 60.0% |
| `high_need` | 4 | `current` | `contemporáneo` | 0.8500 | 2 | 3 | 35.0% |
| `high_need` | 5 | `offset` | `distancia` | 0.8500 | 2 | 3 | 10.0% |
| `high_need` | 6 | `parrot` | `loro` | 0.8500 | 2 | 3 | 30.0% |
| `high_need` | 7 | `rebate` | `descuento` | 0.8500 | 2 | 3 | 15.0% |
| `high_need` | 8 | `stall` | `cuadra` | 0.8500 | 2 | 3 | 10.0% |
| `middle_control` | 1 | `adder` | `víbora` | 0.6500 | 1 | 3 | 13.3% |
| `middle_control` | 2 | `chic` | `elegante` | 0.6500 | 1 | 3 | 46.7% |
| `middle_control` | 3 | `pair` | `par` | 0.6500 | 1 | 3 | 6.7% |
| `middle_control` | 4 | `snore` | `roncar` | 0.6500 | 1 | 3 | 53.3% |
| `low_control` | 1 | `adjoining` | `contiguo` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 2 | `adjoining` | `vecino` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 3 | `begin` | `comenzar` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 4 | `bouillon` | `caldo` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 5 | `december` | `diciembre` | 0.3000 | 0 | 3 | 40.0% |
| `low_control` | 6 | `entirely` | `enteramente` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 7 | `handiwork` | `artesanía` | 0.3000 | 0 | 3 | 0.0% |
| `low_control` | 8 | `upon` | `sobre` | 0.3000 | 0 | 3 | 0.0% |

## Guardrails

| Check | Value |
| --- | --- |
| `dataset_is_user_approved` | `True` |
| `selection_rows_available` | `True` |
| `selection_formula_is_shadow_coverage_only` | `True` |
| `no_outcome_fields_used_for_selection` | `True` |
| `selected_families_unique` | `True` |
| `all_requested_arm_sizes_available` | `True` |
| `planned_slot_count_equal_per_family` | `True` |
| `generation_contract_compatible_with_existing_request_renderer` | `True` |
| `manifest_generated` | `True` |

## Limitations

- `pilot_families_are_from_the_current_49_family_product_scope_denominator`
- `shadow_coverage_is_a_current_best_cheap_signal_not_a_final_language_wide_policy`
- `historical_observed_failure_annotations_are_diagnostic_only`
- `the_middle_band_has_only_four_available_families_in_this_denominator`
- `llm_generation_and_downstream_rescoring_are_not_done_by_this_harness`

## Next Steps

- Render the generation request packet from this manifest before spending.
- Run identical generation slots for high, middle, and low arms.
- Admit generated outputs, then rescore the same five carried-forward candidate policies.
- Prioritize full production generation by band only if high_need improves more than controls.
