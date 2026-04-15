# `en-es` Dataset Expansion Tranche 2 (`2026-03-29`)

The `en-es` benchmark suite was expanded from `64` to `71` cases with a second tranche focused on:

- communication/domain competition
- ranking-boundary nouns
- broad-vs-niche noun competition

Added cases:

- `carta`
- `radio`
- `cadena`
- `nota`
- `sección`
- `seña`
- `perfil`

## Canonical Result After Expansion

- Artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)
- Case count: `71`
- Objective: `135.296`
- `Top1`: `92.96%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.94`
- Best config unchanged:
  - `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

## Newly Added Case Outcomes

- `carta` -> `letter, map, menu`
- `radio` -> `radio, radius, radium`
- `cadena` -> `chain`
- `nota` -> `note, mark, memo`
- `sección` -> `section, department`
- `seña` -> `sign, gesture, indication`
- `perfil` -> `profile`

All seven newly added cases pass on the canonical latest config.

## Actionable Set

The canonical actionable set remains review-only and unchanged:

- `derecho`
- `cuadro`
- `cuenta`
- `red`
- `señal`

## Interpretation

- The suite-expansion tranche increased benchmark breadth without creating new actionable failures.
- Canonical objective and `Top1` both improved slightly, while `AvgRulesPerTarget` decreased slightly.
- That is a useful signal that benchmark expansion is still paying off and that the current remaining review set is not only an artifact of the smaller benchmark.
- Because the review set stayed stable through this expansion, the next best move is now benchmark-side trait/profile instrumentation rather than another immediate blind sweep or another immediate suite bump.
