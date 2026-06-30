# en-ja JLPT Reference Comparison

Generated: `2026-06-22T01:10:34Z`

Status: research-only sidecar; no runtime behavior changed and no product data ingested.

## Purpose

Measure whether `stephenmk/yomichan-jlpt-vocab` is useful as a reference for repairing effective-exact JLPT surface+reading coverage in the current en-ja learner-difficulty matrix.

## Source-Level Comparison

| Metric | Value |
| --- | ---: |
| `current_unique_pairs` | 8430 |
| `stephen_original_unique_pairs` | 8287 |
| `stephen_original_pairs_overlap_current` | 7647 |
| `stephen_original_pairs_only_in_reference` | 640 |
| `stephen_yomitan_unique_pairs` | 8113 |
| `stephen_yomitan_pairs_overlap_current` | 7691 |
| `stephen_yomitan_pairs_only_in_reference` | 422 |
| `stephen_sequence_expanded_unique_pairs` | 13735 |
| `stephen_sequence_expanded_pairs_only_in_reference` | 6365 |
| `stephen_sequence_same_reading_unique_pairs` | 12112 |
| `stephen_sequence_same_reading_pairs_only_in_reference` | 4743 |
| `unsafe_full_sequence_extra_pairs` | 1623 |

## Matrix Impact Estimate

| Metric | Value |
| --- | ---: |
| `matrix_rows` | 73752 |
| `first60_rows_by_core_rank` | 26201 |
| `current_matrix_jlpt_known` | 7800 |
| `current_matrix_jlpt_exact_known` | 6788 |
| `current_matrix_jlpt_normalized_exact_known` | 387 |
| `current_matrix_jlpt_guarded_normalized_exact_known` | 92 |
| `current_matrix_jlpt_effective_exact_known` | 6950 |
| `current_matrix_broad_only` | 850 |
| `broad_only_reference_exact` | 82 |
| `broad_only_yomitan_exact` | 56 |
| `broad_only_sequence_exact` | 41 |
| `reference_exact_not_current_exact` | 200 |
| `reference_exact_not_raw_exact` | 356 |
| `reference_exact_not_current_broad` | 118 |
| `first60_reference_exact_not_current_exact` | 139 |
| `first60_reference_exact_not_raw_exact` | 261 |
| `first60_reference_exact_not_current_broad` | 80 |
| `possible_total_exact_after_reference` | 7150 |
| `possible_exact_gain_pct_of_current_exact` | 0.028777 |

## Trust Checks

| Metric | Value |
| --- | ---: |
| `stephen_original_rows_with_sequence` | 8279 |
| `original_pair_in_claimed_jmdict_sequence` | 7957 |
| `original_pair_not_in_claimed_jmdict_sequence` | 322 |
| `original_pair_sequence_match_rate` | 0.961106 |
| `yomitan_pairs_in_any_referenced_sequence` | 7420 |
| `yomitan_pairs_not_in_any_referenced_sequence` | 693 |
| `yomitan_pair_sequence_match_rate` | 0.914582 |

## Remaining Effective-Exact Gap Audit

- Rows: `200`
- First-60 rows: `139`

Category counts:

| Category | Count | First-60 Count |
| --- | ---: | ---: |
| `current_jlpt_surface_only_no_exact` | 19 | 18 |
| `external_pair_only` | 3 | 2 |
| `external_same_sequence_same_reading_only` | 11 | 6 |
| `guarded_current_same_reading_normalization` | 72 | 44 |
| `jmdict_kana_preferred_or_rare_written_form` | 37 | 24 |
| `jmdict_marked_kanji_form` | 5 | 4 |
| `jmdict_marked_or_rare_reading` | 14 | 11 |
| `jmdict_marked_usage` | 10 | 7 |
| `jmdict_search_only_written_form` | 29 | 23 |

Rows in guarded or marked-form categories are not automatic repairs; they are exactly the cases where effective exact matching should stay conservative unless a product policy intentionally accepts rare or kana-preferred written forms as learner anchors.


## Candidate Examples

### Remaining reference exact rows not covered by effective exact

| Surface | Reading | Core rank | Raw exact | Effective exact | Ref levels | Category | Risk | Seq source |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| 共 | とも | 192.0 | [] | no | [1] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1578040 共/とも |
| 此処 | ここ | 230.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1288810 此処/ここ |
| 良く | よく | 250.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1605870 良く/よく |
| 矢張り | やはり | 410.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 2772770 やはり/やはり |
| 其々 | それぞれ | 592.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1596690 それぞれ/それぞれ |
| 前 | ぜん | 704.0 | [] | no | [1] | `jmdict_marked_usage` | 0.0 | 1392570 前/ぜん |
| 此方 | こちら | 713.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1004500 こちら/こちら |
| 然も | しかも | 1074.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1506050 而も/しかも |
| 略 | ほぼ | 1111.0 | [] | no | [3] | `jmdict_search_only_written_form` | 0.0 | 1551940 略/ほぼ |
| 扠 | さて | 1478.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1585460 偖/さて |
| 御前 | おまえ | 1830.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1002290 おまえ/おまえ |
| 家 | うち | 1830.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 1457730 内/うち |

### Current broad-only rows with reference exact evidence

| Surface | Reading | Core rank | Raw exact | Effective exact | Ref levels | Category | Risk | Seq source |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| 共 | とも | 192.0 | [] | no | [1] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1578040 共/とも |
| 前 | ぜん | 704.0 | [] | no | [1] | `jmdict_marked_usage` | 0.0 | 1392570 前/ぜん |
| 然も | しかも | 1074.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1506050 而も/しかも |
| 家 | うち | 1830.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 1457730 内/うち |
| 施行 | しこう | 2781.0 | [] | no | [1] | `current_jlpt_surface_only_no_exact` | 0.0 |  |
| 真実 | しんじつ | 2961.0 | [] | no | [1] | `jmdict_marked_or_rare_reading` | 0.0 | 1363780 真実/しんじつ |
| 発足 | ほっそく | 3307.0 | [] | no | [1] | `jmdict_marked_or_rare_reading` | 0.0 |  |
| 依存 | いぞん | 3497.0 | [] | no | [1] | `current_jlpt_surface_only_no_exact` | 0.0 |  |
| 手数 | てすう | 3703.0 | [] | no | [1] | `current_jlpt_surface_only_no_exact` | 0.0 |  |
| 復旧 | ふっきゅう | 3830.0 | [] | no | [1] | `jmdict_marked_or_rare_reading` | 0.0 | 1500740 復旧/ふっきゅう |
| 統治 | とうち | 4257.0 | [] | no | [1] | `current_jlpt_surface_only_no_exact` | 0.0 |  |
| 掌 | てのひら | 4257.0 | [] | no | [1] | `current_jlpt_surface_only_no_exact` | 0.0 |  |

### Reference exact rows absent from current broad JLPT

| Surface | Reading | Core rank | Raw exact | Effective exact | Ref levels | Category | Risk | Seq source |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| 此処 | ここ | 230.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1288810 此処/ここ |
| 良く | よく | 250.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1605870 良く/よく |
| 矢張り | やはり | 410.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 2772770 やはり/やはり |
| 其々 | それぞれ | 592.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1596690 それぞれ/それぞれ |
| 此方 | こちら | 713.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1004500 こちら/こちら |
| 略 | ほぼ | 1111.0 | [] | no | [3] | `jmdict_search_only_written_form` | 0.0 | 1551940 略/ほぼ |
| 扠 | さて | 1478.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1585460 偖/さて |
| 御前 | おまえ | 1830.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1002290 おまえ/おまえ |
| 急度 | きっと | 1911.0 | [] | no | [1, 4] | `guarded_current_same_reading_normalization` | 0.0 | 1003430 屹度/きっと |
| 齎す | もたらす | 2100.0 | [] | no | [1] | `guarded_current_same_reading_normalization` | 0.0 | 1573190 齎らす/もたらす |
| 取り上げる | とりあげる | 2312.0 | [] | no | [3] | `jmdict_search_only_written_form` | 0.0 | 1326800 取り上げる/とりあげる |
| 漸と | やっと | 2356.0 | [] | no | [4] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1012800 やっと/やっと |

### First-60 rows where reference adds exact evidence

| Surface | Reading | Core rank | Raw exact | Effective exact | Ref levels | Category | Risk | Seq source |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| 共 | とも | 192.0 | [] | no | [1] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1578040 共/とも |
| 此処 | ここ | 230.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1288810 此処/ここ |
| 良く | よく | 250.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1605870 良く/よく |
| 矢張り | やはり | 410.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 2772770 やはり/やはり |
| 其々 | それぞれ | 592.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1596690 それぞれ/それぞれ |
| 前 | ぜん | 704.0 | [] | no | [1] | `jmdict_marked_usage` | 0.0 | 1392570 前/ぜん |
| 此方 | こちら | 713.0 | [] | no | [5] | `jmdict_kana_preferred_or_rare_written_form` | 0.0 | 1004500 こちら/こちら |
| 然も | しかも | 1074.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1506050 而も/しかも |
| 略 | ほぼ | 1111.0 | [] | no | [3] | `jmdict_search_only_written_form` | 0.0 | 1551940 略/ほぼ |
| 扠 | さて | 1478.0 | [] | no | [1, 3] | `guarded_current_same_reading_normalization` | 0.0 | 1585460 偖/さて |
| 御前 | おまえ | 1830.0 | [] | no | [3] | `guarded_current_same_reading_normalization` | 0.0 | 1002290 おまえ/おまえ |
| 家 | うち | 1830.0 | [] | no | [4] | `guarded_current_same_reading_normalization` | 0.0 | 1457730 内/うち |

## Focus Rows

| Surface | Reading | Matrix | Raw exact | Normalized exact | Guarded normalized | Effective exact | Reference exact | Surface-only? | Risk |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 明日 | あした | yes | [5] | no | no | yes | [5] | no | 0.0 |
| 明日 | あす | yes | [4] | no | no | yes | [4] | no | 0.0 |
| 辛い | つらい | yes | [3] | no | no | yes | [3] | no | 0.0 |
| 辛い | からい | yes | [5] | no | no | yes | [5] | no | 0.0 |
| 外国 | とつくに | yes | [] | no | no | no | [] | yes | 0.0 |
| 外国 | がいこく | yes | [5] | no | no | yes | [5] | no | 0.0 |
| 誘う | いざなう | yes | [] | no | no | no | [] | yes | 0.0 |
| 誘う | さそう | yes | [3] | no | no | yes | [3] | no | 0.0 |
| 真 | まこと | yes | [] | yes | no | yes | [1] | no | 0.0 |
| 真 | しん | yes | [] | no | no | no | [] | yes | 0.0 |
| 枝 | え | yes | [] | no | no | no | [] | yes | 0.0 |
| 僕 | やつがれ | yes | [] | no | no | no | [] | yes | 0.0 |
| 外 | げ | yes | [] | no | no | no | [] | yes | 0.0 |
| 海 | あま | yes | [] | no | no | no | [] | yes | 0.0 |

## Conclusion

Recommendation: `limited_mapping_repair_poc`

Reference evidence could add or repair 200 effective-exact matrix rows, including 82 current broad-only rows and 139 rows inside the first-60-by-core-rank slice.

This is primarily a coverage/mapping repair opportunity, not a new independent JLPT theory. It is most useful if the candidate examples show same-surface or normalized-spelling failures we actually want to fix.

If accepted, inspect the remaining reference-only rows as possible safe normalization candidates, then rebuild the component matrix and compare effective-exact gain.

## License / Use Note

This artifact uses the stephenmk source as a diagnostic reference. The earlier source audit recorded that repository as CC BY-SA 4.0 and Tanos-derived. Direct product ingestion should be handled as a separate licensing/product decision.
