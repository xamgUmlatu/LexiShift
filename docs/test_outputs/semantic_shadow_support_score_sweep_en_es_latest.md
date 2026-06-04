# en-es Shadow Support Score Sweep

- Status: `ok`
- Generated: `2026-04-10T19:12:35Z`
- Forward seed max words: `1`
- Sweep meaning: keep candidate mining fixed per seed mode, then vary only the support-score threshold and the maximum number of promoted shadows.

## Rows
| Mode | Min Score | Max Promoted | Precision | Recall | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | 2.0 | 1 | 7.3% | 90.0% | 90.0% | 81.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 2.0 | 2 | 4.0% | 90.0% | 90.0% | 81.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 2.0 | 3 | 2.9% | 90.0% | 90.0% | 81.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 3.0 | 1 | 20.0% | 90.0% | 90.0% | 26.1% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 3.0 | 2 | 14.8% | 90.0% | 90.0% | 26.1% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 3.0 | 3 | 14.1% | 90.0% | 90.0% | 26.1% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 4.0 | 1 | 19.5% | 80.0% | 80.0% | 23.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 4.0 | 2 | 14.3% | 80.0% | 80.0% | 23.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 4.0 | 3 | 13.8% | 80.0% | 80.0% | 23.9% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 5.0 | 1 | 100.0% | 80.0% | 80.0% | 0.0% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 5.0 | 2 | 100.0% | 80.0% | 80.0% | 0.0% | 14.1% | 90.0% | 26.1% |
| benchmark_reviewed | 5.0 | 3 | 100.0% | 80.0% | 80.0% | 0.0% | 14.1% | 90.0% | 26.1% |
| rulegen_top3_plus_forward_gloss | 2.0 | 1 | 5.8% | 60.0% | 60.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 2.0 | 2 | 4.0% | 80.0% | 80.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 2.0 | 3 | 2.8% | 80.0% | 80.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 1 | 14.0% | 60.0% | 60.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 2 | 12.9% | 80.0% | 80.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 3.0 | 3 | 12.1% | 80.0% | 80.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 1 | 15.8% | 60.0% | 60.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 2 | 14.3% | 80.0% | 80.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 4.0 | 3 | 13.8% | 80.0% | 80.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 12.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | 5.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 1 | 5.8% | 60.0% | 60.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 2 | 4.0% | 80.0% | 80.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 2.0 | 3 | 2.8% | 80.0% | 80.0% | 68.8% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 1 | 14.0% | 60.0% | 60.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 2 | 12.9% | 80.0% | 80.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 3.0 | 3 | 12.1% | 80.0% | 80.0% | 25.4% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 1 | 15.8% | 60.0% | 60.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 2 | 14.3% | 80.0% | 80.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 4.0 | 3 | 13.8% | 80.0% | 80.0% | 21.7% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 1 | 40.0% | 60.0% | 60.0% | 5.1% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 2 | 47.1% | 80.0% | 80.0% | 5.1% | 12.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | 5.0 | 3 | 47.1% | 80.0% | 80.0% | 5.1% | 12.1% | 80.0% | 25.4% |

## Best Rows By Mode
- `benchmark_reviewed` with `min_score=3.0` and `max_promoted=1`: precision `20.0%`, recall `90.0%`, overblocking `26.1%`
- `rulegen_top3_plus_forward_gloss` with `min_score=5.0` and `max_promoted=2`: precision `47.1%`, recall `80.0%`, overblocking `5.1%`
- `rulegen_all_plus_forward_gloss` with `min_score=5.0` and `max_promoted=2`: precision `47.1%`, recall `80.0%`, overblocking `5.1%`
