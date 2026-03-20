# SRS Journey Harness

- Status: WARN
- Findings: pass=8 warn=2 fail=0
- Scenario: `en-ja_real_publication_v1`
- Pair: `en-ja`
- Lane: `real_publication_journey`
- Contract mode: `observe_current_behavior`
- Generated at: `2026-03-20T22:56:32.156823+00:00`

## Phases

### bootstrap_publish
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=alpha, beta, gamma; out=none
- Due delta: in=alpha, beta, gamma; out=none
- Published delta: in=alpha, beta, gamma; out=none
- Events applied: feedback=0 exposure=0
- Published not due: none
- Due not published: none

### baseline_observe
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=none; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: none
- Due not published: none

### high_retention_growth
- Counts: admitted=5 due=3 published=3
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=delta, epsilon; out=none
- Due delta: in=delta, epsilon; out=alpha, beta
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta
- Due not published: delta, epsilon

### low_retention_pause
- Counts: admitted=5 due=2 published=3
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=gamma
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta, gamma
- Due not published: delta, epsilon

### recovery_resume
- Counts: admitted=7 due=2 published=3
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=eta, zeta; out=none
- Due delta: in=eta, zeta; out=delta, epsilon
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta, gamma
- Due not published: eta, zeta

### fade_check
- Counts: admitted=7 due=3 published=3
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=gamma; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: alpha, beta
- Due not published: eta, zeta

## Signal Log

- Event count: 24
- Unique lemmas: 5
- Event types: feedback=24 exposure=0
- Last event at: `2026-03-24T09:07:00+00:00`

## Cohort Check

- Stable cohort due in final phase: none
- Difficult cohort due in final phase: gamma

## Actionable Findings

1. [WARN] [high_retention_growth] `SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE`: Real publication left some due items unpublished in the observed journey phases.
   - phase=high_retention_growth due_not_published=delta,epsilon
2. [WARN] [low_retention_pause] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`: Published set is broader than the due subset in the current journey run.
   - phase=low_retention_pause admitted=5 due=2 published=3
