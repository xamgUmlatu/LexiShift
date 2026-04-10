# en-es Shadow Representative-Pruning Sweep

- Status: `ok`
- Generated: `2026-04-10T19:39:30Z`
- Forward seed max words: `1`
- Sweep meaning: keep seed generation fixed per mode, keep support scoring fixed, and vary only the representative-pruning mode plus the support-score operating point.

## Rows
| Mode | Pruning | Min Score | Max Promoted | Precision | Recall | F1 | Gold Hit | Overblocking |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| benchmark_reviewed | off | 3.0 | 1 | 20.0% | 90.0% | 32.7% | 90.0% | 26.1% |
| benchmark_reviewed | off | 3.0 | 2 | 14.8% | 90.0% | 25.4% | 90.0% | 26.1% |
| benchmark_reviewed | off | 3.0 | 3 | 14.1% | 90.0% | 24.3% | 90.0% | 26.1% |
| benchmark_reviewed | off | 4.0 | 1 | 19.5% | 80.0% | 31.4% | 80.0% | 23.9% |
| benchmark_reviewed | off | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 23.9% |
| benchmark_reviewed | off | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 23.9% |
| benchmark_reviewed | off | 5.0 | 1 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| benchmark_reviewed | off | 5.0 | 2 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| benchmark_reviewed | off | 5.0 | 3 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| benchmark_reviewed | sense_label_pos_v1 | 3.0 | 1 | 20.0% | 90.0% | 32.7% | 90.0% | 26.1% |
| benchmark_reviewed | sense_label_pos_v1 | 3.0 | 2 | 14.8% | 90.0% | 25.4% | 90.0% | 26.1% |
| benchmark_reviewed | sense_label_pos_v1 | 3.0 | 3 | 14.1% | 90.0% | 24.3% | 90.0% | 26.1% |
| benchmark_reviewed | sense_label_pos_v1 | 4.0 | 1 | 19.5% | 80.0% | 31.4% | 80.0% | 23.9% |
| benchmark_reviewed | sense_label_pos_v1 | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 23.9% |
| benchmark_reviewed | sense_label_pos_v1 | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 23.9% |
| benchmark_reviewed | sense_label_pos_v1 | 5.0 | 1 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| benchmark_reviewed | sense_label_pos_v1 | 5.0 | 2 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| benchmark_reviewed | sense_label_pos_v1 | 5.0 | 3 | 100.0% | 80.0% | 88.9% | 80.0% | 0.0% |
| rulegen_top3_plus_forward_gloss | off | 3.0 | 1 | 14.0% | 60.0% | 22.6% | 60.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | off | 3.0 | 2 | 12.9% | 80.0% | 22.2% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | off | 3.0 | 3 | 12.1% | 80.0% | 21.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | off | 4.0 | 1 | 15.8% | 60.0% | 25.0% | 60.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | off | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | off | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | off | 5.0 | 1 | 40.0% | 60.0% | 48.0% | 60.0% | 5.1% |
| rulegen_top3_plus_forward_gloss | off | 5.0 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_top3_plus_forward_gloss | off | 5.0 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 1 | 14.0% | 60.0% | 22.6% | 60.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 2 | 12.9% | 80.0% | 22.2% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 3 | 12.1% | 80.0% | 21.1% | 80.0% | 25.4% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 1 | 15.8% | 60.0% | 25.0% | 60.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 21.7% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 1 | 40.0% | 60.0% | 48.0% | 60.0% | 5.1% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_top3_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_all_plus_forward_gloss | off | 3.0 | 1 | 14.0% | 60.0% | 22.6% | 60.0% | 25.4% |
| rulegen_all_plus_forward_gloss | off | 3.0 | 2 | 12.9% | 80.0% | 22.2% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | off | 3.0 | 3 | 12.1% | 80.0% | 21.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | off | 4.0 | 1 | 15.8% | 60.0% | 25.0% | 60.0% | 21.7% |
| rulegen_all_plus_forward_gloss | off | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 21.7% |
| rulegen_all_plus_forward_gloss | off | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 21.7% |
| rulegen_all_plus_forward_gloss | off | 5.0 | 1 | 40.0% | 60.0% | 48.0% | 60.0% | 5.1% |
| rulegen_all_plus_forward_gloss | off | 5.0 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_all_plus_forward_gloss | off | 5.0 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 1 | 14.0% | 60.0% | 22.6% | 60.0% | 25.4% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 2 | 12.9% | 80.0% | 22.2% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 3.0 | 3 | 12.1% | 80.0% | 21.1% | 80.0% | 25.4% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 1 | 15.8% | 60.0% | 25.0% | 60.0% | 21.7% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 2 | 14.3% | 80.0% | 24.2% | 80.0% | 21.7% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 4.0 | 3 | 13.8% | 80.0% | 23.5% | 80.0% | 21.7% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 1 | 40.0% | 60.0% | 48.0% | 60.0% | 5.1% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 2 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |
| rulegen_all_plus_forward_gloss | sense_label_pos_v1 | 5.0 | 3 | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% |

## Best Rows By Mode
- `benchmark_reviewed` best row: pruning `off`, `min_score=3.0`, `max_promoted=1` -> precision `20.0%`, recall `90.0%`, overblocking `26.1%`
- `rulegen_top3_plus_forward_gloss` best row: pruning `off`, `min_score=5.0`, `max_promoted=2` -> precision `47.1%`, recall `80.0%`, overblocking `5.1%`
- `rulegen_all_plus_forward_gloss` best row: pruning `off`, `min_score=5.0`, `max_promoted=2` -> precision `47.1%`, recall `80.0%`, overblocking `5.1%`
