# en-ja SRS Admission Preference Sample Pack

- status: `WARN`
- findings: pass=84 warn=13 fail=0
- scenarios: `95`
- topic scenarios with movers: `77` / `90`
- runtime scope: `admission_preview_only`

## Method

- strategy: `profile_bootstrap`
- profile shape: single proficiency estimate plus optional topic_weights/interests
- runtime difficulty source: profile_bootstrap uses the corrected en-ja learner-difficulty CSV through an explicit runtime hook when the CSV is available; otherwise it falls back to runtime commonness signals.
- state mutation: none; previews run under a temporary helper data root

## Inputs

- config_json: `docs/test_inputs/srs_admission_topic_proficiency_grid_configs_en_ja.json`
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
| `neutral_p10` | 0.100 | - | 0 | - | 0 | する, いる, ある, 言う, こと, なる, その, よう |
| `neutral_p25` | 0.250 | - | 0 | - | 0 | ある, こと, 無い, よう, 思う, 見る, 出来る, 因る |
| `neutral_p45` | 0.450 | - | 0 | - | 0 | 無い, 御座る, 良く, 矢張り, 共, センター, 其々, 此方 |
| `neutral_p65` | 0.650 | - | 0 | - | 0 | 御座る, 項, 感, 論, 通ずる, 府, 因み, 層 |
| `neutral_p85` | 0.850 | - | 0 | - | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `animals_p10` | 0.100 | animals | 6 | applied | 0 | 犬, 猫, 馬, 鳥, 虫, 牛, 虎, 熊 |
| `animals_p25` | 0.250 | animals | 11 | applied | 0 | 犬, 猫, 馬, 鳥, 虫, 牛, 虎, 熊 |
| `animals_p45` | 0.450 | animals | 15 | applied | 0 | 馬, 牛, 虫, 熊, 虎, 亀, 蝶, 烏 |
| `animals_p65` | 0.650 | animals | 10 | applied | 0 | 烏, 烏賊, 狐, 蛸, 蝶, 蜂, 亀, 鹿 |
| `animals_p85` | 0.850 | animals | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `anime_manga_pop_culture_p10` | 0.100 | anime_manga_pop_culture | 16 | applied | 0 | 作品, 設定, カード, 予約, 日常, 発売, イベント, 漫画 |
| `anime_manga_pop_culture_p25` | 0.250 | anime_manga_pop_culture | 27 | applied | 0 | 作品, 設定, カード, 日常, 予約, 発売, イベント, ファン |
| `anime_manga_pop_culture_p45` | 0.450 | anime_manga_pop_culture | 40 | applied | 0 | 作品, 設定, カード, ファン, 日常, 発売, イベント, コメント |
| `anime_manga_pop_culture_p65` | 0.650 | anime_manga_pop_culture | 31 | applied | 0 | ファン, コメント, キャラ, イラスト, タッチ, ポスター, 連載, 制服 |
| `anime_manga_pop_culture_p85` | 0.850 | anime_manga_pop_culture | 5 | applied | 0 | キャラ, イラスト, タッチ, ポスター, 属性, コメント, ファン, クリア |
| `arts_literature_humanities_p10` | 0.100 | arts_literature_humanities | 15 | applied | 0 | 本, 歴史, 絵, 手紙, 小説, 文学, 宗教, 物語 |
| `arts_literature_humanities_p25` | 0.250 | arts_literature_humanities | 17 | applied | 0 | 本, 歴史, 絵, 手紙, 宗教, 小説, 物語, 美術 |
| `arts_literature_humanities_p45` | 0.450 | arts_literature_humanities | 14 | applied | 0 | 宗教, 物語, 美術, 芸術, 歴史, 哲学, 小説, 日記 |
| `arts_literature_humanities_p65` | 0.650 | arts_literature_humanities | 1 | applied | 0 | 短歌, 哲学, 御座る, 項, 感, 論, 通ずる, 府 |
| `arts_literature_humanities_p85` | 0.850 | arts_literature_humanities | 0 | applied | 0 | 短歌, クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ |
| `computing_internet_p10` | 0.100 | computing_internet | 40 | applied | 0 | 情報, 電話, 写真, 開発, システム, メール, 設定, 処理 |
| `computing_internet_p25` | 0.250 | computing_internet | 40 | applied | 0 | 情報, 電話, 写真, 開発, システム, メール, 処理, 条件 |
| `computing_internet_p45` | 0.450 | computing_internet | 40 | applied | 0 | 情報, 開発, 処理, 条件, 設定, システム, メール, データ |
| `computing_internet_p65` | 0.650 | computing_internet | 40 | applied | 0 | サイト, インターネット, コメント, ソース, サーバー, インストール, 変数, 閲覧 |
| `computing_internet_p85` | 0.850 | computing_internet | 14 | applied | 0 | インストール, ブラウザ, インターフェース, ブロードバンド, バッテリー, テレワーク, クッキー, サーバー |
| `food_cooking_p10` | 0.100 | food_cooking | 33 | applied | 0 | 食べる, 飲む, 料理, 味, 野菜, 酒, パン, 肉 |
| `food_cooking_p25` | 0.250 | food_cooking | 40 | applied | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, 茶, パン |
| `food_cooking_p45` | 0.450 | food_cooking | 31 | applied | 0 | 酒, 茶, ビール, ワイン, 鍋, 焼く, スープ, 味 |
| `food_cooking_p65` | 0.650 | food_cooking | 11 | applied | 0 | 喫茶, 煮る, 箸, 包丁, 餅, 人参, 饂飩, 玉葱 |
| `food_cooking_p85` | 0.850 | food_cooking | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `games_p10` | 0.100 | games | 11 | applied | 0 | カード, 試合, ゲーム, 大会, 戦略, ルール, 作戦, ステージ |
| `games_p25` | 0.250 | games | 17 | applied | 0 | カード, 試合, ゲーム, 大会, レベル, 戦略, ルール, 作戦 |
| `games_p45` | 0.450 | games | 33 | applied | 0 | レベル, カード, 大会, ゲーム, 戦略, ルール, 作戦, 勝負 |
| `games_p65` | 0.650 | games | 23 | applied | 0 | レベル, キャラ, クリア, 局面, 戦術, 点数, 得点, 逆転 |
| `games_p85` | 0.850 | games | 5 | applied | 0 | クリア, キャラ, 詰め, リーチ, 打開, 一手, 攻勢, レベル |
| `hobbies_crafts_p10` | 0.100 | hobbies_crafts | 23 | applied | 0 | 写真, 映画, 料理, 音楽, 旅行, 歌, 絵, ブログ |
| `hobbies_crafts_p25` | 0.250 | hobbies_crafts | 30 | applied | 0 | 写真, 映画, 料理, 音楽, 撮影, ブログ, 旅行, 歌 |
| `hobbies_crafts_p45` | 0.450 | hobbies_crafts | 37 | applied | 0 | 撮影, ブログ, 編集, 収集, 栽培, ドライブ, ピアノ, 日記 |
| `hobbies_crafts_p65` | 0.650 | hobbies_crafts | 21 | applied | 0 | 彫刻, 天文, 演劇, 工作, 模型, 手作り, 金魚, 短歌 |
| `hobbies_crafts_p85` | 0.850 | hobbies_crafts | 1 | applied | 0 | 野鳥, 星空, 短歌, 陶芸, クリア, ジャバ, インターフェース, ウォッチ |
| `law_politics_civics_p10` | 0.100 | law_politics_civics | 20 | applied | 0 | 社会, 政府, 事件, 国民, 政治, 法律, 警察, 市民 |
| `law_politics_civics_p25` | 0.250 | law_politics_civics | 20 | applied | 0 | 社会, 政府, 事件, 国民, 政治, 法律, 市民, 警察 |
| `law_politics_civics_p45` | 0.450 | law_politics_civics | 20 | applied | 0 | 政府, 事件, 国民, 裁判, 権利, 義務, 社会, 選挙 |
| `law_politics_civics_p65` | 0.650 | law_politics_civics | 1 | applied | 0 | 作戦, 御座る, 項, 感, 論, 通ずる, 府, 因み |
| `law_politics_civics_p85` | 0.850 | law_politics_civics | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `medicine_health_p10` | 0.100 | medicine_health | 24 | applied | 0 | 目, 顔, 口, 病院, 足, 病気, 胸, 指 |
| `medicine_health_p25` | 0.250 | medicine_health | 24 | applied | 0 | 目, 顔, 口, 病院, 足, 胸, 病気, 腰 |
| `medicine_health_p45` | 0.450 | medicine_health | 16 | applied | 0 | 顔, 胸, 腰, 肩, 脳, 腹, 指, 血 |
| `medicine_health_p65` | 0.650 | medicine_health | 2 | applied | 0 | 爪, 皮膚, 御座る, 項, 感, 論, 通ずる, 府 |
| `medicine_health_p85` | 0.850 | medicine_health | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `music_media_entertainment_p10` | 0.100 | music_media_entertainment | 20 | applied | 0 | 写真, テレビ, 映画, 新聞, 音楽, 放送, 歌, 監督 |
| `music_media_entertainment_p25` | 0.250 | music_media_entertainment | 23 | applied | 0 | 写真, テレビ, 映画, 新聞, 音楽, 放送, 監督, 歌 |
| `music_media_entertainment_p45` | 0.450 | music_media_entertainment | 16 | applied | 0 | 監督, 広告, 演奏, 放送, ピアノ, 番組, アニメ, テレビ |
| `music_media_entertainment_p65` | 0.650 | music_media_entertainment | 5 | applied | 0 | 太鼓, 合唱, 楽器, ドラム, 音声, 御座る, 項, 感 |
| `music_media_entertainment_p85` | 0.850 | music_media_entertainment | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `plants_nature_p10` | 0.100 | plants_nature | 11 | applied | 0 | 花, 雨, 地震, 森, 季節, 天気, 雲, 台風 |
| `plants_nature_p25` | 0.250 | plants_nature | 14 | applied | 0 | 花, 雨, 地震, 森, 季節, 雲, 天気, 気温 |
| `plants_nature_p45` | 0.450 | plants_nature | 18 | applied | 0 | 森, 雲, 地震, 林檎, 気温, 季節, 豆, 葡萄 |
| `plants_nature_p65` | 0.650 | plants_nature | 10 | applied | 0 | 苺, 洪水, 杉, 麦, 蜜柑, 火山, 津波, 檜 |
| `plants_nature_p85` | 0.850 | plants_nature | 1 | applied | 0 | 檜, クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ |
| `science_math_p10` | 0.100 | science_math | 14 | applied | 0 | 研究, 科学, 電気, 計算, 機械, 実験, 数字, 化学 |
| `science_math_p25` | 0.250 | science_math | 15 | applied | 0 | 研究, 科学, 計算, 電気, 機械, 実験, 数字, 理論 |
| `science_math_p45` | 0.450 | science_math | 14 | applied | 0 | 計算, 機械, 実験, 研究, 理論, 数字, 化学, 温度 |
| `science_math_p65` | 0.650 | science_math | 3 | applied | 0 | 三角, 理論, 公式, 御座る, 項, 感, 論, 通ずる |
| `science_math_p85` | 0.850 | science_math | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `shopping_money_p10` | 0.100 | shopping_money | 22 | applied | 0 | 高い, 買う, 店, 商品, 価格, 売る, 安い, 払う |
| `shopping_money_p25` | 0.250 | shopping_money | 24 | applied | 0 | 高い, 買う, 商品, 店, 価格, 売る, 無料, 安い |
| `shopping_money_p45` | 0.450 | shopping_money | 18 | applied | 0 | 商品, 価格, 無料, 会計, 債権, 料金, 支払う, スーパー |
| `shopping_money_p65` | 0.650 | shopping_money | 2 | applied | 0 | 債権, 商店, コンビニ, 御座る, 項, 感, 論, 通ずる |
| `shopping_money_p85` | 0.850 | shopping_money | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `sports_fitness_p10` | 0.100 | sports_fitness | 7 | applied | 0 | センター, 野球, ゴルフ, サッカー, ダンス, スキー, テニス, 体操 |
| `sports_fitness_p25` | 0.250 | sports_fitness | 11 | applied | 0 | センター, 野球, ゴルフ, サッカー, ダンス, スキー, テニス, 体操 |
| `sports_fitness_p45` | 0.450 | sports_fitness | 14 | applied | 0 | センター, 野球, サッカー, ゴルフ, スキー, 体操, 陸上, 相撲 |
| `sports_fitness_p65` | 0.650 | sports_fitness | 5 | applied | 0 | 陸上, 相撲, 体操, センター, マラソン, 御座る, 項, 感 |
| `sports_fitness_p85` | 0.850 | sports_fitness | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `travel_places_transport_p10` | 0.100 | travel_places_transport | 34 | applied | 0 | 会社, 学校, 車, 日本, 店, 駅, 病院, 銀行 |
| `travel_places_transport_p25` | 0.250 | travel_places_transport | 35 | applied | 0 | 会社, 学校, 車, 日本, 店, 駅, 病院, 銀行 |
| `travel_places_transport_p45` | 0.450 | travel_places_transport | 23 | applied | 0 | 道路, 観光, スーパー, 会場, 日本, 列車, バイク, 教会 |
| `travel_places_transport_p65` | 0.650 | travel_places_transport | 0 | applied | 0 | コンビニ, 御座る, 項, 感, 論, 通ずる, 府, 因み |
| `travel_places_transport_p85` | 0.850 | travel_places_transport | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `work_office_p10` | 0.100 | work_office | 24 | applied | 0 | 会社, 仕事, 働く, 事務, 予定, 報告, 連絡, 会議 |
| `work_office_p25` | 0.250 | work_office | 26 | applied | 0 | 会社, 仕事, 事務, 報告, 働く, 資料, 契約, 予定 |
| `work_office_p45` | 0.450 | work_office | 26 | applied | 0 | 事務, 報告, 資料, 契約, 職員, 社員, 職業, 勤務 |
| `work_office_p65` | 0.650 | work_office | 10 | applied | 0 | 出勤, 残業, 出張, 役員, 商標, 部下, 面接, 上司 |
| `work_office_p85` | 0.850 | work_office | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `mixed_hard_topics_p10` | 0.100 | arts_literature_humanities, law_politics_civics | 35 | applied | 0 | 社会, 政府, 事件, 本, 国民, 政治, 歴史, 法律 |
| `mixed_science_medicine_p20` | 0.200 | science_math, medicine_health | 39 | applied | 0 | 目, 研究, 顔, 口, 病院, 足, 科学, 計算 |
| `mixed_work_computing_p25` | 0.250 | work_office, computing_internet | 40 | applied | 0 | 会社, 情報, 仕事, 電話, 写真, 開発, システム, 事務 |
| `mixed_arts_games_p45` | 0.450 | arts_literature_humanities, games | 40 | applied | 0 | レベル, カード, 大会, 宗教, ゲーム, 物語, 美術, 芸術 |
| `mixed_entertainment_cluster_p45` | 0.450 | anime_manga_pop_culture, games, hobbies_crafts | 40 | applied | 0 | 作品, 設定, 撮影, ブログ, レベル, カード, 大会, ゲーム |
| `mixed_professional_practical_p50` | 0.500 | work_office, computing_internet, shopping_money | 40 | applied | 0 | 通信, 職員, 資料, サイト, 携帯, 契約, インターネット, 会計 |
| `mixed_food_animals_p65` | 0.650 | food_cooking, animals | 21 | applied | 0 | 烏, 烏賊, 狐, 喫茶, 蛸, 蝶, 蜂, 亀 |
| `mixed_music_travel_p65` | 0.650 | music_media_entertainment, travel_places_transport | 5 | applied | 0 | 太鼓, 合唱, 楽器, ドラム, 音声, コンビニ, 御座る, 項 |
| `mixed_food_shopping_p85` | 0.850 | food_cooking, shopping_money | 0 | applied | 0 | クリア, ジャバ, インターフェース, ウォッチ, メソッド, エステ, レフ, ブロードバンド |
| `mixed_entertainment_cluster_p85` | 0.850 | anime_manga_pop_culture, games, hobbies_crafts | 10 | applied | 0 | クリア, キャラ, 詰め, イラスト, タッチ, ポスター, 属性, リーチ |

## Findings

- `PASS` `TOPIC_OVERLAY_AVAILABLE`: Product-shaped en-ja topic overlay was available for preview.
- `PASS` `CORRECTED_RANKING_DIAGNOSTIC_AVAILABLE`: Corrected learner-difficulty ranking was joined for diagnostics.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p10`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p25`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p45`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p65`: Neutral profile generated an admission preview.
- `PASS` `NEUTRAL_PROFILE_PREVIEW:neutral_p85`: Neutral profile generated an admission preview.
- `PASS` `TOPIC_PROFILE_PREVIEW:animals_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:animals_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:animals_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:animals_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:animals_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_pop_culture_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_pop_culture_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_pop_culture_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_pop_culture_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:anime_manga_pop_culture_p85`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_humanities_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_humanities_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_humanities_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:arts_literature_humanities_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:arts_literature_humanities_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:computing_internet_p85`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:food_cooking_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:food_cooking_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:games_p85`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:hobbies_crafts_p85`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:law_politics_civics_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:law_politics_civics_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:law_politics_civics_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:law_politics_civics_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:law_politics_civics_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:medicine_health_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:medicine_health_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:music_media_entertainment_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:music_media_entertainment_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:music_media_entertainment_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:music_media_entertainment_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:music_media_entertainment_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:plants_nature_p85`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:science_math_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:science_math_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:shopping_money_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:shopping_money_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:sports_fitness_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:sports_fitness_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:travel_places_transport_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:travel_places_transport_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:travel_places_transport_p45`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:travel_places_transport_p65`: Topic overlay was present but produced no admitted topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:travel_places_transport_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:work_office_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:work_office_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_hard_topics_p10`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_science_medicine_p20`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_work_computing_p25`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_arts_games_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_entertainment_cluster_p45`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_professional_practical_p50`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_food_animals_p65`: Topic preference produced runtime topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_music_travel_p65`: Topic preference produced runtime topic movers.
- `WARN` `TOPIC_PROFILE_PREVIEW:mixed_food_shopping_p85`: Topic overlay was present but produced no admitted topic movers.
- `PASS` `TOPIC_PROFILE_PREVIEW:mixed_entertainment_cluster_p85`: Topic preference produced runtime topic movers.

## Scenario Details

### `neutral_p10`

No topic preference at beginner stress level; topic preference must not overpower readiness.

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

### `neutral_p25`

No topic preference at upper-beginner level; should surface only approachable topic words.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 3 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `見る` | みる | 0.124 | 0.124 |  | 1.000 | 139 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `出来る` | できる | 0.223 | 0.223 |  | 1.000 | 148 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `因る` | よる | 0.165 | 0.165 |  | 1.000 | 205 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `時` | とき | 0.165 | 0.165 |  | 1.000 | 3 -> 9 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 10 | `良い` | よい | 0.080 | 0.080 |  | 0.976 | 24 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ため` |  | - | 0.160 |  | 1.000 | 5 -> 11 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 12 | `そう` | そう | 0.125 | 0.125 |  | 1.000 | 1139 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `又` | また | 0.165 | 0.165 |  | 1.000 | 3416 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `考える` | かんがえる | 0.125 | 0.125 |  | 1.000 | 354 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `仕舞う` | しまう | 0.165 | 0.165 |  | 1.000 | 358 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `場合` | ばあい | 0.125 | 0.125 |  | 1.000 | 16 -> 16 | Kept near frequency order with support from coverage_gain; strongest profile signal was proficiency_fit. |
| 17 | `彼` |  | - | 0.180 |  | 1.000 | 3727 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `遣る` | やる | 0.165 | 0.165 |  | 1.000 | 389 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `行う` | おこなう | 0.125 | 0.125 |  | 1.000 | 444 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `訳` | わけ | 0.127 | 0.127 |  | 1.000 | 19 -> 20 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `neutral_p45`

No topic preference at intermediate main-use level; expected to show clear topic movement.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `此方` | こちら | 0.321 | 0.321 |  | 1.000 | 6004 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `サービス` | さーびす | 0.302 | 0.302 |  | 1.000 | 231 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `旨い` | うまい | 0.354 | 0.354 |  | 1.000 | 754 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `我々` |  | - | 0.450 |  | 1.000 | 6278 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `然も` | しかも | 0.315 | 0.315 |  | 1.000 | 6287 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `なお` | なお | 0.415 | 0.415 |  | 1.000 | 6545 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `当該` | とうがい | 0.398 | 0.398 |  | 1.000 | 365 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `奴` | やつ | 0.331 | 0.331 |  | 1.000 | 370 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `出来る` | できる | 0.223 | 0.223 |  | 0.703 | 148 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `積り` | つもり | 0.356 | 0.356 |  | 1.000 | 418 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `限り` | かぎり | 0.334 | 0.334 |  | 1.000 | 428 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p65`

No topic preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `存ずる` | ぞんずる | 0.523 | 0.523 |  | 1.000 | 4343 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ライン` | らいん | 0.463 | 0.463 |  | 0.919 | 919 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `neutral_p85`

No topic preference at advanced-tail level; should separate useful domain words from recondite leftovers.

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `animals_p10`

Animals preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `犬` | いぬ | 0.072 | 0.072 | topic_hint:animals | 1.000 | 614 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `猫` | ねこ | 0.068 | 0.068 | topic_hint:animals | 1.000 | 770 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `馬` | うま | 0.211 | 0.211 | topic_hint:animals | 1.000 | 887 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `鳥` | とり | 0.068 | 0.068 | topic_hint:animals | 1.000 | 1354 -> 41 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `虫` | むし | 0.149 | 0.149 | topic_hint:animals | 1.000 | 1782 -> 64 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `牛` | うし | 0.248 | 0.248 | topic_hint:animals | 1.000 | 2140 -> 112 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `虎` | とら | 0.262 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 8 | `熊` | くま | 0.314 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 9 | `象` | ぞう | 0.265 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 10 | `亀` | かめ | 0.348 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 11 | `蝶` | ちょう | 0.358 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 12 | `蚊` | か | 0.317 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 5 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `なる` | なる | 0.002 | 0.002 |  | 1.000 | 47 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `animals_p25`

Animals preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `犬` | いぬ | 0.072 | 0.072 | topic_hint:animals | 1.000 | 614 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `猫` | ねこ | 0.068 | 0.068 | topic_hint:animals | 1.000 | 770 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `馬` | うま | 0.211 | 0.211 | topic_hint:animals | 1.000 | 887 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `鳥` | とり | 0.068 | 0.068 | topic_hint:animals | 1.000 | 1354 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `虫` | むし | 0.149 | 0.149 | topic_hint:animals | 1.000 | 1782 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `牛` | うし | 0.248 | 0.248 | topic_hint:animals | 1.000 | 2140 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `虎` | とら | 0.262 | 0.262 | topic_hint:animals | 1.000 | 3425 -> 89 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `熊` | くま | 0.314 | 0.314 | topic_hint:animals | 1.000 | 3109 -> 92 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `象` | ぞう | 0.265 | 0.265 | topic_hint:animals | 1.000 | 4066 -> 121 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `亀` | かめ | 0.348 | 0.348 | topic_hint:animals | 1.000 | 3929 -> 155 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `蝶` | ちょう | 0.358 | 0.358 | topic_hint:animals | 1.000 | 3987 -> 166 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `烏` | からす | 0.388 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `蚊` | か | 0.317 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `烏賊` | いか | 0.382 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 15 | `狐` | きつね | 0.380 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `蛸` | たこ | 0.385 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `蜂` | はち | 0.367 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `鹿` | しか | 0.362 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `animals_p45`

Animals preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `馬` | うま | 0.211 | 0.211 | topic_hint:animals | 1.000 | 887 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `牛` | うし | 0.248 | 0.248 | topic_hint:animals | 1.000 | 2140 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `虫` | むし | 0.149 | 0.149 | topic_hint:animals | 0.945 | 1782 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `熊` | くま | 0.314 | 0.314 | topic_hint:animals | 1.000 | 3109 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `虎` | とら | 0.262 | 0.262 | topic_hint:animals | 1.000 | 3425 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `亀` | かめ | 0.348 | 0.348 | topic_hint:animals | 1.000 | 3929 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `蝶` | ちょう | 0.358 | 0.358 | topic_hint:animals | 1.000 | 3987 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `烏` | からす | 0.388 | 0.388 | topic_hint:animals | 1.000 | 4001 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `象` | ぞう | 0.265 | 0.265 | topic_hint:animals | 1.000 | 4066 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `烏賊` | いか | 0.382 | 0.382 | topic_hint:animals | 1.000 | 4248 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `狐` | きつね | 0.380 | 0.380 | topic_hint:animals | 1.000 | 4460 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `蚊` | か | 0.317 | 0.317 | topic_hint:animals | 1.000 | 4724 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `蛸` | たこ | 0.385 | 0.385 | topic_hint:animals | 1.000 | 4757 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `蜂` | はち | 0.367 | 0.367 | topic_hint:animals | 1.000 | 5100 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `鹿` | しか | 0.362 | 0.362 | topic_hint:animals | 1.000 | 5591 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `animals_p65`

Animals preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `烏` | からす | 0.388 | 0.388 | topic_hint:animals | 1.000 | 4001 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `烏賊` | いか | 0.382 | 0.382 | topic_hint:animals | 1.000 | 4248 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `狐` | きつね | 0.380 | 0.380 | topic_hint:animals | 1.000 | 4460 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `蛸` | たこ | 0.385 | 0.385 | topic_hint:animals | 1.000 | 4757 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `蝶` | ちょう | 0.358 | 0.358 | topic_hint:animals | 0.971 | 3987 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `蜂` | はち | 0.367 | 0.367 | topic_hint:animals | 0.990 | 5100 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `亀` | かめ | 0.348 | 0.348 | topic_hint:animals | 0.939 | 3929 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `鹿` | しか | 0.362 | 0.362 | topic_hint:animals | 0.980 | 5591 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `熊` | くま | 0.314 | 0.314 | topic_hint:animals | 0.768 | 3109 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `蚊` | か | 0.317 | 0.317 | topic_hint:animals | 0.786 | 4724 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `animals_p85`

Animals preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['animals']` applied_seed_count=`20`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `anime_manga_pop_culture_p10`

Anime/manga/pop-culture preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 1.000 | 282 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 1.000 | 615 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `予約` | よやく | 0.144 | 0.144 | topic_hint:anime_manga_pop_culture | 1.000 | 1024 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 47 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `イベント` | いべんと | 0.171 | 0.171 | topic_hint:anime_manga_pop_culture | 1.000 | 1291 -> 51 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:anime_manga_pop_culture | 1.000 | 1711 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `スペース` | すぺーす | 0.203 | 0.203 | topic_hint:anime_manga_pop_culture | 1.000 | 1983 -> 86 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 88 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 100 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `感想` | かんそう | 0.286 | 0.286 | topic_hint:anime_manga_pop_culture | 1.000 | 2290 -> 145 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:anime_manga_pop_culture | 1.000 | 2848 -> 160 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ブーム` | ぶーむ | 0.188 | 0.188 | topic_hint:anime_manga_pop_culture | 1.000 | 3114 -> 162 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 0.913 | 831 -> 174 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `動画` | どうが | 0.200 | 0.200 | topic_hint:anime_manga_pop_culture | 1.000 | 3380 -> 187 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ロボット` | ろぼっと | 0.193 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `サークル` | さーくる | 0.195 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `キャラクター` | きゃらくたー | 0.280 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 20 | `考察` | こうさつ | 0.329 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |

### `anime_manga_pop_culture_p25`

Anime/manga/pop-culture preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 1.000 | 282 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 1.000 | 615 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `予約` | よやく | 0.144 | 0.144 | topic_hint:anime_manga_pop_culture | 1.000 | 1024 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `イベント` | いべんと | 0.171 | 0.171 | topic_hint:anime_manga_pop_culture | 1.000 | 1291 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:anime_manga_pop_culture | 1.000 | 1711 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `スペース` | すぺーす | 0.203 | 0.203 | topic_hint:anime_manga_pop_culture | 1.000 | 1983 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `感想` | かんそう | 0.286 | 0.286 | topic_hint:anime_manga_pop_culture | 1.000 | 2290 -> 51 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:anime_manga_pop_culture | 1.000 | 2848 -> 64 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ブーム` | ぶーむ | 0.188 | 0.188 | topic_hint:anime_manga_pop_culture | 1.000 | 3114 -> 79 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `動画` | どうが | 0.200 | 0.200 | topic_hint:anime_manga_pop_culture | 1.000 | 3380 -> 95 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ロボット` | ろぼっと | 0.193 | 0.193 | topic_hint:anime_manga_pop_culture | 1.000 | 3642 -> 104 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `サークル` | さーくる | 0.195 | 0.195 | topic_hint:anime_manga_pop_culture | 1.000 | 3797 -> 114 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 3559 -> 116 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `anime_manga_pop_culture_p45`

Anime/manga/pop-culture preference at intermediate main-use level; expected to show clear topic movement.

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

### `anime_manga_pop_culture_p65`

Anime/manga/pop-culture preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:anime_manga_pop_culture | 1.000 | 3633 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `イラスト` | いらすと | 0.505 | 0.505 | topic_hint:anime_manga_pop_culture | 1.000 | 3685 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `タッチ` | たっち | 0.493 | 0.493 | topic_hint:anime_manga_pop_culture | 1.000 | 4226 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ポスター` | ぽすたー | 0.474 | 0.474 | topic_hint:anime_manga_pop_culture | 1.000 | 4259 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `連載` | れんさい | 0.360 | 0.360 | topic_hint:anime_manga_pop_culture | 0.977 | 3745 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `制服` | せいふく | 0.360 | 0.360 | topic_hint:anime_manga_pop_culture | 0.977 | 4198 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `青春` | せいしゅん | 0.367 | 0.367 | topic_hint:anime_manga_pop_culture | 0.990 | 4674 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `脚本` | きゃくほん | 0.388 | 0.388 | topic_hint:anime_manga_pop_culture | 1.000 | 5049 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `傑作` | けっさく | 0.400 | 0.400 | topic_hint:anime_manga_pop_culture | 1.000 | 5383 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `予告` | よこく | 0.370 | 0.370 | topic_hint:anime_manga_pop_culture | 0.994 | 5360 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `表紙` | ひょうし | 0.351 | 0.351 | topic_hint:anime_manga_pop_culture | 0.952 | 4264 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `主役` | しゅやく | 0.348 | 0.348 | topic_hint:anime_manga_pop_culture | 0.940 | 3888 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `回想` | かいそう | 0.415 | 0.415 | topic_hint:anime_manga_pop_culture | 1.000 | 5952 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `特典` | とくてん | 0.382 | 0.382 | topic_hint:anime_manga_pop_culture | 1.000 | 6102 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `新作` | しんさく | 0.362 | 0.362 | topic_hint:anime_manga_pop_culture | 0.980 | 5644 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `尊い` | とうとい | 0.397 | 0.397 | topic_hint:anime_manga_pop_culture | 1.000 | 7175 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `原作` | げんさく | 0.344 | 0.344 | topic_hint:anime_manga_pop_culture | 0.926 | 4262 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `学園` | がくえん | 0.339 | 0.339 | topic_hint:anime_manga_pop_culture | 0.905 | 3683 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `anime_manga_pop_culture_p85`

Anime/manga/pop-culture preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture']` applied_seed_count=`55`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.679543 scarcity=eligible examples=作品, 設定, カード, ファン, 日常

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:anime_manga_pop_culture | 1.000 | 3633 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `イラスト` | いらすと | 0.505 | 0.505 | topic_hint:anime_manga_pop_culture | 0.714 | 3685 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `タッチ` | たっち | 0.493 | 0.493 | topic_hint:anime_manga_pop_culture | 0.637 | 4226 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ポスター` | ぽすたー | 0.474 | 0.474 | topic_hint:anime_manga_pop_culture | 0.509 | 4259 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `属性` | ぞくせい | 0.465 | 0.465 | topic_hint:anime_manga_pop_culture | 0.449 | 6380 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `コメント` | こめんと | 0.419 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 7 | `ファン` | ふぁん | 0.411 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 8 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_humanities_p10`

Arts/literature/humanities preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `本` | ほん | 0.055 | 0.055 | topic_hint:arts_literature_humanities | 1.000 | 224 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `歴史` | れきし | 0.133 | 0.133 | topic_hint:arts_literature_humanities | 1.000 | 255 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `絵` | え | 0.070 | 0.070 | topic_hint:arts_literature_humanities | 1.000 | 595 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `手紙` | てがみ | 0.081 | 0.081 | topic_hint:arts_literature_humanities | 1.000 | 757 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `小説` | しょうせつ | 0.136 | 0.136 | topic_hint:arts_literature_humanities | 1.000 | 837 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `文学` | ぶんがく | 0.134 | 0.134 | topic_hint:arts_literature_humanities | 1.000 | 1027 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `宗教` | しゅうきょう | 0.228 | 0.228 | topic_hint:arts_literature_humanities | 1.000 | 779 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `物語` | ものがたり | 0.221 | 0.221 | topic_hint:arts_literature_humanities | 1.000 | 882 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `詩` | し | 0.102 | 0.102 | topic_hint:arts_literature_humanities | 1.000 | 1392 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:arts_literature_humanities | 1.000 | 1298 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `美術` | びじゅつ | 0.240 | 0.240 | topic_hint:arts_literature_humanities | 1.000 | 992 -> 52 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `芸術` | げいじゅつ | 0.243 | 0.243 | topic_hint:arts_literature_humanities | 1.000 | 1051 -> 56 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `寺` | てら | 0.147 | 0.147 | topic_hint:arts_literature_humanities | 1.000 | 1689 -> 65 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `日記` | にっき | 0.150 | 0.150 | topic_hint:arts_literature_humanities | 1.000 | 1690 -> 67 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `哲学` | てつがく | 0.263 | 0.263 | topic_hint:arts_literature_humanities | 1.000 | 1556 -> 86 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `絵画` | かいが | 0.254 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `辞書` | じしょ | 0.104 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_humanities_p25`

Arts/literature/humanities preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `本` | ほん | 0.055 | 0.055 | topic_hint:arts_literature_humanities | 1.000 | 224 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `歴史` | れきし | 0.133 | 0.133 | topic_hint:arts_literature_humanities | 1.000 | 255 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `絵` | え | 0.070 | 0.070 | topic_hint:arts_literature_humanities | 1.000 | 595 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `手紙` | てがみ | 0.081 | 0.081 | topic_hint:arts_literature_humanities | 1.000 | 757 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `宗教` | しゅうきょう | 0.228 | 0.228 | topic_hint:arts_literature_humanities | 1.000 | 779 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `小説` | しょうせつ | 0.136 | 0.136 | topic_hint:arts_literature_humanities | 1.000 | 837 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `物語` | ものがたり | 0.221 | 0.221 | topic_hint:arts_literature_humanities | 1.000 | 882 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `美術` | びじゅつ | 0.240 | 0.240 | topic_hint:arts_literature_humanities | 1.000 | 992 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `文学` | ぶんがく | 0.134 | 0.134 | topic_hint:arts_literature_humanities | 1.000 | 1027 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `芸術` | げいじゅつ | 0.243 | 0.243 | topic_hint:arts_literature_humanities | 1.000 | 1051 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:arts_literature_humanities | 1.000 | 1298 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `詩` | し | 0.102 | 0.102 | topic_hint:arts_literature_humanities | 1.000 | 1392 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `哲学` | てつがく | 0.263 | 0.263 | topic_hint:arts_literature_humanities | 1.000 | 1556 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `寺` | てら | 0.147 | 0.147 | topic_hint:arts_literature_humanities | 1.000 | 1689 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `日記` | にっき | 0.150 | 0.150 | topic_hint:arts_literature_humanities | 1.000 | 1690 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `絵画` | かいが | 0.254 | 0.254 | topic_hint:arts_literature_humanities | 1.000 | 3323 -> 92 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `辞書` | じしょ | 0.104 | 0.104 | topic_hint:arts_literature_humanities | 1.000 | 4762 -> 159 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 20 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_humanities_p45`

Arts/literature/humanities preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `宗教` | しゅうきょう | 0.228 | 0.228 | topic_hint:arts_literature_humanities | 1.000 | 779 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `物語` | ものがたり | 0.221 | 0.221 | topic_hint:arts_literature_humanities | 1.000 | 882 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `美術` | びじゅつ | 0.240 | 0.240 | topic_hint:arts_literature_humanities | 1.000 | 992 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `芸術` | げいじゅつ | 0.243 | 0.243 | topic_hint:arts_literature_humanities | 1.000 | 1051 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `歴史` | れきし | 0.133 | 0.133 | topic_hint:arts_literature_humanities | 0.876 | 255 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `哲学` | てつがく | 0.263 | 0.263 | topic_hint:arts_literature_humanities | 1.000 | 1556 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `小説` | しょうせつ | 0.136 | 0.136 | topic_hint:arts_literature_humanities | 0.889 | 837 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `日記` | にっき | 0.150 | 0.150 | topic_hint:arts_literature_humanities | 0.948 | 1690 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:arts_literature_humanities | 0.912 | 1298 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `寺` | てら | 0.147 | 0.147 | topic_hint:arts_literature_humanities | 0.936 | 1689 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `文学` | ぶんがく | 0.134 | 0.134 | topic_hint:arts_literature_humanities | 0.882 | 1027 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `絵画` | かいが | 0.254 | 0.254 | topic_hint:arts_literature_humanities | 1.000 | 3323 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `短歌` | たんか | 0.428 | 0.428 | topic_hint:arts_literature_humanities | 1.000 | 6498 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `詩` | し | 0.102 | 0.102 | topic_hint:arts_literature_humanities | 0.695 | 1392 -> 70 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `センター` | せんたー | 0.299 | 0.299 |  | 1.000 | 158 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_humanities_p65`

Arts/literature/humanities preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `短歌` | たんか | 0.428 | 0.428 | topic_hint:arts_literature_humanities | 1.000 | 6498 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `哲学` | てつがく | 0.263 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `arts_literature_humanities_p85`

Arts/literature/humanities preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities']` applied_seed_count=`21`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `短歌` | たんか | 0.428 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 2 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `computing_internet_p10`

Computing/internet preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `情報` | じょうほう | 0.169 | 0.169 | topic_hint:computing_internet | 1.000 | 57 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `電話` | でんわ | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 92 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 107 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `開発` | かいはつ | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 122 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `システム` | しすてむ | 0.166 | 0.166 | topic_hint:computing_internet | 1.000 | 237 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `メール` | めーる | 0.168 | 0.168 | topic_hint:computing_internet | 1.000 | 260 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `設定` | せってい | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 282 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 1.000 | 269 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 1.000 | 275 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `データ` | でーた | 0.167 | 0.167 | topic_hint:computing_internet | 1.000 | 331 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 386 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `登録` | とうろく | 0.178 | 0.178 | topic_hint:computing_internet | 1.000 | 454 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:computing_internet | 1.000 | 474 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `パソコン` | ぱそこん | 0.165 | 0.165 | topic_hint:computing_internet | 1.000 | 577 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ソフト` | そふと | 0.165 | 0.165 | topic_hint:computing_internet | 1.000 | 643 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ファイル` | ふぁいる | 0.173 | 0.173 | topic_hint:computing_internet | 1.000 | 654 -> 41 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `携帯` | けいたい | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 628 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 1.000 | 710 -> 47 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `画像` | がぞう | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 732 -> 49 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `コンピューター` | こんぴゅーたー | 0.123 | 0.123 | topic_hint:computing_internet | 1.000 | 993 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `computing_internet_p25`

Computing/internet preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `情報` | じょうほう | 0.169 | 0.169 | topic_hint:computing_internet | 1.000 | 57 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `電話` | でんわ | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 92 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 107 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `開発` | かいはつ | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 122 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `システム` | しすてむ | 0.166 | 0.166 | topic_hint:computing_internet | 1.000 | 237 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `メール` | めーる | 0.168 | 0.168 | topic_hint:computing_internet | 1.000 | 260 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 1.000 | 269 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 1.000 | 275 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `設定` | せってい | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 282 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `データ` | でーた | 0.167 | 0.167 | topic_hint:computing_internet | 1.000 | 331 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 386 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `登録` | とうろく | 0.178 | 0.178 | topic_hint:computing_internet | 1.000 | 454 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:computing_internet | 1.000 | 474 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `パソコン` | ぱそこん | 0.165 | 0.165 | topic_hint:computing_internet | 1.000 | 577 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `携帯` | けいたい | 0.217 | 0.217 | topic_hint:computing_internet | 1.000 | 628 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ソフト` | そふと | 0.165 | 0.165 | topic_hint:computing_internet | 1.000 | 643 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ファイル` | ふぁいる | 0.173 | 0.173 | topic_hint:computing_internet | 1.000 | 654 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 1.000 | 710 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `画像` | がぞう | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 732 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `機械` | きかい | 0.216 | 0.216 | topic_hint:computing_internet | 1.000 | 758 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `computing_internet_p45`

Computing/internet preference at intermediate main-use level; expected to show clear topic movement.

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

### `computing_internet_p65`

Computing/internet preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `サイト` | さいと | 0.395 | 0.395 | topic_hint:computing_internet | 1.000 | 688 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `インターネット` | いんたーねっと | 0.456 | 0.456 | topic_hint:computing_internet | 1.000 | 851 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:computing_internet | 1.000 | 1538 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ソース` | そーす | 0.487 | 0.487 | topic_hint:computing_internet | 1.000 | 1961 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `サーバー` | さーばー | 0.498 | 0.498 | topic_hint:computing_internet | 1.000 | 2847 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `インストール` | いんすとーる | 0.596 | 0.596 | topic_hint:computing_internet | 1.000 | 2951 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `変数` | へんすう | 0.449 | 0.449 | topic_hint:computing_internet | 1.000 | 4169 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `閲覧` | えつらん | 0.359 | 0.359 | topic_hint:computing_internet | 0.974 | 3733 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `バッテリー` | ばってりー | 0.510 | 0.510 | topic_hint:computing_internet | 1.000 | 4767 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `パッケージ` | ぱっけーじ | 0.477 | 0.477 | topic_hint:computing_internet | 1.000 | 4776 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `圧縮` | あっしゅく | 0.354 | 0.354 | topic_hint:computing_internet | 0.961 | 3871 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `履歴` | りれき | 0.352 | 0.352 | topic_hint:computing_internet | 0.953 | 3857 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 | topic_hint:computing_internet | 1.000 | 5236 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `復元` | ふくげん | 0.360 | 0.360 | topic_hint:computing_internet | 0.975 | 4656 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `同期` | どうき | 0.345 | 0.345 | topic_hint:computing_internet | 0.927 | 3626 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `拡散` | かくさん | 0.364 | 0.364 | topic_hint:computing_internet | 0.984 | 5206 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `クッキー` | くっきー | 0.513 | 0.513 | topic_hint:computing_internet | 1.000 | 5661 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `回線` | かいせん | 0.335 | 0.335 | topic_hint:computing_internet | 0.884 | 2748 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `例外` | れいがい | 0.329 | 0.329 | topic_hint:computing_internet | 0.854 | 2447 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `受信` | じゅしん | 0.330 | 0.330 | topic_hint:computing_internet | 0.859 | 2562 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `computing_internet_p85`

Computing/internet preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['computing_internet']` applied_seed_count=`102`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `インストール` | いんすとーる | 0.596 | 0.596 | topic_hint:computing_internet | 1.000 | 2951 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 | topic_hint:computing_internet | 1.000 | 5236 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 | topic_hint:computing_internet | 1.000 | 6664 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 | topic_hint:computing_internet | 1.000 | 7260 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `バッテリー` | ばってりー | 0.510 | 0.510 | topic_hint:computing_internet | 0.744 | 4767 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `テレワーク` | てれわーく | 0.727 | 0.727 | topic_hint:computing_internet | 1.000 | 9115 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `クッキー` | くっきー | 0.513 | 0.513 | topic_hint:computing_internet | 0.761 | 5661 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `サーバー` | さーばー | 0.498 | 0.498 | topic_hint:computing_internet | 0.668 | 2847 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `デバッグ` | でばっぐ | 0.937 | 0.937 | topic_hint:computing_internet | 1.000 | 9063 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ソース` | そーす | 0.487 | 0.487 | topic_hint:computing_internet | 0.598 | 1961 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `チャット` | ちゃっと | 0.504 | 0.504 | topic_hint:computing_internet | 0.709 | 6550 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `パッケージ` | ぱっけーじ | 0.477 | 0.477 | topic_hint:computing_internet | 0.527 | 4776 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `インターネット` | いんたーねっと | 0.456 | 0.456 | topic_hint:computing_internet | 0.398 | 851 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `変数` | へんすう | 0.449 | 0.449 | topic_hint:computing_internet | 0.359 | 4169 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `コメント` | こめんと | 0.419 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p10`

Food/cooking preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `食べる` | たべる | 0.027 | 0.027 | topic_hint:food_cooking | 1.000 | 1005 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `飲む` | のむ | 0.053 | 0.053 | topic_hint:food_cooking | 1.000 | 1456 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:food_cooking | 1.000 | 346 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `野菜` | やさい | 0.067 | 0.067 | topic_hint:food_cooking | 1.000 | 786 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `肉` | にく | 0.083 | 0.083 | topic_hint:food_cooking | 1.000 | 1016 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 1.000 | 3361 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `甘い` | あまい | 0.072 | 0.072 | topic_hint:food_cooking | 1.000 | 2133 -> 41 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `コーヒー` | こーひー | 0.117 | 0.117 | topic_hint:food_cooking | 1.000 | 1209 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `冷たい` | つめたい | 0.088 | 0.088 | topic_hint:food_cooking | 1.000 | 2413 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `熱い` | あつい | 0.087 | 0.087 | topic_hint:food_cooking | 1.000 | 2615 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 60 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `味噌` | みそ | 0.152 | 0.152 | topic_hint:food_cooking | 1.000 | 1560 -> 65 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `醤油` | しょうゆ | 0.095 | 0.095 | topic_hint:food_cooking | 1.000 | 1780 -> 66 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ワイン` | わいん | 0.173 | 0.173 | topic_hint:food_cooking | 1.000 | 1534 -> 69 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `砂糖` | さとう | 0.100 | 0.100 | topic_hint:food_cooking | 1.000 | 1888 -> 71 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `カレー` | かれー | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 1880 -> 76 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p25`

Food/cooking preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `食べる` | たべる | 0.027 | 0.027 | topic_hint:food_cooking | 1.000 | 1005 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `飲む` | のむ | 0.053 | 0.053 | topic_hint:food_cooking | 1.000 | 1456 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:food_cooking | 1.000 | 346 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 1.000 | 667 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `野菜` | やさい | 0.067 | 0.067 | topic_hint:food_cooking | 1.000 | 786 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `パン` | ぱん | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 884 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 1.000 | 3361 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `肉` | にく | 0.083 | 0.083 | topic_hint:food_cooking | 1.000 | 1016 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `甘い` | あまい | 0.072 | 0.072 | topic_hint:food_cooking | 1.000 | 2133 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `コーヒー` | こーひー | 0.117 | 0.117 | topic_hint:food_cooking | 1.000 | 1209 -> 28 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `冷たい` | つめたい | 0.088 | 0.088 | topic_hint:food_cooking | 1.000 | 2413 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ワイン` | わいん | 0.173 | 0.173 | topic_hint:food_cooking | 1.000 | 1534 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `熱い` | あつい | 0.087 | 0.087 | topic_hint:food_cooking | 1.000 | 2615 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `味噌` | みそ | 0.152 | 0.152 | topic_hint:food_cooking | 1.000 | 1560 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `鍋` | なべ | 0.251 | 0.251 | topic_hint:food_cooking | 1.000 | 1632 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `醤油` | しょうゆ | 0.095 | 0.095 | topic_hint:food_cooking | 1.000 | 1780 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `カレー` | かれー | 0.118 | 0.118 | topic_hint:food_cooking | 1.000 | 1880 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p45`

Food/cooking preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `酒` | さけ | 0.199 | 0.199 | topic_hint:food_cooking | 1.000 | 606 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `茶` | ちゃ | 0.208 | 0.208 | topic_hint:food_cooking | 1.000 | 827 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ビール` | びーる | 0.186 | 0.186 | topic_hint:food_cooking | 1.000 | 1324 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ワイン` | わいん | 0.173 | 0.173 | topic_hint:food_cooking | 0.997 | 1534 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `鍋` | なべ | 0.251 | 0.251 | topic_hint:food_cooking | 1.000 | 1632 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `焼く` | やく | 0.147 | 0.147 | topic_hint:food_cooking | 0.935 | 3361 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `スープ` | すーぷ | 0.206 | 0.206 | topic_hint:food_cooking | 1.000 | 2102 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `味` | あじ | 0.135 | 0.135 | topic_hint:food_cooking | 0.887 | 667 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `トマト` | とまと | 0.180 | 0.180 | topic_hint:food_cooking | 1.000 | 2307 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `味噌` | みそ | 0.152 | 0.152 | topic_hint:food_cooking | 0.953 | 1560 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `豆腐` | とうふ | 0.306 | 0.306 | topic_hint:food_cooking | 1.000 | 2326 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `チーズ` | ちーず | 0.211 | 0.211 | topic_hint:food_cooking | 1.000 | 2338 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ラーメン` | らーめん | 0.167 | 0.167 | topic_hint:food_cooking | 0.990 | 2166 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:food_cooking | 1.000 | 2445 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `サラダ` | さらだ | 0.166 | 0.166 | topic_hint:food_cooking | 0.988 | 2252 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `煮る` | にる | 0.333 | 0.333 | topic_hint:food_cooking | 1.000 | 5705 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `玉葱` | たまねぎ | 0.313 | 0.313 | topic_hint:food_cooking | 1.000 | 2772 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `人参` | にんじん | 0.322 | 0.322 | topic_hint:food_cooking | 1.000 | 2836 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `饂飩` | うどん | 0.322 | 0.322 | topic_hint:food_cooking | 1.000 | 3342 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `餅` | もち | 0.327 | 0.327 | topic_hint:food_cooking | 1.000 | 3382 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p65`

Food/cooking preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `喫茶` | きっさ | 0.357 | 0.357 | topic_hint:food_cooking | 0.968 | 3597 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `煮る` | にる | 0.333 | 0.333 | topic_hint:food_cooking | 0.878 | 5705 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `箸` | はし | 0.337 | 0.337 | topic_hint:food_cooking | 0.894 | 3739 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `包丁` | ほうちょう | 0.338 | 0.338 | topic_hint:food_cooking | 0.902 | 4565 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `餅` | もち | 0.327 | 0.327 | topic_hint:food_cooking | 0.845 | 3382 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `人参` | にんじん | 0.322 | 0.322 | topic_hint:food_cooking | 0.819 | 2836 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `饂飩` | うどん | 0.322 | 0.322 | topic_hint:food_cooking | 0.815 | 3342 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `玉葱` | たまねぎ | 0.313 | 0.313 | topic_hint:food_cooking | 0.765 | 2772 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `豆腐` | とうふ | 0.306 | 0.306 | topic_hint:food_cooking | 0.717 | 2326 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:food_cooking | 0.708 | 2445 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `パスタ` | ぱすた | 0.306 | 0.306 | topic_hint:food_cooking | 0.719 | 5405 -> 49 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `food_cooking_p85`

Food/cooking preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking']` applied_seed_count=`46`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `games_p10`

Games preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `カード` | かーど | 0.172 | 0.172 | topic_hint:games | 1.000 | 615 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `試合` | しあい | 0.132 | 0.132 | topic_hint:games | 1.000 | 727 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 1.000 | 743 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 1.000 | 1551 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 91 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 114 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 1.000 | 2034 -> 124 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ランキング` | らんきんぐ | 0.184 | 0.184 | topic_hint:games | 1.000 | 2708 -> 128 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 0.907 | 597 -> 136 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `キャラクター` | きゃらくたー | 0.280 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `得点` | とくてん | 0.343 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `読み` | よみ | 0.264 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 15 | `逆転` | ぎゃくてん | 0.344 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `防御` | ぼうぎょ | 0.319 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `ターン` | たーん | 0.297 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `ボス` | ぼす | 0.297 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `games_p25`

Games preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `カード` | かーど | 0.172 | 0.172 | topic_hint:games | 1.000 | 615 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `試合` | しあい | 0.132 | 0.132 | topic_hint:games | 1.000 | 727 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 1.000 | 743 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 1.000 | 1551 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 1.000 | 2034 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ランキング` | らんきんぐ | 0.184 | 0.184 | topic_hint:games | 1.000 | 2708 -> 54 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `キャラクター` | きゃらくたー | 0.280 | 0.280 | topic_hint:games | 1.000 | 3559 -> 108 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `得点` | とくてん | 0.343 | 0.343 | topic_hint:games | 1.000 | 3697 -> 146 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `読み` | よみ | 0.264 | 0.264 | topic_hint:games | 1.000 | 4770 -> 160 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `逆転` | ぎゃくてん | 0.344 | 0.344 | topic_hint:games | 1.000 | 4093 -> 170 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `防御` | ぼうぎょ | 0.319 | 0.319 | topic_hint:games | 1.000 | 4355 -> 171 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ターン` | たーん | 0.297 | 0.297 | topic_hint:games | 1.000 | 4772 -> 199 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ボス` | ぼす | 0.297 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `対戦` | たいせん | 0.328 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 20 | `局面` | きょくめん | 0.369 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |

### `games_p45`

Games preference at intermediate main-use level; expected to show clear topic movement.

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

### `games_p65`

Games preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:games | 1.000 | 3633 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `クリア` | くりあ | 0.720 | 0.720 | topic_hint:games | 1.000 | 3366 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `局面` | きょくめん | 0.369 | 0.369 | topic_hint:games | 0.993 | 4716 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `戦術` | せんじゅつ | 0.373 | 0.373 | topic_hint:games | 0.997 | 5485 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `点数` | てんすう | 0.362 | 0.362 | topic_hint:games | 0.980 | 5122 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `得点` | とくてん | 0.343 | 0.343 | topic_hint:games | 0.919 | 3697 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `逆転` | ぎゃくてん | 0.344 | 0.344 | topic_hint:games | 0.926 | 4093 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `将棋` | しょうぎ | 0.382 | 0.382 | topic_hint:games | 1.000 | 6134 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `詰め` | つめ | 0.582 | 0.582 | topic_hint:games | 1.000 | 6407 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `優勢` | ゆうせい | 0.411 | 0.411 | topic_hint:games | 1.000 | 7252 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `一手` | いって | 0.435 | 0.435 | topic_hint:games | 1.000 | 7418 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `終盤` | しゅうばん | 0.398 | 0.398 | topic_hint:games | 1.000 | 7423 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `攻勢` | こうせい | 0.434 | 0.434 | topic_hint:games | 1.000 | 7482 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `打開` | だかい | 0.440 | 0.440 | topic_hint:games | 1.000 | 7608 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `勝敗` | しょうはい | 0.430 | 0.430 | topic_hint:games | 1.000 | 7803 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `対戦` | たいせん | 0.328 | 0.328 | topic_hint:games | 0.851 | 5065 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `防御` | ぼうぎょ | 0.319 | 0.319 | topic_hint:games | 0.799 | 4355 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 0.608 | 2034 -> 57 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `リーチ` | りーち | 0.488 | 0.488 | topic_hint:games | 1.000 | 8242 -> 67 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `games_p85`

Games preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['games']` applied_seed_count=`34`

Active topic support:

- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 | topic_hint:games | 1.000 | 3366 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:games | 1.000 | 3633 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `詰め` | つめ | 0.582 | 0.582 | topic_hint:games | 1.000 | 6407 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `リーチ` | りーち | 0.488 | 0.488 | topic_hint:games | 0.604 | 8242 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `打開` | だかい | 0.440 | 0.440 | topic_hint:games | 0.306 | 7608 -> 194 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `一手` | いって | 0.435 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 7 | `攻勢` | こうせい | 0.434 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 8 | `レベル` | れべる | 0.413 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 9 | `勝敗` | しょうはい | 0.430 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 10 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `hobbies_crafts_p10`

Hobbies/crafts preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:hobbies_crafts | 1.000 | 107 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `映画` | えいが | 0.051 | 0.051 | topic_hint:hobbies_crafts | 1.000 | 295 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:hobbies_crafts | 1.000 | 346 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `音楽` | おんがく | 0.060 | 0.060 | topic_hint:hobbies_crafts | 1.000 | 416 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `旅行` | りょこう | 0.057 | 0.057 | topic_hint:hobbies_crafts | 1.000 | 531 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `歌` | うた | 0.063 | 0.063 | topic_hint:hobbies_crafts | 1.000 | 546 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `絵` | え | 0.070 | 0.070 | topic_hint:hobbies_crafts | 1.000 | 595 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 1.000 | 474 -> 28 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 47 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `趣味` | しゅみ | 0.120 | 0.120 | topic_hint:hobbies_crafts | 1.000 | 1731 -> 61 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `散歩` | さんぽ | 0.092 | 0.092 | topic_hint:hobbies_crafts | 1.000 | 1819 -> 62 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `日記` | にっき | 0.150 | 0.150 | topic_hint:hobbies_crafts | 1.000 | 1690 -> 66 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:hobbies_crafts | 1.000 | 2120 -> 87 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:hobbies_crafts | 1.000 | 2457 -> 92 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ドライブ` | どらいぶ | 0.203 | 0.203 | topic_hint:hobbies_crafts | 1.000 | 1997 -> 93 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 101 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 1.000 | 1899 -> 128 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `登山` | とざん | 0.120 | 0.120 | topic_hint:hobbies_crafts | 1.000 | 3159 -> 137 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ギター` | ぎたー | 0.102 | 0.102 | topic_hint:hobbies_crafts | 1.000 | 3547 -> 153 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `hobbies_crafts_p25`

Hobbies/crafts preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:hobbies_crafts | 1.000 | 107 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `映画` | えいが | 0.051 | 0.051 | topic_hint:hobbies_crafts | 1.000 | 295 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `料理` | りょうり | 0.044 | 0.044 | topic_hint:hobbies_crafts | 1.000 | 346 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `音楽` | おんがく | 0.060 | 0.060 | topic_hint:hobbies_crafts | 1.000 | 416 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 1.000 | 474 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `旅行` | りょこう | 0.057 | 0.057 | topic_hint:hobbies_crafts | 1.000 | 531 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `歌` | うた | 0.063 | 0.063 | topic_hint:hobbies_crafts | 1.000 | 546 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `絵` | え | 0.070 | 0.070 | topic_hint:hobbies_crafts | 1.000 | 595 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `日記` | にっき | 0.150 | 0.150 | topic_hint:hobbies_crafts | 1.000 | 1690 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `趣味` | しゅみ | 0.120 | 0.120 | topic_hint:hobbies_crafts | 1.000 | 1731 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `散歩` | さんぽ | 0.092 | 0.092 | topic_hint:hobbies_crafts | 1.000 | 1819 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ドライブ` | どらいぶ | 0.203 | 0.203 | topic_hint:hobbies_crafts | 1.000 | 1997 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:hobbies_crafts | 1.000 | 2120 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 1.000 | 1899 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:hobbies_crafts | 1.000 | 2457 -> 53 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `キャンプ` | きゃんぷ | 0.244 | 0.244 | topic_hint:hobbies_crafts | 1.000 | 2767 -> 65 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `釣り` | つり | 0.257 | 0.257 | topic_hint:hobbies_crafts | 1.000 | 2873 -> 74 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `hobbies_crafts_p45`

Hobbies/crafts preference at intermediate main-use level; expected to show clear topic movement.

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

### `hobbies_crafts_p65`

Hobbies/crafts preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `彫刻` | ちょうこく | 0.360 | 0.360 | topic_hint:hobbies_crafts | 0.976 | 3849 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `天文` | てんもん | 0.383 | 0.383 | topic_hint:hobbies_crafts | 1.000 | 4738 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `演劇` | えんげき | 0.371 | 0.371 | topic_hint:hobbies_crafts | 0.995 | 4629 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `工作` | こうさく | 0.338 | 0.338 | topic_hint:hobbies_crafts | 0.900 | 2882 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `模型` | もけい | 0.382 | 0.382 | topic_hint:hobbies_crafts | 1.000 | 5677 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `手作り` | てづくり | 0.341 | 0.341 | topic_hint:hobbies_crafts | 0.913 | 3364 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `金魚` | きんぎょ | 0.403 | 0.403 | topic_hint:hobbies_crafts | 1.000 | 6323 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `短歌` | たんか | 0.428 | 0.428 | topic_hint:hobbies_crafts | 1.000 | 6498 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `録音` | ろくおん | 0.333 | 0.333 | topic_hint:hobbies_crafts | 0.876 | 3211 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `刺繍` | ししゅう | 0.380 | 0.380 | topic_hint:hobbies_crafts | 1.000 | 6630 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `水槽` | すいそう | 0.345 | 0.345 | topic_hint:hobbies_crafts | 0.930 | 4931 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `陶芸` | とうげい | 0.428 | 0.428 | topic_hint:hobbies_crafts | 1.000 | 7139 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `書道` | しょどう | 0.419 | 0.419 | topic_hint:hobbies_crafts | 1.000 | 7200 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:hobbies_crafts | 0.850 | 3280 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `野鳥` | やちょう | 0.446 | 0.446 | topic_hint:hobbies_crafts | 1.000 | 7761 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `縫う` | ぬう | 0.334 | 0.334 | topic_hint:hobbies_crafts | 0.878 | 7305 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `盆栽` | ぼんさい | 0.392 | 0.392 | topic_hint:hobbies_crafts | 1.000 | 7952 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `星空` | ほしぞら | 0.439 | 0.439 | topic_hint:hobbies_crafts | 1.000 | 7961 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `栽培` | さいばい | 0.309 | 0.309 | topic_hint:hobbies_crafts | 0.737 | 1899 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 0.686 | 1680 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `hobbies_crafts_p85`

Hobbies/crafts preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['hobbies_crafts']` applied_seed_count=`47`

Active topic support:

- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `野鳥` | やちょう | 0.446 | 0.446 | topic_hint:hobbies_crafts | 0.342 | 7761 -> 135 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `星空` | ほしぞら | 0.439 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 3 | `短歌` | たんか | 0.428 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 4 | `陶芸` | とうげい | 0.428 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 5 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `law_politics_civics_p10`

Law/politics/civics preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`20`

Active topic support:

- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `社会` | しゃかい | 0.125 | 0.125 | topic_hint:law_politics_civics | 1.000 | 37 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `政府` | せいふ | 0.178 | 0.178 | topic_hint:law_politics_civics | 1.000 | 116 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `事件` | じけん | 0.184 | 0.184 | topic_hint:law_politics_civics | 1.000 | 151 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `国民` | こくみん | 0.182 | 0.182 | topic_hint:law_politics_civics | 1.000 | 153 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `政治` | せいじ | 0.130 | 0.130 | topic_hint:law_politics_civics | 1.000 | 219 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `法律` | ほうりつ | 0.137 | 0.137 | topic_hint:law_politics_civics | 1.000 | 251 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `警察` | けいさつ | 0.134 | 0.134 | topic_hint:law_politics_civics | 1.000 | 340 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `市民` | しみん | 0.136 | 0.136 | topic_hint:law_politics_civics | 1.000 | 335 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `裁判` | さいばん | 0.207 | 0.207 | topic_hint:law_politics_civics | 1.000 | 361 -> 28 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `権利` | けんり | 0.222 | 0.222 | topic_hint:law_politics_civics | 1.000 | 561 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `義務` | ぎむ | 0.234 | 0.234 | topic_hint:law_politics_civics | 1.000 | 651 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `選挙` | せんきょ | 0.214 | 0.214 | topic_hint:law_politics_civics | 1.000 | 777 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `犯罪` | はんざい | 0.238 | 0.238 | topic_hint:law_politics_civics | 1.000 | 833 -> 49 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `大統領` | だいとうりょう | 0.216 | 0.216 | topic_hint:law_politics_civics | 1.000 | 1074 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `国会` | こっかい | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1182 -> 63 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `首相` | しゅしょう | 0.241 | 0.241 | topic_hint:law_politics_civics | 1.000 | 1190 -> 64 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `犯人` | はんにん | 0.250 | 0.250 | topic_hint:law_politics_civics | 1.000 | 1277 -> 71 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `投票` | とうひょう | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1839 -> 95 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:law_politics_civics | 1.000 | 1736 -> 102 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `税金` | ぜいきん | 0.254 | 0.254 | topic_hint:law_politics_civics | 1.000 | 2153 -> 127 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `law_politics_civics_p25`

Law/politics/civics preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`20`

Active topic support:

- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `社会` | しゃかい | 0.125 | 0.125 | topic_hint:law_politics_civics | 1.000 | 37 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `政府` | せいふ | 0.178 | 0.178 | topic_hint:law_politics_civics | 1.000 | 116 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `事件` | じけん | 0.184 | 0.184 | topic_hint:law_politics_civics | 1.000 | 151 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `国民` | こくみん | 0.182 | 0.182 | topic_hint:law_politics_civics | 1.000 | 153 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `政治` | せいじ | 0.130 | 0.130 | topic_hint:law_politics_civics | 1.000 | 219 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `法律` | ほうりつ | 0.137 | 0.137 | topic_hint:law_politics_civics | 1.000 | 251 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `市民` | しみん | 0.136 | 0.136 | topic_hint:law_politics_civics | 1.000 | 335 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `警察` | けいさつ | 0.134 | 0.134 | topic_hint:law_politics_civics | 1.000 | 340 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `裁判` | さいばん | 0.207 | 0.207 | topic_hint:law_politics_civics | 1.000 | 361 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `権利` | けんり | 0.222 | 0.222 | topic_hint:law_politics_civics | 1.000 | 561 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `義務` | ぎむ | 0.234 | 0.234 | topic_hint:law_politics_civics | 1.000 | 651 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `選挙` | せんきょ | 0.214 | 0.214 | topic_hint:law_politics_civics | 1.000 | 777 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `犯罪` | はんざい | 0.238 | 0.238 | topic_hint:law_politics_civics | 1.000 | 833 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `大統領` | だいとうりょう | 0.216 | 0.216 | topic_hint:law_politics_civics | 1.000 | 1074 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `国会` | こっかい | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1182 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `首相` | しゅしょう | 0.241 | 0.241 | topic_hint:law_politics_civics | 1.000 | 1190 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `犯人` | はんにん | 0.250 | 0.250 | topic_hint:law_politics_civics | 1.000 | 1277 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `投票` | とうひょう | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1839 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:law_politics_civics | 1.000 | 1736 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `税金` | ぜいきん | 0.254 | 0.254 | topic_hint:law_politics_civics | 1.000 | 2153 -> 51 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `law_politics_civics_p45`

Law/politics/civics preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`20`

Active topic support:

- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `政府` | せいふ | 0.178 | 0.178 | topic_hint:law_politics_civics | 1.000 | 116 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `事件` | じけん | 0.184 | 0.184 | topic_hint:law_politics_civics | 1.000 | 151 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `国民` | こくみん | 0.182 | 0.182 | topic_hint:law_politics_civics | 1.000 | 153 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `裁判` | さいばん | 0.207 | 0.207 | topic_hint:law_politics_civics | 1.000 | 361 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `権利` | けんり | 0.222 | 0.222 | topic_hint:law_politics_civics | 1.000 | 561 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `義務` | ぎむ | 0.234 | 0.234 | topic_hint:law_politics_civics | 1.000 | 651 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `社会` | しゃかい | 0.125 | 0.125 | topic_hint:law_politics_civics | 0.835 | 37 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `選挙` | せんきょ | 0.214 | 0.214 | topic_hint:law_politics_civics | 1.000 | 777 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `犯罪` | はんざい | 0.238 | 0.238 | topic_hint:law_politics_civics | 1.000 | 833 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `大統領` | だいとうりょう | 0.216 | 0.216 | topic_hint:law_politics_civics | 1.000 | 1074 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `法律` | ほうりつ | 0.137 | 0.137 | topic_hint:law_politics_civics | 0.893 | 251 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `国会` | こっかい | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1182 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `首相` | しゅしょう | 0.241 | 0.241 | topic_hint:law_politics_civics | 1.000 | 1190 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `犯人` | はんにん | 0.250 | 0.250 | topic_hint:law_politics_civics | 1.000 | 1277 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `市民` | しみん | 0.136 | 0.136 | topic_hint:law_politics_civics | 0.890 | 335 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `政治` | せいじ | 0.130 | 0.130 | topic_hint:law_politics_civics | 0.861 | 219 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `警察` | けいさつ | 0.134 | 0.134 | topic_hint:law_politics_civics | 0.879 | 340 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:law_politics_civics | 1.000 | 1736 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `投票` | とうひょう | 0.242 | 0.242 | topic_hint:law_politics_civics | 1.000 | 1839 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `税金` | ぜいきん | 0.254 | 0.254 | topic_hint:law_politics_civics | 1.000 | 2153 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `law_politics_civics_p65`

Law/politics/civics preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`20`

Active topic support:

- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:law_politics_civics | 0.581 | 1736 -> 53 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `存ずる` | ぞんずる | 0.523 | 0.523 |  | 1.000 | 4343 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `law_politics_civics_p85`

Law/politics/civics preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['law_politics_civics']` applied_seed_count=`20`

Active topic support:

- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_p10`

Medicine/health preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `目` | め | 0.020 | 0.020 | topic_hint:medicine_health | 1.000 | 33 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `顔` | かお | 0.169 | 0.169 | topic_hint:medicine_health | 1.000 | 56 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `口` | くち | 0.054 | 0.054 | topic_hint:medicine_health | 1.000 | 147 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `病院` | びょういん | 0.034 | 0.034 | topic_hint:medicine_health | 1.000 | 263 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `足` | あし | 0.058 | 0.058 | topic_hint:medicine_health | 1.000 | 288 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `病気` | びょうき | 0.062 | 0.062 | topic_hint:medicine_health | 1.000 | 534 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 1.000 | 513 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `指` | ゆび | 0.149 | 0.149 | topic_hint:medicine_health | 1.000 | 763 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `血` | ち | 0.150 | 0.150 | topic_hint:medicine_health | 1.000 | 829 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 1.000 | 737 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 744 -> 41 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `医者` | いしゃ | 0.082 | 0.082 | topic_hint:medicine_health | 1.000 | 1260 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `熱` | ねつ | 0.146 | 0.146 | topic_hint:medicine_health | 1.000 | 1136 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `鼻` | はな | 0.093 | 0.093 | topic_hint:medicine_health | 1.000 | 1388 -> 52 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 57 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `背中` | せなか | 0.147 | 0.147 | topic_hint:medicine_health | 1.000 | 1419 -> 61 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 1.000 | 1498 -> 83 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `風邪` | かぜ | 0.100 | 0.100 | topic_hint:medicine_health | 1.000 | 2191 -> 86 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 1.000 | 1835 -> 99 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_p25`

Medicine/health preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `目` | め | 0.020 | 0.020 | topic_hint:medicine_health | 1.000 | 33 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `顔` | かお | 0.169 | 0.169 | topic_hint:medicine_health | 1.000 | 56 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `口` | くち | 0.054 | 0.054 | topic_hint:medicine_health | 1.000 | 147 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `病院` | びょういん | 0.034 | 0.034 | topic_hint:medicine_health | 1.000 | 263 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `足` | あし | 0.058 | 0.058 | topic_hint:medicine_health | 1.000 | 288 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 1.000 | 513 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `病気` | びょうき | 0.062 | 0.062 | topic_hint:medicine_health | 1.000 | 534 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 1.000 | 737 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 744 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `指` | ゆび | 0.149 | 0.149 | topic_hint:medicine_health | 1.000 | 763 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `血` | ち | 0.150 | 0.150 | topic_hint:medicine_health | 1.000 | 829 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `熱` | ねつ | 0.146 | 0.146 | topic_hint:medicine_health | 1.000 | 1136 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `医者` | いしゃ | 0.082 | 0.082 | topic_hint:medicine_health | 1.000 | 1260 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `鼻` | はな | 0.093 | 0.093 | topic_hint:medicine_health | 1.000 | 1388 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `背中` | せなか | 0.147 | 0.147 | topic_hint:medicine_health | 1.000 | 1419 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `膝` | ひざ | 0.237 | 0.237 | topic_hint:medicine_health | 1.000 | 1498 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `心臓` | しんぞう | 0.252 | 0.252 | topic_hint:medicine_health | 1.000 | 1835 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 1.000 | 1686 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_p45`

Medicine/health preference at intermediate main-use level; expected to show clear topic movement.

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

### `medicine_health_p65`

Medicine/health preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `爪` | つめ | 0.299 | 0.299 | topic_hint:medicine_health | 0.674 | 2636 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `皮膚` | ひふ | 0.293 | 0.293 | topic_hint:medicine_health | 0.634 | 1686 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `medicine_health_p85`

Medicine/health preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['medicine_health']` applied_seed_count=`27`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `music_media_entertainment_p10`

Music/media/entertainment preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:music_media_entertainment | 1.000 | 107 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `テレビ` | てれび | 0.117 | 0.117 | topic_hint:music_media_entertainment | 1.000 | 258 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `映画` | えいが | 0.051 | 0.051 | topic_hint:music_media_entertainment | 1.000 | 295 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `新聞` | しんぶん | 0.046 | 0.046 | topic_hint:music_media_entertainment | 1.000 | 303 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `音楽` | おんがく | 0.060 | 0.060 | topic_hint:music_media_entertainment | 1.000 | 416 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `放送` | ほうそう | 0.130 | 0.130 | topic_hint:music_media_entertainment | 1.000 | 426 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `歌` | うた | 0.063 | 0.063 | topic_hint:music_media_entertainment | 1.000 | 546 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `監督` | かんとく | 0.207 | 0.207 | topic_hint:music_media_entertainment | 1.000 | 481 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `番組` | ばんぐみ | 0.136 | 0.136 | topic_hint:music_media_entertainment | 1.000 | 834 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `雑誌` | ざっし | 0.078 | 0.078 | topic_hint:music_media_entertainment | 1.000 | 984 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ニュース` | にゅーす | 0.066 | 0.066 | topic_hint:music_media_entertainment | 1.000 | 1166 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `広告` | こうこく | 0.240 | 0.240 | topic_hint:music_media_entertainment | 1.000 | 1197 -> 60 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ラジオ` | らじお | 0.080 | 0.080 | topic_hint:music_media_entertainment | 1.000 | 1785 -> 62 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:music_media_entertainment | 1.000 | 1711 -> 64 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `演奏` | えんそう | 0.245 | 0.245 | topic_hint:music_media_entertainment | 1.000 | 1460 -> 82 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:music_media_entertainment | 1.000 | 2120 -> 89 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ギター` | ぎたー | 0.102 | 0.102 | topic_hint:music_media_entertainment | 1.000 | 3547 -> 150 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `歌手` | かしゅ | 0.121 | 0.121 | topic_hint:music_media_entertainment | 1.000 | 3589 -> 165 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:music_media_entertainment | 1.000 | 2848 -> 166 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `動画` | どうが | 0.200 | 0.200 | topic_hint:music_media_entertainment | 1.000 | 3380 -> 190 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `music_media_entertainment_p25`

Music/media/entertainment preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:music_media_entertainment | 1.000 | 107 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `テレビ` | てれび | 0.117 | 0.117 | topic_hint:music_media_entertainment | 1.000 | 258 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `映画` | えいが | 0.051 | 0.051 | topic_hint:music_media_entertainment | 1.000 | 295 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `新聞` | しんぶん | 0.046 | 0.046 | topic_hint:music_media_entertainment | 1.000 | 303 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `音楽` | おんがく | 0.060 | 0.060 | topic_hint:music_media_entertainment | 1.000 | 416 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `放送` | ほうそう | 0.130 | 0.130 | topic_hint:music_media_entertainment | 1.000 | 426 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `監督` | かんとく | 0.207 | 0.207 | topic_hint:music_media_entertainment | 1.000 | 481 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `歌` | うた | 0.063 | 0.063 | topic_hint:music_media_entertainment | 1.000 | 546 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `番組` | ばんぐみ | 0.136 | 0.136 | topic_hint:music_media_entertainment | 1.000 | 834 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `雑誌` | ざっし | 0.078 | 0.078 | topic_hint:music_media_entertainment | 1.000 | 984 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ニュース` | にゅーす | 0.066 | 0.066 | topic_hint:music_media_entertainment | 1.000 | 1166 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `広告` | こうこく | 0.240 | 0.240 | topic_hint:music_media_entertainment | 1.000 | 1197 -> 28 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `演奏` | えんそう | 0.245 | 0.245 | topic_hint:music_media_entertainment | 1.000 | 1460 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:music_media_entertainment | 1.000 | 1711 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ラジオ` | らじお | 0.080 | 0.080 | topic_hint:music_media_entertainment | 1.000 | 1785 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:music_media_entertainment | 1.000 | 2120 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:music_media_entertainment | 1.000 | 2848 -> 66 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `動画` | どうが | 0.200 | 0.200 | topic_hint:music_media_entertainment | 1.000 | 3380 -> 96 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ギター` | ぎたー | 0.102 | 0.102 | topic_hint:music_media_entertainment | 1.000 | 3547 -> 103 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `音声` | おんせい | 0.300 | 0.300 | topic_hint:music_media_entertainment | 1.000 | 3181 -> 104 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `music_media_entertainment_p45`

Music/media/entertainment preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `監督` | かんとく | 0.207 | 0.207 | topic_hint:music_media_entertainment | 1.000 | 481 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `広告` | こうこく | 0.240 | 0.240 | topic_hint:music_media_entertainment | 1.000 | 1197 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `演奏` | えんそう | 0.245 | 0.245 | topic_hint:music_media_entertainment | 1.000 | 1460 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `放送` | ほうそう | 0.130 | 0.130 | topic_hint:music_media_entertainment | 0.860 | 426 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ピアノ` | ぴあの | 0.166 | 0.166 | topic_hint:music_media_entertainment | 0.988 | 2120 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `番組` | ばんぐみ | 0.136 | 0.136 | topic_hint:music_media_entertainment | 0.891 | 834 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `アニメ` | あにめ | 0.224 | 0.224 | topic_hint:music_media_entertainment | 1.000 | 2848 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `テレビ` | てれび | 0.117 | 0.117 | topic_hint:music_media_entertainment | 0.791 | 258 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `音声` | おんせい | 0.300 | 0.300 | topic_hint:music_media_entertainment | 1.000 | 3181 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:music_media_entertainment | 1.000 | 3280 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `動画` | どうが | 0.200 | 0.200 | topic_hint:music_media_entertainment | 1.000 | 3380 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `太鼓` | たいこ | 0.352 | 0.352 | topic_hint:music_media_entertainment | 1.000 | 3884 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `合唱` | がっしょう | 0.397 | 0.397 | topic_hint:music_media_entertainment | 1.000 | 5149 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ドラム` | どらむ | 0.314 | 0.314 | topic_hint:music_media_entertainment | 1.000 | 5915 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `漫画` | まんが | 0.123 | 0.123 | topic_hint:music_media_entertainment | 0.825 | 1711 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `歌手` | かしゅ | 0.121 | 0.121 | topic_hint:music_media_entertainment | 0.811 | 3589 -> 54 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `music_media_entertainment_p65`

Music/media/entertainment preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `太鼓` | たいこ | 0.352 | 0.352 | topic_hint:music_media_entertainment | 0.955 | 3884 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `合唱` | がっしょう | 0.397 | 0.397 | topic_hint:music_media_entertainment | 1.000 | 5149 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:music_media_entertainment | 0.850 | 3280 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ドラム` | どらむ | 0.314 | 0.314 | topic_hint:music_media_entertainment | 0.767 | 5915 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `音声` | おんせい | 0.300 | 0.300 | topic_hint:music_media_entertainment | 0.684 | 3181 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `music_media_entertainment_p85`

Music/media/entertainment preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment']` applied_seed_count=`26`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `plants_nature_p10`

Plants/nature preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `花` | はな | 0.060 | 0.060 | topic_hint:plants_nature | 1.000 | 225 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `雨` | あめ | 0.068 | 0.068 | topic_hint:plants_nature | 1.000 | 637 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `地震` | じしん | 0.140 | 0.140 | topic_hint:plants_nature | 1.000 | 909 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `森` | もり | 0.145 | 0.145 | topic_hint:plants_nature | 1.000 | 1002 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `季節` | きせつ | 0.144 | 0.144 | topic_hint:plants_nature | 1.000 | 1334 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `天気` | てんき | 0.099 | 0.099 | topic_hint:plants_nature | 1.000 | 1575 -> 49 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `雲` | くも | 0.153 | 0.153 | topic_hint:plants_nature | 1.000 | 1530 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `台風` | たいふう | 0.149 | 0.149 | topic_hint:plants_nature | 1.000 | 2893 -> 123 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `気温` | きおん | 0.256 | 0.256 | topic_hint:plants_nature | 1.000 | 2466 -> 142 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:plants_nature | 1.000 | 2445 -> 164 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `豆` | まめ | 0.250 | 0.250 | topic_hint:plants_nature | 1.000 | 2994 -> 182 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `葡萄` | ぶどう | 0.327 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `火山` | かざん | 0.336 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `杉` | すぎ | 0.356 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 15 | `洪水` | こうずい | 0.365 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `蜜柑` | みかん | 0.351 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `plants_nature_p25`

Plants/nature preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `花` | はな | 0.060 | 0.060 | topic_hint:plants_nature | 1.000 | 225 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `雨` | あめ | 0.068 | 0.068 | topic_hint:plants_nature | 1.000 | 637 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `地震` | じしん | 0.140 | 0.140 | topic_hint:plants_nature | 1.000 | 909 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `森` | もり | 0.145 | 0.145 | topic_hint:plants_nature | 1.000 | 1002 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `季節` | きせつ | 0.144 | 0.144 | topic_hint:plants_nature | 1.000 | 1334 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `雲` | くも | 0.153 | 0.153 | topic_hint:plants_nature | 1.000 | 1530 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `天気` | てんき | 0.099 | 0.099 | topic_hint:plants_nature | 1.000 | 1575 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `気温` | きおん | 0.256 | 0.256 | topic_hint:plants_nature | 1.000 | 2466 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:plants_nature | 1.000 | 2445 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `台風` | たいふう | 0.149 | 0.149 | topic_hint:plants_nature | 1.000 | 2893 -> 63 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `豆` | まめ | 0.250 | 0.250 | topic_hint:plants_nature | 1.000 | 2994 -> 71 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `葡萄` | ぶどう | 0.327 | 0.327 | topic_hint:plants_nature | 1.000 | 3069 -> 98 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `火山` | かざん | 0.336 | 0.336 | topic_hint:plants_nature | 1.000 | 3311 -> 120 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `杉` | すぎ | 0.356 | 0.356 | topic_hint:plants_nature | 1.000 | 3920 -> 162 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `洪水` | こうずい | 0.365 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `蜜柑` | みかん | 0.351 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `苺` | いちご | 0.383 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `麦` | むぎ | 0.375 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 2 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `plants_nature_p45`

Plants/nature preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `森` | もり | 0.145 | 0.145 | topic_hint:plants_nature | 0.928 | 1002 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `雲` | くも | 0.153 | 0.153 | topic_hint:plants_nature | 0.958 | 1530 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `地震` | じしん | 0.140 | 0.140 | topic_hint:plants_nature | 0.907 | 909 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:plants_nature | 1.000 | 2445 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `気温` | きおん | 0.256 | 0.256 | topic_hint:plants_nature | 1.000 | 2466 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `季節` | きせつ | 0.144 | 0.144 | topic_hint:plants_nature | 0.927 | 1334 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `豆` | まめ | 0.250 | 0.250 | topic_hint:plants_nature | 1.000 | 2994 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `葡萄` | ぶどう | 0.327 | 0.327 | topic_hint:plants_nature | 1.000 | 3069 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `火山` | かざん | 0.336 | 0.336 | topic_hint:plants_nature | 1.000 | 3311 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `杉` | すぎ | 0.356 | 0.356 | topic_hint:plants_nature | 1.000 | 3920 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `台風` | たいふう | 0.149 | 0.149 | topic_hint:plants_nature | 0.944 | 2893 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `苺` | いちご | 0.383 | 0.383 | topic_hint:plants_nature | 1.000 | 4344 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `洪水` | こうずい | 0.365 | 0.365 | topic_hint:plants_nature | 1.000 | 4401 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `蜜柑` | みかん | 0.351 | 0.351 | topic_hint:plants_nature | 1.000 | 4589 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `麦` | むぎ | 0.375 | 0.375 | topic_hint:plants_nature | 1.000 | 5265 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `津波` | つなみ | 0.373 | 0.373 | topic_hint:plants_nature | 1.000 | 6561 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `檜` | ひのき | 0.584 | 0.584 | topic_hint:plants_nature | 1.000 | 6841 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `天気` | てんき | 0.099 | 0.099 | topic_hint:plants_nature | 0.672 | 1575 -> 172 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `plants_nature_p65`

Plants/nature preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `苺` | いちご | 0.383 | 0.383 | topic_hint:plants_nature | 1.000 | 4344 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `洪水` | こうずい | 0.365 | 0.365 | topic_hint:plants_nature | 0.987 | 4401 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `杉` | すぎ | 0.356 | 0.356 | topic_hint:plants_nature | 0.966 | 3920 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `麦` | むぎ | 0.375 | 0.375 | topic_hint:plants_nature | 0.999 | 5265 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `蜜柑` | みかん | 0.351 | 0.351 | topic_hint:plants_nature | 0.952 | 4589 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `火山` | かざん | 0.336 | 0.336 | topic_hint:plants_nature | 0.889 | 3311 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `津波` | つなみ | 0.373 | 0.373 | topic_hint:plants_nature | 0.997 | 6561 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `檜` | ひのき | 0.584 | 0.584 | topic_hint:plants_nature | 1.000 | 6841 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `葡萄` | ぶどう | 0.327 | 0.327 | topic_hint:plants_nature | 0.844 | 3069 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:plants_nature | 0.708 | 2445 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `plants_nature_p85`

Plants/nature preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['plants_nature']` applied_seed_count=`21`

Active topic support:

- `plants_nature` candidates=21 mass=5.995802 scarcity=eligible examples=花, 雨, 地震, 森, 季節

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `檜` | ひのき | 0.584 | 0.584 | topic_hint:plants_nature | 1.000 | 6841 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `science_math_p10`

Science/math preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `研究` | けんきゅう | 0.125 | 0.125 | topic_hint:science_math | 1.000 | 54 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `科学` | かがく | 0.129 | 0.129 | topic_hint:science_math | 1.000 | 374 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `電気` | でんき | 0.060 | 0.060 | topic_hint:science_math | 1.000 | 632 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `計算` | けいさん | 0.198 | 0.198 | topic_hint:science_math | 1.000 | 460 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 1.000 | 758 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 1.000 | 802 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 1.000 | 1058 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 1.000 | 1077 -> 52 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 54 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 1.000 | 1583 -> 78 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `数学` | すうがく | 0.155 | 0.155 | topic_hint:science_math | 1.000 | 2301 -> 89 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 1.000 | 2269 -> 126 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 145 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `地理` | ちり | 0.157 | 0.157 | topic_hint:science_math | 1.000 | 3532 -> 176 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `三角` | さんかく | 0.303 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 6 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |

### `science_math_p25`

Science/math preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `研究` | けんきゅう | 0.125 | 0.125 | topic_hint:science_math | 1.000 | 54 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `科学` | かがく | 0.129 | 0.129 | topic_hint:science_math | 1.000 | 374 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `計算` | けいさん | 0.198 | 0.198 | topic_hint:science_math | 1.000 | 460 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `電気` | でんき | 0.060 | 0.060 | topic_hint:science_math | 1.000 | 632 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 1.000 | 758 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 1.000 | 802 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 1.000 | 1058 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 1.000 | 978 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `化学` | かがく | 0.243 | 0.243 | topic_hint:science_math | 1.000 | 1077 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `温度` | おんど | 0.235 | 0.235 | topic_hint:science_math | 1.000 | 1583 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `物理` | ぶつり | 0.254 | 0.254 | topic_hint:science_math | 1.000 | 2269 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `数学` | すうがく | 0.155 | 0.155 | topic_hint:science_math | 1.000 | 2301 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 1.000 | 2311 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 1.000 | 2932 -> 87 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `地理` | ちり | 0.157 | 0.157 | topic_hint:science_math | 1.000 | 3532 -> 96 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 3 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 18 | `無い` | ない | 0.265 | 0.265 |  | 1.000 | 8 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `よう` | よう | 0.123 | 0.123 |  | 1.000 | 13 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `思う` | おもう | 0.124 | 0.124 |  | 1.000 | 135 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `science_math_p45`

Science/math preference at intermediate main-use level; expected to show clear topic movement.

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

### `science_math_p65`

Science/math preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `三角` | さんかく | 0.303 | 0.303 | topic_hint:science_math | 0.699 | 2932 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `理論` | りろん | 0.279 | 0.279 | topic_hint:science_math | 0.541 | 978 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `公式` | こうしき | 0.284 | 0.284 | topic_hint:science_math | 0.576 | 2311 -> 79 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `science_math_p85`

Science/math preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['science_math']` applied_seed_count=`15`

Active topic support:

- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `shopping_money_p10`

Shopping/money preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `高い` | たかい | 0.014 | 0.014 | topic_hint:shopping_money | 1.000 | 235 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `買う` | かう | 0.027 | 0.027 | topic_hint:shopping_money | 1.000 | 1156 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `店` | みせ | 0.043 | 0.043 | topic_hint:shopping_money | 1.000 | 241 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `商品` | しょうひん | 0.179 | 0.179 | topic_hint:shopping_money | 1.000 | 239 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `価格` | かかく | 0.183 | 0.183 | topic_hint:shopping_money | 1.000 | 268 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `売る` | うる | 0.063 | 0.063 | topic_hint:shopping_money | 1.000 | 2563 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `安い` | やすい | 0.061 | 0.061 | topic_hint:shopping_money | 1.000 | 1406 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `払う` | はらう | 0.137 | 0.137 | topic_hint:shopping_money | 1.000 | 2821 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `無料` | むりょう | 0.204 | 0.204 | topic_hint:shopping_money | 1.000 | 608 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `予約` | よやく | 0.144 | 0.144 | topic_hint:shopping_money | 1.000 | 1024 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `会計` | かいけい | 0.243 | 0.243 | topic_hint:shopping_money | 1.000 | 867 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `料金` | りょうきん | 0.239 | 0.239 | topic_hint:shopping_money | 1.000 | 945 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `買い物` | かいもの | 0.069 | 0.069 | topic_hint:shopping_money | 1.000 | 1615 -> 57 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:shopping_money | 1.000 | 1347 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `値段` | ねだん | 0.142 | 0.142 | topic_hint:shopping_money | 1.000 | 1446 -> 59 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 1.000 | 941 -> 63 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `支払う` | しはらう | 0.242 | 0.242 | topic_hint:shopping_money | 1.000 | 3905 -> 71 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `円` | えん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 1897 -> 102 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `商店` | しょうてん | 0.309 | 0.309 | topic_hint:shopping_money | 1.000 | 2056 -> 147 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `現金` | げんきん | 0.252 | 0.252 | topic_hint:shopping_money | 1.000 | 2459 -> 152 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `shopping_money_p25`

Shopping/money preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `高い` | たかい | 0.014 | 0.014 | topic_hint:shopping_money | 1.000 | 235 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `買う` | かう | 0.027 | 0.027 | topic_hint:shopping_money | 1.000 | 1156 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `商品` | しょうひん | 0.179 | 0.179 | topic_hint:shopping_money | 1.000 | 239 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `店` | みせ | 0.043 | 0.043 | topic_hint:shopping_money | 1.000 | 241 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `価格` | かかく | 0.183 | 0.183 | topic_hint:shopping_money | 1.000 | 268 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `売る` | うる | 0.063 | 0.063 | topic_hint:shopping_money | 1.000 | 2563 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `無料` | むりょう | 0.204 | 0.204 | topic_hint:shopping_money | 1.000 | 608 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `安い` | やすい | 0.061 | 0.061 | topic_hint:shopping_money | 1.000 | 1406 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `払う` | はらう | 0.137 | 0.137 | topic_hint:shopping_money | 1.000 | 2821 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `会計` | かいけい | 0.243 | 0.243 | topic_hint:shopping_money | 1.000 | 867 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `料金` | りょうきん | 0.239 | 0.239 | topic_hint:shopping_money | 1.000 | 945 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `予約` | よやく | 0.144 | 0.144 | topic_hint:shopping_money | 1.000 | 1024 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 1.000 | 941 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `支払う` | しはらう | 0.242 | 0.242 | topic_hint:shopping_money | 1.000 | 3905 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:shopping_money | 1.000 | 1347 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `値段` | ねだん | 0.142 | 0.142 | topic_hint:shopping_money | 1.000 | 1446 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `買い物` | かいもの | 0.069 | 0.069 | topic_hint:shopping_money | 1.000 | 1615 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `円` | えん | 0.250 | 0.250 | topic_hint:shopping_money | 1.000 | 1897 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `商店` | しょうてん | 0.309 | 0.309 | topic_hint:shopping_money | 1.000 | 2056 -> 52 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `現金` | げんきん | 0.252 | 0.252 | topic_hint:shopping_money | 1.000 | 2459 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `shopping_money_p45`

Shopping/money preference at intermediate main-use level; expected to show clear topic movement.

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

### `shopping_money_p65`

Shopping/money preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 0.714 | 941 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `商店` | しょうてん | 0.309 | 0.309 | topic_hint:shopping_money | 0.742 | 2056 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `コンビニ` | こんびに | 0.280 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 4 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `shopping_money_p85`

Shopping/money preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['shopping_money']` applied_seed_count=`27`

Active topic support:

- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p10`

Sports/fitness preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 1.000 | 158 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `野球` | やきゅう | 0.241 | 0.241 | topic_hint:sports_fitness | 1.000 | 1243 -> 44 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `ゴルフ` | ごるふ | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 1881 -> 56 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `サッカー` | さっかー | 0.189 | 0.189 | topic_hint:sports_fitness | 1.000 | 1945 -> 64 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 2457 -> 73 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `スキー` | すきー | 0.172 | 0.172 | topic_hint:sports_fitness | 1.000 | 2514 -> 81 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `テニス` | てにす | 0.120 | 0.120 | topic_hint:sports_fitness | 1.000 | 3422 -> 113 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `体操` | たいそう | 0.339 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 9 | `陸上` | りくじょう | 0.352 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 10 | `柔道` | じゅうどう | 0.137 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 11 | `水泳` | すいえい | 0.155 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 12 | `相撲` | すもう | 0.350 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `マラソン` | まらそん | 0.306 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `する` |  | - | 0.005 |  | 1.000 | 9 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `いる` | いる | 0.002 | 0.002 |  | 1.000 | 22 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ある` | ある | 0.120 | 0.120 |  | 1.000 | 26 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `言う` | いう | 0.002 | 0.002 |  | 1.000 | 34 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `こと` | こと | 0.120 | 0.120 |  | 1.000 | 1 -> 5 | Still supported by coverage_gain and proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 19 | `なる` | なる | 0.002 | 0.002 |  | 1.000 | 47 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `その` |  | - | 0.040 |  | 1.000 | 2189 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p25`

Sports/fitness preference at upper-beginner level; should surface only approachable topic words.

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

### `sports_fitness_p45`

Sports/fitness preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 1.000 | 158 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `野球` | やきゅう | 0.241 | 0.241 | topic_hint:sports_fitness | 1.000 | 1243 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `サッカー` | さっかー | 0.189 | 0.189 | topic_hint:sports_fitness | 1.000 | 1945 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ゴルフ` | ごるふ | 0.172 | 0.172 | topic_hint:sports_fitness | 0.996 | 1881 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `スキー` | すきー | 0.172 | 0.172 | topic_hint:sports_fitness | 0.996 | 2514 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `体操` | たいそう | 0.339 | 0.339 | topic_hint:sports_fitness | 1.000 | 3208 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `陸上` | りくじょう | 0.352 | 0.352 | topic_hint:sports_fitness | 1.000 | 3777 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `相撲` | すもう | 0.350 | 0.350 | topic_hint:sports_fitness | 1.000 | 4243 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `マラソン` | まらそん | 0.306 | 0.306 | topic_hint:sports_fitness | 1.000 | 5377 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `水泳` | すいえい | 0.155 | 0.155 | topic_hint:sports_fitness | 0.964 | 5836 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `スケート` | すけーと | 0.260 | 0.260 | topic_hint:sports_fitness | 1.000 | 7266 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ダンス` | だんす | 0.120 | 0.120 | topic_hint:sports_fitness | 0.807 | 2457 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `柔道` | じゅうどう | 0.137 | 0.137 | topic_hint:sports_fitness | 0.895 | 5912 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `テニス` | てにす | 0.120 | 0.120 | topic_hint:sports_fitness | 0.806 | 3422 -> 41 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `無い` | ない | 0.265 | 0.265 |  | 0.929 | 8 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `御座る` | ござる | 0.493 | 0.493 |  | 1.000 | 634 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `良く` | よく | 0.298 | 0.298 |  | 1.000 | 2160 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `矢張り` | やはり | 0.317 | 0.317 |  | 1.000 | 2477 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `共` | とも | 0.322 | 0.322 |  | 1.000 | 84 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `其々` | それぞれ | 0.327 | 0.327 |  | 1.000 | 160 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p65`

Sports/fitness preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `陸上` | りくじょう | 0.352 | 0.352 | topic_hint:sports_fitness | 0.955 | 3777 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `相撲` | すもう | 0.350 | 0.350 | topic_hint:sports_fitness | 0.949 | 4243 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `体操` | たいそう | 0.339 | 0.339 | topic_hint:sports_fitness | 0.904 | 3208 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `センター` | せんたー | 0.299 | 0.299 | topic_hint:sports_fitness | 0.677 | 158 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `マラソン` | まらそん | 0.306 | 0.306 | topic_hint:sports_fitness | 0.717 | 5377 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `sports_fitness_p85`

Sports/fitness preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['sports_fitness']` applied_seed_count=`14`

Active topic support:

- `sports_fitness` candidates=14 mass=3.83668 scarcity=eligible examples=センター, 野球, ゴルフ, サッカー, ダンス

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `travel_places_transport_p10`

Travel/places/transport preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['travel_places_transport']` applied_seed_count=`43`

Active topic support:

- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `会社` | かいしゃ | 0.016 | 0.016 | topic_hint:travel_places_transport | 1.000 | 52 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `学校` | がっこう | 0.016 | 0.016 | topic_hint:travel_places_transport | 1.000 | 63 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `車` | くるま | 0.036 | 0.036 | topic_hint:travel_places_transport | 1.000 | 146 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `日本` | にっぽん | 0.124 | 0.124 | topic_hint:travel_places_transport | 1.000 | 10 -> 11 | Still supported by coverage_gain and topic_affinity, proficiency_fit, but moved down because other items received stronger overall profile lift. |
| 5 | `店` | みせ | 0.043 | 0.043 | topic_hint:travel_places_transport | 1.000 | 241 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `駅` | えき | 0.048 | 0.048 | topic_hint:travel_places_transport | 1.000 | 256 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `病院` | びょういん | 0.034 | 0.034 | topic_hint:travel_places_transport | 1.000 | 263 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `銀行` | ぎんこう | 0.053 | 0.053 | topic_hint:travel_places_transport | 1.000 | 309 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ホテル` | ほてる | 0.055 | 0.055 | topic_hint:travel_places_transport | 1.000 | 458 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `旅行` | りょこう | 0.057 | 0.057 | topic_hint:travel_places_transport | 1.000 | 531 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `道路` | どうろ | 0.200 | 0.200 | topic_hint:travel_places_transport | 1.000 | 375 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `バス` | ばす | 0.118 | 0.118 | topic_hint:travel_places_transport | 1.000 | 622 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `会場` | かいじょう | 0.146 | 0.146 | topic_hint:travel_places_transport | 1.000 | 739 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `船` | ふね | 0.136 | 0.136 | topic_hint:travel_places_transport | 1.000 | 826 -> 42 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `観光` | かんこう | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 678 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `アメリカ` | あめりか | 0.123 | 0.123 | topic_hint:travel_places_transport | 1.000 | 97 -> 46 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `電車` | でんしゃ | 0.078 | 0.078 | topic_hint:travel_places_transport | 1.000 | 1244 -> 52 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `空港` | くうこう | 0.140 | 0.140 | topic_hint:travel_places_transport | 1.000 | 1178 -> 55 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `橋` | はし | 0.089 | 0.089 | topic_hint:travel_places_transport | 1.000 | 1397 -> 56 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:travel_places_transport | 1.000 | 1298 -> 60 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `travel_places_transport_p25`

Travel/places/transport preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['travel_places_transport']` applied_seed_count=`43`

Active topic support:

- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `会社` | かいしゃ | 0.016 | 0.016 | topic_hint:travel_places_transport | 1.000 | 52 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `学校` | がっこう | 0.016 | 0.016 | topic_hint:travel_places_transport | 1.000 | 63 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `車` | くるま | 0.036 | 0.036 | topic_hint:travel_places_transport | 1.000 | 146 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `日本` | にっぽん | 0.124 | 0.124 | topic_hint:travel_places_transport | 1.000 | 10 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `店` | みせ | 0.043 | 0.043 | topic_hint:travel_places_transport | 1.000 | 241 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `駅` | えき | 0.048 | 0.048 | topic_hint:travel_places_transport | 1.000 | 256 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `病院` | びょういん | 0.034 | 0.034 | topic_hint:travel_places_transport | 1.000 | 263 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `銀行` | ぎんこう | 0.053 | 0.053 | topic_hint:travel_places_transport | 1.000 | 309 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `道路` | どうろ | 0.200 | 0.200 | topic_hint:travel_places_transport | 1.000 | 375 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ホテル` | ほてる | 0.055 | 0.055 | topic_hint:travel_places_transport | 1.000 | 458 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `旅行` | りょこう | 0.057 | 0.057 | topic_hint:travel_places_transport | 1.000 | 531 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `バス` | ばす | 0.118 | 0.118 | topic_hint:travel_places_transport | 1.000 | 622 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `観光` | かんこう | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 678 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `会場` | かいじょう | 0.146 | 0.146 | topic_hint:travel_places_transport | 1.000 | 739 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `船` | ふね | 0.136 | 0.136 | topic_hint:travel_places_transport | 1.000 | 826 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `アメリカ` | あめりか | 0.123 | 0.123 | topic_hint:travel_places_transport | 1.000 | 97 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `空港` | くうこう | 0.140 | 0.140 | topic_hint:travel_places_transport | 1.000 | 1178 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `電車` | でんしゃ | 0.078 | 0.078 | topic_hint:travel_places_transport | 1.000 | 1244 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:travel_places_transport | 1.000 | 1298 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:travel_places_transport | 1.000 | 1347 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `travel_places_transport_p45`

Travel/places/transport preference at intermediate main-use level; expected to show clear topic movement.

- overlay: status=`active` application=`applied` active_topics=`['travel_places_transport']` applied_seed_count=`43`

Active topic support:

- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `道路` | どうろ | 0.200 | 0.200 | topic_hint:travel_places_transport | 1.000 | 375 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `観光` | かんこう | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 678 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `スーパー` | すーぱー | 0.167 | 0.167 | topic_hint:travel_places_transport | 0.990 | 1347 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `会場` | かいじょう | 0.146 | 0.146 | topic_hint:travel_places_transport | 0.934 | 739 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `日本` | にっぽん | 0.124 | 0.124 | topic_hint:travel_places_transport | 0.830 | 10 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `列車` | れっしゃ | 0.256 | 0.256 | topic_hint:travel_places_transport | 1.000 | 1728 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `バイク` | ばいく | 0.207 | 0.207 | topic_hint:travel_places_transport | 1.000 | 2144 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `教会` | きょうかい | 0.154 | 0.154 | topic_hint:travel_places_transport | 0.959 | 1527 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `信号` | しんごう | 0.246 | 0.246 | topic_hint:travel_places_transport | 1.000 | 2181 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `劇場` | げきじょう | 0.245 | 0.245 | topic_hint:travel_places_transport | 1.000 | 2468 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `船` | ふね | 0.136 | 0.136 | topic_hint:travel_places_transport | 0.889 | 826 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `フランス` | ふらんす | 0.167 | 0.167 | topic_hint:travel_places_transport | 0.990 | 430 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `空港` | くうこう | 0.140 | 0.140 | topic_hint:travel_places_transport | 0.908 | 1178 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `韓国` | かんこく | 0.183 | 0.183 | topic_hint:travel_places_transport | 1.000 | 568 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:travel_places_transport | 0.912 | 1298 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ドイツ` | どいつ | 0.168 | 0.168 | topic_hint:travel_places_transport | 0.992 | 536 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `寺` | てら | 0.147 | 0.147 | topic_hint:travel_places_transport | 0.936 | 1689 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `イギリス` | いぎりす | 0.169 | 0.169 | topic_hint:travel_places_transport | 0.992 | 648 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `コンビニ` | こんびに | 0.280 | 0.280 | topic_hint:travel_places_transport | 1.000 | 3569 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `バス` | ばす | 0.118 | 0.118 | topic_hint:travel_places_transport | 0.792 | 622 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `travel_places_transport_p65`

Travel/places/transport preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['travel_places_transport']` applied_seed_count=`43`

Active topic support:

- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `コンビニ` | こんびに | 0.280 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 2 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `えっ` | えっ | 0.559 | 0.559 |  | 1.000 | 7699 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `動産` | どうさん | 0.577 | 0.577 |  | 1.000 | 1415 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `引き続く` | ひきつづく | 0.577 | 0.577 |  | 1.000 | 4131 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `主な` | おもな | 0.577 | 0.577 |  | 1.000 | 7866 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `存ずる` | ぞんずる | 0.523 | 0.523 |  | 1.000 | 4343 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `travel_places_transport_p85`

Travel/places/transport preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['travel_places_transport']` applied_seed_count=`43`

Active topic support:

- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_p10`

Work/office preference at beginner stress level; topic preference must not overpower readiness.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `会社` | かいしゃ | 0.016 | 0.016 | topic_hint:work_office | 1.000 | 52 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `仕事` | しごと | 0.023 | 0.023 | topic_hint:work_office | 1.000 | 65 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `働く` | はたらく | 0.052 | 0.052 | topic_hint:work_office | 1.000 | 1885 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 1.000 | 242 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `予定` | よてい | 0.130 | 0.130 | topic_hint:work_office | 1.000 | 322 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 1.000 | 265 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `連絡` | れんらく | 0.135 | 0.135 | topic_hint:work_office | 1.000 | 373 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `会議` | かいぎ | 0.129 | 0.129 | topic_hint:work_office | 1.000 | 387 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 1.000 | 301 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 1.000 | 321 -> 26 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `社長` | しゃちょう | 0.131 | 0.131 | topic_hint:work_office | 1.000 | 753 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 1.000 | 598 -> 38 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `書類` | しょるい | 0.250 | 0.250 | topic_hint:work_office | 1.000 | 1245 -> 67 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 68 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 1.000 | 1426 -> 87 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `上司` | じょうし | 0.306 | 0.306 | topic_hint:work_office | 1.000 | 2049 -> 138 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `給料` | きゅうりょう | 0.256 | 0.256 | topic_hint:work_office | 1.000 | 2424 -> 147 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `部長` | ぶちょう | 0.148 | 0.148 | topic_hint:work_office | 1.000 | 3169 -> 151 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_p25`

Work/office preference at upper-beginner level; should surface only approachable topic words.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `会社` | かいしゃ | 0.016 | 0.016 | topic_hint:work_office | 1.000 | 52 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `仕事` | しごと | 0.023 | 0.023 | topic_hint:work_office | 1.000 | 65 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 1.000 | 242 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 1.000 | 265 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `働く` | はたらく | 0.052 | 0.052 | topic_hint:work_office | 1.000 | 1885 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 1.000 | 301 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 1.000 | 321 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `予定` | よてい | 0.130 | 0.130 | topic_hint:work_office | 1.000 | 322 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `連絡` | れんらく | 0.135 | 0.135 | topic_hint:work_office | 1.000 | 373 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `会議` | かいぎ | 0.129 | 0.129 | topic_hint:work_office | 1.000 | 387 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `職員` | しょくいん | 0.221 | 0.221 | topic_hint:work_office | 1.000 | 598 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `社長` | しゃちょう | 0.131 | 0.131 | topic_hint:work_office | 1.000 | 753 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `職業` | しょくぎょう | 0.241 | 0.241 | topic_hint:work_office | 1.000 | 1050 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `書類` | しょるい | 0.250 | 0.250 | topic_hint:work_office | 1.000 | 1245 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 1.000 | 1122 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 1.000 | 1426 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `上司` | じょうし | 0.306 | 0.306 | topic_hint:work_office | 1.000 | 2049 -> 50 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `給料` | きゅうりょう | 0.256 | 0.256 | topic_hint:work_office | 1.000 | 2424 -> 54 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `役員` | やくいん | 0.329 | 0.329 | topic_hint:work_office | 1.000 | 2114 -> 58 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_p45`

Work/office preference at intermediate main-use level; expected to show clear topic movement.

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

### `work_office_p65`

Work/office preference at N1-ish/post-pedagogical transition; should expose more specialized topic words.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `出勤` | しゅっきん | 0.363 | 0.363 | topic_hint:work_office | 0.983 | 4112 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `残業` | ざんぎょう | 0.366 | 0.366 | topic_hint:work_office | 0.988 | 4777 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `出張` | しゅっちょう | 0.335 | 0.335 | topic_hint:work_office | 0.884 | 2677 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `役員` | やくいん | 0.329 | 0.329 | topic_hint:work_office | 0.858 | 2114 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `商標` | しょうひょう | 0.406 | 0.406 | topic_hint:work_office | 1.000 | 5782 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `部下` | ぶか | 0.317 | 0.317 | topic_hint:work_office | 0.787 | 2312 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `面接` | めんせつ | 0.318 | 0.318 | topic_hint:work_office | 0.791 | 2542 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `上司` | じょうし | 0.306 | 0.306 | topic_hint:work_office | 0.718 | 2049 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `勤務` | きんむ | 0.288 | 0.288 | topic_hint:work_office | 0.604 | 1122 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `職場` | しょくば | 0.286 | 0.286 | topic_hint:work_office | 0.587 | 1426 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `work_office_p85`

Work/office preference at advanced-tail level; should separate useful domain words from recondite leftovers.

- overlay: status=`active` application=`applied` active_topics=`['work_office']` applied_seed_count=`29`

Active topic support:

- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_hard_topics_p10`

Arts/literature plus law/politics at beginner level; adversarial guardrail check for hard topics.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities', 'law_politics_civics']` applied_seed_count=`41`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺
- `law_politics_civics` candidates=20 mass=8.337061 scarcity=eligible examples=社会, 政府, 事件, 国民, 政治

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `社会` | しゃかい | 0.125 | 0.125 | topic_hint:law_politics_civics | 1.000 | 37 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `政府` | せいふ | 0.178 | 0.178 | topic_hint:law_politics_civics | 1.000 | 116 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `事件` | じけん | 0.184 | 0.184 | topic_hint:law_politics_civics | 1.000 | 151 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `本` | ほん | 0.055 | 0.055 | topic_hint:arts_literature_humanities | 1.000 | 224 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `国民` | こくみん | 0.182 | 0.182 | topic_hint:law_politics_civics | 1.000 | 153 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `政治` | せいじ | 0.130 | 0.130 | topic_hint:law_politics_civics | 1.000 | 219 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `歴史` | れきし | 0.133 | 0.133 | topic_hint:arts_literature_humanities | 1.000 | 255 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `法律` | ほうりつ | 0.137 | 0.137 | topic_hint:law_politics_civics | 1.000 | 251 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `警察` | けいさつ | 0.134 | 0.134 | topic_hint:law_politics_civics | 1.000 | 340 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `市民` | しみん | 0.136 | 0.136 | topic_hint:law_politics_civics | 1.000 | 335 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `裁判` | さいばん | 0.207 | 0.207 | topic_hint:law_politics_civics | 1.000 | 361 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `絵` | え | 0.070 | 0.070 | topic_hint:arts_literature_humanities | 1.000 | 595 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `手紙` | てがみ | 0.081 | 0.081 | topic_hint:arts_literature_humanities | 1.000 | 757 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `権利` | けんり | 0.222 | 0.222 | topic_hint:law_politics_civics | 1.000 | 561 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `小説` | しょうせつ | 0.136 | 0.136 | topic_hint:arts_literature_humanities | 1.000 | 837 -> 43 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `義務` | ぎむ | 0.234 | 0.234 | topic_hint:law_politics_civics | 1.000 | 651 -> 45 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `選挙` | せんきょ | 0.214 | 0.214 | topic_hint:law_politics_civics | 1.000 | 777 -> 47 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `文学` | ぶんがく | 0.134 | 0.134 | topic_hint:arts_literature_humanities | 1.000 | 1027 -> 48 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `宗教` | しゅうきょう | 0.228 | 0.228 | topic_hint:arts_literature_humanities | 1.000 | 779 -> 51 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `物語` | ものがたり | 0.221 | 0.221 | topic_hint:arts_literature_humanities | 1.000 | 882 -> 56 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_science_medicine_p20`

Science plus medicine at upper-beginner level; checks whether technical interests back off safely.

- overlay: status=`active` application=`applied` active_topics=`['science_math', 'medicine_health']` applied_seed_count=`42`

Active topic support:

- `medicine_health` candidates=27 mass=10.176543 scarcity=eligible examples=目, 顔, 目, 口, 病院
- `science_math` candidates=15 mass=5.49308 scarcity=eligible examples=研究, 科学, 計算, 電気, 機械

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `目` | め | 0.020 | 0.020 | topic_hint:medicine_health | 1.000 | 33 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `研究` | けんきゅう | 0.125 | 0.125 | topic_hint:science_math | 1.000 | 54 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `顔` | かお | 0.169 | 0.169 | topic_hint:medicine_health | 1.000 | 56 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `口` | くち | 0.054 | 0.054 | topic_hint:medicine_health | 1.000 | 147 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `病院` | びょういん | 0.034 | 0.034 | topic_hint:medicine_health | 1.000 | 263 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `足` | あし | 0.058 | 0.058 | topic_hint:medicine_health | 1.000 | 288 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `科学` | かがく | 0.129 | 0.129 | topic_hint:science_math | 1.000 | 374 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `計算` | けいさん | 0.198 | 0.198 | topic_hint:science_math | 1.000 | 460 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `胸` | むね | 0.204 | 0.204 | topic_hint:medicine_health | 1.000 | 513 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `病気` | びょうき | 0.062 | 0.062 | topic_hint:medicine_health | 1.000 | 534 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `電気` | でんき | 0.060 | 0.060 | topic_hint:science_math | 1.000 | 632 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `指` | ゆび | 0.149 | 0.149 | topic_hint:medicine_health | 1.000 | 763 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `腰` | こし | 0.212 | 0.212 | topic_hint:medicine_health | 1.000 | 737 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `肩` | かた | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 744 -> 32 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `機械` | きかい | 0.216 | 0.216 | topic_hint:science_math | 1.000 | 758 -> 33 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `血` | ち | 0.150 | 0.150 | topic_hint:medicine_health | 1.000 | 829 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `実験` | じっけん | 0.218 | 0.218 | topic_hint:science_math | 1.000 | 802 -> 36 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `脳` | のう | 0.213 | 0.213 | topic_hint:medicine_health | 1.000 | 821 -> 37 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `数字` | すうじ | 0.215 | 0.215 | topic_hint:science_math | 1.000 | 1058 -> 39 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `腹` | はら | 0.229 | 0.229 | topic_hint:medicine_health | 1.000 | 1018 -> 40 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_work_computing_p25`

Work plus computing at upper-beginner level; realistic but potentially sparse early-domain profile.

- overlay: status=`active` application=`applied` active_topics=`['work_office', 'computing_internet']` applied_seed_count=`131`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム
- `work_office` candidates=29 mass=10.592068 scarcity=eligible examples=会社, 仕事, 事務, 報告, 働く

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `会社` | かいしゃ | 0.016 | 0.016 | topic_hint:work_office | 1.000 | 52 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `情報` | じょうほう | 0.169 | 0.169 | topic_hint:computing_internet | 1.000 | 57 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `仕事` | しごと | 0.023 | 0.023 | topic_hint:work_office | 1.000 | 65 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `電話` | でんわ | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 92 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `写真` | しゃしん | 0.025 | 0.025 | topic_hint:computing_internet | 1.000 | 107 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `開発` | かいはつ | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 122 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `システム` | しすてむ | 0.166 | 0.166 | topic_hint:computing_internet | 1.000 | 237 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 1.000 | 242 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `メール` | めーる | 0.168 | 0.168 | topic_hint:computing_internet | 1.000 | 260 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 1.000 | 265 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `処理` | しょり | 0.188 | 0.188 | topic_hint:computing_internet | 1.000 | 269 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 1.000 | 275 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `設定` | せってい | 0.177 | 0.177 | topic_hint:computing_internet | 1.000 | 282 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `働く` | はたらく | 0.052 | 0.052 | topic_hint:work_office | 1.000 | 1885 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `資料` | しりょう | 0.199 | 0.199 | topic_hint:work_office | 1.000 | 301 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `契約` | けいやく | 0.195 | 0.195 | topic_hint:work_office | 1.000 | 321 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `予定` | よてい | 0.130 | 0.130 | topic_hint:work_office | 1.000 | 322 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `データ` | でーた | 0.167 | 0.167 | topic_hint:computing_internet | 1.000 | 331 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `連絡` | れんらく | 0.135 | 0.135 | topic_hint:work_office | 1.000 | 373 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `通信` | つうしん | 0.206 | 0.206 | topic_hint:computing_internet | 1.000 | 386 -> 25 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_arts_games_p45`

Arts/literature plus games at intermediate level; tests heterogeneous topic blending.

- overlay: status=`active` application=`applied` active_topics=`['arts_literature_humanities', 'games']` applied_seed_count=`55`

Active topic support:

- `arts_literature_humanities` candidates=21 mass=7.627901 scarcity=eligible examples=本, 本, 歴史, 絵, 寺
- `games` candidates=34 mass=8.527567 scarcity=eligible examples=レベル, カード, 試合, ゲーム, 大会

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `カード` | かーど | 0.172 | 0.172 | topic_hint:games | 0.996 | 615 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `宗教` | しゅうきょう | 0.228 | 0.228 | topic_hint:arts_literature_humanities | 1.000 | 779 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 0.993 | 743 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `物語` | ものがたり | 0.221 | 0.221 | topic_hint:arts_literature_humanities | 1.000 | 882 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `美術` | びじゅつ | 0.240 | 0.240 | topic_hint:arts_literature_humanities | 1.000 | 992 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `芸術` | げいじゅつ | 0.243 | 0.243 | topic_hint:arts_literature_humanities | 1.000 | 1051 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `歴史` | れきし | 0.133 | 0.133 | topic_hint:arts_literature_humanities | 0.876 | 255 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `哲学` | てつがく | 0.263 | 0.263 | topic_hint:arts_literature_humanities | 1.000 | 1556 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 0.997 | 1551 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `勝負` | しょうぶ | 0.289 | 0.289 | topic_hint:games | 1.000 | 2034 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `ステージ` | すてーじ | 0.212 | 0.212 | topic_hint:games | 1.000 | 2349 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `小説` | しょうせつ | 0.136 | 0.136 | topic_hint:arts_literature_humanities | 0.889 | 837 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `日記` | にっき | 0.150 | 0.150 | topic_hint:arts_literature_humanities | 0.948 | 1690 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `試合` | しあい | 0.132 | 0.132 | topic_hint:games | 0.871 | 727 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ランキング` | らんきんぐ | 0.184 | 0.184 | topic_hint:games | 1.000 | 2708 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `神社` | じんじゃ | 0.141 | 0.141 | topic_hint:arts_literature_humanities | 0.912 | 1298 -> 23 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_entertainment_cluster_p45`

Anime/manga, games, and hobbies at intermediate level; checks distribution across adjacent entertainment topics.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture', 'games', 'hobbies_crafts']` applied_seed_count=`133`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.410732 scarcity=eligible examples=作品, 設定, ファン, 日常, 予約
- `games` candidates=34 mass=8.258756 scarcity=eligible examples=レベル, 試合, ゲーム, 大会, 戦略
- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `作品` | さくひん | 0.181 | 0.181 | topic_hint:anime_manga_pop_culture | 1.000 | 243 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `設定` | せってい | 0.177 | 0.177 | topic_hint:anime_manga_pop_culture | 0.999 | 282 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `撮影` | さつえい | 0.189 | 0.189 | topic_hint:hobbies_crafts | 1.000 | 470 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ブログ` | ぶろぐ | 0.170 | 0.170 | topic_hint:hobbies_crafts | 0.994 | 474 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `レベル` | れべる | 0.413 | 0.413 | topic_hint:games | 1.000 | 597 -> 6 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `カード` | かーど | 0.172 | 0.172 | topic_hint:anime_manga_pop_culture | 0.996 | 615 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `大会` | たいかい | 0.209 | 0.209 | topic_hint:games | 1.000 | 748 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ゲーム` | げーむ | 0.169 | 0.169 | topic_hint:games | 0.993 | 743 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ファン` | ふぁん | 0.411 | 0.411 | topic_hint:anime_manga_pop_culture | 1.000 | 831 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `日常` | にちじょう | 0.222 | 0.222 | topic_hint:anime_manga_pop_culture | 1.000 | 849 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `編集` | へんしゅう | 0.211 | 0.211 | topic_hint:hobbies_crafts | 1.000 | 1006 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `発売` | はつばい | 0.215 | 0.215 | topic_hint:anime_manga_pop_culture | 1.000 | 1079 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `戦略` | せんりゃく | 0.235 | 0.235 | topic_hint:games | 1.000 | 1115 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `イベント` | いべんと | 0.171 | 0.171 | topic_hint:anime_manga_pop_culture | 0.996 | 1291 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `コメント` | こめんと | 0.419 | 0.419 | topic_hint:anime_manga_pop_culture | 1.000 | 1538 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `ルール` | るーる | 0.174 | 0.174 | topic_hint:games | 0.997 | 1551 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `収集` | しゅうしゅう | 0.301 | 0.301 | topic_hint:hobbies_crafts | 1.000 | 1680 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `作戦` | さくせん | 0.285 | 0.285 | topic_hint:games | 1.000 | 1736 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `恋愛` | れんあい | 0.280 | 0.280 | topic_hint:anime_manga_pop_culture | 1.000 | 1822 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `戦闘` | せんとう | 0.234 | 0.234 | topic_hint:anime_manga_pop_culture | 1.000 | 1867 -> 21 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_professional_practical_p50`

Work, computing, and shopping/money at upper-intermediate level; product-like professional profile.

- overlay: status=`active` application=`applied` active_topics=`['work_office', 'computing_internet', 'shopping_money']` applied_seed_count=`158`

Active topic support:

- `computing_internet` candidates=102 mass=31.143727 scarcity=eligible examples=情報, 電話, 写真, 開発, システム
- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店
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
| 8 | `会計` | かいけい | 0.243 | 0.243 | topic_hint:shopping_money | 1.000 | 867 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `機械` | きかい | 0.216 | 0.216 | topic_hint:computing_internet | 0.989 | 758 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `事務` | じむ | 0.190 | 0.190 | topic_hint:work_office | 0.908 | 242 -> 10 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `保存` | ほぞん | 0.212 | 0.212 | topic_hint:computing_internet | 0.981 | 710 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `電子` | でんし | 0.221 | 0.221 | topic_hint:computing_internet | 0.995 | 835 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `実行` | じっこう | 0.217 | 0.217 | topic_hint:computing_internet | 0.991 | 806 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `債権` | さいけん | 0.305 | 0.305 | topic_hint:shopping_money | 1.000 | 941 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `社員` | しゃいん | 0.230 | 0.230 | topic_hint:work_office | 1.000 | 942 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `料金` | りょうきん | 0.239 | 0.239 | topic_hint:shopping_money | 1.000 | 945 -> 16 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `無料` | むりょう | 0.204 | 0.204 | topic_hint:shopping_money | 0.961 | 608 -> 17 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `報告` | ほうこく | 0.189 | 0.189 | topic_hint:work_office | 0.904 | 265 -> 18 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `許可` | きょか | 0.239 | 0.239 | topic_hint:computing_internet | 1.000 | 998 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `条件` | じょうけん | 0.189 | 0.189 | topic_hint:computing_internet | 0.903 | 275 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_food_animals_p65`

Food plus animals at post-N1 transition; checks shallow-topic behavior when learner is already advanced.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking', 'animals']` applied_seed_count=`66`

Active topic support:

- `animals` candidates=20 mass=5.435395 scarcity=eligible examples=犬, 猫, 馬, 鳥, 虫
- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `烏` | からす | 0.388 | 0.388 | topic_hint:animals | 1.000 | 4001 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `烏賊` | いか | 0.382 | 0.382 | topic_hint:animals | 1.000 | 4248 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `狐` | きつね | 0.380 | 0.380 | topic_hint:animals | 1.000 | 4460 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `喫茶` | きっさ | 0.357 | 0.357 | topic_hint:food_cooking | 0.968 | 3597 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `蛸` | たこ | 0.385 | 0.385 | topic_hint:animals | 1.000 | 4757 -> 7 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `蝶` | ちょう | 0.358 | 0.358 | topic_hint:animals | 0.971 | 3987 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `蜂` | はち | 0.367 | 0.367 | topic_hint:animals | 0.990 | 5100 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `亀` | かめ | 0.348 | 0.348 | topic_hint:animals | 0.939 | 3929 -> 11 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `煮る` | にる | 0.333 | 0.333 | topic_hint:food_cooking | 0.878 | 5705 -> 12 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `鹿` | しか | 0.362 | 0.362 | topic_hint:animals | 0.980 | 5591 -> 13 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `箸` | はし | 0.337 | 0.337 | topic_hint:food_cooking | 0.894 | 3739 -> 14 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `包丁` | ほうちょう | 0.338 | 0.338 | topic_hint:food_cooking | 0.902 | 4565 -> 15 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `餅` | もち | 0.327 | 0.327 | topic_hint:food_cooking | 0.845 | 3382 -> 19 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `人参` | にんじん | 0.322 | 0.322 | topic_hint:food_cooking | 0.819 | 2836 -> 20 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `饂飩` | うどん | 0.322 | 0.322 | topic_hint:food_cooking | 0.815 | 3342 -> 22 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `玉葱` | たまねぎ | 0.313 | 0.313 | topic_hint:food_cooking | 0.765 | 2772 -> 24 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `熊` | くま | 0.314 | 0.314 | topic_hint:animals | 0.768 | 3109 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `豆腐` | とうふ | 0.306 | 0.306 | topic_hint:food_cooking | 0.717 | 2326 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `蚊` | か | 0.317 | 0.317 | topic_hint:animals | 0.786 | 4724 -> 34 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `林檎` | りんご | 0.304 | 0.304 | topic_hint:food_cooking | 0.708 | 2445 -> 35 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_music_travel_p65`

Music/media plus travel at post-N1 transition; checks medium-topic continuation beyond the learner core.

- overlay: status=`active` application=`applied` active_topics=`['music_media_entertainment', 'travel_places_transport']` applied_seed_count=`69`

Active topic support:

- `music_media_entertainment` candidates=26 mass=8.854611 scarcity=eligible examples=写真, テレビ, 映画, 新聞, 音楽
- `travel_places_transport` candidates=43 mass=16.40845 scarcity=eligible examples=日本, 会社, 学校, アメリカ, 車

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `太鼓` | たいこ | 0.352 | 0.352 | topic_hint:music_media_entertainment | 0.955 | 3884 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `合唱` | がっしょう | 0.397 | 0.397 | topic_hint:music_media_entertainment | 1.000 | 5149 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `楽器` | がっき | 0.328 | 0.328 | topic_hint:music_media_entertainment | 0.850 | 3280 -> 9 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ドラム` | どらむ | 0.314 | 0.314 | topic_hint:music_media_entertainment | 0.767 | 5915 -> 29 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `音声` | おんせい | 0.300 | 0.300 | topic_hint:music_media_entertainment | 0.684 | 3181 -> 31 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `コンビニ` | こんびに | 0.280 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 7 | `御座る` | ござる | 0.493 | 0.493 |  | 0.997 | 634 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `項` | こう | 0.572 | 0.572 |  | 1.000 | 129 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `感` | かん | 0.531 | 0.531 |  | 1.000 | 201 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `論` | ろん | 0.576 | 0.576 |  | 1.000 | 424 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `通ずる` | つうずる | 0.527 | 0.527 |  | 1.000 | 2253 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `府` | ふ | 0.574 | 0.574 |  | 1.000 | 455 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `因み` | ちなみ | 0.569 | 0.569 |  | 1.000 | 583 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `層` | そう | 0.576 | 0.576 |  | 1.000 | 761 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `増` | ぞう | 0.577 | 0.577 |  | 1.000 | 908 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `故` | ゆえ | 0.577 | 0.577 |  | 1.000 | 969 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ザ` | ざ | 0.578 | 0.578 |  | 1.000 | 1039 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `我々` |  | - | 0.450 |  | 0.861 | 6278 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `有り` | あり | 0.577 | 0.577 |  | 1.000 | 1141 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `御陰` | おかげ | 0.577 | 0.577 |  | 1.000 | 1256 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_food_shopping_p85`

Food plus shopping/money at advanced-tail level; checks that shallow practical interests do not trap the queue.

- overlay: status=`active` application=`applied` active_topics=`['food_cooking', 'shopping_money']` applied_seed_count=`73`

Active topic support:

- `food_cooking` candidates=46 mass=14.718733 scarcity=eligible examples=食べる, 飲む, 料理, 酒, 味
- `shopping_money` candidates=27 mass=10.218774 scarcity=eligible examples=円, 高い, 買う, 商品, 店

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 |  | 1.000 | 3366 -> 1 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 2 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `インターフェース` | いんたーふぇーす | 0.750 | 0.750 |  | 1.000 | 6664 -> 3 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `ウォッチ` | うぉっち | 0.714 | 0.714 |  | 1.000 | 6822 -> 4 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `メソッド` | めそっど | 0.676 | 0.676 |  | 0.966 | 6546 -> 5 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `エステ` | えすて | 0.703 | 0.703 |  | 1.000 | 7083 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `レフ` | れふ | 0.710 | 0.710 |  | 1.000 | 7249 -> 7 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `ブロードバンド` | ぶろーどばんど | 0.702 | 0.702 |  | 1.000 | 7260 -> 8 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `ウィン` | うぃん | 0.647 | 0.647 |  | 0.844 | 5234 -> 9 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `ファー` | ふぁー | 0.937 | 0.937 |  | 1.000 | 6846 -> 10 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `シックス` | しっくす | 0.724 | 0.724 |  | 1.000 | 7579 -> 11 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 12 | `ゲット` | げっと | 0.635 | 0.635 |  | 0.774 | 4319 -> 12 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 13 | `ピックアップ` | ぴっくあっぷ | 0.681 | 0.681 |  | 0.979 | 7535 -> 13 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 14 | `マザー` | まざー | 0.645 | 0.645 |  | 0.833 | 5602 -> 14 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 15 | `インナー` | いんなー | 0.759 | 0.759 |  | 1.000 | 7877 -> 15 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 16 | `オリーブ` | おりーぶ | 0.633 | 0.633 |  | 0.763 | 4995 -> 16 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 17 | `ハザード` | はざーど | 0.790 | 0.790 |  | 1.000 | 8233 -> 17 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 18 | `コスメ` | こすめ | 0.760 | 0.760 |  | 1.000 | 8235 -> 18 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 19 | `ブラウザ` | ぶらうざ | 0.631 | 0.631 |  | 0.753 | 5236 -> 19 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
| 20 | `係属` | けいぞく | 0.696 | 0.696 |  | 0.999 | 8414 -> 20 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |

### `mixed_entertainment_cluster_p85`

Anime/manga, games, and hobbies at advanced-tail level; checks whether deeper on-topic terms remain coherent.

- overlay: status=`active` application=`applied` active_topics=`['anime_manga_pop_culture', 'games', 'hobbies_crafts']` applied_seed_count=`133`

Active topic support:

- `anime_manga_pop_culture` candidates=55 mass=13.410732 scarcity=eligible examples=作品, 設定, ファン, 日常, 予約
- `games` candidates=34 mass=8.258756 scarcity=eligible examples=レベル, 試合, ゲーム, 大会, 戦略
- `hobbies_crafts` candidates=47 mass=13.121235 scarcity=eligible examples=写真, 映画, 料理, 音楽, 撮影

| # | Lemma | Reading | Corrected | Runtime Diff | Topic | Ready | Base -> Rerank | Note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 | `クリア` | くりあ | 0.720 | 0.720 | topic_hint:games | 1.000 | 3366 -> 1 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 2 | `キャラ` | きゃら | 0.578 | 0.578 | topic_hint:anime_manga_pop_culture | 1.000 | 3633 -> 2 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 3 | `詰め` | つめ | 0.582 | 0.582 | topic_hint:games | 1.000 | 6407 -> 3 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 4 | `イラスト` | いらすと | 0.505 | 0.505 | topic_hint:anime_manga_pop_culture | 0.714 | 3685 -> 4 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 5 | `タッチ` | たっち | 0.493 | 0.493 | topic_hint:anime_manga_pop_culture | 0.637 | 4226 -> 5 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 6 | `ポスター` | ぽすたー | 0.474 | 0.474 | topic_hint:anime_manga_pop_culture | 0.509 | 4259 -> 8 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 7 | `属性` | ぞくせい | 0.465 | 0.465 | topic_hint:anime_manga_pop_culture | 0.449 | 6380 -> 27 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 8 | `リーチ` | りーち | 0.488 | 0.488 | topic_hint:games | 0.604 | 8242 -> 30 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 9 | `野鳥` | やちょう | 0.446 | 0.446 | topic_hint:hobbies_crafts | 0.342 | 7761 -> 142 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 10 | `打開` | だかい | 0.440 | 0.440 | topic_hint:games | 0.306 | 7608 -> 199 | Boosted by topic_affinity, proficiency_fit, while remaining supported by coverage_gain. |
| 11 | `星空` | ほしぞら | 0.439 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 12 | `一手` | いって | 0.435 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 13 | `コメント` | こめんと | 0.419 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 14 | `攻勢` | こうせい | 0.434 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 15 | `レベル` | れべる | 0.413 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 16 | `短歌` | たんか | 0.428 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 17 | `勝敗` | しょうはい | 0.430 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 18 | `陶芸` | とうげい | 0.428 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 19 | `ファン` | ふぁん | 0.411 | - |  | - | None -> None | Selected for the initial active bootstrap preview. |
| 20 | `ジャバ` | じゃば | 0.692 | 0.692 |  | 0.997 | 6401 -> 6 | Boosted by proficiency_fit, while remaining supported by coverage_gain. |
