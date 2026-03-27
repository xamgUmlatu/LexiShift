# Rulegen Quality Gate

- Status: FAIL
- Findings: pass=14 warn=4 fail=2
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `docs\test_outputs\rulegen_benchmark_en_es_latest.json`
- Policy JSON: `docs\test_inputs\rulegen_quality_policy.json`

## Actionable Findings
1. [WARN] `BENCHMARK_RECOMMENDED_PAIRS_MISSING`: Recommended benchmark pairs are missing (not yet gated).
   - en-de, en-ja, es-en
2. [FAIL] `QUALITY_FLOOR_BREACH`: Quality floor failed for pair 'en-es'.
   - top1_accuracy=0.9123 below min_top1_accuracy=0.9500
3. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-ja'; skipping its quality floor checks.
4. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'en-de'; skipping its quality floor checks.
5. [WARN] `QUALITY_FLOOR_PAIR_MISSING`: No benchmark summary for pair 'es-en'; skipping its quality floor checks.
6. [FAIL] `DELTA_BUDGET_BREACH`: Delta budgets failed for pair 'en-es'.
   - top1_accuracy drop=0.0877 exceeds budget=0.0000
   - top3_recall drop=0.0175 exceeds budget=0.0000
   - forbidden_any_rate increase=0.0351 exceeds budget=0.0000
   - avg_rules_per_target increase=1.9825 exceeds budget=0.5000
