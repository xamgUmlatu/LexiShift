# en-ja Learner Difficulty Full-Range Sampling Review

Source: `core/lexishift_core/resources/srs/en_ja/learner_difficulty_corrected.csv`
Seed: `20260630`
Method: deterministic random sample of up to 8 rows per 0.05 score band, plus up to 5 mechanically risk-ranked rows per band. Risk rows are not handpicked; they combine manual-correction presence, review flags, same-surface risk, tail/suspicion signals, and normalized-only JLPT support.

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
| 9 | 0.005000 | `いい` | `いい` | `いい` | `normal_vocab` | score_override |
| 39 | 0.018694 | `置く` | `おく` | `置く` | `normal_vocab` | early_kana_preferred_kanji |
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

## Band 0.05-0.10 (284 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 120 | 0.052627 | `飲む` | `のむ` | `飲む` | `normal_vocab` |  |
| 137 | 0.055678 | `下` | `した` | `下` | `normal_vocab` |  |
| 185 | 0.064322 | `大変` | `たいへん` | `大変` | `normal_vocab` |  |
| 209 | 0.068390 | `鳥` | `とり` | `鳥` | `normal_vocab` |  |
| 210 | 0.068559 | `春` | `はる` | `春` | `normal_vocab` |  |
| 228 | 0.071610 | `有名` | `ゆうめい` | `有名` | `normal_vocab` |  |
| 285 | 0.081271 | `テーブル` | `てーぶる` | `テーブル` | `normal_vocab` |  |
| 287 | 0.081610 | `痛い` | `いたい` | `痛い` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.647 | 387 | 0.099407 | `鞄` | `かばん` | `かばん` | `normal_vocab` | display_only,early_kana_preferred_kanji,normalized_only_jlpt |
| 1.565 | 276 | 0.080000 | `良い` | `よい` | `良い` | `normal_vocab` | score_floor,normalized_only_jlpt |
| 1.153 | 277 | 0.080000 | `ワイシャツ` | `わいしゃつ` | `ワイシャツ` | `normal_vocab` | score_floor |
| 1.150 | 235 | 0.073136 | `家` | `うち` | `うち` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 1.150 | 257 | 0.076864 | `御飯` | `ごはん` | `ご飯` | `normal_vocab` | display_only,early_kana_preferred_kanji |

## Band 0.10-0.15 (495 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 420 | 0.102585 | `毎年` | `まいねん` | `毎年` | `normal_vocab` |  |
| 494 | 0.111992 | `花瓶` | `かびん` | `花瓶` | `normal_vocab` |  |
| 560 | 0.122585 | `分` | `ぶん` | `分` | `normal_vocab` |  |
| 568 | 0.123517 | `プレゼント` | `ぷれぜんと` | `プレゼント` | `normal_vocab` |  |
| 627 | 0.128771 | `過ぎる` | `すぎる` | `過ぎる` | `normal_vocab` | early_kana_preferred_kanji |
| 702 | 0.134788 | `音` | `おと` | `音` | `normal_vocab` |  |
| 715 | 0.135805 | `中々` | `なかなか` | `なかなか` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 728 | 0.136822 | `娘` | `むすめ` | `娘` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.544 | 455 | 0.106059 | `開く` | `あく` | `開く` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.499 | 487 | 0.110042 | `黄色` | `おうしょく` | `黄色` | `formal_or_on_reading` | restricted_admission,formal_or_on_reading |
| 1.484 | 505 | 0.116144 | `温い` | `ぬるい` | `ぬるい` | `normal_vocab` | display_only,early_kana_preferred_kanji |
| 1.389 | 460 | 0.106568 | `明日` | `あした` | `明日` | `normal_vocab` | early_same_surface_risk |
| 1.377 | 535 | 0.120000 | `他` | `た` | `他` | `compound_or_formal_reading` | score_floor,restricted_admission,early_kana_preferred_kanji,compound_or_formal_reading |

## Band 0.15-0.20 (798 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1087 | 0.164661 | `時` | `とき` | `時` | `normal_vocab` |  |
| 1192 | 0.171328 | `インド` | `いんど` | `インド` | `deprioritized_vocab` |  |
| 1331 | 0.179520 | `ニーズ` | `にーず` | `ニーズ` | `normal_vocab` |  |
| 1406 | 0.183983 | `メリット` | `めりっと` | `メリット` | `normal_vocab` |  |
| 1503 | 0.189407 | `主義` | `しゅぎ` | `主義` | `normal_vocab` |  |
| 1508 | 0.189689 | `協力` | `きょうりょく` | `協力` | `normal_vocab` |  |
| 1598 | 0.194944 | `サークル` | `さーくる` | `サークル` | `normal_vocab` |  |
| 1673 | 0.199407 | `マナー` | `まなー` | `マナー` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.338 | 1340 | 0.180000 | `後` | `のち` | `後` | `normal_vocab` | score_floor,early_kana_preferred_kanji |
| 1.330 | 1256 | 0.175169 | `或いは` | `あるいは` | `あるいは` | `normal_vocab` | display_only,manual_watchlist,early_kana_preferred_kanji |
| 1.239 | 1307 | 0.178164 | `様` | `さま` | `様` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |
| 1.185 | 1267 | 0.175781 | `火` | `か` | `火` | `compound_or_on_reading` | restricted_admission,compound_or_on_reading |
| 1.178 | 1029 | 0.158446 | `都` | `みやこ` | `都` | `normal_vocab` | early_same_surface_risk |

## Band 0.20-0.25 (1226 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1797 | 0.204809 | `ニット` | `にっと` | `ニット` | `normal_vocab` |  |
| 1851 | 0.207140 | `直接` | `ちょくせつ` | `直接` | `normal_vocab` |  |
| 2106 | 0.218199 | `ドリンク` | `どりんく` | `ドリンク` | `normal_vocab` |  |
| 2189 | 0.221081 | `電子` | `でんし` | `電子` | `normal_vocab` |  |
| 2227 | 0.222691 | `設計` | `せっけい` | `設計` | `normal_vocab` |  |
| 2598 | 0.237648 | `従来` | `じゅうらい` | `従来` | `normal_vocab` |  |
| 2761 | 0.243919 | `売れる` | `うれる` | `売れる` | `normal_vocab` |  |
| 2767 | 0.244174 | `キャンプ` | `きゃんぷ` | `キャンプ` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 3.610 | 2164 | 0.220000 | `入り口` | `いりくち` | `入り口` | `variant_reading` | score_floor,restricted_admission,early_same_surface_risk,normalized_only_jlpt,variant_reading |
| 2.954 | 2166 | 0.220000 | `君` | `くん` | `君` | `suffix_or_title_reading` | score_floor,restricted_admission,early_same_surface_risk,suffix_or_title_reading |
| 2.950 | 2165 | 0.220000 | `南` | `なん` | `南` | `compound_reading` | score_floor,restricted_admission,early_same_surface_risk,compound_reading |
| 2.573 | 2162 | 0.220000 | `塩` | `えん` | `塩` | `compound_or_on_reading` | score_floor,restricted_admission,early_same_surface_risk,compound_or_on_reading |
| 2.550 | 2320 | 0.226526 | `東` | `とう` | `東` | `compound_or_directional_reading` | restricted_admission,early_same_surface_risk,compound_or_directional_reading |

## Band 0.25-0.30 (1312 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3352 | 0.263610 | `騒音` | `そうおん` | `騒音` | `normal_vocab` |  |
| 3403 | 0.265244 | `値` | `ね` | `値` | `normal_vocab` |  |
| 3430 | 0.266199 | `凍る` | `こおる` | `凍る` | `normal_vocab` |  |
| 3471 | 0.267833 | `綿` | `わた` | `綿` | `normal_vocab` | early_kana_preferred_kanji |
| 3498 | 0.268850 | `敬意` | `けいい` | `敬意` | `normal_vocab` |  |
| 3519 | 0.270022 | `咳` | `せき` | `咳` | `normal_vocab` |  |
| 3960 | 0.291877 | `リビング` | `りびんぐ` | `リビング` | `normal_vocab` |  |
| 4186 | 0.299276 | `プロダクト` | `ぷろだくと` | `プロダクト` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.350 | 4217 | 0.300000 | `上` | `かみ` | `上` | `formal_or_spatial_variant` | score_floor,restricted_admission,formal_or_spatial_variant |
| 2.027 | 4219 | 0.300000 | `打つ` | `ぶつ` | `打つ` | `normal_vocab` | score_floor |
| 1.998 | 4221 | 0.300000 | `包む` | `くるむ` | `包む` | `normal_vocab` | score_floor |
| 1.965 | 4218 | 0.300000 | `魚` | `うお` | `魚` | `normal_vocab` | score_floor |
| 1.950 | 3564 | 0.278345 | `面` | `おも` | `面` | `normal_vocab` | early_kana_preferred_kanji,early_same_surface_risk |

## Band 0.30-0.35 (1940 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 4677 | 0.311308 | `移行` | `いこう` | `移行` | `normal_vocab` |  |
| 4711 | 0.312189 | `聖書` | `せいしょ` | `聖書` | `normal_vocab` |  |
| 4757 | 0.313319 | `引き上げる` | `ひきあげる` | `引き上げる` | `normal_vocab` |  |
| 4761 | 0.313455 | `並び` | `ならび` | `並び` | `normal_vocab` |  |
| 4868 | 0.316166 | `圧力` | `あつりょく` | `圧力` | `normal_vocab` |  |
| 5177 | 0.324232 | `乗り越える` | `のりこえる` | `乗り越える` | `normal_vocab` |  |
| 5704 | 0.338127 | `品種` | `ひんしゅ` | `品種` | `normal_vocab` |  |
| 5867 | 0.342239 | `行使` | `こうし` | `行使` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.547 | 6160 | 0.350000 | `昼間` | `ちゅうかん` | `昼間` | `variant_reading` | score_floor,restricted_admission,variant_reading |
| 2.546 | 6152 | 0.350000 | `丈夫` | `じょうふ` | `丈夫` | `rare_reading` | score_floor,restricted_admission,rare_reading |
| 2.541 | 6156 | 0.350000 | `字` | `あざ` | `字` | `rare_or_place_reading` | score_floor,restricted_admission,rare_or_place_reading |
| 2.300 | 6155 | 0.350000 | `僕` | `しもべ` | `僕` | `normal_vocab` | score_floor |
| 2.300 | 6158 | 0.350000 | `工場` | `こうば` | `工場` | `normal_vocab` | score_floor |

## Band 0.35-0.40 (3072 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 6168 | 0.350093 | `歩行` | `ほこう` | `歩行` | `normal_vocab` |  |
| 6824 | 0.364008 | `突く` | `つつく` | `突く` | `normal_vocab` |  |
| 7228 | 0.373263 | `電動` | `でんどう` | `電動` | `normal_vocab` |  |
| 7236 | 0.373568 | `誠実` | `せいじつ` | `誠実` | `normal_vocab` |  |
| 7340 | 0.375890 | `造形` | `ぞうけい` | `造形` | `normal_vocab` |  |
| 8640 | 0.393398 | `列島` | `れっとう` | `列島` | `normal_vocab` |  |
| 8674 | 0.393694 | `ファクター` | `ふぁくたー` | `ファクター` | `normal_vocab` |  |
| 8798 | 0.394873 | `移籍` | `いせき` | `移籍` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.061 | 7772 | 0.385866 | `妙` | `たえ` | `妙` | `normal_vocab` |  |
| 1.050 | 8325 | 0.390246 | `代` | `よ` | `代` | `normal_vocab` |  |
| 1.049 | 7469 | 0.379127 | `自修` | `じしゅう` | `自修` | `normal_vocab` |  |
| 1.000 | 8998 | 0.397094 | `主` | `あるじ` | `主` | `normal_vocab` |  |
| 0.963 | 9230 | 0.399941 | `冠` | `かんむり` | `冠` | `normal_vocab` |  |

## Band 0.40-0.45 (3928 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 9275 | 0.400305 | `経理` | `けいり` | `経理` | `normal_vocab` |  |
| 10452 | 0.416425 | `農園` | `のうえん` | `農園` | `normal_vocab` |  |
| 10563 | 0.417889 | `しなやか` | `しなやか` | `しなやか` | `normal_vocab` |  |
| 11335 | 0.428044 | `滑稽` | `こっけい` | `滑稽` | `normal_vocab` |  |
| 12567 | 0.442510 | `曲目` | `きょくもく` | `曲目` | `normal_vocab` |  |
| 12724 | 0.444503 | `風通し` | `かぜとおし` | `風通し` | `normal_vocab` |  |
| 13139 | 0.449695 | `甘やかす` | `あまやかす` | `甘やかす` | `normal_vocab` |  |
| 13141 | 0.449722 | `発着` | `はっちゃく` | `発着` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.454 | 9238 | 0.400000 | `会` | `え` | `会` | `rare_or_bound_reading` | score_floor,restricted_admission,rare_or_bound_reading |
| 2.451 | 9240 | 0.400000 | `夜中` | `やちゅう` | `夜中` | `rare_or_formal_reading` | score_floor,restricted_admission,rare_or_formal_reading |
| 2.450 | 9239 | 0.400000 | `土産` | `どさん` | `土産` | `variant_or_compound_reading` | score_floor,restricted_admission,variant_or_compound_reading |
| 2.447 | 9245 | 0.400000 | `現場` | `げんじょう` | `現場` | `variant_reading` | score_floor,restricted_admission,variant_reading |
| 2.440 | 9249 | 0.400000 | `鼠` | `ねず` | `鼠` | `bound_or_variant_reading` | score_floor,restricted_admission,bound_or_variant_reading |

## Band 0.45-0.50 (4805 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 13862 | 0.457316 | `荷台` | `にだい` | `荷台` | `normal_vocab` |  |
| 14166 | 0.460605 | `総勢` | `そうぜい` | `総勢` | `normal_vocab` |  |
| 14275 | 0.461723 | `所々` | `しょしょ` | `所々` | `normal_vocab` |  |
| 14835 | 0.467407 | `前述` | `ぜんじゅつ` | `前述` | `normal_vocab` |  |
| 14921 | 0.468288 | `委嘱` | `いしょく` | `委嘱` | `normal_vocab` |  |
| 14977 | 0.468864 | `味の素` | `あじのもと` | `味の素` | `deprioritized_vocab` |  |
| 16111 | 0.480458 | `ポニーテール` | `ぽにーてーる` | `ポニーテール` | `normal_vocab` |  |
| 17434 | 0.494695 | `丹精` | `たんせい` | `丹精` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.192 | 13171 | 0.450000 | `必用` | `ひつよう` | `必用` | `orthographic_variant` | score_floor,restricted_admission,orthographic_variant |
| 2.178 | 13168 | 0.450000 | `伍` | `ご` | `伍` | `rare_or_military_reading` | score_floor,restricted_admission,rare_or_military_reading |
| 2.100 | 13163 | 0.450000 | `暇` | `いとま` | `暇` | `normal_vocab` | score_floor |
| 2.093 | 13172 | 0.450000 | `雷` | `いかずち` | `雷` | `normal_vocab` | score_floor |
| 2.019 | 13162 | 0.450000 | `仏` | `ぶつ` | `仏` | `compound_or_on_reading` | score_floor,restricted_admission,compound_or_on_reading |

## Band 0.50-0.55 (5177 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 18927 | 0.509186 | `担ぎ` | `かつぎ` | `担ぎ` | `normal_vocab` |  |
| 18978 | 0.509660 | `自任` | `じにん` | `自任` | `normal_vocab` |  |
| 19272 | 0.512507 | `目抜き` | `めぬき` | `目抜き` | `normal_vocab` |  |
| 19287 | 0.512653 | `主計` | `かずえ` | `主計` | `normal_vocab` |  |
| 19527 | 0.515006 | `光源` | `こうげん` | `光源` | `normal_vocab` |  |
| 20135 | 0.520913 | `ゲルマン` | `げるまん` | `ゲルマン` | `normal_vocab` |  |
| 22037 | 0.539304 | `舌触り` | `したざわり` | `舌触り` | `normal_vocab` |  |
| 22286 | 0.541705 | `恥辱` | `ちじょく` | `恥辱` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 2.100 | 17967 | 0.500000 | `東` | `あずま` | `東` | `normal_vocab` | score_floor |
| 1.000 | 22300 | 0.541841 | `盲` | `めくら` | `盲` | `normal_vocab` |  |
| 0.908 | 17992 | 0.500245 | `強い` | `こわい` | `強い` | `normal_vocab` |  |
| 0.906 | 18851 | 0.508445 | `塵` | `ちり` | `塵` | `normal_vocab` |  |
| 0.904 | 18341 | 0.503530 | `脚色` | `あしいろ` | `脚色` | `normal_vocab` |  |

## Band 0.55-0.60 (5902 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 23263 | 0.551021 | `勝ち残る` | `かちのこる` | `勝ち残る` | `normal_vocab` |  |
| 26122 | 0.575157 | `鉦` | `しょう` | `鉦` | `normal_vocab` |  |
| 26175 | 0.575606 | `横組み` | `よこぐみ` | `横組み` | `normal_vocab` |  |
| 27604 | 0.587758 | `見知り` | `みしり` | `見知り` | `normal_vocab` |  |
| 27729 | 0.588826 | `光量` | `こうりょう` | `光量` | `normal_vocab` |  |
| 28126 | 0.592191 | `回り込む` | `まわりこむ` | `回り込む` | `normal_vocab` |  |
| 28828 | 0.598165 | `ウベ` | `うべ` | `ウベ` | `deprioritized_vocab` |  |
| 28990 | 0.599538 | `議` | `ぎ` | `議` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 24053 | 0.557691 | `盲` | `めしい` | `盲` | `normal_vocab` |  |
| 1.000 | 27009 | 0.582716 | `項` | `うなじ` | `項` | `normal_vocab` |  |
| 1.000 | 28313 | 0.593784 | `然り` | `さり` | `然り` | `normal_vocab` |  |
| 0.991 | 27214 | 0.584462 | `故` | `け` | `故` | `normal_vocab` |  |
| 0.850 | 27230 | 0.584597 | `空き間` | `あきま` | `空き間` | `normal_vocab` |  |

## Band 0.60-0.65 (4383 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 29985 | 0.610996 | `カルビー` | `かるびー` | `カルビー` | `deprioritized_vocab` |  |
| 30244 | 0.613975 | `目数` | `めかず` | `目数` | `normal_vocab` |  |
| 30469 | 0.616566 | `鹿尾菜` | `ひじき` | `鹿尾菜` | `normal_vocab` |  |
| 31094 | 0.623639 | `丸紅` | `まるべに` | `丸紅` | `deprioritized_vocab` |  |
| 31306 | 0.626001 | `播種` | `はしゅ` | `播種` | `normal_vocab` |  |
| 32230 | 0.636527 | `アレンジメント` | `あれんじめんと` | `アレンジメント` | `normal_vocab` |  |
| 32763 | 0.642569 | `激昂` | `げっこう` | `激昂` | `normal_vocab` |  |
| 32946 | 0.644609 | `委譲` | `いじょう` | `委譲` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 30305 | 0.614674 | `女` | `め` | `女` | `normal_vocab` |  |
| 1.000 | 31210 | 0.624928 | `心` | `しん` | `心` | `normal_vocab` |  |
| 1.000 | 30925 | 0.621778 | `林` | `りん` | `林` | `normal_vocab` |  |
| 1.000 | 30928 | 0.621810 | `水道` | `みずみち` | `水道` | `normal_vocab` |  |
| 0.996 | 30907 | 0.621588 | `石` | `せき` | `石` | `normal_vocab` |  |

## Band 0.65-0.70 (4901 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 33430 | 0.650013 | `稲架` | `はさ` | `稲架` | `normal_vocab` |  |
| 33556 | 0.651415 | `軟質` | `なんしつ` | `軟質` | `normal_vocab` |  |
| 34128 | 0.657754 | `黒む` | `くろむ` | `黒む` | `normal_vocab` |  |
| 35748 | 0.675394 | `頬骨` | `ほおぼね` | `頬骨` | `normal_vocab` |  |
| 36711 | 0.684520 | `遊び人` | `あそびにん` | `遊び人` | `normal_vocab` |  |
| 36934 | 0.686662 | `かごめかごめ` | `かごめかごめ` | `かごめかごめ` | `normal_vocab` |  |
| 37794 | 0.694910 | `端麗` | `たんれい` | `端麗` | `normal_vocab` |  |
| 38308 | 0.699793 | `クラブハウス` | `くらぶはうす` | `クラブハウス` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 35967 | 0.677498 | `白` | `はく` | `白` | `normal_vocab` |  |
| 1.000 | 35977 | 0.677586 | `白` | `しら` | `白` | `normal_vocab` |  |
| 1.000 | 36111 | 0.678818 | `兄` | `けい` | `兄` | `normal_vocab` |  |
| 1.000 | 36121 | 0.678906 | `作文` | `さくもん` | `作文` | `normal_vocab` |  |
| 1.000 | 36925 | 0.686579 | `頭` | `かしら` | `頭` | `normal_vocab` |  |

## Band 0.70-0.75 (5506 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 38345 | 0.700144 | `坪庭` | `つぼにわ` | `坪庭` | `normal_vocab` |  |
| 39283 | 0.708987 | `ビリルビン` | `びりるびん` | `ビリルビン` | `normal_vocab` |  |
| 39921 | 0.714944 | `艦尾` | `かんび` | `艦尾` | `normal_vocab` |  |
| 40512 | 0.720414 | `ラノベ` | `らのべ` | `ラノベ` | `normal_vocab` |  |
| 40760 | 0.722705 | `ワイヤード` | `わいやーど` | `ワイヤード` | `normal_vocab` |  |
| 42011 | 0.734172 | `描出` | `びょうしゅつ` | `描出` | `normal_vocab` |  |
| 42369 | 0.737438 | `黒緑` | `こくりょく` | `黒緑` | `normal_vocab` |  |
| 42513 | 0.738740 | `統監` | `とうかん` | `統監` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.000 | 39969 | 0.715391 | `蝮` | `たじひ` | `蝮` | `normal_vocab` |  |
| 0.999 | 40457 | 0.719905 | `広葉` | `ひろは` | `広葉` | `normal_vocab` |  |
| 0.470 | 38904 | 0.705431 | `灯し火` | `ともしび` | `灯し火` | `normal_vocab` |  |
| 0.323 | 38355 | 0.700239 | `入れ子` | `いれこ` | `入れ子` | `normal_vocab` |  |
| 0.323 | 38370 | 0.700381 | `栄` | `さかえ` | `栄` | `normal_vocab` |  |

## Band 0.75-0.80 (6423 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 44089 | 0.752047 | `過量` | `かりょう` | `過量` | `normal_vocab` |  |
| 44264 | 0.753457 | `入境` | `にゅうきょう` | `入境` | `normal_vocab` |  |
| 45017 | 0.759480 | `晩鐘` | `ばんしょう` | `晩鐘` | `normal_vocab` |  |
| 45167 | 0.760676 | `瓦屋` | `かわらや` | `瓦屋` | `normal_vocab` |  |
| 47630 | 0.779996 | `シグネチャー` | `しぐねちゃー` | `シグネチャー` | `normal_vocab` |  |
| 49411 | 0.793626 | `乾煎り` | `からいり` | `乾煎り` | `normal_vocab` |  |
| 49622 | 0.795218 | `薬玉` | `くすだま` | `薬玉` | `normal_vocab` |  |
| 50017 | 0.798193 | `チェース` | `ちぇーす` | `チェース` | `deprioritized_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.543 | 46621 | 0.772159 | `螺子回し` | `ねじまわし` | `螺子回し` | `normal_vocab` |  |
| 0.536 | 47491 | 0.778921 | `御酒` | `みき` | `御酒` | `normal_vocab` |  |
| 0.522 | 48471 | 0.786460 | `頽れる` | `くずおれる` | `頽れる` | `normal_vocab` |  |
| 0.323 | 43875 | 0.750320 | `冠者` | `かじゃ` | `冠者` | `normal_vocab` |  |
| 0.323 | 43936 | 0.750813 | `叟` | `そう` | `叟` | `normal_vocab` |  |

## Band 0.80-0.85 (7566 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 50761 | 0.803763 | `臍曲がり` | `へそまがり` | `臍曲がり` | `normal_vocab` |  |
| 52112 | 0.813170 | `焼け山` | `やけやま` | `焼け山` | `normal_vocab` |  |
| 52317 | 0.814539 | `小作り` | `こづくり` | `小作り` | `normal_vocab` |  |
| 52695 | 0.817066 | `簡約` | `かんやく` | `簡約` | `normal_vocab` |  |
| 53190 | 0.820353 | `女偏` | `おんなへん` | `女偏` | `normal_vocab` |  |
| 55952 | 0.838260 | `音合わせ` | `おとあわせ` | `音合わせ` | `normal_vocab` |  |
| 56198 | 0.839826 | `名剣` | `めいけん` | `名剣` | `normal_vocab` |  |
| 56436 | 0.841330 | `煙管` | `えんかん` | `煙管` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.546 | 57643 | 0.848878 | `僊` | `せん` | `僊` | `normal_vocab` |  |
| 0.545 | 56621 | 0.842495 | `隷` | `れい` | `隷` | `normal_vocab` |  |
| 0.322 | 50976 | 0.805356 | `方偏` | `かたへん` | `方偏` | `normal_vocab` |  |
| 0.322 | 54267 | 0.827409 | `居玉` | `いぎょく` | `居玉` | `normal_vocab` |  |
| 0.322 | 56730 | 0.843179 | `熱り` | `いきり` | `熱り` | `normal_vocab` |  |

## Band 0.85-0.90 (7569 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 58327 | 0.853122 | `ウンマ` | `うんま` | `ウンマ` | `normal_vocab` |  |
| 58411 | 0.853637 | `バイオロジカル` | `ばいおろじかる` | `バイオロジカル` | `normal_vocab` |  |
| 59467 | 0.860065 | `侵寇` | `しんこう` | `侵寇` | `normal_vocab` |  |
| 60043 | 0.863557 | `胃宿` | `いしゅく` | `胃宿` | `normal_vocab` |  |
| 60662 | 0.867973 | `凶変` | `きょうへん` | `凶変` | `normal_vocab` |  |
| 60898 | 0.869642 | `恋風` | `こいかぜ` | `恋風` | `normal_vocab` |  |
| 61011 | 0.870439 | `梨河豚` | `なしふぐ` | `梨河豚` | `normal_vocab` |  |
| 63467 | 0.887331 | `使い出` | `つかいで` | `使い出` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1.322 | 64865 | 0.896575 | `けつまんこ` | `けつまんこ` | `けつまんこ` | `sensitive_or_adult_vocab` | restricted_admission,sensitive_or_adult_vocab |
| 0.322 | 61342 | 0.872768 | `好き好み` | `すきこのみ` | `好き好み` | `normal_vocab` |  |
| 0.322 | 62886 | 0.883423 | `いちびる` | `いちびる` | `いちびる` | `normal_vocab` |  |
| 0.322 | 64849 | 0.896465 | `古祠` | `こし` | `古祠` | `normal_vocab` |  |
| 0.322 | 64850 | 0.896471 | `小過` | `しょうか` | `小過` | `normal_vocab` |  |

## Band 0.90-0.95 (6004 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 65735 | 0.902190 | `就巣` | `しゅうそう` | `就巣` | `normal_vocab` |  |
| 66441 | 0.906661 | `粒食` | `りゅうしょく` | `粒食` | `normal_vocab` |  |
| 67139 | 0.911031 | `アントラセン` | `あんとらせん` | `アントラセン` | `normal_vocab` |  |
| 67192 | 0.911358 | `オーセンティック` | `おーせんてぃっく` | `オーセンティック` | `normal_vocab` |  |
| 67263 | 0.911795 | `コントリビューション` | `こんとりびゅーしょん` | `コントリビューション` | `normal_vocab` |  |
| 67572 | 0.914458 | `リダンダンシー` | `りだんだんしー` | `リダンダンシー` | `normal_vocab` |  |
| 69202 | 0.930443 | `置き勉` | `おきべん` | `置き勉` | `normal_vocab` |  |
| 70388 | 0.941295 | `アップリケ` | `あっぷりけ` | `アップリケ` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.550 | 68351 | 0.922249 | `御蔭` | `みかげ` | `御蔭` | `normal_vocab` |  |
| 0.421 | 69891 | 0.936830 | `御御` | `おごう` | `御御` | `normal_vocab` |  |
| 0.323 | 69969 | 0.937539 | `田舎侍` | `いなかざむらい` | `田舎侍` | `normal_vocab` |  |
| 0.323 | 69970 | 0.937548 | `白酒` | `しろざけ` | `白酒` | `normal_vocab` |  |
| 0.323 | 70033 | 0.938118 | `モヒ` | `もひ` | `モヒ` | `normal_vocab` |  |

## Band 0.95-1.00 (2355 rows)

### Random Samples

| Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 72034 | 0.958899 | `フェーザー` | `ふぇーざー` | `フェーザー` | `normal_vocab` |  |
| 72111 | 0.960689 | `ブラバ` | `ぶらば` | `ブラバ` | `normal_vocab` |  |
| 72262 | 0.964117 | `ホムペ` | `ほむぺ` | `ホムペ` | `normal_vocab` |  |
| 72439 | 0.967992 | `メリクリ` | `めりくり` | `メリクリ` | `normal_vocab` |  |
| 73107 | 0.981178 | `春霖` | `しゅんりん` | `春霖` | `normal_vocab` |  |
| 73164 | 0.982180 | `桂男` | `かつらおとこ` | `桂男` | `normal_vocab` |  |
| 73239 | 0.983470 | `清しい` | `すがしい` | `清しい` | `normal_vocab` |  |
| 73639 | 0.998267 | `鑽る` | `きる` | `鑽る` | `normal_vocab` |  |

### Mechanical Risk Rows

| Risk | Rank | Score | Word | Reading | Display | Admission | Flags |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 0.323 | 71401 | 0.950027 | `セーミ` | `せーみ` | `セーミ` | `normal_vocab` |  |
| 0.323 | 71405 | 0.950061 | `ゼンチョ` | `ぜんちょ` | `ゼンチョ` | `normal_vocab` |  |
| 0.323 | 71460 | 0.950520 | `ダズン` | `だずん` | `ダズン` | `normal_vocab` |  |
| 0.323 | 71506 | 0.950904 | `チョベリバ` | `ちょべりば` | `チョベリバ` | `normal_vocab` |  |
| 0.323 | 71549 | 0.951261 | `テレグラム` | `てれぐらむ` | `テレグラム` | `normal_vocab` |  |
