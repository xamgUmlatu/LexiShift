# `en-es` Dataset Expansion Tranche 7 (`2026-03-29`)

Scope:

- continue suite growth in the same hard regions as the remaining review set
- prefer broad multi-bucket nouns and modern abstract/device nouns over additional easy computing-only nouns

Added cases:

- `banda`
- `registro`
- `patrón`
- `trazo`
- `tráfico`
- `mando`

Observed canonical outcomes on the refreshed `100`-case benchmark:

- `banda` -> `band, gang, sash`
- `registro` -> `registration, register, entry`
- `patrón` -> `patron, boss, pattern`
- `trazo` -> `line, stroke, outline`
- `tráfico` -> `traffic, smuggle`
- `mando` -> `command, gamepad, controller`

Interpretation:

- the tranche added real pressure rather than only easy passes
- `registro`, `patrón`, and `mando` are now new review cases on canonical
- `banda`, `trazo`, and `tráfico` currently pass on canonical
- the canonical suite is now `100` cases
- latest canonical result after this tranche:
  - objective `131.180`
  - `Top1 89.00%`
  - `Top3 100.00%`
  - `ForbidAny 0.00%`
  - `AvgRules 2.97`
- current canonical review set is now:
  - `derecho`
  - `cuadro`
  - `cuenta`
  - `red`
  - `señal`
  - `archivo`
  - `trama`
  - `navegador`
  - `registro`
  - `patrón`
  - `mando`

Frozen four-profile bank refresh on the `100`-case suite:

- canonical: objective `131.180`, `Top1 89.00%`, `Top3 100.00%`, triage `11`
- admission-tight: objective `136.900`, `Top1 88.00%`, `Top3 100.00%`, triage `12`
- combined-balanced: objective `134.860`, `Top1 88.00%`, `Top3 100.00%`, triage `12`
- family-followup: objective `136.900`, `Top1 88.00%`, `Top3 100.00%`, triage `12`

Profile-bank structure remains stable:

- `1` top1-diff case: `móvil`
- `0` top3-diff cases
- `54` rule-count-diff cases

Current conclusion:

- the suite is still getting better at exposing real lexical/ranking pressure
- profile choice still mostly changes rule volume and objective, not top1 identity
- the new tranche widened the ranking-review surface without introducing forbidden-side regressions
- the highest-value next growth continues to be harder polysemous nouns and broad-vs-technical competition, not additional easy lexical coverage
