# Rulegen Quality Gate

- Status: FAIL
- Findings: pass=15 warn=5 fail=1
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
- Policy JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_quality_policy.json`

## Actionable Findings
1. [WARN] `BENCHMARK_RECOMMENDED_PAIRS_MISSING`: Recommended benchmark pairs are missing (not yet gated).
   - en-de, en-ja, es-en
2. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-ja'; skipping its quality floor checks.
3. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-de'; skipping its quality floor checks.
4. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'es-en'; skipping its quality floor checks.
5. [FAIL] `DELTA_BUDGET_BREACH`: Delta budgets failed for pair 'en-es'.
   - top1_accuracy drop=0.0263 exceeds budget=0.0000
   - top3_recall drop=0.0263 exceeds budget=0.0000
   - forbidden_top1_rate increase=0.0263 exceeds budget=0.0000
   - forbidden_any_rate increase=0.0263 exceeds budget=0.0000
6. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-es' unique metric vectors=4 below expected minimum=5.
