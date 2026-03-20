# SRS Journey Harness

- Status: WARN
- Findings: pass=7 warn=1 fail=0
- Scenario: `en-ja_core_journey_v1`
- Pair: `en-ja`
- Lane: `deterministic_core_journey`
- Contract mode: `observe_current_behavior`
- Generated at: `2026-03-20T22:53:12.080180+00:00`

## Phases

### bootstrap_publish
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=alpha, beta, gamma; out=none
- Due delta: in=alpha, beta, gamma; out=none
- Published delta: in=alpha, beta, gamma; out=none
- Events applied: feedback=0 exposure=0
- Published not due: none

### baseline_observe
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=none; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: none

### high_retention_growth
- Counts: admitted=5 due=3 published=5
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=delta, epsilon; out=none
- Due delta: in=delta, epsilon; out=alpha, beta
- Published delta: in=delta, epsilon; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta

### low_retention_pause
- Counts: admitted=5 due=2 published=5
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=gamma
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta, gamma

### recovery_resume
- Counts: admitted=7 due=2 published=7
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=eta, zeta; out=none
- Due delta: in=eta, zeta; out=delta, epsilon
- Published delta: in=eta, zeta; out=none
- Events applied: feedback=8 exposure=0
- Published not due: alpha, beta, delta, epsilon, gamma

### fade_check
- Counts: admitted=7 due=3 published=7
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=gamma; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: alpha, beta, delta, epsilon

## Signal Log

- Event count: 24
- Unique lemmas: 5
- Event types: feedback=24 exposure=0
- Last event at: `2026-03-24T09:07:00+00:00`

## Cohort Check

- Stable cohort due in final phase: none
- Difficult cohort due in final phase: gamma

## Actionable Findings

1. [WARN] [high_retention_growth] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`: Published set is broader than the due subset in the current journey run.
   - phase=high_retention_growth admitted=5 due=3 published=5
