# en-ja Learner Difficulty Final Ranking Review

## Summary

- Variant: `exgate_orth_ec06_fl044_fh058_mr022_xcr0_ts04_te06_sp05`
- Base candidate: `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap`
- Full ranking CSV: `docs/test_outputs/srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv`
- Component count: `73752`
- Manual corrections applied: `True`
- Selection score: `0.6164`
- MAE: `0.129196`
- Pairwise accuracy: `0.844103`
- Improved/regressed labels >=0.01: `45` / `1`

The full ranking is sorted by final score, then core rank, then surface and reading.

## Band Counts

| Band | Count | Cumulative |
| --- | ---: | ---: |
| 0.00-0.05 | 106 | 106 |
| 0.05-0.10 | 284 | 390 |
| 0.10-0.15 | 494 | 884 |
| 0.15-0.20 | 799 | 1683 |
| 0.20-0.25 | 1226 | 2909 |
| 0.25-0.30 | 1304 | 4213 |
| 0.30-0.35 | 1926 | 6139 |
| 0.35-0.40 | 3094 | 9233 |
| 0.40-0.45 | 3928 | 13161 |
| 0.45-0.50 | 4805 | 17966 |
| 0.50-0.55 | 5177 | 23143 |
| 0.55-0.60 | 5902 | 29045 |
| 0.60-0.65 | 4383 | 33428 |
| 0.65-0.70 | 4901 | 38329 |
| 0.70-0.75 | 5506 | 43835 |
| 0.75-0.80 | 6423 | 50258 |
| 0.80-0.85 | 7566 | 57824 |
| 0.85-0.90 | 7569 | 65393 |
| 0.90-0.95 | 6004 | 71397 |
| 0.95-1.00 | 2355 | 73752 |

## Manual Correction Summary

| Row | Status | Types | Applied | Model | Effective | Delta | Display | Admission | Topic stretch |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| いい/いい | active | score_override | True | 0.112 | 0.005 | -0.107 |  | normal_vocab | True |
| けつまんこ/けつまんこ | active | restricted_admission | False | 0.897 | 0.897 | 0.000 |  | sensitive_or_adult_vocab | False |
| つく/つく | active | exclude_standalone_srs | False | 0.006 | 0.006 | 0.000 |  | exclude_standalone_srs | False |
| ワイシャツ/わいしゃつ | active | score_floor | True | 0.001 | 0.080 | 0.079 |  | normal_vocab | True |
| 一言/いちげん | active | score_floor,restricted_admission | True | 0.273 | 0.400 | 0.127 |  | variant_reading | False |
| 丈夫/じょうふ | active | score_floor,restricted_admission | True | 0.115 | 0.350 | 0.235 |  | rare_reading | False |
| 上/かみ | active | score_floor,restricted_admission | True | 0.108 | 0.300 | 0.192 |  | formal_or_spatial_variant | False |
| 上/じょう | active | score_floor,restricted_admission | True | 0.104 | 0.220 | 0.116 |  | compound_or_suffix_reading | False |
| 上手/うわて | active | score_floor | True | 0.115 | 0.350 | 0.235 |  | normal_vocab | True |
| 下/げ | active | score_floor,restricted_admission | True | 0.104 | 0.220 | 0.116 |  | compound_or_suffix_reading | False |
| 下/しも | active | score_floor | True | 0.115 | 0.350 | 0.235 |  | normal_vocab | True |
| 下/もと | active | score_floor,restricted_admission | True | 0.062 | 0.240 | 0.178 |  | variant_reading | False |
| 中/ちゅう | active | score_floor,restricted_admission | True | 0.096 | 0.220 | 0.124 |  | compound_or_suffix_reading | False |
| 中々/なかなか | active | display_only | False | 0.136 | 0.136 | 0.000 | なかなか | normal_vocab | True |
| 事/こと | active | display_only | False | 0.120 | 0.120 | 0.000 | こと | normal_vocab | True |
| 今日/こんにち | active | score_floor,restricted_admission | True | 0.089 | 0.350 | 0.261 |  | formal_or_written_reading | False |
| 今日は/こんにちは | active | display_only | False | 0.153 | 0.153 | 0.000 | こんにちは | normal_vocab | True |
| 仏/ぶつ | active | score_floor,restricted_admission | True | 0.340 | 0.450 | 0.110 |  | compound_or_on_reading | False |
| 他/た | active | score_floor,restricted_admission | True | 0.031 | 0.120 | 0.089 |  | compound_or_formal_reading | False |
| 伍/ご | active | score_floor,restricted_admission | True | 0.115 | 0.450 | 0.335 |  | rare_or_military_reading | False |
| 会/え | active | score_floor,restricted_admission | True | 0.273 | 0.400 | 0.127 |  | rare_or_bound_reading | False |
| 伯父/おじ | active | display_only | False | 0.092 | 0.092 | 0.000 | おじ | normal_vocab | True |
| 体/てい | active | score_floor,restricted_admission | True | 0.110 | 0.350 | 0.240 |  | rare_or_technical_reading | False |
| 何の/どの | active | display_only | False | 0.130 | 0.130 | 0.000 | どの | normal_vocab | True |
| 何人/なにびと | review | restricted_admission | False | 0.230 | 0.230 | 0.000 |  | rare_or_literary_reading | False |
| 何処/どこ | active | display_only | False | 0.025 | 0.025 | 0.000 | どこ | normal_vocab | True |
| 何時/いつ | active | display_only | False | 0.122 | 0.122 | 0.000 | いつ | normal_vocab | True |
| 余り/あまり | active | display_only | False | 0.055 | 0.055 | 0.000 | あまり | normal_vocab | True |
| 偶に/たまに | active | display_only | False | 0.151 | 0.151 | 0.000 | たまに | normal_vocab | True |
| 僕/しもべ | active | score_floor | True | 0.164 | 0.350 | 0.186 |  | normal_vocab | True |
| 入り口/いりくち | active | score_floor,restricted_admission | True | 0.115 | 0.220 | 0.105 |  | variant_reading | False |
| 入る/いる | active | score_floor,restricted_admission | True | 0.073 | 0.240 | 0.167 |  | variant_or_compound_reading | False |
| 凄い/すごい | active | display_only | False | 0.133 | 0.133 | 0.000 | すごい | normal_vocab | True |
| 出掛ける/でかける | active | display_only | False | 0.079 | 0.079 | 0.000 | 出かける | normal_vocab | True |
| 前/ぜん | active | score_floor,restricted_admission | True | 0.053 | 0.220 | 0.167 |  | compound_or_affix_reading | False |
| 包む/くるむ | active | score_floor | True | 0.164 | 0.300 | 0.136 |  | normal_vocab | True |
| 北/ほく | active | restricted_admission | False | 0.228 | 0.228 | 0.000 |  | compound_or_directional_reading | False |
| 半/はん | active | score_floor,restricted_admission | True | 0.051 | 0.100 | 0.049 |  | compound_or_prefix_reading | False |
| 南/なん | active | score_floor,restricted_admission | True | 0.115 | 0.220 | 0.105 |  | compound_reading | False |
| 印/いん | active | restricted_admission | False | 0.269 | 0.269 | 0.000 |  | compound_or_on_reading | False |
| 取り/とり | active | score_floor,restricted_admission | True | 0.101 | 0.220 | 0.119 |  | derived_or_suffix_form | False |
| 古/いにしえ | active | score_floor | True | 0.130 | 0.450 | 0.320 |  | normal_vocab | True |
| 吐く/つく | review | restricted_admission | False | 0.252 | 0.252 | 0.000 |  | variant_reading | False |
| 君/くん | active | score_floor,restricted_admission | True | 0.118 | 0.220 | 0.102 |  | suffix_or_title_reading | False |
| 国境/くにざかい | active | score_floor | True | 0.270 | 0.400 | 0.130 |  | normal_vocab | True |
| 園/えん | active | score_floor,restricted_admission | True | 0.111 | 0.220 | 0.109 |  | compound_or_on_reading | False |
| 園/その | active | score_floor | True | 0.111 | 0.350 | 0.239 |  | normal_vocab | True |
| 土産/どさん | active | score_floor,restricted_admission | True | 0.274 | 0.400 | 0.126 |  | variant_or_compound_reading | False |
| 地/じ | active | restricted_admission | False | 0.261 | 0.261 | 0.000 |  | compound_or_on_reading | False |
| 塩/えん | active | score_floor,restricted_admission | True | 0.109 | 0.220 | 0.111 |  | compound_or_on_reading | False |
| 塵/ごみ | active | display_only | False | 0.147 | 0.147 | 0.000 | ごみ | normal_vocab | True |
| 夜/よ | active | score_floor | True | 0.108 | 0.240 | 0.132 |  | normal_vocab | True |
| 夜中/やちゅう | active | score_floor,restricted_admission | True | 0.274 | 0.400 | 0.126 |  | rare_or_formal_reading | False |
| 大事/おおごと | active | score_floor | True | 0.161 | 0.350 | 0.189 |  | normal_vocab | True |
| 大分/だいぶ | active | display_only | False | 0.155 | 0.155 | 0.000 | だいぶ | normal_vocab | True |
| 奇麗/きれい | active | display_only | False | 0.063 | 0.063 | 0.000 | きれい | normal_vocab | True |
| 女子/おなご | active | score_floor | True | 0.274 | 0.400 | 0.126 |  | normal_vocab | True |
| 奴/やっこ | active | score_floor | True | 0.328 | 0.450 | 0.122 |  | normal_vocab | True |
| 姉/ねえ | active | restricted_admission | False | 0.101 | 0.101 | 0.000 |  | variant_or_address_reading | False |
| 始め/はじめ | active | display_only | False | 0.057 | 0.057 | 0.000 | はじめ | normal_vocab | True |
| 字/あざ | active | score_floor,restricted_admission | True | 0.164 | 0.350 | 0.186 |  | rare_or_place_reading | False |
| 字引き/じびき | active | score_floor | True | 0.116 | 0.350 | 0.234 |  | normal_vocab | True |
| 家/うち | active | display_only | False | 0.073 | 0.073 | 0.000 | うち | normal_vocab | True |
| 密/みつ | active | restricted_admission | False | 0.251 | 0.251 | 0.000 |  | compound_or_bound_reading | False |
| 尤も/もっとも | active | display_only | False | 0.153 | 0.153 | 0.000 | もっとも | normal_vocab | True |
| 居/きょ | active | score_floor,restricted_admission | True | 0.081 | 0.350 | 0.269 |  | compound_or_sino_morpheme | False |
| 居る/いる | active | display_only | False | 0.002 | 0.002 | 0.000 | いる | normal_vocab | True |
| 居る/おる | active | score_floor,restricted_admission | True | 0.014 | 0.240 | 0.226 |  | variant_reading | False |
| 山/さん | active | score_floor,restricted_admission | True | 0.298 | 0.400 | 0.102 |  | compound_or_on_reading | False |
| 工場/こうば | active | score_floor | True | 0.164 | 0.350 | 0.186 |  | normal_vocab | True |
| 市/いち | active | score_floor | True | 0.158 | 0.350 | 0.192 |  | normal_vocab | True |
| 床/とこ | active | score_floor | True | 0.266 | 0.350 | 0.084 |  | normal_vocab | True |
| 弾く/はじく | active | score_floor | True | 0.107 | 0.220 | 0.113 |  | normal_vocab | True |
| 後/ご | active | score_floor,restricted_admission | True | 0.035 | 0.220 | 0.185 |  | compound_or_affix_reading | False |
| 後/のち | active | score_floor | True | 0.086 | 0.180 | 0.094 |  | normal_vocab | True |
| 徒/と | active | restricted_admission | False | 0.259 | 0.259 | 0.000 |  | compound_or_on_reading | False |
| 御飯/ごはん | active | display_only | False | 0.077 | 0.077 | 0.000 | ご飯 | normal_vocab | True |
| 必用/ひつよう | active | score_floor,restricted_admission | True | 0.164 | 0.450 | 0.286 |  | orthographic_variant | False |
| 怒る/いかる | active | score_floor | True | 0.161 | 0.350 | 0.189 |  | normal_vocab | True |
| 成る/なる | active | display_only | False | 0.002 | 0.002 | 0.000 | なる | normal_vocab | True |
| 或いは/あるいは | watch | display_only | False | 0.175 | 0.175 | 0.000 | あるいは | normal_vocab | True |
| 戸/と | active | score_floor | True | 0.107 | 0.220 | 0.113 |  | normal_vocab | True |
| 所/ところ | active | display_only | False | 0.008 | 0.008 | 0.000 | ところ | normal_vocab | True |
| 打つ/ぶつ | active | score_floor | True | 0.161 | 0.300 | 0.139 |  | normal_vocab | True |
| 持ち/もち | active | score_floor,restricted_admission | True | 0.071 | 0.220 | 0.149 |  | derived_or_suffix_form | False |
| 敵/かたき | active | score_floor | True | 0.275 | 0.350 | 0.075 |  | normal_vocab | True |
| 文/ふみ | active | score_floor | True | 0.275 | 0.400 | 0.125 |  | normal_vocab | True |
| 方々/ほうぼう | active | score_floor | True | 0.269 | 0.350 | 0.081 |  | normal_vocab | True |
| 明く/あく | active | score_floor,restricted_admission | True | 0.107 | 0.350 | 0.243 |  | rare_orthographic_variant | False |
| 明日/あす | active | score_floor | True | 0.063 | 0.220 | 0.157 |  | normal_vocab | True |
| 易しい/やさしい | active | display_only | False | 0.111 | 0.111 | 0.000 | やさしい | normal_vocab | True |
| 昨夜/さくや | active | score_floor | True | 0.102 | 0.220 | 0.118 |  | normal_vocab | True |
| 昼間/ちゅうかん | active | score_floor,restricted_admission | True | 0.164 | 0.350 | 0.186 |  | variant_reading | False |
| 時々/じじ | review | restricted_admission | False | 0.230 | 0.230 | 0.000 |  | rare_reading | False |
| 暇/いとま | active | score_floor | True | 0.112 | 0.450 | 0.338 |  | normal_vocab | True |
| 暫く/しばらく | active | display_only | False | 0.139 | 0.139 | 0.000 | しばらく | normal_vocab | True |
| 有る/ある | active | display_only | False | 0.120 | 0.120 | 0.000 | ある | normal_vocab | True |
| 朝/ちょう | active | restricted_admission | False | 0.227 | 0.227 | 0.000 |  | compound_or_on_reading | False |
| 木/もく | active | score_floor,restricted_admission | True | 0.117 | 0.220 | 0.103 |  | compound_or_on_reading | False |
| 村/そん | active | score_floor,restricted_admission | True | 0.057 | 0.300 | 0.243 |  | compound_or_administrative_reading | False |
| 来たる/きたる | active | score_floor,restricted_admission | True | 0.063 | 0.320 | 0.257 |  | formal_or_written_variant | False |
| 東/あずま | active | score_floor | True | 0.116 | 0.500 | 0.384 |  | normal_vocab | True |
| 東/とう | active | restricted_admission | False | 0.227 | 0.227 | 0.000 |  | compound_or_directional_reading | False |
| 柄/え | active | score_floor | True | 0.275 | 0.400 | 0.125 |  | normal_vocab | True |
| 根/こん | active | score_floor,restricted_admission | True | 0.321 | 0.450 | 0.129 |  | compound_or_on_reading | False |
| 様/よう | active | display_only | False | 0.123 | 0.123 | 0.000 | よう | normal_vocab | True |
| 殆ど/ほとんど | active | display_only | False | 0.130 | 0.130 | 0.000 | ほとんど | normal_vocab | True |
| 段々/だんだん | active | display_only | False | 0.096 | 0.096 | 0.000 | だんだん | normal_vocab | True |
| 水/すい | active | score_floor,restricted_admission | True | 0.120 | 0.220 | 0.100 |  | compound_or_on_reading | False |
| 汚れる/けがれる | active | score_floor | True | 0.164 | 0.350 | 0.186 |  | normal_vocab | True |
| 流行/はやり | active | score_floor | True | 0.271 | 0.350 | 0.079 |  | normal_vocab | True |
| 温い/ぬるい | active | display_only | False | 0.116 | 0.116 | 0.000 | ぬるい | normal_vocab | True |
| 火/か | active | restricted_admission | False | 0.176 | 0.176 | 0.000 |  | compound_or_on_reading | False |
| 煩い/うるさい | active | display_only | False | 0.098 | 0.098 | 0.000 | うるさい | normal_vocab | True |
| 猶/なお | watch | display_only | False | 0.415 | 0.415 | 0.000 | なお | normal_vocab | True |
| 現場/げんじょう | active | score_floor,restricted_admission | True | 0.276 | 0.400 | 0.124 |  | variant_reading | False |
| 用/よう | active | score_floor,restricted_admission | True | 0.156 | 0.190 | 0.034 |  | compound_or_function_noun | False |
| 画/が | active | score_floor,restricted_admission | True | 0.101 | 0.220 | 0.119 |  | compound_or_on_reading | False |
| 癖/へき | active | score_floor | True | 0.340 | 0.450 | 0.110 |  | normal_vocab | True |
| 真っ直ぐ/まっすぐ | active | display_only | False | 0.100 | 0.100 | 0.000 | まっすぐ | normal_vocab | True |
| 眼鏡/がんきょう | active | score_floor,restricted_admission | True | 0.112 | 0.350 | 0.238 |  | rare_or_on_reading | False |
| 眼鏡/めがね | active | display_only | False | 0.103 | 0.103 | 0.000 | めがね | normal_vocab | True |
| 筈/はず | active | display_only | False | 0.129 | 0.129 | 0.000 | はず | normal_vocab | True |
| 米/べい | active | score_floor,restricted_admission | True | 0.128 | 0.300 | 0.172 |  | compound_or_country_reading | False |
| 良い/よい | active | score_floor | True | 0.005 | 0.080 | 0.075 |  | normal_vocab | True |
| 色々/いろいろ | active | display_only | False | 0.066 | 0.066 | 0.000 | いろいろ | normal_vocab | True |
| 苑/えん | active | score_floor,restricted_admission | True | 0.112 | 0.400 | 0.288 |  | rare_or_formal_reading | False |
| 葉書/はがき | active | score_floor | True | 0.089 | 0.220 | 0.131 |  | normal_vocab | True |
| 行き/いき | active | score_floor,restricted_admission | True | 0.099 | 0.220 | 0.121 |  | derived_or_suffix_form | False |
| 西/せい | active | restricted_admission | False | 0.228 | 0.228 | 0.000 |  | compound_or_directional_reading | False |
| 見/けん | active | restricted_admission | False | 0.244 | 0.244 | 0.000 |  | compound_or_on_reading | False |
| 角/かく | active | score_floor | True | 0.105 | 0.140 | 0.035 |  | normal_vocab | True |
| 訳/やく | active | restricted_admission | False | 0.155 | 0.155 | 0.000 |  | compound_or_on_reading | False |
| 認める/したためる | active | score_floor | True | 0.269 | 0.400 | 0.131 |  | normal_vocab | True |
| 質/しち | active | score_floor | True | 0.340 | 0.450 | 0.110 |  | normal_vocab | True |
| 身体/しんたい | active | score_floor | True | 0.073 | 0.150 | 0.077 |  | normal_vocab | True |
| 辺/ほとり | active | score_floor | True | 0.337 | 0.400 | 0.063 |  | normal_vocab | True |
| 道/どう | active | score_floor,restricted_admission | True | 0.051 | 0.240 | 0.189 |  | compound_reading_only | False |
| 都/と | active | restricted_admission | False | 0.128 | 0.128 | 0.000 |  | administrative_or_on_reading | False |
| 金庫/かねぐら | active | score_floor | True | 0.278 | 0.400 | 0.122 |  | normal_vocab | True |
| 長/おさ | active | score_floor | True | 0.105 | 0.450 | 0.345 |  | normal_vocab | True |
| 門/もん | active | score_floor | True | 0.087 | 0.130 | 0.043 |  | normal_vocab | True |
| 間/かん | active | score_floor,restricted_admission | True | 0.154 | 0.300 | 0.146 |  | compound_or_interval_reading | False |
| 雷/いかずち | active | score_floor | True | 0.278 | 0.450 | 0.172 |  | normal_vocab | True |
| 鞄/かばん | active | display_only | False | 0.099 | 0.099 | 0.000 | かばん | normal_vocab | True |
| 音/おん | active | restricted_admission | False | 0.151 | 0.151 | 0.000 |  | compound_or_on_reading | False |
| 音/ね | active | score_floor | True | 0.161 | 0.300 | 0.139 |  | normal_vocab | True |
| 頂く/いただく | active | display_only | False | 0.130 | 0.130 | 0.000 | いただく | normal_vocab | True |
| 高/こう | active | score_floor,restricted_admission | True | 0.396 | 0.400 | 0.004 |  | compound_or_on_reading | False |
| 魚/うお | active | score_floor | True | 0.109 | 0.300 | 0.191 |  | normal_vocab | True |
| 黄色/おうしょく | active | restricted_admission | False | 0.110 | 0.110 | 0.000 |  | formal_or_on_reading | False |
| 鼠/ねず | active | score_floor,restricted_admission | True | 0.279 | 0.400 | 0.121 |  | bound_or_variant_reading | False |

## First 200 Review Rows

| Rank | Word | Score | Model | Correction | Current | Core rank | Flags |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 先生/せんせい | 0.000 | 0.000 | 0.000 | 0.000 | 700.000 |  |
| 2 | はい/はい | 0.001 | 0.001 | 0.000 | 0.001 | 3023.000 |  |
| 3 | 居る/いる | 0.002 | 0.002 | 0.000 | 0.002 | 13.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=いる |
| 4 | 言う/いう | 0.002 | 0.002 | 0.000 | 0.002 | 19.000 |  |
| 5 | 成る/なる | 0.002 | 0.002 | 0.000 | 0.002 | 23.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=なる |
| 6 | 来る/くる | 0.003 | 0.003 | 0.000 | 0.003 | 46.000 | early_kana_preferred_kanji |
| 7 | 物/もの | 0.004 | 0.004 | 0.000 | 0.004 | 52.000 | early_kana_preferred_kanji |
| 8 | 行く/いく | 0.004 | 0.004 | 0.000 | 0.004 | 57.000 | early_kana_preferred_kanji |
| 9 | いい/いい | 0.005 | 0.112 | -0.107 | 0.112 |  | score_override,normal_vocab |
| 10 | 人/ひと | 0.005 | 0.005 | 0.000 | 0.005 | 64.000 | early_kana_preferred_kanji |
| 11 | 何/なに | 0.006 | 0.006 | 0.000 | 0.006 | 75.000 | early_kana_preferred_kanji |
| 12 | つく/つく | 0.006 | 0.006 | 0.000 | 0.006 | 79.000 | exclude_standalone_srs,exclude_standalone_srs |
| 13 | どう/どう | 0.007 | 0.007 | 0.000 | 0.007 | 95.000 |  |
| 14 | 中/なか | 0.007 | 0.007 | 0.000 | 0.007 | 96.000 | early_kana_preferred_kanji |
| 15 | 自分/じぶん | 0.007 | 0.007 | 0.000 | 0.007 | 99.000 |  |
| 16 | 今/いま | 0.008 | 0.008 | 0.000 | 0.008 | 106.000 |  |
| 17 | 所/ところ | 0.008 | 0.008 | 0.000 | 0.008 | 109.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=ところ |
| 18 | 問題/もんだい | 0.009 | 0.009 | 0.000 | 0.009 | 114.000 |  |
| 19 | 前/まえ | 0.009 | 0.009 | 0.000 | 0.009 | 116.000 |  |
| 20 | 使う/つかう | 0.010 | 0.010 | 0.000 | 0.010 | 121.000 |  |
| 21 | 分かる/わかる | 0.010 | 0.010 | 0.000 | 0.010 | 123.000 | early_kana_preferred_kanji |
| 22 | 持つ/もつ | 0.011 | 0.011 | 0.000 | 0.011 | 123.000 |  |
| 23 | 子供/こども | 0.011 | 0.011 | 0.000 | 0.011 | 132.000 |  |
| 24 | 取る/とる | 0.011 | 0.011 | 0.000 | 0.011 | 135.000 |  |
| 25 | 出る/でる | 0.012 | 0.012 | 0.000 | 0.012 | 138.000 |  |
| 26 | 多い/おおい | 0.012 | 0.012 | 0.000 | 0.012 | 147.000 |  |
| 27 | 作る/つくる | 0.013 | 0.013 | 0.000 | 0.013 | 150.000 |  |
| 28 | 聞く/きく | 0.013 | 0.013 | 0.000 | 0.013 | 154.000 |  |
| 29 | 高い/たかい | 0.014 | 0.014 | 0.000 | 0.014 | 160.000 |  |
| 30 | 知る/しる | 0.015 | 0.015 | 0.000 | 0.015 | 177.000 |  |
| 31 | 入る/はいる | 0.015 | 0.015 | 0.000 | 0.015 | 179.000 |  |
| 32 | 国/くに | 0.016 | 0.016 | 0.000 | 0.016 | 180.000 |  |
| 33 | 会社/かいしゃ | 0.016 | 0.016 | 0.000 | 0.016 | 182.000 |  |
| 34 | 学校/がっこう | 0.016 | 0.016 | 0.000 | 0.016 | 184.000 |  |
| 35 | 大学/だいがく | 0.017 | 0.017 | 0.000 | 0.017 | 185.000 |  |
| 36 | 方/ほう | 0.017 | 0.017 | 0.000 | 0.017 | 186.000 |  |
| 37 | 後/あと | 0.018 | 0.018 | 0.000 | 0.018 | 197.000 | early_kana_preferred_kanji |
| 38 | もう/もう | 0.018 | 0.018 | 0.000 | 0.018 | 203.000 |  |
| 39 | 置く/おく | 0.019 | 0.019 | 0.000 | 0.019 | 209.000 | early_kana_preferred_kanji |
| 40 | 他/ほか | 0.019 | 0.019 | 0.000 | 0.019 | 211.000 | early_kana_preferred_kanji |
| 41 | 目/め | 0.020 | 0.020 | 0.000 | 0.020 | 213.000 | early_kana_preferred_kanji |
| 42 | 上/うえ | 0.020 | 0.020 | 0.000 | 0.020 | 226.000 |  |
| 43 | 話/はなし | 0.020 | 0.020 | 0.000 | 0.020 | 228.000 |  |
| 44 | 出す/だす | 0.021 | 0.021 | 0.000 | 0.021 | 238.000 |  |
| 45 | 一人/ひとり | 0.021 | 0.021 | 0.000 | 0.021 | 243.000 | early_kana_preferred_kanji |
| 46 | 大きい/おおきい | 0.022 | 0.022 | 0.000 | 0.022 | 247.000 |  |
| 47 | 皆/みな | 0.022 | 0.022 | 0.000 | 0.022 | 251.000 | early_kana_preferred_kanji |
| 48 | 書く/かく | 0.023 | 0.023 | 0.000 | 0.023 | 252.000 |  |
| 49 | 仕事/しごと | 0.023 | 0.023 | 0.000 | 0.023 | 256.000 |  |
| 50 | 上げる/あげる | 0.024 | 0.024 | 0.000 | 0.024 | 268.000 | early_kana_preferred_kanji |
| 51 | 同じ/おなじ | 0.024 | 0.024 | 0.000 | 0.024 | 275.000 |  |
| 52 | 写真/しゃしん | 0.025 | 0.025 | 0.000 | 0.025 | 281.000 |  |
| 53 | 何処/どこ | 0.025 | 0.025 | 0.000 | 0.025 | 285.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=どこ |
| 54 | 電話/でんわ | 0.025 | 0.025 | 0.000 | 0.025 | 285.000 |  |
| 55 | 入れる/いれる | 0.026 | 0.026 | 0.000 | 0.026 | 290.000 |  |
| 56 | 誰/だれ | 0.026 | 0.026 | 0.000 | 0.026 | 291.000 |  |
| 57 | 食べる/たべる | 0.027 | 0.027 | 0.000 | 0.027 | 293.000 |  |
| 58 | 買う/かう | 0.027 | 0.027 | 0.000 | 0.027 | 294.000 |  |
| 59 | 教える/おしえる | 0.028 | 0.028 | 0.000 | 0.028 | 301.000 |  |
| 60 | 二人/ふたり | 0.028 | 0.028 | 0.000 | 0.028 | 302.000 |  |
| 61 | 強い/つよい | 0.029 | 0.029 | 0.000 | 0.029 | 325.000 | early_kana_preferred_kanji |
| 62 | 男/おとこ | 0.029 | 0.029 | 0.000 | 0.029 | 325.000 |  |
| 63 | 言葉/ことば | 0.030 | 0.030 | 0.000 | 0.030 | 325.000 |  |
| 64 | 今日/きょう | 0.030 | 0.030 | 0.000 | 0.030 | 331.000 |  |
| 65 | 話す/はなす | 0.030 | 0.030 | 0.000 | 0.030 | 341.000 |  |
| 66 | 女/おんな | 0.031 | 0.031 | 0.000 | 0.031 | 346.000 |  |
| 67 | 家/いえ | 0.032 | 0.032 | 0.000 | 0.032 | 360.000 | early_kana_preferred_kanji |
| 68 | 先/さき | 0.032 | 0.032 | 0.000 | 0.032 | 362.000 | early_kana_preferred_kanji |
| 69 | 大きな/おおきな | 0.033 | 0.033 | 0.000 | 0.033 | 364.000 |  |
| 70 | 切る/きる | 0.033 | 0.033 | 0.000 | 0.033 | 366.000 |  |
| 71 | 病院/びょういん | 0.034 | 0.034 | 0.000 | 0.034 | 368.000 |  |
| 72 | 少し/すこし | 0.034 | 0.034 | 0.000 | 0.034 | 370.000 |  |
| 73 | 開く/ひらく | 0.034 | 0.034 | 0.000 | 0.034 | 373.000 | early_kana_preferred_kanji |
| 74 | 少ない/すくない | 0.035 | 0.035 | 0.000 | 0.035 | 385.000 |  |
| 75 | 車/くるま | 0.036 | 0.036 | 0.000 | 0.036 | 392.000 |  |
| 76 | 声/こえ | 0.036 | 0.036 | 0.000 | 0.036 | 394.000 |  |
| 77 | 家族/かぞく | 0.037 | 0.037 | 0.000 | 0.037 | 399.000 |  |
| 78 | 外国/がいこく | 0.037 | 0.037 | 0.000 | 0.037 | 413.000 |  |
| 79 | 意味/いみ | 0.038 | 0.038 | 0.000 | 0.038 | 413.000 |  |
| 80 | 呼ぶ/よぶ | 0.038 | 0.038 | 0.000 | 0.038 | 421.000 |  |
| 81 | 欲しい/ほしい | 0.039 | 0.039 | 0.000 | 0.039 | 421.000 | early_kana_preferred_kanji |
| 82 | 今年/ことし | 0.039 | 0.039 | 0.000 | 0.039 | 425.000 |  |
| 83 | 結婚/けっこん | 0.039 | 0.039 | 0.000 | 0.039 | 425.000 |  |
| 84 | 次/つぎ | 0.040 | 0.040 | 0.000 | 0.040 | 431.000 |  |
| 85 | 違う/ちがう | 0.040 | 0.040 | 0.000 | 0.040 | 441.000 |  |
| 86 | 悪い/わるい | 0.041 | 0.041 | 0.000 | 0.041 | 448.000 | early_kana_preferred_kanji |
| 87 | 側/がわ | 0.041 | 0.041 | 0.000 | 0.041 | 457.000 | early_kana_preferred_kanji |
| 88 | 初めて/はじめて | 0.042 | 0.042 | 0.000 | 0.042 | 457.000 |  |
| 89 | 好き/すき | 0.042 | 0.042 | 0.000 | 0.042 | 462.000 |  |
| 90 | 店/みせ | 0.043 | 0.043 | 0.000 | 0.043 | 467.000 |  |
| 91 | 新しい/あたらしい | 0.043 | 0.043 | 0.000 | 0.043 | 472.000 |  |
| 92 | 黒/くろ | 0.043 | 0.043 | 0.000 | 0.043 | 472.000 |  |
| 93 | 早い/はやい | 0.044 | 0.044 | 0.000 | 0.044 | 474.000 |  |
| 94 | 料理/りょうり | 0.044 | 0.044 | 0.000 | 0.044 | 483.000 |  |
| 95 | こんな/こんな | 0.045 | 0.045 | 0.000 | 0.045 | 500.000 |  |
| 96 | 長い/ながい | 0.045 | 0.045 | 0.000 | 0.045 | 501.000 |  |
| 97 | 読む/よむ | 0.046 | 0.046 | 0.000 | 0.046 | 506.000 |  |
| 98 | 新聞/しんぶん | 0.046 | 0.046 | 0.000 | 0.046 | 513.000 |  |
| 99 | 一緒/いっしょ | 0.047 | 0.047 | 0.000 | 0.047 | 522.000 |  |
| 100 | 白/しろ | 0.047 | 0.047 | 0.000 | 0.047 | 522.000 |  |
| 101 | 立つ/たつ | 0.048 | 0.048 | 0.000 | 0.048 | 535.000 |  |
| 102 | 駅/えき | 0.048 | 0.048 | 0.000 | 0.048 | 535.000 |  |
| 103 | 山/やま | 0.048 | 0.048 | 0.000 | 0.048 | 545.000 | early_kana_preferred_kanji |
| 104 | 体/からだ | 0.049 | 0.049 | 0.000 | 0.049 | 581.000 |  |
| 105 | 始まる/はじまる | 0.049 | 0.049 | 0.000 | 0.049 | 581.000 |  |
| 106 | 水/みず | 0.050 | 0.050 | 0.000 | 0.050 | 581.000 |  |
| 107 | 乗る/のる | 0.050 | 0.050 | 0.000 | 0.050 | 586.000 |  |
| 108 | 一番/いちばん | 0.050 | 0.050 | 0.000 | 0.050 | 598.000 | early_kana_preferred_kanji |
| 109 | 歩く/あるく | 0.050 | 0.050 | 0.000 | 0.050 | 625.000 |  |
| 110 | 午後/ごご | 0.051 | 0.051 | 0.000 | 0.051 | 630.000 |  |
| 111 | 若い/わかい | 0.051 | 0.051 | 0.000 | 0.051 | 641.000 |  |
| 112 | 家庭/かてい | 0.051 | 0.051 | 0.000 | 0.051 | 647.000 |  |
| 113 | 映画/えいが | 0.051 | 0.051 | 0.000 | 0.051 | 650.000 |  |
| 114 | 終わる/おわる | 0.052 | 0.052 | 0.000 | 0.052 | 650.000 |  |
| 115 | 待つ/まつ | 0.052 | 0.052 | 0.000 | 0.052 | 661.000 |  |
| 116 | 頭/あたま | 0.052 | 0.052 | 0.000 | 0.052 | 674.000 | early_kana_preferred_kanji |
| 117 | 町/まち | 0.052 | 0.052 | 0.000 | 0.052 | 680.000 |  |
| 118 | 働く/はたらく | 0.052 | 0.052 | 0.000 | 0.052 | 682.000 |  |
| 119 | もっと/もっと | 0.052 | 0.052 | 0.000 | 0.052 | 686.000 |  |
| 120 | 飲む/のむ | 0.053 | 0.053 | 0.000 | 0.053 | 691.000 |  |
| 121 | 近く/ちかく | 0.053 | 0.053 | 0.000 | 0.053 | 718.000 |  |
| 122 | 渡る/わたる | 0.053 | 0.053 | 0.000 | 0.053 | 722.000 | early_kana_preferred_kanji |
| 123 | 質問/しつもん | 0.053 | 0.053 | 0.000 | 0.053 | 722.000 |  |
| 124 | 銀行/ぎんこう | 0.053 | 0.053 | 0.000 | 0.053 | 737.000 |  |
| 125 | 会う/あう | 0.054 | 0.054 | 0.000 | 0.054 | 746.000 | early_kana_preferred_kanji |
| 126 | 死ぬ/しぬ | 0.054 | 0.054 | 0.000 | 0.054 | 746.000 |  |
| 127 | 走る/はしる | 0.054 | 0.054 | 0.000 | 0.054 | 746.000 |  |
| 128 | 答える/こたえる | 0.054 | 0.054 | 0.000 | 0.054 | 751.000 |  |
| 129 | 夜/よる | 0.054 | 0.054 | 0.000 | 0.054 | 761.000 |  |
| 130 | 口/くち | 0.054 | 0.054 | 0.000 | 0.054 | 771.000 |  |
| 131 | 生まれる/うまれる | 0.055 | 0.055 | 0.000 | 0.055 | 784.000 |  |
| 132 | 近い/ちかい | 0.055 | 0.055 | 0.000 | 0.055 | 784.000 |  |
| 133 | ホテル/ほてる | 0.055 | 0.055 | 0.000 | 0.055 | 788.000 |  |
| 134 | 余り/あまり | 0.055 | 0.055 | 0.000 | 0.055 | 798.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=あまり |
| 135 | 本/ほん | 0.055 | 0.055 | 0.000 | 0.055 | 803.000 |  |
| 136 | 見せる/みせる | 0.056 | 0.056 | 0.000 | 0.056 | 816.000 |  |
| 137 | 下/した | 0.056 | 0.056 | 0.000 | 0.056 | 826.000 |  |
| 138 | 学生/がくせい | 0.056 | 0.056 | 0.000 | 0.056 | 826.000 |  |
| 139 | 村/むら | 0.056 | 0.056 | 0.000 | 0.056 | 826.000 |  |
| 140 | 起きる/おきる | 0.056 | 0.056 | 0.000 | 0.056 | 826.000 |  |
| 141 | 海/うみ | 0.056 | 0.056 | 0.000 | 0.056 | 832.000 |  |
| 142 | 旅行/りょこう | 0.057 | 0.057 | 0.000 | 0.057 | 841.000 |  |
| 143 | 午前/ごぜん | 0.057 | 0.057 | 0.000 | 0.057 | 861.000 |  |
| 144 | 大切/たいせつ | 0.057 | 0.057 | 0.000 | 0.057 | 861.000 |  |
| 145 | 始め/はじめ | 0.057 | 0.057 | 0.000 | 0.057 | 876.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=はじめ |
| 146 | 難しい/むずかしい | 0.057 | 0.057 | 0.000 | 0.057 | 881.000 |  |
| 147 | 大人/おとな | 0.058 | 0.058 | 0.000 | 0.058 | 901.000 |  |
| 148 | 小さい/ちいさい | 0.058 | 0.058 | 0.000 | 0.058 | 901.000 |  |
| 149 | 低い/ひくい | 0.058 | 0.058 | 0.000 | 0.058 | 907.000 |  |
| 150 | 昨日/きのう | 0.058 | 0.058 | 0.000 | 0.058 | 944.000 |  |
| 151 | 毎日/まいにち | 0.058 | 0.058 | 0.000 | 0.058 | 944.000 |  |
| 152 | 足/あし | 0.058 | 0.058 | 0.000 | 0.058 | 944.000 |  |
| 153 | 道/みち | 0.059 | 0.059 | 0.000 | 0.059 | 944.000 |  |
| 154 | 部屋/へや | 0.059 | 0.059 | 0.000 | 0.059 | 957.000 |  |
| 155 | 一日/ついたち | 0.059 | 0.059 | 0.000 | 0.059 | 964.000 |  |
| 156 | 名前/なまえ | 0.059 | 0.059 | 0.000 | 0.059 | 964.000 |  |
| 157 | 小さな/ちいさな | 0.059 | 0.059 | 0.000 | 0.059 | 971.000 |  |
| 158 | 住む/すむ | 0.059 | 0.059 | 0.000 | 0.059 | 976.000 |  |
| 159 | 並ぶ/ならぶ | 0.060 | 0.060 | 0.000 | 0.060 | 985.000 |  |
| 160 | 楽しい/たのしい | 0.060 | 0.060 | 0.000 | 0.060 | 985.000 |  |
| 161 | 忘れる/わすれる | 0.060 | 0.060 | 0.000 | 0.060 | 997.000 |  |
| 162 | 花/はな | 0.060 | 0.060 | 0.000 | 0.060 | 997.000 |  |
| 163 | 音楽/おんがく | 0.060 | 0.060 | 0.000 | 0.060 | 997.000 |  |
| 164 | 電気/でんき | 0.060 | 0.060 | 0.000 | 0.060 | 1022.000 |  |
| 165 | 安い/やすい | 0.061 | 0.061 | 0.000 | 0.061 | 1034.000 |  |
| 166 | 川/かわ | 0.061 | 0.061 | 0.000 | 0.061 | 1053.000 |  |
| 167 | 左/ひだり | 0.061 | 0.061 | 0.000 | 0.061 | 1065.000 |  |
| 168 | 上る/のぼる | 0.061 | 0.061 | 0.000 | 0.061 | 1074.000 |  |
| 169 | 色/いろ | 0.061 | 0.061 | 0.000 | 0.061 | 1074.000 |  |
| 170 | スポーツ/すぽーつ | 0.061 | 0.061 | 0.000 | 0.061 | 1092.000 |  |
| 171 | 友達/ともだち | 0.062 | 0.062 | 0.000 | 0.062 | 1102.000 |  |
| 172 | 夏/なつ | 0.062 | 0.062 | 0.000 | 0.062 | 1102.000 |  |
| 173 | 広い/ひろい | 0.062 | 0.062 | 0.000 | 0.062 | 1111.000 |  |
| 174 | 病気/びょうき | 0.062 | 0.062 | 0.000 | 0.062 | 1122.000 |  |
| 175 | 生徒/せいと | 0.062 | 0.062 | 0.000 | 0.062 | 1132.000 |  |
| 176 | カメラ/かめら | 0.063 | 0.063 | 0.000 | 0.063 | 1147.000 |  |
| 177 | 朝/あさ | 0.063 | 0.063 | 0.000 | 0.063 | 1158.000 |  |
| 178 | 歌/うた | 0.063 | 0.063 | 0.000 | 0.063 | 1158.000 |  |
| 179 | 売る/うる | 0.063 | 0.063 | 0.000 | 0.063 | 1183.000 |  |
| 180 | 奇麗/きれい | 0.063 | 0.063 | 0.000 | 0.063 | 1183.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=きれい |
| 181 | 結構/けっこう | 0.064 | 0.064 | 0.000 | 0.064 | 1206.000 |  |
| 182 | 右/みぎ | 0.064 | 0.064 | 0.000 | 0.064 | 1256.000 |  |
| 183 | 着る/きる | 0.064 | 0.064 | 0.000 | 0.064 | 1256.000 |  |
| 184 | 動物/どうぶつ | 0.064 | 0.064 | 0.000 | 0.064 | 1276.000 |  |
| 185 | 大変/たいへん | 0.064 | 0.064 | 0.000 | 0.064 | 1276.000 |  |
| 186 | 年/とし | 0.064 | 0.064 | 0.000 | 0.064 | 1276.000 |  |
| 187 | 半分/はんぶん | 0.065 | 0.065 | 0.000 | 0.065 | 1295.000 |  |
| 188 | 外/そと | 0.065 | 0.065 | 0.000 | 0.065 | 1295.000 | early_kana_preferred_kanji |
| 189 | 大丈夫/だいじょうぶ | 0.065 | 0.065 | 0.000 | 0.065 | 1315.000 |  |
| 190 | 練習/れんしゅう | 0.065 | 0.065 | 0.000 | 0.065 | 1338.000 |  |
| 191 | 覚える/おぼえる | 0.065 | 0.065 | 0.000 | 0.065 | 1338.000 |  |
| 192 | 歌う/うたう | 0.066 | 0.066 | 0.000 | 0.066 | 1354.000 |  |
| 193 | 色々/いろいろ | 0.066 | 0.066 | 0.000 | 0.066 | 1354.000 | early_kana_preferred_kanji,display_only,normal_vocab,display=いろいろ |
| 194 | ニュース/にゅーす | 0.066 | 0.066 | 0.000 | 0.066 | 1400.000 |  |
| 195 | 嫌/いや | 0.066 | 0.066 | 0.000 | 0.066 | 1400.000 | early_kana_preferred_kanji |
| 196 | 重い/おもい | 0.066 | 0.066 | 0.000 | 0.066 | 1425.000 |  |
| 197 | 北/きた | 0.066 | 0.066 | 0.000 | 0.066 | 1440.000 |  |
| 198 | 軽い/かるい | 0.067 | 0.067 | 0.000 | 0.067 | 1458.000 |  |
| 199 | 遊ぶ/あそぶ | 0.067 | 0.067 | 0.000 | 0.067 | 1458.000 |  |
| 200 | 消える/きえる | 0.067 | 0.067 | 0.000 | 0.067 | 1478.000 |  |

## Manual Watchlist Rows

| Rank | Word | Score | Model | Correction | Current | Core rank | Flags |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2979 | 吐く/つく | 0.252 | 0.252 | 0.000 | 0.252 | 3703.000 | manual_watchlist,early_kana_preferred_kanji,restricted_admission,variant_reading |
| 2422 | 時々/じじ | 0.230 | 0.230 | 0.000 | 0.122 | 9898.000 | manual_watchlist,restricted_admission,rare_reading |
| 2413 | 何人/なにびと | 0.230 | 0.230 | 0.000 | 0.121 | 17861.000 | manual_watchlist,restricted_admission,rare_or_literary_reading |
| 1256 | 或いは/あるいは | 0.175 | 0.175 | 0.000 | 0.175 | 1074.000 | manual_watchlist,early_kana_preferred_kanji,display_only,normal_vocab,display=あるいは |
| 10362 | 猶/なお | 0.415 | 0.415 | 0.000 | 0.195 | 1276.000 | manual_watchlist,display_only,normal_vocab,display=なお |

## First 200 Flag Summary

| Flag | Count |
| --- | ---: |
| early_kana_preferred_kanji | 36 |
