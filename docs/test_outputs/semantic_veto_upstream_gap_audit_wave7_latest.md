# en-es Wave7 Upstream Gap Audit

- Status: `review`
- Decision: `upstream_work_required_before_acceptance_target`
- Generated: `2026-04-30T23:26:08Z`
- Research only: `true`

## Summary

- Residual cases audited: `9`
- Fixed by best no-regression guard: `3`
- Still failing after best no-regression guard: `6`
- Current-evidence ceiling status: `partial_headroom_but_optimistic_ceiling_collapsed`
- Admission rows: `326`
- Source-class frame rows: `90`
- Phrase-control candidate rows: `179`

## Bottleneck Counts

| Bottleneck | Cases |
| --- | ---: |
| `evidence_representation_or_scorer_gap` | 2 |
| `general_guard_headroom_confirmed` | 3 |
| `guard_signal_collides_with_valid_active_replace` | 3 |
| `shadow_signal_visible_but_guard_threshold_insufficient` | 1 |

## Class Summaries

| Bottleneck | Cases | Triggers | Failure Classes | Next Actions |
| --- | ---: | --- | --- | --- |
| `evidence_representation_or_scorer_gap` | 2 | `fix`, `meet` | `phrase_control_overlap_overblocks_active`, `shadow_overlap_overblocks_active` | Audit raw source wording and try stronger contrastive evidence or scorer aggregation before policy tuning. |
| `general_guard_headroom_confirmed` | 3 | `cast`, `squeeze`, `stretch` | `surface_rescue_leaks_when_phrase_control_close`, `surface_rescue_overrode_dominant_phrase_control` | Keep as diagnostic headroom and confirm on a broader locked suite before policy promotion. |
| `guard_signal_collides_with_valid_active_replace` | 3 | `foul`, `score`, `wrong` | `surface_rescue_leaks_when_phrase_control_close`, `surface_rescue_overrode_dominant_phrase_control` | Improve phrase/no-winner evidence specificity or add a separately validated no-winner guard signal. |
| `shadow_signal_visible_but_guard_threshold_insufficient` | 1 | `gross` | `shadow_quantity_evidence_underweighted` | Strengthen quantity/commercial source evidence or test a non-trigger-specific quantity-frame feature. |

## Case Audits

| Case | Error | Score Visible | No-Regression Fix | Bottleneck | Source Rows | Phrase Rows | Next Action |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `harmful_replace` | `true` | `false` | `shadow_signal_visible_but_guard_threshold_insufficient` | 7 | 9 | Strengthen quantity/commercial source evidence or test a non-trigger-specific quantity-frame feature. |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `false_abstain` | `false` | `false` | `evidence_representation_or_scorer_gap` | 10 | 12 | Audit raw source wording and try stronger contrastive evidence or scorer aggregation before policy tuning. |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `false_abstain` | `false` | `false` | `evidence_representation_or_scorer_gap` | 6 | 12 | Audit raw source wording and try stronger contrastive evidence or scorer aggregation before policy tuning. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `harmful_replace` | `true` | `true` | `general_guard_headroom_confirmed` | 6 | 12 | Keep as diagnostic headroom and confirm on a broader locked suite before policy promotion. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `harmful_replace` | `true` | `false` | `guard_signal_collides_with_valid_active_replace` | 3 | 8 | Improve phrase/no-winner evidence specificity or add a separately validated no-winner guard signal. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `harmful_replace` | `true` | `true` | `general_guard_headroom_confirmed` | 6 | 12 | Keep as diagnostic headroom and confirm on a broader locked suite before policy promotion. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `harmful_replace` | `true` | `false` | `guard_signal_collides_with_valid_active_replace` | 9 | 12 | Improve phrase/no-winner evidence specificity or add a separately validated no-winner guard signal. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `harmful_replace` | `true` | `true` | `general_guard_headroom_confirmed` | 7 | 12 | Keep as diagnostic headroom and confirm on a broader locked suite before policy promotion. |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `harmful_replace` | `true` | `false` | `guard_signal_collides_with_valid_active_replace` | 6 | 12 | Improve phrase/no-winner evidence specificity or add a separately validated no-winner guard signal. |

## Interpretation

- The current-evidence guard sweep found real but limited headroom: 3 residuals are fixed by the best no-regression guard, leaving 6 residuals for upstream work.
- The remaining cases are not simply missing admitted evidence: the audit sees source rows and phrase rows, but the score/guard representation is not sufficiently separable.
- The next useful target is not another scalar sweep. It is evidence wording, raw-source/representation review, scorer aggregation, or an explicitly measured LLM-pipeline bound.

## Next Steps

- Use this audit to choose upstream work, not to promote a runtime policy.
- First inspect the evidence/scorer gap cases where gold evidence is admitted but not score-visible.
- Then design a phrase/no-winner representation or guard signal that avoids regressing active replace rows.
- Only after those two lanes should an LLM-pipeline bound be run against locked residual cases.

## Limitations

- `research_only_not_promotion_evidence`
- `raw_source_availability_is_inferred_from_existing_source_reports`
- `does_not_run_new_scorers_or_generate_new_llm_rows`
- `case_classification_is_for_work_routing_not_runtime_policy`
