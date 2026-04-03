# Rulegen Benchmark Triage (en-de Kaikki tuning latest)

- Benchmark JSON: `docs/test_outputs/rulegen_benchmark_en_de_kaikki_tuning_latest.json`
- Pairs processed: 1
- Actionable items: 4
- FAIL items: 2
- REVIEW items: 2

## Items By Pair

- `en-de`: 4

## Actionable Cases

1. [FAIL] `en-de` `en-de:Arbeit` target=`Arbeit`
   - Reasons: expected_candidate_missing_from_top3
   - Observed top1: `toil`
2. [REVIEW] `en-de` `en-de:Kind` target=`Kind`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `kid`
3. [FAIL] `en-de` `en-de:Fall` target=`Fall`
   - Reasons: top1_is_forbidden, forbidden_candidate_present, expected_candidate_missing_from_top3
   - Observed top1: `fall`
4. [REVIEW] `en-de` `en-de:Grund` target=`Grund`
   - Reasons: top1_not_in_expected_set
   - Observed top1: `ground`
