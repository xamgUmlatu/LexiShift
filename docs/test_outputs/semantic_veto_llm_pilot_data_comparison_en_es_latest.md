# en-es Semantic Veto LLM vs Manual Failed-Case Data Comparison

- Status: `ok`
- Decision: `llm_manual_failed_case_data_comparison_complete`
- Generated: `2026-05-04T23:15:55Z`
- Failed LLM rows compared: `21`
- Manual rows referenced: `35`
- Obvious data-difference rows: `21`

## Summary

| Item | Value |
| --- | --- |
| `failed_llm_case_count` | `21` |
| `manual_matching_case_count` | `35` |
| `obvious_data_difference_count` | `21` |
| `failure_class_counts` | `phrase_no_winner_phrase_score_not_dominant:7, positive_overblocked_by_phrase_prototype:3, positive_overblocked_by_shadow_score:1, shadow_negative_active_score_dominated:8, shadow_negative_shadow_lead_below_threshold:2` |
| `diagnosis_confidence_counts` | `high:16, medium:5` |
| `data_difference_note_counts` | `llm_sentence_is_lexically_far_from_manual_same_class_examples:12, phrase_prototype_did_not_cover_this_expression_strongly_enough:7, phrase_surface_pattern_visible_but_not_weighted_enough:3, positive_sentence_was_generic_enough_for_shadow_evidence_to_win:1, positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win:3, same_family_manual_matching_rows_also_have_failures:3, same_family_manual_matching_rows_passed_under_control:18, scorer_chose_active_evidence_over_blocker:12, shadow_negative_was_scored_as_active_like:8, surface_pattern_points_to_different_source_than_score_winner:15` |

## Interpretation

- The automatic comparison found medium/high-confidence data explanations for 21 / 21 failed LLM rows.
- Diagnosis confidence counts: high:16, medium:5.
- The repeated pattern is that LLM-generated negative rows often leave the narrow manual/source evidence lane or expose phrase shapes whose word order is visible but whose semantic score is not dominant enough.
- Several LLM rows are not simply harder examples; they expose source-coverage or label-scope questions, especially for `plant`, `check`, `order`, `match`, and phrase/no-winner rows.
- Largest failure classes: phrase_no_winner_phrase_score_not_dominant:7, positive_overblocked_by_phrase_prototype:3, positive_overblocked_by_shadow_score:1, shadow_negative_active_score_dominated:8, shadow_negative_shadow_lead_below_threshold:2.

## Case Comparisons

### `pilotrow:pilot_bank_banco:phrase_no_winner:001`

- Trigger/gold/outcome: `bank` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `high`
- Short read: The phrase shape is visible in the words, but the semantic score still did not let phrase evidence win.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, phrase_surface_pattern_visible_but_not_weighted_enough`
- LLM sentence: Bank on getting there early, because the parking lot fills up fast before the concert starts.
- LLM context: `___ on getting there early, because the parking lot fills up fast before the concert starts.`
- Scores: active `0.5943`, shadow `0.5377`, phrase `0.5004`, shadow lead `-0.0567`, phrase lead `-0.0939`
- Score winner vs surface-pattern winner: `active` / `phrase`
- Source active: `She deposited the cash at the ___ before lunch.`
- Source shadow: `Wildflowers grew along the muddy ___`
- Source phrase: `You can ___ on her support.`
- Nearest manual same-class row: `en-es:sentence-veto:bank:005` composite `0.1041`, bigram `0.0526`, neighbor `0.2` - You can bank on her support.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:bank:005 | none | abstain | 0.564855 | 0.531059 | You can bank on her support. |

### `pilotrow:pilot_plant_planta:shadow_negative:001`

- Trigger/gold/outcome: `plant` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, shadow_negative_was_scored_as_active_like`
- LLM sentence: After the outage, the plant was restarted, and the lights came back on.
- LLM context: `After the outage, the ___ was restarted, and the lights came back on.`
- Scores: active `0.6462`, shadow `0.64`, phrase `0.5094`, shadow lead `-0.0062`, phrase lead `-0.1368`
- Score winner vs surface-pattern winner: `active` / `shadow`
- Source active: `The ___ needs more sunlight in the afternoon.`
- Source shadow: `The steel ___ closed after the strike.`
- Source phrase: `They tried to ___ evidence in his office.`
- Nearest manual same-class row: `en-es:sentence-veto:plant:003` composite `0.1036`, bigram `0.0588`, neighbor `0.1429` - The steel plant closed after the strike.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:plant:003 | shadow | abstain | 0.483005 | 0.576243 | The steel plant closed after the strike. |
| en-es:sentence-veto:plant:004 | shadow | abstain | 0.502487 | 0.606895 | Hundreds of workers left the chemical plant at noon. |

### `pilotrow:pilot_plant_planta:shadow_negative:002`

- Trigger/gold/outcome: `plant` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_shadow_lead_below_threshold`
- Diagnosis confidence: `medium`
- Short read: The same-family manual examples look easier or more directly aligned with the available evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control`
- LLM sentence: The engineers inspected the cooling systems at the power plant after the alarm sounded.
- LLM context: `The engineers inspected the cooling systems at the power ___ after the alarm sounded.`
- Scores: active `0.6634`, shadow `0.6771`, phrase `0.6175`, shadow lead `0.0137`, phrase lead `-0.0596`
- Score winner vs surface-pattern winner: `shadow` / `shadow`
- Source active: `She watered the ___ on the windowsill.`
- Source shadow: `Hundreds of workers left the chemical ___ at noon.`
- Source phrase: `They tried to ___ evidence in his office.`
- Nearest manual same-class row: `en-es:sentence-veto:plant:003` composite `0.1662`, bigram `0.0556`, neighbor `0.4` - The steel plant closed after the strike.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:plant:003 | shadow | abstain | 0.483005 | 0.576243 | The steel plant closed after the strike. |
| en-es:sentence-veto:plant:004 | shadow | abstain | 0.502487 | 0.606895 | Hundreds of workers left the chemical plant at noon. |

### `pilotrow:pilot_plant_planta:phrase_no_winner:001`

- Trigger/gold/outcome: `plant` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `high`
- Short read: The phrase shape is visible in the words, but the semantic score still did not let phrase evidence win.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, phrase_surface_pattern_visible_but_not_weighted_enough`
- LLM sentence: In the end, the whole plan was a plant to get more clicks.
- LLM context: `In the end, the whole plan was a ___ to get more clicks.`
- Scores: active `0.5957`, shadow `0.5834`, phrase `0.5721`, shadow lead `-0.0123`, phrase lead `-0.0236`
- Score winner vs surface-pattern winner: `active` / `phrase`
- Source active: `She watered the ___ on the windowsill.`
- Source shadow: `The steel ___ closed after the strike.`
- Source phrase: `They tried to ___ evidence in his office.`
- Nearest manual same-class row: `en-es:sentence-veto:plant:005` composite `0.0857`, bigram `0.0`, neighbor `0.1429` - They tried to plant evidence in his office.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:plant:005 | none | abstain | 0.513267 | 0.513748 | They tried to plant evidence in his office. |

### `pilotrow:pilot_board_tablero:positive_active:001`

- Trigger/gold/outcome: `board` / `positive_active` / `positive_abstain`
- Failure class: `positive_overblocked_by_phrase_prototype`
- Diagnosis confidence: `high`
- Short read: The LLM positive row is short or generic enough that phrase evidence beats it.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: New board game guide posted today.
- LLM context: `New ___ game guide posted today.`
- Scores: active `0.5856`, shadow `0.5394`, phrase `0.644`, shadow lead `-0.0463`, phrase lead `0.0584`
- Score winner vs surface-pattern winner: `phrase` / `active`
- Source active: `She folded the ___ after the game ended.`
- Source shadow: `The ___ approved the merger on Tuesday.`
- Source phrase: `Are you on ___ with the revised plan?`
- Nearest manual same-class row: `en-es:sentence-veto:board:002` composite `0.05`, bigram `0.0`, neighbor `0.0` - She folded the board after the game ended.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:board:001 | active | replace | 0.568637 | 0.534764 | He arranged the pieces on the board before the lesson began. |
| en-es:sentence-veto:board:002 | active | replace | 0.625082 | 0.512886 | She folded the board after the game ended. |

### `pilotrow:pilot_check_cheque:shadow_negative:001`

- Trigger/gold/outcome: `check` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, shadow_negative_was_scored_as_active_like, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: At the gate, the final check clears the bag.
- LLM context: `At the gate, the final ___ clears the bag.`
- Scores: active `0.7607`, shadow `0.6082`, phrase `0.6`, shadow lead `-0.1526`, phrase lead `-0.1608`
- Score winner vs surface-pattern winner: `active` / `active`
- Source active: `The ___ cleared after the holiday weekend.`
- Source shadow: `Please ___ the figures one more time.`
- Source phrase: `You should ___ out the new exhibit downtown.`
- Nearest manual same-class row: `en-es:sentence-veto:check:004` composite `0.075`, bigram `0.0`, neighbor `0.2` - Technicians check the pressure every hour.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:check:003 | shadow | abstain | 0.542255 | 0.597344 | Please check the figures one more time. |
| en-es:sentence-veto:check:004 | shadow | abstain | 0.511134 | 0.64983 | Technicians check the pressure every hour. |

### `pilotrow:pilot_check_cheque:shadow_negative:002`

- Trigger/gold/outcome: `check` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, shadow_negative_was_scored_as_active_like, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: The server logs flagged a security check after the failed login attempts.
- LLM context: `The server logs flagged a security ___ after the failed login attempts.`
- Scores: active `0.6459`, shadow `0.5043`, phrase `0.4395`, shadow lead `-0.1416`, phrase lead `-0.2064`
- Score winner vs surface-pattern winner: `active` / `shadow`
- Source active: `He signed the ___ before mailing the rent.`
- Source shadow: `Technicians ___ the pressure every hour.`
- Source phrase: `You should ___ out the new exhibit downtown.`
- Nearest manual same-class row: `en-es:sentence-veto:check:004` composite `0.0609`, bigram `0.0`, neighbor `0.1667` - Technicians check the pressure every hour.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:check:003 | shadow | abstain | 0.542255 | 0.597344 | Please check the figures one more time. |
| en-es:sentence-veto:check:004 | shadow | abstain | 0.511134 | 0.64983 | Technicians check the pressure every hour. |

### `pilotrow:pilot_check_cheque:phrase_no_winner:001`

- Trigger/gold/outcome: `check` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: Check the box below to continue, then review the form before you submit it.
- LLM context: `___ the box below to continue, then review the form before you submit it.`
- Scores: active `0.6063`, shadow `0.5874`, phrase `0.6035`, shadow lead `-0.0189`, phrase lead `-0.0028`
- Score winner vs surface-pattern winner: `active` / `shadow`
- Source active: `The ___ cleared after the holiday weekend.`
- Source shadow: `Please ___ the figures one more time.`
- Source phrase: `You should ___ out the new exhibit downtown.`
- Nearest manual same-class row: `en-es:sentence-veto:check:005` composite `0.0794`, bigram `0.0`, neighbor `0.2` - You should check out the new exhibit downtown.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:check:005 | none | abstain | 0.524828 | 0.63159 | You should check out the new exhibit downtown. |

### `pilotrow:pilot_branch_sucursal:shadow_negative:002`

- Trigger/gold/outcome: `branch` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, shadow_negative_was_scored_as_active_like`
- LLM sentence: The database query returned a branch of the decision tree after the latest update.
- LLM context: `The database query returned a ___ of the decision tree after the latest update.`
- Scores: active `0.6022`, shadow `0.5855`, phrase `0.487`, shadow lead `-0.0167`, phrase lead `-0.1152`
- Score winner vs surface-pattern winner: `active` / `shadow`
- Source active: `She submitted the paperwork at the ___ office.`
- Source shadow: `A bird landed on the highest ___ of the oak.`
- Source phrase: `The startup plans to ___ out into tutoring.`
- Nearest manual same-class row: `en-es:sentence-veto:branch:003` composite `0.1833`, bigram `0.1`, neighbor `0.4` - A bird landed on the highest branch of the oak.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:branch:003 | shadow | abstain | 0.582154 | 0.72092 | A bird landed on the highest branch of the oak. |
| en-es:sentence-veto:branch:004 | shadow | abstain | 0.525142 | 0.660264 | The storm snapped a heavy branch in the yard. |

### `pilotrow:pilot_file_archivo:positive_active:001`

- Trigger/gold/outcome: `file` / `positive_active` / `positive_abstain`
- Failure class: `positive_overblocked_by_shadow_score`
- Diagnosis confidence: `high`
- Short read: The LLM positive row is generic enough that shadow evidence beats it.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, positive_sentence_was_generic_enough_for_shadow_evidence_to_win`
- LLM sentence: The clerk opened the file after lunch.
- LLM context: `The clerk opened the ___ after lunch.`
- Scores: active `0.5517`, shadow `0.6937`, phrase `0.644`, shadow lead `0.142`, phrase lead `-0.0496`
- Score winner vs surface-pattern winner: `shadow` / `active`
- Source active: `The ___ was corrupted after the download.`
- Source shadow: `The jeweler picked up a fine ___ from the bench.`
- Source phrase: `They will ___ the complaint tomorrow morning.`
- Nearest manual same-class row: `en-es:sentence-veto:file:002` composite `0.1496`, bigram `0.0909`, neighbor `0.1667` - The file was corrupted after the download.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:file:001 | active | replace | 0.701831 | 0.536724 | I uploaded the file to the shared folder. |
| en-es:sentence-veto:file:002 | active | replace | 0.633334 | 0.55112 | The file was corrupted after the download. |

### `pilotrow:pilot_play_obra:shadow_negative:002`

- Trigger/gold/outcome: `play` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, shadow_negative_was_scored_as_active_like, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: The server logs show a failed play in the deployment pipeline.
- LLM context: `The server logs show a failed ___ in the deployment pipeline.`
- Scores: active `0.5926`, shadow `0.4652`, phrase `0.5536`, shadow lead `-0.1274`, phrase lead `-0.039`
- Score winner vs surface-pattern winner: `active` / `active`
- Source active: `The ___ opened last night.`
- Source shadow: `The children ___ outside after school.`
- Source phrase: `The scandal will ___ out over several weeks.`
- Nearest manual same-class row: `en-es:sentence-veto:play:003` composite `0.0565`, bigram `0.0`, neighbor `0.1429` - The children play outside after school.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:play:003 | shadow | abstain | 0.585624 | 0.627689 | The children play outside after school. |
| en-es:sentence-veto:play:004 | shadow | abstain | 0.519713 | 0.592138 | She likes to play chess online. |

### `pilotrow:pilot_play_obra:phrase_no_winner:001`

- Trigger/gold/outcome: `play` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_also_have_failures, scorer_chose_active_evidence_over_blocker, phrase_prototype_did_not_cover_this_expression_strongly_enough, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: At the end of the article, the play on words made the headline memorable.
- LLM context: `At the end of the article, the ___ on words made the headline memorable.`
- Scores: active `0.7199`, shadow `0.5906`, phrase `0.6376`, shadow lead `-0.1293`, phrase lead `-0.0823`
- Score winner vs surface-pattern winner: `active` / `active`
- Source active: `They praised the ___ in reviews.`
- Source shadow: `The children ___ outside after school.`
- Source phrase: `The scandal will ___ out over several weeks.`
- Nearest manual same-class row: `en-es:sentence-veto:play:005` composite `0.0156`, bigram `0.0`, neighbor `0.0` - The scandal will play out over several weeks.
- Manual same-class summary: `1` rows, `1` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:play:005 | none | replace | 0.559147 | 0.4937 | The scandal will play out over several weeks. |

### `pilotrow:pilot_report_informe:positive_active:001`

- Trigger/gold/outcome: `report` / `positive_active` / `positive_abstain`
- Failure class: `positive_overblocked_by_phrase_prototype`
- Diagnosis confidence: `high`
- Short read: The manual same-class rows already expose a similar weakness, so this is not purely an LLM-data regression.
- Notes: `same_family_manual_matching_rows_also_have_failures, surface_pattern_points_to_different_source_than_score_winner, positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: The final report from the audit is now online.
- LLM context: `The final ___ from the audit is now online.`
- Scores: active `0.5833`, shadow `0.5841`, phrase `0.6469`, shadow lead `0.0008`, phrase lead `0.0627`
- Score winner vs surface-pattern winner: `phrase` / `active`
- Source active: `The ___ was delayed until Friday.`
- Source shadow: `Analysts ___ slower growth this quarter.`
- Source phrase: `Please ___ back after the conference.`
- Nearest manual same-class row: `en-es:sentence-veto:report:001` composite `0.075`, bigram `0.0`, neighbor `0.2` - The report arrived this morning.
- Manual same-class summary: `2` rows, `2` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:report:001 | active | abstain | 0.567612 | 0.615538 | The report arrived this morning. |
| en-es:sentence-veto:report:002 | active | abstain | 0.50444 | 0.574947 | The report was delayed until Friday. |

### `pilotrow:pilot_report_informe:positive_active:002`

- Trigger/gold/outcome: `report` / `positive_active` / `positive_abstain`
- Failure class: `positive_overblocked_by_phrase_prototype`
- Diagnosis confidence: `high`
- Short read: The manual same-class rows already expose a similar weakness, so this is not purely an LLM-data regression.
- Notes: `same_family_manual_matching_rows_also_have_failures, surface_pattern_points_to_different_source_than_score_winner, positive_sentence_was_short_or_generic_enough_for_phrase_prototype_to_win`
- LLM sentence: After the audit team finished its review, the final report was posted on the compliance portal.
- LLM context: `After the audit team finished its review, the final ___ was posted on the compliance portal.`
- Scores: active `0.6006`, shadow `0.6085`, phrase `0.6627`, shadow lead `0.0079`, phrase lead `0.0543`
- Score winner vs surface-pattern winner: `phrase` / `active`
- Source active: `The ___ was delayed until Friday.`
- Source shadow: `Analysts ___ slower growth this quarter.`
- Source phrase: `Please ___ back after the conference.`
- Nearest manual same-class row: `en-es:sentence-veto:report:002` composite `0.1576`, bigram `0.0526`, neighbor `0.4` - The report was delayed until Friday.
- Manual same-class summary: `2` rows, `2` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:report:001 | active | abstain | 0.567612 | 0.615538 | The report arrived this morning. |
| en-es:sentence-veto:report:002 | active | abstain | 0.50444 | 0.574947 | The report was delayed until Friday. |

### `pilotrow:pilot_report_informe:shadow_negative:001`

- Trigger/gold/outcome: `report` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_shadow_lead_below_threshold`
- Diagnosis confidence: `medium`
- Short read: The same-family manual examples look easier or more directly aligned with the available evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: After the storm, the report from the engine room was a loud bang.
- LLM context: `After the storm, the ___ from the engine room was a loud bang.`
- Scores: active `0.6391`, shadow `0.6566`, phrase `0.6078`, shadow lead `0.0175`, phrase lead `-0.0488`
- Score winner vs surface-pattern winner: `shadow` / `active`
- Source active: `The ___ arrived this morning.`
- Source shadow: `Witnesses ___ heavy rain near the coast.`
- Source phrase: `Please ___ back after the conference.`
- Nearest manual same-class row: `en-es:sentence-veto:report:003` composite `0.0179`, bigram `0.0`, neighbor `0.0` - Witnesses report heavy rain near the coast.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:report:003 | shadow | abstain | 0.560694 | 0.588795 | Witnesses report heavy rain near the coast. |
| en-es:sentence-veto:report:004 | shadow | abstain | 0.603758 | 0.620791 | Analysts report slower growth this quarter. |

### `pilotrow:pilot_report_informe:phrase_no_winner:001`

- Trigger/gold/outcome: `report` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `high`
- Short read: The phrase shape is visible in the words, but the semantic score still did not let phrase evidence win.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, phrase_surface_pattern_visible_but_not_weighted_enough`
- LLM sentence: The report back from the field arrived late, but the team still finished the update.
- LLM context: `The ___ back from the field arrived late, but the team still finished the update.`
- Scores: active `0.7502`, shadow `0.6422`, phrase `0.6528`, shadow lead `-0.108`, phrase lead `-0.0974`
- Score winner vs surface-pattern winner: `active` / `phrase`
- Source active: `The ___ was delayed until Friday.`
- Source shadow: `Analysts ___ slower growth this quarter.`
- Source phrase: `Please ___ back after the conference.`
- Nearest manual same-class row: `en-es:sentence-veto:report:005` composite `0.1135`, bigram `0.0556`, neighbor `0.2` - Please report back after the conference.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:report:005 | none | abstain | 0.636495 | 0.648406 | Please report back after the conference. |

### `pilotrow:pilot_order_pedido:shadow_negative:001`

- Trigger/gold/outcome: `order` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, shadow_negative_was_scored_as_active_like, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: New order restored in the court after the hearing.
- LLM context: `New ___ restored in the court after the hearing.`
- Scores: active `0.5973`, shadow `0.5684`, phrase `0.4649`, shadow lead `-0.0288`, phrase lead `-0.1323`
- Score winner vs surface-pattern winner: `active` / `active`
- Source active: `The ___ shipped this morning.`
- Source shadow: `Commanders ___ the troops forward.`
- Source phrase: `We should ___ out tonight.`
- Nearest manual same-class row: `en-es:sentence-veto:order:004` composite `0.025`, bigram `0.0`, neighbor `0.0` - Commanders order the troops forward.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:order:003 | shadow | abstain | 0.533473 | 0.641595 | Teachers order the class to remain silent. |
| en-es:sentence-veto:order:004 | shadow | abstain | 0.594271 | 0.685274 | Commanders order the troops forward. |

### `pilotrow:pilot_order_pedido:shadow_negative:002`

- Trigger/gold/outcome: `order` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `high`
- Short read: The scorer chose active evidence over the intended blocker evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, scorer_chose_active_evidence_over_blocker, shadow_negative_was_scored_as_active_like, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: The database query returned rows in alphabetical order.
- LLM context: `The database query returned rows in alphabetical ___`
- Scores: active `0.5523`, shadow `0.5087`, phrase `0.5142`, shadow lead `-0.0436`, phrase lead `-0.0381`
- Score winner vs surface-pattern winner: `active` / `active`
- Source active: `The ___ shipped this morning.`
- Source shadow: `Commanders ___ the troops forward.`
- Source phrase: `We should ___ out tonight.`
- Nearest manual same-class row: `en-es:sentence-veto:order:004` composite `0.025`, bigram `0.0`, neighbor `0.0` - Commanders order the troops forward.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:order:003 | shadow | abstain | 0.533473 | 0.641595 | Teachers order the class to remain silent. |
| en-es:sentence-veto:order:004 | shadow | abstain | 0.594271 | 0.685274 | Commanders order the troops forward. |

### `pilotrow:pilot_order_pedido:phrase_no_winner:001`

- Trigger/gold/outcome: `order` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `medium`
- Short read: The LLM phrase/no-winner expression is not well covered by the available phrase prototype.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: The app loaded in order, but the video still buffered for several minutes.
- LLM context: `The app loaded in ___ but the video still buffered for several minutes.`
- Scores: active `0.5249`, shadow `0.5303`, phrase `0.4784`, shadow lead `0.0054`, phrase lead `-0.0519`
- Score winner vs surface-pattern winner: `shadow` / `active`
- Source active: `The ___ shipped this morning.`
- Source shadow: `Teachers ___ the class to remain silent.`
- Source phrase: `We should ___ out tonight.`
- Nearest manual same-class row: `en-es:sentence-veto:order:005` composite `0.0167`, bigram `0.0`, neighbor `0.0` - We should order out tonight.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:order:005 | none | abstain | 0.546349 | 0.582953 | We should order out tonight. |

### `pilotrow:pilot_match_partido:shadow_negative:001`

- Trigger/gold/outcome: `match` / `shadow_negative` / `negative_allow`
- Failure class: `shadow_negative_active_score_dominated`
- Diagnosis confidence: `medium`
- Short read: The same-family manual examples look easier or more directly aligned with the available evidence.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, shadow_negative_was_scored_as_active_like`
- LLM sentence: Headline: a perfect match for the frame, with the finish finally aligned.
- LLM context: `Headline: a perfect ___ for the frame, with the finish finally aligned.`
- Scores: active `0.672`, shadow `0.5893`, phrase `0.697`, shadow lead `-0.0828`, phrase lead `0.0249`
- Score winner vs surface-pattern winner: `phrase` / `active`
- Source active: `The ___ ended after extra time.`
- Source shadow: `He dropped the burning ___ into the sink.`
- Source phrase: `These curtains ___ the sofa perfectly.`
- Nearest manual same-class row: `en-es:sentence-veto:match:003` composite `0.1026`, bigram `0.0`, neighbor `0.3333` - She lit a match beside the stove.
- Manual same-class summary: `2` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:match:003 | shadow | abstain | 0.496029 | 0.733509 | She lit a match beside the stove. |
| en-es:sentence-veto:match:004 | shadow | abstain | 0.537859 | 0.611569 | He dropped the burning match into the sink. |

### `pilotrow:pilot_watch_reloj:phrase_no_winner:001`

- Trigger/gold/outcome: `watch` / `phrase_no_winner` / `negative_allow`
- Failure class: `phrase_no_winner_phrase_score_not_dominant`
- Diagnosis confidence: `medium`
- Short read: The LLM phrase/no-winner expression is not well covered by the available phrase prototype.
- Notes: `same_family_manual_matching_rows_passed_under_control, surface_pattern_points_to_different_source_than_score_winner, phrase_prototype_did_not_cover_this_expression_strongly_enough, llm_sentence_is_lexically_far_from_manual_same_class_examples`
- LLM sentence: Before the meeting starts, watch your step on the wet tiles.
- LLM context: `Before the meeting starts, ___ your step on the wet tiles.`
- Scores: active `0.6263`, shadow `0.6683`, phrase `0.6531`, shadow lead `0.042`, phrase lead `-0.0152`
- Score winner vs surface-pattern winner: `shadow` / `active`
- Source active: `He adjusted his ___ strap before the interview.`
- Source shadow: `Guards ___ the entrance through the night.`
- Source phrase: `You should ___ out for black ice on the bridge.`
- Nearest manual same-class row: `en-es:sentence-veto:watch:005` composite `0.059`, bigram `0.0556`, neighbor `0.0` - You should watch out for black ice on the bridge.
- Manual same-class summary: `1` rows, `0` manual failures under control

| Manual case | Gold | Predicted | Active | Shadow | Sentence |
| --- | --- | --- | ---: | ---: | --- |
| en-es:sentence-veto:watch:005 | none | abstain | 0.551326 | 0.618814 | You should watch out for black ice on the bridge. |
