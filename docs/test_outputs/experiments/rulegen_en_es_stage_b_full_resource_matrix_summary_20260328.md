# `en-es` Stage B Full Resource Matrix Summary

Date: 2026-03-28
Machine: current Windows PC
Dataset: `docs/test_inputs/rulegen_benchmark_cases.json`
Fixed config: `md=2 mr=2 thr=0.000 sd=0.50 var=on pos=on rev=(lane) xamb=off xspec=off w_pos=0.100 kdem=on kfam=mg+gl+hft+rr+aef kprov=0.10`

## Resource Lanes

| Lane | Objective | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Triage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kaikki forward + Kaikki reverse | 139.333 | 91.23% | 98.25% | 0.00% | 0.00% | 1.81 | 5 |
| Kaikki forward + FreeDict reverse | 137.684 | 89.47% | 98.25% | 0.00% | 0.00% | 1.79 | 6 |
| Kaikki forward + reverse disabled | 132.351 | 87.72% | 92.98% | 0.00% | 0.00% | 1.86 | 7 |
| FreeDict forward + Kaikki reverse | 65.228 | 54.39% | 73.68% | 14.04% | 10.53% | 1.35 | 27 |
| FreeDict forward + FreeDict reverse | 65.579 | 54.39% | 71.93% | 14.04% | 8.77% | 1.35 | 26 |
| FreeDict forward + reverse disabled | 59.860 | 54.39% | 64.91% | 14.04% | 10.53% | 1.37 | 27 |

## Main Findings

- Kaikki forward + Kaikki reverse remains the best `en-es` lane on this PC.
- Kaikki forward + FreeDict reverse is slightly worse than Kaikki forward + Kaikki reverse.
- Kaikki forward still benefits materially from reverse scoring in general; disabling reverse drops both `Top1` and `Top3`.
- FreeDict forward remains non-competitive regardless of reverse lane.
- FreeDict reverse is slightly better than Kaikki reverse inside the weak FreeDict-forward lane, but the improvement is too small to change the overall conclusion.

## Key Case Deltas

Comparing the two strong Kaikki-forward lanes:

- only one top1 case changed: `hasta`
  - Kaikki reverse: `until`
  - FreeDict reverse: `even`
- `Top3` stayed unchanged between those two lanes
- both lanes kept `ForbidAny 0.00%`

Comparing the two FreeDict-forward reverse-enabled lanes:

- FreeDict reverse removed a forbidden-any hit on `parte`
- FreeDict reverse lost `Top3` coverage on `derecho`
- net result was still a very weak lane overall

## Installed-Resource Helper Check

The local machine now has:

- `C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\language_packs\freedict-eng-spa-2025.11.23.src\eng-spa.tei`
- `C:\Users\kuuko\AppData\Roaming\LexiShift\LexiShift\frequency_packs\freq-es-cde.sqlite`

Helper-side findings:

- `srs_diagnostics --pair en-es` reports `missing_inputs = []`
- the frequency DB is detected and selected
- a no-persist helper `run_rulegen` smoke succeeded locally
  - `117` rules
  - `40` targets
  - snapshot stats reported `38` target entries

The diagnostics payload still contains an older `status.last_error`, but the successful no-persist helper smoke shows that this is not a current `en-es` resource blocker on this PC.

## Practical Conclusion

For current `en-es` testing on this PC:

- the benchmark/resource side is ready
- Kaikki forward + Kaikki reverse should remain the primary lane
- the next highest-value work is not more source-lane comparison
- the next highest-value work is targeted ranking/failure work on:
  - `cuadro`
  - `sacar`
  - `derecho`
  - `cuenta`
  - `red`
