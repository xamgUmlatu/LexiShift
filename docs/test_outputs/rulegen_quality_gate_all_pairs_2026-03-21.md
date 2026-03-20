# Rulegen Quality Gate

- Status: FAIL
- Findings: pass=14 warn=8 fail=4
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json`
- Policy JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_quality_policy.json`

## Actionable Findings
1. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-es'.
   - top1_accuracy=0.7895 below min_top1_accuracy=0.9500
   - top3_recall=0.7895 below min_top3_recall=0.9500
   - forbidden_top1_rate=0.2105 above max_forbidden_top1_rate=0.0500
   - forbidden_any_rate=0.1316 above max_forbidden_any_rate=0.1000
2. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-de'.
   - top1_accuracy=0.7500 below min_top1_accuracy=0.8500
3. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'es-en'.
   - top1_accuracy=0.7500 below min_top1_accuracy=0.8500
   - top3_recall=0.7500 below min_top3_recall=0.9000
4. [FAIL] `DELTA_BUDGET_BREACH`: Delta budgets failed for pair 'en-es'.
   - top1_accuracy drop=0.2105 exceeds budget=0.0000
   - top3_recall drop=0.2105 exceeds budget=0.0000
   - forbidden_top1_rate increase=0.2105 exceeds budget=0.0000
   - forbidden_any_rate increase=0.1316 exceeds budget=0.0000
5. [WARN] `SATURATION_TOP_VECTOR_WARN`: Pair 'en-de' top metric vector share=0.500 indicates low sensitivity (warn threshold>=0.500).
   - run_count=16 unique_vectors=2 top_count=8
6. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-de' unique metric vectors=2 below expected minimum=5.
7. [WARN] `SATURATION_TOP_VECTOR_WARN`: Pair 'en-es' top metric vector share=0.500 indicates low sensitivity (warn threshold>=0.500).
   - run_count=16 unique_vectors=2 top_count=8
8. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-es' unique metric vectors=2 below expected minimum=5.
9. [WARN] `SATURATION_TOP_VECTOR_WARN`: Pair 'en-ja' top metric vector share=0.500 indicates low sensitivity (warn threshold>=0.500).
   - run_count=16 unique_vectors=2 top_count=8
10. [WARN] `SATURATION_UNIQUE_VECTOR_WARN`: Pair 'en-ja' unique metric vectors=2 below expected minimum=5.
