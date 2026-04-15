# `en-es` Dataset Expansion Tranche 3 (`2026-03-29`)

The `en-es` benchmark suite was expanded from `71` to `77` cases with a third tranche focused on:

- computing / recordkeeping competition
- communication / infrastructure nouns
- device / tool competition
- dense multi-bucket noun ranking

Added cases:

- `archivo`
- `puerto`
- `ratón`
- `tecla`
- `trama`
- `margen`

## Canonical Result After Expansion

- Artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)
- Case count: `77`
- Objective: `133.455`
- `Top1`: `90.91%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.91`
- Best config:
  - `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=0.20 w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

## Newly Added Case Outcomes

- `archivo` -> `archive, file`
- `puerto` -> `port, harbour`
- `ratón` -> `mouse, hangover`
- `tecla` -> `key, trigger, button`
- `trama` -> `weft, plot, weave`
- `margen` -> `margin, leeway, edge`

Current canonical status for the new tranche:

- PASS: `puerto`, `ratón`, `tecla`, `margen`
- REVIEW: `archivo`, `trama`

## Frozen Profile Bank Follow-up

- Artifact: [rulegen_en_es_profile_bank_comparison_20260329_77cases.md](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_profile_bank_comparison_20260329_77cases.md)
- The broadened suite produces the first top-1 split across the frozen profile bank:
  - `trama`
    - canonical: `weft`
    - admission-tight / combined-balanced / family-followup: `weave`
- Aggregate frozen-bank result on the `77`-case suite:
  - top1-diff cases: `1`
  - top3-diff cases: `3`
  - rule-count-diff cases: `59`

## Interpretation

- This tranche is useful because it did not only add easy passes.
- `archivo` and `trama` create exactly the kind of top-1 preference pressure we want before any runtime profile-routing work.
- The current profile bank still mostly changes rule volume and top-3 breadth, but it no longer leaves top-1 identity completely unchanged.
- The right next move remains deeper offline trait/profile analysis on the `77`-case suite, not immediate embeddings or runtime routing.
