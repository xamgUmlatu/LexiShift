# en-ja JMDict Family Admission Review

This is a sidecar diagnostic only. It does not change ranking scores, manual corrections, admission, or runtime behavior.

Ranking CSV: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv`
JMDict path: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/jmdict-ja-en/JMdict_e`
Visible cutoff: top `5000` rows

## Policy

- Family source: JMDict `ent_seq`.
- No heuristic same-surface or same-reading merging.
- A row is assigned to a family only when its surface+reading pair maps unambiguously to one JMDict entry.
- Ambiguous pairs and same-surface different-entry rows are reported only.

## Summary

| Metric | Value |
| --- | ---: |
| `ranking_rows` | `73752` |
| `jmdict_family_count` | `217464` |
| `mapped_rows` | `70964` |
| `unmapped_visible_rows` | `12` |
| `ambiguous_visible_rows` | `220` |
| `multirow_family_count` | `2057` |
| `visible_multirow_family_count` | `37` |
| `safe_visible_family_count` | `4` |
| `caution_visible_family_count` | `33` |
| `review_only_visible_family_count` | `0` |
| `visible_suppressed_sibling_count` | `40` |

## Visible Multirow Families

### `jmdict:1578010`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `魚/さかな` score `0.075508` admission `normal_vocab`
- Visible suppressible siblings: `2`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 249 | 0.075508 | `魚/さかな` | `魚` | `normal_vocab` | `kanji_reading` |  |
| 3741 | 0.284527 | `うお/うお` | `うお` | `normal_vocab` | `reading_form` |  |
| 4218 | 0.3 | `魚/うお` | `魚` | `normal_vocab` | `kanji_reading` | score_floor |

JMDict forms: kanji `魚`, readings `うお, さかな`.
Glosses: fish

### `jmdict:1202450`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `開ける/あける` score `0.078729` admission `normal_vocab`
- Visible suppressible siblings: `2`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 268 | 0.078729 | `開ける/あける` | `開ける` | `normal_vocab` | `kanji_reading` |  |
| 452 | 0.105805 | `明ける/あける` | `明ける` | `normal_vocab` | `kanji_reading` |  |
| 477 | 0.108856 | `空ける/あける` | `空ける` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `明ける, 空ける, 開ける`, readings `あける`.
Glosses: to be away from (e.g. one's house); to begin (of the New Year); to clear out; to dawn

### `jmdict:1584660`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, jmdict_marked_form_or_reading, multiple_readings`
- Representative: `明日/あした` score `0.106568` admission `normal_vocab`
- Visible suppressible siblings: `2`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 460 | 0.106568 | `明日/あした` | `明日` | `normal_vocab` | `kanji_reading` |  |
| 2148 | 0.22 | `明日/あす` | `明日` | `normal_vocab` | `kanji_reading` | score_floor |
| 4169 | 0.298805 | `明日/みょうにち` | `明日` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `明日`, readings `あした, あす, みょうにち`.
Glosses: near future; tomorrow

### `jmdict:1576150`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `一人/ひとり` score `0.021396` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 45 | 0.021396 | `一人/ひとり` | `一人` | `normal_vocab` | `kanji_reading` |  |
| 476 | 0.108771 | `独り/ひとり` | `独り` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `一人, 独り, １人`, readings `いちにん, ひとり`.
Glosses: alone; being alone; being by oneself; being single

### `jmdict:1603990`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `町/まち` score `0.052119` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 117 | 0.052119 | `町/まち` | `町` | `normal_vocab` | `kanji_reading` |  |
| 207 | 0.068051 | `街/まち` | `街` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `町, 街`, readings `まち`.
Glosses: block; downtown; main street; neighborhood

### `jmdict:1536350`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, multiple_readings`
- Representative: `夜/よる` score `0.054322` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 129 | 0.054322 | `夜/よる` | `夜` | `normal_vocab` | `kanji_reading` |  |
| 2660 | 0.24 | `夜/よ` | `夜` | `normal_vocab` | `kanji_reading` | score_floor |

JMDict forms: kanji `夜`, readings `よ, よる`.
Glosses: dinner; evening; night

### `jmdict:1406820`

- Action: `caution_family_representative`
- Caution reasons: `contains_restricted_or_non_normal_sibling, multiple_readings`
- Representative: `村/むら` score `0.056017` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 139 | 0.056017 | `村/むら` | `村` | `normal_vocab` | `kanji_reading` |  |
| 4215 | 0.3 | `村/そん` | `村` | `compound_or_administrative_reading` | `kanji_reading` | score_floor,restricted_admission |

JMDict forms: kanji `村`, readings `そん, むら`.
Glosses: village

### `jmdict:1342540`

- Action: `safe_family_representative`
- Caution reasons: `none`
- Representative: `始め/はじめ` score `0.057034` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 145 | 0.057034 | `始め/はじめ` | `はじめ` | `normal_vocab` | `kanji_reading` | display_only |
| 300 | 0.083814 | `初め/はじめ` | `初め` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `初め, 始め`, readings `はじめ`.
Glosses: beginning; first (in line, etc.); not to mention ...; opening

### `jmdict:1404630`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `足/あし` score `0.05839` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 152 | 0.05839 | `足/あし` | `足` | `normal_vocab` | `kanji_reading` |  |
| 428 | 0.103263 | `脚/あし` | `脚` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `肢, 脚, 足`, readings `あし`.
Glosses: (one's) ride; arm (of an octopus, squid, etc.); coin; foot

### `jmdict:1202270`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_reading_restrictions, contains_restricted_or_non_normal_sibling, multiple_readings`
- Representative: `絵/え` score `0.069915` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 218 | 0.069915 | `絵/え` | `絵` | `normal_vocab` | `kanji_reading` |  |
| 2151 | 0.22 | `画/が` | `画` | `compound_or_on_reading` | `kanji_reading` | score_floor,restricted_admission |

JMDict forms: kanji `画, 絵`, readings `え, が`.
Glosses: drawing; footage; image (TV, film, etc.); painting

### `jmdict:1584360`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `毎年/まいとし` score `0.079576` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 273 | 0.079576 | `毎年/まいとし` | `毎年` | `normal_vocab` | `kanji_reading` |  |
| 420 | 0.102585 | `毎年/まいねん` | `毎年` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `毎年`, readings `まいとし, まいねん`.
Glosses: annually; every year; yearly

### `jmdict:1538160`

- Action: `caution_family_representative`
- Caution reasons: `contains_restricted_or_non_normal_sibling`
- Representative: `薬/くすり` score `0.082797` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 294 | 0.082797 | `薬/くすり` | `薬` | `normal_vocab` | `kanji_reading` |  |
| 4679 | 0.311347 | `くすり/くすり` | `くすり` | `normal_vocab` | `reading_form` |  |

JMDict forms: kanji `薬`, readings `くすり, クスリ`.
Glosses: (illegal) drug; (legal) drugs; (pottery) glaze; efficacious chemical (gunpowder, pesticide, etc.)

### `jmdict:1582820`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading, jmdict_reading_restrictions, contains_restricted_or_non_normal_sibling, multiple_readings`
- Representative: `入り口/いりぐち` score `0.089068` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 328 | 0.089068 | `入り口/いりぐち` | `入り口` | `normal_vocab` | `kanji_reading` |  |
| 2164 | 0.22 | `入り口/いりくち` | `入り口` | `variant_reading` | `kanji_reading` | score_floor,restricted_admission |

JMDict forms: kanji `入り口, 入口, 這入口`, readings `いりくち, いりぐち, はいりくち, はいりぐち`.
Glosses: approach; entrance; entry; gate

### `jmdict:1231690`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading, multiple_readings`
- Representative: `去年/きょねん` score `0.090593` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 336 | 0.090593 | `去年/きょねん` | `去年` | `normal_vocab` | `kanji_reading` |  |
| 4135 | 0.297742 | `去年/こぞ` | `去年` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `去年`, readings `きょねん, こぞ`.
Glosses: last year

### `jmdict:1001140`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading, multiple_readings`
- Representative: `ええ/ええ` score `0.097373` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 375 | 0.097373 | `ええ/ええ` | `ええ` | `normal_vocab` | `reading_form` |  |
| 2557 | 0.235834 | `えー/えー` | `えー` | `normal_vocab` | `reading_form` |  |

JMDict forms: kanji `-`, readings `え〜, ええ, えー, えーっ, えーー`.
Glosses: errr; gah; good; grrr

### `jmdict:1586270`

- Action: `caution_family_representative`
- Caution reasons: `contains_restricted_or_non_normal_sibling`
- Representative: `空く/あく` score `0.098898` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 384 | 0.098898 | `空く/あく` | `空く` | `normal_vocab` | `kanji_reading` |  |
| 455 | 0.106059 | `開く/あく` | `開く` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `明く, 空く, 開く`, readings `あく`.
Glosses: to be available; to be empty; to be free; to be open (e.g. neckline, etc.)

### `jmdict:1457440`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading, multiple_readings`
- Representative: `豚肉/ぶたにく` score `0.102161` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 415 | 0.102161 | `豚肉/ぶたにく` | `豚肉` | `normal_vocab` | `kanji_reading` |  |
| 4235 | 0.300364 | `豚肉/とんにく` | `豚肉` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `ぶた肉, ブタ肉, 豚肉`, readings `とんにく, ぶたにく`.
Glosses: pork

### `jmdict:1576760`

- Action: `caution_family_representative`
- Caution reasons: `contains_restricted_or_non_normal_sibling, multiple_readings`
- Representative: `黄色/きいろ` score `0.105042` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 444 | 0.105042 | `黄色/きいろ` | `黄色` | `normal_vocab` | `kanji_reading` |  |
| 487 | 0.110042 | `黄色/おうしょく` | `黄色` | `formal_or_on_reading` | `kanji_reading` | restricted_admission |

JMDict forms: kanji `黄色`, readings `おうしょく, きいろ, こうしょく`.
Glosses: amber; yellow

### `jmdict:1584640`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, jmdict_marked_form_or_reading, multiple_readings`
- Representative: `あさって/あさって` score `0.10911` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 479 | 0.10911 | `あさって/あさって` | `あさって` | `normal_vocab` | `reading_form` |  |
| 1112 | 0.166412 | `明後日/みょうごにち` | `明後日` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `明後日`, readings `あさって, みょうごにち`.
Glosses: day after tomorrow; wrong (e.g. direction)

### `jmdict:1009290`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading`
- Representative: `どれ/どれ` score `0.109195` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 480 | 0.109195 | `どれ/どれ` | `どれ` | `normal_vocab` | `reading_form` |  |
| 1373 | 0.182119 | `何れ/どれ` | `何れ` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `何れ`, readings `どれ`.
Glosses: c'mon; now; well; which (of three or more)

### `jmdict:1253020`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, jmdict_marked_form_or_reading, jmdict_reading_restrictions, multiple_readings`
- Representative: `鳥肉/とりにく` score `0.117246` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 507 | 0.117246 | `鳥肉/とりにく` | `鳥肉` | `normal_vocab` | `kanji_reading` |  |
| 1427 | 0.185105 | `鶏肉/けいにく` | `鶏肉` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `とり肉, 鳥肉, 鶏肉`, readings `けいにく, ちょうにく, とりにく`.
Glosses: bird meat; chicken meat; fowl; poultry

### `jmdict:1215230`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, jmdict_marked_form_or_reading, multiple_readings`
- Representative: `間/あいだ` score `0.127669` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 615 | 0.127669 | `間/あいだ` | `間` | `normal_vocab` | `kanji_reading` |  |
| 4251 | 0.300737 | `間/あわい` | `間` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `間`, readings `あいだ, あわい`.
Glosses: among (a group); average; because of; between (two parties or things)

### `jmdict:1303050`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `山中/さんちゅう` score `0.139066` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 755 | 0.139066 | `山中/さんちゅう` | `山中` | `normal_vocab` | `kanji_reading` |  |
| 1763 | 0.203446 | `山中/やまなか` | `山中` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `山中`, readings `さんちゅう, やまなか`.
Glosses: among the mountains; in the mountains

### `jmdict:1605630`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading`
- Representative: `軟らかい/やわらかい` score `0.154661` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 966 | 0.154661 | `軟らかい/やわらかい` | `軟らかい` | `normal_vocab` | `kanji_reading` |  |
| 1012 | 0.157373 | `柔らかい/やわらかい` | `柔らかい` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `柔かい, 柔らかい, 軟らかい`, readings `やわらかい`.
Glosses: adaptable; flexible; flexible (thinking, mind, etc.); gentle

### `jmdict:1527110`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, multiple_readings`
- Representative: `未だ/まだ` score `0.168616` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1146 | 0.168616 | `未だ/まだ` | `未だ` | `normal_vocab` | `kanji_reading` |  |
| 1434 | 0.185452 | `未だ/いまだ` | `未だ` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `未だ`, readings `いまだ, まだ`.
Glosses: (more) still; (not) yet; as yet; at least

### `jmdict:1012050`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `まあ/まあ` score `0.168898` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1151 | 0.168898 | `まあ/まあ` | `まあ` | `normal_vocab` | `reading_form` |  |
| 1644 | 0.197767 | `まー/まー` | `まー` | `normal_vocab` | `reading_form` |  |

JMDict forms: kanji `-`, readings `ま, まぁ, まあ, まー`.
Glosses: Hmmm, I guess so ...; I think ...; come now; fairly

### `jmdict:1538900`

- Action: `caution_family_representative`
- Caution reasons: `contains_restricted_or_non_normal_sibling`
- Representative: `唯/ただ` score `0.171893` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1202 | 0.171893 | `唯/ただ` | `唯` | `normal_vocab` | `kanji_reading` |  |
| 2095 | 0.217775 | `只/ただ` | `只` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `但, 只, 唯, 常, 徒`, readings `ただ, タダ`.
Glosses: as is; but; common; free of charge

### `jmdict:1220810`

- Action: `safe_family_representative`
- Caution reasons: `none`
- Representative: `機械/きかい` score `0.21625` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 2059 | 0.21625 | `機械/きかい` | `機械` | `normal_vocab` | `kanji_reading` |  |
| 3521 | 0.270083 | `器械/きかい` | `器械` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `器械, 機械`, readings `きかい`.
Glosses: apparatus; appliance; instrument; machine

### `jmdict:1162920`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_reading_restrictions, multiple_readings`
- Representative: `一時/ひととき` score `0.230395` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 2426 | 0.230395 | `一時/ひととき` | `一時` | `normal_vocab` | `kanji_reading` |  |
| 4064 | 0.295426 | `一時/いっとき` | `一時` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `ひと時, 一時`, readings `いっとき, ひととき`.
Glosses: a (short) time; a period; a while; former times

### `jmdict:1603500`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `保障/ほしょう` score `0.243326` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 2743 | 0.243326 | `保障/ほしょう` | `保障` | `normal_vocab` | `kanji_reading` |  |
| 2914 | 0.250139 | `保証/ほしょう` | `保証` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `保証, 保障`, readings `ほしょう`.
Glosses: assurance; guarantee; pledge; security

### `jmdict:1260670`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions, jmdict_marked_form_or_reading`
- Representative: `基/もと` score `0.251279` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 2953 | 0.251279 | `基/もと` | `基` | `normal_vocab` | `kanji_reading` |  |
| 3534 | 0.271193 | `素/もと` | `素` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `元, 因, 基, 本, 素`, readings `もと`.
Glosses: (one's) side; (raw) material; (soup) stock; (tree) trunk

### `jmdict:1590600`

- Action: `safe_family_representative`
- Caution reasons: `none`
- Representative: `科目/かもく` score `0.252821` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3003 | 0.252821 | `科目/かもく` | `科目` | `normal_vocab` | `kanji_reading` |  |
| 3560 | 0.277543 | `課目/かもく` | `課目` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `科目, 課目`, readings `かもく`.
Glosses: (school) subject; course; curriculum; entry

### `jmdict:1231650`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_sense_restrictions`
- Representative: `去る/さる` score `0.254547` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3063 | 0.254547 | `去る/さる` | `去る` | `normal_vocab` | `kanji_reading` |  |
| 3562 | 0.277851 | `避る/さる` | `避る` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `去る, 避る`, readings `さる`.
Glosses: last ... (e.g. "last April"); to (do) completely; to be distant; to divorce

### `jmdict:1240810`

- Action: `safe_family_representative`
- Caution reasons: `none`
- Representative: `勤め/つとめ` score `0.264257` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3372 | 0.264257 | `勤め/つとめ` | `勤め` | `normal_vocab` | `kanji_reading` |  |
| 3515 | 0.269867 | `務め/つとめ` | `務め` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `務め, 勤め`, readings `つとめ`.
Glosses: Buddhist religious services; business; duty; responsibility

### `jmdict:1582870`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `年月/としつき` score `0.264411` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3377 | 0.264411 | `年月/としつき` | `年月` | `normal_vocab` | `kanji_reading` |  |
| 3459 | 0.267371 | `年月/ねんげつ` | `年月` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `年月`, readings `としつき, ねんげつ`.
Glosses: months and years

### `jmdict:1582960`

- Action: `caution_family_representative`
- Caution reasons: `jmdict_marked_form_or_reading, multiple_readings`
- Representative: `梅雨/つゆ` score `0.265613` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 3414 | 0.265613 | `梅雨/つゆ` | `梅雨` | `normal_vocab` | `kanji_reading` |  |
| 3551 | 0.27557 | `梅雨/ばいう` | `梅雨` | `normal_vocab` | `kanji_reading` |  |

JMDict forms: kanji `梅雨, 黴雨`, readings `つゆ, ばいう`.
Glosses: (East Asian) rainy season (in Japan, usu. from early June to mid-July); rain during the rainy season

### `jmdict:1098360`

- Action: `caution_family_representative`
- Caution reasons: `multiple_readings`
- Representative: `バザー/ばざー` score `0.304688` admission `normal_vocab`
- Visible suppressible siblings: `1`

| Rank | Score | Row | Display | Admission | Pair | Flags |
| ---: | ---: | --- | --- | --- | --- | --- |
| 4412 | 0.304688 | `バザー/ばざー` | `バザー` | `normal_vocab` | `reading_form` |  |
| 4895 | 0.316889 | `バザール/ばざーる` | `バザール` | `normal_vocab` | `reading_form` |  |

JMDict forms: kanji `-`, readings `バザー, バザール`.
Glosses: bazaar; bazar; special sale (at a department store)


## Same Surface, Different JMDict Entries

These are explicit non-merges: JMDict maps the visible rows to different entries.

### `居る`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 3 | 0.001577 | `居る/いる` | `jmdict:1577980` | `normal_vocab` |
| 2656 | 0.24 | `居る/おる` | `jmdict:1577985` | `variant_reading` |

### `中`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 14 | 0.006982 | `中/なか` | `jmdict:1423310` | `normal_vocab` |
| 2150 | 0.22 | `中/ちゅう` | `jmdict:1620400` | `compound_or_suffix_reading` |

### `前`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 19 | 0.009234 | `前/まえ` | `jmdict:1392580` | `normal_vocab` |
| 2147 | 0.22 | `前/ぜん` | `jmdict:1392570` | `compound_or_affix_reading` |

### `入る`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 31 | 0.01509 | `入る/はいる` | `jmdict:1465590` | `normal_vocab` |
| 2659 | 0.24 | `入る/いる` | `jmdict:1465580` | `variant_or_compound_reading` |

### `後`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 37 | 0.017793 | `後/あと` | `jmdict:1269320` | `normal_vocab` |
| 1340 | 0.18 | `後/のち` | `jmdict:1269330` | `normal_vocab` |
| 2146 | 0.22 | `後/ご` | `jmdict:2147630` | `compound_or_affix_reading` |

### `他`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 40 | 0.019144 | `他/ほか` | `jmdict:1203260` | `normal_vocab` |
| 535 | 0.12 | `他/た` | `jmdict:1949190` | `compound_or_formal_reading` |

### `上`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 42 | 0.020045 | `上/うえ` | `jmdict:1352130` | `normal_vocab` |
| 2156 | 0.22 | `上/じょう` | `jmdict:1352170` | `compound_or_suffix_reading` |
| 4217 | 0.3 | `上/かみ` | `jmdict:1352150` | `formal_or_spatial_variant` |

### `家`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 67 | 0.031757 | `家/いえ` | `jmdict:1191730` | `normal_vocab` |
| 2343 | 0.227415 | `家/や` | `jmdict:2082160` | `normal_vocab` |

### `開く`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 73 | 0.034459 | `開く/ひらく` | `jmdict:1202440` | `normal_vocab` |
| 455 | 0.106059 | `開く/あく` | `jmdict:1586270` | `normal_vocab` |

### `側`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 87 | 0.041216 | `側/がわ` | `jmdict:1581310` | `normal_vocab` |
| 335 | 0.090424 | `側/そば` | `jmdict:1403830` | `normal_vocab` |

### `水`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 106 | 0.049775 | `水/みず` | `jmdict:1371260` | `normal_vocab` |
| 2155 | 0.22 | `水/すい` | `jmdict:2153780` | `compound_or_on_reading` |

### `下`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 137 | 0.055678 | `下/した` | `jmdict:1184140` | `normal_vocab` |
| 2153 | 0.22 | `下/げ` | `jmdict:2080200` | `compound_or_suffix_reading` |
| 2658 | 0.24 | `下/もと` | `jmdict:2004390` | `variant_reading` |

### `道`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 153 | 0.058559 | `道/みち` | `jmdict:1454080` | `normal_vocab` |
| 2657 | 0.24 | `道/どう` | `jmdict:2158900` | `compound_reading_only` |

### `朝`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 177 | 0.062966 | `朝/あさ` | `jmdict:1428280` | `normal_vocab` |
| 2326 | 0.226745 | `朝/ちょう` | `jmdict:1428285` | `compound_or_on_reading` |

### `東`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 201 | 0.067034 | `東/ひがし` | `jmdict:1447440` | `normal_vocab` |
| 2320 | 0.226526 | `東/とう` | `jmdict:2869019` | `compound_or_directional_reading` |

### `木`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 217 | 0.069746 | `木/き` | `jmdict:1534520` | `normal_vocab` |
| 2154 | 0.22 | `木/もく` | `jmdict:2248570` | `compound_or_on_reading` |

### `塩`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 222 | 0.070593 | `塩/しお` | `jmdict:1576630` | `normal_vocab` |
| 2162 | 0.22 | `塩/えん` | `jmdict:2847901` | `compound_or_on_reading` |

### `西`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 226 | 0.071271 | `西/にし` | `jmdict:1380840` | `normal_vocab` |
| 2348 | 0.227601 | `西/せい` | `jmdict:2394070` | `compound_or_directional_reading` |

### `風`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 230 | 0.071949 | `風/かぜ` | `jmdict:1499720` | `normal_vocab` |
| 248 | 0.075339 | `風/ふう` | `jmdict:1499730` | `normal_vocab` |

### `辛い`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 240 | 0.073983 | `辛い/つらい` | `jmdict:1365860` | `normal_vocab` |
| 438 | 0.104449 | `辛い/からい` | `jmdict:1365850` | `normal_vocab` |

### `空`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 292 | 0.082458 | `空/そら` | `jmdict:1245290` | `normal_vocab` |
| 443 | 0.104873 | `空/から` | `jmdict:1245280` | `normal_vocab` |

### `兄`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 296 | 0.083136 | `兄/あに` | `jmdict:1249900` | `normal_vocab` |
| 347 | 0.092458 | `兄/にい` | `jmdict:2254970` | `normal_vocab` |

### `空く`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 384 | 0.098898 | `空く/あく` | `jmdict:1586270` | `normal_vocab` |
| 427 | 0.103178 | `空く/すく` | `jmdict:1586265` | `normal_vocab` |

### `妹`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 390 | 0.099915 | `妹/いもうと` | `jmdict:1524590` | `normal_vocab` |
| 4148 | 0.298147 | `妹/いも` | `jmdict:2752050` | `normal_vocab` |

### `傘`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 401 | 0.100805 | `傘/かさ` | `jmdict:1301940` | `normal_vocab` |
| 4124 | 0.297511 | `傘/からかさ` | `jmdict:1774770` | `normal_vocab` |

### `姉`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 408 | 0.101483 | `姉/ねえ` | `jmdict:2266990` | `variant_or_address_reading` |
| 437 | 0.104364 | `姉/あね` | `jmdict:1307630` | `normal_vocab` |

### `角`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 454 | 0.105975 | `角/かど` | `jmdict:1206110` | `normal_vocab` |
| 768 | 0.14 | `角/かく` | `jmdict:1206100` | `normal_vocab` |

### `弾く`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 459 | 0.106483 | `弾く/ひく` | `jmdict:1419370` | `normal_vocab` |
| 2159 | 0.22 | `弾く/はじく` | `jmdict:1419360` | `normal_vocab` |

### `昨夜`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 468 | 0.1075 | `昨夜/ゆうべ` | `jmdict:1542640` | `normal_vocab` |
| 2152 | 0.22 | `昨夜/さくや` | `jmdict:2863052` | `normal_vocab` |

### `君`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 513 | 0.117924 | `君/きみ` | `jmdict:1247250` | `normal_vocab` |
| 2166 | 0.22 | `君/くん` | `jmdict:1247260` | `suffix_or_title_reading` |
| 4137 | 0.2978 | `君/きんじ` | `jmdict:2697540` | `normal_vocab` |

### `悪`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 550 | 0.121372 | `悪/あく` | `jmdict:1151230` | `normal_vocab` |
| 3550 | 0.275185 | `悪/わる` | `jmdict:1151240` | `normal_vocab` |

### `何時`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 559 | 0.1225 | `何時/いつ` | `jmdict:1188760` | `normal_vocab` |
| 2429 | 0.23044 | `何時/なんどき` | `jmdict:2844601` | `normal_vocab` |

### `一時`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 564 | 0.122924 | `一時/いちじ` | `jmdict:1576100` | `normal_vocab` |
| 2426 | 0.230395 | `一時/ひととき` | `jmdict:1162920` | `normal_vocab` |
| 4064 | 0.295426 | `一時/いっとき` | `jmdict:1162920` | `normal_vocab` |

### `様`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 565 | 0.123263 | `様/よう` | `jmdict:1605840` | `normal_vocab` |
| 1307 | 0.178164 | `様/さま` | `jmdict:1545790` | `normal_vocab` |

### `訳`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 603 | 0.126653 | `訳/わけ` | `jmdict:1538330` | `normal_vocab` |
| 968 | 0.154774 | `訳/やく` | `jmdict:2057030` | `compound_or_on_reading` |

### `間`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 615 | 0.127669 | `間/あいだ` | `jmdict:1215230` | `normal_vocab` |
| 4216 | 0.3 | `間/かん` | `jmdict:2067900` | `compound_or_interval_reading` |
| 4251 | 0.300737 | `間/あわい` | `jmdict:1215230` | `normal_vocab` |

### `都`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 616 | 0.127754 | `都/と` | `jmdict:1621470` | `administrative_or_on_reading` |
| 1029 | 0.158446 | `都/みやこ` | `jmdict:1444950` | `normal_vocab` |

### `表`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 690 | 0.133856 | `表/ひょう` | `jmdict:1489350` | `normal_vocab` |
| 876 | 0.14928 | `表/おもて` | `jmdict:1489340` | `normal_vocab` |

### `打つ`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 699 | 0.134534 | `打つ/うつ` | `jmdict:1408810` | `normal_vocab` |
| 4219 | 0.3 | `打つ/ぶつ` | `jmdict:1408815` | `normal_vocab` |

### `音`

| Rank | Score | Row | JMDict family | Admission |
| ---: | ---: | --- | --- | --- |
| 702 | 0.134788 | `音/おと` | `jmdict:1576900` | `normal_vocab` |
| 896 | 0.150593 | `音/おん` | `jmdict:2859161` | `compound_or_on_reading` |
| 4220 | 0.3 | `音/ね` | `jmdict:2859162` | `normal_vocab` |


## Ambiguous Visible Rows

These rows matched multiple JMDict entries for the same surface+reading pair, so no family assignment was made.

| Rank | Score | Row | Ambiguous entries | Admission |
| ---: | ---: | --- | --- | --- |
| 2 | 0.000676 | `はい/はい` | `1010080, 1201860, 1472870, 1563260, 1586010, 1633870, 1901390, 2019640` | `normal_vocab` |
| 9 | 0.005 | `いい/いい` | `2571360, 2672300, 2672310, 2672320, 2672330, 2820690, 2846378, 2846386` | `normal_vocab` |
| 12 | 0.006081 | `つく/つく` | `1331530, 1422970, 1441400, 1444150, 1456890, 1495740, 1566940, 2097190` | `exclude_standalone_srs` |
| 13 | 0.006532 | `どう/どう` | `1000050, 1008910, 1451160, 1451730, 1453640, 1454010, 1582390, 2158900` | `normal_vocab` |
| 38 | 0.018243 | `もう/もう` | `1012480, 1912250, 2081490, 2127920, 2434690, 2844205` | `normal_vocab` |
| 235 | 0.073136 | `家/うち` | `1191740, 1457730` | `normal_vocab` |
| 363 | 0.095169 | `コート/こーと` | `1049000, 2842174` | `normal_vocab` |
| 398 | 0.100551 | `いや/いや` | `1587610, 2580180, 2830360, 2857380` | `normal_vocab` |
| 406 | 0.101314 | `ペン/ぺん` | `1121380, 5000059` | `normal_vocab` |
| 457 | 0.106314 | `マッチ/まっち` | `1128430, 2784220` | `normal_vocab` |
| 465 | 0.106992 | `いえ/いえ` | `1191730, 1583250` | `normal_vocab` |
| 481 | 0.10928 | `ほう/ほう` | `1515270, 1515620, 1516930, 1517150, 1517560, 1518370, 1591300, 2180310` | `normal_vocab` |
| 488 | 0.110127 | `おおい/おおい` | `1407460, 1501480, 1674140, 2427860, 2853873` | `normal_vocab` |
| 495 | 0.113008 | `じゃ/じゃ` | `1005900, 1323350, 2842999, 2851029` | `normal_vocab` |
| 510 | 0.117585 | `バス/ばす` | `1098390, 2845312, 2845314, 2845315` | `normal_vocab` |
| 511 | 0.117669 | `パン/ぱん` | `1103090, 2827858, 2850596, 2850597` | `normal_vocab` |
| 512 | 0.117839 | `ボタン/ぼたん` | `1123880, 1182880` | `normal_vocab` |
| 519 | 0.118686 | `ペット/ぺっと` | `1120990, 2189230` | `normal_vocab` |
| 524 | 0.11911 | `フォーク/ふぉーく` | `1110110, 2848171` | `normal_vocab` |
| 525 | 0.119195 | `コップ/こっぷ` | `1050390, 2846389, 5000045` | `normal_vocab` |
| 563 | 0.122839 | `ああ/ああ` | `1565440, 2085080, 2252550` | `normal_vocab` |
| 577 | 0.124534 | `キャップ/きゃっぷ` | `1041620, 2857548` | `normal_vocab` |
| 578 | 0.124619 | `そう/そう` | `1006610, 1176700, 1241450, 1272690, 1290810, 1375190, 1398030, 1398670` | `normal_vocab` |
| 595 | 0.125975 | `こう/こう` | `1004310, 1167880, 1272630, 1272680, 1275120, 1277850, 1278370, 1280050` | `normal_vocab` |
| 712 | 0.135551 | `妻/つま` | `1294330, 2746070, 2852371` | `normal_vocab` |
| 811 | 0.143602 | `うん/うん` | `1001090, 1172610, 1957130, 2759530` | `normal_vocab` |
| 856 | 0.1475 | `さっき/さっき` | `1005180, 1299060, 1373000, 2827653, 2848393, 2853309` | `normal_vocab` |
| 936 | 0.152853 | `尤も/もっとも` | `1293700, 1535810` | `normal_vocab` |
| 952 | 0.153757 | `あんな/あんな` | `1000590, 2090240` | `normal_vocab` |
| 974 | 0.155113 | `鏡/かがみ` | `1238550, 2017840` | `normal_vocab` |
| 1050 | 0.159746 | `ベル/べる` | `1120010, 2857911` | `normal_vocab` |
| 1060 | 0.160424 | `おや/おや` | `1001560, 1365040` | `normal_vocab` |
| 1078 | 0.162345 | `あ/あ` | `1149990, 1196670, 2220160, 2394370, 2844412` | `normal_vocab` |
| 1079 | 0.162458 | `かっこう/かっこう` | `1204960, 1204970, 1206270, 1208680, 1577480, 1590480, 1650780, 2605390` | `normal_vocab` |
| 1080 | 0.162853 | `ちゃん/ちゃん` | `1007660, 1497610` | `normal_vocab` |
| 1081 | 0.163136 | `まず/まず` | `1387240, 2783660` | `normal_vocab` |
| 1082 | 0.163249 | `もし/もし` | `1012500, 1912410, 2607730` | `normal_vocab` |
| 1098 | 0.165565 | `ビル/びる` | `1106010, 2856006` | `normal_vocab` |
| 1114 | 0.166525 | `アルバイト/あるばいと` | `1019420, 2855080` | `normal_vocab` |
| 1121 | 0.166921 | `ソウル/そうる` | `1075370, 2843957` | `normal_vocab` |
