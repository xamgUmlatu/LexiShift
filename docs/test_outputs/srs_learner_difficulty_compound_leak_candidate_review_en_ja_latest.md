# en-ja Compound Leak Candidate Review

This is a sidecar review pack only. It does not change canonical ranking, manual corrections, admission, or runtime behavior.

## Selected Variant

- Variant: `guard_probe_combined_log_t0.94_p0.5_l2_scopestrict_component_core_guard_core1_standordinary_noun_direct`
- Scope: `strict_component_core_guard`
- Standalone guard: `ordinary_noun_direct`
- Leak threshold/power: `0.94` / `0.5`

## Summary

- Changed rows under candidate: `71`
- Already-manual confirmations: `35`
- Safe auto-restrict candidates: `1`
- Score-lift/restriction review candidates: `2`
- Review-only candidates: `33`
- Rows protected by standalone guard vs legacy behavior: `11`
- Existing manual compoundish misses: `5`

## Metrics

| Split | Balanced | MAE |
| --- | ---: | ---: |
| Calibration | 0.790897 | 0.2032 |
| Holdout | 0.910723 | 0.084609 |

## Safe Auto-Restrict Candidates

| Row | Base -> Candidate | Delta | Direct/Cx | Leak | Action | Reasons | Examples |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `縁/えん` | 0.25914 -> 0.275363 | 0.016223 | 3079/13532 | 0.981923 | `propose_restricted_admission_no_canonical_score_change_yet` | kanjidic_on; guard= | 縁側/えんがわ, 縁起/えんぎ, 無縁/むえん, 縁談/えんだん, 離縁/りえん |

## Score-Lift / Restriction Review Candidates

| Row | Base -> Candidate | Delta | Direct/Cx | Leak | Action | Reasons | Examples |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `線/せん` | 0.135127 -> 0.168819 | 0.033692 | 26897/47569 | 0.979112 | `review_for_restricted_admission_and_optional_score_floor` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 視線/しせん, 曲線/きょくせん, 光線/こうせん, 直線/ちょくせん, 線路/せんろ |
| `服/ふく` | 0.074153 -> 0.107059 | 0.032906 | 10859/25094 | 0.959883 | `review_for_restricted_admission_and_optional_score_floor` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 洋服/ようふく, 服装/ふくそう, 衣服/いふく, 征服/せいふく, 制服/せいふく |

## Review-Only Candidates

| Row | Base -> Candidate | Delta | Direct/Cx | Leak | Action | Reasons | Examples |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `変/へん` | 0.142839 -> 0.172597 | 0.029758 | 15952/88225 | 0.97358 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 大変/たいへん, 変化/へんか, 変更/へんこう, 変動/へんどう, 変形/へんけい |
| `土/ど` | 0.21036 -> 0.238769 | 0.028409 | 15512/41446 | 0.97697 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 国土/こくど, 土曜/どよう, 土間/どま, 土手/どて, 領土/りょうど |
| `語/ご` | 0.175282 -> 0.200768 | 0.025486 | 27311/46544 | 0.979111 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 英語/えいご, 言語/げんご, 用語/ようご, 国語/こくご, 落語/らくご |
| `金/きん` | 0.180254 -> 0.204138 | 0.023884 | 47041/115561 | 0.985485 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,very_strong_direct_priority,on_component_discount | 資金/しきん, 金額/きんがく, 金属/きんぞく, 借金/しゃっきん, 金銭/きんせん |
| `大/だい` | 0.221843 -> 0.245448 | 0.023605 | 87187/199156 | 0.98647 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=on_component_discount | 大学/だいがく, 大臣/だいじん, 大事/だいじ, 大丈夫/だいじょうぶ, 大体/だいたい |
| `同/どう` | 0.196751 -> 0.219739 | 0.022988 | 22572/140390 | 0.986429 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 同様/どうよう, 共同/きょうどう, 同一/どういつ, 同士/どうし, 一同/いちどう |
| `熱/ねつ` | 0.14572 -> 0.1686 | 0.02288 | 8996/14682 | 0.959656 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 情熱/じょうねつ, 熱意/ねつい, 熱烈/ねつれつ, 発熱/はつねつ, 熱情/ねつじょう |
| `表/ひょう` | 0.133856 -> 0.156243 | 0.022387 | 28772/91694 | 0.957005 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 表現/ひょうげん, 代表/だいひょう, 表情/ひょうじょう, 表面/ひょうめん, 表示/ひょうじ |
| `量/りょう` | 0.177881 -> 0.200191 | 0.02231 | 21079/33094 | 0.971261 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 大量/たいりょう, 重量/じゅうりょう, 分量/ぶんりょう, 多量/たりょう, 測量/そくりょう |
| `性/せい` | 0.188446 -> 0.208528 | 0.020082 | 99430/122052 | 0.977054 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,very_strong_direct_priority,on_component_discount | 女性/じょせい, 性格/せいかく, 性質/せいしつ, 男性/だんせい, 個性/こせい |
| `式/しき` | 0.179689 -> 0.199348 | 0.019659 | 22772/48818 | 0.965008 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 形式/けいしき, 様式/ようしき, 公式/こうしき, 方式/ほうしき, 正式/せいしき |
| `死/し` | 0.207436 -> 0.226761 | 0.019325 | 20928/70916 | 0.980823 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 死ぬ/しぬ, 死体/したい, 死亡/しぼう, 必死/ひっし, 死者/ししゃ |
| `愛/あい` | 0.200445 -> 0.219421 | 0.018976 | 15747/42999 | 0.97403 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 愛する/あいする, 恋愛/れんあい, 愛情/あいじょう, 愛想/あいそ, 愛人/あいじん |
| `茶/ちゃ` | 0.207606 -> 0.226292 | 0.018686 | 11581/26799 | 0.976555 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_misc; guard=strong_exact_priority,on_component_discount | 茶碗/ちゃわん, 茶屋/ちゃや, 茶色/ちゃいろ, 紅茶/こうちゃ, 茶の間/ちゃのま |
| `客/きゃく` | 0.129788 -> 0.148169 | 0.018381 | 25515/17119 | 0.950922 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 観客/かんきゃく, 乗客/じょうきゃく, 顧客/こきゃく, 来客/らいきゃく, 客間/きゃくま |
| `差/さ` | 0.199463 -> 0.217578 | 0.018115 | 11489/37070 | 0.970409 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 差別/さべつ, 差す/さす, 差し/さし, 差異/さい, 差し出す/さしだす |
| `曲/きょく` | 0.187712 -> 0.204816 | 0.017104 | 13827/15310 | 0.961732 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 戯曲/ぎきょく, 曲線/きょくせん, 作曲/さっきょく, 謡曲/ようきょく, 曲折/きょくせつ |
| `対/たい` | 0.215869 -> 0.232203 | 0.016334 | 9459/235838 | 0.975307 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 反対/はんたい, 対象/たいしょう, 絶対/ぜったい, 対立/たいりつ, 対する/たいする |
| `肉/にく` | 0.082627 -> 0.098786 | 0.016159 | 12185/27355 | 0.971279 | `review_only_no_auto_action` | kanjidic_on; guard=strong_exact_priority | 肉体/にくたい, 皮肉/ひにく, 筋肉/きんにく, 牛肉/ぎゅうにく, 肉親/にくしん |
| `王/おう` | 0.207564 -> 0.223022 | 0.015458 | 16620/25746 | 0.966192 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 女王/じょおう, 王子/おうじ, 国王/こくおう, 大王/だいおう, 王国/おうこく |
| `悪/あく` | 0.121372 -> 0.136078 | 0.014706 | 5979/25855 | 0.978365 | `review_only_no_auto_action` | kanjidic_on; guard=strong_exact_priority | 悪魔/あくま, 罪悪/ざいあく, 悪意/あくい, 最悪/さいあく, 悪人/あくにん |
| `案/あん` | 0.221292 -> 0.233801 | 0.012509 | 8639/36870 | 0.963659 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 案内/あんない, 案外/あんがい, 提案/ていあん, 思案/しあん, 法案/ほうあん |
| `真/しん` | 0.223708 -> 0.23564 | 0.011932 | 11290/63951 | 0.96186 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_misc; guard=strong_exact_priority,on_component_discount | 写真/しゃしん, 真実/しんじつ, 真理/しんり, 真剣/しんけん, 真相/しんそう |
| `生/せい` | 0.267555 -> 0.27897 | 0.011415 | 33536/310728 | 0.985563 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=on_component_discount | 生活/せいかつ, 先生/せんせい, 人生/じんせい, 生産/せいさん, 生命/せいめい |
| `旧/きゅう` | 0.230572 -> 0.241666 | 0.011094 | 9024/8178 | 0.963914 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 復旧/ふっきゅう, 旧来/きゅうらい, 旧友/きゅうゆう, 旧式/きゅうしき, 新旧/しんきゅう |
| `花/はな` | 0.060085 -> 0.071017 | 0.010932 | 41530/13919 | 0.961141 | `review_only_no_auto_action` | jmdict_component_misc; guard=kanjidic_kun,strong_exact_priority,strong_exact_commonness | 花火/はなび, 花嫁/はなよめ, 花見/はなみ, 花束/はなたば, 菜の花/なのはな |
| `赤/あか` | 0.084492 -> 0.095112 | 0.01062 | 11947/29972 | 0.964723 | `review_only_no_auto_action` | jmdict_component_misc; guard=kanjidic_kun | 赤い/あかい, 赤ん坊/あかんぼう, 赤ちゃん/あかちゃん, 赤字/あかじ, 赤色/あかいろ |
| `詩/し` | 0.102076 -> 0.112519 | 0.010443 | 13814/13232 | 0.955758 | `review_only_no_auto_action` | kanjidic_on; guard=strong_exact_priority | 詩人/しじん, 詩集/ししゅう, 詩的/してき, 漢詩/かんし, 詩文/しぶん |
| `職/しょく` | 0.247013 -> 0.257288 | 0.010275 | 5771/54209 | 0.973603 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 職業/しょくぎょう, 職人/しょくにん, 職員/しょくいん, 職場/しょくば, 就職/しゅうしょく |
| `無/む` | 0.266507 -> 0.276751 | 0.010244 | 26733/113000 | 0.987657 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=on_component_discount | 無理/むり, 無論/むろん, 無駄/むだ, 無視/むし, 無限/むげん |
| `青/あお` | 0.099237 -> 0.109426 | 0.010189 | 7533/22216 | 0.96339 | `review_only_no_auto_action` | jmdict_component_pos,jmdict_component_misc; guard=kanjidic_kun,strong_exact_priority | 青い/あおい, 青空/あおぞら, 青白い/あおじろい, 青色/あおいろ, 青々/あおあお |
| `字/じ` | 0.142161 -> 0.152261 | 0.0101 | 15254/45013 | 0.973376 | `review_only_no_auto_action` | kanjidic_on; guard=strong_exact_priority,strong_exact_commonness | 文字/もじ, 数字/すうじ, 漢字/かんじ, 十字/じゅうじ, 活字/かつじ |
| `質/しつ` | 0.246674 -> 0.256731 | 0.010057 | 9850/86062 | 0.97179 | `review_only_no_auto_action` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 質問/しつもん, 物質/ぶっしつ, 性質/せいしつ, 本質/ほんしつ, 実質/じっしつ |

## Already-Manual Confirmations

| Row | Base -> Candidate | Delta | Direct/Cx | Leak | Action | Reasons | Examples |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `下/げ` | 0.103686 -> 0.183686 | 0.08 | 146/28935 | 0.989391 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,tiny_direct_mass; guard= | 上下/じょうげ, 下宿/げしゅく, 下駄/げた, 下落/げらく, 下旬/げじゅん |
| `南/なん` | 0.115381 -> 0.19532 | 0.079939 | 67/17625 | 0.989857 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos,weak_exact_same_surface,tiny_direct_mass; guard=on_component_discount | 南部/なんぶ, 南北/なんぼく, 東南/とうなん, 南方/なんぽう, 西南/せいなん |
| `水/すい` | 0.12019 -> 0.186335 | 0.066145 | 12747/77825 | 0.989807 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 水準/すいじゅん, 水道/すいどう, 水面/すいめん, 水平/すいへい, 海水/かいすい |
| `道/どう` | 0.051271 -> 0.116428 | 0.065157 | 16561/90451 | 0.986438 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_misc; guard=strong_exact_commonness,on_component_discount | 道路/どうろ, 道具/どうぐ, 道徳/どうとく, 鉄道/てつどう, 報道/ほうどう |
| `木/もく` | 0.116838 -> 0.181784 | 0.064946 | 1175/13641 | 0.973435 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 樹木/じゅもく, 木曜/もくよう, 木造/もくぞう, 木材/もくざい, 材木/ざいもく |
| `中/ちゅう` | 0.095508 -> 0.158957 | 0.063449 | 83416/203570 | 0.989044 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=on_component_discount | 中心/ちゅうしん, 途中/とちゅう, 中央/ちゅうおう, 中国/ちゅうごく, 中学/ちゅうがく |
| `画/が` | 0.101229 -> 0.161565 | 0.060336 | 5578/57991 | 0.973913 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on; guard= | 映画/えいが, 画家/がか, 画面/がめん, 画像/がぞう, 絵画/かいが |
| `塩/えん` | 0.108517 -> 0.165859 | 0.057342 | 195/4711 | 0.963848 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_misc,weak_exact_same_surface,tiny_direct_mass; guard=on_component_discount | 食塩/しょくえん, 塩分/えんぶん, 塩田/えんでん, 塩化/えんか, 塩素/えんそ |
| `前/ぜん` | 0.052797 -> 0.107292 | 0.054495 | 13189/128635 | 0.985516 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 以前/いぜん, 午前/ごぜん, 前後/ぜんご, 前年/ぜんねん, 前方/ぜんぽう |
| `取り/とり` | 0.10086 -> 0.154547 | 0.053687 | 8413/93367 | 0.986572 | `keep_existing_manual:score_floor,restricted_admission` | jmdict_component_pos,nominalized_stem_surface; guard= | 取り上げる/とりあげる, 取り出す/とりだす, 取り扱い/とりあつかい, 取り扱う/とりあつかう, 取り引き/とりひき |
| `火/か` | 0.175781 -> 0.227467 | 0.051686 | 4633/27341 | 0.98604 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 火事/かじ, 火災/かさい, 火山/かざん, 火星/かせい, 火曜/かよう |
| `半/はん` | 0.050932 -> 0.100018 | 0.049086 | 21230/53845 | 0.976378 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,strong_exact_commonness,on_component_discount | 半分/はんぶん, 半年/はんとし, 後半/こうはん, 半身/はんしん, 大半/たいはん |
| `門/もん` | 0.086864 -> 0.130293 | 0.043429 | 16047/40167 | 0.977105 | `keep_existing_manual:score_floor` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 専門/せんもん, 部門/ぶもん, 門前/もんぜん, 入門/にゅうもん, 一門/いちもん |
| `上/じょう` | 0.104195 -> 0.14405 | 0.039855 | 92388/178894 | 0.98737 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,very_strong_direct_priority,on_component_discount | 以上/いじょう, 地上/ちじょう, 上手/じょうず, 向上/こうじょう, 上下/じょうげ |
| `後/ご` | 0.03536 -> 0.072657 | 0.037297 | 63895/117468 | 0.958604 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos; guard=strong_exact_commonness,on_component_discount | 最後/さいご, 午後/ごご, 今後/こんご, 前後/ぜんご, 以後/いご |
| `西/せい` | 0.227601 -> 0.261298 | 0.033697 | 1/20194 | 0.997608 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_misc,weak_exact_same_surface,tiny_direct_mass,audit_high_confidence; guard=on_component_discount | 西洋/せいよう, 西暦/せいれき, 西部/せいぶ, 西方/せいほう, 西南/せいなん |
| `角/かく` | 0.104958 -> 0.13856 | 0.033602 | 12365/32145 | 0.966526 | `keep_existing_manual:score_floor` | kanjidic_on,jmdict_component_pos,jmdict_component_misc; guard=strong_exact_priority,on_component_discount | 折角/せっかく, 角度/かくど, 一角/いっかく, 三角/さんかく, 四角/しかく |
| `間/かん` | 0.153701 -> 0.186778 | 0.033077 | 22348/196796 | 0.966041 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos; guard=on_component_discount | 時間/じかん, 年間/ねんかん, 瞬間/しゅんかん, 空間/くうかん, 週間/しゅうかん |
| `用/よう` | 0.156186 -> 0.188668 | 0.032482 | 37323/204748 | 0.985592 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 利用/りよう, 使用/しよう, 用意/ようい, 作用/さよう, 信用/しんよう |
| `音/おん` | 0.150593 -> 0.18272 | 0.032127 | 4130/39617 | 0.981324 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_pos; guard=strong_exact_priority,on_component_discount | 音楽/おんがく, 発音/はつおん, 音声/おんせい, 音響/おんきょう, 騒音/そうおん |
| `東/とう` | 0.226526 -> 0.258184 | 0.031658 | 152/40123 | 0.98937 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc,weak_exact_same_surface,tiny_direct_mass; guard=on_component_discount | 東洋/とうよう, 東西/とうざい, 東南/とうなん, 東方/とうほう, 東北/とうほく |
| `北/ほく` | 0.22838 -> 0.257549 | 0.029169 | 124/9313 | 0.984109 | `keep_existing_manual:restricted_admission` | kanjidic_on,weak_exact_same_surface,tiny_direct_mass; guard= | 北部/ほくぶ, 東北/とうほく, 北上/ほくじょう, 北東/ほくとう, 北西/ほくせい |
| `見/けん` | 0.243514 -> 0.269615 | 0.026101 | 6/74473 | 0.996779 | `keep_existing_manual:restricted_admission` | kanjidic_on,tiny_direct_mass,audit_high_confidence; guard= | 発見/はっけん, 意見/いけん, 見物/けんぶつ, 一見/いっけん, 見当/けんとう |
| `訳/やく` | 0.154774 -> 0.179712 | 0.024938 | 4602/10358 | 0.950853 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_pos; guard=on_component_discount | 翻訳/ほんやく, 通訳/つうやく, 訳者/やくしゃ, 訳す/やくす, 英訳/えいやく |
| `朝/ちょう` | 0.226745 -> 0.246084 | 0.019339 | 1748/24114 | 0.965652 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc,weak_exact_same_surface; guard=on_component_discount | 朝鮮/ちょうせん, 朝食/ちょうしょく, 早朝/そうちょう, 朝廷/ちょうてい, 王朝/おうちょう |
| `園/えん` | 0.111144 -> 0.129106 | 0.017962 | 12319/23882 | 0.948084 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_pos,jmdict_component_misc,weak_exact_same_surface; guard=strong_exact_priority,on_component_discount | 公園/こうえん, 庭園/ていえん, 田園/でんえん, 学園/がくえん, 園芸/えんげい |
| `地/じ` | 0.260676 -> 0.278455 | 0.017779 | 73/50625 | 0.99436 | `keep_existing_manual:restricted_admission` | kanjidic_on,tiny_direct_mass; guard= | 地震/じしん, 地面/じめん, 地獄/じごく, 意地/いじ, 地主/じぬし |
| `夜/よ` | 0.108008 -> 0.125584 | 0.017576 | 112/14595 | 0.989351 | `keep_existing_manual:score_floor` | weak_exact_same_surface,tiny_direct_mass; guard=kanjidic_kun,strong_exact_priority | 夜中/よなか, 夜明け/よあけ, 月夜/つきよ, 夜空/よぞら, 毎夜/まいよ |
| `都/と` | 0.127754 -> 0.143135 | 0.015381 | 16466/37396 | 0.945396 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_pos; guard=strong_exact_commonness,on_component_discount | 都市/とし, 都会/とかい, 首都/しゅと, 帝都/ていと, 都内/とない |
| `徒/と` | 0.258924 -> 0.273585 | 0.014661 | 2020/19738 | 0.973877 | `keep_existing_manual:restricted_admission` | kanjidic_on; guard= | 生徒/せいと, 徒歩/とほ, 信徒/しんと, 使徒/しと, 学徒/がくと |
| `持ち/もち` | 0.070586 -> 0.083732 | 0.013146 | 7214/52352 | 0.972359 | `keep_existing_manual:score_floor,restricted_admission` | jmdict_component_pos,nominalized_stem_surface; guard=strong_exact_priority | 気持ち/きもち, 金持ち/かねもち, 心持ち/こころもち, 持ち主/もちぬし, 持ち出す/もちだす |
| `入る/いる` | 0.072966 -> 0.084453 | 0.011487 | 4057/4025 | 0.958227 | `keep_existing_manual:score_floor,restricted_admission` | jmdict_component_pos; guard=strong_exact_priority | 立ち入る/たちいる, 見入る/みいる, 恐れ入る/おそれいる, 滅入る/めいる, 食い入る/くいいる |
| `米/べい` | 0.128347 -> 0.13978 | 0.011433 | 14672/23282 | 0.944155 | `keep_existing_manual:score_floor,restricted_admission` | kanjidic_on,jmdict_component_misc; guard=strong_exact_commonness,on_component_discount | 米国/べいこく, 欧米/おうべい, 米穀/べいこく, 全米/ぜんべい, 渡米/とべい |
| `密/みつ` | 0.250817 -> 0.262063 | 0.011246 | 1700/21891 | 0.959244 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 秘密/ひみつ, 厳密/げんみつ, 精密/せいみつ, 親密/しんみつ, 密度/みつど |
| `印/いん` | 0.268573 -> 0.279299 | 0.010726 | 763/24531 | 0.982878 | `keep_existing_manual:restricted_admission` | kanjidic_on,jmdict_component_misc; guard=on_component_discount | 印象/いんしょう, 印刷/いんさつ, 消印/けしいん, 調印/ちょういん, 封印/ふういん |

## Protected By Standalone Guard

| Row | Base | Legacy delta | Direct/Cx | Leak | Guard | Reasons | Examples |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `会/かい` | 0.168672 | 0.024301 | 73075/242788 | 0.979149 | 0.92 | strong_exact_priority,strong_exact_commonness,very_strong_direct_priority,on_component_discount,direct_high_first_ordinary_noun | 社会/しゃかい, 会社/かいしゃ, 機会/きかい, 会議/かいぎ, 会話/かいわ |
| `分/ぶん` | 0.122585 | 0.039887 | 34840/454237 | 0.987343 | 0.92 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_ordinary_noun | 自分/じぶん, 部分/ぶぶん, 十分/じゅうぶん, 気分/きぶん, 半分/はんぶん |
| `別/べつ` | 0.126737 | 0.029048 | 42007/63394 | 0.966326 | 0.97 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_plain_noun | 特別/とくべつ, 区別/くべつ, 差別/さべつ, 別々/べつべつ, 個別/こべつ |
| `図/ず` | 0.175904 | 0.018309 | 42700/22179 | 0.960388 | 0.92 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_ordinary_noun | 地図/ちず, 合図/あいず, 指図/さしず, 構図/こうず, 図面/ずめん |
| `地/ち` | 0.173757 | 0.028557 | 41645/223438 | 0.987927 | 0.92 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_ordinary_noun | 地方/ちほう, 土地/とち, 地球/ちきゅう, 地域/ちいき, 地上/ちじょう |
| `山/やま` | 0.048423 | 0.016996 | 42748/30070 | 0.98145 | 0.92 | kanjidic_kun,strong_exact_priority,strong_exact_commonness,direct_high_first_ordinary_noun | 山々/やまやま, 山奥/やまおく, 山の手/やまのて, 小山/こやま, 山伏/やまぶし |
| `市/し` | 0.124788 | 0.020172 | 56331/70027 | 0.952415 | 0.92 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_ordinary_noun | 都市/とし, 市民/しみん, 市場/しじょう, 市街/しがい, 市長/しちょう |
| `数/すう` | 0.17178 | 0.026488 | 48356/77458 | 0.979972 | 0.9 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_plain_noun | 多数/たすう, 数学/すうがく, 数字/すうじ, 無数/むすう, 少数/しょうすう |
| `本/ほん` | 0.055339 | 0.05037 | 68302/213395 | 0.988461 | 0.97 | strong_exact_priority,strong_exact_commonness,very_strong_direct_priority,on_component_discount,direct_high_first_plain_noun | 本当/ほんとう, 資本/しほん, 基本/きほん, 本来/ほんらい, 本人/ほんにん |
| `法/ほう` | 0.171836 | 0.027736 | 57775/139730 | 0.983864 | 0.92 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_ordinary_noun | 方法/ほうほう, 法律/ほうりつ, 法則/ほうそく, 手法/しゅほう, 魔法/まほう |
| `風/ふう` | 0.075339 | 0.047203 | 34674/39787 | 0.981348 | 0.97 | strong_exact_priority,strong_exact_commonness,on_component_discount,direct_high_first_plain_noun | 風景/ふうけい, 風俗/ふうぞく, 風習/ふうしゅう, 風流/ふうりゅう, 風土/ふうど |

## Manual Misses

| Row | Score | Manual Types | Admission | Direct/Cx | Leak | Note |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `他/た` | 0.12 | score_floor,restricted_admission | compound_or_formal_reading | 53028/ | 0.950312 | not enough guarded compound-leak pressure; likely needs separate lexical/admission rule |
| `君/くん` | 0.22 | score_floor,restricted_admission | suffix_or_title_reading | 57048/ | 0.923802 | not enough guarded compound-leak pressure; likely needs separate lexical/admission rule |
| `村/そん` | 0.3 | score_floor,restricted_admission | compound_or_administrative_reading | 8599/ | 0.945122 | not enough guarded compound-leak pressure; likely needs separate lexical/admission rule |
| `行き/いき` | 0.22 | score_floor,restricted_admission | derived_or_suffix_form | 17618/ | 0.914189 | not enough guarded compound-leak pressure; likely needs separate lexical/admission rule |
| `黄色/おうしょく` | 0.110042 | restricted_admission | formal_or_on_reading | 683/ | 0.057375 | not enough guarded compound-leak pressure; likely needs separate lexical/admission rule |

## Interpretation

- `safe_auto_restrict` means the signal looks strong enough to propose restricted admission, but this pack still does not apply it.
- `score_lift_candidate` means the row has real component pressure but needs product review before any score floor or admission change.
- `protected_by_guard` are rows the older component-leak shape would have moved, but the standalone guard now keeps.
- Existing manual misses are a reminder that compound leak is not meant to solve every awkward standalone-admission case.
