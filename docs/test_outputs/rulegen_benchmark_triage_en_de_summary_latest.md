# Rulegen Benchmark Triage (en-de latest)

- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- Pairs processed: 1
- Actionable items: 4
- FAIL items: 0
- REVIEW items: 4

## Items By Pair

- `en-de`: 4

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
