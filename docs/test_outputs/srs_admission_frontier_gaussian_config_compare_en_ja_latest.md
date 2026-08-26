# en-ja SRS Admission Frontier Gaussian Config Compare

- generated_at: `2026-08-26T18:42:51.104536+00:00`
- runtime_scope: `offline_selector_comparison_only`
- scenarios: `22`
- seed_count: `9222`
- set_top_n: `10000`
- initial_active_count: `40`
- corrected_ranking_available: `True`

## Overall Summary

| Metric | Legacy v5 | Frontier v1 | Hybrid v2 | Hybrid soft v3 | Frontier Delta | Hybrid Delta | Hybrid soft Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Below target by >0.20 | 67 | 14 | 0 | 16 | -53 | -67 | -51 |
| Within target ±0.10 | 328 | 729 | 704 | 688 | 401 | 376 | 360 |
| Topic selections | 262 | 69 | 172 | 188 | -193 | -90 | -74 |

## Scenario Summary

| Scenario | p | Topics | Legacy v5 mean/range | Legacy v5 topic/<p-.20 | Frontier mean/range | Frontier topic/<p-.20 | Hybrid mean/range | Hybrid topic/<p-.20 | Hybrid soft mean/range | Hybrid soft topic/<p-.20 | Hybrid soft lanes |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | ---: | --- | ---: | --- |
| `neutral_beginner` | 0.100 | - | 0.014 (0.002-0.080) | 0/0 | 0.091 (0.040-0.102) | 0/0 | 0.058 (0.002-0.101) | 0/0 | 0.058 (0.002-0.101) | 0/0 | core:16, frontier:17, trail:7 |
| `neutral_lower_intermediate` | 0.300 | - | 0.177 (0.160-0.298) | 0/0 | 0.285 (0.200-0.301) | 0/0 | 0.285 (0.200-0.301) | 0/0 | 0.285 (0.200-0.301) | 0/0 | frontier:33, trail:7 |
| `neutral_n1ish` | 0.580 | - | 0.515 (0.421-0.579) | 0/0 | 0.559 (0.450-0.581) | 0/0 | 0.559 (0.450-0.581) | 0/0 | 0.559 (0.450-0.581) | 0/0 | frontier:33, trail:7 |
| `neutral_advanced` | 0.820 | - | 0.708 (0.665-0.790) | 0/0 | 0.768 (0.692-0.937) | 0/0 | 0.768 (0.692-0.937) | 0/0 | 0.768 (0.692-0.937) | 0/0 | frontier:33, trail:7 |
| `shopping_money_intermediate` | 0.450 | shopping_money | 0.288 (0.137-0.450) | 17/11 | 0.413 (0.252-0.452) | 4/0 | 0.403 (0.250-0.452) | 6/0 | 0.387 (0.239-0.451) | 9/3 | frontier:24, topic:9, trail:7 |
| `work_office_intermediate` | 0.450 | work_office | 0.309 (0.190-0.450) | 20/7 | 0.421 (0.322-0.452) | 4/0 | 0.385 (0.250-0.451) | 13/0 | 0.375 (0.241-0.451) | 15/2 | frontier:18, topic:15, trail:7 |
| `science_math_intermediate` | 0.450 | science_math | 0.303 (0.129-0.450) | 13/9 | 0.412 (0.254-0.452) | 4/0 | 0.412 (0.254-0.452) | 4/0 | 0.384 (0.215-0.451) | 9/5 | frontier:24, topic:9, trail:7 |
| `computing_internet_intermediate` | 0.450 | computing_internet | 0.334 (0.281-0.456) | 20/0 | 0.430 (0.322-0.477) | 4/0 | 0.420 (0.322-0.513) | 17/0 | 0.420 (0.322-0.513) | 17/0 | frontier:16, topic:17, trail:7 |
| `medicine_health_intermediate` | 0.450 | medicine_health | 0.291 (0.146-0.450) | 16/12 | 0.412 (0.252-0.452) | 4/0 | 0.412 (0.252-0.452) | 4/0 | 0.378 (0.212-0.451) | 10/6 | frontier:23, topic:10, trail:7 |
| `sports_beginner` | 0.250 | sports_fitness | 0.176 (0.120-0.352) | 14/0 | 0.235 (0.165-0.299) | 4/0 | 0.228 (0.120-0.352) | 14/0 | 0.228 (0.120-0.352) | 14/0 | frontier:19, topic:14, trail:7 |
| `games_intermediate` | 0.450 | games | 0.349 (0.280-0.450) | 20/0 | 0.428 (0.322-0.452) | 4/0 | 0.415 (0.322-0.582) | 16/0 | 0.415 (0.322-0.582) | 16/0 | frontier:17, topic:16, trail:7 |
| `hobbies_crafts_intermediate` | 0.450 | hobbies_crafts | 0.352 (0.298-0.450) | 20/0 | 0.428 (0.322-0.452) | 4/0 | 0.404 (0.322-0.451) | 16/0 | 0.404 (0.322-0.451) | 16/0 | frontier:17, topic:16, trail:7 |
| `arts_literature_advanced` | 0.720 | arts_literature_humanities | 0.575 (0.428-0.596) | 1/1 | 0.666 (0.384-0.740) | 4/4 | 0.699 (0.572-0.743) | 0/0 | 0.699 (0.572-0.743) | 0/0 | frontier:33, trail:7 |
| `mixed_work_computing` | 0.500 | computing_internet, work_office | 0.397 (0.329-0.498) | 20/0 | 0.481 (0.377-0.513) | 5/0 | 0.464 (0.364-0.631) | 17/0 | 0.464 (0.364-0.631) | 17/0 | frontier:16, topic:17, trail:7 |
| `mixed_food_travel` | 0.350 | food_cooking, travel_places_transport | 0.253 (0.186-0.333) | 20/0 | 0.332 (0.242-0.357) | 4/0 | 0.311 (0.211-0.357) | 17/0 | 0.311 (0.211-0.357) | 17/0 | frontier:16, topic:17, trail:7 |
| `mixed_science_medicine` | 0.550 | science_math, medicine_health | 0.382 (0.229-0.531) | 13/13 | 0.504 (0.284-0.559) | 4/4 | 0.529 (0.415-0.562) | 0/0 | 0.529 (0.415-0.562) | 0/0 | frontier:33, trail:7 |
| `food_cooking_beginner` | 0.200 | food_cooking | 0.119 (0.027-0.199) | 20/0 | 0.187 (0.120-0.211) | 4/0 | 0.175 (0.118-0.251) | 17/0 | 0.175 (0.118-0.251) | 17/0 | frontier:16, topic:17, trail:7 |
| `anime_manga_intermediate` | 0.450 | anime_manga_pop_culture | 0.345 (0.280-0.450) | 20/0 | 0.429 (0.322-0.474) | 4/0 | 0.413 (0.322-0.505) | 17/0 | 0.413 (0.322-0.505) | 17/0 | frontier:16, topic:17, trail:7 |
| `probe_neutral_expert` | 0.930 | - | 0.861 (0.759-0.937) | 0/0 | 0.911 (0.782-0.971) | 0/0 | 0.911 (0.782-0.971) | 0/0 | 0.911 (0.782-0.971) | 0/0 | frontier:33, trail:7 |
| `probe_plants_nature_mid` | 0.440 | plants_nature | 0.319 (0.140-0.584) | 17/5 | 0.413 (0.317-0.441) | 4/0 | 0.394 (0.250-0.584) | 12/0 | 0.394 (0.250-0.584) | 12/0 | frontier:21, topic:12, trail:7 |
| `probe_plants_nature_upper` | 0.620 | plants_nature | 0.503 (0.304-0.584) | 10/9 | 0.579 (0.373-0.631) | 4/3 | 0.598 (0.488-0.633) | 1/0 | 0.598 (0.488-0.633) | 1/0 | frontier:32, topic:1, trail:7 |
| `probe_plants_nature_advanced` | 0.730 | plants_nature | 0.582 (0.569-0.720) | 1/0 | 0.679 (0.373-0.755) | 4/3 | 0.705 (0.584-0.759) | 1/0 | 0.705 (0.584-0.759) | 1/0 | frontier:32, topic:1, trail:7 |

## Scenario Details

### `neutral_beginner`

- proficiency: `0.100`
- topics: `-`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane targets: `{'core': 16, 'frontier': 17, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 16, 'frontier': 17, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 16, 'frontier': 17, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 16, 'frontier': 17, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `する` | 0.005 | - | `その` | 0.040 | trail | `する` | 0.005 | core | `する` | 0.005 | core | - |
| 2 | `いる`/いる | 0.002 | - | `私` | 0.040 | trail | `いる`/いる | 0.002 | core | `いる`/いる | 0.002 | core | - |
| 3 | `言う`/いう | 0.002 | - | `質問`/しつもん | 0.053 | trail | `言う`/いう | 0.002 | core | `言う`/いう | 0.002 | core | - |
| 4 | `なる`/なる | 0.002 | - | `頭`/あたま | 0.052 | trail | `なる`/なる | 0.002 | core | `なる`/なる | 0.002 | core | - |
| 5 | `その` | 0.040 | - | `口`/くち | 0.054 | trail | `その` | 0.040 | core | `その` | 0.040 | core | - |
| 6 | `この` | 0.030 | - | `あまり`/あまり | 0.055 | trail | `この` | 0.030 | core | `この` | 0.030 | core | - |
| 7 | `物`/もの | 0.004 | - | `水`/みず | 0.050 | trail | `物`/もの | 0.004 | core | `物`/もの | 0.004 | core | - |
| 8 | `それ` | 0.008 | - | `涼しい`/すずしい | 0.100 | frontier | `それ` | 0.008 | core | `それ` | 0.008 | core | - |
| 9 | `来る`/くる | 0.003 | - | `妹`/いもうと | 0.100 | frontier | `来る`/くる | 0.003 | core | `来る`/くる | 0.003 | core | - |
| 10 | `行く`/いく | 0.004 | - | `風邪`/かぜ | 0.100 | frontier | `行く`/いく | 0.004 | core | `行く`/いく | 0.004 | core | - |
| 11 | `これ` | 0.005 | - | `大勢`/おおぜい | 0.100 | frontier | `これ` | 0.005 | core | `これ` | 0.005 | core | - |
| 12 | `良い`/よい | 0.080 | - | `パーティー`/ぱーてぃー | 0.100 | frontier | `良い`/よい | 0.080 | core | `良い`/よい | 0.080 | core | - |

- legacy_v5_only: `する, いる, 言う, なる, この, 物, それ, 来る, 行く, これ, 良い, 何`
- frontier_only: `質問, 頭, 口, あまり, 水, 涼しい, 妹, 風邪, 大勢, パーティー, まっすぐ, 上手`
- legacy_v5_only_vs_hybrid: `中, 自分, ところ, 方, 今, 持つ, 分かる, 出る, 前, 取る, 問題, 使う`
- hybrid_only_vs_legacy_v5: `質問, 頭, 口, あまり, 水, 一番, 飲む, 涼しい, 妹, 風邪, 大勢, パーティー`
- hybrid_soft_only_vs_legacy_v5: `質問, 頭, 口, あまり, 水, 一番, 飲む, 涼しい, 妹, 風邪, 大勢, パーティー`
- hybrid_soft_only_vs_hybrid: ``

### `neutral_lower_intermediate`

- proficiency: `0.300`
- topics: `-`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `無い`/ない | 0.265 | - | `出来る`/できる | 0.223 | trail | `出来る`/できる | 0.223 | trail | `出来る`/できる | 0.223 | trail | - |
| 2 | `出来る`/できる | 0.223 | - | `定める`/さだめる | 0.213 | trail | `定める`/さだめる | 0.213 | trail | `定める`/さだめる | 0.213 | trail | - |
| 3 | `因る`/よる | 0.165 | - | `法人`/ほうじん | 0.213 | trail | `法人`/ほうじん | 0.213 | trail | `法人`/ほうじん | 0.213 | trail | - |
| 4 | `時`/とき | 0.165 | - | `年金`/ねんきん | 0.214 | trail | `年金`/ねんきん | 0.214 | trail | `年金`/ねんきん | 0.214 | trail | - |
| 5 | `ため` | 0.160 | - | `生ずる`/しょうずる | 0.214 | trail | `生ずる`/しょうずる | 0.214 | trail | `生ずる`/しょうずる | 0.214 | trail | - |
| 6 | `又`/また | 0.165 | - | `彼女` | 0.200 | trail | `彼女` | 0.200 | trail | `彼女` | 0.200 | trail | - |
| 7 | `仕舞う`/しまう | 0.165 | - | `世紀`/せいき | 0.210 | trail | `世紀`/せいき | 0.210 | trail | `世紀`/せいき | 0.210 | trail | - |
| 8 | `彼` | 0.180 | - | `あっ` | 0.300 | frontier | `あっ` | 0.300 | frontier | `あっ` | 0.300 | frontier | - |
| 9 | `遣る`/やる | 0.165 | - | `慌てる`/あわてる | 0.300 | frontier | `慌てる`/あわてる | 0.300 | frontier | `慌てる`/あわてる | 0.300 | frontier | - |
| 10 | `下さる`/くださる | 0.166 | - | `個別`/こべつ | 0.300 | frontier | `個別`/こべつ | 0.300 | frontier | `個別`/こべつ | 0.300 | frontier | - |
| 11 | `然し`/しかし | 0.168 | - | `真実`/しんじつ | 0.300 | frontier | `真実`/しんじつ | 0.300 | frontier | `真実`/しんじつ | 0.300 | frontier | - |
| 12 | `対する`/たいする | 0.167 | - | `報酬`/ほうしゅう | 0.300 | frontier | `報酬`/ほうしゅう | 0.300 | frontier | `報酬`/ほうしゅう | 0.300 | frontier | - |

- legacy_v5_only: `無い, 因る, 時, ため, 又, 仕舞う, 彼, 遣る, 下さる, 然し, 対する, 呉れる`
- frontier_only: `定める, 法人, 年金, 生ずる, 世紀, あっ, 慌てる, 個別, 真実, 報酬, セント, 本体`
- legacy_v5_only_vs_hybrid: `無い, 因る, 時, ため, 又, 仕舞う, 彼, 遣る, 下さる, 然し, 対する, 呉れる`
- hybrid_only_vs_legacy_v5: `定める, 法人, 年金, 生ずる, 世紀, あっ, 慌てる, 個別, 真実, 報酬, セント, 本体`
- hybrid_soft_only_vs_legacy_v5: `定める, 法人, 年金, 生ずる, 世紀, あっ, 慌てる, 個別, 真実, 報酬, セント, 本体`
- hybrid_soft_only_vs_hybrid: ``

### `neutral_n1ish`

- proficiency: `0.580`
- topics: `-`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `御座る`/ござる | 0.493 | - | `我々` | 0.450 | trail | `我々` | 0.450 | trail | `我々` | 0.450 | trail | - |
| 2 | `項`/こう | 0.572 | - | `ライン`/らいん | 0.463 | trail | `ライン`/らいん | 0.463 | trail | `ライン`/らいん | 0.463 | trail | - |
| 3 | `感`/かん | 0.531 | - | `インターネット`/いんたーねっと | 0.456 | trail | `インターネット`/いんたーねっと | 0.456 | trail | `インターネット`/いんたーねっと | 0.456 | trail | - |
| 4 | `我々` | 0.450 | - | `タイム`/たいむ | 0.455 | trail | `タイム`/たいむ | 0.455 | trail | `タイム`/たいむ | 0.455 | trail | - |
| 5 | `論`/ろん | 0.576 | - | `プレー`/ぷれー | 0.466 | trail | `プレー`/ぷれー | 0.466 | trail | `プレー`/ぷれー | 0.466 | trail | - |
| 6 | `通ずる`/つうずる | 0.527 | - | `マイナス`/まいなす | 0.454 | trail | `マイナス`/まいなす | 0.454 | trail | `マイナス`/まいなす | 0.454 | trail | - |
| 7 | `府`/ふ | 0.574 | - | `キス`/きす | 0.456 | trail | `キス`/きす | 0.456 | trail | `キス`/きす | 0.456 | trail | - |
| 8 | `因み`/ちなみ | 0.569 | - | `ド`/ど | 0.580 | frontier | `ド`/ど | 0.580 | frontier | `ド`/ど | 0.580 | frontier | - |
| 9 | `層`/そう | 0.576 | - | `霊的`/れいてき | 0.580 | frontier | `霊的`/れいてき | 0.580 | frontier | `霊的`/れいてき | 0.580 | frontier | - |
| 10 | `インターネット`/いんたーねっと | 0.456 | - | `呈する`/ていする | 0.580 | frontier | `呈する`/ていする | 0.580 | frontier | `呈する`/ていする | 0.580 | frontier | - |
| 11 | `増`/ぞう | 0.577 | - | `ラ`/ら | 0.580 | frontier | `ラ`/ら | 0.580 | frontier | `ラ`/ら | 0.580 | frontier | - |
| 12 | `ライン`/らいん | 0.463 | - | `前出`/ぜんしゅつ | 0.580 | frontier | `前出`/ぜんしゅつ | 0.580 | frontier | `前出`/ぜんしゅつ | 0.580 | frontier | - |

- legacy_v5_only: `御座る, 項, 感, 論, 通ずる, 府, 因み, 層, 増, 故, ザ, バランス`
- frontier_only: `キス, ド, 霊的, 呈する, ラ, 前出, ヤフオク, 甲子, 乗用, 敵う, 原動, 余儀`
- legacy_v5_only_vs_hybrid: `御座る, 項, 感, 論, 通ずる, 府, 因み, 層, 増, 故, ザ, バランス`
- hybrid_only_vs_legacy_v5: `キス, ド, 霊的, 呈する, ラ, 前出, ヤフオク, 甲子, 乗用, 敵う, 原動, 余儀`
- hybrid_soft_only_vs_legacy_v5: `キス, ド, 霊的, 呈する, ラ, 前出, ヤフオク, 甲子, 乗用, 敵う, 原動, 余儀`
- hybrid_soft_only_vs_hybrid: ``

### `neutral_advanced`

- proficiency: `0.820`
- topics: `-`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `クリア`/くりあ | 0.720 | - | `ジャバ`/じゃば | 0.692 | trail | `ジャバ`/じゃば | 0.692 | trail | `ジャバ`/じゃば | 0.692 | trail | - |
| 2 | `ジャバ`/じゃば | 0.692 | - | `エステ`/えすて | 0.703 | trail | `エステ`/えすて | 0.703 | trail | `エステ`/えすて | 0.703 | trail | - |
| 3 | `メソッド`/めそっど | 0.676 | - | `ブロードバンド`/ぶろーどばんど | 0.702 | trail | `ブロードバンド`/ぶろーどばんど | 0.702 | trail | `ブロードバンド`/ぶろーどばんど | 0.702 | trail | - |
| 4 | `インターフェース`/いんたーふぇーす | 0.750 | - | `クリア`/くりあ | 0.720 | trail | `クリア`/くりあ | 0.720 | trail | `クリア`/くりあ | 0.720 | trail | - |
| 5 | `ウォッチ`/うぉっち | 0.714 | - | `レフ`/れふ | 0.710 | trail | `レフ`/れふ | 0.710 | trail | `レフ`/れふ | 0.710 | trail | - |
| 6 | `エステ`/えすて | 0.703 | - | `係属`/けいぞく | 0.696 | trail | `係属`/けいぞく | 0.696 | trail | `係属`/けいぞく | 0.696 | trail | - |
| 7 | `レフ`/れふ | 0.710 | - | `ウォッチ`/うぉっち | 0.714 | trail | `ウォッチ`/うぉっち | 0.714 | trail | `ウォッチ`/うぉっち | 0.714 | trail | - |
| 8 | `ブロードバンド`/ぶろーどばんど | 0.702 | - | `飯蛸`/いいだこ | 0.800 | frontier | `飯蛸`/いいだこ | 0.800 | frontier | `飯蛸`/いいだこ | 0.800 | frontier | - |
| 9 | `ピックアップ`/ぴっくあっぷ | 0.681 | - | `唐臼`/からうす | 0.796 | frontier | `唐臼`/からうす | 0.796 | frontier | `唐臼`/からうす | 0.796 | frontier | - |
| 10 | `シックス`/しっくす | 0.724 | - | `兜蟹`/かぶとがに | 0.791 | frontier | `兜蟹`/かぶとがに | 0.791 | frontier | `兜蟹`/かぶとがに | 0.791 | frontier | - |
| 11 | `インナー`/いんなー | 0.759 | - | `ハザード`/はざーど | 0.790 | frontier | `ハザード`/はざーど | 0.790 | frontier | `ハザード`/はざーど | 0.790 | frontier | - |
| 12 | `ハザード`/はざーど | 0.790 | - | `売り越し`/うりこし | 0.785 | frontier | `売り越し`/うりこし | 0.785 | frontier | `売り越し`/うりこし | 0.785 | frontier | - |

- legacy_v5_only: `メソッド, ピックアップ, シックス, 木目細か, クエスチョン, 欠格, 付表, カスタマイズ, 人作り, 騙し取る, 付図, リテラシー`
- frontier_only: `飯蛸, 唐臼, 兜蟹, 売り越し, 梶木鮪, 山桃, 見栄っ張り, スピリチュアリズム, 黒痣, 所記, 実包, 丁数`
- legacy_v5_only_vs_hybrid: `メソッド, ピックアップ, シックス, 木目細か, クエスチョン, 欠格, 付表, カスタマイズ, 人作り, 騙し取る, 付図, リテラシー`
- hybrid_only_vs_legacy_v5: `飯蛸, 唐臼, 兜蟹, 売り越し, 梶木鮪, 山桃, 見栄っ張り, スピリチュアリズム, 黒痣, 所記, 実包, 丁数`
- hybrid_soft_only_vs_legacy_v5: `飯蛸, 唐臼, 兜蟹, 売り越し, 梶木鮪, 山桃, 見栄っ張り, スピリチュアリズム, 黒痣, 所記, 実包, 丁数`
- hybrid_soft_only_vs_hybrid: ``

### `shopping_money_intermediate`

- proficiency: `0.450`
- topics: `shopping_money`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 26, 'trail': 7, 'topic': 7}`
- hybrid lane fills: `{'core': 0, 'frontier': 27, 'trail': 7, 'topic': 6}`
- hybrid topic depth: `{'eligible_candidate_count': 7, 'eligible_mass': 3.970636, 'candidate_count': 7, 'mass': 3.970636, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 23, 'trail': 7, 'topic': 10}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 24, 'trail': 7, 'topic': 9}`
- hybrid soft topic depth: `{'eligible_candidate_count': 10, 'eligible_mass': 5.402061, 'candidate_count': 27, 'mass': 5.444808, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `債権`/さいけん | 0.305 | shopping_money | `商店`/しょうてん | 0.309 | topic | `商店`/しょうてん | 0.309 | topic | `商店`/しょうてん | 0.309 | topic | shopping_money |
| 2 | `商店`/しょうてん | 0.309 | shopping_money | `債権`/さいけん | 0.305 | topic | `債権`/さいけん | 0.305 | topic | `債権`/さいけん | 0.305 | topic | shopping_money |
| 3 | `コンビニ`/こんびに | 0.280 | shopping_money | `コンビニ`/こんびに | 0.280 | topic | `コンビニ`/こんびに | 0.280 | topic | `コンビニ`/こんびに | 0.280 | topic | shopping_money |
| 4 | `現金`/げんきん | 0.252 | shopping_money | `現金`/げんきん | 0.252 | topic | `現金`/げんきん | 0.252 | topic | `現金`/げんきん | 0.252 | topic | shopping_money |
| 5 | `円`/えん | 0.250 | shopping_money | `其々`/それぞれ | 0.327 | trail | `円`/えん | 0.250 | topic | `円`/えん | 0.250 | topic | shopping_money |
| 6 | `代金`/だいきん | 0.250 | shopping_money | `共`/とも | 0.322 | trail | `代金`/だいきん | 0.250 | topic | `代金`/だいきん | 0.250 | topic | shopping_money |
| 7 | `会計`/かいけい | 0.243 | shopping_money | `限り`/かぎり | 0.334 | trail | `其々`/それぞれ | 0.327 | trail | `会計`/かいけい | 0.243 | topic | shopping_money |
| 8 | `支払う`/しはらう | 0.242 | shopping_money | `奴`/やつ | 0.331 | trail | `共`/とも | 0.322 | trail | `支払う`/しはらう | 0.242 | topic | shopping_money |
| 9 | `料金`/りょうきん | 0.239 | shopping_money | `扠`/さて | 0.336 | trail | `限り`/かぎり | 0.334 | trail | `料金`/りょうきん | 0.239 | topic | shopping_money |
| 10 | `無料`/むりょう | 0.204 | shopping_money | `急度`/きっと | 0.337 | trail | `奴`/やつ | 0.331 | trail | `其々`/それぞれ | 0.327 | trail | - |
| 11 | `価格`/かかく | 0.183 | shopping_money | `イン`/いん | 0.336 | trail | `扠`/さて | 0.336 | trail | `共`/とも | 0.322 | trail | - |
| 12 | `商品`/しょうひん | 0.179 | shopping_money | `我々` | 0.450 | frontier | `急度`/きっと | 0.337 | trail | `限り`/かぎり | 0.334 | trail | - |

- legacy_v5_only: `円, 代金, 会計, 支払う, 料金, 無料, 価格, 商品, スーパー, レジ, 予約, 値段`
- frontier_only: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- legacy_v5_only_vs_hybrid: `会計, 支払う, 料金, 無料, 価格, 商品, スーパー, レジ, 予約, 値段, 払う, 良く`
- hybrid_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_hybrid: `会計, 支払う, 料金`

### `work_office_intermediate`

- proficiency: `0.450`
- topics: `work_office`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 20, 'trail': 7, 'topic': 13}`
- hybrid lane fills: `{'core': 0, 'frontier': 20, 'trail': 7, 'topic': 13}`
- hybrid topic depth: `{'eligible_candidate_count': 13, 'eligible_mass': 9.693524, 'candidate_count': 13, 'mass': 9.693524, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 18, 'trail': 7, 'topic': 15}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 18, 'trail': 7, 'topic': 15}`
- hybrid soft topic depth: `{'eligible_candidate_count': 17, 'eligible_mass': 11.204691, 'candidate_count': 29, 'mass': 11.252003, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `勤務`/きんむ | 0.288 | work_office | `商標`/しょうひょう | 0.406 | topic | `商標`/しょうひょう | 0.406 | topic | `商標`/しょうひょう | 0.406 | topic | work_office |
| 2 | `上司`/じょうし | 0.306 | work_office | `残業`/ざんぎょう | 0.366 | topic | `残業`/ざんぎょう | 0.366 | topic | `残業`/ざんぎょう | 0.366 | topic | work_office |
| 3 | `職場`/しょくば | 0.286 | work_office | `出勤`/しゅっきん | 0.363 | topic | `出勤`/しゅっきん | 0.363 | topic | `出勤`/しゅっきん | 0.363 | topic | work_office |
| 4 | `役員`/やくいん | 0.329 | work_office | `出張`/しゅっちょう | 0.335 | topic | `出張`/しゅっちょう | 0.335 | topic | `出張`/しゅっちょう | 0.335 | topic | work_office |
| 5 | `部下`/ぶか | 0.317 | work_office | `其々`/それぞれ | 0.327 | trail | `役員`/やくいん | 0.329 | topic | `役員`/やくいん | 0.329 | topic | work_office |
| 6 | `面接`/めんせつ | 0.318 | work_office | `共`/とも | 0.322 | trail | `面接`/めんせつ | 0.318 | topic | `面接`/めんせつ | 0.318 | topic | work_office |
| 7 | `出張`/しゅっちょう | 0.335 | work_office | `限り`/かぎり | 0.334 | trail | `部下`/ぶか | 0.317 | topic | `部下`/ぶか | 0.317 | topic | work_office |
| 8 | `出勤`/しゅっきん | 0.363 | work_office | `奴`/やつ | 0.331 | trail | `上司`/じょうし | 0.306 | topic | `上司`/じょうし | 0.306 | topic | work_office |
| 9 | `残業`/ざんぎょう | 0.366 | work_office | `扠`/さて | 0.336 | trail | `勤務`/きんむ | 0.288 | topic | `勤務`/きんむ | 0.288 | topic | work_office |
| 10 | `商標`/しょうひょう | 0.406 | work_office | `急度`/きっと | 0.337 | trail | `職場`/しょくば | 0.286 | topic | `職場`/しょくば | 0.286 | topic | work_office |
| 11 | `給料`/きゅうりょう | 0.256 | work_office | `イン`/いん | 0.336 | trail | `雇う`/やとう | 0.258 | topic | `雇う`/やとう | 0.258 | topic | work_office |
| 12 | `雇う`/やとう | 0.258 | work_office | `我々` | 0.450 | frontier | `給料`/きゅうりょう | 0.256 | topic | `給料`/きゅうりょう | 0.256 | topic | work_office |

- legacy_v5_only: `勤務, 上司, 職場, 役員, 部下, 面接, 給料, 雇う, 書類, 同僚, 職業, 社員`
- frontier_only: `扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい`
- legacy_v5_only_vs_hybrid: `同僚, 職業, 社員, 職員, 資料, 契約, 事務, 良く, 矢張り, センター, 此方, サービス`
- hybrid_only_vs_legacy_v5: `扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい`
- hybrid_soft_only_vs_legacy_v5: `扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい`
- hybrid_soft_only_vs_hybrid: `同僚, 職業`

### `science_math_intermediate`

- proficiency: `0.450`
- topics: `science_math`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane fills: `{'core': 0, 'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid topic depth: `{'eligible_candidate_count': 4, 'eligible_mass': 2.591712, 'candidate_count': 4, 'mass': 2.591712, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 24, 'trail': 7, 'topic': 9}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 24, 'trail': 7, 'topic': 9}`
- hybrid soft topic depth: `{'eligible_candidate_count': 9, 'eligible_mass': 3.844889, 'candidate_count': 15, 'mass': 3.864591, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `理論`/りろん | 0.279 | science_math | `三角`/さんかく | 0.303 | topic | `三角`/さんかく | 0.303 | topic | `三角`/さんかく | 0.303 | topic | science_math |
| 2 | `三角`/さんかく | 0.303 | science_math | `公式`/こうしき | 0.284 | topic | `公式`/こうしき | 0.284 | topic | `公式`/こうしき | 0.284 | topic | science_math |
| 3 | `公式`/こうしき | 0.284 | science_math | `理論`/りろん | 0.279 | topic | `理論`/りろん | 0.279 | topic | `理論`/りろん | 0.279 | topic | science_math |
| 4 | `物理`/ぶつり | 0.254 | science_math | `物理`/ぶつり | 0.254 | topic | `物理`/ぶつり | 0.254 | topic | `物理`/ぶつり | 0.254 | topic | science_math |
| 5 | `化学`/かがく | 0.243 | science_math | `其々`/それぞれ | 0.327 | trail | `其々`/それぞれ | 0.327 | trail | `化学`/かがく | 0.243 | topic | science_math |
| 6 | `温度`/おんど | 0.235 | science_math | `共`/とも | 0.322 | trail | `共`/とも | 0.322 | trail | `温度`/おんど | 0.235 | topic | science_math |
| 7 | `実験`/じっけん | 0.218 | science_math | `限り`/かぎり | 0.334 | trail | `限り`/かぎり | 0.334 | trail | `実験`/じっけん | 0.218 | topic | science_math |
| 8 | `機械`/きかい | 0.216 | science_math | `奴`/やつ | 0.331 | trail | `奴`/やつ | 0.331 | trail | `機械`/きかい | 0.216 | topic | science_math |
| 9 | `数字`/すうじ | 0.215 | science_math | `扠`/さて | 0.336 | trail | `扠`/さて | 0.336 | trail | `数字`/すうじ | 0.215 | topic | science_math |
| 10 | `計算`/けいさん | 0.198 | science_math | `急度`/きっと | 0.337 | trail | `急度`/きっと | 0.337 | trail | `其々`/それぞれ | 0.327 | trail | - |
| 11 | `地理`/ちり | 0.157 | science_math | `イン`/いん | 0.336 | trail | `イン`/いん | 0.336 | trail | `共`/とも | 0.322 | trail | - |
| 12 | `数学`/すうがく | 0.155 | science_math | `我々` | 0.450 | frontier | `我々` | 0.450 | frontier | `限り`/かぎり | 0.334 | trail | - |

- legacy_v5_only: `化学, 温度, 実験, 機械, 数字, 計算, 地理, 数学, 科学, 良く, 矢張り, センター`
- frontier_only: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- legacy_v5_only_vs_hybrid: `化学, 温度, 実験, 機械, 数字, 計算, 地理, 数学, 科学, 良く, 矢張り, センター`
- hybrid_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_hybrid: `化学, 温度, 実験, 機械, 数字`

### `computing_internet_intermediate`

- proficiency: `0.450`
- topics: `computing_internet`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid topic depth: `{'eligible_candidate_count': 51, 'eligible_mass': 39.739151, 'candidate_count': 52, 'mass': 39.776667, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft topic depth: `{'eligible_candidate_count': 64, 'eligible_mass': 42.74829, 'candidate_count': 102, 'mass': 43.189814, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `サイト`/さいと | 0.395 | computing_internet | `変数`/へんすう | 0.449 | topic | `変数`/へんすう | 0.449 | topic | `変数`/へんすう | 0.449 | topic | computing_internet |
| 2 | `コメント`/こめんと | 0.419 | computing_internet | `インターネット`/いんたーねっと | 0.456 | topic | `インターネット`/いんたーねっと | 0.456 | topic | `インターネット`/いんたーねっと | 0.456 | topic | computing_internet |
| 3 | `形式`/けいしき | 0.284 | computing_internet | `パッケージ`/ぱっけーじ | 0.477 | topic | `パッケージ`/ぱっけーじ | 0.477 | topic | `パッケージ`/ぱっけーじ | 0.477 | topic | computing_internet |
| 4 | `権限`/けんげん | 0.321 | computing_internet | `コメント`/こめんと | 0.419 | topic | `コメント`/こめんと | 0.419 | topic | `コメント`/こめんと | 0.419 | topic | computing_internet |
| 5 | `無線`/むせん | 0.316 | computing_internet | `其々`/それぞれ | 0.327 | trail | `ソース`/そーす | 0.487 | topic | `ソース`/そーす | 0.487 | topic | computing_internet |
| 6 | `通知`/つうち | 0.285 | computing_internet | `共`/とも | 0.322 | trail | `サーバー`/さーばー | 0.498 | topic | `サーバー`/さーばー | 0.498 | topic | computing_internet |
| 7 | `削除`/さくじょ | 0.281 | computing_internet | `限り`/かぎり | 0.334 | trail | `有線`/ゆうせん | 0.404 | topic | `有線`/ゆうせん | 0.404 | topic | computing_internet |
| 8 | `インターネット`/いんたーねっと | 0.456 | computing_internet | `奴`/やつ | 0.331 | trail | `チャット`/ちゃっと | 0.504 | topic | `チャット`/ちゃっと | 0.504 | topic | computing_internet |
| 9 | `例外`/れいがい | 0.329 | computing_internet | `扠`/さて | 0.336 | trail | `サイト`/さいと | 0.395 | topic | `サイト`/さいと | 0.395 | topic | computing_internet |
| 10 | `受信`/じゅしん | 0.330 | computing_internet | `急度`/きっと | 0.337 | trail | `バッテリー`/ばってりー | 0.510 | topic | `バッテリー`/ばってりー | 0.510 | topic | computing_internet |
| 11 | `数値`/すうち | 0.286 | computing_internet | `イン`/いん | 0.336 | trail | `クッキー`/くっきー | 0.513 | topic | `クッキー`/くっきー | 0.513 | topic | computing_internet |
| 12 | `回線`/かいせん | 0.335 | computing_internet | `我々` | 0.450 | frontier | `分岐`/ぶんき | 0.376 | topic | `分岐`/ぶんき | 0.376 | topic | computing_internet |

- legacy_v5_only: `サイト, 形式, 権限, 無線, 通知, 削除, 例外, 受信, 数値, 回線, 容量, 出力`
- frontier_only: `変数, パッケージ, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 耕作`
- legacy_v5_only_vs_hybrid: `形式, 権限, 無線, 通知, 削除, 例外, 受信, 数値, 回線, 容量, 出力, 送信`
- hybrid_only_vs_legacy_v5: `変数, パッケージ, ソース, サーバー, 有線, チャット, バッテリー, クッキー, 分岐, 拡散, 復元, 圧縮`
- hybrid_soft_only_vs_legacy_v5: `変数, パッケージ, ソース, サーバー, 有線, チャット, バッテリー, クッキー, 分岐, 拡散, 復元, 圧縮`
- hybrid_soft_only_vs_hybrid: ``

### `medicine_health_intermediate`

- proficiency: `0.450`
- topics: `medicine_health`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane fills: `{'core': 0, 'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid topic depth: `{'eligible_candidate_count': 4, 'eligible_mass': 2.527189, 'candidate_count': 4, 'mass': 2.527189, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 23, 'trail': 7, 'topic': 10}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 23, 'trail': 7, 'topic': 10}`
- hybrid soft topic depth: `{'eligible_candidate_count': 10, 'eligible_mass': 4.032929, 'candidate_count': 27, 'mass': 4.070433, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `皮膚`/ひふ | 0.293 | medicine_health | `爪`/つめ | 0.299 | topic | `爪`/つめ | 0.299 | topic | `爪`/つめ | 0.299 | topic | medicine_health |
| 2 | `爪`/つめ | 0.299 | medicine_health | `皮膚`/ひふ | 0.293 | topic | `皮膚`/ひふ | 0.293 | topic | `皮膚`/ひふ | 0.293 | topic | medicine_health |
| 3 | `胃`/い | 0.257 | medicine_health | `胃`/い | 0.257 | topic | `胃`/い | 0.257 | topic | `胃`/い | 0.257 | topic | medicine_health |
| 4 | `心臓`/しんぞう | 0.252 | medicine_health | `心臓`/しんぞう | 0.252 | topic | `心臓`/しんぞう | 0.252 | topic | `心臓`/しんぞう | 0.252 | topic | medicine_health |
| 5 | `怪我`/けが | 0.244 | medicine_health | `其々`/それぞれ | 0.327 | trail | `其々`/それぞれ | 0.327 | trail | `怪我`/けが | 0.244 | topic | medicine_health |
| 6 | `膝`/ひざ | 0.237 | medicine_health | `共`/とも | 0.322 | trail | `共`/とも | 0.322 | trail | `膝`/ひざ | 0.237 | topic | medicine_health |
| 7 | `腹`/はら | 0.229 | medicine_health | `限り`/かぎり | 0.334 | trail | `限り`/かぎり | 0.334 | trail | `腹`/はら | 0.229 | topic | medicine_health |
| 8 | `肩`/かた | 0.213 | medicine_health | `奴`/やつ | 0.331 | trail | `奴`/やつ | 0.331 | trail | `肩`/かた | 0.213 | topic | medicine_health |
| 9 | `脳`/のう | 0.213 | medicine_health | `扠`/さて | 0.336 | trail | `扠`/さて | 0.336 | trail | `脳`/のう | 0.213 | topic | medicine_health |
| 10 | `腰`/こし | 0.212 | medicine_health | `急度`/きっと | 0.337 | trail | `急度`/きっと | 0.337 | trail | `腰`/こし | 0.212 | topic | medicine_health |
| 11 | `胸`/むね | 0.204 | medicine_health | `イン`/いん | 0.336 | trail | `イン`/いん | 0.336 | trail | `其々`/それぞれ | 0.327 | trail | - |
| 12 | `顔`/かお | 0.169 | medicine_health | `我々` | 0.450 | frontier | `我々` | 0.450 | frontier | `共`/とも | 0.322 | trail | - |

- legacy_v5_only: `怪我, 膝, 腹, 肩, 脳, 腰, 胸, 顔, 血, 指, 背中, 熱`
- frontier_only: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- legacy_v5_only_vs_hybrid: `怪我, 膝, 腹, 肩, 脳, 腰, 胸, 顔, 血, 指, 背中, 熱`
- hybrid_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_legacy_v5: `急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい, 官民`
- hybrid_soft_only_vs_hybrid: `怪我, 膝, 腹, 肩, 脳, 腰`

### `sports_beginner`

- proficiency: `0.250`
- topics: `sports_fitness`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 19, 'trail': 7, 'topic': 14}`
- hybrid lane fills: `{'core': 0, 'frontier': 19, 'trail': 7, 'topic': 14}`
- hybrid topic depth: `{'eligible_candidate_count': 14, 'eligible_mass': 12.846293, 'candidate_count': 14, 'mass': 12.846293, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 19, 'trail': 7, 'topic': 14}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 19, 'trail': 7, 'topic': 14}`
- hybrid soft topic depth: `{'eligible_candidate_count': 14, 'eligible_mass': 12.846293, 'candidate_count': 14, 'mass': 12.846293, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `野球`/やきゅう | 0.241 | sports_fitness | `野球`/やきゅう | 0.241 | topic | `野球`/やきゅう | 0.241 | topic | `野球`/やきゅう | 0.241 | topic | sports_fitness |
| 2 | `ゴルフ`/ごるふ | 0.172 | sports_fitness | `スケート`/すけーと | 0.260 | topic | `スケート`/すけーと | 0.260 | topic | `スケート`/すけーと | 0.260 | topic | sports_fitness |
| 3 | `サッカー`/さっかー | 0.189 | sports_fitness | `センター`/せんたー | 0.299 | topic | `センター`/せんたー | 0.299 | topic | `センター`/せんたー | 0.299 | topic | sports_fitness |
| 4 | `ダンス`/だんす | 0.120 | sports_fitness | `サッカー`/さっかー | 0.189 | topic | `サッカー`/さっかー | 0.189 | topic | `サッカー`/さっかー | 0.189 | topic | sports_fitness |
| 5 | `スキー`/すきー | 0.172 | sports_fitness | `彼` | 0.180 | trail | `マラソン`/まらそん | 0.306 | topic | `マラソン`/まらそん | 0.306 | topic | sports_fitness |
| 6 | `テニス`/てにす | 0.120 | sports_fitness | `因る`/よる | 0.165 | trail | `スキー`/すきー | 0.172 | topic | `スキー`/すきー | 0.172 | topic | sports_fitness |
| 7 | `水泳`/すいえい | 0.155 | sports_fitness | `時`/とき | 0.165 | trail | `ゴルフ`/ごるふ | 0.172 | topic | `ゴルフ`/ごるふ | 0.172 | topic | sports_fitness |
| 8 | `柔道`/じゅうどう | 0.137 | sports_fitness | `又`/また | 0.165 | trail | `水泳`/すいえい | 0.155 | topic | `水泳`/すいえい | 0.155 | topic | sports_fitness |
| 9 | `スケート`/すけーと | 0.260 | sports_fitness | `仕舞う`/しまう | 0.165 | trail | `体操`/たいそう | 0.339 | topic | `体操`/たいそう | 0.339 | topic | sports_fitness |
| 10 | `センター`/せんたー | 0.299 | sports_fitness | `然し`/しかし | 0.168 | trail | `相撲`/すもう | 0.350 | topic | `相撲`/すもう | 0.350 | topic | sports_fitness |
| 11 | `マラソン`/まらそん | 0.306 | sports_fitness | `会`/かい | 0.169 | trail | `陸上`/りくじょう | 0.352 | topic | `陸上`/りくじょう | 0.352 | topic | sports_fitness |
| 12 | `体操`/たいそう | 0.339 | sports_fitness | `犯人`/はんにん | 0.250 | frontier | `柔道`/じゅうどう | 0.137 | topic | `柔道`/じゅうどう | 0.137 | topic | sports_fitness |

- legacy_v5_only: `ゴルフ, ダンス, スキー, テニス, 水泳, 柔道, マラソン, 体操, 相撲, 陸上, ある, こと`
- frontier_only: `犯人, 浴びる, 論文, 月曜, 豆, 恐れる, 代金, 微妙, 保証, 強盗, 円, 好み`
- legacy_v5_only_vs_hybrid: `ある, こと, よう, 思う, 見る, 出来る, ため, そう, 考える, 場合, 遣る, 行う`
- hybrid_only_vs_legacy_v5: `犯人, 浴びる, 論文, 月曜, 豆, 恐れる, 代金, 微妙, 保証, 強盗, 円, 好み`
- hybrid_soft_only_vs_legacy_v5: `犯人, 浴びる, 論文, 月曜, 豆, 恐れる, 代金, 微妙, 保証, 強盗, 円, 好み`
- hybrid_soft_only_vs_hybrid: ``

### `games_intermediate`

- proficiency: `0.450`
- topics: `games`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid lane fills: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid topic depth: `{'eligible_candidate_count': 25, 'eligible_mass': 20.527317, 'candidate_count': 25, 'mass': 20.527317, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid soft topic depth: `{'eligible_candidate_count': 28, 'eligible_mass': 21.206973, 'candidate_count': 34, 'mass': 21.27462, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `レベル`/れべる | 0.413 | games | `打開`/だかい | 0.440 | topic | `打開`/だかい | 0.440 | topic | `打開`/だかい | 0.440 | topic | games |
| 2 | `勝負`/しょうぶ | 0.289 | games | `一手`/いって | 0.435 | topic | `一手`/いって | 0.435 | topic | `一手`/いって | 0.435 | topic | games |
| 3 | `作戦`/さくせん | 0.285 | games | `攻勢`/こうせい | 0.434 | topic | `攻勢`/こうせい | 0.434 | topic | `攻勢`/こうせい | 0.434 | topic | games |
| 4 | `得点`/とくてん | 0.343 | games | `勝敗`/しょうはい | 0.430 | topic | `勝敗`/しょうはい | 0.430 | topic | `勝敗`/しょうはい | 0.430 | topic | games |
| 5 | `逆転`/ぎゃくてん | 0.344 | games | `其々`/それぞれ | 0.327 | trail | `レベル`/れべる | 0.413 | topic | `レベル`/れべる | 0.413 | topic | games |
| 6 | `防御`/ぼうぎょ | 0.319 | games | `共`/とも | 0.322 | trail | `優勢`/ゆうせい | 0.411 | topic | `優勢`/ゆうせい | 0.411 | topic | games |
| 7 | `局面`/きょくめん | 0.369 | games | `限り`/かぎり | 0.334 | trail | `終盤`/しゅうばん | 0.398 | topic | `終盤`/しゅうばん | 0.398 | topic | games |
| 8 | `ターン`/たーん | 0.297 | games | `奴`/やつ | 0.331 | trail | `将棋`/しょうぎ | 0.382 | topic | `将棋`/しょうぎ | 0.382 | topic | games |
| 9 | `ボス`/ぼす | 0.297 | games | `扠`/さて | 0.336 | trail | `戦術`/せんじゅつ | 0.373 | topic | `戦術`/せんじゅつ | 0.373 | topic | games |
| 10 | `対戦`/たいせん | 0.328 | games | `急度`/きっと | 0.337 | trail | `局面`/きょくめん | 0.369 | topic | `局面`/きょくめん | 0.369 | topic | games |
| 11 | `点数`/てんすう | 0.362 | games | `イン`/いん | 0.336 | trail | `点数`/てんすう | 0.362 | topic | `点数`/てんすう | 0.362 | topic | games |
| 12 | `戦術`/せんじゅつ | 0.373 | games | `我々` | 0.450 | frontier | `逆転`/ぎゃくてん | 0.344 | topic | `逆転`/ぎゃくてん | 0.344 | topic | games |

- legacy_v5_only: `レベル, 勝負, 作戦, 得点, 逆転, 防御, 局面, ターン, ボス, 対戦, 点数, 戦術`
- frontier_only: `扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作, 目覚ましい`
- legacy_v5_only_vs_hybrid: `勝負, 作戦, 防御, ターン, ボス, キャラクター, 良く, 矢張り, センター, 此方, サービス, 旨い`
- hybrid_only_vs_legacy_v5: `キャラ, 詰め, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数`
- hybrid_soft_only_vs_legacy_v5: `キャラ, 詰め, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数`
- hybrid_soft_only_vs_hybrid: ``

### `hobbies_crafts_intermediate`

- proficiency: `0.450`
- topics: `hobbies_crafts`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid lane fills: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid topic depth: `{'eligible_candidate_count': 24, 'eligible_mass': 20.426329, 'candidate_count': 24, 'mass': 20.426329, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 17, 'trail': 7, 'topic': 16}`
- hybrid soft topic depth: `{'eligible_candidate_count': 25, 'eligible_mass': 20.93686, 'candidate_count': 47, 'mass': 21.055771, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `収集`/しゅうしゅう | 0.301 | hobbies_crafts | `野鳥`/やちょう | 0.446 | topic | `野鳥`/やちょう | 0.446 | topic | `野鳥`/やちょう | 0.446 | topic | hobbies_crafts |
| 2 | `栽培`/さいばい | 0.309 | hobbies_crafts | `星空`/ほしぞら | 0.439 | topic | `星空`/ほしぞら | 0.439 | topic | `星空`/ほしぞら | 0.439 | topic | hobbies_crafts |
| 3 | `工作`/こうさく | 0.338 | hobbies_crafts | `短歌`/たんか | 0.428 | topic | `短歌`/たんか | 0.428 | topic | `短歌`/たんか | 0.428 | topic | hobbies_crafts |
| 4 | `録音`/ろくおん | 0.333 | hobbies_crafts | `陶芸`/とうげい | 0.428 | topic | `陶芸`/とうげい | 0.428 | topic | `陶芸`/とうげい | 0.428 | topic | hobbies_crafts |
| 5 | `楽器`/がっき | 0.328 | hobbies_crafts | `其々`/それぞれ | 0.327 | trail | `書道`/しょどう | 0.419 | topic | `書道`/しょどう | 0.419 | topic | hobbies_crafts |
| 6 | `手作り`/てづくり | 0.341 | hobbies_crafts | `共`/とも | 0.322 | trail | `金魚`/きんぎょ | 0.403 | topic | `金魚`/きんぎょ | 0.403 | topic | hobbies_crafts |
| 7 | `彫刻`/ちょうこく | 0.360 | hobbies_crafts | `限り`/かぎり | 0.334 | trail | `盆栽`/ぼんさい | 0.392 | topic | `盆栽`/ぼんさい | 0.392 | topic | hobbies_crafts |
| 8 | `演劇`/えんげき | 0.371 | hobbies_crafts | `奴`/やつ | 0.331 | trail | `天文`/てんもん | 0.383 | topic | `天文`/てんもん | 0.383 | topic | hobbies_crafts |
| 9 | `天文`/てんもん | 0.383 | hobbies_crafts | `扠`/さて | 0.336 | trail | `模型`/もけい | 0.382 | topic | `模型`/もけい | 0.382 | topic | hobbies_crafts |
| 10 | `縫う`/ぬう | 0.334 | hobbies_crafts | `急度`/きっと | 0.337 | trail | `刺繍`/ししゅう | 0.380 | topic | `刺繍`/ししゅう | 0.380 | topic | hobbies_crafts |
| 11 | `水槽`/すいそう | 0.345 | hobbies_crafts | `イン`/いん | 0.336 | trail | `演劇`/えんげき | 0.371 | topic | `演劇`/えんげき | 0.371 | topic | hobbies_crafts |
| 12 | `マジック`/まじっく | 0.306 | hobbies_crafts | `我々` | 0.450 | frontier | `彫刻`/ちょうこく | 0.360 | topic | `彫刻`/ちょうこく | 0.360 | topic | hobbies_crafts |

- legacy_v5_only: `収集, 栽培, 工作, 録音, 楽器, 手作り, 彫刻, 演劇, 天文, 縫う, 水槽, マジック`
- frontier_only: `星空, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作`
- legacy_v5_only_vs_hybrid: `収集, 栽培, 録音, 楽器, マジック, 良く, 矢張り, センター, 此方, サービス, 旨い, 然も`
- hybrid_only_vs_legacy_v5: `星空, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作`
- hybrid_soft_only_vs_legacy_v5: `星空, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数, 耕作`
- hybrid_soft_only_vs_hybrid: ``

### `arts_literature_advanced`

- proficiency: `0.720`
- topics: `arts_literature_humanities`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 41, 'mass': 1e-05, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `短歌`/たんか | 0.428 | arts_literature_humanities | `短歌`/たんか | 0.428 | topic | `インストール`/いんすとーる | 0.596 | trail | `インストール`/いんすとーる | 0.596 | trail | - |
| 2 | `項`/こう | 0.572 | - | `脚本`/きゃくほん | 0.388 | topic | `前掲`/ぜんけい | 0.596 | trail | `前掲`/ぜんけい | 0.596 | trail | - |
| 3 | `論`/ろん | 0.576 | - | `歌舞伎`/かぶき | 0.387 | topic | `サン`/さん | 0.594 | trail | `サン`/さん | 0.594 | trail | - |
| 4 | `府`/ふ | 0.574 | - | `評論`/ひょうろん | 0.384 | topic | `論`/ろん | 0.576 | trail | `論`/ろん | 0.576 | trail | - |
| 5 | `因み`/ちなみ | 0.569 | - | `インストール`/いんすとーる | 0.596 | trail | `エクセル`/えくせる | 0.604 | trail | `エクセル`/えくせる | 0.604 | trail | - |
| 6 | `層`/そう | 0.576 | - | `前掲`/ぜんけい | 0.596 | trail | `項`/こう | 0.572 | trail | `項`/こう | 0.572 | trail | - |
| 7 | `増`/ぞう | 0.577 | - | `サン`/さん | 0.594 | trail | `ザ`/ざ | 0.578 | trail | `ザ`/ざ | 0.578 | trail | - |
| 8 | `故`/ゆえ | 0.577 | - | `論`/ろん | 0.576 | trail | `訪朝`/ほうちょう | 0.720 | frontier | `訪朝`/ほうちょう | 0.720 | frontier | - |
| 9 | `ザ`/ざ | 0.578 | - | `エクセル`/えくせる | 0.604 | trail | `クリア`/くりあ | 0.720 | frontier | `クリア`/くりあ | 0.720 | frontier | - |
| 10 | `有り`/あり | 0.577 | - | `項`/こう | 0.572 | trail | `持ち合う`/もちあう | 0.720 | frontier | `持ち合う`/もちあう | 0.720 | frontier | - |
| 11 | `御陰`/おかげ | 0.577 | - | `ザ`/ざ | 0.578 | trail | `ノーマリゼーション`/のーまりぜーしょん | 0.720 | frontier | `ノーマリゼーション`/のーまりぜーしょん | 0.720 | frontier | - |
| 12 | `動産`/どうさん | 0.577 | - | `訪朝`/ほうちょう | 0.720 | frontier | `在院`/ざいいん | 0.721 | frontier | `在院`/ざいいん | 0.721 | frontier | - |

- legacy_v5_only: `府, 因み, 層, 増, 故, 有り, 御陰, 動産, 引き続く, 主な, オブ, 炉`
- frontier_only: `脚本, 歌舞伎, 評論, 前掲, エクセル, 訪朝, クリア, 持ち合う, ノーマリゼーション, 在院, 院外, シックス`
- legacy_v5_only_vs_hybrid: `短歌, 府, 因み, 層, 増, 故, 有り, 御陰, 動産, 引き続く, 主な, オブ`
- hybrid_only_vs_legacy_v5: `前掲, エクセル, 訪朝, クリア, 持ち合う, ノーマリゼーション, 在院, 院外, シックス, ポストモダン, 温風, ウォッチ`
- hybrid_soft_only_vs_legacy_v5: `前掲, エクセル, 訪朝, クリア, 持ち合う, ノーマリゼーション, 在院, 院外, シックス, ポストモダン, 温風, ウォッチ`
- hybrid_soft_only_vs_hybrid: ``

### `mixed_work_computing`

- proficiency: `0.500`
- topics: `computing_internet, work_office`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid topic depth: `{'eligible_candidate_count': 47, 'eligible_mass': 33.750538, 'candidate_count': 48, 'mass': 33.818831, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft topic depth: `{'eligible_candidate_count': 60, 'eligible_mass': 38.528971, 'candidate_count': 131, 'mass': 38.842625, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `サイト`/さいと | 0.395 | computing_internet | `サーバー`/さーばー | 0.498 | topic | `サーバー`/さーばー | 0.498 | topic | `サーバー`/さーばー | 0.498 | topic | computing_internet |
| 2 | `インターネット`/いんたーねっと | 0.456 | computing_internet | `チャット`/ちゃっと | 0.504 | topic | `チャット`/ちゃっと | 0.504 | topic | `チャット`/ちゃっと | 0.504 | topic | computing_internet |
| 3 | `コメント`/こめんと | 0.419 | computing_internet | `バッテリー`/ばってりー | 0.510 | topic | `バッテリー`/ばってりー | 0.510 | topic | `バッテリー`/ばってりー | 0.510 | topic | computing_internet |
| 4 | `ソース`/そーす | 0.487 | computing_internet | `クッキー`/くっきー | 0.513 | topic | `クッキー`/くっきー | 0.513 | topic | `クッキー`/くっきー | 0.513 | topic | computing_internet |
| 5 | `サーバー`/さーばー | 0.498 | computing_internet | `成す`/なす | 0.382 | trail | `ソース`/そーす | 0.487 | topic | `ソース`/そーす | 0.487 | topic | computing_internet |
| 6 | `閲覧`/えつらん | 0.359 | computing_internet | `当該`/とうがい | 0.398 | trail | `パッケージ`/ぱっけーじ | 0.477 | topic | `パッケージ`/ぱっけーじ | 0.477 | topic | computing_internet |
| 7 | `同期`/どうき | 0.345 | computing_internet | `有り難う`/ありがとう | 0.394 | trail | `インターネット`/いんたーねっと | 0.456 | topic | `インターネット`/いんたーねっと | 0.456 | topic | computing_internet |
| 8 | `履歴`/りれき | 0.352 | computing_internet | `仰る`/おっしゃる | 0.377 | trail | `変数`/へんすう | 0.449 | topic | `変数`/へんすう | 0.449 | topic | computing_internet |
| 9 | `圧縮`/あっしゅく | 0.354 | computing_internet | `サイト`/さいと | 0.395 | trail | `コメント`/こめんと | 0.419 | topic | `コメント`/こめんと | 0.419 | topic | computing_internet |
| 10 | `出張`/しゅっちょう | 0.335 | work_office | `自転`/じてん | 0.377 | trail | `インストール`/いんすとーる | 0.596 | topic | `インストール`/いんすとーる | 0.596 | topic | computing_internet |
| 11 | `回線`/かいせん | 0.335 | computing_internet | `オン`/おん | 0.380 | trail | `商標`/しょうひょう | 0.406 | topic | `商標`/しょうひょう | 0.406 | topic | work_office |
| 12 | `出勤`/しゅっきん | 0.363 | work_office | `ロック`/ろっく | 0.500 | frontier | `有線`/ゆうせん | 0.404 | topic | `有線`/ゆうせん | 0.404 | topic | computing_internet |

- legacy_v5_only: `インターネット, コメント, ソース, 閲覧, 同期, 履歴, 圧縮, 出張, 回線, 出勤, 変数, 役員`
- frontier_only: `チャット, バッテリー, クッキー, 自転, オン, ロック, 昨秋, 仮名遣い, アトム, 培う, 社団, 知見`
- legacy_v5_only_vs_hybrid: `閲覧, 同期, 履歴, 圧縮, 出張, 回線, 出勤, 役員, 復元, 受信, 例外, 認証`
- hybrid_only_vs_legacy_v5: `チャット, バッテリー, クッキー, インストール, 商標, 有線, ブラウザ, 分岐, 拡散, 自転, オン, ロック`
- hybrid_soft_only_vs_legacy_v5: `チャット, バッテリー, クッキー, インストール, 商標, 有線, ブラウザ, 分岐, 拡散, 自転, オン, ロック`
- hybrid_soft_only_vs_hybrid: ``

### `mixed_food_travel`

- proficiency: `0.350`
- topics: `food_cooking, travel_places_transport`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid topic depth: `{'eligible_candidate_count': 37, 'eligible_mass': 29.515697, 'candidate_count': 38, 'mass': 29.530639, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft topic depth: `{'eligible_candidate_count': 53, 'eligible_mass': 35.128054, 'candidate_count': 88, 'mass': 35.396707, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `道路`/どうろ | 0.200 | travel_places_transport | `喫茶`/きっさ | 0.357 | topic | `喫茶`/きっさ | 0.357 | topic | `喫茶`/きっさ | 0.357 | topic | food_cooking |
| 2 | `酒`/さけ | 0.199 | food_cooking | `包丁`/ほうちょう | 0.338 | topic | `包丁`/ほうちょう | 0.338 | topic | `包丁`/ほうちょう | 0.338 | topic | food_cooking |
| 3 | `観光`/かんこう | 0.207 | travel_places_transport | `箸`/はし | 0.337 | topic | `箸`/はし | 0.337 | topic | `箸`/はし | 0.337 | topic | food_cooking |
| 4 | `茶`/ちゃ | 0.208 | food_cooking | `煮る`/にる | 0.333 | topic | `煮る`/にる | 0.333 | topic | `煮る`/にる | 0.333 | topic | food_cooking |
| 5 | `鍋`/なべ | 0.251 | food_cooking | `無い`/ない | 0.265 | trail | `餅`/もち | 0.327 | topic | `餅`/もち | 0.327 | topic | food_cooking |
| 6 | `列車`/れっしゃ | 0.256 | travel_places_transport | `税`/ぜい | 0.242 | trail | `人参`/にんじん | 0.322 | topic | `人参`/にんじん | 0.322 | topic | food_cooking |
| 7 | `ビール`/びーる | 0.186 | food_cooking | `説`/せつ | 0.253 | trail | `饂飩`/うどん | 0.322 | topic | `饂飩`/うどん | 0.322 | topic | food_cooking |
| 8 | `スープ`/すーぷ | 0.206 | food_cooking | `保証`/ほしょう | 0.250 | trail | `玉葱`/たまねぎ | 0.313 | topic | `玉葱`/たまねぎ | 0.313 | topic | food_cooking |
| 9 | `バイク`/ばいく | 0.207 | travel_places_transport | `憲法`/けんぽう | 0.249 | trail | `パスタ`/ぱすた | 0.306 | topic | `パスタ`/ぱすた | 0.306 | topic | food_cooking |
| 10 | `信号`/しんごう | 0.246 | travel_places_transport | `心理`/しんり | 0.251 | trail | `豆腐`/とうふ | 0.306 | topic | `豆腐`/とうふ | 0.306 | topic | food_cooking |
| 11 | `豆腐`/とうふ | 0.306 | food_cooking | `解釈`/かいしゃく | 0.254 | trail | `林檎`/りんご | 0.304 | topic | `林檎`/りんご | 0.304 | topic | food_cooking |
| 12 | `チーズ`/ちーず | 0.211 | food_cooking | `市`/いち | 0.350 | frontier | `コンビニ`/こんびに | 0.280 | topic | `コンビニ`/こんびに | 0.280 | topic | travel_places_transport |

- legacy_v5_only: `道路, 酒, 観光, 茶, 鍋, 列車, ビール, スープ, バイク, 信号, 豆腐, チーズ`
- frontier_only: `喫茶, 包丁, 箸, 税, 説, 保証, 憲法, 心理, 解釈, 市, 上限, 雛`
- legacy_v5_only_vs_hybrid: `道路, 酒, 観光, 茶, ビール, スープ, バイク, 出来る, 良く, 彼女, 矢張り, 共`
- hybrid_only_vs_legacy_v5: `喫茶, 包丁, 箸, パスタ, 税, 説, 保証, 憲法, 心理, 解釈, 市, 上限`
- hybrid_soft_only_vs_legacy_v5: `喫茶, 包丁, 箸, パスタ, 税, 説, 保証, 憲法, 心理, 解釈, 市, 上限`
- hybrid_soft_only_vs_hybrid: ``

### `mixed_science_medicine`

- proficiency: `0.550`
- topics: `science_math, medicine_health`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 42, 'mass': 0.057242, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `三角`/さんかく | 0.303 | science_math | `三角`/さんかく | 0.303 | topic | `バランス`/ばらんす | 0.429 | trail | `バランス`/ばらんす | 0.429 | trail | - |
| 2 | `爪`/つめ | 0.299 | medicine_health | `爪`/つめ | 0.299 | topic | `ワン`/わん | 0.421 | trail | `ワン`/わん | 0.421 | trail | - |
| 3 | `皮膚`/ひふ | 0.293 | medicine_health | `皮膚`/ひふ | 0.293 | topic | `なお`/なお | 0.415 | trail | `なお`/なお | 0.415 | trail | - |
| 4 | `公式`/こうしき | 0.284 | science_math | `公式`/こうしき | 0.284 | topic | `我々` | 0.450 | trail | `我々` | 0.450 | trail | - |
| 5 | `理論`/りろん | 0.279 | science_math | `バランス`/ばらんす | 0.429 | trail | `キー`/きー | 0.442 | trail | `キー`/きー | 0.442 | trail | - |
| 6 | `胃`/い | 0.257 | medicine_health | `ワン`/わん | 0.421 | trail | `コスト`/こすと | 0.422 | trail | `コスト`/こすと | 0.422 | trail | - |
| 7 | `物理`/ぶつり | 0.254 | science_math | `なお`/なお | 0.415 | trail | `パワー`/ぱわー | 0.438 | trail | `パワー`/ぱわー | 0.438 | trail | - |
| 8 | `心臓`/しんぞう | 0.252 | medicine_health | `我々` | 0.450 | trail | `育種`/いくしゅ | 0.551 | frontier | `育種`/いくしゅ | 0.551 | frontier | - |
| 9 | `怪我`/けが | 0.244 | medicine_health | `キー`/きー | 0.442 | trail | `受検`/じゅけん | 0.551 | frontier | `受検`/じゅけん | 0.551 | frontier | - |
| 10 | `化学`/かがく | 0.243 | science_math | `コスト`/こすと | 0.422 | trail | `公序`/こうじょ | 0.549 | frontier | `公序`/こうじょ | 0.549 | frontier | - |
| 11 | `膝`/ひざ | 0.237 | medicine_health | `パワー`/ぱわー | 0.438 | trail | `年報`/ねんぽう | 0.549 | frontier | `年報`/ねんぽう | 0.549 | frontier | - |
| 12 | `温度`/おんど | 0.235 | science_math | `育種`/いくしゅ | 0.551 | frontier | `骨太`/ほねぶと | 0.548 | frontier | `骨太`/ほねぶと | 0.548 | frontier | - |

- legacy_v5_only: `理論, 胃, 物理, 心臓, 怪我, 化学, 膝, 温度, 腹, 御座る, 感, 当該`
- frontier_only: `パワー, 育種, 受検, 公序, 年報, 骨太, 口述, 続発, 調製, ゴロ, 十二指腸, 畑地`
- legacy_v5_only_vs_hybrid: `三角, 爪, 皮膚, 公式, 理論, 胃, 物理, 心臓, 怪我, 化学, 膝, 温度`
- hybrid_only_vs_legacy_v5: `パワー, 育種, 受検, 公序, 年報, 骨太, 口述, 続発, 調製, ゴロ, 十二指腸, 畑地`
- hybrid_soft_only_vs_legacy_v5: `パワー, 育種, 受検, 公序, 年報, 骨太, 口述, 続発, 調製, ゴロ, 十二指腸, 畑地`
- hybrid_soft_only_vs_hybrid: ``

### `food_cooking_beginner`

- proficiency: `0.200`
- topics: `food_cooking`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid topic depth: `{'eligible_candidate_count': 44, 'eligible_mass': 39.570867, 'candidate_count': 46, 'mass': 39.610032, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft topic depth: `{'eligible_candidate_count': 44, 'eligible_mass': 39.570867, 'candidate_count': 46, 'mass': 39.610032, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `飲む`/のむ | 0.053 | food_cooking | `酒`/さけ | 0.199 | topic | `酒`/さけ | 0.199 | topic | `酒`/さけ | 0.199 | topic | food_cooking |
| 2 | `食べる`/たべる | 0.027 | food_cooking | `スープ`/すーぷ | 0.206 | topic | `スープ`/すーぷ | 0.206 | topic | `スープ`/すーぷ | 0.206 | topic | food_cooking |
| 3 | `料理`/りょうり | 0.044 | food_cooking | `茶`/ちゃ | 0.208 | topic | `茶`/ちゃ | 0.208 | topic | `茶`/ちゃ | 0.208 | topic | food_cooking |
| 4 | `酒`/さけ | 0.199 | food_cooking | `チーズ`/ちーず | 0.211 | topic | `チーズ`/ちーず | 0.211 | topic | `チーズ`/ちーず | 0.211 | topic | food_cooking |
| 5 | `味`/あじ | 0.135 | food_cooking | `ある`/ある | 0.120 | trail | `ビール`/びーる | 0.186 | topic | `ビール`/びーる | 0.186 | topic | food_cooking |
| 6 | `野菜`/やさい | 0.067 | food_cooking | `こと`/こと | 0.120 | trail | `トマト`/とまと | 0.180 | topic | `トマト`/とまと | 0.180 | topic | food_cooking |
| 7 | `パン`/ぱん | 0.118 | food_cooking | `よう`/よう | 0.123 | trail | `ワイン`/わいん | 0.173 | topic | `ワイン`/わいん | 0.173 | topic | food_cooking |
| 8 | `焼く`/やく | 0.147 | food_cooking | `思う`/おもう | 0.124 | trail | `ハンバーグ`/はんばーぐ | 0.168 | topic | `ハンバーグ`/はんばーぐ | 0.168 | topic | food_cooking |
| 9 | `肉`/にく | 0.083 | food_cooking | `見る`/みる | 0.124 | trail | `ジュース`/じゅーす | 0.168 | topic | `ジュース`/じゅーす | 0.168 | topic | food_cooking |
| 10 | `甘い`/あまい | 0.072 | food_cooking | `そう`/そう | 0.125 | trail | `ラーメン`/らーめん | 0.167 | topic | `ラーメン`/らーめん | 0.167 | topic | food_cooking |
| 11 | `コーヒー`/こーひー | 0.117 | food_cooking | `場合`/ばあい | 0.125 | trail | `サラダ`/さらだ | 0.166 | topic | `サラダ`/さらだ | 0.166 | topic | food_cooking |
| 12 | `ビール`/びーる | 0.186 | food_cooking | `彼女` | 0.200 | frontier | `味噌`/みそ | 0.152 | topic | `味噌`/みそ | 0.152 | topic | food_cooking |

- legacy_v5_only: `飲む, 食べる, 料理, 味, 野菜, パン, 焼く, 肉, 甘い, コーヒー, ビール, 冷たい`
- frontier_only: `スープ, 茶, チーズ, 彼女, 殺す, 記事, 道路, 完成, 範囲, 指定, 動画, 素晴らしい`
- legacy_v5_only_vs_hybrid: `飲む, 食べる, 料理, 野菜, パン, 肉, 甘い, コーヒー, 冷たい, 熱い, 醤油, 砂糖`
- hybrid_only_vs_legacy_v5: `スープ, 茶, チーズ, トマト, ハンバーグ, ジュース, ラーメン, サラダ, 鍋, 彼女, 殺す, 記事`
- hybrid_soft_only_vs_legacy_v5: `スープ, 茶, チーズ, トマト, ハンバーグ, ジュース, ラーメン, サラダ, 鍋, 彼女, 殺す, 記事`
- hybrid_soft_only_vs_hybrid: ``

### `anime_manga_intermediate`

- proficiency: `0.450`
- topics: `anime_manga_pop_culture`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid topic depth: `{'eligible_candidate_count': 37, 'eligible_mass': 31.526915, 'candidate_count': 37, 'mass': 31.526915, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 16, 'trail': 7, 'topic': 17}`
- hybrid soft topic depth: `{'eligible_candidate_count': 44, 'eligible_mass': 33.285683, 'candidate_count': 55, 'mass': 33.376337, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `ファン`/ふぁん | 0.411 | anime_manga_pop_culture | `属性`/ぞくせい | 0.465 | topic | `属性`/ぞくせい | 0.465 | topic | `属性`/ぞくせい | 0.465 | topic | anime_manga_pop_culture |
| 2 | `コメント`/こめんと | 0.419 | anime_manga_pop_culture | `ポスター`/ぽすたー | 0.474 | topic | `ポスター`/ぽすたー | 0.474 | topic | `ポスター`/ぽすたー | 0.474 | topic | anime_manga_pop_culture |
| 3 | `感想`/かんそう | 0.286 | anime_manga_pop_culture | `コメント`/こめんと | 0.419 | topic | `コメント`/こめんと | 0.419 | topic | `コメント`/こめんと | 0.419 | topic | anime_manga_pop_culture |
| 4 | `考察`/こうさつ | 0.329 | anime_manga_pop_culture | `回想`/かいそう | 0.415 | topic | `回想`/かいそう | 0.415 | topic | `回想`/かいそう | 0.415 | topic | anime_manga_pop_culture |
| 5 | `恋愛`/れんあい | 0.280 | anime_manga_pop_culture | `其々`/それぞれ | 0.327 | trail | `ファン`/ふぁん | 0.411 | topic | `ファン`/ふぁん | 0.411 | topic | anime_manga_pop_culture |
| 6 | `学園`/がくえん | 0.339 | anime_manga_pop_culture | `共`/とも | 0.322 | trail | `名作`/めいさく | 0.411 | topic | `名作`/めいさく | 0.411 | topic | anime_manga_pop_culture |
| 7 | `再開`/さいかい | 0.328 | anime_manga_pop_culture | `限り`/かぎり | 0.334 | trail | `タッチ`/たっち | 0.493 | topic | `タッチ`/たっち | 0.493 | topic | anime_manga_pop_culture |
| 8 | `連載`/れんさい | 0.360 | anime_manga_pop_culture | `奴`/やつ | 0.331 | trail | `傑作`/けっさく | 0.400 | topic | `傑作`/けっさく | 0.400 | topic | anime_manga_pop_culture |
| 9 | `主役`/しゅやく | 0.348 | anime_manga_pop_culture | `扠`/さて | 0.336 | trail | `尊い`/とうとい | 0.397 | topic | `尊い`/とうとい | 0.397 | topic | anime_manga_pop_culture |
| 10 | `制服`/せいふく | 0.360 | anime_manga_pop_culture | `急度`/きっと | 0.337 | trail | `イラスト`/いらすと | 0.505 | topic | `イラスト`/いらすと | 0.505 | topic | anime_manga_pop_culture |
| 11 | `原作`/げんさく | 0.344 | anime_manga_pop_culture | `イン`/いん | 0.336 | trail | `脚本`/きゃくほん | 0.388 | topic | `脚本`/きゃくほん | 0.388 | topic | anime_manga_pop_culture |
| 12 | `表紙`/ひょうし | 0.351 | anime_manga_pop_culture | `我々` | 0.450 | frontier | `特典`/とくてん | 0.382 | topic | `特典`/とくてん | 0.382 | topic | anime_manga_pop_culture |

- legacy_v5_only: `ファン, 感想, 考察, 恋愛, 学園, 再開, 連載, 主役, 制服, 原作, 表紙, 青春`
- frontier_only: `属性, ポスター, 扠, 急度, イン, ハードディスク, 洋画, 随所, 自前, 公布, 慣行, 変数`
- legacy_v5_only_vs_hybrid: `感想, 考察, 恋愛, 学園, 再開, 連載, 主役, 制服, 原作, 表紙, ジャンル, キャラクター`
- hybrid_only_vs_legacy_v5: `属性, ポスター, 名作, タッチ, 尊い, イラスト, 特典, 字幕, フィギュア, 扠, 急度, イン`
- hybrid_soft_only_vs_legacy_v5: `属性, ポスター, 名作, タッチ, 尊い, イラスト, 特典, 字幕, フィギュア, 扠, 急度, イン`
- hybrid_soft_only_vs_hybrid: ``

### `probe_neutral_expert`

- proficiency: `0.930`
- topics: `-`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 33, 'trail': 7, 'topic': 0}`
- hybrid soft topic depth: `{'eligible_candidate_count': 0, 'eligible_mass': 0, 'candidate_count': 0, 'mass': 0, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `ハザード`/はざーど | 0.790 | - | `ハザード`/はざーど | 0.790 | trail | `ハザード`/はざーど | 0.790 | trail | `ハザード`/はざーど | 0.790 | trail | - |
| 2 | `ファー`/ふぁー | 0.937 | - | `飯蛸`/いいだこ | 0.800 | trail | `飯蛸`/いいだこ | 0.800 | trail | `飯蛸`/いいだこ | 0.800 | trail | - |
| 3 | `山桃`/やまもも | 0.782 | - | `唐臼`/からうす | 0.796 | trail | `唐臼`/からうす | 0.796 | trail | `唐臼`/からうす | 0.796 | trail | - |
| 4 | `見栄っ張り`/みえっぱり | 0.781 | - | `兜蟹`/かぶとがに | 0.791 | trail | `兜蟹`/かぶとがに | 0.791 | trail | `兜蟹`/かぶとがに | 0.791 | trail | - |
| 5 | `売り越し`/うりこし | 0.785 | - | `売り越し`/うりこし | 0.785 | trail | `売り越し`/うりこし | 0.785 | trail | `売り越し`/うりこし | 0.785 | trail | - |
| 6 | `デス`/です | 0.937 | - | `梶木鮪`/かじきまぐろ | 0.784 | trail | `梶木鮪`/かじきまぐろ | 0.784 | trail | `梶木鮪`/かじきまぐろ | 0.784 | trail | - |
| 7 | `梶木鮪`/かじきまぐろ | 0.784 | - | `山桃`/やまもも | 0.782 | trail | `山桃`/やまもも | 0.782 | trail | `山桃`/やまもも | 0.782 | trail | - |
| 8 | `兜蟹`/かぶとがに | 0.791 | - | `シュラフ`/しゅらふ | 0.937 | frontier | `シュラフ`/しゅらふ | 0.937 | frontier | `シュラフ`/しゅらふ | 0.937 | frontier | - |
| 9 | `飯蛸`/いいだこ | 0.800 | - | `キュイジーヌ`/きゅいじーぬ | 0.937 | frontier | `キュイジーヌ`/きゅいじーぬ | 0.937 | frontier | `キュイジーヌ`/きゅいじーぬ | 0.937 | frontier | - |
| 10 | `黒痣`/くろあざ | 0.777 | - | `パラサイト`/ぱらさいと | 0.937 | frontier | `パラサイト`/ぱらさいと | 0.937 | frontier | `パラサイト`/ぱらさいと | 0.937 | frontier | - |
| 11 | `唐臼`/からうす | 0.796 | - | `ハンドラー`/はんどらー | 0.937 | frontier | `ハンドラー`/はんどらー | 0.937 | frontier | `ハンドラー`/はんどらー | 0.937 | frontier | - |
| 12 | `スピリチュアリズム`/すぴりちゅありずむ | 0.778 | - | `デバッグ`/でばっぐ | 0.937 | frontier | `デバッグ`/でばっぐ | 0.937 | frontier | `デバッグ`/でばっぐ | 0.937 | frontier | - |

- legacy_v5_only: `見栄っ張り, 黒痣, スピリチュアリズム, 所記, 実包, 丁数, 鉄船, 脱北, アウトリーチ, コスメ, チューバ, インナー`
- frontier_only: `と, 平方メートル, 立方メートル, 床, ジョン, フィックス, ローブ, ＬＳＩ, ＴＯＢ, ブッシュ, ＰＯＰ, ＦＸ`
- legacy_v5_only_vs_hybrid: `見栄っ張り, 黒痣, スピリチュアリズム, 所記, 実包, 丁数, 鉄船, 脱北, アウトリーチ, コスメ, チューバ, インナー`
- hybrid_only_vs_legacy_v5: `と, 平方メートル, 立方メートル, 床, ジョン, フィックス, ローブ, ＬＳＩ, ＴＯＢ, ブッシュ, ＰＯＰ, ＦＸ`
- hybrid_soft_only_vs_legacy_v5: `と, 平方メートル, 立方メートル, 床, ジョン, フィックス, ローブ, ＬＳＩ, ＴＯＢ, ブッシュ, ＰＯＰ, ＦＸ`
- hybrid_soft_only_vs_hybrid: ``

### `probe_plants_nature_mid`

- proficiency: `0.440`
- topics: `plants_nature`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 21, 'trail': 7, 'topic': 12}`
- hybrid lane fills: `{'core': 0, 'frontier': 21, 'trail': 7, 'topic': 12}`
- hybrid topic depth: `{'eligible_candidate_count': 12, 'eligible_mass': 9.92927, 'candidate_count': 12, 'mass': 9.92927, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 21, 'trail': 7, 'topic': 12}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 21, 'trail': 7, 'topic': 12}`
- hybrid soft topic depth: `{'eligible_candidate_count': 12, 'eligible_mass': 9.92927, 'candidate_count': 21, 'mass': 9.929392, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `林檎`/りんご | 0.304 | plants_nature | `苺`/いちご | 0.383 | topic | `苺`/いちご | 0.383 | topic | `苺`/いちご | 0.383 | topic | plants_nature |
| 2 | `葡萄`/ぶどう | 0.327 | plants_nature | `麦`/むぎ | 0.375 | topic | `麦`/むぎ | 0.375 | topic | `麦`/むぎ | 0.375 | topic | plants_nature |
| 3 | `火山`/かざん | 0.336 | plants_nature | `津波`/つなみ | 0.373 | topic | `津波`/つなみ | 0.373 | topic | `津波`/つなみ | 0.373 | topic | plants_nature |
| 4 | `杉`/すぎ | 0.356 | plants_nature | `洪水`/こうずい | 0.365 | topic | `洪水`/こうずい | 0.365 | topic | `洪水`/こうずい | 0.365 | topic | plants_nature |
| 5 | `苺`/いちご | 0.383 | plants_nature | `共`/とも | 0.322 | trail | `杉`/すぎ | 0.356 | topic | `杉`/すぎ | 0.356 | topic | plants_nature |
| 6 | `洪水`/こうずい | 0.365 | plants_nature | `其々`/それぞれ | 0.327 | trail | `蜜柑`/みかん | 0.351 | topic | `蜜柑`/みかん | 0.351 | topic | plants_nature |
| 7 | `蜜柑`/みかん | 0.351 | plants_nature | `矢張り`/やはり | 0.317 | trail | `火山`/かざん | 0.336 | topic | `火山`/かざん | 0.336 | topic | plants_nature |
| 8 | `麦`/むぎ | 0.375 | plants_nature | `此方`/こちら | 0.321 | trail | `葡萄`/ぶどう | 0.327 | topic | `葡萄`/ぶどう | 0.327 | topic | plants_nature |
| 9 | `津波`/つなみ | 0.373 | plants_nature | `奴`/やつ | 0.331 | trail | `林檎`/りんご | 0.304 | topic | `林檎`/りんご | 0.304 | topic | plants_nature |
| 10 | `気温`/きおん | 0.256 | plants_nature | `限り`/かぎり | 0.334 | trail | `檜`/ひのき | 0.584 | topic | `檜`/ひのき | 0.584 | topic | plants_nature |
| 11 | `豆`/まめ | 0.250 | plants_nature | `常`/つね | 0.322 | trail | `気温`/きおん | 0.256 | topic | `気温`/きおん | 0.256 | topic | plants_nature |
| 12 | `檜`/ひのき | 0.584 | plants_nature | `香る`/かおる | 0.440 | frontier | `豆`/まめ | 0.250 | topic | `豆`/まめ | 0.250 | topic | plants_nature |

- legacy_v5_only: `林檎, 葡萄, 火山, 杉, 蜜柑, 気温, 豆, 檜, 雲, 台風, 森, 季節`
- frontier_only: `香る, 浜辺, 全集, 中部, 傘下, 引き下げ, 究明, 自助, 連行, ギョーザ, 打開, 暗黙`
- legacy_v5_only_vs_hybrid: `雲, 台風, 森, 季節, 地震, 良く, センター, サービス, 旨い, 然も, なお, 当該`
- hybrid_only_vs_legacy_v5: `香る, 浜辺, 全集, 中部, 傘下, 引き下げ, 究明, 自助, 連行, ギョーザ, 打開, 暗黙`
- hybrid_soft_only_vs_legacy_v5: `香る, 浜辺, 全集, 中部, 傘下, 引き下げ, 究明, 自助, 連行, ギョーザ, 打開, 暗黙`
- hybrid_soft_only_vs_hybrid: ``

### `probe_plants_nature_upper`

- proficiency: `0.620`
- topics: `plants_nature`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid lane fills: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid topic depth: `{'eligible_candidate_count': 1, 'eligible_mass': 0.973195, 'candidate_count': 1, 'mass': 0.973195, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid soft topic depth: `{'eligible_candidate_count': 1, 'eligible_mass': 0.973195, 'candidate_count': 21, 'mass': 1.109103, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `檜`/ひのき | 0.584 | plants_nature | `檜`/ひのき | 0.584 | topic | `檜`/ひのき | 0.584 | topic | `檜`/ひのき | 0.584 | topic | plants_nature |
| 2 | `苺`/いちご | 0.383 | plants_nature | `苺`/いちご | 0.383 | topic | `御座る`/ござる | 0.493 | trail | `御座る`/ござる | 0.493 | trail | - |
| 3 | `麦`/むぎ | 0.375 | plants_nature | `麦`/むぎ | 0.375 | topic | `アンド`/あんど | 0.491 | trail | `アンド`/あんど | 0.491 | trail | - |
| 4 | `津波`/つなみ | 0.373 | plants_nature | `津波`/つなみ | 0.373 | topic | `ブロック`/ぶろっく | 0.496 | trail | `ブロック`/ぶろっく | 0.496 | trail | - |
| 5 | `洪水`/こうずい | 0.365 | plants_nature | `御座る`/ござる | 0.493 | trail | `サーバー`/さーばー | 0.498 | trail | `サーバー`/さーばー | 0.498 | trail | - |
| 6 | `杉`/すぎ | 0.356 | plants_nature | `アンド`/あんど | 0.491 | trail | `ロック`/ろっく | 0.500 | trail | `ロック`/ろっく | 0.500 | trail | - |
| 7 | `蜜柑`/みかん | 0.351 | plants_nature | `ブロック`/ぶろっく | 0.496 | trail | `カット`/かっと | 0.488 | trail | `カット`/かっと | 0.488 | trail | - |
| 8 | `火山`/かざん | 0.336 | plants_nature | `サーバー`/さーばー | 0.498 | trail | `リアル`/りある | 0.503 | trail | `リアル`/りある | 0.503 | trail | - |
| 9 | `葡萄`/ぶどう | 0.327 | plants_nature | `ロック`/ろっく | 0.500 | trail | `木質`/もくしつ | 0.620 | frontier | `木質`/もくしつ | 0.620 | frontier | - |
| 10 | `林檎`/りんご | 0.304 | plants_nature | `カット`/かっと | 0.488 | trail | `カテ`/かて | 0.621 | frontier | `カテ`/かて | 0.621 | frontier | - |
| 11 | `御座る`/ござる | 0.493 | - | `リアル`/りある | 0.503 | trail | `プロバイダー`/ぷろばいだー | 0.621 | frontier | `プロバイダー`/ぷろばいだー | 0.621 | frontier | - |
| 12 | `項`/こう | 0.572 | - | `木質`/もくしつ | 0.620 | frontier | `おまる`/おまる | 0.621 | frontier | `おまる`/おまる | 0.621 | frontier | - |

- legacy_v5_only: `洪水, 杉, 蜜柑, 火山, 葡萄, 林檎, 項, 感, 論, 通ずる, 府, 因み`
- frontier_only: `ブロック, サーバー, ロック, リアル, 木質, カテ, プロバイダー, おまる, 排熱, 足軽, 米糠, スリー`
- legacy_v5_only_vs_hybrid: `苺, 麦, 津波, 洪水, 杉, 蜜柑, 火山, 葡萄, 林檎, 項, 感, 論`
- hybrid_only_vs_legacy_v5: `ブロック, サーバー, ロック, リアル, 木質, カテ, プロバイダー, おまる, 排熱, 足軽, 米糠, スリー`
- hybrid_soft_only_vs_legacy_v5: `ブロック, サーバー, ロック, リアル, 木質, カテ, プロバイダー, おまる, 排熱, 足軽, 米糠, スリー`
- hybrid_soft_only_vs_hybrid: ``

### `probe_plants_nature_advanced`

- proficiency: `0.730`
- topics: `plants_nature`
- frontier lane targets: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- frontier lane fills: `{'frontier': 29, 'trail': 7, 'topic': 4}`
- hybrid lane targets: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid lane fills: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid topic depth: `{'eligible_candidate_count': 1, 'eligible_mass': 0.576541, 'candidate_count': 1, 'mass': 0.576541, 'minimum_lane_score': 0.08}`
- hybrid soft lane targets: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid soft lane fills: `{'core': 0, 'frontier': 32, 'trail': 7, 'topic': 1}`
- hybrid soft topic depth: `{'eligible_candidate_count': 1, 'eligible_mass': 0.576541, 'candidate_count': 21, 'mass': 0.576541, 'minimum_lane_score': 0.08}`

| # | Legacy v5 | Diff | Topic | Frontier | Diff | Lane | Hybrid | Diff | Lane | Hybrid soft | Diff | Lane | Topic |
| ---: | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- |
| 1 | `檜`/ひのき | 0.584 | plants_nature | `檜`/ひのき | 0.584 | topic | `檜`/ひのき | 0.584 | topic | `檜`/ひのき | 0.584 | topic | plants_nature |
| 2 | `項`/こう | 0.572 | - | `苺`/いちご | 0.383 | topic | `エクセル`/えくせる | 0.604 | trail | `エクセル`/えくせる | 0.604 | trail | - |
| 3 | `論`/ろん | 0.576 | - | `麦`/むぎ | 0.375 | topic | `インストール`/いんすとーる | 0.596 | trail | `インストール`/いんすとーる | 0.596 | trail | - |
| 4 | `府`/ふ | 0.574 | - | `津波`/つなみ | 0.373 | topic | `前掲`/ぜんけい | 0.596 | trail | `前掲`/ぜんけい | 0.596 | trail | - |
| 5 | `層`/そう | 0.576 | - | `エクセル`/えくせる | 0.604 | trail | `カテ`/かて | 0.621 | trail | `カテ`/かて | 0.621 | trail | - |
| 6 | `増`/ぞう | 0.577 | - | `インストール`/いんすとーる | 0.596 | trail | `サン`/さん | 0.594 | trail | `サン`/さん | 0.594 | trail | - |
| 7 | `故`/ゆえ | 0.577 | - | `前掲`/ぜんけい | 0.596 | trail | `スリー`/すりー | 0.622 | trail | `スリー`/すりー | 0.622 | trail | - |
| 8 | `ザ`/ざ | 0.578 | - | `カテ`/かて | 0.621 | trail | `スキル`/すきる | 0.600 | trail | `スキル`/すきる | 0.600 | trail | - |
| 9 | `有り`/あり | 0.577 | - | `サン`/さん | 0.594 | trail | `潮干`/しおひ | 0.732 | frontier | `潮干`/しおひ | 0.732 | frontier | - |
| 10 | `御陰`/おかげ | 0.577 | - | `スリー`/すりー | 0.622 | trail | `テレワーク`/てれわーく | 0.727 | frontier | `テレワーク`/てれわーく | 0.727 | frontier | - |
| 11 | `引き続く`/ひきつづく | 0.577 | - | `スキル`/すきる | 0.600 | trail | `ステント`/すてんと | 0.733 | frontier | `ステント`/すてんと | 0.733 | frontier | - |
| 12 | `動産`/どうさん | 0.577 | - | `潮干`/しおひ | 0.732 | frontier | `林木`/りんぼく | 0.734 | frontier | `林木`/りんぼく | 0.734 | frontier | - |

- legacy_v5_only: `項, 論, 府, 層, 増, 故, ザ, 有り, 御陰, 引き続く, 動産, 主な`
- frontier_only: `苺, 麦, 津波, エクセル, 前掲, カテ, スリー, スキル, 潮干, テレワーク, ステント, 林木`
- legacy_v5_only_vs_hybrid: `項, 論, 府, 層, 増, 故, ザ, 有り, 御陰, 引き続く, 動産, 主な`
- hybrid_only_vs_legacy_v5: `エクセル, 前掲, カテ, スリー, スキル, 潮干, テレワーク, ステント, 林木, 門脈, 勅許, 内腔`
- hybrid_soft_only_vs_legacy_v5: `エクセル, 前掲, カテ, スリー, スキル, 潮干, テレワーク, ステント, 林木, 門脈, 勅許, 内腔`
- hybrid_soft_only_vs_hybrid: ``
