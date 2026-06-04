# en-es Shadow Embedding Bridge Sweep

- Status: `ok`
- Generated: `2026-04-10T21:26:47Z`
- Bridge model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Meaning: keep lexical mining and support-score promotion fixed, then inject a narrow embedding-backed backoff candidate only when lexical mining surfaced no benchmark-target shadow.

## Best Rows
| Mode | Bridge | Min Sim | Top K | Injected | Support Min | Max Promoted | Precision | Recall | Hit Rate | Overblocking |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `21` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `57` | `4.0` | `2` | 11.8% | 90.0% | 90.0% | 35.5% |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `50` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% |

## Rows
| Mode | Bridge | Min Sim | Top K | Support Min | Max Promoted | Precision | Recall | Hit Rate | Overblocking | Underblocked |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `benchmark_reviewed` | `baseline` | n/a | n/a | `4.0` | `1` | 18.5% | 100.0% | 100.0% | 31.9% | `0` |
| `benchmark_reviewed` | `baseline` | n/a | n/a | `4.0` | `2` | 14.3% | 100.0% | 100.0% | 31.9% | `0` |
| `benchmark_reviewed` | `baseline` | n/a | n/a | `4.0` | `3` | 13.9% | 100.0% | 100.0% | 31.9% | `0` |
| `benchmark_reviewed` | `baseline` | n/a | n/a | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `baseline` | n/a | n/a | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `baseline` | n/a | n/a | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `4.0` | `1` | 13.3% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `4.0` | `2` | 11.0% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `4.0` | `3` | 10.8% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `1` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `4.0` | `1` | 13.3% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `4.0` | `2` | 10.0% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `4.0` | `3` | 9.8% | 100.0% | 100.0% | 47.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.60` | `2` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `4.0` | `1` | 16.9% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `4.0` | `2` | 13.3% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `4.0` | `3` | 13.0% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `1` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `4.0` | `1` | 16.9% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `4.0` | `2` | 12.8% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `4.0` | `3` | 12.5% | 100.0% | 100.0% | 35.5% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.65` | `2` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `4.0` | `1` | 17.5% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `4.0` | `2` | 13.7% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `4.0` | `3` | 13.3% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `1` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `4.0` | `1` | 17.5% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `4.0` | `2` | 13.7% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `4.0` | `3` | 13.3% | 100.0% | 100.0% | 34.1% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `5.0` | `1` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `5.0` | `2` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `benchmark_reviewed` | `embedding_bridge` | `0.70` | `2` | `5.0` | `3` | 100.0% | 100.0% | 100.0% | 0.0% | `0` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `4.0` | `1` | 15.8% | 60.0% | 60.0% | 21.7% | `4` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `4.0` | `2` | 14.3% | 80.0% | 80.0% | 21.7% | `2` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `4.0` | `3` | 13.8% | 80.0% | 80.0% | 21.7% | `2` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `baseline` | n/a | n/a | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `4.0` | `1` | 12.1% | 70.0% | 70.0% | 35.5% | `3` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `4.0` | `2` | 11.8% | 90.0% | 90.0% | 35.5% | `1` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `4.0` | `3` | 11.5% | 90.0% | 90.0% | 35.5% | `1` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `1` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `4.0` | `1` | 10.3% | 60.0% | 60.0% | 35.5% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `4.0` | `2` | 10.6% | 90.0% | 90.0% | 35.5% | `1` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `4.0` | `3` | 10.3% | 90.0% | 90.0% | 35.5% | `1` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.60` | `2` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `4.0` | `1` | 14.3% | 60.0% | 60.0% | 24.6% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `4.0` | `2` | 13.3% | 80.0% | 80.0% | 24.6% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `4.0` | `3` | 12.9% | 80.0% | 80.0% | 24.6% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `1` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `4.0` | `1` | 14.3% | 60.0% | 60.0% | 24.6% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `4.0` | `2` | 12.7% | 80.0% | 80.0% | 24.6% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `4.0` | `3` | 12.3% | 80.0% | 80.0% | 24.6% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.65` | `2` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `4.0` | `1` | 14.6% | 60.0% | 60.0% | 23.9% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `4.0` | `2` | 13.6% | 80.0% | 80.0% | 23.9% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `4.0` | `3` | 13.1% | 80.0% | 80.0% | 23.9% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `1` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `4.0` | `1` | 14.6% | 60.0% | 60.0% | 23.9% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `4.0` | `2` | 13.6% | 80.0% | 80.0% | 23.9% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `4.0` | `3` | 13.1% | 80.0% | 80.0% | 23.9% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `5.0` | `1` | 40.0% | 60.0% | 60.0% | 5.1% | `4` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `5.0` | `2` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss` | `embedding_bridge` | `0.70` | `2` | `5.0` | `3` | 47.1% | 80.0% | 80.0% | 5.1% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `4.0` | `1` | 16.7% | 70.0% | 70.0% | 23.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `4.0` | `2` | 12.7% | 80.0% | 80.0% | 23.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `4.0` | `3` | 11.4% | 80.0% | 80.0% | 23.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `baseline` | n/a | n/a | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `4.0` | `1` | 11.9% | 70.0% | 70.0% | 35.5% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `4.0` | `2` | 10.0% | 80.0% | 80.0% | 35.5% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `4.0` | `3` | 9.2% | 80.0% | 80.0% | 35.5% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `1` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `4.0` | `1` | 11.9% | 70.0% | 70.0% | 35.5% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `4.0` | `2` | 9.2% | 80.0% | 80.0% | 35.5% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `4.0` | `3` | 8.5% | 80.0% | 80.0% | 35.5% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.60` | `2` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `4.0` | `1` | 15.6% | 70.0% | 70.0% | 25.4% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `4.0` | `2` | 12.1% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `4.0` | `3` | 11.0% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `1` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `4.0` | `1` | 15.6% | 70.0% | 70.0% | 25.4% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `4.0` | `2` | 11.6% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `4.0` | `3` | 10.5% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.65` | `2` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `4.0` | `1` | 15.6% | 70.0% | 70.0% | 25.4% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `4.0` | `2` | 12.1% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `4.0` | `3` | 11.0% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `1` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `4.0` | `1` | 15.6% | 70.0% | 70.0% | 25.4% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `4.0` | `2` | 12.1% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `4.0` | `3` | 11.0% | 80.0% | 80.0% | 25.4% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `5.0` | `1` | 35.0% | 70.0% | 70.0% | 7.2% | `3` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `5.0` | `2` | 30.8% | 80.0% | 80.0% | 7.2% | `2` |
| `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` | `embedding_bridge` | `0.70` | `2` | `5.0` | `3` | 28.6% | 80.0% | 80.0% | 7.2% | `2` |
