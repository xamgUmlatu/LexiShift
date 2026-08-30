# en-ja SRS Topic Autotag Promotion Overlay

- Status: `ok`
- Decision: `srs_topic_autotag_promotion_overlay_ready`
- Generated: `2026-07-02T19:04:30+00:00`
- Overlay rows: `3996`
- Runtime-effective rows: `831`
- Review-only rows: `3165`

## Coverage

| Topic | Rows | Runtime-effective |
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

## Promotion Rules

- `product_owned_manual_semantic_lexicon`: `894`
- `reviewed_jmdict_overlay`: `65`
- `strict_jawikipedia_dump_category`: `286`
- `strict_kaikki_wiktionary_topic`: `2747`
- `strict_wikidata_claim_probe`: `4`

## Excluded Counts

- `jawikipedia_dump_category:auto_review_rejected:reject_secondary_or_obscure_sense`: `7`
- `jawikipedia_dump_category:auto_review_rejected:reject_wrong_sense`: `3`
- `jawikipedia_dump_category:auto_review_rejected:reject_wrong_topic`: `26`
- `jawikipedia_dump_category:not_promotion_ready`: `5932`
- `kaikki_wiktionary_topic:auto_review_rejected:reject_secondary_or_obscure_sense`: `25`
- `kaikki_wiktionary_topic:auto_review_rejected:reject_wrong_sense`: `15`
- `kaikki_wiktionary_topic:auto_review_rejected:reject_wrong_topic`: `79`
- `kaikki_wiktionary_topic:not_promotion_ready`: `5484`
- `manual_semantic_lexicon:manual_review_rejected_key`: `1`
- `wikidata_claim_probe:auto_review_rejected:reject_secondary_or_obscure_sense`: `1`

## Runtime-Effective Sample

| Topic | Lemma | Reading | Membership | Rule | Source labels | Blockers |
| --- | --- | --- | ---: | --- | --- | --- |
| `animals` | `パンダ` | `ぱんだ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `ライオン` | `らいおん` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `亀` | `かめ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `兎` | `うさぎ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `烏` | `からす` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `烏賊` | `いか` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `熊` | `くま` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `牛` | `うし` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `犬` | `いぬ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `狐` | `きつね` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `猫` | `ねこ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `猿` | `さる` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `虎` | `とら` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `虫` | `むし` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals, 動物` | `` |
| `animals` | `蚊` | `か` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蛸` | `たこ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蜂` | `はち` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蜘蛛` | `くも` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蝶` | `ちょう` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蟻` | `あり` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `蠅` | `はえ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `象` | `ぞう` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `馬` | `うま` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `鮫` | `さめ` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `鳥` | `とり` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals, 鳥類` | `` |
| `animals` | `鴨` | `かも` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `animals` | `鹿` | `しか` | 1.0 | `product_owned_manual_semantic_lexicon` | `common_animals` | `` |
| `anime_manga_pop_culture` | `アクリル` | `あくりる` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `アニメ` | `あにめ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime, anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `アニメーター` | `あにめーたー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core, アニメ` | `` |
| `anime_manga_pop_culture` | `アフレコ` | `あふれこ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `イベント` | `いべんと` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `イラスト` | `いらすと` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `イラストレーター` | `いらすとれーたー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `エンディング` | `えんでぃんぐ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `オープニング` | `おーぷにんぐ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `カード` | `かーど` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `キャラ` | `きゃら` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `キャラクター` | `きゃらくたー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ギャグ` | `ぎゃぐ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `グッズ` | `ぐっず` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `コスチューム` | `こすちゅーむ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `コスプレ` | `こすぷれ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core, アニメ` | `` |
| `anime_manga_pop_culture` | `コミケ` | `こみけ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `コメント` | `こめんと` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `サントラ` | `さんとら` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `サークル` | `さーくる` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ジャンル` | `じゃんる` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ステッカー` | `すてっかー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `スペース` | `すぺーす` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `タッチ` | `たっち` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ノベライズ` | `のべらいず` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ヒロイン` | `ひろいん` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ヒーロー` | `ひーろー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ファン` | `ふぁん` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ファンタジー` | `ふぁんたじー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `フィギュア` | `ふぃぎゅあ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ブーム` | `ぶーむ` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ホラー` | `ほらー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ポスター` | `ぽすたー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ポストカード` | `ぽすとかーど` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ミステリー` | `みすてりー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `レビュー` | `れびゅー` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `ロボット` | `ろぼっと` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `主役` | `しゅやく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `予告` | `よこく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `予約` | `よやく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `付録` | `ふろく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `伏線` | `ふくせん` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `休載` | `きゅうさい` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `作品` | `さくひん` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `作画` | `さくが` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `作風` | `さくふう` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `傑作` | `けっさく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `再開` | `さいかい` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `冒険` | `ぼうけん` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `制服` | `せいふく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `動画` | `どうが` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `原作` | `げんさく` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |
| `anime_manga_pop_culture` | `原画` | `げんが` | 1.0 | `product_owned_manual_semantic_lexicon` | `anime_manga_pop_culture_core` | `` |

## Review-Only Sample

| Topic | Lemma | Reading | Membership | Rule | Source labels | Blockers |
| --- | --- | --- | ---: | --- | --- | --- |
| `animals` | `エソロジー` | `えそろじー` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `カラザ` | `からざ` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology, zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `マウス` | `まうす` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology, zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `体毛` | `たいもう` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `冷血` | `れいけつ` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology, zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `動物` | `どうぶつ` | 0.65 | `strict_jawikipedia_dump_category` | `Animals, 動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `卵` | `` | 0.65 | `reviewed_jmdict_overlay` | `zoology` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `吸盤` | `きゅうばん` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology, zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `吸血` | `きゅうけつ` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `吻` | `ふん` | 0.65 | `strict_kaikki_wiktionary_topic` | `zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `哺乳` | `ほにゅう` | 0.65 | `strict_jawikipedia_dump_category` | `哺乳` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `営巣` | `えいそう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `嘴` | `くちばし` | 0.65 | `strict_jawikipedia_dump_category` | `zoology, 鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `四肢` | `しし` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `夏羽` | `なつばね` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `小魚` | `こざかな` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `小鳥` | `ことり` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `尻鰭` | `しりびれ` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `尾筒` | `おづつ` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `尾羽` | `おは` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `川虫` | `かわむし` | 0.65 | `strict_jawikipedia_dump_category` | `昆虫` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `巨獣` | `きょじゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Animals` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `幼虫` | `ようちゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology, entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `役畜` | `えきちく` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `成虫` | `せいちゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology, entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `換羽` | `かんう` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `昆虫` | `こんちゅう` | 0.65 | `strict_jawikipedia_dump_category` | `昆虫` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `毒針` | `どくばり` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `海綿` | `かいめん` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `熊虫` | `くまむし` | 0.65 | `strict_jawikipedia_dump_category` | `Animals, 動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `猛獣` | `もうじゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Animals` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `獣毛` | `じゅうもう` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `獣脂` | `じゅうし` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `珍獣` | `ちんじゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Animals` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `畜力` | `ちくりょく` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `簗` | `やな` | 0.65 | `strict_kaikki_wiktionary_topic` | `zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `線虫` | `せんちゅう` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `繭` | `まゆ` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology, entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `羊` | `ひつじ` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `羊水` | `ようすい` | 0.65 | `strict_kaikki_wiktionary_topic` | `Zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `羽化` | `うか` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology, entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `羽太` | `はた` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `胸鰭` | `むなびれ` | 0.65 | `strict_jawikipedia_dump_category` | `zoology, 魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `腹鰭` | `はらびれ` | 0.65 | `strict_kaikki_wiktionary_topic` | `zoology` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings, unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `草食` | `そうしょく` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `蛇` | `へび` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `蛙` | `かえる` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `蛞蝓魚` | `なめくじうお` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `蛭` | `ひる` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `蛹` | `さなぎ` | 0.65 | `strict_kaikki_wiktionary_topic` | `Entomology, entomology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `衣蛾` | `いが` | 0.65 | `strict_jawikipedia_dump_category` | `昆虫` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `被毛` | `ひもう` | 0.65 | `strict_jawikipedia_dump_category` | `動物` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `角` | `つの` | 0.65 | `strict_kaikki_wiktionary_topic` | `zoology` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings, unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `触腕` | `しょくわん` | 0.65 | `strict_kaikki_wiktionary_topic` | `zoology` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `豚` | `ぶた` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `貝` | `かい` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `趾` | `し` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `野獣` | `やじゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Animals` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `魚` | `さかな` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `魚種` | `ぎょしゅ` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `魚類` | `ぎょるい` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `鯨` | `くじら` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings, topic_stretch_disallowed` |
| `animals` | `鱗板` | `りんばん` | 0.65 | `strict_jawikipedia_dump_category` | `魚類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `鳥獣` | `ちょうじゅう` | 0.65 | `strict_kaikki_wiktionary_topic` | `Animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings, unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `鳥類` | `ちょうるい` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `鶏` | `にわとり` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings` |
| `animals` | `鷭` | `ばん` | 0.65 | `strict_jawikipedia_dump_category` | `鳥類` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `animals` | `鼠` | `ねずみ` | 0.65 | `product_owned_manual_semantic_lexicon` | `common_animals` | `runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings, topic_stretch_disallowed` |
| `animals` | `ＢＳＥ` | `` | 0.65 | `reviewed_jmdict_overlay` | `veterinary terms` | `candidate_lemma_missing_from_corrected_csv` |
| `anime_manga_pop_culture` | `アイコラ` | `あいこら` | 0.65 | `strict_jawikipedia_dump_category` | `アイドル` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `アイドル` | `あいどる` | 0.65 | `strict_jawikipedia_dump_category` | `アイドル` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `アニソン` | `あにそん` | 0.65 | `strict_jawikipedia_dump_category` | `アニメ` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `アニメイト` | `あにめいと` | 0.65 | `strict_jawikipedia_dump_category` | `アニメ` | `candidate_state_not_all_normal_vocab, unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `アニメーション` | `あにめーしょん` | 0.65 | `strict_jawikipedia_dump_category` | `anime, アニメ` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `アメコミ` | `あめこみ` | 0.65 | `strict_kaikki_wiktionary_topic` | `Comics` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `グラドル` | `ぐらどる` | 0.65 | `strict_jawikipedia_dump_category` | `アイドル` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `コスプレイヤー` | `こすぷれいやー` | 0.65 | `strict_jawikipedia_dump_category` | `アニメ` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `コミック` | `こみっく` | 0.65 | `strict_jawikipedia_dump_category` | `Comics, 漫画` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `ジャパニメーション` | `じゃぱにめーしょん` | 0.65 | `strict_jawikipedia_dump_category` | `アニメ` | `unreviewed_auto_topic_evidence_requires_manual_acceptance` |
| `anime_manga_pop_culture` | `ピクサー` | `ぴくさー` | 0.65 | `strict_jawikipedia_dump_category` | `アニメ` | `candidate_state_not_all_normal_vocab, unreviewed_auto_topic_evidence_requires_manual_acceptance` |

## Findings

- `PASS` `candidate_index_loaded`: Loaded 71799 candidate lemma surfaces.
- `PASS` `reviewed_overlay_loaded`: Reviewed JMDict overlay rows were loaded.
- `PASS` `dump_evidence_loaded`: Guarded dump evidence rows were loaded.
- `PASS` `wikidata_evidence_loaded`: Wikidata claim-probe evidence rows were loaded.
- `PASS` `manual_semantic_evidence_loaded`: Manual semantic lexicon evidence rows were loaded.
- `PASS` `promotion_overlay_ready`: Product-safe topic overlay candidate was built.

## Limitations

- This is a product-safe candidate overlay, not a default-enabled runtime artifact.
- Rows with membership below 1.0 are retained as review evidence but are not runtime-effective under the current overlay contract.
- The current runtime overlay key is lemma-only; reading-specific topic membership needs a runtime schema change before it can be safely admitted.
- This export intentionally favors precision over coverage and therefore leaves many plausible topic rows in the review-candidate pool.
