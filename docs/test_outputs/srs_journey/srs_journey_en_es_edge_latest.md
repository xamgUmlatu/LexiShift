# SRS Journey Harness

- Status: WARN
- Findings: pass=4 warn=1 fail=0
- Scenario: `en-es_edge_behaviors_v1`
- Pair: `en-es`
- Lane: `deterministic_edge_behaviors`
- Contract mode: `observe_current_behavior`
- Generated at: `2026-03-21T01:02:39.519395+00:00`

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

### duplicate_feedback_burst
- Counts: admitted=3 due=2 published=3
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=none; out=casa
- Published delta: in=none; out=none
- Events applied: feedback=2 exposure=0
- Published not due: casa
- Due not published: none

### low_retention_seed
- Counts: admitted=3 due=1 published=3
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=hora
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: casa, hora
- Due not published: none

### exposure_only_pause_probe
- Counts: admitted=3 due=1 published=3
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=6
- Published not due: casa, hora
- Due not published: none

### final_observe
- Counts: admitted=3 due=2 published=3
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=hora; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: casa
- Due not published: none

## Signal Log

- Event count: 16
- Unique lemmas: 3
- Event types: feedback=10 exposure=6
- Last event at: `2026-03-23T09:05:00+00:00`

## Cohort Check

- Stable cohort due in final phase: libro
- Difficult cohort due in final phase: hora

## Actionable Findings

1. [WARN] [duplicate_feedback_burst] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`: Published set is broader than the due subset in the current journey run.
   - phase=duplicate_feedback_burst admitted=3 due=2 published=3
