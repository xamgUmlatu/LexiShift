# en-ja SRS Admission Veto Review Label Audit

Source pack: `docs/test_outputs/srs_admission_veto_candidate_review_en_ja_latest.json`
Labels: `docs/test_inputs/srs_admission_veto_review_labels_en_ja.json`

## Summary

| Metric | Value |
| --- | ---: |
| Labels | 132 |
| Updated labels this pass | 3 |
| User-review rows | 0 |

Decision counts: `false_positive`=22, `partial_positive`=16, `true_positive`=94

Action counts: `add_or_keep_restricted_admission`=68, `display_only_or_kana_preferred`=4, `keep_current_restriction`=24, `no_action`=22, `raise_score_or_floor`=14

Updated labels: `直/あたい`, `気/け`, `徒/あだ`

## By Source Category

| Source Category | Rows | Productive | Rate | Needs User | Decisions | Actions |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `active_hard_veto` | 24 | 24 | 1.00 | 0 | true_positive:24 | keep_current_restriction:24 |
| `kana_preferred_kanji_display` | 24 | 22 | 0.92 | 0 | false_positive:2, partial_positive:5, true_positive:17 | add_or_keep_restricted_admission:16, no_action:2, raise_score_or_floor:6 |
| `low_support_early_rows` | 10 | 9 | 0.90 | 0 | false_positive:1, true_positive:9 | add_or_keep_restricted_admission:9, no_action:1 |
| `manual_watchlist` | 2 | 1 | 0.50 | 0 | false_positive:1, true_positive:1 | display_only_or_kana_preferred:1, no_action:1 |
| `same_surface_rare_reading` | 24 | 22 | 0.92 | 0 | false_positive:2, partial_positive:2, true_positive:20 | add_or_keep_restricted_admission:20, no_action:2, raise_score_or_floor:2 |
| `single_kanji_component_like` | 24 | 22 | 0.92 | 0 | false_positive:2, partial_positive:2, true_positive:20 | add_or_keep_restricted_admission:20, no_action:2, raise_score_or_floor:2 |
| `unhandled_review_flags` | 24 | 10 | 0.42 | 0 | false_positive:14, partial_positive:7, true_positive:3 | add_or_keep_restricted_admission:3, display_only_or_kana_preferred:3, no_action:14, raise_score_or_floor:4 |

## By Band

| Analysis Band | Rows | Productive | Rate | Needs User | Decisions | Actions |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `0.00-0.20` | 10 | 1 | 0.10 | 0 | false_positive:9, partial_positive:1 | no_action:9, raise_score_or_floor:1 |
| `0.20-0.40` | 34 | 27 | 0.79 | 0 | false_positive:7, partial_positive:6, true_positive:21 | add_or_keep_restricted_admission:12, display_only_or_kana_preferred:3, keep_current_restriction:9, no_action:7, raise_score_or_floor:3 |
| `0.40-0.60` | 85 | 79 | 0.93 | 0 | false_positive:6, partial_positive:9, true_positive:70 | add_or_keep_restricted_admission:56, display_only_or_kana_preferred:1, keep_current_restriction:12, no_action:6, raise_score_or_floor:10 |
| `0.60-0.80` | 3 | 3 | 1.00 | 0 | true_positive:3 | keep_current_restriction:3 |

## By Candidate Shape

| Candidate Shape | Rows | Productive | Rate | Needs User | Decisions | Actions |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `hiragana` | 7 | 7 | 1.00 | 0 | true_positive:7 | add_or_keep_restricted_admission:7 |
| `kanji_compound_or_phrase` | 32 | 23 | 0.72 | 0 | false_positive:9, partial_positive:5, true_positive:18 | add_or_keep_restricted_admission:15, keep_current_restriction:2, no_action:9, raise_score_or_floor:6 |
| `single_kanji` | 93 | 80 | 0.86 | 0 | false_positive:13, partial_positive:11, true_positive:69 | add_or_keep_restricted_admission:46, display_only_or_kana_preferred:4, keep_current_restriction:22, no_action:13, raise_score_or_floor:8 |

## By Visibility Match Mode

| Visibility Match Mode | Rows | Productive | Rate | Needs User | Decisions | Actions |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `lemma_any_reading` | 11 | 11 | 1.00 | 0 | partial_positive:2, true_positive:9 | add_or_keep_restricted_admission:3, keep_current_restriction:5, raise_score_or_floor:3 |
| `not_observed` | 121 | 99 | 0.82 | 0 | false_positive:22, partial_positive:14, true_positive:85 | add_or_keep_restricted_admission:65, display_only_or_kana_preferred:4, keep_current_restriction:19, no_action:22, raise_score_or_floor:11 |

## User Review Needed

_No rows._
