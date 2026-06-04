# en-es Semantic Veto Full-Family Score Surface

- Status: `ok`
- Decision: `full_family_score_surface_established`
- Generated: `2026-05-06T20:20:35Z`
- Families: `58`
- Cases: `206`
- Review state: `agent_draft_human_review_pending`

## Methodology

This report summarizes the frozen full-family draft manual packet by scorer and by measurable source/target features. It does not change runtime policy and it does not promote the draft rows as locked eval.

## Overall By Scorer

| scorer_id | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | 206 | 80.6% | 45.2% | 100.0% | 100.0% | 0.0% (0) | 54.8% (40) |
| sentence_transformer_cosine | 206 | 72.8% | 83.6% | 94.7% | 31.0% | 33.1% (44) | 16.4% (12) |

## Source Band

| scorer_id | source_zipf_band_en | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | 59 | 76.3% | 33.3% | 100.0% | 100.0% | 0.0% (0) | 66.7% (14) |
| tfidf_cosine | zipf_4_to_5_common | 59 | 76.3% | 33.3% | 100.0% | 100.0% | 0.0% (0) | 66.7% (14) |
| tfidf_cosine | zipf_3_to_4_mid | 50 | 78.0% | 38.9% | 100.0% | 100.0% | 0.0% (0) | 61.1% (11) |
| tfidf_cosine | zipf_below_3_rare | 32 | 96.9% | 90.0% | 100.0% | 100.0% | 0.0% (0) | 10.0% (1) |
| tfidf_cosine | missing | 6 | 100.0% | 100.0% | n/a | 100.0% | 0.0% (0) | 0.0% (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | 59 | 74.6% | 81.0% | 95.5% | 37.5% | 28.9% (11) | 19.0% (4) |
| sentence_transformer_cosine | zipf_4_to_5_common | 59 | 71.2% | 81.0% | 87.0% | 33.3% | 34.2% (13) | 19.0% (4) |
| sentence_transformer_cosine | zipf_3_to_4_mid | 50 | 76.0% | 83.3% | 100.0% | 35.7% | 28.1% (9) | 16.7% (3) |
| sentence_transformer_cosine | zipf_below_3_rare | 32 | 71.9% | 90.0% | 100.0% | 20.0% | 36.4% (8) | 10.0% (1) |
| sentence_transformer_cosine | missing | 6 | 50.0% | 100.0% | n/a | 0.0% | 100.0% (3) | 0.0% (0) |

## Case Type

| scorer_id | manual_case_type | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | positive_active | 73 | 45.2% | 45.2% | n/a | n/a | n/a (0) | 54.8% (40) |
| tfidf_cosine | shadow_negative | 75 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | phrase_no_winner | 58 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | positive_active | 73 | 83.6% | 83.6% | n/a | n/a | n/a (0) | 16.4% (12) |
| sentence_transformer_cosine | shadow_negative | 75 | 94.7% | n/a | 94.7% | n/a | 5.3% (4) | n/a (0) |
| sentence_transformer_cosine | phrase_no_winner | 58 | 31.0% | n/a | n/a | 31.0% | 69.0% (40) | n/a (0) |

## Source Band By Case Type

| scorer_id | source_zipf_band_en | manual_case_type | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | positive_active | 21 | 33.3% | 33.3% | n/a | n/a | n/a (0) | 66.7% (14) |
| tfidf_cosine | zipf_5_plus_very_common | shadow_negative | 22 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_5_plus_very_common | phrase_no_winner | 16 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | positive_active | 21 | 33.3% | 33.3% | n/a | n/a | n/a (0) | 66.7% (14) |
| tfidf_cosine | zipf_4_to_5_common | shadow_negative | 23 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | phrase_no_winner | 15 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | positive_active | 18 | 38.9% | 38.9% | n/a | n/a | n/a (0) | 61.1% (11) |
| tfidf_cosine | zipf_3_to_4_mid | shadow_negative | 18 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | phrase_no_winner | 14 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | positive_active | 10 | 90.0% | 90.0% | n/a | n/a | n/a (0) | 10.0% (1) |
| tfidf_cosine | zipf_below_3_rare | shadow_negative | 12 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | phrase_no_winner | 10 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | missing | positive_active | 3 | 100.0% | 100.0% | n/a | n/a | n/a (0) | 0.0% (0) |
| tfidf_cosine | missing | phrase_no_winner | 3 | 100.0% | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | positive_active | 21 | 81.0% | 81.0% | n/a | n/a | n/a (0) | 19.0% (4) |
| sentence_transformer_cosine | zipf_5_plus_very_common | shadow_negative | 22 | 95.5% | n/a | 95.5% | n/a | 4.5% (1) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | phrase_no_winner | 16 | 37.5% | n/a | n/a | 37.5% | 62.5% (10) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | positive_active | 21 | 81.0% | 81.0% | n/a | n/a | n/a (0) | 19.0% (4) |
| sentence_transformer_cosine | zipf_4_to_5_common | shadow_negative | 23 | 87.0% | n/a | 87.0% | n/a | 13.0% (3) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | phrase_no_winner | 15 | 33.3% | n/a | n/a | 33.3% | 66.7% (10) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | positive_active | 18 | 83.3% | 83.3% | n/a | n/a | n/a (0) | 16.7% (3) |
| sentence_transformer_cosine | zipf_3_to_4_mid | shadow_negative | 18 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | phrase_no_winner | 14 | 35.7% | n/a | n/a | 35.7% | 64.3% (9) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | positive_active | 10 | 90.0% | 90.0% | n/a | n/a | n/a (0) | 10.0% (1) |
| sentence_transformer_cosine | zipf_below_3_rare | shadow_negative | 12 | 100.0% | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | phrase_no_winner | 10 | 20.0% | n/a | n/a | 20.0% | 80.0% (8) | n/a (0) |
| sentence_transformer_cosine | missing | positive_active | 3 | 100.0% | 100.0% | n/a | n/a | n/a (0) | 0.0% (0) |
| sentence_transformer_cosine | missing | phrase_no_winner | 3 | 0.0% | n/a | n/a | 0.0% | 100.0% (3) | n/a (0) |

## Target Band

| scorer_id | target_zipf_band_es | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | 38 | 81.6% | 50.0% | 100.0% | 100.0% | 0.0% (0) | 50.0% (7) |
| tfidf_cosine | zipf_4_to_5_common | 72 | 73.6% | 29.6% | 100.0% | 100.0% | 0.0% (0) | 70.4% (19) |
| tfidf_cosine | zipf_3_to_4_mid | 82 | 85.4% | 57.1% | 100.0% | 100.0% | 0.0% (0) | 42.9% (12) |
| tfidf_cosine | zipf_below_3_rare | 14 | 85.7% | 50.0% | 100.0% | 100.0% | 0.0% (0) | 50.0% (2) |
| sentence_transformer_cosine | zipf_5_plus_very_common | 38 | 68.4% | 92.9% | 91.7% | 16.7% | 45.8% (11) | 7.1% (1) |
| sentence_transformer_cosine | zipf_4_to_5_common | 72 | 79.2% | 81.5% | 96.2% | 52.6% | 22.2% (10) | 18.5% (5) |
| sentence_transformer_cosine | zipf_3_to_4_mid | 82 | 68.3% | 82.1% | 93.5% | 17.4% | 38.9% (21) | 17.9% (5) |
| sentence_transformer_cosine | zipf_below_3_rare | 14 | 78.6% | 75.0% | 100.0% | 50.0% | 20.0% (2) | 25.0% (1) |

## Polysemy

| scorer_id | polysemy_band | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | high_10_plus | 45 | 71.1% | 13.3% | 100.0% | 100.0% | 0.0% (0) | 86.7% (13) |
| tfidf_cosine | low_1_to_3 | 80 | 85.0% | 57.1% | 100.0% | 100.0% | 0.0% (0) | 42.9% (12) |
| tfidf_cosine | medium_4_to_9 | 63 | 76.2% | 28.6% | 100.0% | 100.0% | 0.0% (0) | 71.4% (15) |
| tfidf_cosine | missing | 18 | 100.0% | 100.0% | n/a | 100.0% | 0.0% (0) | 0.0% (0) |
| sentence_transformer_cosine | high_10_plus | 45 | 73.3% | 53.3% | 100.0% | 50.0% | 16.7% (5) | 46.7% (7) |
| sentence_transformer_cosine | low_1_to_3 | 80 | 72.5% | 89.3% | 96.3% | 28.0% | 36.5% (19) | 10.7% (3) |
| sentence_transformer_cosine | medium_4_to_9 | 63 | 79.4% | 90.5% | 89.3% | 42.9% | 26.2% (11) | 9.5% (2) |
| sentence_transformer_cosine | missing | 18 | 50.0% | 100.0% | n/a | 0.0% | 100.0% (9) | 0.0% (0) |

## POS Shape

| scorer_id | pos_shape | cases | decision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | cross_pos_polysemy | 94 | 78.7% | 31.0% | 100.0% | 100.0% | 0.0% (0) | 69.0% (20) |
| tfidf_cosine | missing | 18 | 100.0% | 100.0% | n/a | 100.0% | 0.0% (0) | 0.0% (0) |
| tfidf_cosine | same_pos_polysemy | 76 | 73.7% | 23.1% | 100.0% | 100.0% | 0.0% (0) | 76.9% (20) |
| tfidf_cosine | single_sense | 18 | 100.0% | 100.0% | n/a | 100.0% | 0.0% (0) | 0.0% (0) |
| sentence_transformer_cosine | cross_pos_polysemy | 94 | 80.9% | 86.2% | 97.7% | 40.9% | 21.5% (14) | 13.8% (4) |
| sentence_transformer_cosine | missing | 18 | 50.0% | 100.0% | n/a | 0.0% | 100.0% (9) | 0.0% (0) |
| sentence_transformer_cosine | same_pos_polysemy | 76 | 73.7% | 69.2% | 90.6% | 50.0% | 24.0% (12) | 30.8% (8) |
| sentence_transformer_cosine | single_sense | 18 | 50.0% | 100.0% | n/a | 0.0% | 100.0% (9) | 0.0% (0) |

## Prior Reference

| scope | cases | scorer | phrase mode | rescue mode | decision | positive recall | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage1_representative_reference | 120 | tfidf_cosine | noun_family_frame_guard | sense_label_near_tie_active_rescue | 66.7% | 24.5% | 0.0% (0) | 75.5% (40) |

`stage1_representative_reference` is orientation only; it uses a different dataset mix and current-policy phrase/rescue settings.

## Failure Concentration

| scorer | dimension | value | cases | errors | error rate | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sentence_transformer_cosine | manual_case_type | phrase_no_winner | 58 | 40 | 69.0% | 40 | 0 |
| tfidf_cosine | manual_case_type | positive_active | 73 | 40 | 54.8% | 0 | 40 |
| tfidf_cosine | shadow_contract | candidate_polysemic | 170 | 40 | 23.5% | 0 | 40 |
| sentence_transformer_cosine | shadow_contract | candidate_polysemic | 170 | 38 | 22.4% | 26 | 12 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_3_to_4_mid | 82 | 26 | 31.7% | 21 | 5 |
| sentence_transformer_cosine | polysemy_band | low_1_to_3 | 80 | 22 | 27.5% | 19 | 3 |
| tfidf_cosine | pos_shape | same_pos_polysemy | 76 | 20 | 26.3% | 0 | 20 |
| sentence_transformer_cosine | pos_shape | same_pos_polysemy | 76 | 20 | 26.3% | 12 | 8 |
| tfidf_cosine | pos_shape | cross_pos_polysemy | 94 | 20 | 21.3% | 0 | 20 |
| tfidf_cosine | target_zipf_band_es | zipf_4_to_5_common | 72 | 19 | 26.4% | 0 | 19 |
| sentence_transformer_cosine | shadow_contract | not_applicable | 36 | 18 | 50.0% | 18 | 0 |
| sentence_transformer_cosine | pos_shape | cross_pos_polysemy | 94 | 18 | 19.1% | 14 | 4 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_4_to_5_common | 59 | 17 | 28.8% | 13 | 4 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_5_plus_very_common | 59 | 15 | 25.4% | 11 | 4 |
| tfidf_cosine | polysemy_band | medium_4_to_9 | 63 | 15 | 23.8% | 0 | 15 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_4_to_5_common | 72 | 15 | 20.8% | 10 | 5 |
| tfidf_cosine | source_zipf_band_en | zipf_4_to_5_common | 59 | 14 | 23.7% | 0 | 14 |
| tfidf_cosine | source_zipf_band_en | zipf_5_plus_very_common | 59 | 14 | 23.7% | 0 | 14 |
| tfidf_cosine | polysemy_band | high_10_plus | 45 | 13 | 28.9% | 0 | 13 |
| sentence_transformer_cosine | polysemy_band | medium_4_to_9 | 63 | 13 | 20.6% | 11 | 2 |
| sentence_transformer_cosine | target_zipf_band_es | zipf_5_plus_very_common | 38 | 12 | 31.6% | 11 | 1 |
| sentence_transformer_cosine | polysemy_band | high_10_plus | 45 | 12 | 26.7% | 5 | 7 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_3_to_4_mid | 50 | 12 | 24.0% | 9 | 3 |
| sentence_transformer_cosine | manual_case_type | positive_active | 73 | 12 | 16.4% | 0 | 12 |
| tfidf_cosine | polysemy_band | low_1_to_3 | 80 | 12 | 15.0% | 0 | 12 |
| tfidf_cosine | target_zipf_band_es | zipf_3_to_4_mid | 82 | 12 | 14.6% | 0 | 12 |
| tfidf_cosine | source_zipf_band_en | zipf_3_to_4_mid | 50 | 11 | 22.0% | 0 | 11 |
| sentence_transformer_cosine | polysemy_band | missing | 18 | 9 | 50.0% | 9 | 0 |
| sentence_transformer_cosine | pos_shape | missing | 18 | 9 | 50.0% | 9 | 0 |
| sentence_transformer_cosine | pos_shape | single_sense | 18 | 9 | 50.0% | 9 | 0 |

## Limitations

- `agent_draft_rows_can_be_too_close_to_wordnet_evidence`
- `tfidf_score_can_be_optimistic_under_template_and_definition_overlap`
- `sentence_transformer_phrase_no_winner_failures_are_diagnostic_until_rows_are_reviewed`
- `source_band_curves_are_directional_not_causal_on_this_packet`
- `runtime_policy_remains_unchanged`

## Next Steps

- Review the high-failure source-band and case-type cells before interpreting the curve.
- Replace weak no-winner templates with realistic observed or human-authored browser contexts.
- Rerun this surface after row review, then rerun formula and boundary sweeps on the reviewed packet.
