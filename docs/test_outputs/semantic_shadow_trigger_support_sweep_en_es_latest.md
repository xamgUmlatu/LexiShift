# en-es Trigger Support Sweep

- Status: `ok`
- Generated: `2026-04-10T19:12:35Z`
- Forward seed max words: `1`
- Fixed shadow support score: `min=4.0`, `max_promoted=2`
- Sweep meaning: filter automatic trigger seeds by a compact trigger-support score, then keep the downstream shadow-promotion policy fixed.

## Rows
| Mode | Min Trigger Score | Seed Triggers After | Trigger Keep Rate | Precision | Recall | F1 | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline F1 | Baseline Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rulegen_top3_plus_forward_gloss | 2.0 | 362 | 100.0% | 8.0% | 80.0% | 14.5% | 80.0% | 43.5% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_top3_plus_forward_gloss | 3.0 | 165 | 45.6% | 13.6% | 80.0% | 23.2% | 80.0% | 23.9% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_top3_plus_forward_gloss | 4.0 | 19 | 5.2% | 22.2% | 20.0% | 21.1% | 20.0% | 2.9% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_top3_plus_forward_gloss | 5.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_top3_plus_forward_gloss | 6.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_all_plus_forward_gloss | 2.0 | 360 | 98.9% | 8.0% | 80.0% | 14.5% | 80.0% | 43.5% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_all_plus_forward_gloss | 3.0 | 38 | 10.4% | 14.3% | 20.0% | 16.7% | 20.0% | 2.2% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_all_plus_forward_gloss | 4.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_all_plus_forward_gloss | 5.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 8.0% | 80.0% | 14.5% | 43.5% |
| rulegen_all_plus_forward_gloss | 6.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 8.0% | 80.0% | 14.5% | 43.5% |

## Best Rows By Mode
- `rulegen_top3_plus_forward_gloss` with `min_trigger_score=3.0`: precision `13.6%`, recall `80.0%`, F1 `23.2%`, overblocking `23.9%`, trigger keep `45.6%`
  Trigger examples dropped at this threshold:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- `rulegen_all_plus_forward_gloss` with `min_trigger_score=3.0`: precision `14.3%`, recall `20.0%`, F1 `16.7%`, overblocking `2.2%`, trigger keep `10.4%`
  Trigger examples dropped at this threshold:
  - `acabar` / `finish` score=`2.0` features=['rulegen_all_source', 'active_side_support']
  - `acabar` / `cum` score=`2.0` features=['rulegen_all_source', 'active_side_support']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_all_source', 'active_side_support']
