# Rulegen Benchmark Triage

- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json`
- Pairs processed: 4
- Actionable items: 17
- FAIL items: 12
- REVIEW items: 5

## Items By Pair

- `en-de`: 4
- `en-es`: 8
- `en-ja`: 1
- `es-en`: 4

## Actionable Cases

1. [REVIEW] `en-de` `en-de:Haus` target=`Haus`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `establishment`
2. [REVIEW] `en-de` `en-de:Schule` target=`Schule`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `pod`
3. [REVIEW] `en-de` `en-de:Weg` target=`Weg`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `alley`
4. [REVIEW] `en-de` `en-de:Zeit` target=`Zeit`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `spell`
5. [FAIL] `en-es` `en-es:madre` target=`madre`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `bed`
6. [FAIL] `en-es` `en-es:planta` target=`planta`
   - Reasons: top1_is_forbidden, expected_candidate_missing_from_top3
   - Observed top1: `sole`
7. [FAIL] `en-es` `en-es:derecho` target=`derecho`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `claim`
8. [FAIL] `en-es` `en-es:cuadro` target=`cuadro`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `bed`
9. [FAIL] `en-es` `en-es:cargo` target=`cargo`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `accusal`
10. [FAIL] `en-es` `en-es:masa` target=`masa`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `lump`
11. Additional items omitted: 7
