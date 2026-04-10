# en-es Trigger Support Sweep

- Status: `ok`
- Generated: `2026-04-10T05:29:04Z`
- Forward seed max words: `1`
- Fixed shadow support score: `min=4.0`, `max_promoted=2`
- Sweep meaning: filter automatic trigger seeds by a compact trigger-support score, then keep the downstream shadow-promotion policy fixed.

## Rows
| Mode | Min Trigger Score | Seed Triggers After | Trigger Keep Rate | Precision | Recall | F1 | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline F1 | Baseline Overblocking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rulegen_top3_plus_forward_gloss | 2.0 | 362 | 100.0% | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 3.0 | 165 | 45.6% | 50.0% | 80.0% | 61.5% | 80.0% | 4.3% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 4.0 | 19 | 5.2% | 66.7% | 20.0% | 30.8% | 20.0% | 0.7% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 5.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_top3_plus_forward_gloss | 6.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_all_plus_forward_gloss | 2.0 | 360 | 98.9% | 47.1% | 80.0% | 59.3% | 80.0% | 5.1% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_all_plus_forward_gloss | 3.0 | 38 | 10.4% | 40.0% | 20.0% | 26.7% | 20.0% | 0.7% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_all_plus_forward_gloss | 4.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_all_plus_forward_gloss | 5.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 47.1% | 80.0% | 59.3% | 5.1% |
| rulegen_all_plus_forward_gloss | 6.0 | 0 | 0.0% | n/a | 0.0% | n/a | 0.0% | 0.0% | 47.1% | 80.0% | 59.3% | 5.1% |

## Best Rows By Mode
- `rulegen_top3_plus_forward_gloss` with `min_trigger_score=3.0`: precision `50.0%`, recall `80.0%`, F1 `61.5%`, overblocking `4.3%`, trigger keep `45.6%`
  Trigger examples dropped at this threshold:
  - `acabar` / `just` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `orgasm` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `agua` / `stream` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- `rulegen_all_plus_forward_gloss` with `min_trigger_score=2.0`: precision `47.1%`, recall `80.0%`, F1 `59.3%`, overblocking `5.1%`, trigger keep `98.9%`
  Trigger examples dropped at this threshold:
  - `hasta` / `up to` score=`1.0` features=['rulegen_all_source', 'active_side_support']
  - `hasta` / `the point of` score=`0.0` features=['rulegen_all_source']
  - `hasta` / `as much as` score=`1.0` features=['rulegen_all_source', 'active_side_support']
