# SRS Browsing Admission Signal Gradient (en-ja)

- Status: `PASS`
- Groups: `4`
- Scenarios: `36`
- Scenario pass/warn/fail: `36` / `0` / `0`
- Pair: `en-ja`
- Runtime scope: `preview_only_implicit_browsing_admission_signal_gradient`

## Interpretation

This artifact varies already-resolved browsing aggregate counts to show when weak, medium, and saturated history begins changing preview admission. It does not validate live page-text extraction or mutate SRS.

## Group Thresholds

| Group | Side | Lemmas | First balanced lane | First strong lane | Max balanced lane | Max strong lane |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `explicit_food_four_target_p20` | `target` | 4 | 0.5 | 0.25 | 2 | 3 |
| `four_food_replacement_exposure_p20` | `replacement_exposure` | 4 | 2 | 0.5 | 1 | 3 |
| `four_food_target_p20` | `target` | 4 | 0.5 | 0.25 | 2 | 3 |
| `single_food_target_p20` | `target` | 1 | 4 | 1 | 1 | 1 |

## Curves

### explicit_food_four_target_p20

| Count | Raw/lemma | Signal/lemma | Signal total | Balanced lane/driven | Strong lane/driven | Strong selected |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.000 | 0.000 | 0.000 | 0/0 | 0/0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| 0.25 | 0.250 | 0.079 | 0.315 | 0/0 | 1/0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| 0.5 | 0.500 | 0.143 | 0.572 | 1/0 | 1/0 | 料理, 食べる, 飲む, 酒, 味, 野菜, パン, 焼く |
| 1 | 1.000 | 0.245 | 0.979 | 1/0 | 1/0 | 料理, 食べる, 飲む, 酒, 味, 野菜, パン, 焼く |
| 2 | 2.000 | 0.388 | 1.551 | 1/0 | 2/0 | 料理, 食べる, 飲む, 酒, 味, 野菜, パン, 焼く |
| 4 | 4.000 | 0.568 | 2.272 | 1/0 | 2/0 | 料理, 食べる, 飲む, 酒, 味, 野菜, パン, 焼く |
| 8 | 8.000 | 0.776 | 3.102 | 1/0 | 3/0 | 料理, 食べる, 野菜, 飲む, 酒, 味, パン, 焼く |
| 16 | 16.000 | 1.000 | 4.000 | 2/0 | 3/0 | 料理, 食べる, 野菜, 飲む, 酒, 味, パン, 焼く |
| 32 | 32.000 | 1.000 | 4.000 | 2/0 | 3/0 | 料理, 食べる, 野菜, 飲む, 酒, 味, パン, 焼く |

### four_food_replacement_exposure_p20

| Count | Raw/lemma | Signal/lemma | Signal total | Balanced lane/driven | Strong lane/driven | Strong selected |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.000 | 0.000 | 0.000 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 0.25 | 0.087 | 0.030 | 0.118 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 0.5 | 0.175 | 0.057 | 0.228 | 0/0 | 1/1 | 飲む, ある, こと, よう, 思う, 見る, 良い, その |
| 1 | 0.350 | 0.106 | 0.424 | 0/0 | 1/1 | 飲む, ある, こと, よう, 思う, 見る, 良い, その |
| 2 | 0.700 | 0.187 | 0.749 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 4 | 1.400 | 0.309 | 1.236 | 1/1 | 2/2 | 料理, 飲む, ある, こと, よう, 思う, 見る, 良い |
| 8 | 2.800 | 0.471 | 1.885 | 1/1 | 2/2 | 料理, 野菜, ある, こと, よう, 思う, 見る, 良い |
| 16 | 5.600 | 0.666 | 2.664 | 1/1 | 3/3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |
| 32 | 11.200 | 0.883 | 3.532 | 1/1 | 3/3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |

### four_food_target_p20

| Count | Raw/lemma | Signal/lemma | Signal total | Balanced lane/driven | Strong lane/driven | Strong selected |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.000 | 0.000 | 0.000 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 0.25 | 0.250 | 0.079 | 0.315 | 0/0 | 1/1 | 飲む, ある, こと, よう, 思う, 見る, 良い, その |
| 0.5 | 0.500 | 0.143 | 0.572 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 1 | 1.000 | 0.245 | 0.979 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 2 | 2.000 | 0.388 | 1.551 | 1/1 | 2/2 | 料理, 飲む, ある, こと, よう, 思う, 見る, 良い |
| 4 | 4.000 | 0.568 | 2.272 | 1/1 | 2/2 | 料理, 野菜, ある, こと, よう, 思う, 見る, 良い |
| 8 | 8.000 | 0.776 | 3.102 | 1/1 | 3/3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |
| 16 | 16.000 | 1.000 | 4.000 | 2/2 | 3/3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |
| 32 | 32.000 | 1.000 | 4.000 | 2/2 | 3/3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |

### single_food_target_p20

| Count | Raw/lemma | Signal/lemma | Signal total | Balanced lane/driven | Strong lane/driven | Strong selected |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.000 | 0.000 | 0.000 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 0.25 | 0.250 | 0.079 | 0.079 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 0.5 | 0.500 | 0.143 | 0.143 | 0/0 | 0/0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| 1 | 1.000 | 0.245 | 0.245 | 0/0 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 2 | 2.000 | 0.388 | 0.388 | 0/0 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 4 | 4.000 | 0.568 | 0.568 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 8 | 8.000 | 0.776 | 0.776 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 16 | 16.000 | 1.000 | 1.000 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |
| 32 | 32.000 | 1.000 | 1.000 | 1/1 | 1/1 | 料理, ある, こと, よう, 思う, 見る, 良い, その |

## Findings

| Level | Code | Message |
| --- | --- | --- |
| `PASS` | `ALL_SCENARIOS_PASS` | All count-gradient scenarios satisfied baseline preview expectations. |
| `PASS` | `explicit_food_four_target_p20:SIGNAL_TOTAL_MONOTONIC` | Normalized signal volume is nondecreasing as count rises. |
| `PASS` | `explicit_food_four_target_p20:BALANCED_LANE_MONOTONIC` | balanced browsing lane count is nondecreasing. |
| `PASS` | `explicit_food_four_target_p20:STRONG_LANE_MONOTONIC` | strong browsing lane count is nondecreasing. |
| `PASS` | `four_food_replacement_exposure_p20:SIGNAL_TOTAL_MONOTONIC` | Normalized signal volume is nondecreasing as count rises. |
| `PASS` | `four_food_replacement_exposure_p20:BALANCED_LANE_MONOTONIC` | balanced browsing lane count is nondecreasing. |
| `PASS` | `four_food_replacement_exposure_p20:STRONG_LANE_MONOTONIC` | strong browsing lane count is nondecreasing. |
| `PASS` | `four_food_target_p20:SIGNAL_TOTAL_MONOTONIC` | Normalized signal volume is nondecreasing as count rises. |
| `PASS` | `four_food_target_p20:BALANCED_LANE_MONOTONIC` | balanced browsing lane count is nondecreasing. |
| `PASS` | `four_food_target_p20:STRONG_LANE_MONOTONIC` | strong browsing lane count is nondecreasing. |
| `PASS` | `single_food_target_p20:SIGNAL_TOTAL_MONOTONIC` | Normalized signal volume is nondecreasing as count rises. |
| `PASS` | `single_food_target_p20:BALANCED_LANE_MONOTONIC` | balanced browsing lane count is nondecreasing. |
| `PASS` | `single_food_target_p20:STRONG_LANE_MONOTONIC` | strong browsing lane count is nondecreasing. |
