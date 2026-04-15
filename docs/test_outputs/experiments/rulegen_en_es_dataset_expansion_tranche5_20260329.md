# `en-es` Dataset Expansion Tranche 5

- Date: `2026-03-29`
- Benchmark baseline artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)
- Profile-bank comparison artifact: [rulegen_en_es_profile_bank_comparison_20260329_88cases_post_nominalphrase.md](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_profile_bank_comparison_20260329_88cases_post_nominalphrase.md)

## Added Cases

- `móvil`
- `servidor`
- `ventana`
- `hilo`
- `portal`

## Canonical Outcomes

- `móvil` -> `mobile phone, mobile, motive`
- `servidor` -> `server`
- `ventana` -> `window, nostril`
- `hilo` -> `thread, linen, crosshair`
- `portal` -> `portal, porch`

## Canonical Summary

- case count: `88`
- objective: `133.455`
- `Top1`: `90.91%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.91`

## Interpretation

- All five additions now pass on the canonical latest config.
- `móvil` is still the most useful new pressure point:
  - canonical now keeps `mobile phone` top1
  - tighter profiles still regress to bare `mobile`
- This tranche still adds useful adjective-vs-noun and computing/interface pressure, but it is no longer contributing a canonical hard fail.

## Frozen Profile-Bank Rerun

- compared profiles:
  - `canonical`
  - `admission-tight`
  - `combined-balanced`
  - `family-followup`
- result:
  - top1-diff cases: `1`
  - top3-diff cases: `0`
  - rule-count-diff cases: `46`
- top1-diff case is now:
  - `móvil`
    - canonical: `mobile phone`
    - tighter profiles: `mobile`
