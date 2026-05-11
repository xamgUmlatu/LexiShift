# en-es Semantic Veto Product-Scope Band-Grading v1 Allocation Plan

- Status: `ok`
- Decision: `product_scope_band_grading_v1_allocation_plan_established`
- Generated: `2026-05-09T20:22:29Z`
- Candidate families: `49`
- Selected families: `18`
- Planned generation slots: `54`
- Expected generated items: `90`
- Previous-overlap selected: `0`

## Methodology

Freeze the smallest useful new-family follow-through batch for the accepted v1 band heuristic, while preserving high/middle/low controls.

Families are banded by the accepted formula and sampled deterministically within each band. Previous paid-pilot families are excluded by default so the next spend increases coverage instead of duplicating rows.

## Candidate

- Scorer/config: `safest_80pct_positive_sentence_transformer_a0000_m0015`
- Formula: `sweep_linear_2169`
- Primary grade: `0.2202`
- Base SRS high-low delta: `+24.8%`
- Weights: `{"polysemy_risk":0.07692307692307693,"pos_shape_risk":0.23076923076923078,"shadow_coverage_risk":0.3076923076923077,"source_zipf_risk":0.23076923076923078,"target_zipf_risk":0.15384615384615385}`

## Band Availability

| Band | Families | Previous pilot overlap | New families |
| --- | ---: | ---: | ---: |
| `high_need` | 17 | 8 | 9 |
| `middle_need` | 16 | 6 | 10 |
| `low_need` | 16 | 6 | 10 |

## Arm Summary

| Arm | Families | Mean need | Historical failure | Harmful share | False abstains |
| --- | ---: | ---: | ---: | ---: | ---: |
| `high_need` | 6 | 0.7609 | 12.5% | 0.0% | 3 |
| `middle_control` | 6 | 0.5968 | 0.0% | 0.0% | 0 |
| `low_control` | 6 | 0.4038 | 0.0% | 0.0% | 0 |

## Selected Families

| Arm | Rank | Trigger | Target | Need | Prev pilot | Slots | Historical fail |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| `high_need` | 1 | `cite` | `mencionar` | 0.6731 | `false` | 3 | 25.0% |
| `high_need` | 2 | `smile` | `sonreír` | 0.7577 | `false` | 3 | 0.0% |
| `high_need` | 3 | `bar` | `cercar` | 0.8500 | `false` | 3 | 0.0% |
| `high_need` | 4 | `control` | `gobernar` | 0.8308 | `false` | 3 | 25.0% |
| `high_need` | 5 | `except` | `excepto` | 0.6885 | `false` | 3 | 25.0% |
| `high_need` | 6 | `region` | `comarca` | 0.7654 | `false` | 3 | 0.0% |
| `middle_control` | 1 | `govern` | `gobernar` | 0.5923 | `false` | 3 | 0.0% |
| `middle_control` | 2 | `german` | `alemán` | 0.5423 | `false` | 3 | 0.0% |
| `middle_control` | 3 | `american` | `americano` | 0.6308 | `false` | 3 | 0.0% |
| `middle_control` | 4 | `endure` | `durar` | 0.6385 | `false` | 3 | 0.0% |
| `middle_control` | 5 | `tomorrow` | `mañana` | 0.5769 | `false` | 3 | 0.0% |
| `middle_control` | 6 | `russian` | `ruso` | 0.6000 | `false` | 3 | 0.0% |
| `low_control` | 1 | `dentist` | `dentista` | 0.3577 | `false` | 3 | 0.0% |
| `low_control` | 2 | `pub` | `taberna` | 0.4269 | `false` | 3 | 0.0% |
| `low_control` | 3 | `shortage` | `falta` | 0.3692 | `false` | 3 | 0.0% |
| `low_control` | 4 | `rumanian` | `rumano` | 0.4615 | `false` | 3 | 0.0% |
| `low_control` | 5 | `argentinean` | `argentino` | 0.3462 | `false` | 3 | 0.0% |
| `low_control` | 6 | `owe` | `deber` | 0.4615 | `false` | 3 | 0.0% |

## Guardrails

| Check | Value |
| --- | --- |
| `acceptance_audit_ok` | `True` |
| `acceptance_decision_is_carry_forward` | `True` |
| `dataset_is_user_approved` | `True` |
| `band_rows_available` | `True` |
| `band_rows_unique` | `True` |
| `selected_families_unique` | `True` |
| `no_previous_overlap_selected` | `True` |
| `no_outcome_fields_used_for_selection` | `True` |
| `all_requested_arm_sizes_available` | `True` |
| `generation_contract_compatible_with_existing_request_renderer` | `True` |
| `manifest_generated` | `True` |

## Limitations

- `this_is_a_no_spend_plan_not_generated_data`
- `selection_is_for_sentence_transformer_product_lane_not_backend_agnostic`
- `historical_failure_fields_are_diagnostic_only_and_not_used_for_selection`
- `the_plan_expands_beyond_previous_pilot_families_but_still_uses_the_49_family_denominator`

## Next Steps

- Render the generation request packet from this manifest.
- Inspect selected families and prompt packet before any paid generation.
- Generate the same slot contract for all arms if approved.
- Admit outputs and compare improvement by arm before broad language-wide spending.
