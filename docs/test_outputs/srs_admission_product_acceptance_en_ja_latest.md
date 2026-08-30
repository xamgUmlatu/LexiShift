# en-ja SRS Admission Preference Sample Pack

- status: `PASS`
- findings: pass=32 warn=0 fail=0
- scenarios: `30`
- topic scenarios with movers: `19` / `19`
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
- overlay_source_path: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/srs_topic_autotag_promotion_overlay_en_ja_latest.json`
- corrected_ranking_available: `True`
- set_top_n: `10000`
- initial_active_count: `80`
- preview_count: `80`
- preview_sampling_mode: `reserved_topic_lane`

## Overlay Inventory

- status: `ok`
- overlay_id: `srs_topic_autotag_promotion_overlay_en_ja_product_safe_candidate_v1`
- row_count: `3996`
- runtime_supported_row_count: `831`
- runtime_min_membership: `1.0`

| Topic | Rows | Runtime-Supported Rows |
| --- | ---: | ---: |
| `animals` | 96 | 27 |
| `anime_manga_pop_culture` | 116 | 100 |
| `arts_literature_humanities` | 196 | 47 |
| `computing_internet` | 273 | 129 |
| `food_cooking` | 183 | 55 |
| `games` | 236 | 111 |
| `hobbies_crafts` | 100 | 100 |
| `law_politics_civics` | 346 | 46 |
| `medicine_health` | 509 | 25 |
| `music_media_entertainment` | 282 | 28 |
| `plants_nature` | 159 | 26 |
| `science_math` | 806 | 18 |
| `shopping_money` | 129 | 27 |
| `sports_fitness` | 212 | 24 |
| `travel_places_transport` | 249 | 38 |
| `work_office` | 104 | 30 |

## Taxonomy Coverage

| Family | Readiness | Overlay Rows | Runtime-Supported Rows |
| --- | --- | ---: | ---: |
| `medicine_health` | `source_ready_candidate` | 509 | 25 |
| `finance_business` | `compatibility_parent_candidate` | 0 | 0 |
| `shopping_money` | `source_ready_candidate` | 129 | 27 |
| `work_office` | `source_ready_candidate` | 104 | 30 |
| `sports_fitness` | `source_ready_candidate` | 212 | 24 |
| `games` | `source_ready_candidate` | 236 | 111 |
| `music_media_entertainment` | `source_ready_candidate` | 282 | 28 |
| `law_politics_civics` | `source_ready_candidate` | 346 | 46 |
| `science_technology` | `compatibility_parent_candidate` | 0 | 0 |
| `science_math` | `source_ready_candidate` | 806 | 18 |
| `computing_internet` | `source_ready_candidate` | 273 | 129 |
| `travel_places_transport` | `partial_source_candidate` | 249 | 38 |
| `arts_literature_humanities` | `partial_source_candidate` | 196 | 47 |
| `animals` | `p0_enrichment_candidate` | 96 | 27 |
| `plants_nature` | `p0_enrichment_candidate` | 159 | 26 |
| `food_cooking` | `source_ready_candidate` | 183 | 55 |
| `anime_manga_pop_culture` | `source_thin_candidate` | 116 | 100 |
| `hobbies_crafts` | `source_thin_candidate` | 100 | 100 |
| `casual_slang_register` | `review_only` | 0 | 0 |
| `formal_professional_register` | `review_only` | 0 | 0 |

## Scenario Summary

| Scenario | Proficiency | Topics | Topic Movers | Overlay | Difficulty Mismatches | Top Lemmas |
| --- | ---: | --- | ---: | --- | ---: | --- |
| `neutral_p00` | 0.000 | - | 0 | - | 0 | する, いる, 言う, なる, 物, 来る, 行く, これ |
| `neutral_p10` | 0.100 | - | 0 | - | 0 | する, いる, 言う, なる, その, この, 物, それ |
| `neutral_p20` | 0.200 | - | 0 | - | 0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| `neutral_p30` | 0.300 | - | 0 | - | 0 | 無い, 出来る, 因る, 時, ため, 又, 仕舞う, 彼 |
| `neutral_p40` | 0.400 | - | 0 | - | 0 | 無い, 良く, 矢張り, 共, センター, 其々, 此方, サービス |
| `neutral_p50` | 0.500 | - | 0 | - | 0 | 御座る, 旨い, 我々, なお, 当該, 積り, 成す, レベル |
| `neutral_p60` | 0.600 | - | 0 | - | 0 | 御座る, 項, 感, 我々, 論, 通ずる, 府, 因み |
| `neutral_p70` | 0.700 | - | 0 | - | 0 | 項, 論, 府, 因み, 層, 増, 故, ザ |
| `neutral_p80` | 0.800 | - | 0 | - | 0 | クリア, ウィン, マザー, ジャバ, メソッド, インターフェース, ウォッチ, エステ |
| `neutral_p90` | 0.900 | - | 0 | - | 0 | インターフェース, インナー, ハザード, コスメ, 山桃, 見栄っ張り, 売り越し, 漉し器 |
| `neutral_p100` | 1.000 | - | 0 | - | 0 | ファー, デス, プレース, バイオマス, ワンピ, パラレル, ホールディング, ラッテ |
| `shopping_money_p45` | 0.450 | shopping_money | 19 | applied | 0 | 商品, 価格, 無料, 会計, 債権, 料金, 支払う, 円 |
| `work_office_p45` | 0.450 | work_office | 26 | applied | 0 | 事務, 報告, 資料, 契約, 職員, 社員, 職業, 勤務 |
| `science_math_p45` | 0.450 | science_math | 14 | applied | 0 | 計算, 機械, 実験, 理論, 数字, 化学, 温度, 物理 |
| `computing_internet_p45` | 0.450 | computing_internet | 40 | applied | 0 | 開発, 処理, 条件, 設定, 通信, 登録, 情報, 携帯 |
| `medicine_health_p45` | 0.450 | medicine_health | 17 | applied | 0 | 顔, 胸, 腰, 肩, 脳, 腹, 膝, 皮膚 |
| `sports_fitness_p25` | 0.250 | sports_fitness | 14 | applied | 0 | 野球, ゴルフ, サッカー, ダンス, スキー, テニス, 水泳, 柔道 |
| `games_p45` | 0.450 | games | 34 | applied | 0 | レベル, 大会, 戦略, カード, 作戦, 勝負, ステージ, ルール |
| `anime_manga_p45` | 0.450 | anime_manga_pop_culture | 40 | applied | 0 | 作品, 設定, ファン, 日常, 発売, カード, コメント, 恋愛 |
| `hobbies_crafts_p45` | 0.450 | hobbies_crafts | 38 | applied | 0 | 撮影, 編集, 収集, ブログ, 栽培, ドライブ, キャンプ, 釣り |
| `mixed_work_computing_p50` | 0.500 | computing_internet, work_office | 40 | applied | 0 | サイト, インターネット, 社員, 許可, 職業, 勤務, 削除, 形式 |
| `mixed_food_travel_p35` | 0.350 | food_cooking, travel_places_transport | 40 | applied | 0 | 道路, 酒, バス, 味, 観光, 会場, 船, 茶 |
| `mixed_science_medicine_p50` | 0.500 | science_math, medicine_health | 28 | applied | 0 | 理論, 腹, 化学, 膝, 温度, 皮膚, 心臓, 怪我 |
| `mixed_anime_games_hobbies_p45` | 0.450 | anime_manga_pop_culture, games, hobbies_crafts | 40 | applied | 0 | 作品, 設定, 撮影, レベル, 大会, ファン, 日常, 編集 |
| `arts_literature_p72` | 0.720 | arts_literature_humanities | 6 | applied | 0 | 短歌, 脚本, 歌舞伎, 評論, 寺院, 演劇, 項, 論 |
| `food_cooking_p20` | 0.200 | food_cooking | 40 | applied | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| `music_media_p35` | 0.350 | music_media_entertainment | 25 | applied | 0 | テレビ, 放送, 監督, 番組, 雑誌, 広告, 演奏, 漫画 |
| `law_politics_p60` | 0.600 | law_politics_civics | 20 | applied | 0 | 司法, 条例, 被告, 検察, 政党, 国籍, 税制, 立法 |
| `animals_p30` | 0.300 | animals | 18 | applied | 0 | 犬, 猫, 馬, 鳥, 虫, 牛, 虎, 象 |
| `plants_nature_p40` | 0.400 | plants_nature | 20 | applied | 0 | 地震, 森, 季節, 雲, 林檎, 気温, 台風, 豆 |

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
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_work_computing_p50`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_food_travel_p35`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_science_medicine_p50`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_anime_games_hobbies_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_p72`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_p20`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:music_media_p35`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:law_politics_p60`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:animals_p30`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p40`: Topic preference produced runtime topic movers.

## Scenario Details

### `neutral_p00`

No topic preference, absolute beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `なる` | なる | 0.002 | 0.002 |  | 1.000 | 47 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `物` | もの | 0.004 | 0.004 |  | 1.000 | 2 -> 5 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 6 | `来る` | くる | 0.003 | 0.003 |  | 1.000 | 131 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `行く` | いく | 0.004 | 0.004 |  | 1.000 | 143 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `これ` |  | - | 0.005 |  | 1.000 | 2820 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `それ` |  | - | 0.008 |  | 1.000 | 2526 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `何` | なに | 0.006 | 0.006 |  | 1.000 | 3008 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `人` | ひと | 0.005 | 0.005 |  | 1.000 | 4 -> 11 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 12 | `どう` | どう | 0.007 | 0.007 |  | 1.000 | 1208 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `中` | なか | 0.007 | 0.007 |  | 1.000 | 11 -> 13 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 14 | `自分` | じぶん | 0.007 | 0.007 |  | 1.000 | 12 -> 14 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 15 | `ところ` | ところ | 0.008 | 0.008 |  | 1.000 | 14 -> 15 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 16 | `今` | いま | 0.008 | 0.008 |  | 1.000 | 17 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `先生` | せんせい | 0.000 | 0.000 |  | 1.000 | 104 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `前` | まえ | 0.009 | 0.009 |  | 1.000 | 18 -> 18 | Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit. |
| 19 | `問題` | もんだい | 0.009 | 0.009 |  | 1.000 | 20 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `分かる` | わかる | 0.010 | 0.010 |  | 1.000 | 402 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p10`

No topic preference, early beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `なる` | なる | 0.002 | 0.002 |  | 1.000 | 47 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `この` |  | - | 0.030 |  | 1.000 | 2479 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `物` | もの | 0.004 | 0.004 |  | 1.000 | 2 -> 7 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 8 | `それ` |  | - | 0.008 |  | 1.000 | 2526 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `来る` | くる | 0.003 | 0.003 |  | 1.000 | 131 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `行く` | いく | 0.004 | 0.004 |  | 1.000 | 143 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `これ` |  | - | 0.005 |  | 1.000 | 2820 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `私` |  | - | 0.040 |  | 1.000 | 2883 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `何` | なに | 0.006 | 0.006 |  | 1.000 | 3008 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `人` | ひと | 0.005 | 0.005 |  | 1.000 | 4 -> 15 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 16 | `どう` | どう | 0.007 | 0.007 |  | 1.000 | 1208 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `中` | なか | 0.007 | 0.007 |  | 1.000 | 11 -> 17 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `自分` | じぶん | 0.007 | 0.007 |  | 1.000 | 12 -> 18 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 19 | `ところ` | ところ | 0.008 | 0.008 |  | 1.000 | 14 -> 19 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 20 | `方` | ほう | 0.017 | 0.017 |  | 1.000 | 15 -> 20 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `neutral_p20`

No topic preference, upper beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 3 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `良い` | よい | 0.080 | 0.080 |  | 1.000 | 24 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `その` |  | - | 0.040 |  | 0.994 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 9 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 10 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 10 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 11 | `そう` | そう | 0.125 | 0.125 |  | 1.000 | 1139 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `考える` | かんがえる | 0.125 | 0.125 |  | 1.000 | 354 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `仕舞う` | しまう | 0.165 | 0.165 |  | 1.000 | 358 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `場合` | ばあい | 0.125 | 0.125 |  | 1.000 | 16 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `彼` |  | - | 0.180 |  | 1.000 | 3727 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `遣る` | やる | 0.165 | 0.165 |  | 1.000 | 389 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `私` |  | - | 0.040 |  | 0.994 | 2883 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `行う` | おこなう | 0.125 | 0.125 |  | 1.000 | 444 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `訳` | わけ | 0.127 | 0.127 |  | 1.000 | 19 -> 20 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `neutral_p30`

No topic preference, lower-intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 4 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 5 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 5 | Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit. |
| 6 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `仕舞う` | しまう | 0.165 | 0.165 |  | 1.000 | 358 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `彼` |  | - | 0.180 |  | 1.000 | 3727 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `遣る` | やる | 0.165 | 0.165 |  | 1.000 | 389 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `下さる` | くださる | 0.166 | 0.166 |  | 1.000 | 479 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `然し` | しかし | 0.168 | 0.168 |  | 1.000 | 4072 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `対する` | たいする | 0.167 | 0.167 |  | 1.000 | 499 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `呉れる` | くれる | 0.166 | 0.166 |  | 1.000 | 526 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `会` | かい | 0.169 | 0.169 |  | 1.000 | 27 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `事業` | じぎょう | 0.171 | 0.171 |  | 1.000 | 41 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `付ける` | つける | 0.167 | 0.167 |  | 1.000 | 760 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `人間` | にんげん | 0.169 | 0.169 |  | 1.000 | 48 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `法` | ほう | 0.172 | 0.172 |  | 1.000 | 51 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `貰う` | もらう | 0.167 | 0.167 |  | 1.000 | 794 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p40`

No topic preference, intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 5 | Boosted by proficiency_fit. |
| 6 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 6 | Boosted by proficiency_fit. |
| 7 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 7 | Boosted by proficiency_fit. |
| 8 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 8 | Boosted by proficiency_fit. |
| 9 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 9 | Boosted by proficiency_fit. |
| 10 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 10 | Boosted by proficiency_fit. |
| 11 | `当該` | とうがい | 0.398 | 0.398 |  | 1.000 | 365 -> 11 | Boosted by proficiency_fit. |
| 12 | `奴` | やつ | 0.331 | 0.331 |  | 1.000 | 370 -> 12 | Boosted by proficiency_fit. |
| 13 | `積り` | つもり | 0.356 | 0.356 |  | 1.000 | 418 -> 13 | Boosted by proficiency_fit. |
| 14 | `限り` | かぎり | 0.334 | 0.334 |  | 1.000 | 428 -> 14 | Boosted by proficiency_fit. |
| 15 | `成す` | なす | 0.382 | 0.382 |  | 1.000 | 2258 -> 15 | Boosted by proficiency_fit. |
| 16 | `ホーム` | ほーむ | 0.307 | 0.307 |  | 1.000 | 445 -> 16 | Boosted by proficiency_fit. |
| 17 | `自ら` | みずから | 0.309 | 0.309 |  | 1.000 | 457 -> 17 | Boosted by proficiency_fit. |
| 18 | `エネルギー` | えねるぎー | 0.308 | 0.308 |  | 1.000 | 494 -> 18 | Boosted by proficiency_fit. |
| 19 | `あっ` |  | - | 0.300 |  | 1.000 | 6857 -> 19 | Boosted by proficiency_fit. |
| 20 | `税` | ぜい | 0.242 | 0.242 |  | 0.996 | 310 -> 20 | Boosted by proficiency_fit. |

### `neutral_p50`

No topic preference, upper-intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 2 | Boosted by proficiency_fit. |
| 3 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 3 | Boosted by proficiency_fit. |
| 4 | `なお` | なお | 0.415 | 0.415 |  | 1.000 | 6545 -> 4 | Boosted by proficiency_fit. |
| 5 | `当該` | とうがい | 0.398 | 0.398 |  | 1.000 | 365 -> 5 | Boosted by proficiency_fit. |
| 6 | `積り` | つもり | 0.356 | 0.356 |  | 1.000 | 418 -> 6 | Boosted by proficiency_fit. |
| 7 | `成す` | なす | 0.382 | 0.382 |  | 1.000 | 2258 -> 7 | Boosted by proficiency_fit. |
| 8 | `レベル` | れべる | 0.413 | 0.413 |  | 1.000 | 597 -> 8 | Boosted by proficiency_fit. |
| 9 | `有り難う` | ありがとう | 0.394 | 0.394 |  | 1.000 | 7098 -> 9 | Boosted by proficiency_fit. |
| 10 | `サイト` | さいと | 0.395 | 0.395 |  | 1.000 | 688 -> 10 | Boosted by proficiency_fit. |
| 11 | `ワン` | わん | 0.421 | 0.421 |  | 1.000 | 736 -> 11 | Boosted by proficiency_fit. |
| 12 | `一杯` | いっぱい | 0.365 | 0.365 |  | 1.000 | 756 -> 12 | Boosted by proficiency_fit. |
| 13 | `ファン` | ふぁん | 0.411 | 0.411 |  | 1.000 | 831 -> 13 | Boosted by proficiency_fit. |
| 14 | `インターネット` | いんたーねっと | 0.456 | 0.456 |  | 1.000 | 851 -> 14 | Boosted by proficiency_fit. |
| 15 | `ライン` | らいん | 0.463 | 0.463 |  | 1.000 | 919 -> 15 | Boosted by proficiency_fit. |
| 16 | `齎す` | もたらす | 0.357 | 0.357 |  | 1.000 | 3284 -> 16 | Boosted by proficiency_fit. |
| 17 | `仰る` | おっしゃる | 0.377 | 0.377 |  | 1.000 | 3363 -> 17 | Boosted by proficiency_fit. |
| 18 | `婆` | ばば | 0.393 | 0.393 |  | 1.000 | 1012 -> 18 | Boosted by proficiency_fit. |
| 19 | `バランス` | ばらんす | 0.429 | 0.429 |  | 1.000 | 1055 -> 19 | Boosted by proficiency_fit. |
| 20 | `取り敢えず` | とりあえず | 0.413 | 0.413 |  | 1.000 | 5637 -> 20 | Boosted by proficiency_fit. |

### `neutral_p60`

No topic preference, N1-ish proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit. |
| 4 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 4 | Boosted by proficiency_fit. |
| 5 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 5 | Boosted by proficiency_fit. |
| 6 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 6 | Boosted by proficiency_fit. |
| 7 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 7 | Boosted by proficiency_fit. |
| 8 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 8 | Boosted by proficiency_fit. |
| 9 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 9 | Boosted by proficiency_fit. |
| 10 | `インターネット` | いんたーねっと | 0.456 | 0.456 |  | 1.000 | 851 -> 10 | Boosted by proficiency_fit. |
| 11 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 11 | Boosted by proficiency_fit. |
| 12 | `ライン` | らいん | 0.463 | 0.463 |  | 1.000 | 919 -> 12 | Boosted by proficiency_fit. |
| 13 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 13 | Boosted by proficiency_fit. |
| 14 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 14 | Boosted by proficiency_fit. |
| 15 | `タイム` | たいむ | 0.455 | 0.455 |  | 1.000 | 1096 -> 15 | Boosted by proficiency_fit. |
| 16 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 16 | Boosted by proficiency_fit. |
| 17 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 17 | Boosted by proficiency_fit. |
| 18 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 18 | Boosted by proficiency_fit. |
| 19 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 19 | Boosted by proficiency_fit. |
| 20 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 20 | Boosted by proficiency_fit. |

### `neutral_p70`

No topic preference, post-N1 / early advanced proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 2 | Boosted by proficiency_fit. |
| 3 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 3 | Boosted by proficiency_fit. |
| 4 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 4 | Boosted by proficiency_fit. |
| 5 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 5 | Boosted by proficiency_fit. |
| 6 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 6 | Boosted by proficiency_fit. |
| 7 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 7 | Boosted by proficiency_fit. |
| 8 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 8 | Boosted by proficiency_fit. |
| 9 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 9 | Boosted by proficiency_fit. |
| 10 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 10 | Boosted by proficiency_fit. |
| 11 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 11 | Boosted by proficiency_fit. |
| 12 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 12 | Boosted by proficiency_fit. |
| 13 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 13 | Boosted by proficiency_fit. |
| 14 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 14 | Boosted by proficiency_fit. |
| 15 | `オブ` | おぶ | 0.579 | 0.579 |  | 1.000 | 1683 -> 15 | Boosted by proficiency_fit. |
| 16 | `炉` | ろ | 0.578 | 0.578 |  | 1.000 | 1848 -> 16 | Boosted by proficiency_fit. |
| 17 | `減` | げん | 0.578 | 0.578 |  | 1.000 | 1892 -> 17 | Boosted by proficiency_fit. |
| 18 | `テル` | てる | 0.579 | 0.579 |  | 1.000 | 1920 -> 18 | Boosted by proficiency_fit. |
| 19 | `デ` | で | 0.581 | 0.581 |  | 1.000 | 2111 -> 19 | Boosted by proficiency_fit. |
| 20 | `堪る` | たまる | 0.578 | 0.578 |  | 1.000 | 5134 -> 20 | Boosted by proficiency_fit. |

### `neutral_p80`

No topic preference, advanced-tail proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit. |
| 2 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.999 | 5234 -> 2 | Boosted by proficiency_fit. |
| 3 | `マザー` | まざー | 0.645 | 0.645 |  | 0.998 | 5602 -> 3 | Boosted by proficiency_fit. |
| 4 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 1.000 | 6401 -> 4 | Boosted by proficiency_fit. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 1.000 | 6546 -> 5 | Boosted by proficiency_fit. |
| 6 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 6 | Boosted by proficiency_fit. |
| 7 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 7 | Boosted by proficiency_fit. |
| 8 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 8 | Boosted by proficiency_fit. |
| 9 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 9 | Boosted by proficiency_fit. |
| 10 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 10 | Boosted by proficiency_fit. |
| 11 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 1.000 | 7535 -> 11 | Boosted by proficiency_fit. |
| 12 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 12 | Boosted by proficiency_fit. |
| 13 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 13 | Boosted by proficiency_fit. |
| 14 | `シー` | しー | 0.644 | 0.644 |  | 0.998 | 7303 -> 14 | Boosted by proficiency_fit. |
| 15 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 15 | Boosted by proficiency_fit. |
| 16 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 16 | Boosted by proficiency_fit. |
| 17 | `係属` | けいぞく | 0.696 | 0.696 |  | 1.000 | 8414 -> 18 | Boosted by proficiency_fit. |
| 18 | `木目細か` | きめこまか | 0.667 | 0.667 |  | 1.000 | 8723 -> 19 | Boosted by proficiency_fit. |
| 19 | `カスタマイズ` | かすたまいず | 0.665 | 0.665 |  | 1.000 | 8512 -> 20 | Boosted by proficiency_fit. |
| 20 | `尊皇` | そんのう | 0.652 | 0.652 |  | 1.000 | 8528 -> 21 | Boosted by proficiency_fit. |

### `neutral_p90`

No topic preference, very advanced proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 1 | Boosted by proficiency_fit. |
| 2 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 2 | Boosted by proficiency_fit. |
| 3 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 3 | Boosted by proficiency_fit. |
| 4 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 4 | Boosted by proficiency_fit. |
| 5 | `山桃` | やまもも | 0.782 | 0.782 |  | 1.000 | 9140 -> 5 | Boosted by proficiency_fit. |
| 6 | `見栄っ張り` | みえっぱり | 0.781 | 0.781 |  | 1.000 | 9152 -> 6 | Boosted by proficiency_fit. |
| 7 | `売り越し` | うりこし | 0.785 | 0.785 |  | 1.000 | 9157 -> 7 | Boosted by proficiency_fit. |
| 8 | `漉し器` | こしき | 0.755 | 0.755 |  | 1.000 | 9174 -> 8 | Boosted by proficiency_fit. |
| 9 | `アクアマリン` | あくあまりん | 0.755 | 0.755 |  | 1.000 | 9177 -> 9 | Boosted by proficiency_fit. |
| 10 | `エコシステム` | えこしすてむ | 0.751 | 0.751 |  | 1.000 | 9180 -> 10 | Boosted by proficiency_fit. |
| 11 | `梶木鮪` | かじきまぐろ | 0.784 | 0.784 |  | 1.000 | 9181 -> 11 | Boosted by proficiency_fit. |
| 12 | `党則` | とうそく | 0.761 | 0.761 |  | 1.000 | 9189 -> 12 | Boosted by proficiency_fit. |
| 13 | `チューバ` | ちゅーば | 0.763 | 0.763 |  | 1.000 | 9193 -> 13 | Boosted by proficiency_fit. |
| 14 | `黒痣` | くろあざ | 0.777 | 0.777 |  | 1.000 | 9199 -> 14 | Boosted by proficiency_fit. |
| 15 | `アウトリーチ` | あうとりーち | 0.766 | 0.766 |  | 1.000 | 9200 -> 15 | Boosted by proficiency_fit. |
| 16 | `脱北` | だっぽく | 0.767 | 0.767 |  | 1.000 | 9201 -> 16 | Boosted by proficiency_fit. |
| 17 | `兜蟹` | かぶとがに | 0.791 | 0.791 |  | 1.000 | 9202 -> 17 | Boosted by proficiency_fit. |
| 18 | `飯蛸` | いいだこ | 0.800 | 0.800 |  | 1.000 | 9203 -> 18 | Boosted by proficiency_fit. |
| 19 | `鉄船` | てっせん | 0.771 | 0.771 |  | 1.000 | 9204 -> 19 | Boosted by proficiency_fit. |
| 20 | `丁数` | ちょうすう | 0.774 | 0.774 |  | 1.000 | 9209 -> 20 | Boosted by proficiency_fit. |

### `neutral_p100`

No topic preference, full-range / recondite-tail proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 1 | Boosted by proficiency_fit. |
| 2 | `デス` | です | 0.937 | 0.937 |  | 1.000 | 8001 -> 2 | Boosted by proficiency_fit. |
| 3 | `プレース` | ぷれーす | 0.937 | 0.937 |  | 1.000 | 8605 -> 3 | Boosted by proficiency_fit. |
| 4 | `バイオマス` | ばいおます | 0.937 | 0.937 |  | 1.000 | 8832 -> 4 | Boosted by proficiency_fit. |
| 5 | `ワンピ` | わんぴ | 0.937 | 0.937 |  | 1.000 | 8927 -> 5 | Boosted by proficiency_fit. |
| 6 | `パラレル` | ぱられる | 0.937 | 0.937 |  | 1.000 | 8933 -> 6 | Boosted by proficiency_fit. |
| 7 | `ホールディング` | ほーるでぃんぐ | 0.937 | 0.937 |  | 1.000 | 9009 -> 7 | Boosted by proficiency_fit. |
| 8 | `ラッテ` | らって | 0.937 | 0.937 |  | 1.000 | 9015 -> 8 | Boosted by proficiency_fit. |
| 9 | `デバッグ` | でばっぐ | 0.937 | 0.937 |  | 1.000 | 9063 -> 9 | Boosted by proficiency_fit. |
| 10 | `シュラフ` | しゅらふ | 0.937 | 0.937 |  | 1.000 | 9070 -> 10 | Boosted by proficiency_fit. |
| 11 | `パラサイト` | ぱらさいと | 0.937 | 0.937 |  | 1.000 | 9085 -> 11 | Boosted by proficiency_fit. |
| 12 | `ハンドラー` | はんどらー | 0.937 | 0.937 |  | 1.000 | 9091 -> 12 | Boosted by proficiency_fit. |
| 13 | `ソール` | そーる | 0.937 | 0.937 |  | 1.000 | 9113 -> 13 | Boosted by proficiency_fit. |
| 14 | `ジェラート` | じぇらーと | 0.937 | 0.937 |  | 1.000 | 9133 -> 14 | Boosted by proficiency_fit. |
| 15 | `ペペロンチーノ` | ぺぺろんちーの | 0.937 | 0.937 |  | 1.000 | 9163 -> 15 | Boosted by proficiency_fit. |
| 16 | `ピッケル` | ぴっける | 0.937 | 0.937 |  | 1.000 | 9167 -> 16 | Boosted by proficiency_fit. |
| 17 | `キュイジーヌ` | きゅいじーぬ | 0.937 | 0.937 |  | 1.000 | 9175 -> 17 | Boosted by proficiency_fit. |
| 18 | `と` |  | - | 0.971 |  | 1.000 | 9215 -> 18 | Boosted by proficiency_fit. |
| 19 | `デポ` | でぽ | 0.937 | 0.937 |  | 1.000 | 9185 -> 19 | Boosted by proficiency_fit. |
| 20 | `疾う` | とう | 0.937 | 0.937 |  | 1.000 | 9190 -> 20 | Boosted by proficiency_fit. |

### `shopping_money_p45`

Shopping/money preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `商品` | しょうひん | 0.179 | 0.179 | topic_hint:shopping_money | 1.000 | 239 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `価格` | かかく | 0.183 | 0.183 | topic_hint:shopping_money | 1.000 | 268 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `無料` | むりょう | 0.204 | 0.204 | topic_hint:shopping_money | 1.000 | 608 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `会計` | かいけい | 0.243 | 0.243 | topic_hint:shopping_money | 1.000 | 867 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 1.000 | 941 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `料金` | りょうきん | 0.239 | 0.239 | topic_hint:shopping_money | 1.000 | 945 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `支払う` | しはらう | 0.242 | 0.242 | topic_hint:shopping_money | 1.000 | 3905 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `円` | えん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 1897 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `商店` | しょうてん | 0.309 | 0.309 | topic_hint:shopping_money | 1.000 | 2056 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `現金` | げんきん | 0.252 | 0.252 | topic_hint:shopping_money | 1.000 | 2459 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `代金` | だいきん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 3140 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `コンビニ` | こんびに | 0.280 | 0.280 | topic_hint:shopping_money | 1.000 | 3569 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:shopping_money | 0.990 | 1347 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `レジ` | れじ | 0.167 | 0.167 | topic_hint:shopping_money | 0.989 | 5177 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `予約` | よやく | 0.144 | 0.144 | topic_hint:shopping_money | 0.926 | 1024 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `値段` | ねだん | 0.142 | 0.142 | topic_hint:shopping_money | 0.917 | 1446 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `払う` | はらう | 0.137 | 0.137 | topic_hint:shopping_money | 0.893 | 2821 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `店員` | てんいん | 0.124 | 0.124 | topic_hint:shopping_money | 0.831 | 3508 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `財布` | さいふ | 0.103 | 0.103 | topic_hint:shopping_money | 0.700 | 3939 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_p45`

Work/office preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 1.000 | 242 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 1.000 | 265 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 1.000 | 301 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 1.000 | 321 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 1.000 | 598 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `書類` | しょるい | 0.250 | 0.250 | topic_hint:work_office | 1.000 | 1245 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 1.000 | 1426 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `上司` | じょうし | 0.306 | 0.306 | topic_hint:work_office | 1.000 | 2049 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `役員` | やくいん | 0.329 | 0.329 | topic_hint:work_office | 1.000 | 2114 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `部下` | ぶか | 0.317 | 0.317 | topic_hint:work_office | 1.000 | 2312 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `給料` | きゅうりょう | 0.256 | 0.256 | topic_hint:work_office | 1.000 | 2424 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `面接` | めんせつ | 0.318 | 0.318 | topic_hint:work_office | 1.000 | 2542 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `出張` | しゅっちょう | 0.335 | 0.335 | topic_hint:work_office | 1.000 | 2677 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `同僚` | どうりょう | 0.249 | 0.249 | topic_hint:work_office | 1.000 | 2838 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `雇う` | やとう | 0.258 | 0.258 | topic_hint:work_office | 1.000 | 6652 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `出勤` | しゅっきん | 0.363 | 0.363 | topic_hint:work_office | 1.000 | 4112 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `残業` | ざんぎょう | 0.366 | 0.366 | topic_hint:work_office | 1.000 | 4777 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `science_math_p45`

Science/math preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `計算` | けいさん | 0.198 | 0.198 | topic_hint:science_math | 1.000 | 460 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 1.000 | 758 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 1.000 | 802 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 1.000 | 1058 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 1.000 | 1077 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 1.000 | 1583 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 1.000 | 2269 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 1.000 | 2932 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `地理` | ちり | 0.157 | 0.157 | topic_hint:science_math | 0.970 | 3532 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `数学` | すうがく | 0.155 | 0.155 | topic_hint:science_math | 0.964 | 2301 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `科学` | かがく | 0.129 | 0.129 | topic_hint:science_math | 0.855 | 374 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `研究` | けんきゅう | 0.125 | 0.125 | topic_hint:science_math | 0.836 | 54 -> 14 | Boosted by proficiency_fit, topic_affinity, while remaining supported by coverage_gain. |
| 15 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 18 | Boosted by proficiency_fit. |
| 19 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 19 | Boosted by proficiency_fit. |
| 20 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 20 | Boosted by proficiency_fit. |

### `computing_internet_p45`

Computing/internet preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `開発` | かいはつ | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 122 -> 1 | Boosted by proficiency_fit, topic_affinity, while remaining supported by coverage_gain. |
| 2 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 1.000 | 269 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 1.000 | 275 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `設定` | せってい | 0.177 | 0.177 | topic_hint:computing_internet | 0.999 | 282 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 386 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `登録` | とうろく | 0.178 | 0.178 | topic_hint:computing_internet | 1.000 | 454 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `情報` | じょうほう | 0.169 | 0.169 | topic_hint:computing_internet | 0.993 | 57 -> 7 | Boosted by proficiency_fit, topic_affinity, while remaining supported by coverage_gain. |
| 8 | `携帯` | けいたい | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 628 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `サイト` | さいと | 0.395 | 0.395 | topic_hint:computing_internet | 1.000 | 688 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 1.000 | 710 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `画像` | がぞう | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 732 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `機械` | きかい | 0.216 | 0.216 | topic_hint:computing_internet | 1.000 | 758 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `実行` | じっこう | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 806 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `電子` | でんし | 0.221 | 0.221 | topic_hint:computing_internet | 1.000 | 835 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `画面` | がめん | 0.192 | 0.192 | topic_hint:computing_internet | 1.000 | 854 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `入力` | にゅうりょく | 0.211 | 0.211 | topic_hint:computing_internet | 1.000 | 995 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `許可` | きょか | 0.239 | 0.239 | topic_hint:computing_internet | 1.000 | 998 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `ネット` | ねっと | 0.177 | 0.177 | topic_hint:computing_internet | 0.999 | 873 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `プログラム` | ぷろぐらむ | 0.182 | 0.182 | topic_hint:computing_internet | 1.000 | 1117 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `削除` | さくじょ | 0.281 | 0.281 | topic_hint:computing_internet | 1.000 | 1124 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `medicine_health_p45`

Medicine/health preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `顔` | かお | 0.169 | 0.169 | topic_hint:medicine_health | 0.993 | 56 -> 1 | Boosted by proficiency_fit, topic_affinity, while remaining supported by coverage_gain. |
| 2 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 1.000 | 513 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 1.000 | 737 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 744 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 1.000 | 1498 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 1.000 | 1686 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 1.000 | 1835 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `怪我` | けが | 0.244 | 0.244 | topic_hint:medicine_health | 1.000 | 2070 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `胃` | い | 0.257 | 0.257 | topic_hint:medicine_health | 1.000 | 2357 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `爪` | つめ | 0.299 | 0.299 | topic_hint:medicine_health | 1.000 | 2636 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `血` | ち | 0.150 | 0.150 | topic_hint:medicine_health | 0.949 | 829 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `指` | ゆび | 0.149 | 0.149 | topic_hint:medicine_health | 0.943 | 763 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `背中` | せなか | 0.147 | 0.147 | topic_hint:medicine_health | 0.938 | 1419 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `熱` | ねつ | 0.146 | 0.146 | topic_hint:medicine_health | 0.932 | 1136 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `風邪` | かぜ | 0.100 | 0.100 | topic_hint:medicine_health | 0.682 | 2191 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p25`

Sports preference at low proficiency; topic items should still respect readiness.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `野球` | やきゅう | 0.241 | 0.241 | topic_hint:sports_fitness | 1.000 | 1243 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `ゴルフ` | ごるふ | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 1881 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `サッカー` | さっかー | 0.189 | 0.189 | topic_hint:sports_fitness | 1.000 | 1945 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 2457 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `スキー` | すきー | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 2514 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `テニス` | てにす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 3422 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `水泳` | すいえい | 0.155 | 0.155 | topic_hint:sports_fitness | 1.000 | 5836 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `柔道` | じゅうどう | 0.137 | 0.137 | topic_hint:sports_fitness | 1.000 | 5912 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `スケート` | すけーと | 0.260 | 0.260 | topic_hint:sports_fitness | 1.000 | 7266 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 1.000 | 158 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `マラソン` | まらそん | 0.306 | 0.306 | topic_hint:sports_fitness | 1.000 | 5377 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `体操` | たいそう | 0.339 | 0.339 | topic_hint:sports_fitness | 1.000 | 3208 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `相撲` | すもう | 0.350 | 0.350 | topic_hint:sports_fitness | 1.000 | 4243 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `陸上` | りくじょう | 0.352 | 0.352 | topic_hint:sports_fitness | 1.000 | 3777 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 16 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 17 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 17 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `games_p45`

Games preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `カード` | かーど | 0.172 | 0.172 | topic_hint:games | 0.996 | 615 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 1.000 | 2034 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 0.997 | 1551 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `ランキング` | らんきんぐ | 0.184 | 0.184 | topic_hint:games | 1.000 | 2708 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 0.993 | 743 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:games | 1.000 | 3559 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `得点` | とくてん | 0.343 | 0.343 | topic_hint:games | 1.000 | 3697 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `逆転` | ぎゃくてん | 0.344 | 0.344 | topic_hint:games | 1.000 | 4093 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `防御` | ぼうぎょ | 0.319 | 0.319 | topic_hint:games | 1.000 | 4355 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `局面` | きょくめん | 0.369 | 0.369 | topic_hint:games | 1.000 | 4716 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `読み` | よみ | 0.264 | 0.264 | topic_hint:games | 1.000 | 4770 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `ターン` | たーん | 0.297 | 0.297 | topic_hint:games | 1.000 | 4772 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `ボス` | ぼす | 0.297 | 0.297 | topic_hint:games | 1.000 | 4784 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `対戦` | たいせん | 0.328 | 0.328 | topic_hint:games | 1.000 | 5065 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `点数` | てんすう | 0.362 | 0.362 | topic_hint:games | 1.000 | 5122 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `anime_manga_p45`

Anime/manga/pop-culture preference at intermediate proficiency; documents current overlay coverage.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 0.999 | 282 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 0.996 | 615 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `スペース` | すぺーす | 0.203 | 0.203 | topic_hint:anime_manga_pop_culture | 1.000 | 1983 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `感想` | かんそう | 0.286 | 0.286 | topic_hint:anime_manga_pop_culture | 1.000 | 2290 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:anime_manga_pop_culture | 1.000 | 2848 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `イベント` | いべんと | 0.171 | 0.171 | topic_hint:anime_manga_pop_culture | 0.996 | 1291 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `ブーム` | ぶーむ | 0.188 | 0.188 | topic_hint:anime_manga_pop_culture | 1.000 | 3114 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `考察` | こうさつ | 0.329 | 0.329 | topic_hint:anime_manga_pop_culture | 1.000 | 3253 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `動画` | どうが | 0.200 | 0.200 | topic_hint:anime_manga_pop_culture | 1.000 | 3380 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 3559 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `ロボット` | ろぼっと | 0.193 | 0.193 | topic_hint:anime_manga_pop_culture | 1.000 | 3642 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `学園` | がくえん | 0.339 | 0.339 | topic_hint:anime_manga_pop_culture | 1.000 | 3683 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `再開` | さいかい | 0.328 | 0.328 | topic_hint:anime_manga_pop_culture | 1.000 | 3732 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `hobbies_crafts_p45`

Hobbies/crafts preference at intermediate proficiency; documents current overlay coverage.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 0.994 | 474 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 1.000 | 1899 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `ドライブ` | どらいぶ | 0.203 | 0.203 | topic_hint:hobbies_crafts | 1.000 | 1997 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `キャンプ` | きゃんぷ | 0.244 | 0.244 | topic_hint:hobbies_crafts | 1.000 | 2767 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `釣り` | つり | 0.257 | 0.257 | topic_hint:hobbies_crafts | 1.000 | 2873 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `工作` | こうさく | 0.338 | 0.338 | topic_hint:hobbies_crafts | 1.000 | 2882 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `録音` | ろくおん | 0.333 | 0.333 | topic_hint:hobbies_crafts | 1.000 | 3211 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:hobbies_crafts | 1.000 | 3280 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `絵画` | かいが | 0.254 | 0.254 | topic_hint:hobbies_crafts | 1.000 | 3323 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `手作り` | てづくり | 0.341 | 0.341 | topic_hint:hobbies_crafts | 1.000 | 3364 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `彫刻` | ちょうこく | 0.360 | 0.360 | topic_hint:hobbies_crafts | 1.000 | 3849 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `演劇` | えんげき | 0.371 | 0.371 | topic_hint:hobbies_crafts | 1.000 | 4629 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `天文` | てんもん | 0.383 | 0.383 | topic_hint:hobbies_crafts | 1.000 | 4738 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `縫う` | ぬう | 0.334 | 0.334 | topic_hint:hobbies_crafts | 1.000 | 7305 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `水槽` | すいそう | 0.345 | 0.345 | topic_hint:hobbies_crafts | 1.000 | 4931 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `マジック` | まじっく | 0.306 | 0.306 | topic_hint:hobbies_crafts | 1.000 | 5373 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `模型` | もけい | 0.382 | 0.382 | topic_hint:hobbies_crafts | 1.000 | 5677 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `mixed_work_computing_p50`

Weighted mixed professional and computing interests.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet', 'work_office']` applied_seed_count=`131`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム
- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `サイト` | さいと | 0.395 | 0.395 | topic_hint:computing_internet | 1.000 | 688 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `インターネット` | いんたーねっと | 0.456 | 0.456 | topic_hint:computing_internet | 1.000 | 851 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `許可` | きょか | 0.239 | 0.239 | topic_hint:computing_internet | 1.000 | 998 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `削除` | さくじょ | 0.281 | 0.281 | topic_hint:computing_internet | 1.000 | 1124 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `形式` | けいしき | 0.284 | 0.284 | topic_hint:computing_internet | 1.000 | 1167 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `広告` | こうこく | 0.240 | 0.240 | topic_hint:computing_internet | 1.000 | 1197 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `書類` | しょるい | 0.250 | 0.250 | topic_hint:work_office | 1.000 | 1245 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `更新` | こうしん | 0.229 | 0.229 | topic_hint:computing_internet | 1.000 | 1351 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 1.000 | 1426 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `印刷` | いんさつ | 0.249 | 0.249 | topic_hint:computing_internet | 1.000 | 1509 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `通知` | つうち | 0.285 | 0.285 | topic_hint:computing_internet | 1.000 | 1513 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:computing_internet | 1.000 | 1538 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `接続` | せつぞく | 0.224 | 0.224 | topic_hint:computing_internet | 0.998 | 1238 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `数値` | すうち | 0.286 | 0.286 | topic_hint:computing_internet | 1.000 | 1856 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 0.995 | 598 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `ソース` | そーす | 0.487 | 0.487 | topic_hint:computing_internet | 1.000 | 1961 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `権限` | けんげん | 0.321 | 0.321 | topic_hint:computing_internet | 1.000 | 1975 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `mixed_food_travel_p35`

Weighted food/travel interests at lower-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking', 'travel_places_transport']` applied_seed_count=`88`

Active topic support:

- `food_cooking` candidates=46 mass=14.625705 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味
- `travel_places_transport` candidates=43 mass=16.315422 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `道路` | どうろ | 0.200 | 0.200 | topic_hint:travel_places_transport | 1.000 | 375 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `バス` | ばす | 0.118 | 0.118 | topic_hint:travel_places_transport | 1.000 | 622 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `観光` | かんこう | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 678 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `会場` | かいじょう | 0.146 | 0.146 | topic_hint:travel_places_transport | 1.000 | 739 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `船` | ふね | 0.136 | 0.136 | topic_hint:travel_places_transport | 1.000 | 826 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 1.000 | 3361 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `肉` | にく | 0.083 | 0.083 | topic_hint:food_cooking | 1.000 | 1016 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `空港` | くうこう | 0.140 | 0.140 | topic_hint:travel_places_transport | 1.000 | 1178 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `コーヒー` | こーひー | 0.117 | 0.117 | topic_hint:food_cooking | 1.000 | 1209 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:travel_places_transport | 1.000 | 1298 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `電車` | でんしゃ | 0.078 | 0.078 | topic_hint:travel_places_transport | 1.000 | 1244 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:travel_places_transport | 1.000 | 1347 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `冷たい` | つめたい | 0.088 | 0.088 | topic_hint:food_cooking | 1.000 | 2413 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `橋` | はし | 0.089 | 0.089 | topic_hint:travel_places_transport | 1.000 | 1397 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `教会` | きょうかい | 0.154 | 0.154 | topic_hint:travel_places_transport | 1.000 | 1527 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `mixed_science_medicine_p50`

Weighted science/medicine interests at upper-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['science_math', 'medicine_health']` applied_seed_count=`42`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院
- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 1.000 | 1077 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 1.000 | 1498 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 1.000 | 1583 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 1.000 | 1686 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 1.000 | 1835 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `怪我` | けが | 0.244 | 0.244 | topic_hint:medicine_health | 1.000 | 2070 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 1.000 | 2269 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `胃` | い | 0.257 | 0.257 | topic_hint:medicine_health | 1.000 | 2357 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `爪` | つめ | 0.299 | 0.299 | topic_hint:medicine_health | 1.000 | 2636 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 1.000 | 2932 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 0.991 | 802 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 0.989 | 758 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 0.987 | 1058 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 0.983 | 744 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 0.983 | 821 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 0.981 | 737 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 0.959 | 513 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `mixed_anime_games_hobbies_p45`

Weighted entertainment, games, and hobbies interests at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture', 'games', 'hobbies_crafts']` applied_seed_count=`133`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.410732 scarcity=eligible examples=作品, 設定, ファン, 日常, 予約
- `games` candidates=34 mass=8.258756 scarcity=eligible examples=レベル, 試合, ゲーム, 大会, 戦略
- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 0.999 | 282 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 0.996 | 615 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 0.994 | 474 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 1.000 | 1899 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `スペース` | すぺーす | 0.203 | 0.203 | topic_hint:anime_manga_pop_culture | 1.000 | 1983 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `ドライブ` | どらいぶ | 0.203 | 0.203 | topic_hint:hobbies_crafts | 1.000 | 1997 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `arts_literature_p72`

Arts/literature/humanities preference at advanced proficiency; documents current overlay coverage.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`41`

Active topic support:

- `arts_literature_humanities` candidates=41 mass=13.642955 scarcity=eligible examples=文化, 本, 本, 作品, 歴史

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `短歌` | たんか | 0.428 | 0.428 | topic_hint:arts_literature_humanities | 0.971 | 6498 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `脚本` | きゃくほん | 0.388 | 0.388 | topic_hint:arts_literature_humanities | 0.796 | 5049 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `歌舞伎` | かぶき | 0.387 | 0.387 | topic_hint:arts_literature_humanities | 0.786 | 5132 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `評論` | ひょうろん | 0.384 | 0.384 | topic_hint:arts_literature_humanities | 0.771 | 3998 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `寺院` | じいん | 0.373 | 0.373 | topic_hint:arts_literature_humanities | 0.702 | 4025 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `演劇` | えんげき | 0.371 | 0.371 | topic_hint:arts_literature_humanities | 0.685 | 4629 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 8 | Boosted by proficiency_fit. |
| 9 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 9 | Boosted by proficiency_fit. |
| 10 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 10 | Boosted by proficiency_fit. |
| 11 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 11 | Boosted by proficiency_fit. |
| 12 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 12 | Boosted by proficiency_fit. |
| 13 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 13 | Boosted by proficiency_fit. |
| 14 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 14 | Boosted by proficiency_fit. |
| 15 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 15 | Boosted by proficiency_fit. |
| 16 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 16 | Boosted by proficiency_fit. |
| 17 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 17 | Boosted by proficiency_fit. |
| 18 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 18 | Boosted by proficiency_fit. |
| 19 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 19 | Boosted by proficiency_fit. |
| 20 | `オブ` | おぶ | 0.579 | 0.579 |  | 1.000 | 1683 -> 20 | Boosted by proficiency_fit. |

### `food_cooking_p20`

Food/cooking preference at upper beginner proficiency; documents current overlay coverage.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `食べる` | たべる | 0.027 | 0.027 | topic_hint:food_cooking | 1.000 | 1005 -> 1 | Boosted by proficiency_fit, topic_affinity, while remaining supported by coverage_gain. |
| 2 | `飲む` | のむ | 0.053 | 0.053 | topic_hint:food_cooking | 1.000 | 1456 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:food_cooking | 1.000 | 346 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `野菜` | やさい | 0.067 | 0.067 | topic_hint:food_cooking | 1.000 | 786 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 1.000 | 3361 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `肉` | にく | 0.083 | 0.083 | topic_hint:food_cooking | 1.000 | 1016 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `甘い` | あまい | 0.072 | 0.072 | topic_hint:food_cooking | 1.000 | 2133 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `コーヒー` | こーひー | 0.117 | 0.117 | topic_hint:food_cooking | 1.000 | 1209 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `冷たい` | つめたい | 0.088 | 0.088 | topic_hint:food_cooking | 1.000 | 2413 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `ワイン` | わいん | 0.173 | 0.173 | topic_hint:food_cooking | 1.000 | 1534 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `熱い` | あつい | 0.087 | 0.087 | topic_hint:food_cooking | 1.000 | 2615 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `味噌` | みそ | 0.152 | 0.152 | topic_hint:food_cooking | 1.000 | 1560 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `醤油` | しょうゆ | 0.095 | 0.095 | topic_hint:food_cooking | 1.000 | 1780 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `カレー` | かれー | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 1880 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `砂糖` | さとう | 0.100 | 0.100 | topic_hint:food_cooking | 1.000 | 1888 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `レストラン` | れすとらん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 1911 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `music_media_p35`

Music/media/entertainment preference at lower-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `テレビ` | てれび | 0.117 | 0.117 | topic_hint:music_media_entertainment | 1.000 | 258 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `放送` | ほうそう | 0.130 | 0.130 | topic_hint:music_media_entertainment | 1.000 | 426 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `監督` | かんとく | 0.207 | 0.207 | topic_hint:music_media_entertainment | 1.000 | 481 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `番組` | ばんぐみ | 0.136 | 0.136 | topic_hint:music_media_entertainment | 1.000 | 834 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `雑誌` | ざっし | 0.078 | 0.078 | topic_hint:music_media_entertainment | 1.000 | 984 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `広告` | こうこく | 0.240 | 0.240 | topic_hint:music_media_entertainment | 1.000 | 1197 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `演奏` | えんそう | 0.245 | 0.245 | topic_hint:music_media_entertainment | 1.000 | 1460 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:music_media_entertainment | 1.000 | 1711 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `ラジオ` | らじお | 0.080 | 0.080 | topic_hint:music_media_entertainment | 1.000 | 1785 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:music_media_entertainment | 1.000 | 2120 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:music_media_entertainment | 1.000 | 2848 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `音声` | おんせい | 0.300 | 0.300 | topic_hint:music_media_entertainment | 1.000 | 3181 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:music_media_entertainment | 1.000 | 3280 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `動画` | どうが | 0.200 | 0.200 | topic_hint:music_media_entertainment | 1.000 | 3380 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `ギター` | ぎたー | 0.102 | 0.102 | topic_hint:music_media_entertainment | 1.000 | 3547 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `歌手` | かしゅ | 0.121 | 0.121 | topic_hint:music_media_entertainment | 1.000 | 3589 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `太鼓` | たいこ | 0.352 | 0.352 | topic_hint:music_media_entertainment | 1.000 | 3884 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `ドラム` | どらむ | 0.314 | 0.314 | topic_hint:music_media_entertainment | 1.000 | 5915 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `ニュース` | にゅーす | 0.066 | 0.066 | topic_hint:music_media_entertainment | 0.988 | 1166 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `歌` | うた | 0.063 | 0.063 | topic_hint:music_media_entertainment | 0.983 | 546 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `law_politics_p60`

Law/politics/civics preference at N1-ish proficiency.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`46`

Active topic support:

- `law_politics_civics` candidates=46 mass=17.064101 scarcity=eligible examples=社会, 政府, 制度, 事件, 国民

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `司法` | しほう | 0.329 | 0.329 | topic_hint:law_politics_civics | 1.000 | 2377 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `条例` | じょうれい | 0.330 | 0.330 | topic_hint:law_politics_civics | 1.000 | 2503 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `被告` | ひこく | 0.357 | 0.357 | topic_hint:law_politics_civics | 1.000 | 2631 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `検察` | けんさつ | 0.344 | 0.344 | topic_hint:law_politics_civics | 1.000 | 2851 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `政党` | せいとう | 0.334 | 0.334 | topic_hint:law_politics_civics | 1.000 | 2964 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `国籍` | こくせき | 0.358 | 0.358 | topic_hint:law_politics_civics | 1.000 | 3162 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `税制` | ぜいせい | 0.375 | 0.375 | topic_hint:law_politics_civics | 1.000 | 3353 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `立法` | りっぽう | 0.378 | 0.378 | topic_hint:law_politics_civics | 1.000 | 3615 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `罰金` | ばっきん | 0.391 | 0.391 | topic_hint:law_politics_civics | 1.000 | 4498 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `兵士` | へいし | 0.314 | 0.314 | topic_hint:law_politics_civics | 0.986 | 2494 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `判決` | はんけつ | 0.307 | 0.307 | topic_hint:law_politics_civics | 0.968 | 1608 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `捜査` | そうさ | 0.302 | 0.302 | topic_hint:law_politics_civics | 0.954 | 1204 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `条約` | じょうやく | 0.292 | 0.292 | topic_hint:law_politics_civics | 0.918 | 1102 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `内閣` | ないかく | 0.287 | 0.287 | topic_hint:law_politics_civics | 0.894 | 1054 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:law_politics_civics | 0.885 | 1736 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `証拠` | しょうこ | 0.279 | 0.279 | topic_hint:law_politics_civics | 0.857 | 1237 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `軍隊` | ぐんたい | 0.265 | 0.265 | topic_hint:law_politics_civics | 0.776 | 2825 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `税金` | ぜいきん | 0.254 | 0.254 | topic_hint:law_politics_civics | 0.706 | 2153 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `犯人` | はんにん | 0.250 | 0.250 | topic_hint:law_politics_civics | 0.681 | 1277 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `憲法` | けんぽう | 0.249 | 0.249 | topic_hint:law_politics_civics | 0.677 | 1029 -> 20 | Boosted by proficiency_fit, topic_affinity. |

### `animals_p30`

Animals preference at lower-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `犬` | いぬ | 0.072 | 0.072 | topic_hint:animals | 1.000 | 614 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `猫` | ねこ | 0.068 | 0.068 | topic_hint:animals | 1.000 | 770 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `馬` | うま | 0.211 | 0.211 | topic_hint:animals | 1.000 | 887 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `鳥` | とり | 0.068 | 0.068 | topic_hint:animals | 1.000 | 1354 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `虫` | むし | 0.149 | 0.149 | topic_hint:animals | 1.000 | 1782 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `牛` | うし | 0.248 | 0.248 | topic_hint:animals | 1.000 | 2140 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `虎` | とら | 0.262 | 0.262 | topic_hint:animals | 1.000 | 3425 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `象` | ぞう | 0.265 | 0.265 | topic_hint:animals | 1.000 | 4066 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `熊` | くま | 0.314 | 0.314 | topic_hint:animals | 1.000 | 3109 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `蚊` | か | 0.317 | 0.317 | topic_hint:animals | 1.000 | 4724 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `亀` | かめ | 0.348 | 0.348 | topic_hint:animals | 1.000 | 3929 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `蝶` | ちょう | 0.358 | 0.358 | topic_hint:animals | 1.000 | 3987 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `鹿` | しか | 0.362 | 0.362 | topic_hint:animals | 1.000 | 5591 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `蜂` | はち | 0.367 | 0.367 | topic_hint:animals | 1.000 | 5100 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `狐` | きつね | 0.380 | 0.380 | topic_hint:animals | 1.000 | 4460 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `烏賊` | いか | 0.382 | 0.382 | topic_hint:animals | 1.000 | 4248 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `蛸` | たこ | 0.385 | 0.385 | topic_hint:animals | 1.000 | 4757 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `烏` | からす | 0.388 | 0.388 | topic_hint:animals | 1.000 | 4001 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 19 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 20 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `plants_nature_p40`

Plants/nature preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `地震` | じしん | 0.140 | 0.140 | topic_hint:plants_nature | 1.000 | 909 -> 1 | Boosted by proficiency_fit, topic_affinity. |
| 2 | `森` | もり | 0.145 | 0.145 | topic_hint:plants_nature | 1.000 | 1002 -> 2 | Boosted by proficiency_fit, topic_affinity. |
| 3 | `季節` | きせつ | 0.144 | 0.144 | topic_hint:plants_nature | 1.000 | 1334 -> 3 | Boosted by proficiency_fit, topic_affinity. |
| 4 | `雲` | くも | 0.153 | 0.153 | topic_hint:plants_nature | 1.000 | 1530 -> 4 | Boosted by proficiency_fit, topic_affinity. |
| 5 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:plants_nature | 1.000 | 2445 -> 5 | Boosted by proficiency_fit, topic_affinity. |
| 6 | `気温` | きおん | 0.256 | 0.256 | topic_hint:plants_nature | 1.000 | 2466 -> 6 | Boosted by proficiency_fit, topic_affinity. |
| 7 | `台風` | たいふう | 0.149 | 0.149 | topic_hint:plants_nature | 1.000 | 2893 -> 7 | Boosted by proficiency_fit, topic_affinity. |
| 8 | `豆` | まめ | 0.250 | 0.250 | topic_hint:plants_nature | 1.000 | 2994 -> 8 | Boosted by proficiency_fit, topic_affinity. |
| 9 | `葡萄` | ぶどう | 0.327 | 0.327 | topic_hint:plants_nature | 1.000 | 3069 -> 9 | Boosted by proficiency_fit, topic_affinity. |
| 10 | `火山` | かざん | 0.336 | 0.336 | topic_hint:plants_nature | 1.000 | 3311 -> 10 | Boosted by proficiency_fit, topic_affinity. |
| 11 | `杉` | すぎ | 0.356 | 0.356 | topic_hint:plants_nature | 1.000 | 3920 -> 11 | Boosted by proficiency_fit, topic_affinity. |
| 12 | `苺` | いちご | 0.383 | 0.383 | topic_hint:plants_nature | 1.000 | 4344 -> 12 | Boosted by proficiency_fit, topic_affinity. |
| 13 | `洪水` | こうずい | 0.365 | 0.365 | topic_hint:plants_nature | 1.000 | 4401 -> 13 | Boosted by proficiency_fit, topic_affinity. |
| 14 | `蜜柑` | みかん | 0.351 | 0.351 | topic_hint:plants_nature | 1.000 | 4589 -> 14 | Boosted by proficiency_fit, topic_affinity. |
| 15 | `麦` | むぎ | 0.375 | 0.375 | topic_hint:plants_nature | 1.000 | 5265 -> 15 | Boosted by proficiency_fit, topic_affinity. |
| 16 | `津波` | つなみ | 0.373 | 0.373 | topic_hint:plants_nature | 1.000 | 6561 -> 16 | Boosted by proficiency_fit, topic_affinity. |
| 17 | `天気` | てんき | 0.099 | 0.099 | topic_hint:plants_nature | 0.942 | 1575 -> 17 | Boosted by proficiency_fit, topic_affinity. |
| 18 | `檜` | ひのき | 0.584 | 0.584 | topic_hint:plants_nature | 1.000 | 6841 -> 18 | Boosted by proficiency_fit, topic_affinity. |
| 19 | `雨` | あめ | 0.068 | 0.068 | topic_hint:plants_nature | 0.795 | 637 -> 19 | Boosted by proficiency_fit, topic_affinity. |
| 20 | `花` | はな | 0.060 | 0.060 | topic_hint:plants_nature | 0.746 | 225 -> 20 | Boosted by proficiency_fit, topic_affinity. |
