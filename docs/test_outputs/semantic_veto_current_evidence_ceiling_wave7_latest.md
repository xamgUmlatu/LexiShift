# en-es Wave7 Current-Evidence Ceiling Validation

- Status: `review`
- Decision: `current_evidence_ceiling_partially_supported`
- Generated: `2026-04-30T23:09:49Z`
- Research only: `true`
- Candidate policies: `445`

## Result

- Baseline: `39 / 48` correct, `7` harmful, `2` false abstain
- Optimistic current-evidence target: `46 / 48` correct
- Best no-regression policy: `surface_frame|phrase_lead>=0.05|shadow_lead>=0.05`
- Best no-regression result: `42 / 48` correct, `4` harmful, `2` false abstain
- Ceiling read: `partial_headroom_but_optimistic_ceiling_collapsed`

## Representative Policies

| Policy | Correct | Harm | False Abstain | Fixed | Regressed | Changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline_current_policy` | 39 | 7 | 2 | 0 | 0 | 0 |
| `surface_frame|nonactive_lead>=0.03` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|nonactive_lead>=0` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |

## Top Policies By Accuracy

| Policy | Correct | Harm | False Abstain | Fixed | Regressed | Changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `surface_frame|nonactive_lead>=0.03` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.03|shadow_lead>=0.005` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.03|shadow_lead>=0.01` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.04|shadow_lead>=0.005` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.04|shadow_lead>=0.01` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.005` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.01` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.06|shadow_lead>=0.005` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.06|shadow_lead>=0.01` | 42 | 1 | 5 | 6 | 3 | 9 |
| `surface_frame|phrase_lead>=0.07|shadow_lead>=0.005` | 42 | 1 | 5 | 6 | 3 | 9 |

## Top Zero-Harm Policies

| Policy | Correct | Harm | False Abstain | Fixed | Regressed | Changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `surface_frame|nonactive_lead>=0` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|nonactive_lead>=0.005` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0.005` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0.01` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0.015` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0.02` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.005|shadow_lead>=0.03` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.01|shadow_lead>=0` | 39 | 0 | 9 | 7 | 7 | 14 |
| `surface_frame|phrase_close<=0.01|shadow_lead>=0.005` | 39 | 0 | 9 | 7 | 7 | 14 |

## Top No-Regression Policies

| Policy | Correct | Harm | False Abstain | Fixed | Regressed | Changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_frame|phrase_lead>=0.06|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_frame|phrase_lead>=0.07|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_rescue|phrase_lead>=0.05|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_rescue|phrase_lead>=0.06|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_rescue|phrase_lead>=0.07|shadow_lead>=0.05` | 42 | 4 | 2 | 3 | 0 | 3 |
| `surface_frame|phrase_lead>=0.05` | 41 | 5 | 2 | 2 | 0 | 2 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.06` | 41 | 5 | 2 | 2 | 0 | 2 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.08` | 41 | 5 | 2 | 2 | 0 | 2 |
| `surface_frame|phrase_lead>=0.05|shadow_lead>=0.1` | 41 | 5 | 2 | 2 | 0 | 2 |

## Interpretation

- The optimistic ceiling would require 46 / 48 correct cases.
- The best no-regression guard only reaches 42 / 48 and fixes 3 / 7 score-visible residuals.
- Zero-harm guard policies exist in this sweep, but they trade away currently correct replace cases, so they do not validate the optimistic bound.

## Next Steps

- Do not treat the optimistic 46/48 current-evidence ceiling as validated.
- Use the no-regression policy as a diagnostic: it shows partial phrase/no-winner headroom but leaves harmful replacements.
- Move upstream for the remaining gap: raw-source, evidence representation, scoring, and LLM-pipeline bound work.

## Limitations

- `current_evidence_only_no_new_source_rows`
- `abstain_guard_sweep_only_does_not_recover_false_abstains_to_replace`
- `no_case_ids_no_trigger_specific_rules`
- `fixed_trace_research_only_not_runtime_policy`
