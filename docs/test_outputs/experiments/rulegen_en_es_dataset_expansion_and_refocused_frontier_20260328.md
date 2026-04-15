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
- objective `129.000`
- `Top1 90.62%`
- `Top3 98.44%`
- `ForbidTop1 0.00%`
- `ForbidAny 3.12%`
- `AvgRulesPerTarget 3.03`
- exact-tie count `12`

Canonical latest best config remains:

- `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Canonical latest triage count is now `8`:

- `cuadro` FAIL
- `acabar` FAIL
- `coger` FAIL
- `derecho` REVIEW
- `cuenta` REVIEW
- `red` REVIEW
- `sacar` REVIEW
- `señal` REVIEW

## New Case Behavior Under Canonical Latest

New cases that currently pass:

- `canal`
- `clave`
- `gato`
- `masa`
- `llevar`

New case that currently reviews:

- `señal`

New case that now also passes:

- `batería`

## Important `batería` Finding

The Kaikki forward pack is not missing the battery-side source row.

Direct source rows for `batería` include:

- `large and rechargeable battery`
- `drum kit, drum set`
- `set (collection of things)`
- `drummer`

So the original `batería` failure was not primarily a raw dictionary-coverage problem.
It was a rulegen extraction / normalization / phrase-condensation problem:

- the source has a battery-side translation
- the original pipeline was not surfacing a useful bare `battery` candidate from that longer phrase

This mattered for follow-up planning:

- category demotion alone would not fix `batería`
- we needed a path that could recover or normalize strong head translations from longer source phrases

That targeted follow-up is now in place:

- a narrow nominal-head recovery step was added for long noun-like gloss phrases
- canonical latest now recovers `battery` from `large and rechargeable battery`
- `batería` now passes on the canonical latest surface with top1 `battery`

Late 2026-03-28 canonical follow-up:

- a second narrow follow-up now suppresses reverse-miss penalties only for heuristic `leading_alias` and `nominal_head` fragments when they do not already have a direct reverse hit
- this keeps ordinary comma-fragment behavior unchanged while lifting `cuadro` from hard FAIL to REVIEW by surfacing `square, picture, frame`
- current canonical latest therefore now lands at objective `129.938`, `Top1 90.62%`, `Top3 100.00%`, `ForbidTop1 0.00%`, `ForbidAny 3.12%`

Later 2026-03-28 canonical phrase-policy follow-up:

- a third narrow follow-up now admits only recurrent exact reverse-attested two-word phrasal-verb candidates
- the rule is deliberately narrow:
  - two-word phrasal-verb shape only
  - exact reverse hit required
  - target-local sanitized gloss recurrence required
- this lifts `sacar` from REVIEW to PASS on the canonical surface with top3 `take out, withdraw, draw`
- a fourth narrow follow-up now suppresses explicit vulgar senses when clean competition exists
- current canonical latest therefore now lands at objective `134.094`, `Top1 92.19%`, `Top3 100.00%`, `ForbidTop1 0.00%`, `ForbidAny 0.00%`
- the canonical actionable set is now review-only: `derecho`, `cuadro`, `cuenta`, `red`, and `señal`

## Focused Expanded-Set Frontier Reruns

### Admission Frontier v2

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_admission_frontier_v2_64cases_20260328.json`

Best result:

- objective `139.094`
- config `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `Top1 90.62%`
- `Top3 93.75%`
- `ForbidTop1 0.00%`
- `ForbidAny 0.00%`
- `AvgRulesPerTarget 1.30`
- triage count `6`

Interpretation:

- strong objective due to aggressive admission and low rule count
- fixes the older `acabar` / `coger` forbidden-any problem
- but trims recall too hard for `cuadro`, `cuenta`, `red`, and `sacar`

### Combined Frontier v1

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_combined_frontier_v1_64cases_20260328.json`

Best result:

- objective `136.656`
- exact-tie count `12`
- config `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `Top1 90.62%`
- `Top3 98.44%`
- `ForbidTop1 0.00%`
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

### Family Follow-up v2

Artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_post_batteryfix_20260328.json`

Best result:

- objective `138.719`
- config `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off`
- `Top1 90.62%`
- `Top3 98.44%`
- `ForbidTop1 0.00%`
- `ForbidAny 0.00%`
- `AvgRulesPerTarget 1.83`
- triage count `6`

Interpretation:

- the currently exposed family-set variants still do not decisively beat the non-family frontier
- but after the `batería` extraction fix this plane is now competitive with the combined frontier rather than clearly flat

## Current Practical Read

The expanded set changed the frontier shape in an important way:

- the old `57`-case admission winner is no longer the only meaningful story
- the `64`-case set now exposes a real tradeoff between:
  - a stricter low-rule admission winner
  - a broader-recall combined frontier
- minor label-tightening on top of that expanded set also matters:
  - `señal` moved from pass to review once the benchmark began explicitly preferring `signal` over `signal/sign`

This is useful because it gives the next sweeps a more realistic objective surface than the older smaller set.

## Next Recommended Steps

1. Keep the `64`-case dataset as the active baseline.
2. Preserve the expanded family/category control surface for future sweeps, but do not treat it as the main remaining lever on `en-es`.
3. Treat `batería` as fixed on the current benchmark surface and keep the narrow nominal-head recovery heuristic as the extraction baseline.
4. Keep `cuadro` as the highest-value targeted ranking/extraction follow-up.
5. Treat the `acabar` / `coger` vulgar-leakage issue as fixed on the current benchmark surface via narrow clean-competition suppression.
6. Keep `derecho`, `cuenta`, `red`, and `señal` as preference/ranking follow-ups rather than extraction failures.

## Family-Control Follow-up Note

The next scaffold slice after this write-up is now in place:

- verified preset: `en_es_stage_a_family_followup_v2`
- newly exposed normalized families:
  - `art_media`
  - `communication_network`
  - `computing`
  - `mechanics_tools`
  - `music`
  - `biology`
  - `chemistry`
- the benchmark CLI now also supports explicit per-family demotion maps through `--kaikki-policy-risk-family-demotion-sets`
- full-run result on the same `64`-case dataset after the `batería` extraction fix is objective `138.719`
- the winner still stays on the default family-demotion map, so the family plane is valid but not yet the decisive differentiator
