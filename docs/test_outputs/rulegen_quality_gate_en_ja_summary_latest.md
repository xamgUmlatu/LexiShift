# Rulegen Quality Gate (en-ja latest)

- Status: WARN
- Findings: pass=14 warn=2 fail=0
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
- Policy JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_quality_policy.json`
- Pair scope: `en-ja`

## Actionable Findings
1. [WARN] `DELTA_SCOPE_BASELINE_MISSING`: Scoped pair 'en-ja' has no baseline metrics; skipping delta checks.
2. [WARN] `SATURATION_SINGLE_RUN_WARN`: Pair 'en-ja' has one benchmark run; metric-vector saturation cannot be evaluated.
   - run_count=1 unique_vectors=1 top_count=1
