# Rulegen Benchmark

- Generated at: `2026-03-20T19:56:37.232974+00:00`
- Dataset: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_benchmark_cases.json`
- Profile ID: `default`
- Pair filter: `en-de, en-es, en-ja, es-en`
- Configurations per pair: 16
- Pairs reported: 4

## Best Runs

| Pair | Case Count | Run Count | Objective | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Config |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| en-de | 16 | 16 | 120.750 | 75.00% | 100.00% | 0.00% | 0.00% | 2.38 | `md=3 mr=none thr=0.000 sd=1.00 var=off pos=on rev=off w_pos=0.000` |
| en-es | 38 | 16 | 84.526 | 78.95% | 78.95% | 21.05% | 13.16% | 1.00 | `md=3 mr=1 thr=0.000 sd=1.00 var=off pos=on rev=off w_pos=0.000` |
| en-ja | 17 | 16 | 148.118 | 94.12% | 100.00% | 0.00% | 0.00% | 1.00 | `md=3 mr=1 thr=0.000 sd=1.00 var=off pos=on rev=off w_pos=0.000` |
| es-en | 16 | 16 | 114.000 | 75.00% | 75.00% | 0.00% | 0.00% | 1.00 | `md=3 mr=1 thr=0.000 sd=1.00 var=off pos=on rev=off w_pos=0.000` |
