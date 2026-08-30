# en-ja SRS Admission Preference Sample Pack

- status: `PASS`
- findings: pass=20 warn=0 fail=0
- scenarios: `18`
- topic scenarios with movers: `14` / `14`
- runtime scope: `admission_preview_only`

## Method

- strategy: `profile_bootstrap`
- profile shape: single proficiency estimate plus optional topic_weights/interests
- runtime difficulty source: profile_bootstrap uses the corrected en-ja learner-difficulty CSV through an explicit runtime hook when the CSV is available; otherwise it falls back to runtime commonness signals.
- state mutation: none; previews run under a temporary helper data root

## Inputs

- config_json: `docs/test_inputs/srs_admission_preference_sample_configs_en_ja.json`
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
- row_count: `3955`
- runtime_supported_row_count: `778`
- runtime_min_membership: `1.0`

| Topic | Rows | Runtime-Supported Rows |
| --- | ---: | ---: |
| `animals` | 96 | 27 |
| `anime_manga_pop_culture` | 116 | 100 |
| `arts_literature_humanities` | 171 | 20 |
| `computing_internet` | 273 | 129 |
| `food_cooking` | 183 | 55 |
| `games` | 236 | 111 |
| `hobbies_crafts` | 100 | 100 |
| `law_politics_civics` | 330 | 20 |
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
| `law_politics_civics` | `source_ready_candidate` | 330 | 20 |
| `science_technology` | `compatibility_parent_candidate` | 0 | 0 |
| `science_math` | `source_ready_candidate` | 806 | 18 |
| `computing_internet` | `source_ready_candidate` | 273 | 129 |
| `travel_places_transport` | `partial_source_candidate` | 249 | 38 |
| `arts_literature_humanities` | `partial_source_candidate` | 171 | 20 |
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
| `neutral_beginner` | 0.100 | - | 0 | - | 0 | する, いる, ある, 言う, こと, なる, その, よう |
| `neutral_lower_intermediate` | 0.300 | - | 0 | - | 0 | ある, 無い, こと, よう, 出来る, 因る, 時, 思う |
| `neutral_n1ish` | 0.580 | - | 0 | - | 0 | 御座る, 項, 感, 我々, なお, 論, 通ずる, 府 |
| `neutral_advanced` | 0.820 | - | 0 | - | 0 | クリア, ゲット, 項, ウィン, マザー, オリーブ, ジャバ, 論 |
| `shopping_money_intermediate` | 0.450 | shopping_money | 18 | applied | 0 | 商品, 価格, 無料, 会計, 債権, 料金, 支払う, スーパー |
| `work_office_intermediate` | 0.450 | work_office | 26 | applied | 0 | 事務, 報告, 資料, 契約, 職員, 社員, 職業, 勤務 |
| `science_math_intermediate` | 0.450 | science_math | 14 | applied | 0 | 計算, 機械, 実験, 研究, 理論, 数字, 化学, 温度 |
| `computing_internet_intermediate` | 0.450 | computing_internet | 40 | applied | 0 | 情報, 開発, 処理, 条件, 設定, システム, メール, データ |
| `medicine_health_intermediate` | 0.450 | medicine_health | 16 | applied | 0 | 顔, 胸, 腰, 肩, 脳, 腹, 指, 血 |
| `sports_beginner` | 0.250 | sports_fitness | 11 | applied | 0 | センター, 野球, ゴルフ, サッカー, ダンス, スキー, テニス, 体操 |
| `games_intermediate` | 0.450 | games | 33 | applied | 0 | レベル, カード, 大会, ゲーム, 戦略, ルール, 作戦, 勝負 |
| `hobbies_crafts_intermediate` | 0.450 | hobbies_crafts | 37 | applied | 0 | 撮影, ブログ, 編集, 収集, 栽培, ドライブ, ピアノ, 日記 |
| `arts_literature_advanced` | 0.720 | arts_literature_humanities | 1 | applied | 0 | 短歌, 項, 論, 府, 感, 因み, 層, 増 |
| `mixed_work_computing` | 0.500 | computing_internet, work_office | 40 | applied | 0 | 通信, 職員, 資料, サイト, 携帯, 契約, インターネット, 機械 |
| `mixed_food_travel` | 0.350 | food_cooking, travel_places_transport | 40 | applied | 0 | 日本, 飲む, 道路, 銀行, 駅, 酒, バス, 味 |
| `mixed_science_medicine` | 0.550 | science_math, medicine_health | 22 | applied | 0 | 理論, 皮膚, 化学, 公式, 爪, 心臓, 三角, 胃 |
| `food_cooking_beginner` | 0.200 | food_cooking | 36 | applied | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, 茶, パン |
| `anime_manga_intermediate` | 0.450 | anime_manga_pop_culture | 40 | applied | 0 | 作品, 設定, カード, ファン, 日常, 発売, イベント, コメント |

## Findings

- `PASS` `TOPIC_OVERLAY_AVAILABLE`: Product-shaped en-ja topic overlay was available for preview.
- `PASS` `CORRECTED_RANKING_DIAGNOSTIC_AVAILABLE`: Corrected learner-difficulty ranking was joined for diagnostics.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_beginner`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_lower_intermediate`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_n1ish`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_advanced`: Neutral profile generated an admission preview.
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_beginner`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_intermediate`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_advanced`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_work_computing`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_food_travel`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_science_medicine`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_beginner`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_intermediate`: Topic preference produced runtime topic movers.

## Scenario Details

### `neutral_beginner`

No topic preference, early beginner proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 5 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 6 | `なる` | なる | 0.002 | 0.002 |  | 1.000 | 47 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
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

### `neutral_lower_intermediate`

No topic preference, lower-intermediate proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` | ある | 0.120 | 0.120 |  | 0.947 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `こと` | こと | 0.120 | 0.120 |  | 0.947 | 1 -> 3 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 4 | `よう` | よう | 0.123 | 0.123 |  | 0.958 | 13 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
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

### `neutral_n1ish`

No topic preference, roughly upper-intermediate / N1-ish proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `なお` | なお | 0.415 | 0.415 |  | 0.987 | 6545 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `当該` | とうがい | 0.398 | 0.398 |  | 0.940 | 365 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `レベル` | れべる | 0.413 | 0.413 |  | 0.982 | 597 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ワン` | わん | 0.421 | 0.421 |  | 0.995 | 736 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `インターネット` | いんたーねっと | 0.456 | 0.456 |  | 1.000 | 851 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ライン` | らいん | 0.463 | 0.463 |  | 1.000 | 919 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ファン` | ふぁん | 0.411 | 0.411 |  | 0.979 | 831 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `バランス` | ばらんす | 0.429 | 0.429 |  | 1.000 | 1055 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_advanced`

No topic preference, advanced-tail proficiency.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.928 | 4319 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `項` | こう | 0.572 | 0.572 |  | 0.559 | 129 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.969 | 5234 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `マザー` | まざー | 0.645 | 0.645 |  | 0.962 | 5602 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.920 | 4995 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 1.000 | 6401 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `論` | ろん | 0.576 | 0.576 |  | 0.589 | 424 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.914 | 5236 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `メソッド` | めそっど | 0.676 | 0.676 |  | 1.000 | 6546 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `府` | ふ | 0.574 | 0.574 |  | 0.574 | 455 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `スリー` | すりー | 0.622 | 0.622 |  | 0.871 | 5033 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `カテ` | かて | 0.621 | 0.621 |  | 0.864 | 5251 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `層` | そう | 0.576 | 0.576 |  | 0.588 | 761 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `増` | ぞう | 0.577 | 0.577 |  | 0.597 | 908 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `shopping_money_intermediate`

Shopping/money preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `商品` | しょうひん | 0.179 | 0.179 | topic_hint:shopping_money | 1.000 | 239 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `価格` | かかく | 0.183 | 0.183 | topic_hint:shopping_money | 1.000 | 268 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `無料` | むりょう | 0.204 | 0.204 | topic_hint:shopping_money | 1.000 | 608 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `会計` | かいけい | 0.243 | 0.243 | topic_hint:shopping_money | 1.000 | 867 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 1.000 | 941 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `料金` | りょうきん | 0.239 | 0.239 | topic_hint:shopping_money | 1.000 | 945 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `支払う` | しはらう | 0.242 | 0.242 | topic_hint:shopping_money | 1.000 | 3905 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:shopping_money | 0.990 | 1347 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `円` | えん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 1897 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `商店` | しょうてん | 0.309 | 0.309 | topic_hint:shopping_money | 1.000 | 2056 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `予約` | よやく | 0.144 | 0.144 | topic_hint:shopping_money | 0.926 | 1024 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `払う` | はらう | 0.137 | 0.137 | topic_hint:shopping_money | 0.893 | 2821 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `現金` | げんきん | 0.252 | 0.252 | topic_hint:shopping_money | 1.000 | 2459 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `値段` | ねだん | 0.142 | 0.142 | topic_hint:shopping_money | 0.917 | 1446 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `代金` | だいきん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 3140 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `コンビニ` | こんびに | 0.280 | 0.280 | topic_hint:shopping_money | 1.000 | 3569 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `レジ` | れじ | 0.167 | 0.167 | topic_hint:shopping_money | 0.989 | 5177 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `店員` | てんいん | 0.124 | 0.124 | topic_hint:shopping_money | 0.831 | 3508 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_intermediate`

Work/office preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 1.000 | 242 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 1.000 | 265 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 1.000 | 301 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 1.000 | 321 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 1.000 | 598 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `書類` | しょるい | 0.250 | 0.250 | topic_hint:work_office | 1.000 | 1245 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 1.000 | 1426 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `連絡` | れんらく | 0.135 | 0.135 | topic_hint:work_office | 0.884 | 373 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `予定` | よてい | 0.130 | 0.130 | topic_hint:work_office | 0.862 | 322 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `上司` | じょうし | 0.306 | 0.306 | topic_hint:work_office | 1.000 | 2049 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `会議` | かいぎ | 0.129 | 0.129 | topic_hint:work_office | 0.856 | 387 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `役員` | やくいん | 0.329 | 0.329 | topic_hint:work_office | 1.000 | 2114 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `部下` | ぶか | 0.317 | 0.317 | topic_hint:work_office | 1.000 | 2312 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `給料` | きゅうりょう | 0.256 | 0.256 | topic_hint:work_office | 1.000 | 2424 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `面接` | めんせつ | 0.318 | 0.318 | topic_hint:work_office | 1.000 | 2542 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `出張` | しゅっちょう | 0.335 | 0.335 | topic_hint:work_office | 1.000 | 2677 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `同僚` | どうりょう | 0.249 | 0.249 | topic_hint:work_office | 1.000 | 2838 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `science_math_intermediate`

Science/math preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `計算` | けいさん | 0.198 | 0.198 | topic_hint:science_math | 1.000 | 460 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 1.000 | 758 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 1.000 | 802 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `研究` | けんきゅう | 0.125 | 0.125 | topic_hint:science_math | 0.836 | 54 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 1.000 | 1058 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 1.000 | 1077 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 1.000 | 1583 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `科学` | かがく | 0.129 | 0.129 | topic_hint:science_math | 0.855 | 374 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 1.000 | 2269 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 1.000 | 2932 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `数学` | すうがく | 0.155 | 0.155 | topic_hint:science_math | 0.964 | 2301 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `地理` | ちり | 0.157 | 0.157 | topic_hint:science_math | 0.970 | 3532 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `computing_internet_intermediate`

Computing/internet preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `情報` | じょうほう | 0.169 | 0.169 | topic_hint:computing_internet | 0.993 | 57 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `開発` | かいはつ | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 122 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 1.000 | 269 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 1.000 | 275 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `設定` | せってい | 0.177 | 0.177 | topic_hint:computing_internet | 0.999 | 282 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `システム` | しすてむ | 0.166 | 0.166 | topic_hint:computing_internet | 0.989 | 237 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `メール` | めーる | 0.168 | 0.168 | topic_hint:computing_internet | 0.992 | 260 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `データ` | でーた | 0.167 | 0.167 | topic_hint:computing_internet | 0.990 | 331 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 386 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `登録` | とうろく | 0.178 | 0.178 | topic_hint:computing_internet | 1.000 | 454 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:computing_internet | 0.994 | 474 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `携帯` | けいたい | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 628 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ファイル` | ふぁいる | 0.173 | 0.173 | topic_hint:computing_internet | 0.997 | 654 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `サイト` | さいと | 0.395 | 0.395 | topic_hint:computing_internet | 1.000 | 688 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `パソコン` | ぱそこん | 0.165 | 0.165 | topic_hint:computing_internet | 0.986 | 577 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 1.000 | 710 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `画像` | がぞう | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 732 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ソフト` | そふと | 0.165 | 0.165 | topic_hint:computing_internet | 0.987 | 643 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `機械` | きかい | 0.216 | 0.216 | topic_hint:computing_internet | 1.000 | 758 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `実行` | じっこう | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 806 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_intermediate`

Medicine/health preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `顔` | かお | 0.169 | 0.169 | topic_hint:medicine_health | 0.993 | 56 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 1.000 | 513 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 1.000 | 737 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 744 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `指` | ゆび | 0.149 | 0.149 | topic_hint:medicine_health | 0.943 | 763 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `血` | ち | 0.150 | 0.150 | topic_hint:medicine_health | 0.949 | 829 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 1.000 | 1498 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 1.000 | 1686 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 1.000 | 1835 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `怪我` | けが | 0.244 | 0.244 | topic_hint:medicine_health | 1.000 | 2070 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `熱` | ねつ | 0.146 | 0.146 | topic_hint:medicine_health | 0.932 | 1136 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `胃` | い | 0.257 | 0.257 | topic_hint:medicine_health | 1.000 | 2357 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `背中` | せなか | 0.147 | 0.147 | topic_hint:medicine_health | 0.938 | 1419 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `爪` | つめ | 0.299 | 0.299 | topic_hint:medicine_health | 1.000 | 2636 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `風邪` | かぜ | 0.100 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `鼻` | はな | 0.093 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_beginner`

Sports preference at low proficiency; should only admit ready topic items.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 1.000 | 158 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `野球` | やきゅう | 0.241 | 0.241 | topic_hint:sports_fitness | 1.000 | 1243 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ゴルフ` | ごるふ | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 1881 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `サッカー` | さっかー | 0.189 | 0.189 | topic_hint:sports_fitness | 1.000 | 1945 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 2457 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `スキー` | すきー | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 2514 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `テニス` | てにす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 3422 -> 65 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `体操` | たいそう | 0.339 | 0.339 | topic_hint:sports_fitness | 1.000 | 3208 -> 84 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `陸上` | りくじょう | 0.352 | 0.352 | topic_hint:sports_fitness | 1.000 | 3777 -> 120 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `相撲` | すもう | 0.350 | 0.350 | topic_hint:sports_fitness | 1.000 | 4243 -> 142 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `水泳` | すいえい | 0.155 | 0.155 | topic_hint:sports_fitness | 1.000 | 5836 -> 200 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `マラソン` | まらそん | 0.306 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `柔道` | じゅうどう | 0.137 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `スケート` | すけーと | 0.260 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 15 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 17 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `games_intermediate`

Games preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `カード` | かーど | 0.172 | 0.172 | topic_hint:games | 0.996 | 615 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 0.993 | 743 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 0.997 | 1551 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 1.000 | 2034 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `試合` | しあい | 0.132 | 0.132 | topic_hint:games | 0.871 | 727 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ランキング` | らんきんぐ | 0.184 | 0.184 | topic_hint:games | 1.000 | 2708 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:games | 1.000 | 3559 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `得点` | とくてん | 0.343 | 0.343 | topic_hint:games | 1.000 | 3697 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `逆転` | ぎゃくてん | 0.344 | 0.344 | topic_hint:games | 1.000 | 4093 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `防御` | ぼうぎょ | 0.319 | 0.319 | topic_hint:games | 1.000 | 4355 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `局面` | きょくめん | 0.369 | 0.369 | topic_hint:games | 1.000 | 4716 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `読み` | よみ | 0.264 | 0.264 | topic_hint:games | 1.000 | 4770 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ターン` | たーん | 0.297 | 0.297 | topic_hint:games | 1.000 | 4772 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ボス` | ぼす | 0.297 | 0.297 | topic_hint:games | 1.000 | 4784 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:games | 1.000 | 3633 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `hobbies_crafts_intermediate`

Hobbies/crafts preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 0.994 | 474 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 1.000 | 1899 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ドライブ` | どらいぶ | 0.203 | 0.203 | topic_hint:hobbies_crafts | 1.000 | 1997 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:hobbies_crafts | 0.988 | 2120 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `日記` | にっき | 0.150 | 0.150 | topic_hint:hobbies_crafts | 0.948 | 1690 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `キャンプ` | きゃんぷ | 0.244 | 0.244 | topic_hint:hobbies_crafts | 1.000 | 2767 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `釣り` | つり | 0.257 | 0.257 | topic_hint:hobbies_crafts | 1.000 | 2873 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `工作` | こうさく | 0.338 | 0.338 | topic_hint:hobbies_crafts | 1.000 | 2882 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `録音` | ろくおん | 0.333 | 0.333 | topic_hint:hobbies_crafts | 1.000 | 3211 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:hobbies_crafts | 1.000 | 3280 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `絵画` | かいが | 0.254 | 0.254 | topic_hint:hobbies_crafts | 1.000 | 3323 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `手作り` | てづくり | 0.341 | 0.341 | topic_hint:hobbies_crafts | 1.000 | 3364 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `彫刻` | ちょうこく | 0.360 | 0.360 | topic_hint:hobbies_crafts | 1.000 | 3849 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `演劇` | えんげき | 0.371 | 0.371 | topic_hint:hobbies_crafts | 1.000 | 4629 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `天文` | てんもん | 0.383 | 0.383 | topic_hint:hobbies_crafts | 1.000 | 4738 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `縫う` | ぬう | 0.334 | 0.334 | topic_hint:hobbies_crafts | 1.000 | 7305 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `水槽` | すいそう | 0.345 | 0.345 | topic_hint:hobbies_crafts | 1.000 | 4931 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_advanced`

Arts/literature/humanities preference at advanced-tail proficiency.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `短歌` | たんか | 0.428 | 0.428 | topic_hint:arts_literature_humanities | 0.971 | 6498 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `感` | かん | 0.531 | 0.531 |  | 0.913 | 201 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `通ずる` | つうずる | 0.527 | 0.527 |  | 0.893 | 2253 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `御座る` | ござる | 0.493 | 0.493 |  | 0.703 | 634 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `えっ` | えっ | 0.559 | 0.559 |  | 0.992 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `オブ` | おぶ | 0.579 | 0.579 |  | 1.000 | 1683 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `炉` | ろ | 0.578 | 0.578 |  | 1.000 | 1848 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_work_computing`

Weighted mixed professional and computing interests.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet', 'work_office']` applied_seed_count=`131`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム
- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 0.967 | 386 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 0.995 | 598 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 0.944 | 301 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `サイト` | さいと | 0.395 | 0.395 | topic_hint:computing_internet | 1.000 | 688 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `携帯` | けいたい | 0.217 | 0.217 | topic_hint:computing_internet | 0.989 | 628 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 0.930 | 321 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `インターネット` | いんたーねっと | 0.456 | 0.456 | topic_hint:computing_internet | 1.000 | 851 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `機械` | きかい | 0.216 | 0.216 | topic_hint:computing_internet | 0.989 | 758 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 0.908 | 242 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 0.981 | 710 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `電子` | でんし | 0.221 | 0.221 | topic_hint:computing_internet | 0.995 | 835 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `実行` | じっこう | 0.217 | 0.217 | topic_hint:computing_internet | 0.991 | 806 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 0.904 | 265 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `許可` | きょか | 0.239 | 0.239 | topic_hint:computing_internet | 1.000 | 998 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 0.903 | 275 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 0.899 | 269 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `画像` | がぞう | 0.206 | 0.206 | topic_hint:computing_internet | 0.966 | 732 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_food_travel`

Weighted food/travel interests at lower-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking', 'travel_places_transport']` applied_seed_count=`88`

Active topic support:

- `food_cooking` candidates=46 mass=14.625705 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味
- `travel_places_transport` candidates=43 mass=16.315422 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `日本` | にっぽん | 0.124 | 0.124 | topic_hint:travel_places_transport | 1.000 | 10 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `飲む` | のむ | 0.053 | 0.053 | topic_hint:food_cooking | 0.956 | 1456 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `道路` | どうろ | 0.200 | 0.200 | topic_hint:travel_places_transport | 1.000 | 375 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `銀行` | ぎんこう | 0.053 | 0.053 | topic_hint:travel_places_transport | 0.959 | 309 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `駅` | えき | 0.048 | 0.048 | topic_hint:travel_places_transport | 0.940 | 256 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `バス` | ばす | 0.118 | 0.118 | topic_hint:travel_places_transport | 1.000 | 622 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `観光` | かんこう | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 678 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ホテル` | ほてる | 0.055 | 0.055 | topic_hint:travel_places_transport | 0.963 | 458 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `会場` | かいじょう | 0.146 | 0.146 | topic_hint:travel_places_transport | 1.000 | 739 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `店` | みせ | 0.043 | 0.043 | topic_hint:travel_places_transport | 0.919 | 241 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `車` | くるま | 0.036 | 0.036 | topic_hint:travel_places_transport | 0.889 | 146 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `旅行` | りょこう | 0.057 | 0.057 | topic_hint:travel_places_transport | 0.967 | 531 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `船` | ふね | 0.136 | 0.136 | topic_hint:travel_places_transport | 1.000 | 826 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `野菜` | やさい | 0.067 | 0.067 | topic_hint:food_cooking | 0.990 | 786 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:food_cooking | 0.927 | 346 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `食べる` | たべる | 0.027 | 0.027 | topic_hint:food_cooking | 0.844 | 1005 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_science_medicine`

Weighted science/medicine interests at upper-intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['science_math', 'medicine_health']` applied_seed_count=`42`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院
- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 1.000 | 1686 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 0.919 | 1077 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `爪` | つめ | 0.299 | 0.299 | topic_hint:medicine_health | 1.000 | 2636 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 0.953 | 1835 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 1.000 | 2932 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `胃` | い | 0.257 | 0.257 | topic_hint:medicine_health | 0.968 | 2357 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 0.960 | 2269 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 0.893 | 1498 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `怪我` | けが | 0.244 | 0.244 | topic_hint:medicine_health | 0.927 | 2070 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 0.857 | 1018 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 0.884 | 1583 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 0.791 | 802 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 0.784 | 758 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 0.766 | 744 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 0.760 | 737 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 0.763 | 821 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 0.776 | 1058 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 0.705 | 513 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_beginner`

Food/cooking preference at upper beginner proficiency.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `食べる` | たべる | 0.027 | 0.027 | topic_hint:food_cooking | 1.000 | 1005 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `飲む` | のむ | 0.053 | 0.053 | topic_hint:food_cooking | 1.000 | 1456 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:food_cooking | 1.000 | 346 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `野菜` | やさい | 0.067 | 0.067 | topic_hint:food_cooking | 1.000 | 786 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 1.000 | 3361 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `肉` | にく | 0.083 | 0.083 | topic_hint:food_cooking | 1.000 | 1016 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `甘い` | あまい | 0.072 | 0.072 | topic_hint:food_cooking | 1.000 | 2133 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `コーヒー` | こーひー | 0.117 | 0.117 | topic_hint:food_cooking | 1.000 | 1209 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `冷たい` | つめたい | 0.088 | 0.088 | topic_hint:food_cooking | 1.000 | 2413 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ワイン` | わいん | 0.173 | 0.173 | topic_hint:food_cooking | 1.000 | 1534 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `熱い` | あつい | 0.087 | 0.087 | topic_hint:food_cooking | 1.000 | 2615 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `味噌` | みそ | 0.152 | 0.152 | topic_hint:food_cooking | 1.000 | 1560 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `醤油` | しょうゆ | 0.095 | 0.095 | topic_hint:food_cooking | 1.000 | 1780 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `鍋` | なべ | 0.251 | 0.251 | topic_hint:food_cooking | 1.000 | 1632 -> 56 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `カレー` | かれー | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 1880 -> 57 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `anime_manga_intermediate`

Anime/manga/pop-culture preference at intermediate proficiency.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 0.999 | 282 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 0.996 | 615 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `イベント` | いべんと | 0.171 | 0.171 | topic_hint:anime_manga_pop_culture | 0.996 | 1291 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `スペース` | すぺーす | 0.203 | 0.203 | topic_hint:anime_manga_pop_culture | 1.000 | 1983 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `予約` | よやく | 0.144 | 0.144 | topic_hint:anime_manga_pop_culture | 0.926 | 1024 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `感想` | かんそう | 0.286 | 0.286 | topic_hint:anime_manga_pop_culture | 1.000 | 2290 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:anime_manga_pop_culture | 1.000 | 2848 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ブーム` | ぶーむ | 0.188 | 0.188 | topic_hint:anime_manga_pop_culture | 1.000 | 3114 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `考察` | こうさつ | 0.329 | 0.329 | topic_hint:anime_manga_pop_culture | 1.000 | 3253 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `動画` | どうが | 0.200 | 0.200 | topic_hint:anime_manga_pop_culture | 1.000 | 3380 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 3559 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ロボット` | ろぼっと | 0.193 | 0.193 | topic_hint:anime_manga_pop_culture | 1.000 | 3642 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `学園` | がくえん | 0.339 | 0.339 | topic_hint:anime_manga_pop_culture | 1.000 | 3683 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
