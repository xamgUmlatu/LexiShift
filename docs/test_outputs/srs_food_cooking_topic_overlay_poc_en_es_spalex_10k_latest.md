# en-es Food/Cooking Topic Overlay PoC

- Status: `ok`
- Decision: `srs_food_cooking_topic_overlay_poc_ready`
- Generated: `2026-05-19T03:40:51+00:00`
- Frequency DB: `/private/tmp/lexishift-spalex-audit/data-root/frequency_packs/freq-es-spalex-expanded-v1/main.sqlite`
- Overlay rows: `91`
- Overlay confidence: `{'light': 37, 'strong': 54}`

## Findings

- `PASS` `topic_overlay_ready`: Food/cooking overlay candidate was built.
- `PASS` `seed_frontier_loaded`: SRS seed frontier loaded.
- `PASS` `overlay_lifts_profile:food_cooking`: Overlay increases food/cooking rows in the profile preview.

## Profile Scenario

### `food_cooking`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `20`
- overlay hit delta: `20`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `chile` | 1344 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 2 | `pan` | 1858 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 3 | `maíz` | 2441 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 4 | `aceite` | 2457 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 5 | `trigo` | 2567 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 6 | `arroz` | 2796 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 7 | `fruta` | 3171 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 8 | `manzana` | 3979 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 9 | `postre` | 4143 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 10 | `limón` | 4244 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 11 | `tomate` | 4245 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 12 | `uva` | 4471 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 13 | `cebolla` | 4798 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 14 | `ajo` | 4862 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 15 | `mantequilla` | 4909 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 16 | `patata` | 5758 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 17 | `verdura` | 6207 | `food_cooking` | `food_cooking` | 1.0 | `topic_hint:food_cooking` |
| 18 | `huevo` | 3293 | `biology, food_cooking, natural_sciences` | `food_cooking` | 0.57735 | `topic_hint:food_cooking` |
| 19 | `agua` | 1193 | `climatology, food_cooking, meteorology, natural_sciences` | `food_cooking` | 0.5 | `topic_hint:food_cooking` |
| 20 | `sal` | 2264 | `chemistry, food_cooking, natural_sciences, physical_sciences` | `food_cooking` | 0.5 | `topic_hint:food_cooking` |
| 21 | `siglo` | 1 | `` | `` | 0.0 | `None` |
| 22 | `millón` | 2 | `` | `` | 0.0 | `None` |
| 23 | `hora` | 3 | `education` | `` | 0.0 | `None` |
| 24 | `música` | 4 | `` | `` | 0.0 | `None` |


## Limitations

- This PoC does not install or enable a product overlay.
- Light accepted labels are included with lower membership in the artifact, but are not injected into profile_topics because current profile-bootstrap scoring consumes topic presence rather than scalar membership.
- The result proves reviewed-label integration for the current frontier; it does not solve food/cooking recall.
