# Rulegen Quality Gate

- Status: FAIL
- Findings: pass=13 warn=6 fail=2
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Policy JSON: `docs/test_inputs/rulegen_quality_policy.json`

## Actionable Findings
1. [WARN] `BENCHMARK_RECOMMENDED_PAIRS_MISSING`: Recommended benchmark pairs are missing (not yet gated).
   - en-de, en-ja, es-en
2. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-es'.
   - top1_accuracy=0.9375 below min_top1_accuracy=0.9500
   - forbidden_top1_rate=0.0625 above max_forbidden_top1_rate=0.0500
3. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-ja'; skipping its quality floor checks.
4. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-de'; skipping its quality floor checks.
5. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'es-en'; skipping its quality floor checks.
6. [FAIL] `DELTA_BUDGET_BREACH`: Delta budgets failed for pair 'en-es'.
   - top1_accuracy drop=0.0625 exceeds budget=0.0000
   - forbidden_top1_rate increase=0.0625 exceeds budget=0.0000
   - forbidden_any_rate increase=0.0625 exceeds budget=0.0000
7. [WARN] `SATURATION_TOP_VECTOR_WARN`: Pair 'en-es' top metric vector share=0.500 indicates low sensitivity (warn threshold>=0.500).
   - run_count=4 unique_vectors=2 top_count=2
8. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-es' unique metric vectors=2 below expected minimum=5.
