# Rulegen Quality Gate

- Status: FAIL
- Findings: pass=14 warn=0 fail=2
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Policy JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_quality_policy.json`
- Pair scope: `en-es`

## Actionable Findings
1. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-es'.
   - top1_accuracy=0.9062 below min_top1_accuracy=0.9500
   - avg_rules_per_target=3.0312 above max_avg_rules_per_target=3.0000
2. [FAIL] `DELTA_BUDGET_BREACH`: Delta budgets failed for pair 'en-es'.
   - top1_accuracy drop=0.0938 exceeds budget=0.0000
   - top3_recall drop=0.0312 exceeds budget=0.0000
   - forbidden_top1_rate increase=0.0156 exceeds budget=0.0000
   - forbidden_any_rate increase=0.0312 exceeds budget=0.0000
   - avg_rules_per_target increase=2.0312 exceeds budget=0.5000
