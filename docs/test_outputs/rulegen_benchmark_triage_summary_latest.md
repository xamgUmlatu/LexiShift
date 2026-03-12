# Rulegen Benchmark Triage

- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Pairs processed: 1
- Actionable items: 4
- FAIL items: 4
- REVIEW items: 0

## Items By Pair

- `en-es`: 4

## Actionable Cases

1. [FAIL] `en-es` `en-es:madre` target=`madre`
   - Reasons: top1_is_forbidden, forbidden_candidate_present
   - Observed top1: `bed`
2. [FAIL] `en-es` `en-es:planta` target=`planta`
   - Reasons: top1_is_forbidden
   - Observed top1: `sole`
3. [FAIL] `en-es` `en-es:derecho` target=`derecho`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `claim`
4. [FAIL] `en-es` `en-es:cuadro` target=`cuadro`
   - Reasons: top1_is_forbidden, forbidden_candidate_present
   - Observed top1: `bed`
