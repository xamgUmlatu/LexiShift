# Rulegen Benchmark Triage

- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_es_latest.json`
- Pairs processed: 1
- Actionable items: 13
- FAIL items: 7
- REVIEW items: 6

## Items By Pair

- `en-es`: 13

## Actionable Cases

1. [FAIL] `en-es` `en-es:amor` target=`amor`
   - Reasons: expected_candidate_missing_from_top3, no_rules_emitted
2. [REVIEW] `en-es` `en-es:derecho` target=`derecho`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `straight`
3. [FAIL] `en-es` `en-es:cuadro` target=`cuadro`
   - Reasons: expected_candidate_missing_from_top3
   - Observed top1: `square`
4. [REVIEW] `en-es` `en-es:cuenta` target=`cuenta`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `count`
5. [REVIEW] `en-es` `en-es:red` target=`red`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `web`
6. [REVIEW] `en-es` `en-es:sacar` target=`sacar`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `withdraw`
7. [FAIL] `en-es` `en-es:malla` target=`malla`
   - Reasons: expected_candidate_missing_from_top3, no_rules_emitted
8. [FAIL] `en-es` `en-es:acabar` target=`acabar`
   - Reasons: forbidden_candidate_present
   - Observed top1: `finish`
9. [FAIL] `en-es` `en-es:coger` target=`coger`
   - Reasons: forbidden_candidate_present
   - Observed top1: `take`
10. [FAIL] `en-es` `en-es:batería` target=`batería`
   - Reasons: top1_is_forbidden, expected_candidate_missing_from_top3
   - Observed top1: `drummer`
11. Additional items omitted: 3
