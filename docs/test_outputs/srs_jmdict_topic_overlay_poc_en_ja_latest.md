# en-ja JMDict Topic Overlay PoC

- Status: `ok`
- Decision: `srs_jmdict_topic_overlay_poc_ready`
- Generated: `2026-06-10T00:46:55+00:00`
- Frequency DB: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj.sqlite`
- JMDict: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/JMdict_e`
- Overlay rows: `65`
- Overlay topics: `{'animals': 2, 'arts_literature_humanities': 11, 'finance_business': 9, 'games': 7, 'law_politics_civics': 2, 'medicine_health': 4, 'music_media_entertainment': 1, 'plants_nature': 1, 'science_technology': 16, 'sports_fitness': 10, 'travel_places_transport': 2}`
- Overlay confidence: `{'light': 57, 'strong': 8}`

## Findings

- `PASS` `frequency_db_present`: Frequency DB: /Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj.sqlite
- `PASS` `jmdict_present`: JMDict: /Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/JMdict_e
- `PASS` `topic_overlay_ready`: en-ja topic overlay candidate was built.
- `PASS` `seed_frontier_loaded`: SRS seed frontier loaded.
- `PASS` `overlay_lifts_at_least_one_profile`: Overlay increases topic rows for at least one profile scenario.
- `PASS` `overlay_lifts_profile:finance_business`: Overlay increases finance_business rows in the profile preview.
- `WARN` `overlay_lifts_profile:games`: Overlay does not increase games rows in the top preview.
- `PASS` `overlay_lifts_profile:law_politics_civics`: Overlay increases law_politics_civics rows in the profile preview.
- `PASS` `overlay_lifts_profile:medicine_health`: Overlay increases medicine_health rows in the profile preview.
- `WARN` `overlay_lifts_profile:science_technology`: Overlay does not increase science_technology rows in the top preview.
- `PASS` `overlay_lifts_profile:sports_fitness`: Overlay increases sports_fitness rows in the profile preview.

## Profile Scenarios

### `finance_business`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `1`
- overlay hit delta: `1`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 3 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 4 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 5 | `為` | 5 | `` | `` | 0.0 | `None` |
| 6 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 7 | `た` | 7 | `` | `` | 0.0 | `None` |
| 8 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 9 | `する` | 9 | `` | `` | 0.0 | `None` |
| 10 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 11 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 12 | `債権` | 941 | `finance_business` | `finance_business` | 1.0 | `topic_hint:finance_business` |
| 13 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 14 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 15 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 16 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 17 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 18 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 19 | `前` | 507 | `` | `` | 0.0 | `None` |
| 20 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 21 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 22 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 23 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 24 | `ます` | 23 | `` | `` | 0.0 | `None` |

### `games`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `0`
- overlay hit delta: `0`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 3 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 4 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 5 | `為` | 5 | `` | `` | 0.0 | `None` |
| 6 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 7 | `た` | 7 | `` | `` | 0.0 | `None` |
| 8 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 9 | `する` | 9 | `` | `` | 0.0 | `None` |
| 10 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 11 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 12 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 13 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 14 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 15 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 16 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 17 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 18 | `前` | 507 | `` | `` | 0.0 | `None` |
| 19 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 20 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 21 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 22 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 23 | `ます` | 23 | `` | `` | 0.0 | `None` |
| 24 | `良い` | 24 | `` | `` | 0.0 | `None` |

### `law_politics_civics`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `1`
- overlay hit delta: `1`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 3 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 4 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 5 | `為` | 5 | `` | `` | 0.0 | `None` |
| 6 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 7 | `た` | 7 | `` | `` | 0.0 | `None` |
| 8 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 9 | `する` | 9 | `` | `` | 0.0 | `None` |
| 10 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 11 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 12 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 13 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 14 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 15 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 16 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 17 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 18 | `前` | 507 | `` | `` | 0.0 | `None` |
| 19 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 20 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 21 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 22 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 23 | `ます` | 23 | `` | `` | 0.0 | `None` |
| 24 | `作戦` | 1736 | `law_politics_civics` | `law_politics_civics` | 1.0 | `topic_hint:law_politics_civics` |

### `medicine_health`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `1`
- overlay hit delta: `1`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 3 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 4 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 5 | `為` | 5 | `` | `` | 0.0 | `None` |
| 6 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 7 | `た` | 7 | `` | `` | 0.0 | `None` |
| 8 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 9 | `脳` | 821 | `medicine_health` | `medicine_health` | 1.0 | `topic_hint:medicine_health` |
| 10 | `する` | 9 | `` | `` | 0.0 | `None` |
| 11 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 12 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 13 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 14 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 15 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 16 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 17 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 18 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 19 | `前` | 507 | `` | `` | 0.0 | `None` |
| 20 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 21 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 22 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 23 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 24 | `ます` | 23 | `` | `` | 0.0 | `None` |

### `science_technology`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `0`
- overlay hit delta: `0`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 3 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 4 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 5 | `為` | 5 | `` | `` | 0.0 | `None` |
| 6 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 7 | `た` | 7 | `` | `` | 0.0 | `None` |
| 8 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 9 | `する` | 9 | `` | `` | 0.0 | `None` |
| 10 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 11 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 12 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 13 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 14 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 15 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 16 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 17 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 18 | `前` | 507 | `` | `` | 0.0 | `None` |
| 19 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 20 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 21 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 22 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 23 | `ます` | 23 | `` | `` | 0.0 | `None` |
| 24 | `良い` | 24 | `` | `` | 0.0 | `None` |

### `sports_fitness`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `1`
- overlay hit delta: `1`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `事` | 8602 | `` | `arts_literature_humanities` | 0.0 | `None` |
| 2 | `センター` | 158 | `sports_fitness` | `sports_fitness` | 1.0 | `topic_hint:sports_fitness` |
| 3 | `物` | 8959 | `` | `` | 0.0 | `None` |
| 4 | `時` | 4036 | `` | `` | 0.0 | `None` |
| 5 | `人` | 4240 | `` | `` | 0.0 | `None` |
| 6 | `為` | 5 | `` | `` | 0.0 | `None` |
| 7 | `だ` | 6 | `` | `` | 0.0 | `None` |
| 8 | `た` | 7 | `` | `` | 0.0 | `None` |
| 9 | `無い` | 8 | `` | `` | 0.0 | `None` |
| 10 | `する` | 9 | `` | `` | 0.0 | `None` |
| 11 | `日本` | 10 | `` | `` | 0.0 | `None` |
| 12 | `中` | 8449 | `` | `games` | 0.0 | `None` |
| 13 | `自分` | 12 | `` | `` | 0.0 | `None` |
| 14 | `様` | 8212 | `` | `` | 0.0 | `None` |
| 15 | `所` | 5004 | `` | `` | 0.0 | `None` |
| 16 | `方` | 6365 | `` | `` | 0.0 | `None` |
| 17 | `場合` | 16 | `` | `` | 0.0 | `None` |
| 18 | `今` | 7906 | `` | `` | 0.0 | `None` |
| 19 | `前` | 507 | `` | `` | 0.0 | `None` |
| 20 | `訳` | 3815 | `` | `` | 0.0 | `None` |
| 21 | `問題` | 20 | `` | `` | 0.0 | `None` |
| 22 | `必要` | 21 | `` | `` | 0.0 | `None` |
| 23 | `居る` | 408 | `` | `` | 0.0 | `None` |
| 24 | `ます` | 23 | `` | `` | 0.0 | `None` |


## Limitations

- This PoC does not install, publish, or default-enable a product topic overlay.
- Light accepted labels are retained as lower-membership scalar-ready evidence but are not injected into profile_topics.
- User-approved labels are sufficient for this approved candidate artifact, but default enablement still needs options-flow and runtime smoke.
- The result measures admission movement for reviewed strong labels only; it does not prove broad topic recall.
