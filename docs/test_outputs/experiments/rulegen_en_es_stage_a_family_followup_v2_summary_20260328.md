# `en_es_stage_a_family_followup_v2` Summary

Date: `2026-03-28`

Dataset:

- `64`-case expanded `en-es` benchmark

Preset:

- `en_es_stage_a_family_followup_v2`

Artifact set:

- [JSON](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328.json)
- [Markdown](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328.md)
- [HTML](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328.html)
- [Timing JSON](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328_timing.json)
- [Triage JSON](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328_triage.json)
- [Triage Markdown](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328_triage.md)
- [Gate JSON](D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_64cases_20260328_gate.json)

## Result

Best run:

- objective `134.344`
- `Top1 89.06%`
- `Top3 96.88%`
- `ForbidTop1 1.56%`
- `ForbidAny 0.00%`
- `AvgRulesPerTarget 1.83`
- best config label:
  - `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off`

Plateau shape:

- run count `90`
- exact-tie count at best objective `60`
- unique metric vectors only `2`
- near-frontier count within `1.0` objective of best: `60`

Best non-default family-demotion config:

- objective `134.344`
- label:
  - `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kfd=cn:0.35+cmp:0.35 kprov=off`

Interpretation:

- the new family/category controls are implemented and benchmark-visible
- but on this tranche they did not separate the frontier in a meaningful way
- many distinct family-set and family-demotion combinations landed on the exact same best metric vector

## Practical Delta

Compared with the current canonical latest (`64`-case, objective `124.625`):

- `ForbidAny` improved from `3.12%` to `0.00%`
- `AvgRulesPerTarget` improved from `3.03` to `1.83`
- `Top1` and `Top3` did not improve

Compared with the canonical triage:

- `acabar` dropped out of the actionable set
- `coger` dropped out of the actionable set
- remaining actionable items are:
  - `cuadro` FAIL
  - `batería` FAIL
  - `derecho` REVIEW
  - `cuenta` REVIEW
  - `red` REVIEW
  - `sacar` REVIEW
  - `señal` REVIEW

Important caution:

- this improvement is on the `md=2 mr=2 sd=0.50` family-followup surface
- the experiment does not show that the newly added family controls solved those cases
- it mainly shows that, under this tighter admission surface, the expanded family knobs still do not discriminate strongly

## Gate

The experiment still fails the repo quality gate.

Main reasons:

- `Top1` below policy floor
- delta budget still breached on `Top1`, `Top3`, `ForbidTop1`, and `AvgRulesPerTarget`
- saturation warnings confirm the surface is highly insensitive (`2` unique metric vectors across `90` configs)

## Conclusion

This was a necessary sweep, and it taught us something useful:

- the family/category scaffold is now real
- the first full run says this surface is mostly flat on the current `64`-case benchmark
- the next best move is not more family scaffolding
- it is either:
  - a narrower targeted family follow-up around a few cases like `red` / `batería`, or
  - moving into feature work for `batería`, `cuadro`, and `sacar`
