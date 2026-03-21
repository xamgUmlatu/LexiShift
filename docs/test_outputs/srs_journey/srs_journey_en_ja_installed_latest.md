# SRS Journey Harness

- Status: WARN
- Findings: pass=9 warn=2 fail=0
- Scenario: `en-ja_installed_data_journey_v1`
- Pair: `en-ja`
- Lane: `installed_resource_journey`
- Contract mode: `observe_current_behavior`
- Generated at: `2026-03-21T01:58:05.994418+00:00`

## Phases

### bootstrap_publish
- Counts: admitted=3 due=3 published=3
- Refresh: not requested
- Admitted delta: in=事, 時, 物; out=none
- Due delta: in=事, 時, 物; out=none
- Published delta: in=事, 時, 物; out=none
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
- Admitted delta: in=人, 無い; out=none
- Due delta: in=人, 無い; out=事, 物
- Published delta: in=人, 無い; out=none
- Events applied: feedback=8 exposure=0
- Published not due: 事, 物
- Due not published: none

### low_retention_pause
- Counts: admitted=5 due=2 published=5
- Refresh: applied=no reason=`retention_low`
- Admitted delta: in=none; out=none
- Due delta: in=none; out=時
- Published delta: in=none; out=none
- Events applied: feedback=8 exposure=0
- Published not due: 事, 時, 物
- Due not published: none

### recovery_resume
- Counts: admitted=7 due=2 published=6
- Refresh: applied=yes reason=`normal`
- Admitted delta: in=日本, 為る; out=none
- Due delta: in=日本, 為る; out=人, 無い
- Published delta: in=日本; out=none
- Events applied: feedback=8 exposure=0
- Published not due: 事, 人, 時, 無い, 物
- Due not published: 為る

### fade_check
- Counts: admitted=7 due=3 published=6
- Refresh: not requested
- Admitted delta: in=none; out=none
- Due delta: in=時; out=none
- Published delta: in=none; out=none
- Events applied: feedback=0 exposure=0
- Published not due: 事, 人, 無い, 物
- Due not published: 為る

## Signal Log

- Event count: 24
- Unique lemmas: 5
- Event types: feedback=24 exposure=0
- Last event at: `2026-03-24T09:07:00+00:00`

## Cohort Check

- Stable cohort due in final phase: none
- Difficult cohort due in final phase: 時

## Actionable Findings

1. [WARN] [recovery_resume] `SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE`: Real publication left some due items unpublished in the observed journey phases.
   - phase=recovery_resume due_not_published=為る
2. [WARN] [high_retention_growth] `SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED`: Published set is broader than the due subset in the current journey run.
   - phase=high_retention_growth admitted=5 due=3 published=5
