# en-es Semantic Veto LLM Pilot Scoring

- Status: `ok`
- Decision: `frozen_candidate_product_target_passed_on_llm_pilot`
- Generated: `2026-05-04T23:01:58Z`
- Admitted rows: `72`
- Scored cases: `72`
- Scoreable families: `12` / `12`
- Product target: `pass`
- Positive allow / negative abstain: `88.9%` / `52.8%`
- Utility: `35.4`

## Candidate

| Key | Value |
| --- | --- |
| `candidate_id` | `control_st_masked_all_margin_phrase_override\|shadow_or_phrase_score\|lead=0.05\|score=0.0` |
| `decision_shape` | `allow_default_shadow_veto` |
| `base_config_id` | `control_st_masked_all_margin_phrase_override` |
| `phrase_mode` | `shadow_or_phrase_score` |
| `shadow_lead_min` | `0.05` |
| `shadow_score_min` | `0.0` |
| `runtime_policy_change` | `none` |
| `source_evidence_promotion` | `none` |
| `scorer_id` | `sentence_transformer_cosine` |
| `context_view` | `masked_sentence` |
| `scoring_shape` | `independent_source_prototype_scores` |
| `final_decision` | `binary_replace_or_abstain` |

## Strict Flow Checks

| Key | Value |
| --- | --- |
| `evaluation_rows_used_as_evidence` | `False` |
| `source_evidence_promotion` | `none` |
| `runtime_policy_change` | `none` |
| `locked_eval_threshold_tuning_allowed` | `False` |
| `thresholds_frozen_from_plan` | `True` |

## Source Evidence

| Key | Value |
| --- | --- |
| `contract_status` | `ok` |
| `contract_complete` | `True` |
| `semantic_contract_complete` | `True` |
| `phrase_containment_contract_complete` | `True` |
| `contract_family_count` | `19` |
| `contract_complete_family_count` | `19` |
| `batch_id` | `en-es:reviewed-example-frames:reviewed-example-frames-v10-full-20260425a` |
| `source_id` | `reviewed_sentence_veto_example_frames` |
| `source_family` | `silver_llm_generation` |
| `model_id` | `reviewed-sentence-veto-fixture` |
| `row_count` | `95` |
| `coverage_family_count` | `12` |
| `pilot_family_count` | `12` |
| `coverage_row_count` | `72` |
| `pilot_row_count` | `72` |

## Leakage Checks

| Key | Value |
| --- | --- |
| `evaluation_rows_used_as_evidence` | `False` |
| `row_id_overlap_count` | `0` |
| `row_id_overlaps` | `` |
| `context_text_exact_overlap_count` | `0` |
| `context_text_exact_overlap_case_ids` | `` |
| `gold_reason_used_for_scoring` | `False` |
| `negative_sense_label_used_for_scoring` | `False` |
| `no_winner_reason_used_for_scoring` | `False` |
| `blocking_issue_count` | `0` |

## Split Breakdown

| split | Cases | Pos allow | Neg abstain | Pos allow rate | Neg abstain rate | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| discovery | 56 | 22 | 15 | 84.6% | 50.0% | 23.4 | pass |
| locked_eval | 16 | 10 | 4 | 100.0% | 66.7% | 12.0 | pass |

## Gold Type Breakdown

| gold_type | Cases | Pos allow | Neg abstain | Pos allow rate | Neg abstain rate | Utility | Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| phrase_no_winner | 12 | 0 | 5 | n/a | 41.7% | -0.2 | fail |
| positive_active | 36 | 32 | 0 | 88.9% | n/a | 30.4 | fail |
| shadow_negative | 24 | 0 | 14 | n/a | 58.3% | 5.2 | pass |

## Family Coverage

| Family | Pilot rows | Active | Shadow | Phrase | Scoreable | Missing |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| en-es:sentence-veto:bank:banco | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:board:tablero | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:branch:sucursal | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:check:cheque | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:file:archivo | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:match:partido | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:order:pedido | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:plant:planta | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:play:obra | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:report:informe | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:seal:sello | 6 | 2 | 2 | 1 | yes |  |
| en-es:sentence-veto:watch:reloj | 6 | 2 | 2 | 1 | yes |  |

## Failure Rows

| Case | Split | Gold | Trigger | Outcome | Reason | Active | Shadow | Phrase | Sentence |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| pilotrow:pilot_bank_banco:phrase_no_winner:001 | discovery | phrase_no_winner | bank | negative_allow |  | 0.5943 | 0.5377 | 0.5004 | Bank on getting there early, because the parking lot fills up fast before the concert starts. |
| pilotrow:pilot_plant_planta:shadow_negative:001 | discovery | shadow_negative | plant | negative_allow |  | 0.6462 | 0.64 | 0.5094 | After the outage, the plant was restarted, and the lights came back on. |
| pilotrow:pilot_plant_planta:shadow_negative:002 | discovery | shadow_negative | plant | negative_allow |  | 0.6634 | 0.6771 | 0.6175 | The engineers inspected the cooling systems at the power plant after the alarm sounded. |
| pilotrow:pilot_plant_planta:phrase_no_winner:001 | discovery | phrase_no_winner | plant | negative_allow |  | 0.5957 | 0.5834 | 0.5721 | In the end, the whole plan was a plant to get more clicks. |
| pilotrow:pilot_board_tablero:positive_active:001 | discovery | positive_active | board | positive_abstain | phrase_score_lead | 0.5856 | 0.5394 | 0.644 | New board game guide posted today. |
| pilotrow:pilot_check_cheque:shadow_negative:001 | discovery | shadow_negative | check | negative_allow |  | 0.7607 | 0.6082 | 0.6 | At the gate, the final check clears the bag. |
| pilotrow:pilot_check_cheque:shadow_negative:002 | discovery | shadow_negative | check | negative_allow |  | 0.6459 | 0.5043 | 0.4395 | The server logs flagged a security check after the failed login attempts. |
| pilotrow:pilot_check_cheque:phrase_no_winner:001 | discovery | phrase_no_winner | check | negative_allow |  | 0.6063 | 0.5874 | 0.6035 | Check the box below to continue, then review the form before you submit it. |
| pilotrow:pilot_branch_sucursal:shadow_negative:002 | discovery | shadow_negative | branch | negative_allow |  | 0.6022 | 0.5855 | 0.487 | The database query returned a branch of the decision tree after the latest update. |
| pilotrow:pilot_file_archivo:positive_active:001 | discovery | positive_active | file | positive_abstain | shadow_lead | 0.5517 | 0.6937 | 0.644 | The clerk opened the file after lunch. |
| pilotrow:pilot_play_obra:shadow_negative:002 | locked_eval | shadow_negative | play | negative_allow |  | 0.5926 | 0.4652 | 0.5536 | The server logs show a failed play in the deployment pipeline. |
| pilotrow:pilot_play_obra:phrase_no_winner:001 | discovery | phrase_no_winner | play | negative_allow |  | 0.7199 | 0.5906 | 0.6376 | At the end of the article, the play on words made the headline memorable. |
| pilotrow:pilot_report_informe:positive_active:001 | discovery | positive_active | report | positive_abstain | phrase_score_lead | 0.5833 | 0.5841 | 0.6469 | The final report from the audit is now online. |
| pilotrow:pilot_report_informe:positive_active:002 | discovery | positive_active | report | positive_abstain | phrase_score_lead | 0.6006 | 0.6085 | 0.6627 | After the audit team finished its review, the final report was posted on the compliance portal. |
| pilotrow:pilot_report_informe:shadow_negative:001 | locked_eval | shadow_negative | report | negative_allow |  | 0.6391 | 0.6566 | 0.6078 | After the storm, the report from the engine room was a loud bang. |
| pilotrow:pilot_report_informe:phrase_no_winner:001 | discovery | phrase_no_winner | report | negative_allow |  | 0.7502 | 0.6422 | 0.6528 | The report back from the field arrived late, but the team still finished the update. |
| pilotrow:pilot_order_pedido:shadow_negative:001 | discovery | shadow_negative | order | negative_allow |  | 0.5973 | 0.5684 | 0.4649 | New order restored in the court after the hearing. |
| pilotrow:pilot_order_pedido:shadow_negative:002 | discovery | shadow_negative | order | negative_allow |  | 0.5523 | 0.5087 | 0.5142 | The database query returned rows in alphabetical order. |
| pilotrow:pilot_order_pedido:phrase_no_winner:001 | discovery | phrase_no_winner | order | negative_allow |  | 0.5249 | 0.5303 | 0.4784 | The app loaded in order, but the video still buffered for several minutes. |
| pilotrow:pilot_match_partido:shadow_negative:001 | discovery | shadow_negative | match | negative_allow |  | 0.672 | 0.5893 | 0.697 | Headline: a perfect match for the frame, with the finish finally aligned. |
| pilotrow:pilot_watch_reloj:phrase_no_winner:001 | discovery | phrase_no_winner | watch | negative_allow |  | 0.6263 | 0.6683 | 0.6531 | Before the meeting starts, watch your step on the wet tiles. |

## Next Steps

- Inspect failure rows by split and gold type before expanding the LLM pilot.
- Run a larger locked eval lane with the same source/evaluation separation.
- Keep thresholds frozen until discovery-only diagnostics justify a separate candidate.

## Limitations

- `llm_pilot_is_not_representative_browsing`
- `source_evidence_is_independent_but_still_silver_llm_reviewed_fixture`
- `candidate_thresholds_are_frozen_not_tuned_on_locked_eval`
- `scoring_does_not_promote_runtime_policy_or_source_evidence`
