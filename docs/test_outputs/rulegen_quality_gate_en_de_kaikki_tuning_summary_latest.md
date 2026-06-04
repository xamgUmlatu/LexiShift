# Rulegen Quality Gate (en-de Kaikki tuning latest)

- Status: WARN
- Findings: pass=15 warn=1 fail=0
- Fail on warn: no
- Strict saturation: no
- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.json`
- Policy JSON: `docs/test_inputs/rulegen_quality_policy.json`
- Pair scope: `en-de`

## Actionable Findings
1. [WARN] `DELTA_SCOPE_BASELINE_MISSING`: Scoped pair 'en-de' has no baseline metrics; skipping delta checks.
