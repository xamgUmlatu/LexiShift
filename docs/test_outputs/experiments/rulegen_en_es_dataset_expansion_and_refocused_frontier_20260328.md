# `en-es` Dataset Expansion And Refocused Frontier

Date: 2026-03-28
Machine: current Windows PC
Status: completed follow-up tranche

## What Changed

The `en-es` benchmark dataset was expanded from `57` to `64` cases by adding:

- `canal`
- `clave`
- `gato`
- `masa`
- `señal`
- `batería`
- `llevar`

Intent of the added batch:

- broaden everyday-vs-domain competition
- add more category-rich nouns for later family-toggle work
- add one more phrase-sensitive common verb
- reduce the risk of overfitting the next sweeps to the older smaller case set

## Canonical Latest On The Expanded Set

Canonical latest benchmark artifacts now report:

- case count `64`
- run count `144`
- objective `126.188`
- `Top1 90.62%`
- `Top3 96.88%`
- `ForbidTop1 1.56%`
- `ForbidAny 3.12%`
- `AvgRulesPerTarget 3.03`
- exact-tie count `12`

Canonical latest best config remains:

- `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Canonical latest triage count is now `8`:

- `cuadro` FAIL
- `acabar` FAIL
- `coger` FAIL
- `batería` FAIL
- `derecho` REVIEW
- `cuenta` REVIEW
- `red` REVIEW
- `sacar` REVIEW

## New Case Behavior Under Canonical Latest

New cases that currently pass:

- `canal`
- `clave`
- `gato`
- `masa`
- `señal`
- `llevar`

New case that currently fails:

- `batería`

Observed current canonical output for `batería`:

- top1 `drummer`
- top3 `drummer`, `set`

## Important `batería` Finding

The Kaikki forward pack is not missing the battery-side source row.

Direct source rows for `batería` include:

- `large and rechargeable battery`
- `drum kit, drum set`
- `set (collection of things)`
- `drummer`

So the current `batería` failure is not primarily a raw dictionary-coverage problem.
It is a rulegen extraction / normalization / phrase-condensation problem:

- the source has a battery-side translation
- the current pipeline is not surfacing a useful bare `battery` candidate from that longer phrase

This matters for follow-up planning:

- category demotion alone will not fix `batería`
- we need a path that can recover or normalize strong head translations from longer source phrases

## Focused Expanded-Set Frontier Reruns

### Admission Frontier v2

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_admission_frontier_v2_64cases_20260328.json`

Best result:

- objective `136.281`
- exact-tie count `14`
- config `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `Top1 90.62%`
- `Top3 92.19%`
- `ForbidTop1 1.56%`
- `ForbidAny 0.00%`
- `AvgRulesPerTarget 1.30`
- triage count `6`

Interpretation:

- strong objective due to aggressive admission and low rule count
- fixes the lingering `acabar` / `coger` forbidden-any problem
- but trims recall too hard for `cuadro`, `cuenta`, `red`, and `sacar`

### Combined Frontier v1

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_combined_frontier_v1_64cases_20260328.json`

Best result:

- objective `133.844`
- exact-tie count `12`
- config `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `Top1 90.62%`
- `Top3 96.88%`
- `ForbidTop1 1.56%`
- `ForbidAny 0.00%`
- `AvgRulesPerTarget 2.17`
- triage count `6`

Interpretation:

- preserves broader top-3 coverage
- still removes `ForbidAny`
- does not beat the stricter admission-led objective

### Reverse Frontier v2

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_reverse_frontier_v2_64cases_20260328.json`

Best result:

- objective `127.438`

Interpretation:

- no longer the leading direction on the expanded set

### Family Follow-up v1

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v1_64cases_20260328.json`

Best result:

- objective `126.188`

Interpretation:

- the currently exposed family-set variants do not move the expanded set enough to matter yet

## Current Practical Read

The expanded set changed the frontier shape in an important way:

- the old `57`-case admission winner is no longer the only meaningful story
- the `64`-case set now exposes a real tradeoff between:
  - a stricter low-rule admission winner
  - a broader-recall combined frontier

This is useful because it gives the next sweeps a more realistic objective surface than the older smaller set.

## Next Recommended Steps

1. Keep the `64`-case dataset as the active baseline.
2. Add a small number of additional normalized family/category controls beyond `mg+gl+hft+rr+aef`.
3. Rerun focused family and winner-neighborhood sweeps on the expanded set.
4. If `batería` still fails after that, treat it as targeted rulegen work around phrase condensation rather than a demotion-only problem.
5. Keep `cuadro` and `sacar` as the highest-value targeted algorithmic follow-ups once the next focused sweep tranche is complete.
