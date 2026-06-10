# en-ja JMDict Topic Source Readiness

- status: `ok`
- decision: `srs_jmdict_topic_source_readiness_completed`
- generated_at: `2026-06-10T00:46:51+00:00`
- language_pair: `en-ja`

## Summary

| Metric | Value |
| --- | ---: |
| `frontier_rows` | `10000` |
| `candidate_like_rows` | `9258` |
| `jmdict_matched_candidate_like_rows` | `8403` |
| `jmdict_strong_matched_candidate_like_rows` | `8363` |
| `trusted_topic_candidate_like_rows` | `1910` |
| `trusted_topic_strong_match_candidate_like_rows` | `866` |
| `families_total` | `16` |
| `families_with_strong_candidate_rows` | `12` |
| `candidate_like_jmdict_match_rate` | `0.907647` |
| `candidate_like_strong_jmdict_match_rate` | `0.903327` |
| `candidate_like_trusted_topic_rate` | `0.206308` |
| `candidate_like_trusted_strong_topic_rate` | `0.093541` |

Strong matches are exact BCCWJ lemma/sublemma matches plus a small set of deterministic orthographic aliases. Reading-only matches are useful inventory but remain homophone-sensitive and need review before lift.

## Family Coverage

| Family | Taxonomy state | Strong candidate rows | Reading-only candidate rows | Top labels | Examples |
| --- | --- | ---: | ---: | --- | --- |
| `medicine_health` | `source_ready_candidate` | `50` | `243` | `anatomy` (146), `medicine` (132), `dentistry` (12), `physiology` (11) | `プロ` rank `1183` `medicine`; `脳` rank `1625` `anatomy`; `形成` rank `1737` `medicine` |
| `finance_business` | `source_ready_candidate` | `36` | `17` | `finance` (42), `economics` (6), `stock market` (5), `business` (3) | `上げる` rank `268` `finance`; `子` rank `386` `finance`; `展開` rank `795` `business` |
| `sports_fitness` | `source_ready_candidate` | `213` | `103` | `baseball` (129), `sports` (98), `sumo` (52), `golf` (29) | `障害` rank `175` `horse racing`; `サービス` rank `323` `sports`; `開く` rank `373` `sports` |
| `games` | `source_ready_candidate` | `114` | `148` | `go (game)` (83), `mahjong` (69), `shogi` (67), `hanafuda` (44) | `為る` rank `8` `shogi`; `成る` rank `23` `shogi`; `中` rank `96` `mahjong` |
| `music_media_entertainment` | `source_ready_candidate` | `39` | `66` | `music` (102), `film` (3), `television` (1) | `たい` rank `89` `music`; `アップ` rank `1022` `film`, `television`; `バス` rank `1147` `music` |
| `law_politics_civics` | `source_ready_candidate` | `34` | `83` | `law` (79), `military` (43) | `表示` rank `944` `law`; `ビル` rank `985` `law`; `被告` rank `1375` `law` |
| `science_technology` | `source_ready_candidate` | `329` | `392` | `computing` (194), `mathematics` (190), `astronomy` (99), `biology` (97) | `成る` rank `23` `computing`; `目` rank `213` `biology`; `法` rank `234` `engineering` |
| `travel_places_transport` | `partial_source_candidate` | `5` | `7` | `aviation` (7), `railway` (5) | `ホーム` rank `635` `railway`; `バンク` rank `3307` `aviation`; `エレベーター` rank `4715` `aviation` |
| `arts_literature_humanities` | `partial_source_candidate` | `108` | `330` | `Buddhism` (362), `Christianity` (35), `philosophy` (24), `Shinto` (16) | `事` rank `18` `Buddhism`; `世界` rank `217` `Buddhism`; `法` rank `234` `Buddhism` |
| `animals` | `p0_enrichment_candidate` | `3` | `29` | `zoology` (23), `ornithology` (8), `veterinary terms` (1), `entomology` (1) | `卵` rank `2845` `zoology`; `ＢＳＥ` rank `7789` `veterinary terms`; `帯` rank `8378` `zoology` |
| `plants_nature` | `p0_enrichment_candidate` | `9` | `55` | `botany` (61), `agriculture` (2), `gardening, horticulture` (1) | `列` rank `2356` `botany`; `英` rank `2904` `botany`; `一環` rank `3703` `botany` |
| `food_cooking` | `source_ready_candidate` | `50` | `35` | `food, cooking` (85) | `どう` rank `95` `food, cooking`; `開く` rank `373` `food, cooking`; `白` rank `522` `food, cooking` |
| `anime_manga_pop_culture` | `source_thin_candidate` | `0` | `0` | - | - |
| `hobbies_crafts` | `source_thin_candidate` | `0` | `0` | - | - |
| `casual_slang_register` | `review_only` | `0` | `0` | - | - |
| `formal_professional_register` | `review_only` | `0` | `0` | - | - |

## Findings

- `PASS` `bccwj_frequency_db_present`: BCCWJ frequency DB path: ~/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj.sqlite
- `PASS` `jmdict_present`: JMDict path: ~/Library/Application Support/LexiShift/LexiShift/language_packs/JMdict_e
- `PASS` `taxonomy_present`: Taxonomy path: docs/test_inputs/srs_topic_preference_taxonomy_en_ja.json
- `PASS` `trusted_jmdict_topics_present`: Strong matched candidate-like rows with trusted topic fields: 866
- `PASS` `source_ready_families_have_candidates`: All source-ready taxonomy families have strong candidate rows.

## Next Gate

This artifact only proves source-readiness. Promotion still needs a pair-local review packet, accepted labels or overlay rows, and admission-preview evidence that selected en-ja topics actually move SRS samples.
