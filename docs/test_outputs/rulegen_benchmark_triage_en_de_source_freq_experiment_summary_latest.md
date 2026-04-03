# Rulegen Benchmark Triage (en-de source frequency experiment)

- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_de_source_freq_experiment_latest.json`
- Pairs processed: 1
- Actionable items: 20
- FAIL items: 15
- REVIEW items: 5

## Items By Pair

- `en-de`: 20

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
4. [FAIL] `en-de` `en-de:Zeit` target=`Zeit`
   - Reasons: forbidden_candidate_present
   - Observed top1: `spell`
5. [FAIL] `en-de` `en-de:Sprache` target=`Sprache`
   - Reasons: forbidden_candidate_present
   - Observed top1: `diction`
6. [FAIL] `en-de` `en-de:Fenster` target=`Fenster`
   - Reasons: forbidden_candidate_present
   - Observed top1: `box`
7. [FAIL] `en-de` `en-de:Tag` target=`Tag`
   - Reasons: forbidden_candidate_present
   - Observed top1: `tag`
8. [FAIL] `en-de` `en-de:Stunde` target=`Stunde`
   - Reasons: forbidden_candidate_present
   - Observed top1: `lesson`
9. [FAIL] `en-de` `en-de:Kopf` target=`Kopf`
   - Reasons: forbidden_candidate_present
   - Observed top1: `mind`
10. [FAIL] `en-de` `en-de:Gesicht` target=`Gesicht`
   - Reasons: forbidden_candidate_present
   - Observed top1: `facies`
11. Additional items omitted: 10
