# en-ja Learner Difficulty Full-Range Sampling Review

Source: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv`
Seed: `20260630`
Method: deterministic random sample of up to 12 rows per 0.05 score band, plus up to 8 mechanically risk-ranked rows per band. Risk rows are not handpicked; they combine manual-correction presence, review flags, same-surface risk, tail/suspicion signals, and normalized-only JLPT support.

## Band Counts

| Band | Count |
| --- | ---: |
| `0.00-0.05` | 106 |
| `0.05-0.10` | 284 |
| `0.10-0.15` | 495 |
| `0.15-0.20` | 798 |
| `0.20-0.25` | 1226 |
| `0.25-0.30` | 1312 |
| `0.30-0.35` | 1940 |
| `0.35-0.40` | 3072 |
| `0.40-0.45` | 3928 |
| `0.45-0.50` | 4805 |
| `0.50-0.55` | 5177 |
| `0.55-0.60` | 5902 |
| `0.60-0.65` | 4383 |
| `0.65-0.70` | 4901 |
| `0.70-0.75` | 5506 |
| `0.75-0.80` | 6423 |
| `0.80-0.85` | 7566 |
| `0.85-0.90` | 7569 |
| `0.90-0.95` | 6004 |
| `0.95-1.00` | 2355 |

## Band 0.00-0.05 (106 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 7 | 0.003829 | `物` | `もの` | `物` | `normal_vocab` | early_kana_preferred_kanji |
| 8 | 0.004279 | `行く` | `いく` | `行く` | `normal_vocab` | early_kana_preferred_kanji |
| 9 | 0.005000 | `いい` | `いい` | `いい` | `normal_vocab` | score_override |
| 20 | 0.009685 | `使う` | `つかう` | `使う` | `normal_vocab` |  |
| 39 | 0.018694 | `置く` | `おく` | `置く` | `normal_vocab` | early_kana_preferred_kanji |
| 45 | 0.021396 | `一人` | `ひとり` | `一人` | `normal_vocab` | early_kana_preferred_kanji |
| 46 | 0.021847 | `大きい` | `おおきい` | `大きい` | `normal_vocab` |  |
| 47 | 0.022297 | `皆` | `みな` | `皆` | `normal_vocab` | early_kana_preferred_kanji |
| 49 | 0.023198 | `仕事` | `しごと` | `仕事` | `normal_vocab` |  |
| 52 | 0.024550 | `写真` | `しゃしん` | `写真` | `normal_vocab` |  |
| 59 | 0.027703 | `教える` | `おしえる` | `教える` | `normal_vocab` |  |
| 97 | 0.045721 | `読む` | `よむ` | `読む` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.500 | 9 | 0.005000 | `いい` | `いい` | `いい` | `normal_vocab` | score_override |
| 0.972 | 53 | 0.025000 | `何処` | `どこ` | `どこ` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.961 | 17 | 0.008333 | `所` | `ところ` | `ところ` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.960 | 5 | 0.002477 | `成る` | `なる` | `なる` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.957 | 3 | 0.001577 | `居る` | `いる` | `いる` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.752 | 12 | 0.006081 | `つく` | `つく` | `つく` | `exclude_standalone_srs` | exclude_standalone_srs |
| 0.400 | 14 | 0.006982 | `中` | `なか` | `中` | `normal_vocab` | early_kana_preferred_kanji |
| 0.400 | 37 | 0.017793 | `後` | `あと` | `後` | `normal_vocab` | early_kana_preferred_kanji |

## Band 0.05-0.10 (284 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 120 | 0.052627 | `飲む` | `のむ` | `飲む` | `normal_vocab` |  |
| 136 | 0.055508 | `見せる` | `みせる` | `見せる` | `normal_vocab` |  |
| 207 | 0.068051 | `街` | `まち` | `街` | `normal_vocab` |  |
| 209 | 0.068390 | `鳥` | `とり` | `鳥` | `normal_vocab` |  |
| 210 | 0.068559 | `春` | `はる` | `春` | `normal_vocab` |  |
| 228 | 0.071610 | `有名` | `ゆうめい` | `有名` | `normal_vocab` |  |
| 260 | 0.077373 | `着く` | `つく` | `着く` | `normal_vocab` |  |
| 276 | 0.080000 | `良い` | `よい` | `良い` | `normal_vocab` | score_floor,normalized_only_jlpt |
| 284 | 0.081102 | `短い` | `みじかい` | `短い` | `normal_vocab` |  |
| 329 | 0.089237 | `橋` | `はし` | `橋` | `normal_vocab` |  |
| 343 | 0.091780 | `散歩` | `さんぽ` | `散歩` | `normal_vocab` |  |
| 367 | 0.096017 | `帽子` | `ぼうし` | `帽子` | `normal_vocab` | early_kana_preferred_kanji |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.647 | 387 | 0.099407 | `鞄` | `かばん` | `かばん` | `normal_vocab` | display_only,early_kana_preferred_kanji,normalized_only_jlpt |
| 1.565 | 276 | 0.080000 | `良い` | `よい` | `良い` | `normal_vocab` | score_floor,normalized_only_jlpt |
| 1.153 | 277 | 0.080000 | `ワイシャツ` | `わいしゃつ` | `ワイシャツ` | `normal_vocab` | score_floor |
| 1.150 | 235 | 0.073136 | `家` | `うち` | `うち` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 1.150 | 257 | 0.076864 | `御飯` | `ごはん` | `ご飯` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.995 | 379 | 0.098051 | `煩い` | `うるさい` | `うるさい` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.975 | 134 | 0.055169 | `余り` | `あまり` | `あまり` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 0.968 | 145 | 0.057034 | `始め` | `はじめ` | `はじめ` | `normal_vocab` | display_only,early_kana_preferred_kanji |

## Band 0.10-0.15 (495 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 419 | 0.102500 | `曲がる` | `まがる` | `曲がる` | `normal_vocab` |  |
| 432 | 0.103602 | `シャワー` | `しゃわー` | `シャワー` | `normal_vocab` |  |
| 496 | 0.113093 | `じゃあ` | `じゃあ` | `じゃあ` | `normal_vocab` |  |
| 517 | 0.118517 | `ノート` | `のーと` | `ノート` | `normal_vocab` |  |
| 526 | 0.119280 | `ズボン` | `ずぼん` | `ズボン` | `normal_vocab` |  |
| 619 | 0.128008 | `生産` | `せいさん` | `生産` | `normal_vocab` |  |
| 660 | 0.131229 | `以外` | `いがい` | `以外` | `normal_vocab` |  |
| 661 | 0.131314 | `最初` | `さいしょ` | `最初` | `normal_vocab` |  |
| 705 | 0.135000 | `借り` | `かり` | `借り` | `normal_vocab` |  |
| 785 | 0.141398 | `用意` | `ようい` | `用意` | `normal_vocab` |  |
| 809 | 0.143432 | `落とす` | `おとす` | `落とす` | `normal_vocab` |  |
| 849 | 0.146907 | `答え` | `こたえ` | `答え` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.544 | 455 | 0.106059 | `開く` | `あく` | `開く` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.499 | 487 | 0.110042 | `黄色` | `おうしょく` | `黄色` | `formal_or_on_reading` | restricted_admission,formal_or_on_reading |
| 1.484 | 505 | 0.116144 | `温い` | `ぬるい` | `ぬるい` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 1.389 | 460 | 0.106568 | `明日` | `あした` | `明日` | `normal_vocab` | early_same_surface_risk |
| 1.377 | 535 | 0.120000 | `他` | `た` | `他` | `compound_or_formal_reading` | score_floor,restricted_admission,early_kana_preferred_kanji,compound_or_formal_reading |
| 1.357 | 491 | 0.111483 | `易しい` | `やさしい` | `やさしい` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 1.298 | 391 | 0.100000 | `半` | `はん` | `半` | `compound_or_prefix_reading` | score_floor,restricted_admission,compound_or_prefix_reading |
| 1.190 | 507 | 0.117246 | `鳥肉` | `とりにく` | `鳥肉` | `normal_vocab` | normalized_only_jlpt |

## Band 0.15-0.20 (798 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1107 | 0.166130 | `呉れる` | `くれる` | `呉れる` | `normal_vocab` | early_kana_preferred_kanji |
| 1132 | 0.167599 | `然し` | `しかし` | `然し` | `normal_vocab` | early_kana_preferred_kanji |
| 1146 | 0.168616 | `未だ` | `まだ` | `未だ` | `normal_vocab` | early_kana_preferred_kanji |
| 1153 | 0.169011 | `ゲーム` | `げーむ` | `ゲーム` | `normal_vocab` |  |
| 1155 | 0.169124 | `デザイン` | `でざいん` | `デザイン` | `normal_vocab` |  |
| 1166 | 0.169802 | `願う` | `ねがう` | `願う` | `normal_vocab` |  |
| 1180 | 0.170650 | `現在` | `げんざい` | `現在` | `normal_vocab` |  |
| 1190 | 0.171215 | `オーケー` | `おーけー` | `オーケー` | `normal_vocab` |  |
| 1209 | 0.172401 | `レース` | `れーす` | `レース` | `normal_vocab` |  |
| 1411 | 0.184266 | `期間` | `きかん` | `期間` | `normal_vocab` |  |
| 1524 | 0.190480 | `生` | `なま` | `生` | `normal_vocab` | early_kana_preferred_kanji |
| 1613 | 0.195904 | `セキュリティー` | `せきゅりてぃー` | `セキュリティー` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.338 | 1340 | 0.180000 | `後` | `のち` | `後` | `normal_vocab` | score_floor,early_kana_preferred_kanji |
| 1.330 | 1256 | 0.175169 | `或いは` | `あるいは` | `あるいは` | `normal_vocab` | display_only,manual_watchlist,early_kana_preferred_kanji |
| 1.239 | 1307 | 0.178164 | `様` | `さま` | `様` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.185 | 1267 | 0.175781 | `火` | `か` | `火` | `compound_or_on_reading` | restricted_admission,compound_or_on_reading |
| 1.178 | 1029 | 0.158446 | `都` | `みやこ` | `都` | `normal_vocab` | early_same_surface_risk |
| 1.129 | 968 | 0.154774 | `訳` | `やく` | `訳` | `compound_or_on_reading` | restricted_admission,compound_or_on_reading |
| 1.072 | 1515 | 0.190000 | `用` | `よう` | `用` | `compound_or_function_noun` | score_floor,restricted_admission,compound_or_function_noun |
| 1.000 | 896 | 0.150593 | `音` | `おん` | `音` | `compound_or_on_reading` | restricted_admission,compound_or_on_reading |

## Band 0.20-0.25 (1226 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1687 | 0.200191 | `動画` | `どうが` | `動画` | `normal_vocab` |  |
| 1704 | 0.200996 | `団体` | `だんたい` | `団体` | `normal_vocab` |  |
| 2015 | 0.214258 | `其方` | `そちら` | `其方` | `normal_vocab` | early_kana_preferred_kanji |
| 2139 | 0.219725 | `費用` | `ひよう` | `費用` | `normal_vocab` |  |
| 2173 | 0.220275 | `連続` | `れんぞく` | `連続` | `normal_vocab` |  |
| 2217 | 0.222267 | `話題` | `わだい` | `話題` | `normal_vocab` |  |
| 2221 | 0.222436 | `パウダー` | `ぱうだー` | `パウダー` | `normal_vocab` |  |
| 2273 | 0.224597 | `オプション` | `おぷしょん` | `オプション` | `normal_vocab` |  |
| 2293 | 0.225445 | `トレード` | `とれーど` | `トレード` | `normal_vocab` |  |
| 2348 | 0.227601 | `西` | `せい` | `西` | `compound_or_directional_reading` | restricted_admission,early_same_surface_risk,compound_or_directional_reading |
| 2639 | 0.239343 | `パーソナル` | `ぱーそなる` | `パーソナル` | `normal_vocab` |  |
| 2734 | 0.242945 | `一層` | `いっそう` | `一層` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 3.610 | 2164 | 0.220000 | `入り口` | `いりくち` | `入り口` | `variant_reading` | score_floor,restricted_admission,early_same_surface_risk,normalized_only_jlpt,variant_reading |
| 2.954 | 2166 | 0.220000 | `君` | `くん` | `君` | `suffix_or_title_reading` | score_floor,restricted_admission,early_same_surface_risk,suffix_or_title_reading |
| 2.950 | 2165 | 0.220000 | `南` | `なん` | `南` | `compound_reading` | score_floor,restricted_admission,early_same_surface_risk,compound_reading |
| 2.573 | 2162 | 0.220000 | `塩` | `えん` | `塩` | `compound_or_on_reading` | score_floor,restricted_admission,early_same_surface_risk,compound_or_on_reading |
| 2.550 | 2320 | 0.226526 | `東` | `とう` | `東` | `compound_or_directional_reading` | restricted_admission,early_same_surface_risk,compound_or_directional_reading |
| 2.550 | 2348 | 0.227601 | `西` | `せい` | `西` | `compound_or_directional_reading` | restricted_admission,early_same_surface_risk,compound_or_directional_reading |
| 2.550 | 2370 | 0.228380 | `北` | `ほく` | `北` | `compound_or_directional_reading` | restricted_admission,early_same_surface_risk,compound_or_directional_reading |
| 2.414 | 2660 | 0.240000 | `夜` | `よ` | `夜` | `normal_vocab` | score_floor,early_same_surface_risk |

## Band 0.25-0.30 (1312 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3085 | 0.255225 | `賛成` | `さんせい` | `賛成` | `normal_vocab` |  |
| 3150 | 0.257198 | `睡眠` | `すいみん` | `睡眠` | `normal_vocab` |  |
| 3161 | 0.257568 | `才能` | `さいのう` | `才能` | `normal_vocab` |  |
| 3188 | 0.258399 | `セクシー` | `せくしー` | `セクシー` | `normal_vocab` |  |
| 3300 | 0.261883 | `座席` | `ざせき` | `座席` | `normal_vocab` |  |
| 3328 | 0.262808 | `能` | `のう` | `能` | `normal_vocab` |  |
| 3349 | 0.263517 | `芽` | `め` | `芽` | `normal_vocab` |  |
| 3363 | 0.263949 | `等しい` | `ひとしい` | `等しい` | `normal_vocab` |  |
| 3452 | 0.267124 | `予期` | `よき` | `予期` | `normal_vocab` |  |
| 3647 | 0.281489 | `総理` | `そうり` | `総理` | `normal_vocab` |  |
| 3978 | 0.292494 | `プレート` | `ぷれーと` | `プレート` | `normal_vocab` |  |
| 4114 | 0.297179 | `記す` | `しるす` | `記す` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.350 | 4217 | 0.300000 | `上` | `かみ` | `上` | `formal_or_spatial_variant` | score_floor,restricted_admission,formal_or_spatial_variant |
| 2.027 | 4219 | 0.300000 | `打つ` | `ぶつ` | `打つ` | `normal_vocab` | score_floor |
| 1.998 | 4221 | 0.300000 | `包む` | `くるむ` | `包む` | `normal_vocab` | score_floor |
| 1.965 | 4218 | 0.300000 | `魚` | `うお` | `魚` | `normal_vocab` | score_floor |
| 1.950 | 3564 | 0.278345 | `面` | `おも` | `面` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.949 | 3565 | 0.278560 | `骨` | `こつ` | `骨` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.878 | 4220 | 0.300000 | `音` | `ね` | `音` | `normal_vocab` | score_floor |
| 1.750 | 3549 | 0.274800 | `悪口` | `あっこう` | `悪口` | `normal_vocab` | early_same_surface_risk |

## Band 0.30-0.35 (1940 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 4474 | 0.305953 | `実感` | `じっかん` | `実感` | `normal_vocab` |  |
| 4548 | 0.307919 | `伝説` | `でんせつ` | `伝説` | `normal_vocab` |  |
| 4552 | 0.308032 | `顧客` | `こきゃく` | `顧客` | `normal_vocab` |  |
| 4979 | 0.318809 | `エコノミスト` | `えこのみすと` | `エコノミスト` | `normal_vocab` |  |
| 5239 | 0.325791 | `カロチン` | `かろちん` | `カロチン` | `normal_vocab` |  |
| 5301 | 0.327259 | `イズム` | `いずむ` | `イズム` | `normal_vocab` |  |
| 5368 | 0.328999 | `預金` | `よきん` | `預金` | `normal_vocab` |  |
| 5541 | 0.333653 | `発送` | `はっそう` | `発送` | `normal_vocab` |  |
| 5643 | 0.336613 | `行方` | `ゆくえ` | `行方` | `normal_vocab` |  |
| 5764 | 0.339686 | `ベーカリー` | `べーかりー` | `ベーカリー` | `normal_vocab` |  |
| 5773 | 0.339889 | `阿呆` | `あほう` | `阿呆` | `normal_vocab` |  |
| 5863 | 0.342149 | `有機` | `ゆうき` | `有機` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.547 | 6160 | 0.350000 | `昼間` | `ちゅうかん` | `昼間` | `variant_reading` | score_floor,restricted_admission,variant_reading |
| 2.546 | 6152 | 0.350000 | `丈夫` | `じょうふ` | `丈夫` | `rare_reading` | score_floor,restricted_admission,rare_reading |
| 2.541 | 6156 | 0.350000 | `字` | `あざ` | `字` | `rare_or_place_reading` | score_floor,restricted_admission,rare_or_place_reading |
| 2.300 | 6155 | 0.350000 | `僕` | `しもべ` | `僕` | `normal_vocab` | score_floor |
| 2.300 | 6158 | 0.350000 | `工場` | `こうば` | `工場` | `normal_vocab` | score_floor |
| 2.298 | 6153 | 0.350000 | `上手` | `うわて` | `上手` | `normal_vocab` | score_floor |
| 2.291 | 6154 | 0.350000 | `下` | `しも` | `下` | `normal_vocab` | score_floor |
| 2.253 | 6151 | 0.350000 | `眼鏡` | `がんきょう` | `眼鏡` | `rare_or_on_reading` | score_floor,restricted_admission,rare_or_on_reading |

## Band 0.35-0.40 (3072 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 6221 | 0.351161 | `鑑定` | `かんてい` | `鑑定` | `normal_vocab` |  |
| 6631 | 0.359958 | `密か` | `ひそか` | `密か` | `normal_vocab` |  |
| 6873 | 0.365110 | `罰` | `ばつ` | `罰` | `normal_vocab` |  |
| 7292 | 0.374653 | `ラバー` | `らばー` | `ラバー` | `normal_vocab` |  |
| 7651 | 0.383636 | `提携` | `ていけい` | `提携` | `normal_vocab` |  |
| 7754 | 0.385634 | `がんがん` | `がんがん` | `がんがん` | `normal_vocab` |  |
| 8020 | 0.388177 | `ホステル` | `ほすてる` | `ホステル` | `normal_vocab` |  |
| 8112 | 0.388650 | `トレンディー` | `とれんでぃー` | `トレンディー` | `normal_vocab` |  |
| 8392 | 0.390856 | `協調` | `きょうちょう` | `協調` | `normal_vocab` |  |
| 8653 | 0.393578 | `トラクター` | `とらくたー` | `トラクター` | `normal_vocab` |  |
| 8771 | 0.394586 | `ポテンシャル` | `ぽてんしゃる` | `ポテンシャル` | `normal_vocab` |  |
| 9085 | 0.398093 | `連勝` | `れんしょう` | `連勝` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.061 | 7772 | 0.385866 | `妙` | `たえ` | `妙` | `normal_vocab` |  |
| 1.050 | 8325 | 0.390246 | `代` | `よ` | `代` | `normal_vocab` |  |
| 1.049 | 7469 | 0.379127 | `自修` | `じしゅう` | `自修` | `normal_vocab` |  |
| 1.000 | 8998 | 0.397094 | `主` | `あるじ` | `主` | `normal_vocab` |  |
| 0.963 | 9230 | 0.399941 | `冠` | `かんむり` | `冠` | `normal_vocab` |  |
| 0.750 | 6287 | 0.352669 | `かた` | `かた` | `かた` | `normal_vocab` |  |
| 0.750 | 6328 | 0.353432 | `ひく` | `ひく` | `ひく` | `normal_vocab` |  |
| 0.750 | 6460 | 0.356398 | `眼` | `がん` | `眼` | `normal_vocab` |  |

## Band 0.40-0.45 (3928 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 9234 | 0.400000 | `認める` | `したためる` | `認める` | `normal_vocab` | score_floor |
| 9297 | 0.400612 | `ビス` | `びす` | `ビス` | `normal_vocab` |  |
| 9583 | 0.404700 | `老齢` | `ろうれい` | `老齢` | `normal_vocab` |  |
| 9833 | 0.408224 | `鰻` | `うなぎ` | `鰻` | `normal_vocab` |  |
| 10258 | 0.413824 | `リラ` | `りら` | `リラ` | `normal_vocab` |  |
| 10393 | 0.415652 | `容姿` | `ようし` | `容姿` | `normal_vocab` |  |
| 10875 | 0.421956 | `野心` | `やしん` | `野心` | `normal_vocab` |  |
| 10986 | 0.423543 | `中将` | `ちゅうじょう` | `中将` | `normal_vocab` |  |
| 11416 | 0.429169 | `境遇` | `きょうぐう` | `境遇` | `normal_vocab` |  |
| 11673 | 0.432545 | `酒造` | `しゅぞう` | `酒造` | `normal_vocab` |  |
| 12110 | 0.437903 | `平安` | `へいあん` | `平安` | `normal_vocab` |  |
| 12742 | 0.444692 | `先行き` | `さきゆき` | `先行き` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.454 | 9238 | 0.400000 | `会` | `え` | `会` | `rare_or_bound_reading` | score_floor,restricted_admission,rare_or_bound_reading |
| 2.451 | 9240 | 0.400000 | `夜中` | `やちゅう` | `夜中` | `rare_or_formal_reading` | score_floor,restricted_admission,rare_or_formal_reading |
| 2.450 | 9239 | 0.400000 | `土産` | `どさん` | `土産` | `variant_or_compound_reading` | score_floor,restricted_admission,variant_or_compound_reading |
| 2.447 | 9245 | 0.400000 | `現場` | `げんじょう` | `現場` | `variant_reading` | score_floor,restricted_admission,variant_reading |
| 2.440 | 9249 | 0.400000 | `鼠` | `ねず` | `鼠` | `bound_or_variant_reading` | score_floor,restricted_admission,bound_or_variant_reading |
| 2.403 | 9242 | 0.400000 | `山` | `さん` | `山` | `compound_or_on_reading` | score_floor,restricted_admission,compound_or_on_reading |
| 2.240 | 9237 | 0.400000 | `一言` | `いちげん` | `一言` | `variant_reading` | score_floor,restricted_admission,variant_reading |
| 2.202 | 9241 | 0.400000 | `女子` | `おなご` | `女子` | `normal_vocab` | score_floor |

## Band 0.45-0.50 (4805 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 13177 | 0.450028 | `乗馬` | `じょうば` | `乗馬` | `normal_vocab` |  |
| 13415 | 0.452606 | `ジャンキー` | `じゃんきー` | `ジャンキー` | `normal_vocab` |  |
| 13590 | 0.454446 | `川柳` | `せんりゅう` | `川柳` | `normal_vocab` |  |
| 14115 | 0.460107 | `男優` | `だんゆう` | `男優` | `normal_vocab` |  |
| 14343 | 0.462429 | `行き止まり` | `いきどまり` | `行き止まり` | `normal_vocab` |  |
| 14753 | 0.466616 | `戒め` | `いましめ` | `戒め` | `normal_vocab` |  |
| 15344 | 0.472571 | `損得` | `そんとく` | `損得` | `normal_vocab` |  |
| 15592 | 0.475192 | `配電` | `はいでん` | `配電` | `normal_vocab` |  |
| 16843 | 0.488390 | `モモ` | `もも` | `モモ` | `deprioritized_vocab` |  |
| 16956 | 0.489621 | `主著` | `しゅちょ` | `主著` | `normal_vocab` |  |
| 17201 | 0.492333 | `疾い` | `とい` | `疾い` | `normal_vocab` |  |
| 17345 | 0.493802 | `世銀` | `せぎん` | `世銀` | `deprioritized_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.192 | 13171 | 0.450000 | `必用` | `ひつよう` | `必用` | `orthographic_variant` | score_floor,restricted_admission,orthographic_variant |
| 2.178 | 13168 | 0.450000 | `伍` | `ご` | `伍` | `rare_or_military_reading` | score_floor,restricted_admission,rare_or_military_reading |
| 2.100 | 13163 | 0.450000 | `暇` | `いとま` | `暇` | `normal_vocab` | score_floor |
| 2.093 | 13172 | 0.450000 | `雷` | `いかずち` | `雷` | `normal_vocab` | score_floor |
| 2.019 | 13162 | 0.450000 | `仏` | `ぶつ` | `仏` | `compound_or_on_reading` | score_floor,restricted_admission,compound_or_on_reading |
| 1.994 | 13170 | 0.450000 | `奴` | `やっこ` | `奴` | `normal_vocab` | score_floor |
| 1.855 | 13164 | 0.450000 | `根` | `こん` | `根` | `compound_or_on_reading` | score_floor,restricted_admission,compound_or_on_reading |
| 1.793 | 13167 | 0.450000 | `長` | `おさ` | `長` | `normal_vocab` | score_floor |

## Band 0.50-0.55 (5177 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 18469 | 0.504770 | `病患` | `びょうかん` | `病患` | `normal_vocab` |  |
| 18553 | 0.505573 | `着信` | `ちゃくしん` | `着信` | `normal_vocab` |  |
| 19298 | 0.512759 | `真冬` | `まふゆ` | `真冬` | `normal_vocab` |  |
| 19609 | 0.515819 | `木陰` | `こかげ` | `木陰` | `normal_vocab` |  |
| 19820 | 0.517863 | `本道` | `ほんどう` | `本道` | `normal_vocab` |  |
| 20025 | 0.519838 | `先般` | `せんぱん` | `先般` | `normal_vocab` |  |
| 20185 | 0.521397 | `紺屋` | `こうや` | `紺屋` | `normal_vocab` |  |
| 20403 | 0.523509 | `肌寒い` | `はださむい` | `肌寒い` | `normal_vocab` |  |
| 20804 | 0.527402 | `朝市` | `あさいち` | `朝市` | `normal_vocab` |  |
| 20898 | 0.528312 | `空冷` | `くうれい` | `空冷` | `normal_vocab` |  |
| 21040 | 0.529678 | `大敵` | `たいてき` | `大敵` | `normal_vocab` |  |
| 21153 | 0.530762 | `大蛇` | `だいじゃ` | `大蛇` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.100 | 17967 | 0.500000 | `東` | `あずま` | `東` | `normal_vocab` | score_floor |
| 1.000 | 22300 | 0.541841 | `盲` | `めくら` | `盲` | `normal_vocab` |  |
| 0.908 | 17992 | 0.500245 | `強い` | `こわい` | `強い` | `normal_vocab` |  |
| 0.906 | 18851 | 0.508445 | `塵` | `ちり` | `塵` | `normal_vocab` |  |
| 0.904 | 18341 | 0.503530 | `脚色` | `あしいろ` | `脚色` | `normal_vocab` |  |
| 0.850 | 19069 | 0.510541 | `訪う` | `とう` | `訪う` | `normal_vocab` |  |
| 0.850 | 18842 | 0.508362 | `悠悠` | `ゆうゆう` | `悠悠` | `deprioritized_vocab` |  |
| 0.844 | 18808 | 0.508033 | `日影` | `ひかげ` | `日影` | `normal_vocab` |  |

## Band 0.55-0.60 (5902 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 23485 | 0.552886 | `生薬` | `きぐすり` | `生薬` | `normal_vocab` |  |
| 24191 | 0.558860 | `低俗` | `ていぞく` | `低俗` | `normal_vocab` |  |
| 24417 | 0.560767 | `棋譜` | `きふ` | `棋譜` | `normal_vocab` |  |
| 24570 | 0.562064 | `挽歌` | `ばんか` | `挽歌` | `normal_vocab` |  |
| 24889 | 0.564742 | `幕の内` | `まくのうち` | `幕の内` | `normal_vocab` |  |
| 24942 | 0.565191 | `燃え広がる` | `もえひろがる` | `燃え広がる` | `normal_vocab` |  |
| 25013 | 0.565792 | `作劇` | `さくげき` | `作劇` | `normal_vocab` |  |
| 25322 | 0.568403 | `旧版` | `きゅうはん` | `旧版` | `normal_vocab` |  |
| 26563 | 0.578928 | `ジ` | `じ` | `ジ` | `normal_vocab` |  |
| 26952 | 0.582233 | `絡める` | `からめる` | `絡める` | `normal_vocab` |  |
| 28138 | 0.592292 | `大夫` | `たいふ` | `大夫` | `normal_vocab` |  |
| 28428 | 0.594758 | `ブランディング` | `ぶらんでぃんぐ` | `ブランディング` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 24053 | 0.557691 | `盲` | `めしい` | `盲` | `normal_vocab` |  |
| 1.000 | 27009 | 0.582716 | `項` | `うなじ` | `項` | `normal_vocab` |  |
| 1.000 | 28313 | 0.593784 | `然り` | `さり` | `然り` | `normal_vocab` |  |
| 0.991 | 27214 | 0.584462 | `故` | `け` | `故` | `normal_vocab` |  |
| 0.850 | 27230 | 0.584597 | `空き間` | `あきま` | `空き間` | `normal_vocab` |  |
| 0.850 | 27234 | 0.584623 | `豪気` | `ごうぎ` | `豪気` | `normal_vocab` |  |
| 0.849 | 27199 | 0.584335 | `勃々` | `ぼつぼつ` | `勃々` | `normal_vocab` |  |
| 0.845 | 26678 | 0.579911 | `や行` | `やぎょう` | `や行` | `normal_vocab` |  |

## Band 0.60-0.65 (4383 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 29165 | 0.601429 | `食い付く` | `くいつく` | `食い付く` | `normal_vocab` |  |
| 29631 | 0.606873 | `べとべと` | `べとべと` | `べとべと` | `normal_vocab` |  |
| 29851 | 0.609435 | `雀蜂` | `すずめばち` | `雀蜂` | `normal_vocab` |  |
| 29926 | 0.610302 | `功利` | `こうり` | `功利` | `normal_vocab` |  |
| 30774 | 0.620079 | `ぎくり` | `ぎくり` | `ぎくり` | `normal_vocab` |  |
| 30775 | 0.620091 | `とにもかくにも` | `とにもかくにも` | `とにもかくにも` | `normal_vocab` |  |
| 31129 | 0.624004 | `端折る` | `はしょる` | `端折る` | `normal_vocab` |  |
| 32517 | 0.639783 | `正徳` | `しょうとく` | `正徳` | `deprioritized_vocab` |  |
| 32578 | 0.640469 | `酢豚` | `すぶた` | `酢豚` | `normal_vocab` |  |
| 32594 | 0.640649 | `ばっくれる` | `ばっくれる` | `ばっくれる` | `normal_vocab` |  |
| 32717 | 0.642042 | `げんなり` | `げんなり` | `げんなり` | `normal_vocab` |  |
| 32728 | 0.642165 | `ソマリア` | `そまりあ` | `ソマリア` | `deprioritized_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 30305 | 0.614674 | `女` | `め` | `女` | `normal_vocab` |  |
| 1.000 | 31210 | 0.624928 | `心` | `しん` | `心` | `normal_vocab` |  |
| 1.000 | 30925 | 0.621778 | `林` | `りん` | `林` | `normal_vocab` |  |
| 1.000 | 30928 | 0.621810 | `水道` | `みずみち` | `水道` | `normal_vocab` |  |
| 0.996 | 30907 | 0.621588 | `石` | `せき` | `石` | `normal_vocab` |  |
| 0.991 | 30935 | 0.621884 | `正しい` | `まさしい` | `正しい` | `normal_vocab` |  |
| 0.853 | 31290 | 0.625821 | `人形` | `ひとがた` | `人形` | `normal_vocab` |  |
| 0.550 | 31030 | 0.622923 | `ゆめ` | `ゆめ` | `ゆめ` | `normal_vocab` |  |

## Band 0.65-0.70 (4901 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 33510 | 0.650903 | `株高` | `かぶだか` | `株高` | `normal_vocab` |  |
| 33573 | 0.651604 | `雑い` | `ざつい` | `雑い` | `normal_vocab` |  |
| 33963 | 0.655930 | `溢れ返る` | `あふれかえる` | `溢れ返る` | `normal_vocab` |  |
| 34012 | 0.656472 | `旅籠` | `はたご` | `旅籠` | `normal_vocab` |  |
| 34256 | 0.659167 | `掛け橋` | `かけはし` | `掛け橋` | `normal_vocab` |  |
| 34437 | 0.661162 | `茎葉` | `けいよう` | `茎葉` | `normal_vocab` |  |
| 34545 | 0.662350 | `長針` | `ちょうしん` | `長針` | `normal_vocab` |  |
| 35653 | 0.674431 | `タックス` | `たっくす` | `タックス` | `normal_vocab` |  |
| 35800 | 0.675901 | `鰆` | `さわら` | `鰆` | `normal_vocab` |  |
| 36128 | 0.678968 | `黒線` | `くろせん` | `黒線` | `normal_vocab` |  |
| 36491 | 0.682421 | `魍魎` | `もうりょう` | `魍魎` | `normal_vocab` |  |
| 38312 | 0.699831 | `冷涼` | `れいりょう` | `冷涼` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 35967 | 0.677498 | `白` | `はく` | `白` | `normal_vocab` |  |
| 1.000 | 35977 | 0.677586 | `白` | `しら` | `白` | `normal_vocab` |  |
| 1.000 | 36111 | 0.678818 | `兄` | `けい` | `兄` | `normal_vocab` |  |
| 1.000 | 36121 | 0.678906 | `作文` | `さくもん` | `作文` | `normal_vocab` |  |
| 1.000 | 36925 | 0.686579 | `頭` | `かしら` | `頭` | `normal_vocab` |  |
| 1.000 | 35843 | 0.676304 | `雪` | `せつ` | `雪` | `normal_vocab` |  |
| 1.000 | 36576 | 0.683244 | `潮干` | `しおひる` | `潮干` | `normal_vocab` |  |
| 0.999 | 35813 | 0.676021 | `耳` | `じ` | `耳` | `normal_vocab` |  |

## Band 0.70-0.75 (5506 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 38359 | 0.700277 | `花金` | `はなきん` | `花金` | `normal_vocab` |  |
| 38540 | 0.701992 | `県都` | `けんと` | `県都` | `normal_vocab` |  |
| 38978 | 0.706137 | `靴箱` | `くつばこ` | `靴箱` | `normal_vocab` |  |
| 40577 | 0.721015 | `中忍` | `ちゅうにん` | `中忍` | `normal_vocab` |  |
| 40796 | 0.723038 | `ホチキス` | `ほちきす` | `ホチキス` | `normal_vocab` |  |
| 40827 | 0.723323 | `土性` | `どせい` | `土性` | `normal_vocab` |  |
| 40868 | 0.723701 | `ぐにゃり` | `ぐにゃり` | `ぐにゃり` | `normal_vocab` |  |
| 41976 | 0.733854 | `笄` | `こうがい` | `笄` | `normal_vocab` |  |
| 42166 | 0.735580 | `運上` | `うんじょう` | `運上` | `normal_vocab` |  |
| 42343 | 0.737193 | `甌穴` | `おうけつ` | `甌穴` | `normal_vocab` |  |
| 43100 | 0.744013 | `マモン` | `まもん` | `マモン` | `normal_vocab` |  |
| 43657 | 0.748548 | `リプトン` | `りぷとん` | `リプトン` | `deprioritized_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 39969 | 0.715391 | `蝮` | `たじひ` | `蝮` | `normal_vocab` |  |
| 0.999 | 40457 | 0.719905 | `広葉` | `ひろは` | `広葉` | `normal_vocab` |  |
| 0.470 | 38904 | 0.705431 | `灯し火` | `ともしび` | `灯し火` | `normal_vocab` |  |
| 0.323 | 38355 | 0.700239 | `入れ子` | `いれこ` | `入れ子` | `normal_vocab` |  |
| 0.323 | 38370 | 0.700381 | `栄` | `さかえ` | `栄` | `normal_vocab` |  |
| 0.323 | 38408 | 0.700741 | `言の葉` | `ことのは` | `言の葉` | `normal_vocab` |  |
| 0.323 | 38443 | 0.701073 | `尤` | `ゆう` | `尤` | `normal_vocab` |  |
| 0.323 | 38463 | 0.701263 | `利生` | `りしょう` | `利生` | `normal_vocab` |  |

## Band 0.75-0.80 (6423 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 44366 | 0.754277 | `宣う` | `のたまう` | `宣う` | `normal_vocab` |  |
| 44942 | 0.758882 | `神州` | `しんしゅう` | `神州` | `normal_vocab` |  |
| 44974 | 0.759138 | `扱き下ろす` | `こきおろす` | `扱き下ろす` | `normal_vocab` |  |
| 45263 | 0.761439 | `冷泉` | `れいせん` | `冷泉` | `normal_vocab` |  |
| 45694 | 0.764858 | `バイカー` | `ばいかー` | `バイカー` | `normal_vocab` |  |
| 46200 | 0.768857 | `紫微` | `しび` | `紫微` | `deprioritized_vocab` |  |
| 46396 | 0.770396 | `グロッグ` | `ぐろっぐ` | `グロッグ` | `normal_vocab` |  |
| 47471 | 0.778766 | `骨化` | `こっか` | `骨化` | `normal_vocab` |  |
| 47848 | 0.781678 | `コミュニカティブ` | `こみゅにかてぃぶ` | `コミュニカティブ` | `normal_vocab` |  |
| 48207 | 0.784438 | `賦存` | `ふそん` | `賦存` | `normal_vocab` |  |
| 48510 | 0.786758 | `オルターナティブ` | `おるたーなてぃぶ` | `オルターナティブ` | `normal_vocab` |  |
| 48632 | 0.787682 | `骨片` | `こっぺん` | `骨片` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.543 | 46621 | 0.772159 | `螺子回し` | `ねじまわし` | `螺子回し` | `normal_vocab` |  |
| 0.536 | 47491 | 0.778921 | `御酒` | `みき` | `御酒` | `normal_vocab` |  |
| 0.522 | 48471 | 0.786460 | `頽れる` | `くずおれる` | `頽れる` | `normal_vocab` |  |
| 0.323 | 43875 | 0.750320 | `冠者` | `かじゃ` | `冠者` | `normal_vocab` |  |
| 0.323 | 43936 | 0.750813 | `叟` | `そう` | `叟` | `normal_vocab` |  |
| 0.323 | 43957 | 0.750982 | `暑気` | `しょき` | `暑気` | `normal_vocab` |  |
| 0.323 | 44079 | 0.751967 | `紅毛` | `こうもう` | `紅毛` | `normal_vocab` |  |
| 0.323 | 44096 | 0.752104 | `そやす` | `そやす` | `そやす` | `normal_vocab` |  |

## Band 0.80-0.85 (7566 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 50337 | 0.800593 | `寛保` | `かんぽう` | `寛保` | `deprioritized_vocab` |  |
| 50498 | 0.801808 | `直衣` | `のうし` | `直衣` | `normal_vocab` |  |
| 50581 | 0.802426 | `喀血` | `かっけつ` | `喀血` | `normal_vocab` |  |
| 52574 | 0.816263 | `墨流し` | `すみながし` | `墨流し` | `normal_vocab` |  |
| 52740 | 0.817365 | `隠秘` | `いんぴ` | `隠秘` | `normal_vocab` |  |
| 54653 | 0.829924 | `計時` | `けいじ` | `計時` | `normal_vocab` |  |
| 54779 | 0.830738 | `キャパシター` | `きゃぱしたー` | `キャパシター` | `normal_vocab` |  |
| 54794 | 0.830834 | `コンベンショナル` | `こんべんしょなる` | `コンベンショナル` | `normal_vocab` |  |
| 54966 | 0.831943 | `塩湯` | `しおゆ` | `塩湯` | `normal_vocab` |  |
| 56636 | 0.842590 | `馬市` | `うまいち` | `馬市` | `normal_vocab` |  |
| 57387 | 0.847288 | `雁皮` | `がんぴ` | `雁皮` | `normal_vocab` |  |
| 57822 | 0.849987 | `戦塵` | `せんじん` | `戦塵` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.546 | 57643 | 0.848878 | `僊` | `せん` | `僊` | `normal_vocab` |  |
| 0.545 | 56621 | 0.842495 | `隷` | `れい` | `隷` | `normal_vocab` |  |
| 0.322 | 50976 | 0.805356 | `方偏` | `かたへん` | `方偏` | `normal_vocab` |  |
| 0.322 | 54267 | 0.827409 | `居玉` | `いぎょく` | `居玉` | `normal_vocab` |  |
| 0.322 | 56730 | 0.843179 | `熱り` | `いきり` | `熱り` | `normal_vocab` |  |
| 0.322 | 52204 | 0.813785 | `涙型` | `なみだがた` | `涙型` | `normal_vocab` |  |
| 0.322 | 52767 | 0.817544 | `内苑` | `ないえん` | `内苑` | `normal_vocab` |  |
| 0.321 | 51302 | 0.807702 | `イソソルビド` | `いそそるびど` | `イソソルビド` | `normal_vocab` |  |

## Band 0.85-0.90 (7569 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 59995 | 0.863243 | `糸瓜水` | `へちますい` | `糸瓜水` | `normal_vocab` |  |
| 60690 | 0.868171 | `勅裁` | `ちょくさい` | `勅裁` | `normal_vocab` |  |
| 60731 | 0.868462 | `呼び上げる` | `よびあげる` | `呼び上げる` | `normal_vocab` |  |
| 61932 | 0.876883 | `仏土` | `ぶつど` | `仏土` | `normal_vocab` |  |
| 62202 | 0.878745 | `峻峭` | `しゅんしょう` | `峻峭` | `normal_vocab` |  |
| 62318 | 0.879549 | `指穴` | `ゆびあな` | `指穴` | `normal_vocab` |  |
| 62387 | 0.880023 | `本藍` | `ほんあい` | `本藍` | `normal_vocab` |  |
| 63022 | 0.884340 | `駐仏` | `ちゅうふつ` | `駐仏` | `normal_vocab` |  |
| 63494 | 0.887512 | `僻陬` | `へきすう` | `僻陬` | `normal_vocab` |  |
| 63895 | 0.890187 | `抜き出る` | `ぬきでる` | `抜き出る` | `normal_vocab` |  |
| 64090 | 0.891479 | `河系` | `かけい` | `河系` | `normal_vocab` |  |
| 65094 | 0.898061 | `ダンデライオン` | `だんでらいおん` | `ダンデライオン` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.322 | 64865 | 0.896575 | `けつまんこ` | `けつまんこ` | `けつまんこ` | `sensitive_or_adult_vocab` | restricted_admission,sensitive_or_adult_vocab |
| 0.322 | 61342 | 0.872768 | `好き好み` | `すきこのみ` | `好き好み` | `normal_vocab` |  |
| 0.322 | 62886 | 0.883423 | `いちびる` | `いちびる` | `いちびる` | `normal_vocab` |  |
| 0.322 | 64849 | 0.896465 | `古祠` | `こし` | `古祠` | `normal_vocab` |  |
| 0.322 | 64850 | 0.896471 | `小過` | `しょうか` | `小過` | `normal_vocab` |  |
| 0.322 | 64853 | 0.896491 | `い段` | `いだん` | `い段` | `normal_vocab` |  |
| 0.322 | 64855 | 0.896504 | `え段` | `えだん` | `え段` | `normal_vocab` |  |
| 0.322 | 64861 | 0.896549 | `きらず` | `きらず` | `きらず` | `normal_vocab` |  |

## Band 0.90-0.95 (6004 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 65811 | 0.902674 | `弾ずる` | `だんずる` | `弾ずる` | `normal_vocab` |  |
| 66232 | 0.905347 | `焦がれ死に` | `こがれじに` | `焦がれ死に` | `normal_vocab` |  |
| 66449 | 0.906711 | `糞転がし` | `ふんころがし` | `糞転がし` | `normal_vocab` |  |
| 66542 | 0.907293 | `肉月` | `にくづき` | `肉月` | `normal_vocab` |  |
| 66868 | 0.909330 | `隊旗` | `たいき` | `隊旗` | `normal_vocab` |  |
| 67067 | 0.910581 | `なむなむ` | `なむなむ` | `なむなむ` | `normal_vocab` |  |
| 67590 | 0.914640 | `レベニュー` | `れべにゅー` | `レベニュー` | `normal_vocab` |  |
| 67935 | 0.918117 | `卵肌` | `たまごはだ` | `卵肌` | `normal_vocab` |  |
| 68474 | 0.923451 | `探り箸` | `さぐりばし` | `探り箸` | `normal_vocab` |  |
| 68675 | 0.925400 | `毀傷` | `きしょう` | `毀傷` | `normal_vocab` |  |
| 69068 | 0.929177 | `突き殺す` | `つつきころす` | `突き殺す` | `normal_vocab` |  |
| 71211 | 0.948427 | `ショービニズム` | `しょーびにずむ` | `ショービニズム` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.550 | 68351 | 0.922249 | `御蔭` | `みかげ` | `御蔭` | `normal_vocab` |  |
| 0.421 | 69891 | 0.936830 | `御御` | `おごう` | `御御` | `normal_vocab` |  |
| 0.323 | 69969 | 0.937539 | `田舎侍` | `いなかざむらい` | `田舎侍` | `normal_vocab` |  |
| 0.323 | 69970 | 0.937548 | `白酒` | `しろざけ` | `白酒` | `normal_vocab` |  |
| 0.323 | 70033 | 0.938118 | `モヒ` | `もひ` | `モヒ` | `normal_vocab` |  |
| 0.323 | 70042 | 0.938199 | `山鼠` | `やまね` | `山鼠` | `normal_vocab` |  |
| 0.323 | 70045 | 0.938226 | `槍持ち` | `やりもち` | `槍持ち` | `normal_vocab` |  |
| 0.323 | 70046 | 0.938235 | `篤農` | `とくのう` | `篤農` | `normal_vocab` |  |

## Band 0.95-1.00 (2355 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 71460 | 0.950520 | `ダズン` | `だずん` | `ダズン` | `normal_vocab` |  |
| 72006 | 0.958241 | `ファルファッレ` | `ふぁるふぁっれ` | `ファルファッレ` | `normal_vocab` |  |
| 72015 | 0.958453 | `ファージ` | `ふぁーじ` | `ファージ` | `normal_vocab` |  |
| 72321 | 0.965426 | `マイカ` | `まいか` | `マイカ` | `normal_vocab` |  |
| 72597 | 0.971316 | `レジューム` | `れじゅーむ` | `レジューム` | `normal_vocab` |  |
| 72730 | 0.974012 | `優婆塞` | `うばそく` | `優婆塞` | `normal_vocab` |  |
| 73017 | 0.979537 | `恬` | `てん` | `恬` | `normal_vocab` |  |
| 73298 | 0.985263 | `生年` | `しょうねん` | `生年` | `normal_vocab` |  |
| 73439 | 0.991700 | `胴中` | `どうなか` | `胴中` | `normal_vocab` |  |
| 73508 | 0.994346 | `蠱` | `こ` | `蠱` | `normal_vocab` |  |
| 73539 | 0.995414 | `訪い` | `おとない` | `訪い` | `normal_vocab` |  |
| 73575 | 0.996550 | `転び出る` | `ころびでる` | `転び出る` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.323 | 71401 | 0.950027 | `セーミ` | `せーみ` | `セーミ` | `normal_vocab` |  |
| 0.323 | 71405 | 0.950061 | `ゼンチョ` | `ぜんちょ` | `ゼンチョ` | `normal_vocab` |  |
| 0.323 | 71460 | 0.950520 | `ダズン` | `だずん` | `ダズン` | `normal_vocab` |  |
| 0.323 | 71506 | 0.950904 | `チョベリバ` | `ちょべりば` | `チョベリバ` | `normal_vocab` |  |
| 0.323 | 71549 | 0.951261 | `テレグラム` | `てれぐらむ` | `テレグラム` | `normal_vocab` |  |
| 0.323 | 71586 | 0.951568 | `デキストロース` | `できすとろーす` | `デキストロース` | `normal_vocab` |  |
| 0.323 | 71686 | 0.952393 | `ドミンゴ` | `どみんご` | `ドミンゴ` | `normal_vocab` |  |
| 0.323 | 71706 | 0.952558 | `ナタル` | `なたる` | `ナタル` | `normal_vocab` |  |
