# en-es Semantic Veto Full-Family Score Surface

- Status: `ok`
- Decision: `full_family_score_surface_established`
- Generated: `2026-05-07T19:47:46Z`
- Families: `49`
- Cases: `189`
- Review state: ``

## Methodology

This report summarizes the full-family packet by scorer and by measurable source/target features. It does not change runtime policy and it does not promote these rows as locked eval.

## Overall By Scorer

| scorer_id | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | 189 | 50.3% | 5.1% | 97.6% | 100.0% | 1.1% (1) | 94.9% (93) |
| sentence_transformer_cosine | 189 | 73.0% | 87.8% | 90.5% | 28.6% | 42.9% (39) | 12.2% (12) |

## Source Band

| scorer_id | source_zipf_band_en | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | 60 | 48.3% | 6.2% | 91.7% | 100.0% | 3.6% (1) | 93.8% (30) |
| tfidf_cosine | zipf_4_to_5_common | 42 | 50.0% | 4.5% | 100.0% | 100.0% | 0.0% (0) | 95.5% (21) |
| tfidf_cosine | zipf_3_to_4_mid | 57 | 54.4% | 7.1% | 100.0% | 100.0% | 0.0% (0) | 92.9% (26) |
| tfidf_cosine | zipf_below_3_rare | 30 | 46.7% | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (16) |
| sentence_transformer_cosine | zipf_5_plus_very_common | 60 | 68.3% | 90.6% | 83.3% | 12.5% | 57.1% (16) | 9.4% (3) |
| sentence_transformer_cosine | zipf_4_to_5_common | 42 | 78.6% | 90.9% | 88.9% | 45.5% | 35.0% (7) | 9.1% (2) |
| sentence_transformer_cosine | zipf_3_to_4_mid | 57 | 73.7% | 89.3% | 93.3% | 21.4% | 41.4% (12) | 10.7% (3) |
| sentence_transformer_cosine | zipf_below_3_rare | 30 | 73.3% | 75.0% | 100.0% | 50.0% | 28.6% (4) | 25.0% (4) |

## Case Type

| scorer_id | manual_case_type | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | positive_active | 98 | 5.1% | 5.1% | n/a | n/a | n/a (0) | 94.9% (93) |
| tfidf_cosine | shadow_negative | 42 | 97.6% | n/a | 97.6% | n/a | 2.4% (1) | n/a (0) |
| tfidf_cosine | phrase_no_winner | 49 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | positive_active | 98 | 87.8% | 87.8% | n/a | n/a | n/a (0) | 12.2% (12) |
| sentence_transformer_cosine | shadow_negative | 42 | 90.5% | n/a | 90.5% | n/a | 9.5% (4) | n/a (0) |
| sentence_transformer_cosine | phrase_no_winner | 49 | 28.6% | n/a | n/a | 28.6% | 71.4% (35) | n/a (0) |

## Source Band By Case Type

| scorer_id | source_zipf_band_en | manual_case_type | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | positive_active | 32 | 6.2% | 6.2% | n/a | n/a | n/a (0) | 93.8% (30) |
| tfidf_cosine | zipf_5_plus_very_common | shadow_negative | 12 | 91.7% | n/a | 91.7% | n/a | 8.3% (1) | n/a (0) |
| tfidf_cosine | zipf_5_plus_very_common | phrase_no_winner | 16 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | positive_active | 22 | 4.5% | 4.5% | n/a | n/a | n/a (0) | 95.5% (21) |
| tfidf_cosine | zipf_4_to_5_common | shadow_negative | 9 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | phrase_no_winner | 11 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | positive_active | 28 | 7.1% | 7.1% | n/a | n/a | n/a (0) | 92.9% (26) |
| tfidf_cosine | zipf_3_to_4_mid | shadow_negative | 15 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | phrase_no_winner | 14 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | positive_active | 16 | 0.0% | 0.0% | n/a | n/a | n/a (0) | 100.0% (16) |
| tfidf_cosine | zipf_below_3_rare | shadow_negative | 6 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | phrase_no_winner | 8 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | positive_active | 32 | 90.6% | 90.6% | n/a | n/a | n/a (0) | 9.4% (3) |
| sentence_transformer_cosine | zipf_5_plus_very_common | shadow_negative | 12 | 83.3% | n/a | 83.3% | n/a | 16.7% (2) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | phrase_no_winner | 16 | 12.5% | n/a | n/a | 12.5% | 87.5% (14) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | positive_active | 22 | 90.9% | 90.9% | n/a | n/a | n/a (0) | 9.1% (2) |
| sentence_transformer_cosine | zipf_4_to_5_common | shadow_negative | 9 | 88.9% | n/a | 88.9% | n/a | 11.1% (1) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | phrase_no_winner | 11 | 45.5% | n/a | n/a | 45.5% | 54.5% (6) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | positive_active | 28 | 89.3% | 89.3% | n/a | n/a | n/a (0) | 10.7% (3) |
| sentence_transformer_cosine | zipf_3_to_4_mid | shadow_negative | 15 | 93.3% | n/a | 93.3% | n/a | 6.7% (1) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | phrase_no_winner | 14 | 21.4% | n/a | n/a | 21.4% | 78.6% (11) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | positive_active | 16 | 75.0% | 75.0% | n/a | n/a | n/a (0) | 25.0% (4) |
| sentence_transformer_cosine | zipf_below_3_rare | shadow_negative | 6 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | phrase_no_winner | 8 | 50.0% | n/a | n/a | 50.0% | 50.0% (4) | n/a (0) |

## Target Band

| scorer_id | target_zipf_band_es | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | 31 | 35.5% | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (20) |
| tfidf_cosine | zipf_4_to_5_common | 71 | 53.5% | 11.1% | 94.1% | 100.0% | 2.9% (1) | 88.9% (32) |
| tfidf_cosine | zipf_3_to_4_mid | 75 | 53.3% | 2.8% | 100.0% | 100.0% | 0.0% (0) | 97.2% (35) |
| tfidf_cosine | zipf_below_3_rare | 12 | 50.0% | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (6) |
| sentence_transformer_cosine | zipf_5_plus_very_common | 31 | 71.0% | 100.0% | 100.0% | 10.0% | 81.8% (9) | 0.0% (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | 71 | 66.2% | 80.6% | 88.2% | 16.7% | 48.6% (17) | 19.4% (7) |
| sentence_transformer_cosine | zipf_3_to_4_mid | 75 | 80.0% | 91.7% | 90.5% | 44.4% | 30.8% (12) | 8.3% (3) |
| sentence_transformer_cosine | zipf_below_3_rare | 12 | 75.0% | 66.7% | 100.0% | 66.7% | 16.7% (1) | 33.3% (2) |

## Polysemy

| scorer_id | polysemy_band | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | high_10_plus | 36 | 58.3% | 12.5% | 91.7% | 100.0% | 5.0% (1) | 87.5% (14) |
| tfidf_cosine | low_1_to_3 | 78 | 42.3% | 2.2% | 100.0% | 100.0% | 0.0% (0) | 97.8% (45) |
| tfidf_cosine | medium_4_to_9 | 55 | 58.2% | 4.2% | 100.0% | 100.0% | 0.0% (0) | 95.8% (23) |
| tfidf_cosine | missing | 20 | 45.0% | 8.3% | 100.0% | 100.0% | 0.0% (0) | 91.7% (11) |
| sentence_transformer_cosine | high_10_plus | 36 | 75.0% | 93.8% | 83.3% | 25.0% | 40.0% (8) | 6.2% (1) |
| sentence_transformer_cosine | low_1_to_3 | 78 | 70.5% | 89.1% | 100.0% | 21.7% | 56.2% (18) | 10.9% (5) |
| sentence_transformer_cosine | medium_4_to_9 | 55 | 74.5% | 75.0% | 89.5% | 50.0% | 25.8% (8) | 25.0% (6) |
| sentence_transformer_cosine | missing | 20 | 75.0% | 100.0% | 100.0% | 16.7% | 62.5% (5) | 0.0% (0) |

## POS Shape

| scorer_id | pos_shape | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | cross_pos_polysemy | 87 | 56.3% | 7.5% | 96.3% | 100.0% | 2.1% (1) | 92.5% (37) |
| tfidf_cosine | missing | 20 | 45.0% | 8.3% | 100.0% | 100.0% | 0.0% (0) | 91.7% (11) |
| tfidf_cosine | same_pos_polysemy | 58 | 48.3% | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (30) |
| tfidf_cosine | single_sense | 24 | 37.5% | 6.2% | n/a | 100.0% | 0.0% (0) | 93.8% (15) |
| sentence_transformer_cosine | cross_pos_polysemy | 87 | 74.7% | 77.5% | 96.3% | 40.0% | 27.7% (13) | 22.5% (9) |
| sentence_transformer_cosine | missing | 20 | 75.0% | 100.0% | 100.0% | 16.7% | 62.5% (5) | 0.0% (0) |
| sentence_transformer_cosine | same_pos_polysemy | 58 | 72.4% | 90.0% | 76.9% | 33.3% | 46.4% (13) | 10.0% (3) |
| sentence_transformer_cosine | single_sense | 24 | 66.7% | 100.0% | n/a | 0.0% | 100.0% (8) | 0.0% (0) |

## Prior Reference

| scope | cases | scorer | phrase mode | rescue mode | decision | positive recall | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage1_representative_reference | 120 | tfidf_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 66.7% | 24.5% | 0.0% (0) | 75.5% (40) |

`stage1_representative_reference` is orientation only; it uses a different dataset mix and current-policy phrase/rescue settings.

## Failure Concentration

| scorer | dimension | value | cases | errors | error rate | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | shadow_contract | missing | 189 | 94 | 49.7% | 1 | 93 |
| tfidf_cosine | manual_case_type | positive_active | 98 | 93 | 94.9% | 0 | 93 |
| sentence_transformer_cosine | shadow_contract | missing | 189 | 51 | 27.0% | 39 | 12 |
| tfidf_cosine | polysemy_band | low_1_to_3 | 78 | 45 | 57.7% | 0 | 45 |
| tfidf_cosine | pos_shape | cross_pos_polysemy | 87 | 38 | 43.7% | 1 | 37 |
| sentence_transformer_cosine | manual_case_type | phrase_no_winner | 49 | 35 | 71.4% | 35 | 0 |
| tfidf_cosine | target_zipf_band_es | zipf_3_to_4_mid | 75 | 35 | 46.7% | 0 | 35 |
| tfidf_cosine | target_zipf_band_es | zipf_4_to_5_common | 71 | 33 | 46.5% | 1 | 32 |
| tfidf_cosine | source_zipf_band_en | zipf_5_plus_very_common | 60 | 31 | 51.7% | 1 | 30 |
| tfidf_cosine | pos_shape | same_pos_polysemy | 58 | 30 | 51.7% | 0 | 30 |
| tfidf_cosine | source_zipf_band_en | zipf_3_to_4_mid | 57 | 26 | 45.6% | 0 | 26 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_4_to_5_common | 71 | 24 | 33.8% | 17 | 7 |
| tfidf_cosine | polysemy_band | medium_4_to_9 | 55 | 23 | 41.8% | 0 | 23 |
| sentence_transformer_cosine | polysemy_band | low_1_to_3 | 78 | 23 | 29.5% | 18 | 5 |
| sentence_transformer_cosine | pos_shape | cross_pos_polysemy | 87 | 22 | 25.3% | 13 | 9 |
| tfidf_cosine | source_zipf_band_en | zipf_4_to_5_common | 42 | 21 | 50.0% | 0 | 21 |
| tfidf_cosine | target_zipf_band_es | zipf_5_plus_very_common | 31 | 20 | 64.5% | 0 | 20 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_5_plus_very_common | 60 | 19 | 31.7% | 16 | 3 |
| tfidf_cosine | source_zipf_band_en | zipf_below_3_rare | 30 | 16 | 53.3% | 0 | 16 |
| sentence_transformer_cosine | pos_shape | same_pos_polysemy | 58 | 16 | 27.6% | 13 | 3 |
| tfidf_cosine | pos_shape | single_sense | 24 | 15 | 62.5% | 0 | 15 |
| tfidf_cosine | polysemy_band | high_10_plus | 36 | 15 | 41.7% | 1 | 14 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_3_to_4_mid | 57 | 15 | 26.3% | 12 | 3 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_3_to_4_mid | 75 | 15 | 20.0% | 12 | 3 |
| sentence_transformer_cosine | polysemy_band | medium_4_to_9 | 55 | 14 | 25.5% | 8 | 6 |
| sentence_transformer_cosine | manual_case_type | positive_active | 98 | 12 | 12.2% | 0 | 12 |
| tfidf_cosine | polysemy_band | missing | 20 | 11 | 55.0% | 0 | 11 |
| tfidf_cosine | pos_shape | missing | 20 | 11 | 55.0% | 0 | 11 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_5_plus_very_common | 31 | 9 | 29.0% | 9 | 0 |
| sentence_transformer_cosine | polysemy_band | high_10_plus | 36 | 9 | 25.0% | 8 | 1 |

## Limitations

- `approved_rows_are_still_not_final_locked_eval`
- `tfidf_score_can_be_optimistic_under_template_and_definition_overlap`
- `sentence_transformer_phrase_no_winner_failures_are_diagnostic_until_locked_eval`
- `source_band_curves_are_directional_not_causal_on_this_packet`
- `runtime_policy_remains_unchanged`

## Next Steps

- Review the high-failure source-band and case-type cells before interpreting the curve.
- Rerun formula and boundary sweeps on this approved repaired denominator.
- Use the resulting ranking only for LLM evidence allocation until locked-eval confirms it.
