# Rulegen Benchmark Triage

- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
- Pairs processed: 1
- Actionable items: 1
- FAIL items: 1
- REVIEW items: 0

## Items By Pair

- `en-es`: 1

## Actionable Cases

1. [FAIL] `en-es` `en-es:cuadro` target=`cuadro`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `bed`
