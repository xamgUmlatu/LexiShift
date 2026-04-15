# `en-es` Post-Vulgar-Fix Frontier Summary (`2026-03-28`)

After the narrow explicit-vulgar clean-competition suppression landed, the canonical `en-es` benchmark and the focused Stage A frontier presets were rerun on the expanded `64`-case dataset.

## Canonical Latest

- Artifact: [rulegen_benchmark_en_es_latest.json](/D:/projects/LexiShift/docs/test_outputs/rulegen_benchmark_en_es_latest.json)
- Objective: `134.094`
- `Top1`: `92.19%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `3.02`
- Best config:
  - `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- Actionable set:
  - `derecho`
  - `cuadro`
  - `cuenta`
  - `red`
  - `señal`

## Focused Frontier Reruns

### Admission Frontier v2

- Artifact: [rulegen_en_es_stage_a_admission_frontier_v2_post_vulgarfix_20260328.json](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_admission_frontier_v2_post_vulgarfix_20260328.json)
- Objective: `141.594`
- `Top1`: `92.19%`
- `Top3`: `95.31%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `1.30`
- Best config:
  - `md=1 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- Triage: same `5` review items as canonical

Interpretation:

- This is now the highest-objective rerun on the current exposed frontier.
- The gain comes mostly from much lower rule volume, not higher `Top1`.
- It gives up some `Top3` recall relative to canonical.
- Quality-gate note:
  - this clears the average-rule floor locally, but still fails the repo gate on `Top1` floor and `Top3` delta budget.

### Combined Frontier v1

- Artifact: [rulegen_en_es_stage_a_combined_frontier_v1_post_vulgarfix_20260328.json](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_combined_frontier_v1_post_vulgarfix_20260328.json)
- Objective: `139.250`
- `Top1`: `92.19%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `2.16`
- Best config:
  - `md=2 mr=3 thr=0.000 sd=0.75 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- Triage: same `5` review items as canonical

Interpretation:

- This is the strongest balanced rerun if preserving `Top3 = 100%` matters.
- It improves objective over canonical without changing the review surface.
- Quality-gate note:
  - this still fails the repo gate on `Top1` floor and average-rule delta budget.

### Family Follow-up v2

- Artifact: [rulegen_en_es_stage_a_family_followup_v2_post_vulgarfix_20260328.json](/D:/projects/LexiShift/docs/test_outputs/experiments/rulegen_en_es_stage_a_family_followup_v2_post_vulgarfix_20260328.json)
- Objective: `141.219`
- `Top1`: `92.19%`
- `Top3`: `100.00%`
- `ForbidAny`: `0.00%`
- `AvgRulesPerTarget`: `1.83`
- Best config:
  - `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=off`
- Triage: same `5` review items as canonical

Interpretation:

- This currently dominates the canonical lane on objective while preserving full `Top3`.
- The winning run still uses the default family map, so the widened family-control surface remains implemented and sweepable, but is not the main driver of the current improvement.
- Quality-gate note:
  - this clears the average-rule floor locally, but still fails the repo gate on `Top1` floor and average-rule delta budget.

## Current Decision Point

The explicit-vulgar suppression follow-up changed the frontier in a useful way:

- the default canonical lane is now clean on forbidden-any
- the remaining misses are all review/ranking cases
- the best focused objective now comes from tighter admission, not from additional family tuning

Practical next options:

1. Treat the `admission_frontier_v2` winner as the current objective-maximizing operating point.
2. Treat the `family_followup_v2` winner as the safer high-objective operating point if keeping `Top3 = 100%` is preferred.
3. Move next into targeted ranking work for `cuadro`, `red`, `derecho`, `cuenta`, and `señal`.
