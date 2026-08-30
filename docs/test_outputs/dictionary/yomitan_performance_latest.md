# Synthetic Yomitan Dictionary Performance

This report uses generated, redistributable Yomitan format-3 data. Timing budgets are optional and machine-specific; correctness is reported separately.

## Fixture

- Banks: 8
- Terms: 200000
- ZIP bytes: 2095367
- Third-party data: no

## Timings

| Operation | Time |
| --- | ---: |
| Generate fixture | 286.015 ms |
| Initial import and indexing | 1263.685 ms |
| Repeat import | 2.287 ms |
| Lookup median (100 runs) | 0.142 ms |
| Lookup p95 | 0.228 ms |
| Cancel after first bank | 150.541 ms |

## Correctness

- PASS: term count matches
- PASS: all banks reported
- PASS: repeat import reused pack
- PASS: lookups succeeded
- PASS: cancellation observed
- PASS: cancellation cleaned up
