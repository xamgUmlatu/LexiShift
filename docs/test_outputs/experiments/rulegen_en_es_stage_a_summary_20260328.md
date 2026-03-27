# `en-es` Stage A Sweep Summary

- Canonical baseline objective: `129.474`
- Canonical baseline config: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- Canonical current triage count: `7`

| Preset | Runs | Objective | Delta vs Canonical | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Exact Ties | Triage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `en_es_stage_a_admission_matrix_v1_20260328` | 108 | 135.719 | +6.246 | 91.23% | 98.25% | 0.00% | 1.75% | 2.18 | 8 | 6 |
| `en_es_stage_a_reverse_weight_matrix_v1_20260328` | 486 | 132.596 | +3.123 | 91.23% | 98.25% | 0.00% | 0.00% | 2.93 | 12 | 5 |
| `en_es_stage_a_exact_hit_matrix_v1_20260328` | 27 | 129.474 | +0.000 | 91.23% | 98.25% | 0.00% | 3.51% | 2.98 | 27 |  |
| `en_es_stage_a_family_followup_v1_20260328` | 16 | 129.474 | +0.000 | 91.23% | 98.25% | 0.00% | 3.51% | 2.98 | 4 |  |
| `en_es_stage_a_scoring_weight_matrix_v1_20260328` | 243 | 129.474 | +0.000 | 91.23% | 98.25% | 0.00% | 3.51% | 2.98 | 243 |  |
| `en_es_stage_a_toggle_frontier_v1_20260328` | 1728 | 129.474 | +0.000 | 91.23% | 98.25% | 0.00% | 3.51% | 2.98 | 408 |  |

## Best Configs

- `en_es_stage_a_admission_matrix_v1_20260328`
  best: `md=2 mr=3 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `en_es_stage_a_reverse_weight_matrix_v1_20260328`
  best: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `en_es_stage_a_exact_hit_matrix_v1_20260328`
  best: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `en_es_stage_a_family_followup_v1_20260328`
  best: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft kprov=0.10`
- `en_es_stage_a_scoring_weight_matrix_v1_20260328`
  best: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.000 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
- `en_es_stage_a_toggle_frontier_v1_20260328`
  best: `md=3 mr=none thr=0.000 sd=1.00 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`
