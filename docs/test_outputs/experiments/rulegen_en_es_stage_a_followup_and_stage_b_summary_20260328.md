# `en-es` Stage A Follow-up And Stage B Summary

Date: 2026-03-28
Machine: current Windows PC
Dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
Resource baseline: Kaikki forward + Kaikki reverse

## Stage A Follow-up Frontier

| Sweep | Runs | Objective | Top1 | Top3 | ForbidAny | AvgRules | Exact Ties | Triage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| canonical replay | 144 | 129.474 | 91.23% | 98.25% | 3.51% | 2.98 | 12 | 7 |
| admission frontier v2 | 189 | 139.333 | 91.23% | 98.25% | 0.00% | 1.81 | 28 | 5 |
| reverse frontier v2 | 144 | 130.877 | 91.23% | 98.25% | 1.75% | 2.98 | 48 | 6 |
| combined frontier v1 | 216 | 137.228 | 91.23% | 98.25% | 0.00% | 2.16 | 12 | 5 |
| combined frontier v2 | 192 | 139.333 | 91.23% | 98.25% | 0.00% | 1.81 | 48 | 5 |

## Current Best Config

Current best-known `en-es` config on this PC:

- `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=on xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

Best artifact:

- `docs/test_outputs/experiments/rulegen_en_es_stage_a_admission_frontier_v2_20260328.json`

The admission-led deepening pass is the clearest improvement so far. It kept `Top1` and `Top3` flat, eliminated `ForbidAny`, reduced `AvgRules` sharply, and lowered triage count from `7` to `5`.

## Interpretation

- The broad toggle plateau finding still holds.
- The major gains came from tighter admission settings, not from broader reverse fine-tuning.
- The reverse-only deepening pass did not improve on the earlier reverse sweep.
- The first combined pass underperformed because it was centered on the older `mr=3` admission winner.
- A second combined pass centered on the real `mr=2` admission winner matched the best admission objective but did not exceed it.
- The combined plateau suggests that once the tighter admission surface is in place, the tested reverse refinements are mostly neutral.

## Key Case Effects

Across the current best admission-led frontier:

- `acabar` no longer has a forbidden-any hit.
- `coger` no longer has a forbidden-any hit.
- `cuadro` remains the hard fail.
- `sacar`, `derecho`, `cuenta`, and `red` remain review-tier ranking problems.

## Stage B Initial Resource Lanes

All Stage B lanes held the current best admission-led config fixed and only changed the forward resource lane and whether reverse scoring was enabled.

This was still an initial Stage B slice, not the full forward-plus-reverse family matrix. In particular, the FreeDict reverse-enabled lane should be treated as a provisional reverse-on comparison, not as the final explicit FreeDict-forward plus FreeDict-reverse result.

| Lane | Objective | Top1 | Top3 | ForbidAny | AvgRules | Triage |
|---|---:|---:|---:|---:|---:|---:|
| Kaikki forward + reverse on | 139.333 | 91.23% | 98.25% | 0.00% | 1.81 | 5 |
| Kaikki forward + reverse off | 132.351 | 87.72% | 92.98% | 0.00% | 1.86 | 7 |
| FreeDict forward + reverse on | 65.228 | 54.39% | 73.68% | 10.53% | 1.35 | 27 |
| FreeDict forward + reverse off | 59.860 | 54.39% | 64.91% | 10.53% | 1.37 | 27 |

## Stage B Interpretation

- Kaikki forward is decisively better than FreeDict forward on the current `en-es` benchmark.
- Reverse scoring still matters meaningfully inside the Kaikki lane.
- FreeDict forward is not competitive on this benchmark even in the initial reverse-enabled comparison.

## Current Note

This summary captures the first Stage B lane pass.

At the time of these runs, the strongest immediate conclusions were still:

- Kaikki vs FreeDict forward comparison
- reverse enabled vs reverse disabled comparison

The local machine now has a real FreeDict `eng-spa.tei` reverse pack, so the next Stage B retest should complete the full forward+reverse family comparison and supersede this initial Stage B slice.

## Recommended Next Step

Do not spend more time broadening reverse-weight neighborhoods right now.

The highest-value next move is one of:

1. lexical/ranking work targeted at `cuadro`
2. review-tier ranking cleanup for `sacar`, `derecho`, `cuenta`, and `red`
3. a fuller Stage B lane comparison using the now-installed real FreeDict `eng-spa.tei` reverse resource
