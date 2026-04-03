# Rulegen Quality Gate (en-de source frequency experiment)

- Status: FAIL
- Findings: pass=13 warn=3 fail=1
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.json`
- Policy JSON: `docs/test_inputs/rulegen_quality_policy.json`
- Pair scope: `en-de`

## Actionable Findings
1. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-de'.
   - top1_accuracy=0.6552 below min_top1_accuracy=0.8500
2. [WARN] `DELTA_SCOPE_BASELINE_MISSING`: Scoped pair 'en-de' has no baseline metrics; skipping delta checks.
3. [WARN] `SATURATION_TOP_VECTOR_WARN`: Pair 'en-de' top metric vector share=0.500 indicates low sensitivity (warn threshold>=0.500).
   - run_count=64 unique_vectors=4 top_count=32
4. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-de' unique metric vectors=4 below expected minimum=5.
