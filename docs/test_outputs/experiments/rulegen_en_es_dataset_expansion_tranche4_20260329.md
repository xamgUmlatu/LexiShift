# `en-es` Dataset Expansion Tranche 4 (`2026-03-29`)

The `en-es` benchmark suite was expanded from `77` to `83` cases with a fourth tranche focused on:

- computing / interface nouns
- infrastructure nouns
- adjective-vs-noun competition inside computing-marked regions

Added cases:

- `carpeta`
- `directorio`
- `navegador`
- `celda`
- `pestaña`
- `puente`

## Canonical Result After Expansion

- Artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)
- Case count: `83`
- Objective: `133.157`
- `Top1`: `90.36%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.87`
- Best config:
  - `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=0.20 w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

## Newly Added Case Outcomes

- `carpeta` -> `folder, cloth, desk`
- `directorio` -> `directory, directive`
- `navegador` -> `navigating, navigator, browser`
- `celda` -> `cell`
- `pestaña` -> `eyelash, flange, tab`
- `puente` -> `bridge, denture`

Current canonical status for the new tranche:

- PASS: `carpeta`, `directorio`, `celda`, `pestaña`, `puente`
- REVIEW: `navegador`

## Frozen Profile Bank Follow-up

- Artifact: [rulegen_en_es_profile_bank_comparison_20260329_83cases.md](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_profile_bank_comparison_20260329_83cases.md)
- Aggregate frozen-bank result on the `83`-case suite:
  - top1-diff cases: `1`
  - top3-diff cases: `4`
  - rule-count-diff cases: `64`
- The only top1 split remains:
  - `trama`
    - canonical: `weft`
    - tighter profiles: `weave`
- `navegador` widens the top3-sensitive set:
  - canonical: `navigating, navigator, browser`
  - admission-tight: `navigating`
  - combined/family: `navigating, navigator`

## Interpretation

- This tranche is useful because it adds one more real review case without introducing new forbidden-side failures.
- `navegador` is a clean example of the current remaining issue class: adjective leakage beating the intended noun-side computing reading.
- The frozen profile bank still changes top1 identity only on `trama`, but it now changes top3 behavior on `navegador` too.
- The right next move remains deeper trait/profile analysis on the `83`-case suite, not immediate embeddings or runtime routing.
