# Rulegen Quality Gate (en-de Kaikki register latest)

- Status: FAIL
- Findings: pass=14 warn=2 fail=1
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json`
- Policy JSON: `docs/test_inputs/rulegen_quality_policy.json`
- Pair scope: `en-de`

## Actionable Findings
1. [WARN] `DELTA_SCOPE_BASELINE_MISSING`: Scoped pair 'en-de' has no baseline metrics; skipping delta checks.
2. [FAIL] `SATURATION_TOP_VECTOR_FAIL`: Pair 'en-de' top metric vector share=1.000 exceeds fail threshold>0.900.
   - run_count=2 unique_vectors=1 top_count=2
3. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-de' unique metric vectors=1 below expected minimum=5.
