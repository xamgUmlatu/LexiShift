# en-es Semantic Veto Bound Ladder: Wave7 Residuals

- Status: `review`
- Decision: `bounds_reference_only_llm_lane_unmeasured`
- Generated: `2026-04-30T22:27:26Z`
- Research only: `true`

## Summary

- Locked cases: `48`
- Current correct cases: `39`
- Current accuracy: `81.25%`
- Current harmful replacements: `7`
- Current false abstains: `2`
- Score-visible residuals: `7`
- Residuals likely needing better evidence/scoring: `2`
- Existing runtime-shaped sweep pass count: `0`

## Bound Ladder

| Bound | Value | Meaning |
| --- | --- | --- |
| `end_to_end_lower_bound` | `81.25%` accuracy, `7` harm, `2` false abstain | This is the best actually observed current wave7 phrase-control triage result, not a production acceptance target. |
| `current_evidence_upper_bound` | `95.83%` optimistic | This is an optimistic score-visibility ceiling. It assumes a future rule can recover all score-visible residuals without causing regressions. Existing wave7 sweeps do not prove such a rule exists. |
| `admitted_evidence_presence_bound` | `9` / `9` residuals have admitted gold-lane evidence | This checks whether a relevant admitted evidence field is non-empty. It is not a raw-source inventory audit and it does not prove the wording is strong enough. |
| `runtime_policy_family_bound` | `0` combined passing policies | The tested runtime-shaped policy families have no combined pass. This is a negative signal for simple scalar tuning, not a formal proof over all possible runtime-compatible policies. |
| `llm_pipeline_bound` | `not_measured` | Planned LLM-generated evidence is not included in the current bound value. Measure it separately with locked cases, generation prompts, admission, leakage filters, sense checks, scoring, and downstream validation all included. |
| `oracle_evidence_bound` | `100.00%` diagnostic optimistic | This is diagnostic only. It says the residuals look evidence/guard-fixable, but it does not prove the planned LLM pipeline can generate the needed rows. |

## Case Bounds

| Case | Error | Class | Evidence Lane | Evidence Present | Score Visible | Representation | LLM Opportunity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `harmful_replace` | `shadow_quantity_evidence_underweighted` | `shadow` | `true` | `true` | `score_visible_but_policy_failed` | `generation_may_help_but_policy_guard_is_primary` |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `false_abstain` | `shadow_overlap_overblocks_active` | `active` | `true` | `false` | `evidence_present_but_not_score_visible` | `generate_stronger_contrastive_active_shadow_evidence` |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `false_abstain` | `phrase_control_overlap_overblocks_active` | `active` | `true` | `false` | `evidence_present_but_not_score_visible` | `generate_stronger_contrastive_active_shadow_evidence` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `phrase_control` | `true` | `true` | `phrase_signal_present_but_guard_failed` | `generate_exact_no_winner_phrase_evidence_and_guard_examples` |

## Interpretation

- The current wave7 result is a lower bound, not an acceptable target: 7 harmful replacements and 2 false abstains remain.
- 7 residuals have the gold signal visible in current scores; these are candidates for guard or decision-rule repair.
- 2 residuals do not expose the gold signal under the current score shape; these point toward better evidence, scoring, or aggregation.
- The LLM pipeline bound is intentionally not measured yet, so generated data should not be counted in the current acceptance target.

## Next Steps

- Treat the current wave7 result as the observed lower bound, not the acceptable goal.
- Keep LLM-generated evidence out of acceptance estimates until an LLM-pipeline bound is run.
- Do not claim scalar policy tuning can close the gap; existing runtime-shaped sweeps have zero combined passing policies.
- Prioritize evidence/scorer work for residuals whose gold signal is not visible in current scores.
- Run a deeper raw-source and representation audit before assuming the problem is missing source coverage.
- Prototype the LLM-pipeline bound separately: generate evidence on locked residual cases, run admission and leakage checks, then rerun heldout validation.

## Limitations

- `research_only_not_quality_gate`
- `uses_existing_wave7_residual_artifacts_only`
- `llm_pipeline_not_measured`
- `oracle_evidence_bound_is_diagnostic_not_promotion_evidence`
- `score_visibility_is_a_heuristic_not_a_formal_language_bound`
