# en-es Shadow Frequency Sweep

- Status: `ok`
- Generated: `2026-04-10T19:13:24Z`
- Forward seed max words: `1`
- Fixed trigger support min: `0.0`
- Fixed shadow support score: `min=5.0`, `max_promoted=2`
- Sweep meaning: keep the current lexical source-only pipeline fixed, then add a soft bonus for the most frequent shadow targets within each trigger bucket.

## Rows
| Mode | Bonus | Top-K | Precision | Recall | F1 | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline F1 | Baseline Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | 0.0 | 0 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.0 | 1 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.0 | 2 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.0 | 3 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.25 | 0 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.25 | 1 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.25 | 2 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.25 | 3 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.5 | 0 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.5 | 1 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.5 | 2 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 0.5 | 3 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 1.0 | 0 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 1.0 | 1 | 40.0% | 80.0% | 53.3% | 80.0% | 7.2% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 1.0 | 2 | 38.1% | 80.0% | 51.6% | 80.0% | 8.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| benchmark_reviewed | 1.0 | 3 | 36.4% | 80.0% | 50.0% | 80.0% | 8.0% | 100.0% | 80.0% | 88.9% | 0.0% |
| rulegen_top3_plus_forward_gloss | 0.0 | 0 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.0 | 1 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.0 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.0 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.25 | 0 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.25 | 1 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.25 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.25 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.5 | 0 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.5 | 1 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.5 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 0.5 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 1.0 | 0 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 1.0 | 1 | 21.6% | 80.0% | 34.0% | 80.0% | 18.8% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 1.0 | 2 | 20.0% | 80.0% | 32.0% | 80.0% | 18.8% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 1.0 | 3 | 19.5% | 80.0% | 31.4% | 80.0% | 18.8% | 47.1% | 80.0% | 59.3% | 5.1% |

## Best Rows By Mode
- `benchmark_reviewed` with `bonus=0.0` and `top_k=0`: precision `100.0%`, recall `80.0%`, F1 `88.9%`, overblocking `0.0%`
- `rulegen_top3_plus_forward_gloss` with `bonus=0.0` and `top_k=0`: precision `47.1%`, recall `80.0%`, F1 `59.3%`, overblocking `5.1%`
