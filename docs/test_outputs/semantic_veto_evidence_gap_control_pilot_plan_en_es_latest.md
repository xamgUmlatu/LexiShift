# en-es Semantic Veto Evidence-Gap Control Pilot Plan

- Status: `ok`
- Decision: `evidence_gap_control_pilot_plan_established`
- Generated: `2026-05-07T21:42:15Z`
- Candidate families: `49`
- Selected families: `24`
- Planned generation slots: `72`

## Methodology

Freeze a top/middle/low control pilot that can falsify whether evidence-gap ranking predicts benefit from better generated evidence.

Families are selected by predicted_need from the chosen pre-outcome heuristic only. Historical observed failures are attached after selection for diagnosis, not used for selecting pilot rows.

## Arm Summary

| Arm | Families | Mean need | TF-IDF historical failure | ST historical failure |
| --- | ---: | ---: | ---: | ---: |
| `high_need` | 8 | 0.8359 | 62.5% | 33.3% |
| `middle_control` | 8 | 0.7266 | 61.3% | 38.8% |
| `low_control` | 8 | 0.5371 | 37.5% | 22.5% |

## Selected Families

| Arm | Rank | Trigger | Target | Need | Slots | TF-IDF fail | ST fail |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| `high_need` | 1 | `adjoining` | `vecino` | 0.8750 | 3 | 33.3% | 33.3% |
| `high_need` | 2 | `entirely` | `enteramente` | 0.8750 | 3 | 66.7% | 33.3% |
| `high_need` | 3 | `bouillon` | `caldo` | 0.8438 | 3 | 66.7% | 33.3% |
| `high_need` | 4 | `december` | `diciembre` | 0.8438 | 3 | 66.7% | 33.3% |
| `high_need` | 5 | `american` | `americano` | 0.8125 | 3 | 66.7% | 33.3% |
| `high_need` | 6 | `among` | `entre` | 0.8125 | 3 | 66.7% | 33.3% |
| `high_need` | 7 | `begin` | `comenzar` | 0.8125 | 3 | 66.7% | 33.3% |
| `high_need` | 8 | `dentist` | `dentista` | 0.8125 | 3 | 66.7% | 33.3% |
| `middle_control` | 1 | `brother` | `hermano` | 0.7500 | 3 | 66.7% | 33.3% |
| `middle_control` | 2 | `german` | `alemán` | 0.7500 | 3 | 66.7% | 33.3% |
| `middle_control` | 3 | `heart` | `corazón` | 0.7500 | 3 | 66.7% | 33.3% |
| `middle_control` | 4 | `rumanian` | `rumano` | 0.7500 | 3 | 66.7% | 33.3% |
| `middle_control` | 5 | `salesman` | `vendedor` | 0.7188 | 3 | 66.7% | 33.3% |
| `middle_control` | 6 | `tomorrow` | `mañana` | 0.7188 | 3 | 66.7% | 33.3% |
| `middle_control` | 7 | `acceptable` | `razonable` | 0.6875 | 3 | 40.0% | 60.0% |
| `middle_control` | 8 | `chic` | `elegante` | 0.6875 | 3 | 50.0% | 50.0% |
| `low_control` | 1 | `smile` | `sonreír` | 0.4531 | 3 | 40.0% | 0.0% |
| `low_control` | 2 | `break` | `quebrar` | 0.5156 | 3 | 20.0% | 20.0% |
| `low_control` | 3 | `rebate` | `descuento` | 0.5312 | 3 | 40.0% | 40.0% |
| `low_control` | 4 | `govern` | `gobernar` | 0.5469 | 3 | 40.0% | 20.0% |
| `low_control` | 5 | `offset` | `distancia` | 0.5625 | 3 | 20.0% | 20.0% |
| `low_control` | 6 | `control` | `gobernar` | 0.5625 | 3 | 60.0% | 40.0% |
| `low_control` | 7 | `bridle` | `reprimir` | 0.5625 | 3 | 40.0% | 40.0% |
| `low_control` | 8 | `bar` | `cercar` | 0.5625 | 3 | 40.0% | 0.0% |

## Guardrails

| Check | Value |
| --- | --- |
| `dataset_is_user_approved` | `True` |
| `selection_rows_available` | `True` |
| `no_outcome_fields_used_for_selection` | `True` |
| `all_arms_have_requested_size` | `True` |
| `selected_families_unique` | `True` |
| `planned_slot_count_equal_per_family` | `True` |
| `manifest_generated` | `True` |

## Limitations

- `pilot_families_are_from_the_current_49_family_repaired_full_denominator`
- `historical_observed_failure_annotations_are_diagnostic_only`
- `middle_and_low_controls_are_required_to_avoid_top_rank_overfitting`
- `llm_generation_and_downstream_rescoring_are_not_done_by_this_harness`

## Next Steps

- Use this manifest to generate or collect the same evidence/context slots for every arm.
- Apply generated evidence without changing thresholds, then compare improvement by high, middle, and low arms.
- Promote the heuristic only if high-need families improve more than middle and low controls.
