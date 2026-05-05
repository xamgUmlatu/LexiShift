# en-es Semantic Veto LLM Pilot Failure Review

- Status: `ok`
- Decision: `llm_pilot_failure_review_complete`
- Generated: `2026-05-04T23:02:07Z`
- Failure count: `21`
- Main read: The LLM pilot keeps positive replacements visible, but negative blocking is weaker than manual/stress comparators; the largest failure class is `shadow_negative_active_score_dominated`. Weak expectations: negative_abstain_overall, shadow_negative_abstain, phrase_no_winner_abstain.

## Expectation Check

| Expectation | Actual | Target | Manual comparator | Delta vs target | Delta vs manual | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| positive_allow | 88.9% | 80.0% | 81.2% | +8.9pp | +7.6pp | meets_target_and_comparator |
| negative_abstain_overall | 52.8% | 50.0% | 75.0% | +2.8pp | -22.2pp | below_manual_comparator |
| shadow_negative_abstain | 58.3% | 50.0% | 87.5% | +8.3pp | -29.2pp | below_manual_comparator |
| phrase_no_winner_abstain | 41.7% | 50.0% | 62.5% | -8.3pp | -20.8pp | below_target |

## Comparison Rows

| Scope | Cases | Pos allow | Neg abstain | Utility | Target | Note |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| llm_pilot_overall | 72 | 88.9% | 52.8% | 35.4 | pass | LLM pilot, all admitted rows |
| llm_pilot_split:discovery | 56 | 84.6% | 50.0% | 23.4 | pass | LLM pilot split |
| llm_pilot_split:locked_eval | 16 | 100.0% | 66.7% | 12.0 | pass | LLM pilot split |
| llm_pilot_gold:phrase_no_winner | 12 | n/a | 41.7% | -0.2 | fail | LLM pilot gold type |
| llm_pilot_gold:positive_active | 36 | 88.9% | n/a | 30.4 | fail | LLM pilot gold type |
| llm_pilot_gold:shadow_negative | 24 | n/a | 58.3% | 5.2 | pass | LLM pilot gold type |
| manual_stress_best_veto_only |  | 81.2% | 75.0% | 26.2 | pass | Current manual/stress best row |
| manual_stress_source:semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_heldout |  | 81.2% | 87.5% | 21.8 | pass | Manual/stress source breakdown |
| manual_stress_source:semantic_source_non_v10_wave7_source_class_breadth_v1_phrase_control_triage_phrase |  | n/a | 62.5% | 4.4 | pass | Manual/stress source breakdown |
| product_quality_current_overall | 143 | 50.0% | 92.1% | 77.6 | fail | Current product-quality aggregate |

## Failure Classes

| Class | Cases | Gold types | Triggers | Median shadow lead | Median phrase lead | Samples |
| --- | ---: | --- | --- | ---: | ---: | --- |
| shadow_negative_active_score_dominated | 8 | shadow_negative:8 | branch:1, check:2, match:1, order:2, plant:1, play:1 | -0.0632 | -0.1237 | pilotrow:pilot_plant_planta:shadow_negative:001, pilotrow:pilot_check_cheque:shadow_negative:001, pilotrow:pilot_check_cheque:shadow_negative:002, pilotrow:pilot_branch_sucursal:shadow_negative:002, pilotrow:pilot_play_obra:shadow_negative:002, pilotrow:pilot_order_pedido:shadow_negative:001 |
| phrase_no_winner_phrase_score_not_dominant | 7 | phrase_no_winner:7 | bank:1, check:1, order:1, plant:1, play:1, report:1, watch:1 | -0.0189 | -0.0519 | pilotrow:pilot_bank_banco:phrase_no_winner:001, pilotrow:pilot_plant_planta:phrase_no_winner:001, pilotrow:pilot_check_cheque:phrase_no_winner:001, pilotrow:pilot_play_obra:phrase_no_winner:001, pilotrow:pilot_report_informe:phrase_no_winner:001, pilotrow:pilot_order_pedido:phrase_no_winner:001 |
| positive_overblocked_by_phrase_prototype | 3 | positive_active:3 | board:1, report:2 | 0.0008 | 0.0584 | pilotrow:pilot_board_tablero:positive_active:001, pilotrow:pilot_report_informe:positive_active:001, pilotrow:pilot_report_informe:positive_active:002 |
| shadow_negative_shadow_lead_below_threshold | 2 | shadow_negative:2 | plant:1, report:1 | 0.0156 | -0.0542 | pilotrow:pilot_plant_planta:shadow_negative:002, pilotrow:pilot_report_informe:shadow_negative:001 |
| positive_overblocked_by_shadow_score | 1 | positive_active:1 | file:1 | 0.142 | -0.0496 | pilotrow:pilot_file_archivo:positive_active:001 |

## Trigger Failures

| Trigger | Failures | Outcomes | Gold types | Samples |
| --- | ---: | --- | --- | --- |
| report | 4 | negative_allow:2, positive_abstain:2 | phrase_no_winner:1, positive_active:2, shadow_negative:1 | pilotrow:pilot_report_informe:positive_active:001, pilotrow:pilot_report_informe:positive_active:002, pilotrow:pilot_report_informe:shadow_negative:001, pilotrow:pilot_report_informe:phrase_no_winner:001 |
| check | 3 | negative_allow:3 | phrase_no_winner:1, shadow_negative:2 | pilotrow:pilot_check_cheque:shadow_negative:001, pilotrow:pilot_check_cheque:shadow_negative:002, pilotrow:pilot_check_cheque:phrase_no_winner:001 |
| order | 3 | negative_allow:3 | phrase_no_winner:1, shadow_negative:2 | pilotrow:pilot_order_pedido:shadow_negative:001, pilotrow:pilot_order_pedido:shadow_negative:002, pilotrow:pilot_order_pedido:phrase_no_winner:001 |
| plant | 3 | negative_allow:3 | phrase_no_winner:1, shadow_negative:2 | pilotrow:pilot_plant_planta:shadow_negative:001, pilotrow:pilot_plant_planta:shadow_negative:002, pilotrow:pilot_plant_planta:phrase_no_winner:001 |
| play | 2 | negative_allow:2 | phrase_no_winner:1, shadow_negative:1 | pilotrow:pilot_play_obra:shadow_negative:002, pilotrow:pilot_play_obra:phrase_no_winner:001 |
| bank | 1 | negative_allow:1 | phrase_no_winner:1 | pilotrow:pilot_bank_banco:phrase_no_winner:001 |
| board | 1 | positive_abstain:1 | positive_active:1 | pilotrow:pilot_board_tablero:positive_active:001 |
| branch | 1 | negative_allow:1 | shadow_negative:1 | pilotrow:pilot_branch_sucursal:shadow_negative:002 |
| file | 1 | positive_abstain:1 | positive_active:1 | pilotrow:pilot_file_archivo:positive_active:001 |
| match | 1 | negative_allow:1 | shadow_negative:1 | pilotrow:pilot_match_partido:shadow_negative:001 |
| watch | 1 | negative_allow:1 | phrase_no_winner:1 | pilotrow:pilot_watch_reloj:phrase_no_winner:001 |

## Samples

| Case | Gold | Trigger | Outcome | Class | Active | Shadow | Phrase | Sentence |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| pilotrow:pilot_bank_banco:phrase_no_winner:001 | phrase_no_winner | bank | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.5943 | 0.5377 | 0.5004 | Bank on getting there early, because the parking lot fills up fast before the concert starts. |
| pilotrow:pilot_plant_planta:shadow_negative:001 | shadow_negative | plant | negative_allow | shadow_negative_active_score_dominated | 0.6462 | 0.64 | 0.5094 | After the outage, the plant was restarted, and the lights came back on. |
| pilotrow:pilot_plant_planta:shadow_negative:002 | shadow_negative | plant | negative_allow | shadow_negative_shadow_lead_below_threshold | 0.6634 | 0.6771 | 0.6175 | The engineers inspected the cooling systems at the power plant after the alarm sounded. |
| pilotrow:pilot_plant_planta:phrase_no_winner:001 | phrase_no_winner | plant | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.5957 | 0.5834 | 0.5721 | In the end, the whole plan was a plant to get more clicks. |
| pilotrow:pilot_board_tablero:positive_active:001 | positive_active | board | positive_abstain | positive_overblocked_by_phrase_prototype | 0.5856 | 0.5394 | 0.644 | New board game guide posted today. |
| pilotrow:pilot_check_cheque:shadow_negative:001 | shadow_negative | check | negative_allow | shadow_negative_active_score_dominated | 0.7607 | 0.6082 | 0.6 | At the gate, the final check clears the bag. |
| pilotrow:pilot_check_cheque:shadow_negative:002 | shadow_negative | check | negative_allow | shadow_negative_active_score_dominated | 0.6459 | 0.5043 | 0.4395 | The server logs flagged a security check after the failed login attempts. |
| pilotrow:pilot_check_cheque:phrase_no_winner:001 | phrase_no_winner | check | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.6063 | 0.5874 | 0.6035 | Check the box below to continue, then review the form before you submit it. |
| pilotrow:pilot_branch_sucursal:shadow_negative:002 | shadow_negative | branch | negative_allow | shadow_negative_active_score_dominated | 0.6022 | 0.5855 | 0.487 | The database query returned a branch of the decision tree after the latest update. |
| pilotrow:pilot_file_archivo:positive_active:001 | positive_active | file | positive_abstain | positive_overblocked_by_shadow_score | 0.5517 | 0.6937 | 0.644 | The clerk opened the file after lunch. |
| pilotrow:pilot_play_obra:shadow_negative:002 | shadow_negative | play | negative_allow | shadow_negative_active_score_dominated | 0.5926 | 0.4652 | 0.5536 | The server logs show a failed play in the deployment pipeline. |
| pilotrow:pilot_play_obra:phrase_no_winner:001 | phrase_no_winner | play | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.7199 | 0.5906 | 0.6376 | At the end of the article, the play on words made the headline memorable. |
| pilotrow:pilot_report_informe:positive_active:001 | positive_active | report | positive_abstain | positive_overblocked_by_phrase_prototype | 0.5833 | 0.5841 | 0.6469 | The final report from the audit is now online. |
| pilotrow:pilot_report_informe:positive_active:002 | positive_active | report | positive_abstain | positive_overblocked_by_phrase_prototype | 0.6006 | 0.6085 | 0.6627 | After the audit team finished its review, the final report was posted on the compliance portal. |
| pilotrow:pilot_report_informe:shadow_negative:001 | shadow_negative | report | negative_allow | shadow_negative_shadow_lead_below_threshold | 0.6391 | 0.6566 | 0.6078 | After the storm, the report from the engine room was a loud bang. |
| pilotrow:pilot_report_informe:phrase_no_winner:001 | phrase_no_winner | report | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.7502 | 0.6422 | 0.6528 | The report back from the field arrived late, but the team still finished the update. |
| pilotrow:pilot_order_pedido:shadow_negative:001 | shadow_negative | order | negative_allow | shadow_negative_active_score_dominated | 0.5973 | 0.5684 | 0.4649 | New order restored in the court after the hearing. |
| pilotrow:pilot_order_pedido:shadow_negative:002 | shadow_negative | order | negative_allow | shadow_negative_active_score_dominated | 0.5523 | 0.5087 | 0.5142 | The database query returned rows in alphabetical order. |
| pilotrow:pilot_order_pedido:phrase_no_winner:001 | phrase_no_winner | order | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.5249 | 0.5303 | 0.4784 | The app loaded in order, but the video still buffered for several minutes. |
| pilotrow:pilot_match_partido:shadow_negative:001 | shadow_negative | match | negative_allow | shadow_negative_active_score_dominated | 0.672 | 0.5893 | 0.697 | Headline: a perfect match for the frame, with the finish finally aligned. |
| pilotrow:pilot_watch_reloj:phrase_no_winner:001 | phrase_no_winner | watch | negative_allow | phrase_no_winner_phrase_score_not_dominant | 0.6263 | 0.6683 | 0.6531 | Before the meeting starts, watch your step on the wet tiles. |

## Interpretation

- The pilot is not lower in every way: positive allow beats the 80% target and the current manual/stress comparator.
- The worrying gap is negative blocking. Overall negative abstain barely clears the 50% target and is well below the manual/stress best row.
- Phrase/no-winner is the clearest miss: its abstain rate is below target and below the manual phrase-source comparator.
- Shadow-negative rows pass the minimum target but lag the manual active/shadow comparator, so the issue is not only phrase handling.
- Most failures are no-veto negative allows, meaning the active/shadow/phrase scores did not produce a strong enough blocker rather than a blocker firing incorrectly.

## Next Steps

- Review the no-veto negative-allow rows first; they show whether source evidence, context representation, or threshold shape is the limiting factor.
- Keep phrase/no-winner separate from shadow-negative rows; the phrase class is below target even while the aggregate passes.
- Do not interpret the small locked-eval pass as enough to justify full-scale generation; expand only after the discovered failure classes are understood.
