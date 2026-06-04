# en-es Semantic Veto Heuristic Difficulty Surface

- Status: `ok`
- Decision: `heuristic_difficulty_surface_established`
- Generated: `2026-05-05T03:00:51Z`
- Score rows: `242`
- Authored triggers: `29`
- Primary rows / sentinel rows: `192` / `50`
- Overall difficulty: `26.5%`
- Primary-only difficulty: `29.2%`

## Methodology

This report treats the current frequency/polysemy heuristic as a control, not as the final formula. It compares source-word features, case shape, score-surface features, and observed product outcomes while keeping the outcome-informed sentinel group out of primary heuristic validation.

## Scorer Summary

| Scope | Cases | Pos allow | Neg abstain | Pos diff | Shadow diff | Phrase diff | Overall diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sentence_transformer_cosine` | 121 | 89.7% | 66.7% | 10.3% | 5.9% | 65.5% | 22.3% |
| `tfidf_cosine` | 121 | 39.7% | 96.8% | 60.3% | 0.0% | 6.9% | 30.6% |

## Case-Type Difficulty

| Scope | Cases | Pos allow | Neg abstain | Pos diff | Shadow diff | Phrase diff | Overall diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sentence_transformer_cosine::phrase_no_winner` | 29 | n/a | 34.5% | n/a | n/a | 65.5% | 65.5% |
| `sentence_transformer_cosine::positive_active` | 58 | 89.7% | n/a | 10.3% | n/a | n/a | 10.3% |
| `sentence_transformer_cosine::shadow_negative` | 34 | n/a | 94.1% | n/a | 5.9% | n/a | 5.9% |
| `tfidf_cosine::phrase_no_winner` | 29 | n/a | 93.1% | n/a | n/a | 6.9% | 6.9% |
| `tfidf_cosine::positive_active` | 58 | 39.7% | n/a | 60.3% | n/a | n/a | 60.3% |
| `tfidf_cosine::shadow_negative` | 34 | n/a | 100.0% | n/a | 0.0% | n/a | 0.0% |

## Primary Heuristic Groups

| Scope | Cases | Pos allow | Neg abstain | Pos diff | Shadow diff | Phrase diff | Overall diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sentence_transformer_cosine::core_high_polysemy` | 20 | 75.0% | 83.3% | 25.0% | 12.5% | 25.0% | 20.0% |
| `sentence_transformer_cosine::core_low_polysemy_control` | 12 | 100.0% | 0.0% | 0.0% | n/a | 100.0% | 33.3% |
| `sentence_transformer_cosine::mid_high_polysemy` | 20 | 100.0% | 66.7% | 0.0% | 0.0% | 100.0% | 20.0% |
| `sentence_transformer_cosine::mid_low_polysemy_control` | 12 | 100.0% | 0.0% | 0.0% | n/a | 100.0% | 33.3% |
| `sentence_transformer_cosine::tail_high_polysemy` | 20 | 62.5% | 83.3% | 37.5% | 12.5% | 25.0% | 25.0% |
| `sentence_transformer_cosine::tail_low_polysemy_control` | 12 | 100.0% | 0.0% | 0.0% | n/a | 100.0% | 33.3% |
| `tfidf_cosine::core_high_polysemy` | 20 | 25.0% | 100.0% | 75.0% | 0.0% | 0.0% | 30.0% |
| `tfidf_cosine::core_low_polysemy_control` | 12 | 25.0% | 100.0% | 75.0% | n/a | 0.0% | 50.0% |
| `tfidf_cosine::mid_high_polysemy` | 20 | 25.0% | 83.3% | 75.0% | 0.0% | 50.0% | 40.0% |
| `tfidf_cosine::mid_low_polysemy_control` | 12 | 37.5% | 100.0% | 62.5% | n/a | 0.0% | 41.7% |
| `tfidf_cosine::tail_high_polysemy` | 20 | 50.0% | 100.0% | 50.0% | 0.0% | 0.0% | 20.0% |
| `tfidf_cosine::tail_low_polysemy_control` | 12 | 75.0% | 100.0% | 25.0% | n/a | 0.0% | 16.7% |

## Formula Bakeoff

| Formula | Scorer | Compared | Excluded sentinel | Excluded missing rank | Spearman r | Top predicted triggers |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `baseline_frequency_polysemy` | `sentence_transformer_cosine` | 24 | 5 | 0 | -0.5368 | call:20.0%, work:20.0%, deep:20.0%, man:40.0% |
| `evidence_margin` | `sentence_transformer_cosine` | 24 | 5 | 0 | -0.4711 | work:20.0%, call:20.0%, trade:20.0%, particular:20.0% |
| `richer_case_shape` | `sentence_transformer_cosine` | 24 | 5 | 0 | -0.5246 | call:20.0%, work:20.0%, deep:20.0%, man:40.0% |
| `baseline_frequency_polysemy` | `tfidf_cosine` | 24 | 5 | 0 | 0.3781 | call:40.0%, work:40.0%, deep:40.0%, help:20.0% |
| `evidence_margin` | `tfidf_cosine` | 24 | 5 | 0 | 0.4695 | work:40.0%, green:40.0%, trade:40.0%, man:20.0% |
| `richer_case_shape` | `tfidf_cosine` | 24 | 5 | 0 | 0.2655 | call:40.0%, work:40.0%, deep:40.0%, man:20.0% |

## Failure Concentration

| Dimension | Value | Scorer | Cases | Failures | Failure rate | Failure share | Pos abstain | Neg allow |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `manual_case_type` | `positive_active` | `tfidf_cosine` | 58 | 35 | 60.3% | 94.6% | 35 | 0 |
| `selection_mode` | `pre_outcome` | `tfidf_cosine` | 96 | 31 | 32.3% | 83.8% | 29 | 2 |
| `selection_mode` | `pre_outcome` | `sentence_transformer_cosine` | 96 | 25 | 26.0% | 92.6% | 5 | 20 |
| `shadow_contract` | `full` | `tfidf_cosine` | 80 | 23 | 28.7% | 62.2% | 21 | 2 |
| `polysemy_band` | `high_10_plus` | `tfidf_cosine` | 80 | 22 | 27.5% | 59.5% | 20 | 2 |
| `score_margin_bin` | `near_tie_abs_lt_0.02` | `tfidf_cosine` | 52 | 21 | 40.4% | 56.8% | 21 | 0 |
| `manual_case_type` | `phrase_no_winner` | `sentence_transformer_cosine` | 29 | 19 | 65.5% | 70.4% | 0 | 19 |
| `shadow_contract` | `full` | `sentence_transformer_cosine` | 80 | 15 | 18.8% | 55.6% | 6 | 9 |
| `score_margin_bin` | `active_leads_0.02_to_0.05` | `tfidf_cosine` | 20 | 14 | 70.0% | 37.8% | 13 | 1 |
| `polysemy_band` | `high_10_plus` | `sentence_transformer_cosine` | 80 | 14 | 17.5% | 51.8% | 6 | 8 |
| `source_rank_bin` | `1001-2000` | `tfidf_cosine` | 32 | 13 | 40.6% | 35.1% | 11 | 2 |
| `polysemy_band` | `low_1_to_3` | `tfidf_cosine` | 36 | 13 | 36.1% | 35.1% | 13 | 0 |
| `shadow_contract` | `not_applicable` | `tfidf_cosine` | 36 | 13 | 36.1% | 35.1% | 13 | 0 |
| `source_rank_bin` | `1-500` | `tfidf_cosine` | 32 | 12 | 37.5% | 32.4% | 12 | 0 |
| `polysemy_band` | `low_1_to_3` | `sentence_transformer_cosine` | 36 | 12 | 33.3% | 44.4% | 0 | 12 |
| `shadow_contract` | `not_applicable` | `sentence_transformer_cosine` | 36 | 12 | 33.3% | 44.4% | 0 | 12 |

## Expansion Planner

| Priority | Cell | Reason | Action | Manual | LLM discovery | Locked eval |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `P0` | `core_low_polysemy_control:phrase_no_winner:not_applicable` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P0` | `mid_high_polysemy:phrase_no_winner:full` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P0` | `mid_low_polysemy_control:phrase_no_winner:not_applicable` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P0` | `tail_low_polysemy_control:phrase_no_winner:not_applicable` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P1` | `core_high_polysemy:phrase_no_winner:full` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P1` | `core_high_polysemy:phrase_no_winner:limited` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P1` | `core_high_polysemy:shadow_negative:full` | `shadow_negative_needs_more_competition_coverage` | add_shadow_negative_rows_and_review_shadow_evidence | 4 | 8 | 4 |
| `P1` | `core_high_polysemy:shadow_negative:limited` | `shadow_negative_needs_more_competition_coverage` | add_shadow_negative_rows_and_review_shadow_evidence | 4 | 8 | 4 |
| `P1` | `core_low_polysemy_phrase:money` | `high_frequency_low_polysemy_control_needs_phrase_and_mention_negatives` | add_phrase_no_winner_rows_not_fake_shadow_rows | 4 | 12 | 6 |
| `P1` | `core_low_polysemy_phrase:often` | `high_frequency_low_polysemy_control_needs_phrase_and_mention_negatives` | add_phrase_no_winner_rows_not_fake_shadow_rows | 4 | 12 | 6 |
| `P1` | `core_low_polysemy_phrase:percent` | `high_frequency_low_polysemy_control_needs_phrase_and_mention_negatives` | add_phrase_no_winner_rows_not_fake_shadow_rows | 4 | 12 | 6 |
| `P1` | `core_low_polysemy_phrase:yes` | `high_frequency_low_polysemy_control_needs_phrase_and_mention_negatives` | add_phrase_no_winner_rows_not_fake_shadow_rows | 4 | 12 | 6 |
| `P1` | `measured_missing_rank_high_failure_sentinel:phrase_no_winner:full` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P1` | `tail_high_polysemy:phrase_no_winner:full` | `phrase_no_winner_underfilled_or_leaking` | expand_phrase_no_winner_discovery_then_locked_eval | 4 | 12 | 6 |
| `P2` | `core_high_polysemy:positive_active:full` | `positive_active_false_abstain_cluster` | review_active_evidence_before_row_expansion | 2 | 6 | 3 |
| `P2` | `sentinel_metadata:check` | `outcome_informed_sentinel_excluded_from_primary_validation` | improve_frequency_metadata_or_keep_as_regression_anchor | 0 | 0 | 0 |
| `P2` | `sentinel_metadata:order` | `outcome_informed_sentinel_excluded_from_primary_validation` | improve_frequency_metadata_or_keep_as_regression_anchor | 0 | 0 | 0 |
| `P2` | `sentinel_metadata:plant` | `outcome_informed_sentinel_excluded_from_primary_validation` | improve_frequency_metadata_or_keep_as_regression_anchor | 0 | 0 | 0 |
| `P2` | `sentinel_metadata:play` | `outcome_informed_sentinel_excluded_from_primary_validation` | improve_frequency_metadata_or_keep_as_regression_anchor | 0 | 0 | 0 |
| `P2` | `sentinel_metadata:report` | `outcome_informed_sentinel_excluded_from_primary_validation` | improve_frequency_metadata_or_keep_as_regression_anchor | 0 | 0 | 0 |

## Limitations

- `agent_authored_cases_need_human_review_before_promotion_claims`
- `formula_bakeoff_is_correlation_not_causal_proof`
- `sentence_transformer_phrase_score_lead_is_unavailable_in_current_sentence_veto_rows`
- `sentinel_rows_are_outcome_informed_and_excluded_from_primary_heuristic_validation`
- `runtime_policy_remains_unchanged`

## Next Steps

- Review formula bakeoff rows to decide which feature family predicts each failure class.
- Expand phrase/no-winner cells before spending broad LLM budget.
- Keep low-polysemy controls positive-plus-phrase unless a real alternate sense is found.
- Human-review draft target/shadow choices before using this lane as locked evaluation.
