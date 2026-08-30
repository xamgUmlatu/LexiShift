# Rulegen Benchmark Triage (en-ja latest)

- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_ja_latest.json`
- Pairs processed: 1
- Actionable items: 1
- FAIL items: 1
- REVIEW items: 0

## Items By Pair

- `en-ja`: 1

## Actionable Cases

1. [FAIL] `en-ja` `en-ja:世界` target=`世界`
   - Reasons: forbidden_candidate_present
   - Observed top1: `society`
