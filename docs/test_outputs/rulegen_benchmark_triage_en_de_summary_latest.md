# Rulegen Benchmark Triage (en-de latest)

- Benchmark JSON: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_de_latest.json`
- Pairs processed: 1
- Actionable items: 12
- FAIL items: 9
- REVIEW items: 3

## Items By Pair

- `en-de`: 12

## Actionable Cases

1. [FAIL] `en-de` `en-de:Schule` target=`Schule`
   - Reasons: forbidden_candidate_present
   - Observed top1: `school`
2. [FAIL] `en-de` `en-de:Zeit` target=`Zeit`
   - Reasons: forbidden_candidate_present
   - Observed top1: `time`
3. [FAIL] `en-de` `en-de:Fenster` target=`Fenster`
   - Reasons: forbidden_candidate_present
   - Observed top1: `box`
4. [FAIL] `en-de` `en-de:Tag` target=`Tag`
   - Reasons: forbidden_candidate_present
   - Observed top1: `day`
5. [FAIL] `en-de` `en-de:Kopf` target=`Kopf`
   - Reasons: forbidden_candidate_present
   - Observed top1: `mind`
6. [FAIL] `en-de` `en-de:Ohr` target=`Ohr`
   - Reasons: forbidden_candidate_present
   - Observed top1: `hearing`
7. [FAIL] `en-de` `en-de:Fuß` target=`Fuß`
   - Reasons: forbidden_candidate_present
   - Observed top1: `base`
8. [REVIEW] `en-de` `en-de:Straße` target=`Straße`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `avenue`
9. [REVIEW] `en-de` `en-de:Chef` target=`Chef`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `chief`
10. [FAIL] `en-de` `en-de:Zug` target=`Zug`
   - Reasons: forbidden_candidate_present
   - Observed top1: `train`
11. Additional items omitted: 2
