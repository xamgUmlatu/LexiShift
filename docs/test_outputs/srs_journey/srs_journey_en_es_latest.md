# SRS Journey Harness

- Status: WARN
- Findings: pass=7 warn=1 fail=0
- Scenario: `en-es_core_journey_v1`
- Pair: `en-es`
- Lane: `deterministic_core_journey`
- Contract mode: `observe_current_behavior`
- Generated at: `2026-03-21T01:02:38.144673+00:00`

## Phases

### bootstrap_publish
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=casa, hora, libro; out=none
- Due delta: in=casa, hora, libro; out=none
- Published delta: in=casa, hora, libro; out=none
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
- Counts: admitted=5 due=3 published=5
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=campo, madre; out=none
- Due delta: in=campo, madre; out=casa, libro
- Published delta: in=campo, madre; out=none
- Events applied: feedback=8 exposure=0
- Published not due: casa, libro
- Due not published: none

### low_retention_pause
- Counts: admitted=5 due=2 published=5
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=hora
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: casa, hora, libro
- Due not published: none

### recovery_resume
- Counts: admitted=7 due=2 published=7
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=mesa, ventana; out=none
- Due delta: in=mesa, ventana; out=campo, madre
- Published delta: in=mesa, ventana; out=none
- Events applied: feedback=8 exposure=0
- Published not due: campo, casa, hora, libro, madre
- Due not published: none

### fade_check
- Counts: admitted=7 due=3 published=7
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=hora; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: campo, casa, libro, madre
- Due not published: none

## Signal Log

- Event count: 24
- Unique lemmas: 5
- Event types: feedback=24 exposure=0
- Last event at: `2026-03-24T09:07:00+00:00`

## Cohort Check

- Stable cohort due in final phase: none
- Difficult cohort due in final phase: hora

## Actionable Findings

1. [WARN] [high_retention_growth] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`: Published set is broader than the due subset in the current journey run.
   - phase=high_retention_growth admitted=5 due=3 published=5
