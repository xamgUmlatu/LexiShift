# en-ja Standalone Independence Broad Audit

This is a sidecar diagnostic only. It does not change scores, admission, or runtime behavior.

## Inputs

- Ranking: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv`
- BCCWJ: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj/main.sqlite`
- Aozora: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-aozora-word/main.sqlite`
- JMDict: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/jmdict-ja-en/JMdict_e`
- Candidate filter: rank <= `5000`, score <= `0.8`, surface length <= `3`
- Candidate count: `3381`

## Summary

- Audited rows: `3381`
- Classifications: `{"compound_rich_but_standalone_supported": 2139, "high_confidence_compound_component": 4, "independent_supported": 1168, "low_or_uncertain": 61, "medium_confidence_compound_component": 9}`
- Pressure bands: `{"low_review_pressure": 2768, "moderate_review_pressure": 497, "severe_review_pressure": 24, "strong_review_pressure": 92}`
- Manual compoundish corrections in audited rows: `37`
- Manual compoundish recall by moderate pressure: `36` / `37` = `0.972973`
- Manual compoundish recall by strong pressure: `29` / `37` = `0.783784`
- Manual compoundish recall by severe pressure: `7` / `37` = `0.189189`
- Strong-pressure rows already manual: `29` / `116` = `0.25`
- High-confidence rows already manual: `2` / `4` = `0.5`

## Top Candidates

| Row | Score | Risk | Leak | Pressure | Class | Manual | Fx direct | Cx compounds | JMDict exact/compound/priority | Examples |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| `見/けん` | 0.244 | 0.774 | 0.997 | `severe_review_pressure` | `high_confidence_compound_component` | restricted_admission | 6/0 | 44406+30067 | 1/206/38 | 発見/はっけん[18.1]@0.200, 意見/いけん[17.9]@0.131, 見物/けんぶつ[15.5]@0.158, 一見/いっけん[14.9]@0.340, 見当/けんとう[14.9]@0.265 |
| `生/せい` | 0.268 | 0.772 | 0.986 | `severe_review_pressure` | `independent_supported` |  | 3429/30107 | 190652+120076 | 1/1385/146 | 生活/せいかつ[21.1]@0.126, 先生/せんせい[20.6]@0.000, 人生/じんせい[18.2]@0.187, 生産/せいさん[18.0]@0.128, 生命/せいめい[17.6]@0.229 |
| `骨/こつ` | 0.279 | 0.771 | 0.966 | `severe_review_pressure` | `high_confidence_compound_component` |  | 4/2616 | 5426+3932 | 1/323/22 | 露骨/ろこつ[13.0]@0.430, 遺骨/いこつ[11.3]@0.451, 骸骨/がいこつ[11.1]@0.457, 白骨/はっこつ[10.8]@0.491, 鉄骨/てっこつ[10.1]@0.452 |
| `公/こう` | 0.310 | 0.767 | 0.984 | `severe_review_pressure` | `independent_supported` |  | 1180/7350 | 77750+17693 | 1/734/109 | 公園/こうえん[16.8]@0.069, 公共/こうきょう[14.9]@0.229, 公開/こうかい[14.6]@0.206, 公式/こうしき[14.4]@0.284, 公平/こうへい[14.1]@0.255 |
| `書/しょ` | 0.289 | 0.766 | 0.984 | `severe_review_pressure` | `independent_supported` |  | 5305/32030 | 50303+28667 | 1/964/109 | 書類/しょるい[15.6]@0.250, 書物/しょもつ[15.3]@0.266, 文書/ぶんしょ[15.0]@0.286, 図書/としょ[14.9]@0.234, 読書/どくしょ[14.8]@0.120 |
| `要/よう` | 0.305 | 0.748 | 0.975 | `severe_review_pressure` | `independent_supported` |  | 1320/3775 | 155372+34910 | 1/409/44 | 必要/ひつよう[20.8]@0.125, 重要/じゅうよう[17.7]@0.175, 要求/ようきゅう[17.3]@0.230, 要素/ようそ[16.4]@0.214, 要する/ようする[15.8]@0.221 |
| `海/かい` | 0.299 | 0.745 | 0.984 | `severe_review_pressure` | `high_confidence_compound_component` |  | 52/3573 | 35847+16717 | 0/655/75 | 海岸/かいがん[16.1]@0.144, 海外/かいがい[15.3]@0.198, 海軍/かいぐん[15.0]@0.314, 海上/かいじょう[14.5]@0.337, 航海/こうかい[14.0]@0.385 |
| `西/せい` | 0.228 | 0.717 | 0.998 | `severe_review_pressure` | `high_confidence_compound_component` | restricted_admission | 1/0 | 9359+10835 | 1/205/24 | 西洋/せいよう[16.8]@0.152, 西暦/せいれき[12.4]@0.435, 西部/せいぶ[12.2]@0.382, 西方/せいほう[12.0]@0.427, 西南/せいなん[11.9]@0.453 |
| `画/が` | 0.220 | 0.715 | 0.974 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 2734/2844 | 44005+13986 | 1/296/39 | 映画/えいが[17.8]@0.051, 画家/がか[15.4]@0.260, 画面/がめん[15.4]@0.192, 画像/がぞう[14.5]@0.206, 絵画/かいが[14.4]@0.254 |
| `道/どう` | 0.240 | 0.708 | 0.986 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 9310/7251 | 54736+35715 | 1/866/83 | 道路/どうろ[16.8]@0.200, 道具/どうぐ[16.3]@0.151, 道徳/どうとく[15.6]@0.264, 鉄道/てつどう[15.5]@0.239, 報道/ほうどう[15.2]@0.237 |
| `原/げん` | 0.273 | 0.702 | 0.983 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 143/2099 | 55189+18994 | 1/566/76 | 原因/げんいん[18.0]@0.135, 原則/げんそく[15.8]@0.279, 原子/げんし[15.8]@0.241, 原稿/げんこう[15.6]@0.346, 原理/げんり[15.5]@0.313 |
| `便/べん` | 0.316 | 0.670 | 0.990 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 12/0 | 10759+6538 | 1/113/15 | 便利/べんり[15.7]@0.076, 不便/ふべん[13.9]@0.157, 便所/べんじょ[13.6]@0.425, 便宜/べんぎ[13.3]@0.432, 小便/しょうべん[12.1]@0.452 |
| `水/すい` | 0.220 | 0.660 | 0.990 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 4824/7923 | 56627+21198 | 1/1091/145 | 水準/すいじゅん[15.3]@0.242, 水道/すいどう[14.3]@0.160, 水面/すいめん[14.1]@0.360, 水平/すいへい[13.7]@0.335, 海水/かいすい[13.6]@0.361 |
| `約/やく` | 0.277 | 0.659 | 0.952 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 29/29044 | 41885+10005 | 1/382/35 | 約束/やくそく[17.4]@0.141, 契約/けいやく[15.8]@0.195, 条約/じょうやく[14.6]@0.292, 予約/よやく[14.2]@0.144, 制約/せいやく[14.1]@0.349 |
| `家/や` | 0.227 | 0.647 | 0.991 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 3/0 | 6821+3864 | 1/55/20 | 大家/おおや[13.5]@0.264, 我が家/わがや[13.5]@0.309, 家賃/やちん[13.3]@0.252, 借家/しゃくや[12.3]@0.427, 家主/やぬし[11.9]@0.457 |
| `間/あい` | 0.243 | 0.645 | 0.983 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 3/0 | 2065+1356 | 0/68/10 | 間柄/あいだがら[12.7]@0.437, 合間/あいま[12.4]@0.392, 幕間/まくあい[8.5]@0.563, 間合い/まあい[8.3]@0.518, 此の間/このあいだ[6.0]@0.407 |
| `適/てき` | 0.317 | 0.642 | 0.967 | `severe_review_pressure` | `independent_supported` |  | 970/0 | 35179+5151 | 0/176/33 | 適当/てきとう[15.7]@0.150, 適用/てきよう[15.4]@0.226, 適切/てきせつ[15.2]@0.238, 適する/てきする[13.0]@0.261, 適応/てきおう[12.9]@0.353 |
| `地/じ` | 0.261 | 0.633 | 0.994 | `severe_review_pressure` | `medium_confidence_compound_component` | restricted_admission | 73/0 | 31598+19027 | 1/290/48 | 地震/じしん[16.4]@0.140, 地面/じめん[15.6]@0.304, 地獄/じごく[15.6]@0.306, 意地/いじ[14.7]@0.343, 地主/じぬし[14.2]@0.408 |
| `妹/いも` | 0.298 | 0.609 | 0.910 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 3/0 | 33+56 | 1/12/1 | 妹御/いもうとご[3.9], 妹婿/いもうとむこ[2.8]@0.823, 妹背/いもせ[2.8]@0.977, 妹分/いもうとぶん[2.4]@0.701, 妹娘/いもうとむすめ[2.1]@0.749 |
| `朝/ちょう` | 0.227 | 0.606 | 0.966 | `severe_review_pressure` | `medium_confidence_compound_component` | restricted_admission | 171/754 | 16662+7452 | 1/175/22 | 朝鮮/ちょうせん[16.2]@0.288, 朝食/ちょうしょく[13.8]@0.376, 早朝/そうちょう[13.6]@0.366, 朝廷/ちょうてい[13.4]@0.488, 王朝/おうちょう[12.8]@0.388 |
| `海/あま` | 0.299 | 0.606 | 0.967 | `severe_review_pressure` | `medium_confidence_compound_component` |  | 1/0 | 220+290 | 0/6/1 | 海女/あま[10.3]@0.527, 海人/あま[4.9], 甘海老/あまえび[3.7]@0.701, 甘海苔/あまのり[1.4]@0.928 |
| `全/ぜん` | 0.273 | 0.603 | 0.981 | `severe_review_pressure` | `compound_rich_but_standalone_supported` |  | 285/16479 | 112705+32449 | 1/718/80 | 全体/ぜんたい[18.6]@0.175, 完全/かんぜん[17.7]@0.187, 全部/ぜんぶ[17.6]@0.077, 安全/あんぜん[17.1]@0.127, 全然/ぜんぜん[17.0]@0.170 |
| `大/だい` | 0.222 | 0.601 | 0.986 | `severe_review_pressure` | `compound_rich_but_standalone_supported` |  | 3438/83746 | 142789+56367 | 1/2525/131 | 大学/だいがく[18.6]@0.017, 大臣/だいじん[17.7]@0.198, 大事/だいじ[17.7]@0.140, 大丈夫/だいじょうぶ[17.5]@0.065, 大体/だいたい[16.6]@0.148 |
| `学/がく` | 0.264 | 0.600 | 0.988 | `severe_review_pressure` | `compound_rich_but_standalone_supported` |  | 1315/25353 | 131459+89993 | 1/3465/187 | 科学/かがく[19.0]@0.129, 大学/だいがく[18.6]@0.017, 文学/ぶんがく[18.6]@0.134, 学生/がくせい[17.5]@0.056, 哲学/てつがく[17.3]@0.263 |
| `中/ちゅう` | 0.220 | 0.597 | 0.989 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 6329/76093 | 135911+67659 | 1/1345/172 | 中心/ちゅうしん[18.4]@0.179, 途中/とちゅう[17.6]@0.139, 中央/ちゅうおう[17.5]@0.197, 中国/ちゅうごく[17.4]@0.174, 中学/ちゅうがく[16.0]@0.231 |
| `無/む` | 0.267 | 0.595 | 0.988 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 2217/24516 | 61460+51540 | 1/866/136 | 無理/むり[18.1]@0.138, 無論/むろん[16.0]@0.353, 無駄/むだ[15.6]@0.241, 無視/むし[15.6]@0.252, 無限/むげん[15.0]@0.316 |
| `取り/とり` | 0.220 | 0.589 | 0.987 | `strong_review_pressure` | `independent_supported` | score_floor,restricted_admission | 7368/1045 | 86423+6944 | 1/432/90 | 取り上げる/とりあげる[14.1]@0.280, 取り出す/とりだす[13.8]@0.282, 取り扱い/とりあつかい[13.5]@0.310, 取り扱う/とりあつかう[13.1]@0.350, 取り引き/とりひき[13.0]@0.201 |
| `品/ひん` | 0.269 | 0.582 | 0.955 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 3179/22163 | 61002+16067 | 1/614/65 | 作品/さくひん[18.9]@0.181, 商品/しょうひん[16.4]@0.179, 製品/せいひん[14.5]@0.207, 上品/じょうひん[13.9]@0.370, 食品/しょくひん[13.8]@0.233 |
| `用/よう` | 0.190 | 0.580 | 0.986 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 7111/30211 | 167413+37335 | 1/1178/123 | 利用/りよう[18.5]@0.125, 使用/しよう[17.8]@0.173, 用意/ようい[17.2]@0.141, 作用/さよう[16.7]@0.230, 信用/しんよう[16.2]@0.245 |
| `間/かん` | 0.300 | 0.576 | 0.966 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 4167/18181 | 146234+50562 | 1/841/58 | 時間/じかん[20.9], 年間/ねんかん[17.8], 瞬間/しゅんかん[17.3]@0.209, 空間/くうかん[17.3]@0.209, 週間/しゅうかん[17.3] |
| `計/けい` | 0.267 | 0.571 | 0.963 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 1322/4837 | 77471+15259 | 1/697/47 | 計画/けいかく[18.4]@0.126, 時計/とけい[16.6]@0.078, 計算/けいさん[16.5]@0.198, 統計/とうけい[15.3]@0.287, 余計/よけい[15.2]@0.310 |
| `訳/やく` | 0.155 | 0.560 | 0.951 | `strong_review_pressure` | `independent_supported` | restricted_admission | 3483/1119 | 6529+3829 | 1/138/21 | 翻訳/ほんやく[15.0]@0.153, 通訳/つうやく[12.7]@0.364, 訳者/やくしゃ[11.6]@0.475, 訳す/やくす[11.4]@0.371, 英訳/えいやく[10.0]@0.468 |
| `悪/わる` | 0.275 | 0.554 | 0.912 | `strong_review_pressure` | `independent_supported` |  | 2012/0 | 28975+17021 | 1/166/12 | 悪い/わるい[19.8]@0.041, 悪者/わるもの[11.2]@0.448, 悪気/わるぎ[10.3]@0.468, 悪ふざけ/わるふざけ[8.3]@0.549, 性悪/しょうわる[7.4]@0.662 |
| `大き/おおき` | 0.213 | 0.542 | 0.861 | `strong_review_pressure` | `independent_supported` |  | 2180/0 | 68499+38467 | 1/29/4 | 大きな/おおきな[20.4]@0.033, 大きい/おおきい[19.5]@0.022, 大きに/おおきに[10.7]@0.593, 大きめ/おおきめ[9.0]@0.578, 大きく/おおきく[8.9] |
| `個/こ` | 0.315 | 0.541 | 0.898 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 851/15543 | 30741+8341 | 1/138/16 | 個人/こじん[18.2]@0.179, 個性/こせい[15.3]@0.295, 個々/ここ[14.8]@0.327, 個別/こべつ[13.7]@0.300, 個体/こたい[12.5]@0.346 |
| `後/ご` | 0.220 | 0.539 | 0.959 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 10885/53010 | 82256+35212 | 1/121/31 | 最後/さいご[19.2]@0.131, 午後/ごご[18.5]@0.051, 今後/こんご[17.1]@0.180, 前後/ぜんご[16.7]@0.227, 以後/いご[16.2]@0.318 |
| `上/じょう` | 0.220 | 0.538 | 0.987 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 45419/46969 | 124090+54804 | 1/861/110 | 以上/いじょう[20.4]@0.126, 地上/ちじょう[16.2]@0.285, 上手/じょうず[16.1]@0.100, 向上/こうじょう[15.5]@0.221, 上下/じょうげ[15.2]@0.300 |
| `下/げ` | 0.220 | 0.535 | 0.989 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 146/0 | 13845+15090 | 1/148/27 | 上下/じょうげ[15.2]@0.300, 下宿/げしゅく[14.4]@0.159, 下駄/げた[14.3]@0.409, 下落/げらく[13.1]@0.308, 下旬/げじゅん[13.0]@0.370 |
| `火/か` | 0.176 | 0.534 | 0.986 | `strong_review_pressure` | `independent_supported` | restricted_admission | 4633/0 | 15799+11542 | 1/249/40 | 火事/かじ[14.4]@0.157, 火災/かさい[14.1]@0.245, 火山/かざん[13.8]@0.336, 火星/かせい[13.8]@0.405, 火曜/かよう[12.7]@0.261 |
| `徒/と` | 0.259 | 0.531 | 0.974 | `strong_review_pressure` | `independent_supported` | restricted_admission | 2020/0 | 11870+7868 | 1/78/12 | 生徒/せいと[17.2]@0.062, 徒歩/とほ[13.6]@0.335, 信徒/しんと[12.0]@0.432, 使徒/しと[11.0]@0.505, 学徒/がくと[10.9]@0.477 |
| `氏/うじ` | 0.276 | 0.531 | 0.901 | `strong_review_pressure` | `low_or_uncertain` |  | 34/0 | 350+252 | 1/19/3 | 氏神/うじがみ[9.7]@0.554, 氏子/うじこ[9.1]@0.541, 杜氏/とうじ[8.1]@0.629, 氏寺/うじでら[3.1]@0.810, 氏名/うじな[1.4]@0.481 |
| `値/ね` | 0.265 | 0.528 | 0.961 | `strong_review_pressure` | `independent_supported` |  | 570/0 | 10163+1223 | 1/68/23 | 値段/ねだん[14.8]@0.142, 値打ち/ねうち[11.0]@0.428, 高値/たかね[11.0]@0.327, 値上げ/ねあげ[11.0]@0.394, 安値/やすね[10.5]@0.363 |
| `密/みつ` | 0.251 | 0.528 | 0.959 | `strong_review_pressure` | `independent_supported` | restricted_admission | 1700/0 | 12527+9364 | 1/211/29 | 秘密/ひみつ[17.1]@0.239, 厳密/げんみつ[13.3]@0.367, 精密/せいみつ[13.1]@0.387, 親密/しんみつ[12.4]@0.418, 密度/みつど[12.0]@0.355 |
| `税/ぜい` | 0.242 | 0.527 | 0.956 | `strong_review_pressure` | `independent_supported` |  | 14489/0 | 24783+1453 | 1/370/44 | 税金/ぜいきん[13.4]@0.254, 課税/かぜい[13.1]@0.302, 租税/そぜい[12.3]@0.415, 納税/のうぜい[12.0]@0.346, 税関/ぜいかん[11.5]@0.446 |
| `可/か` | 0.264 | 0.525 | 0.939 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 7333/7312 | 80686+10544 | 1/197/24 | 可能/かのう[18.6]@0.169, 可愛い/かわいい[16.7]@0.180, 許可/きょか[15.2]@0.239, 不可/ふか[14.1]@0.267, 可哀想/かわいそう[13.9]@0.308 |
| `南/なん` | 0.220 | 0.523 | 0.990 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 67/0 | 11419+6206 | 2/264/33 | 南部/なんぶ[13.9]@0.333, 南北/なんぼく[13.6]@0.359, 東南/とうなん[13.3]@0.358, 南方/なんぽう[12.9]@0.417, 西南/せいなん[11.9]@0.453 |
| `正/せい` | 0.254 | 0.523 | 0.978 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 3862/2727 | 47419+11339 | 1/483/55 | 正確/せいかく[16.0]@0.241, 改正/かいせい[15.2]@0.235, 正当/せいとう[15.0]@0.336, 正義/せいぎ[14.6]@0.337, 不正/ふせい[14.1]@0.248 |
| `性/せい` | 0.188 | 0.522 | 0.977 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 5354/94076 | 93804+28248 | 1/2060/105 | 女性/じょせい[18.9]@0.126, 性格/せいかく[17.4]@0.221, 性質/せいしつ[16.9]@0.298, 男性/だんせい[16.6]@0.130, 個性/こせい[15.3]@0.295 |
| `御/ご` | 0.203 | 0.522 | 0.946 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 338/117352 | 71859+25828 | 1/228/28 | 御覧/ごらん[16.6]@0.202, 御座る/ござる[16.2]@0.493, 御飯/ごはん[16.1]@0.077, 御免/ごめん[16.1]@0.204, 御前/ごぜん[13.5]@0.414 |
| `遠/おち` | 0.226 | 0.517 | 0.866 | `strong_review_pressure` | `low_or_uncertain` |  | 1/0 | 21+3 | 0/2/1 | 遠近/おちこち[3.1]@0.551, 遠方/おちかた[1.4] |
| `土/ど` | 0.210 | 0.517 | 0.977 | `strong_review_pressure` | `independent_supported` |  | 13003/2509 | 26982+14464 | 1/290/53 | 国土/こくど[14.2]@0.320, 土曜/どよう[14.2]@0.253, 土間/どま[13.7]@0.432, 土手/どて[13.5]@0.419, 領土/りょうど[13.2]@0.350 |
| `科/か` | 0.271 | 0.515 | 0.952 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 698/10606 | 28228+17480 | 1/410/40 | 科学/かがく[19.0]@0.129, 外科/げか[13.4]@0.323, 内科/ないか[12.3]@0.367, 科目/かもく[12.0]@0.253, 学科/がっか[11.9]@0.404 |
| `粗/あら` | 0.271 | 0.514 | 0.865 | `strong_review_pressure` | `independent_supported` |  | 357/179 | 1419+155 | 1/43/5 | 粗い/あらい[11.2]@0.399, 粗削り/あらけずり[5.8]@0.558, 粗筋/あらすじ[5.5]@0.426, 粗熱/あらねつ[4.9]@0.595, 粗方/あらかた[4.6]@0.620 |
| `術/じゅつ` | 0.299 | 0.514 | 0.961 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 4616/2813 | 50675+26590 | 1/743/32 | 技術/ぎじゅつ[18.6]@0.125, 芸術/げいじゅつ[18.1]@0.243, 美術/びじゅつ[16.4]@0.240, 手術/しゅじゅつ[15.7]@0.236, 学術/がくじゅつ[13.6]@0.387 |
| `東/とう` | 0.227 | 0.497 | 0.989 | `strong_review_pressure` | `low_or_uncertain` | restricted_admission | 152/0 | 13636+26487 | 1/473/30 | 東洋/とうよう[15.3]@0.349, 東西/とうざい[14.4]@0.359, 東南/とうなん[13.3]@0.358, 東方/とうほう[12.9]@0.374, 東北/とうほく[12.7]@0.441 |
| `縁/えん` | 0.259 | 0.497 | 0.982 | `strong_review_pressure` | `independent_supported` |  | 3047/32 | 5501+8031 | 1/179/23 | 縁側/えんがわ[13.8]@0.439, 縁起/えんぎ[12.5]@0.438, 無縁/むえん[12.3]@0.417, 縁談/えんだん[11.7]@0.474, 離縁/りえん[11.5]@0.538 |
| `北/ほく` | 0.228 | 0.496 | 0.984 | `strong_review_pressure` | `low_or_uncertain` | restricted_admission | 124/0 | 6201+3112 | 0/161/20 | 北部/ほくぶ[12.8]@0.347, 東北/とうほく[12.7]@0.441, 北上/ほくじょう[11.1]@0.426, 北東/ほくとう[11.1]@0.410, 北西/ほくせい[11.1]@0.406 |
| `木/もく` | 0.220 | 0.494 | 0.973 | `strong_review_pressure` | `independent_supported` | score_floor,restricted_admission | 1175/0 | 8466+5175 | 1/145/17 | 樹木/じゅもく[14.2]@0.389, 木曜/もくよう[13.1]@0.261, 木造/もくぞう[13.0]@0.377, 木材/もくざい[13.0]@0.333, 材木/ざいもく[12.7]@0.449 |
| `玉/ぎょく` | 0.276 | 0.493 | 0.971 | `strong_review_pressure` | `low_or_uncertain` |  | 164/0 | 985+1230 | 1/70/5 | 宝玉/ほうぎょく[9.6]@0.607, 珠玉/しゅぎょく[9.6]@0.549, 紅玉/こうぎょく[9.5]@0.648, 玉座/ぎょくざ[9.5]@0.593, 玉砕/ぎょくさい[8.6]@0.546 |
| `都/と` | 0.128 | 0.493 | 0.945 | `strong_review_pressure` | `independent_supported` | restricted_admission | 15743/723 | 27667+9729 | 1/143/24 | 都市/とし[17.1]@0.190, 都会/とかい[15.2]@0.251, 首都/しゅと[13.3]@0.243, 帝都/ていと[10.8]@0.536, 都内/とない[10.4]@0.369 |
| `財/ざい` | 0.271 | 0.491 | 0.945 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 882/3177 | 24115+4324 | 1/256/25 | 財産/ざいさん[16.6]@0.246, 財政/ざいせい[14.8]@0.237, 財源/ざいげん[11.9]@0.348, 財閥/ざいばつ[11.1]@0.427, 財宝/ざいほう[10.7]@0.517 |
| `塩/えん` | 0.220 | 0.491 | 0.964 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 195/0 | 4235+476 | 1/245/13 | 食塩/しょくえん[10.7]@0.415, 塩分/えんぶん[10.6]@0.377, 塩田/えんでん[9.5]@0.484, 塩化/えんか[9.1]@0.433, 塩素/えんそ[9.1]@0.417 |
| `任せ/まかせ` | 0.318 | 0.490 | 0.803 | `strong_review_pressure` | `independent_supported` |  | 1804/0 | 3963+470 | 1/28/1 | 任せる/まかせる[13.7]@0.246, 力任せ/ちからまかせ[9.6]@0.670, 出任せ/でまかせ[8.5]@0.733, 人任せ/ひとまかせ[7.8]@0.715, 運任せ/うんまかせ[3.2]@0.809 |
| `求め/もとめ` | 0.280 | 0.484 | 0.778 | `strong_review_pressure` | `independent_supported` |  | 5980/0 | 21517+2134 | 1/18/4 | 求める/もとめる[17.6]@0.179, 追い求める/おいもとめる[8.3]@0.521, 捜し求める/さがしもとめる[8.0]@0.527, 買い求める/かいもとめる[7.6]@0.520, 請い求める/こいもとめる[2.2]@0.852 |
| `小/しょう` | 0.264 | 0.484 | 0.975 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 2233/39945 | 24804+25912 | 1/582/62 | 小説/しょうせつ[18.3]@0.136, 小学/しょうがく[14.7]@0.282, 小児/しょうに[14.4]@0.359, 大小/だいしょう[14.1]@0.397, 小生/しょうせい[12.8]@0.512 |
| `会/かい` | 0.169 | 0.482 | 0.979 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 64132/8943 | 192588+50200 | 1/2328/167 | 社会/しゃかい[20.8]@0.125, 会社/かいしゃ[18.9]@0.016, 機会/きかい[17.4]@0.134, 会議/かいぎ[16.4]@0.129, 会話/かいわ[16.0]@0.148 |
| `能/のう` | 0.263 | 0.481 | 0.964 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 6773/1118 | 86110+17077 | 1/636/37 | 可能/かのう[18.6]@0.169, 能力/のうりょく[17.1]@0.187, 機能/きのう[16.7]@0.176, 才能/さいのう[15.0]@0.258, 本能/ほんのう[14.9]@0.356 |
| `祝/しゅく` | 0.281 | 0.480 | 0.916 | `strong_review_pressure` | `independent_supported` |  | 1870/0 | 3470+1467 | 1/30/11 | 祝福/しゅくふく[13.2]@0.363, 祝日/しゅくじつ[11.4]@0.361, 祝賀/しゅくが[9.9]@0.474, 祝宴/しゅくえん[9.4]@0.544, 祝祭/しゅくさい[9.1]@0.616 |
| `文/ぶん` | 0.205 | 0.477 | 0.986 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 15380/1206 | 65956+64572 | 1/936/104 | 文化/ぶんか[19.3]@0.128, 文学/ぶんがく[18.6]@0.134, 文章/ぶんしょう[17.0]@0.078, 文明/ぶんめい[16.1]@0.255, 論文/ろんぶん[15.5]@0.250 |
| `主/しゅ` | 0.202 | 0.472 | 0.985 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 6864/3039 | 86993+63042 | 1/1078/116 | 主義/しゅぎ[19.7]@0.189, 主人/しゅじん[18.7]@0.200, 主張/しゅちょう[17.3]@0.216, 民主/みんしゅ[16.5]@0.232, 主婦/しゅふ[15.2]@0.121 |
| `付き/つき` | 0.244 | 0.470 | 0.938 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 827/8597 | 14873+634 | 1/222/23 | 顔付き/かおつき[11.9]@0.400, 付き合う/つきあう[10.8]@0.225, 結び付き/むすびつき[10.5]@0.421, 目付き/めつき[10.4]@0.408, 思い付き/おもいつき[10.3]@0.449 |
| `天/てん` | 0.280 | 0.469 | 0.989 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 13635/131 | 43431+40773 | 1/915/84 | 天皇/てんのう[16.9]@0.223, 天井/てんじょう[16.2]@0.295, 天下/てんか[15.8]@0.342, 天気/てんき[15.7]@0.099, 天才/てんさい[14.8]@0.333 |
| `気/き` | 0.126 | 0.467 | 0.989 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 111632/0 | 159219+83904 | 1/705/153 | 気持ち/きもち[18.2]@0.129, 病気/びょうき[18.1]@0.062, 気分/きぶん[17.6]@0.141, 空気/くうき[17.4]@0.144, 元気/げんき[17.4]@0.069 |
| `質/しつ` | 0.247 | 0.466 | 0.972 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 4394/5456 | 63404+22658 | 1/483/55 | 質問/しつもん[17.9]@0.053, 物質/ぶっしつ[17.0]@0.218, 性質/せいしつ[16.9]@0.298, 本質/ほんしつ[16.4]@0.308, 実質/じっしつ[15.0]@0.297 |
| `偶/たま` | 0.267 | 0.465 | 0.818 | `strong_review_pressure` | `low_or_uncertain` |  | 228/0 | 6074+163 | 1/6/2 | 偶に/たまに[13.0]@0.151, 偶々/たまたま[7.9]@0.256, 時偶/ときたま[3.6] |
| `園/えん` | 0.220 | 0.465 | 0.948 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 1776/10543 | 19278+4604 | 1/244/29 | 公園/こうえん[16.8]@0.069, 庭園/ていえん[13.4]@0.365, 田園/でんえん[12.1]@0.432, 学園/がくえん[11.6]@0.339, 園芸/えんげい[11.5]@0.399 |
| `対/たい` | 0.216 | 0.464 | 0.975 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 9459/0 | 183904+51934 | 1/622/60 | 反対/はんたい[18.0]@0.135, 対象/たいしょう[17.9]@0.181, 絶対/ぜったい[17.7]@0.178, 対立/たいりつ[15.9]@0.313, 対する/たいする[15.8]@0.167 |
| `害/がい` | 0.266 | 0.463 | 0.971 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 1840/0 | 60238+7699 | 1/505/41 | 被害/ひがい[16.5]@0.202, 障害/しょうがい[15.8]@0.186, 災害/さいがい[14.6]@0.218, 損害/そんがい[14.5]@0.245, 利害/りがい[14.1]@0.393 |
| `第/だい` | 0.305 | 0.462 | 0.855 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 245/177252 | 9180+13358 | 1/254/22 | 次第/しだい[17.5]@0.214, 落第/らくだい[11.1]@0.492, 及第/きゅうだい[10.3]@0.548, 第一/だいいち[9.7], 次第に/しだいに[8.6] |
| `運/うん` | 0.251 | 0.462 | 0.968 | `strong_review_pressure` | `compound_rich_but_standalone_supported` |  | 4934/0 | 55524+19884 | 1/506/42 | 運動/うんどう[18.8]@0.133, 運命/うんめい[16.8]@0.293, 運転/うんてん[16.7]@0.137, 運用/うんよう[14.0]@0.230, 運営/うんえい[13.7]@0.219 |

## High-Confidence Unreviewed

| Row | Score | Risk | Leak | Pressure | Class | Manual | Fx direct | Cx compounds | JMDict exact/compound/priority | Examples |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| `骨/こつ` | 0.279 | 0.771 | 0.966 | `severe_review_pressure` | `high_confidence_compound_component` |  | 4/2616 | 5426+3932 | 1/323/22 | 露骨/ろこつ[13.0]@0.430, 遺骨/いこつ[11.3]@0.451, 骸骨/がいこつ[11.1]@0.457, 白骨/はっこつ[10.8]@0.491, 鉄骨/てっこつ[10.1]@0.452 |
| `海/かい` | 0.299 | 0.745 | 0.984 | `severe_review_pressure` | `high_confidence_compound_component` |  | 52/3573 | 35847+16717 | 0/655/75 | 海岸/かいがん[16.1]@0.144, 海外/かいがい[15.3]@0.198, 海軍/かいぐん[15.0]@0.314, 海上/かいじょう[14.5]@0.337, 航海/こうかい[14.0]@0.385 |

## Known Manual Compoundish Hits

| Row | Score | Risk | Leak | Pressure | Class | Manual | Fx direct | Cx compounds | JMDict exact/compound/priority | Examples |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| `見/けん` | 0.244 | 0.774 | 0.997 | `severe_review_pressure` | `high_confidence_compound_component` | restricted_admission | 6/0 | 44406+30067 | 1/206/38 | 発見/はっけん[18.1]@0.200, 意見/いけん[17.9]@0.131, 見物/けんぶつ[15.5]@0.158, 一見/いっけん[14.9]@0.340, 見当/けんとう[14.9]@0.265 |
| `西/せい` | 0.228 | 0.717 | 0.998 | `severe_review_pressure` | `high_confidence_compound_component` | restricted_admission | 1/0 | 9359+10835 | 1/205/24 | 西洋/せいよう[16.8]@0.152, 西暦/せいれき[12.4]@0.435, 西部/せいぶ[12.2]@0.382, 西方/せいほう[12.0]@0.427, 西南/せいなん[11.9]@0.453 |
| `画/が` | 0.220 | 0.715 | 0.974 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 2734/2844 | 44005+13986 | 1/296/39 | 映画/えいが[17.8]@0.051, 画家/がか[15.4]@0.260, 画面/がめん[15.4]@0.192, 画像/がぞう[14.5]@0.206, 絵画/かいが[14.4]@0.254 |
| `道/どう` | 0.240 | 0.708 | 0.986 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 9310/7251 | 54736+35715 | 1/866/83 | 道路/どうろ[16.8]@0.200, 道具/どうぐ[16.3]@0.151, 道徳/どうとく[15.6]@0.264, 鉄道/てつどう[15.5]@0.239, 報道/ほうどう[15.2]@0.237 |
| `水/すい` | 0.220 | 0.660 | 0.990 | `severe_review_pressure` | `independent_supported` | score_floor,restricted_admission | 4824/7923 | 56627+21198 | 1/1091/145 | 水準/すいじゅん[15.3]@0.242, 水道/すいどう[14.3]@0.160, 水面/すいめん[14.1]@0.360, 水平/すいへい[13.7]@0.335, 海水/かいすい[13.6]@0.361 |
| `地/じ` | 0.261 | 0.633 | 0.994 | `severe_review_pressure` | `medium_confidence_compound_component` | restricted_admission | 73/0 | 31598+19027 | 1/290/48 | 地震/じしん[16.4]@0.140, 地面/じめん[15.6]@0.304, 地獄/じごく[15.6]@0.306, 意地/いじ[14.7]@0.343, 地主/じぬし[14.2]@0.408 |
| `朝/ちょう` | 0.227 | 0.606 | 0.966 | `severe_review_pressure` | `medium_confidence_compound_component` | restricted_admission | 171/754 | 16662+7452 | 1/175/22 | 朝鮮/ちょうせん[16.2]@0.288, 朝食/ちょうしょく[13.8]@0.376, 早朝/そうちょう[13.6]@0.366, 朝廷/ちょうてい[13.4]@0.488, 王朝/おうちょう[12.8]@0.388 |
| `中/ちゅう` | 0.220 | 0.597 | 0.989 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 6329/76093 | 135911+67659 | 1/1345/172 | 中心/ちゅうしん[18.4]@0.179, 途中/とちゅう[17.6]@0.139, 中央/ちゅうおう[17.5]@0.197, 中国/ちゅうごく[17.4]@0.174, 中学/ちゅうがく[16.0]@0.231 |
| `取り/とり` | 0.220 | 0.589 | 0.987 | `strong_review_pressure` | `independent_supported` | score_floor,restricted_admission | 7368/1045 | 86423+6944 | 1/432/90 | 取り上げる/とりあげる[14.1]@0.280, 取り出す/とりだす[13.8]@0.282, 取り扱い/とりあつかい[13.5]@0.310, 取り扱う/とりあつかう[13.1]@0.350, 取り引き/とりひき[13.0]@0.201 |
| `用/よう` | 0.190 | 0.580 | 0.986 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 7111/30211 | 167413+37335 | 1/1178/123 | 利用/りよう[18.5]@0.125, 使用/しよう[17.8]@0.173, 用意/ようい[17.2]@0.141, 作用/さよう[16.7]@0.230, 信用/しんよう[16.2]@0.245 |
| `間/かん` | 0.300 | 0.576 | 0.966 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 4167/18181 | 146234+50562 | 1/841/58 | 時間/じかん[20.9], 年間/ねんかん[17.8], 瞬間/しゅんかん[17.3]@0.209, 空間/くうかん[17.3]@0.209, 週間/しゅうかん[17.3] |
| `訳/やく` | 0.155 | 0.560 | 0.951 | `strong_review_pressure` | `independent_supported` | restricted_admission | 3483/1119 | 6529+3829 | 1/138/21 | 翻訳/ほんやく[15.0]@0.153, 通訳/つうやく[12.7]@0.364, 訳者/やくしゃ[11.6]@0.475, 訳す/やくす[11.4]@0.371, 英訳/えいやく[10.0]@0.468 |
| `後/ご` | 0.220 | 0.539 | 0.959 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 10885/53010 | 82256+35212 | 1/121/31 | 最後/さいご[19.2]@0.131, 午後/ごご[18.5]@0.051, 今後/こんご[17.1]@0.180, 前後/ぜんご[16.7]@0.227, 以後/いご[16.2]@0.318 |
| `上/じょう` | 0.220 | 0.538 | 0.987 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 45419/46969 | 124090+54804 | 1/861/110 | 以上/いじょう[20.4]@0.126, 地上/ちじょう[16.2]@0.285, 上手/じょうず[16.1]@0.100, 向上/こうじょう[15.5]@0.221, 上下/じょうげ[15.2]@0.300 |
| `下/げ` | 0.220 | 0.535 | 0.989 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 146/0 | 13845+15090 | 1/148/27 | 上下/じょうげ[15.2]@0.300, 下宿/げしゅく[14.4]@0.159, 下駄/げた[14.3]@0.409, 下落/げらく[13.1]@0.308, 下旬/げじゅん[13.0]@0.370 |
| `火/か` | 0.176 | 0.534 | 0.986 | `strong_review_pressure` | `independent_supported` | restricted_admission | 4633/0 | 15799+11542 | 1/249/40 | 火事/かじ[14.4]@0.157, 火災/かさい[14.1]@0.245, 火山/かざん[13.8]@0.336, 火星/かせい[13.8]@0.405, 火曜/かよう[12.7]@0.261 |
| `徒/と` | 0.259 | 0.531 | 0.974 | `strong_review_pressure` | `independent_supported` | restricted_admission | 2020/0 | 11870+7868 | 1/78/12 | 生徒/せいと[17.2]@0.062, 徒歩/とほ[13.6]@0.335, 信徒/しんと[12.0]@0.432, 使徒/しと[11.0]@0.505, 学徒/がくと[10.9]@0.477 |
| `密/みつ` | 0.251 | 0.528 | 0.959 | `strong_review_pressure` | `independent_supported` | restricted_admission | 1700/0 | 12527+9364 | 1/211/29 | 秘密/ひみつ[17.1]@0.239, 厳密/げんみつ[13.3]@0.367, 精密/せいみつ[13.1]@0.387, 親密/しんみつ[12.4]@0.418, 密度/みつど[12.0]@0.355 |
| `南/なん` | 0.220 | 0.523 | 0.990 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 67/0 | 11419+6206 | 2/264/33 | 南部/なんぶ[13.9]@0.333, 南北/なんぼく[13.6]@0.359, 東南/とうなん[13.3]@0.358, 南方/なんぽう[12.9]@0.417, 西南/せいなん[11.9]@0.453 |
| `東/とう` | 0.227 | 0.497 | 0.989 | `strong_review_pressure` | `low_or_uncertain` | restricted_admission | 152/0 | 13636+26487 | 1/473/30 | 東洋/とうよう[15.3]@0.349, 東西/とうざい[14.4]@0.359, 東南/とうなん[13.3]@0.358, 東方/とうほう[12.9]@0.374, 東北/とうほく[12.7]@0.441 |
| `北/ほく` | 0.228 | 0.496 | 0.984 | `strong_review_pressure` | `low_or_uncertain` | restricted_admission | 124/0 | 6201+3112 | 0/161/20 | 北部/ほくぶ[12.8]@0.347, 東北/とうほく[12.7]@0.441, 北上/ほくじょう[11.1]@0.426, 北東/ほくとう[11.1]@0.410, 北西/ほくせい[11.1]@0.406 |
| `木/もく` | 0.220 | 0.494 | 0.973 | `strong_review_pressure` | `independent_supported` | score_floor,restricted_admission | 1175/0 | 8466+5175 | 1/145/17 | 樹木/じゅもく[14.2]@0.389, 木曜/もくよう[13.1]@0.261, 木造/もくぞう[13.0]@0.377, 木材/もくざい[13.0]@0.333, 材木/ざいもく[12.7]@0.449 |
| `都/と` | 0.128 | 0.493 | 0.945 | `strong_review_pressure` | `independent_supported` | restricted_admission | 15743/723 | 27667+9729 | 1/143/24 | 都市/とし[17.1]@0.190, 都会/とかい[15.2]@0.251, 首都/しゅと[13.3]@0.243, 帝都/ていと[10.8]@0.536, 都内/とない[10.4]@0.369 |
| `塩/えん` | 0.220 | 0.491 | 0.964 | `strong_review_pressure` | `low_or_uncertain` | score_floor,restricted_admission | 195/0 | 4235+476 | 1/245/13 | 食塩/しょくえん[10.7]@0.415, 塩分/えんぶん[10.6]@0.377, 塩田/えんでん[9.5]@0.484, 塩化/えんか[9.1]@0.433, 塩素/えんそ[9.1]@0.417 |
| `園/えん` | 0.220 | 0.465 | 0.948 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 1776/10543 | 19278+4604 | 1/244/29 | 公園/こうえん[16.8]@0.069, 庭園/ていえん[13.4]@0.365, 田園/でんえん[12.1]@0.432, 学園/がくえん[11.6]@0.339, 園芸/えんげい[11.5]@0.399 |
| `君/くん` | 0.220 | 0.441 | 0.924 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 150/56898 | 3601+13126 | 1/91/8 | 諸君/しょくん[15.1]@0.393, 細君/さいくん[13.9]@0.585, 君主/くんしゅ[13.0]@0.410, 君子/くんし[12.2]@0.454, 主君/しゅくん[11.6]@0.510 |
| `前/ぜん` | 0.220 | 0.429 | 0.986 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 9695/3494 | 92953+35682 | 1/509/95 | 以前/いぜん[18.5]@0.188, 午前/ごぜん[17.3]@0.057, 前後/ぜんご[16.7]@0.227, 前年/ぜんねん[15.1]@0.300, 前方/ぜんぽう[14.6]@0.334 |
| `音/おん` | 0.151 | 0.412 | 0.981 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | restricted_admission | 2397/1733 | 26390+13227 | 1/752/51 | 音楽/おんがく[17.9]@0.060, 発音/はつおん[13.9]@0.158, 音声/おんせい[13.3]@0.300, 音響/おんきょう[13.0]@0.409, 騒音/そうおん[12.8]@0.264 |
| `半/はん` | 0.100 | 0.408 | 0.976 | `strong_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 12669/8561 | 34831+19014 | 1/422/54 | 半分/はんぶん[17.4]@0.065, 半年/はんとし[15.0]@0.301, 後半/こうはん[14.4]@0.224, 半身/はんしん[14.1]@0.323, 大半/たいはん[13.8]@0.245 |
| `印/いん` | 0.269 | 0.391 | 0.983 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | restricted_admission | 763/0 | 15946+8585 | 1/287/27 | 印象/いんしょう[17.1]@0.201, 印刷/いんさつ[15.3]@0.249, 消印/けしいん[11.2]@0.472, 調印/ちょういん[10.7]@0.448, 封印/ふういん[10.7]@0.492 |
| `持ち/もち` | 0.220 | 0.377 | 0.972 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 5849/1365 | 42852+9500 | 1/191/44 | 気持ち/きもち[18.2]@0.129, 金持ち/かねもち[13.6]@0.261, 心持ち/こころもち[13.4]@0.509, 持ち主/もちぬし[13.1]@0.364, 持ち出す/もちだす[12.9]@0.370 |
| `米/べい` | 0.300 | 0.344 | 0.944 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 6199/0 | 20752+2530 | 1/263/23 | 米国/べいこく[16.2]@0.208, 欧米/おうべい[14.2]@0.320, 米穀/べいこく[9.9]@0.489, 全米/ぜんべい[9.4]@0.406, 渡米/とべい[9.3]@0.529 |
| `行き/いき` | 0.220 | 0.320 | 0.914 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 15024/2594 | 3802+1150 | 1/53/15 | 行き着く/いきつく[10.9]@0.586, 行き来/いきき[10.6]@0.409, 行き先/いきさき[10.2]@0.406, 行き交う/いきかう[9.6]@0.522, 行き届く/いきとどく[9.2]@0.452 |
| `他/た` | 0.120 | 0.314 | 0.950 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 50764/2264 | 15293+17258 | 1/126/18 | 他人/たにん[17.5]@0.226, 他方/たほう[14.6]@0.366, 他者/たしゃ[13.6]@0.354, 他国/たこく[13.2]@0.386, 他愛/たあい[11.1]@0.607 |
| `入る/いる` | 0.240 | 0.310 | 0.958 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 4057/0 | 3160+865 | 1/98/14 | 立ち入る/たちいる[10.6]@0.497, 見入る/みいる[10.4]@0.457, 恐れ入る/おそれいる[10.0]@0.584, 滅入る/めいる[9.3]@0.655, 食い入る/くいいる[8.9]@0.553 |
| `村/そん` | 0.300 | 0.307 | 0.945 | `moderate_review_pressure` | `compound_rich_but_standalone_supported` | score_floor,restricted_admission | 8562/0 | 5999+4847 | 1/74/15 | 農村/のうそん[15.3]@0.373, 村長/そんちょう[12.9]@0.409, 村落/そんらく[12.3]@0.527, 山村/さんそん[12.1]@0.444, 村民/そんみん[11.6]@0.454 |
| `黄色/おうしょく` | 0.110 | 0.062 | 0.057 | `low_review_pressure` | `compound_rich_but_standalone_supported` | restricted_admission | 683/0 | 0+1 | 1/10/1 | 緑黄色/りょくおうしょく[0.7] |

## Interpretation

- `high_confidence_compound_component`: strongest candidates for restricted admission or a frequency-ease discount.
- `medium_confidence_compound_component`: review candidates; useful for recall, not safe as an automatic correction by itself.
- `compound_rich_but_standalone_supported`: many compounds exist, but exact independent support or exact priority argues against demotion.
- `independent_supported`: this probe should not be used to demote the row.
- JMDict vocabulary-graph evidence counts only reading-compatible compounds: prefix, suffix, or multi-mora internal reading matches.
