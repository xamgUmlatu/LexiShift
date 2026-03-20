# Rulegen Benchmark Triage

- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Pairs processed: 1
- Actionable items: 11
- FAIL items: 11
- REVIEW items: 0

## Items By Pair

- `en-es`: 11

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
5. [FAIL] `en-es` `en-es:orden` target=`orden`
   - Reasons: forbidden_candidate_present
   - Observed top1: `order`
6. [FAIL] `en-es` `en-es:cargo` target=`cargo`
   - Reasons: top1_is_forbidden, forbidden_candidate_present
   - Observed top1: `accusal`
7. [FAIL] `en-es` `en-es:plaza` target=`plaza`
   - Reasons: forbidden_candidate_present
   - Observed top1: `plaza`
8. [FAIL] `en-es` `en-es:masa` target=`masa`
   - Reasons: top1_is_forbidden, forbidden_candidate_present
   - Observed top1: `lump`
9. [FAIL] `en-es` `en-es:caso` target=`caso`
   - Reasons: top1_is_forbidden
   - Observed top1: `affair`
10. [FAIL] `en-es` `en-es:parte` target=`parte`
   - Reasons: forbidden_candidate_present
   - Observed top1: `part`
11. Additional items omitted: 1
