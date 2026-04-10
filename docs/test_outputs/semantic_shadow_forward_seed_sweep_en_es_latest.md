# en-es Forward Seed Sweep

- Status: `ok`
- Generated: `2026-04-10T04:40:58Z`
- Sweep meaning: keep the shadow miner and strict `cross_checked_v1` promotion policy fixed, then vary only the maximum word count allowed for forward-gloss-derived automatic trigger seeds.

## Rows
| Max Words | Mode | Seed Triggers | Gold Trigger Coverage | Candidate-Pool Recall | Strict Precision | Strict Recall | Overblocking |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | rulegen_top3_plus_forward_gloss | 362 | 90.0% | 80.0% | 32.0% | 80.0% | 9.4% |
| 1 | rulegen_all_plus_forward_gloss | 364 | 90.0% | 80.0% | 32.0% | 80.0% | 9.4% |
| 2 | rulegen_top3_plus_forward_gloss | 440 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 2 | rulegen_all_plus_forward_gloss | 442 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 3 | rulegen_top3_plus_forward_gloss | 463 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 3 | rulegen_all_plus_forward_gloss | 464 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 4 | rulegen_top3_plus_forward_gloss | 471 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 4 | rulegen_all_plus_forward_gloss | 472 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 5 | rulegen_top3_plus_forward_gloss | 473 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |
| 5 | rulegen_all_plus_forward_gloss | 474 | 90.0% | 80.0% | 29.6% | 80.0% | 10.9% |

## Best Current Rows
- `max_words=1` / `rulegen_top3_plus_forward_gloss`: precision `32.0%`, recall `80.0%`, overblocking `9.4%`
- `max_words=1` / `rulegen_all_plus_forward_gloss`: precision `32.0%`, recall `80.0%`, overblocking `9.4%`
- `max_words=2` / `rulegen_top3_plus_forward_gloss`: precision `29.6%`, recall `80.0%`, overblocking `10.9%`
- `max_words=2` / `rulegen_all_plus_forward_gloss`: precision `29.6%`, recall `80.0%`, overblocking `10.9%`
