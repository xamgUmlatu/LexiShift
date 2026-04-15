# SRS Quality Harness

- Status: WARN
- Findings: pass=15 warn=1 fail=0
- Fail on warn: no
- Synthetic pairs: en-ja, en-de

## Bootstrap Scenarios

### en-ja
- Store/Due/Published targets: 48/48/0
- Ruleset unique targets: 0
- Runtime artifacts: store=yes ruleset=yes snapshot=yes

### en-de
- Store/Due/Published targets: 48/48/48
- Ruleset unique targets: 48
- Runtime artifacts: store=yes ruleset=yes snapshot=yes

## Feedback Cycle

- high_retention_1: applied=yes, reason=`normal`, total_items=3, ruleset=3
- low_retention_pause: applied=no, reason=`retention_low`, total_items=3, ruleset=3
- high_retention_2: applied=yes, reason=`normal`, total_items=5, ruleset=5

## Actionable Findings

1. [WARN] [en-ja] `SRS_DUE_AWARE_PUBLISH_UNVERIFIED`: Published ruleset appears to cover admitted items beyond the due subset.
   - phase=high_retention_1 total_items=3 due_count=2 ruleset_count=3
