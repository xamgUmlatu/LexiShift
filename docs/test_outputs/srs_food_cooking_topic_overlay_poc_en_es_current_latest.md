# en-es Food/Cooking Topic Overlay PoC

- Status: `ok`
- Decision: `srs_food_cooking_topic_overlay_poc_ready`
- Generated: `2026-05-19T01:09:56+00:00`
- Frequency DB: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-cde.sqlite`
- Overlay rows: `37`
- Overlay confidence: `{'light': 18, 'strong': 19}`

## Findings

- `PASS` `topic_overlay_ready`: Food/cooking overlay candidate was built.
- `PASS` `seed_frontier_loaded`: SRS seed frontier loaded.
- `PASS` `overlay_lifts_profile:food_cooking`: Overlay increases food/cooking rows in the profile preview.

## Profile Scenario

### `food_cooking`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `7`
- overlay hit delta: `7`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `té` | 144 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 2 | `naranja` | 189 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 3 | `siglo` | 1 | `` | `` | 0.0 | `None` |
| 4 | `dulce` | 255 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 5 | `cereal` | 262 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 6 | `millón` | 2 | `` | `` | 0.0 | `None` |
| 7 | `hora` | 3 | `` | `` | 0.0 | `None` |
| 8 | `caldo` | 426 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 9 | `música` | 4 | `` | `` | 0.0 | `None` |
| 10 | `principio` | 5 | `` | `` | 0.0 | `None` |
| 11 | `movimiento` | 6 | `` | `` | 0.0 | `None` |
| 12 | `luz` | 7 | `` | `` | 0.0 | `None` |
| 13 | `mayoría` | 8 | `` | `` | 0.0 | `None` |
| 14 | `ensalada` | 576 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 15 | `fondo` | 9 | `` | `` | 0.0 | `None` |
| 16 | `hermano` | 10 | `` | `` | 0.0 | `None` |
| 17 | `producción` | 11 | `` | `` | 0.0 | `None` |
| 18 | `tortilla` | 647 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 19 | `teatro` | 12 | `` | `` | 0.0 | `None` |
| 20 | `área` | 13 | `` | `` | 0.0 | `None` |
| 21 | `autor` | 14 | `` | `` | 0.0 | `None` |
| 22 | `capital` | 15 | `` | `` | 0.0 | `None` |
| 23 | `estilo` | 16 | `` | `` | 0.0 | `None` |
| 24 | `resto` | 17 | `` | `` | 0.0 | `None` |


## Limitations

- This PoC does not install or enable a product overlay.
- Light accepted labels are included with lower membership in the artifact, but are not injected into profile_topics because current profile-bootstrap scoring consumes topic presence rather than scalar membership.
- The result proves reviewed-label integration for the current frontier; it does not solve food/cooking recall.
