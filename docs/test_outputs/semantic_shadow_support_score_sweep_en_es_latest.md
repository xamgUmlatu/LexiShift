# en-es Shadow Support Score Sweep

- Status: `ok`
- Generated: `2026-04-10T04:57:54Z`
- Forward seed max words: `1`
- Sweep meaning: keep candidate mining fixed per seed mode, then vary only the support-score threshold and the maximum number of promoted shadows.

## Rows
| Mode | Min Score | Max Promoted | Precision | Recall | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | 2.0 | 1 | 8.3% | 90.0% | 90.0% | 71.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 2.0 | 2 | 4.5% | 90.0% | 90.0% | 71.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 2.0 | 3 | 3.2% | 90.0% | 90.0% | 71.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 3.0 | 1 | 64.3% | 90.0% | 90.0% | 3.6% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 3.0 | 2 | 64.3% | 90.0% | 90.0% | 3.6% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 3.0 | 3 | 64.3% | 90.0% | 90.0% | 3.6% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 4.0 | 1 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 4.0 | 2 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 4.0 | 3 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 5.0 | 1 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 5.0 | 2 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| benchmark_reviewed | 5.0 | 3 | 100.0% | 80.0% | 80.0% | 0.0% | 64.3% | 90.0% | 3.6% |
| rulegen_top3_plus_forward_gloss | 2.0 | 1 | 5.9% | 60.0% | 60.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 2.0 | 2 | 4.1% | 80.0% | 80.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 2.0 | 3 | 2.9% | 80.0% | 80.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 1 | 28.6% | 60.0% | 60.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 2 | 32.0% | 80.0% | 80.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 3 | 32.0% | 80.0% | 80.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 1 | 5.9% | 60.0% | 60.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 2 | 4.1% | 80.0% | 80.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 3 | 2.9% | 80.0% | 80.0% | 67.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 1 | 28.6% | 60.0% | 60.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 2 | 32.0% | 80.0% | 80.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 3 | 32.0% | 80.0% | 80.0% | 9.4% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 32.0% | 80.0% | 9.4% |

## Best Rows By Mode
- `benchmark_reviewed` with `min_score=3.0` and `max_promoted=1`: precision `64.3%`, recall `90.0%`, overblocking `3.6%`
- `rulegen_top3_plus_forward_gloss` with `min_score=4.0` and `max_promoted=2`: precision `47.1%`, recall `80.0%`, overblocking `5.1%`
- `rulegen_all_plus_forward_gloss` with `min_score=4.0` and `max_promoted=2`: precision `47.1%`, recall `80.0%`, overblocking `5.1%`
