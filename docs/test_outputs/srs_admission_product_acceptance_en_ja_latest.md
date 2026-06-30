# en-ja SRS Admission Preference Sample Pack

- status: `WARN`
- findings: pass=19 warn=3 fail=0
- scenarios: `20`
- topic scenarios with movers: `6` / `9`
- runtime scope: `admission_preview_only`

## Method

- strategy: `profile_bootstrap`
- profile shape: single proficiency estimate plus optional topic_weights/interests
- runtime difficulty source: profile_bootstrap uses the corrected en-ja learner-difficulty CSV through an explicit runtime hook when the CSV is available; otherwise it falls back to runtime commonness signals.
- state mutation: none; previews run under a temporary helper data root

## Inputs

- config_json: `docs/test_inputs/srs_admission_product_acceptance_configs_en_ja.json`
- frequency_db: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj/main.sqlite`
- jmdict: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/jmdict-ja-en/JMdict_e`
- overlay_source_path: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/srs_jmdict_topic_overlay_en_ja_latest.json`
- corrected_ranking_available: `True`
- set_top_n: `10000`
- initial_active_count: `80`
- preview_count: `80`
- preview_sampling_mode: `reserved_topic_lane`

## Overlay Inventory

- status: `ok`
- overlay_id: `srs_jmdict_topic_overlay_en_ja_approved_candidate_v1`
- row_count: `65`
- runtime_supported_row_count: `8`
- runtime_min_membership: `1.0`

| Topic | Rows | Runtime-Supported Rows |
| --- | ---: | ---: |
| `animals` | 2 | 0 |
| `arts_literature_humanities` | 11 | 0 |
| `finance_business` | 9 | 2 |
| `games` | 7 | 1 |
| `law_politics_civics` | 2 | 1 |
| `medicine_health` | 4 | 1 |
| `music_media_entertainment` | 1 | 0 |
| `plants_nature` | 1 | 0 |
| `science_technology` | 16 | 2 |
| `sports_fitness` | 10 | 1 |
| `travel_places_transport` | 2 | 0 |

## Taxonomy Coverage

| Family | Readiness | Overlay Rows | Runtime-Supported Rows |
| --- | --- | ---: | ---: |
| `medicine_health` | `source_ready_candidate` | 4 | 1 |
| `finance_business` | `source_ready_candidate` | 9 | 2 |
| `sports_fitness` | `source_ready_candidate` | 10 | 1 |
| `games` | `source_ready_candidate` | 7 | 1 |
| `music_media_entertainment` | `source_ready_candidate` | 1 | 0 |
| `law_politics_civics` | `source_ready_candidate` | 2 | 1 |
| `science_technology` | `source_ready_candidate` | 16 | 2 |
| `travel_places_transport` | `partial_source_candidate` | 2 | 0 |
| `arts_literature_humanities` | `partial_source_candidate` | 11 | 0 |
| `animals` | `p0_enrichment_candidate` | 2 | 0 |
| `plants_nature` | `p0_enrichment_candidate` | 1 | 0 |
| `food_cooking` | `source_ready_candidate` | 0 | 0 |
| `anime_manga_pop_culture` | `source_thin_candidate` | 0 | 0 |
| `hobbies_crafts` | `source_thin_candidate` | 0 | 0 |
| `casual_slang_register` | `review_only` | 0 | 0 |
| `formal_professional_register` | `review_only` | 0 | 0 |

## Scenario Summary

| Scenario | Proficiency | Topics | Topic Movers | Overlay | Difficulty Mismatches | Top Lemmas |
| --- | ---: | --- | ---: | --- | ---: | --- |
| `neutral_p00` | 0.000 | - | 0 | - | 0 | する, いる, 言う, ある, なる, こと, その, 物 |
| `neutral_p10` | 0.100 | - | 0 | - | 0 | する, いる, ある, 言う, こと, なる, その, よう |
| `neutral_p20` | 0.200 | - | 0 | - | 0 | ある, こと, する, 無い, よう, その, いる, 思う |
| `neutral_p30` | 0.300 | - | 0 | - | 0 | ある, 無い, こと, よう, 出来る, 因る, 時, 思う |
| `neutral_p40` | 0.400 | - | 0 | - | 0 | 無い, 出来る, 御座る, 良く, 矢張り, 共, どの, あるいは |
| `neutral_p50` | 0.500 | - | 0 | - | 0 | 御座る, どの, あるいは, はず, 共, ほとんど, あまり, 矢張り |
| `neutral_p60` | 0.600 | - | 0 | - | 0 | 御座る, どの, あるいは, はず, 項, ほとんど, あまり, 感 |
| `neutral_p70` | 0.700 | - | 0 | - | 0 | 項, 感, すごい, いろいろ, 御座る, なかなか, きれい, はじめ |
| `neutral_p80` | 0.800 | - | 0 | - | 0 | ご飯, ごみ, おじ, あまり, 出かける, たまに, もっとも, だんだん |
| `neutral_p90` | 0.900 | - | 0 | - | 0 | だいぶ, うるさい, うち, まっすぐ, めがね, こんにちは, クリア, かばん |
| `neutral_p100` | 1.000 | - | 0 | - | 0 | ファー, デス, プレース, かばん, バイオマス, こんにちは, ワンピ, パラレル |
| `finance_business_p45` | 0.450 | finance_business | 2 | applied | 0 | 債権, 商標, 無い, 御座る, 良く, 矢張り, 共, どの |
| `science_technology_p45` | 0.450 | science_technology | 1 | applied | 0 | ブロードバンド, 無い, 御座る, 良く, 矢張り, 共, どの, あるいは |
| `medicine_health_p45` | 0.450 | medicine_health | 1 | applied | 0 | 脳, 無い, 御座る, 良く, 矢張り, 共, どの, あるいは |
| `sports_fitness_p25` | 0.250 | sports_fitness | 1 | applied | 0 | センター, ある, こと, 無い, よう, 思う, 見る, 出来る |
| `games_p45` | 0.450 | games | 1 | applied | 0 | ステージ, 無い, 御座る, 良く, 矢張り, 共, どの, あるいは |
| `mixed_business_tech_p50` | 0.500 | science_technology, finance_business | 3 | applied | 0 | 債権, 商標, ブロードバンド, 御座る, どの, あるいは, はず, 共 |
| `arts_literature_p72` | 0.720 | arts_literature_humanities | 0 | unavailable | 0 | 項, なかなか, きれい, いろいろ, 論, はじめ, 府, すごい |
| `food_cooking_p20` | 0.200 | food_cooking | 0 | unavailable | 0 | ある, こと, する, 無い, よう, その, いる, 思う |
| `anime_manga_p45` | 0.450 | anime_manga_pop_culture | 0 | unavailable | 0 | 無い, 御座る, 良く, 矢張り, 共, どの, あるいは, はず |

## Findings

- `PASS` `TOPIC_OVERLAY_AVAILABLE`: Product-shaped en-ja topic overlay was available for preview.
- `PASS` `CORRECTED_RANKING_DIAGNOSTIC_AVAILABLE`: Corrected learner-difficulty ranking was joined for diagnostics.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p00`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p10`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p20`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p30`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p40`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p50`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p60`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p70`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p80`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p90`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p100`: Neutral profile generated an admission preview.
- `PASS` `TOPIC_PROFILE_PREVIEW:finance_business_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_technology_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_business_tech_p50`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:arts_literature_p72`: Requested topic is unsupported by the current runtime overlay.
- `WARN` `TOPIC_PROFILE_PREVIEW:food_cooking_p20`: Requested topic is unsupported by the current runtime overlay.
- `WARN` `TOPIC_PROFILE_PREVIEW:anime_manga_p45`: Requested topic is unsupported by the current runtime overlay.

## Scenario Details

### `neutral_p00`

No topic preference, absolute beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `いる` |  | - | 0.005 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ある` |  | - | 0.120 |  | 1.000 | 26 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `なる` |  | - | 0.005 |  | 1.000 | 47 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `こと` |  | - | 0.120 |  | 1.000 | 1 -> 6 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 7 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `物` | もの | 0.004 | 0.004 |  | 1.000 | 2 -> 8 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 9 | `よう` |  | - | 0.120 |  | 1.000 | 13 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `それ` |  | - | 0.008 |  | 1.000 | 2526 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `この` |  | - | 0.030 |  | 1.000 | 2479 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `来る` | くる | 0.003 | 0.003 |  | 1.000 | 131 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `行く` | いく | 0.004 | 0.004 |  | 1.000 | 143 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `これ` |  | - | 0.005 |  | 1.000 | 2820 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `私` |  | - | 0.040 |  | 1.000 | 2883 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `何` | なに | 0.006 | 0.006 |  | 1.000 | 3008 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `人` | ひと | 0.005 | 0.005 |  | 1.000 | 4 -> 20 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `neutral_p10`

No topic preference, early beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `いる` |  | - | 0.005 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ある` |  | - | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `こと` |  | - | 0.120 |  | 1.000 | 1 -> 5 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 6 | `なる` |  | - | 0.005 |  | 1.000 | 47 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `よう` |  | - | 0.120 |  | 1.000 | 13 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 9 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 10 | `この` |  | - | 0.030 |  | 1.000 | 2479 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `物` | もの | 0.004 | 0.004 |  | 1.000 | 2 -> 11 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 12 | `それ` |  | - | 0.008 |  | 1.000 | 2526 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `来る` | くる | 0.003 | 0.003 |  | 1.000 | 131 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `行く` | いく | 0.004 | 0.004 |  | 1.000 | 143 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `これ` |  | - | 0.005 |  | 1.000 | 2820 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `私` |  | - | 0.040 |  | 1.000 | 2883 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `何` | なに | 0.006 | 0.006 |  | 1.000 | 3008 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p20`

No topic preference, upper beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` |  | - | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `こと` |  | - | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 3 | `する` |  | - | 0.005 |  | 0.886 | 9 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `よう` |  | - | 0.120 |  | 1.000 | 13 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `その` |  | - | 0.040 |  | 0.994 | 2189 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `いる` |  | - | 0.005 |  | 0.886 | 22 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `この` |  | - | 0.030 |  | 0.976 | 2479 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `言う` | いう | 0.002 | 0.002 |  | 0.871 | 34 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `私` |  | - | 0.040 |  | 0.994 | 2883 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `なる` |  | - | 0.005 |  | 0.886 | 47 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 17 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 18 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 19 | `そう` | そう | 0.125 | 0.125 |  | 1.000 | 1139 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p30`

No topic preference, lower-intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` |  | - | 0.120 |  | 0.947 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `こと` |  | - | 0.120 |  | 0.947 | 1 -> 3 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 4 | `よう` |  | - | 0.120 |  | 0.947 | 13 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 7 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 8 | `思う` | おもう | 0.124 | 0.124 |  | 0.960 | 135 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 9 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 10 | `見る` | みる | 0.124 | 0.124 |  | 0.961 | 139 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `仕舞う` | しまう | 0.165 | 0.165 |  | 1.000 | 358 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `そう` | そう | 0.125 | 0.125 |  | 0.962 | 1139 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `彼` |  | - | 0.180 |  | 1.000 | 3727 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `遣る` | やる | 0.165 | 0.165 |  | 1.000 | 389 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `下さる` | くださる | 0.166 | 0.166 |  | 1.000 | 479 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `然し` | しかし | 0.168 | 0.168 |  | 1.000 | 4072 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `考える` | かんがえる | 0.125 | 0.125 |  | 0.963 | 354 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `対する` | たいする | 0.167 | 0.167 |  | 1.000 | 499 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `場合` | ばあい | 0.125 | 0.125 |  | 0.964 | 16 -> 20 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `neutral_p40`

No topic preference, intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `出来る` | できる | 0.223 | 0.223 |  | 0.958 | 148 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `税` | ぜい | 0.242 | 0.242 |  | 0.996 | 310 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p50`

No topic preference, upper-intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `共` | とも | 0.322 | 0.322 |  | 0.955 | 84 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `矢張り` | やはり | 0.317 | 0.317 |  | 0.937 | 2477 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `其々` | それぞれ | 0.327 | 0.327 |  | 0.968 | 160 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `すごい` |  | - | 0.540 |  | 1.000 | 775 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `此方` | こちら | 0.321 | 0.321 |  | 0.951 | 6004 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `良く` | よく | 0.298 | 0.298 |  | 0.848 | 2160 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `なお` |  | - | 0.415 |  | 1.000 | 6545 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `当該` | とうがい | 0.398 | 0.398 |  | 1.000 | 365 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `無い` | ない | 0.265 | 0.265 |  | 0.649 | 8 -> 19 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 20 | `いろいろ` |  | - | 0.550 |  | 1.000 | 3858 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p60`

No topic preference, N1-ish proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `すごい` |  | - | 0.540 |  | 1.000 | 775 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `いろいろ` |  | - | 0.550 |  | 1.000 | 3858 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `なかなか` |  | - | 0.559 |  | 1.000 | 4052 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `きれい` |  | - | 0.562 |  | 1.000 | 1010 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `はじめ` |  | - | 0.567 |  | 1.000 | 423 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `しばらく` |  | - | 0.579 |  | 1.000 | 4470 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `なお` |  | - | 0.415 |  | 0.929 | 6545 -> 21 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p70`

No topic preference, post-N1 / early advanced proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `感` | かん | 0.531 | 0.531 |  | 0.979 | 201 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `すごい` |  | - | 0.540 |  | 0.994 | 775 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `いろいろ` |  | - | 0.550 |  | 1.000 | 3858 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `御座る` | ござる | 0.493 | 0.493 |  | 0.825 | 634 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `なかなか` |  | - | 0.559 |  | 1.000 | 4052 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `きれい` |  | - | 0.562 |  | 1.000 | 1010 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `はじめ` |  | - | 0.567 |  | 1.000 | 423 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `あまり` |  | - | 0.509 |  | 0.902 | 3106 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `しばらく` |  | - | 0.579 |  | 1.000 | 4470 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `通ずる` | つうずる | 0.527 | 0.527 |  | 0.968 | 2253 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ほとんど` |  | - | 0.501 |  | 0.868 | 137 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `出かける` |  | - | 0.605 |  | 1.000 | 2923 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `おじ` |  | - | 0.620 |  | 1.000 | 914 -> 21 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `はず` |  | - | 0.490 |  | 0.807 | 111 -> 22 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p80`

No topic preference, advanced-tail proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ご飯` |  | - | 0.630 |  | 0.976 | 1042 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ごみ` |  | - | 0.645 |  | 0.999 | 1266 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `おじ` |  | - | 0.620 |  | 0.948 | 914 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `あまり` |  | - | 0.619 |  | 0.946 | 1796 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `出かける` |  | - | 0.605 |  | 0.885 | 2923 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `たまに` |  | - | 0.672 |  | 1.000 | 6418 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `もっとも` |  | - | 0.676 |  | 1.000 | 7997 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `だんだん` |  | - | 0.686 |  | 1.000 | 6723 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `めがね` |  | - | 0.707 |  | 1.000 | 2490 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `項` | こう | 0.572 | 0.572 |  | 0.691 | 129 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `うるさい` |  | - | 0.720 |  | 1.000 | 4257 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `だいぶ` |  | - | 0.726 |  | 1.000 | 7414 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `しばらく` |  | - | 0.579 |  | 0.736 | 4470 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `論` | ろん | 0.576 | 0.576 |  | 0.721 | 424 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `うち` |  | - | 0.751 |  | 1.000 | 3801 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `府` | ふ | 0.574 | 0.574 |  | 0.706 | 455 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `いろいろ` |  | - | 0.573 |  | 0.703 | 1149 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `まっすぐ` |  | - | 0.757 |  | 1.000 | 5435 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `こんにちは` |  | - | 0.760 |  | 1.000 | 8680 -> 21 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p90`

No topic preference, very advanced proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `だいぶ` |  | - | 0.726 |  | 0.966 | 7414 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `うるさい` |  | - | 0.720 |  | 0.948 | 4257 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `うち` |  | - | 0.751 |  | 1.000 | 3801 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `まっすぐ` |  | - | 0.757 |  | 1.000 | 5435 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `めがね` |  | - | 0.707 |  | 0.895 | 2490 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `こんにちは` |  | - | 0.760 |  | 1.000 | 8680 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `クリア` | くりあ | 0.720 | 0.720 |  | 0.948 | 3366 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `かばん` |  | - | 0.766 |  | 1.000 | 4397 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `だんだん` |  | - | 0.686 |  | 0.784 | 6723 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `もっとも` |  | - | 0.676 |  | 0.719 | 7997 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `あまり` |  | - | 0.674 |  | 0.709 | 1765 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `たまに` |  | - | 0.672 |  | 0.697 | 6418 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 0.926 | 6822 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `シックス` | しっくす | 0.724 | 0.724 |  | 0.961 | 7579 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `レフ` | れふ | 0.710 | 0.710 |  | 0.907 | 7249 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `デス` | です | 0.937 | 0.937 |  | 1.000 | 8001 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p100`

No topic preference, full-range / recondite-tail proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `デス` | です | 0.937 | 0.937 |  | 1.000 | 8001 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `プレース` | ぷれーす | 0.937 | 0.937 |  | 1.000 | 8605 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `かばん` |  | - | 0.766 |  | 0.656 | 4397 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `バイオマス` | ばいおます | 0.937 | 0.937 |  | 1.000 | 8832 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `こんにちは` |  | - | 0.760 |  | 0.615 | 8680 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `ワンピ` | わんぴ | 0.937 | 0.937 |  | 1.000 | 8927 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `パラレル` | ぱられる | 0.937 | 0.937 |  | 1.000 | 8933 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `まっすぐ` |  | - | 0.757 |  | 0.592 | 5435 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ホールディング` | ほーるでぃんぐ | 0.937 | 0.937 |  | 1.000 | 9009 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ラッテ` | らって | 0.937 | 0.937 |  | 1.000 | 9015 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ハザード` | はざーど | 0.790 | 0.790 |  | 0.804 | 8233 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `うち` |  | - | 0.751 |  | 0.554 | 3801 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `デバッグ` | でばっぐ | 0.937 | 0.937 |  | 1.000 | 9063 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `シュラフ` | しゅらふ | 0.937 | 0.937 |  | 1.000 | 9070 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `パラサイト` | ぱらさいと | 0.937 | 0.937 |  | 1.000 | 9085 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハンドラー` | はんどらー | 0.937 | 0.937 |  | 1.000 | 9091 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ソール` | そーる | 0.937 | 0.937 |  | 1.000 | 9113 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ジェラート` | じぇらーと | 0.937 | 0.937 |  | 1.000 | 9133 -> 19 | Boosted by proficiency_fit. |
| 20 | `ペペロンチーノ` | ぺぺろんちーの | 0.937 | 0.937 |  | 1.000 | 9163 -> 20 | Boosted by proficiency_fit. |

### `finance_business_p45`

Finance/business preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['finance_business']` applied_seed_count=`2`

Active topic support:

- `finance_business` candidates=2 mass=0.574996 scarcity=insufficient_labeled_support examples=債権, 商標

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:finance_business | 1.000 | 941 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `商標` | しょうひょう | 0.406 | 0.406 | topic_hint:finance_business | 1.000 | 5782 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `science_technology_p45`

Science/technology preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['science_technology']` applied_seed_count=`1`

Active topic support:

- `science_technology` candidates=1 mass=0.156124 scarcity=insufficient_labeled_support examples=ブロードバンド

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 | topic_hint:science_technology | 1.000 | 7260 -> 86 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_p45`

Medicine/health preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`1`

Active topic support:

- `medicine_health` candidates=1 mass=0.386449 scarcity=insufficient_labeled_support examples=脳

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p25`

Sports preference at low proficiency; topic items should still respect readiness.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`1`

Active topic support:

- `sports_fitness` candidates=1 mass=0.490494 scarcity=insufficient_labeled_support examples=センター

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 1.000 | 158 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ある` |  | - | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `こと` |  | - | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 4 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `よう` |  | - | 0.120 |  | 1.000 | 13 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 10 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 11 | `良い` | よい | 0.080 | 0.080 |  | 0.976 | 24 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 12 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 13 | `そう` | そう | 0.125 | 0.125 |  | 1.000 | 1139 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `考える` | かんがえる | 0.125 | 0.125 |  | 1.000 | 354 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `仕舞う` | しまう | 0.165 | 0.165 |  | 1.000 | 358 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `場合` | ばあい | 0.125 | 0.125 |  | 1.000 | 16 -> 17 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `彼` |  | - | 0.180 |  | 1.000 | 3727 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `遣る` | やる | 0.165 | 0.165 |  | 1.000 | 389 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `行う` | おこなう | 0.125 | 0.125 |  | 1.000 | 444 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `games_p45`

Games preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`1`

Active topic support:

- `games` candidates=1 mass=0.298593 scarcity=insufficient_labeled_support examples=ステージ

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_business_tech_p50`

Weighted mixed professional interests.

- overlay: status=`active` application=`applied` active_topics=`['science_technology', 'finance_business']` applied_seed_count=`3`

Active topic support:

- `finance_business` candidates=2 mass=0.574996 scarcity=insufficient_labeled_support examples=債権, 商標
- `science_technology` candidates=1 mass=0.156124 scarcity=insufficient_labeled_support examples=ブロードバンド

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:finance_business | 1.000 | 941 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `商標` | しょうひょう | 0.406 | 0.406 | topic_hint:finance_business | 1.000 | 5782 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 | topic_hint:science_technology | 1.000 | 7260 -> 49 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `共` | とも | 0.322 | 0.322 |  | 0.955 | 84 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `矢張り` | やはり | 0.317 | 0.317 |  | 0.937 | 2477 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `其々` | それぞれ | 0.327 | 0.327 |  | 0.968 | 160 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `すごい` |  | - | 0.540 |  | 1.000 | 775 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `此方` | こちら | 0.321 | 0.321 |  | 0.951 | 6004 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `良く` | よく | 0.298 | 0.298 |  | 0.848 | 2160 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `なお` |  | - | 0.415 |  | 1.000 | 6545 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_p72`

Arts/literature/humanities preference at advanced proficiency; documents current overlay coverage.

- overlay: status=`unavailable` application=`None` active_topics=`[]` applied_seed_count=`None`

Active topic support:

- `arts_literature_humanities` candidates=0 mass=0.0 scarcity=insufficient_labeled_support examples=

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `なかなか` |  | - | 0.559 |  | 0.993 | 4052 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `きれい` |  | - | 0.562 |  | 0.996 | 1010 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `いろいろ` |  | - | 0.550 |  | 0.977 | 3858 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `はじめ` |  | - | 0.567 |  | 1.000 | 423 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `すごい` |  | - | 0.540 |  | 0.948 | 775 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `感` | かん | 0.531 | 0.531 |  | 0.913 | 201 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `しばらく` |  | - | 0.579 |  | 1.000 | 4470 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `出かける` |  | - | 0.605 |  | 1.000 | 2923 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `あまり` |  | - | 0.619 |  | 1.000 | 1796 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `おじ` |  | - | 0.620 |  | 1.000 | 914 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ご飯` |  | - | 0.630 |  | 1.000 | 1042 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `通ずる` | つうずる | 0.527 | 0.527 |  | 0.893 | 2253 -> 21 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p20`

Food/cooking preference at upper beginner proficiency; documents current overlay coverage.

- overlay: status=`unavailable` application=`None` active_topics=`[]` applied_seed_count=`None`

Active topic support:

- `food_cooking` candidates=0 mass=0.0 scarcity=insufficient_labeled_support examples=

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` |  | - | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `こと` |  | - | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 3 | `する` |  | - | 0.005 |  | 0.886 | 9 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `よう` |  | - | 0.120 |  | 1.000 | 13 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `その` |  | - | 0.040 |  | 0.994 | 2189 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `いる` |  | - | 0.005 |  | 0.886 | 22 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `この` |  | - | 0.030 |  | 0.976 | 2479 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `言う` | いう | 0.002 | 0.002 |  | 0.871 | 34 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `私` |  | - | 0.040 |  | 0.994 | 2883 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `なる` |  | - | 0.005 |  | 0.886 | 47 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 17 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 18 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 19 | `そう` | そう | 0.125 | 0.125 |  | 1.000 | 1139 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `anime_manga_p45`

Anime/manga/pop-culture preference at intermediate proficiency; documents current overlay coverage.

- overlay: status=`unavailable` application=`None` active_topics=`[]` applied_seed_count=`None`

Active topic support:

- `anime_manga_pop_culture` candidates=0 mass=0.0 scarcity=insufficient_labeled_support examples=

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `どの` |  | - | 0.486 |  | 1.000 | 5480 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `あるいは` |  | - | 0.486 |  | 1.000 | 5482 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `はず` |  | - | 0.490 |  | 1.000 | 111 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ほとんど` |  | - | 0.501 |  | 1.000 | 137 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `あまり` |  | - | 0.509 |  | 1.000 | 3106 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `なお` |  | - | 0.415 |  | 1.000 | 6545 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
