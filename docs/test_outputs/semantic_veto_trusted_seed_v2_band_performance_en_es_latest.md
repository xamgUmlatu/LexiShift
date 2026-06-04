# en-es Semantic Veto Trusted Seed v2 Band Performance

- Status: `ok`
- Decision: `trusted_seed_v2_band_performance_established`
- Generated: `2026-05-06T22:56:20Z`
- Unique cases: `42`
- Unique families: `10`

## Answer To The Band Question

- Claim strength: `directional_underpowered`
- Main signal: The trusted v2 bands preserve the broad scorer tradeoff: TF-IDF is safe but allows only 15.0% of positives, while sentence-transformer recovers active/shadow rows but abstains on only 20.0% of phrase/no-winner rows.
- Main caution: Band-level rows are now trusted, but the seed has only 42 cases and several source-band x case-type cells are tiny.

## Overall By Scorer

| scorer_id | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | 42 | 59.5% | 100.0% | 15.0% | 100.0% | 100.0% | 0.0% (0) | 85.0% (17) |
| sentence_transformer_cosine | 42 | 69.0% | 65.2% | 75.0% | 100.0% | 20.0% | 36.4% (8) | 25.0% (5) |

## Source Band

| scorer_id | source_zipf_band_en | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | 13 | 61.5% | 100.0% | 16.7% | 100.0% | 100.0% | 0.0% (0) | 83.3% (5) |
| tfidf_cosine | zipf_4_to_5_common | 13 | 69.2% | 100.0% | 33.3% | 100.0% | 100.0% | 0.0% (0) | 66.7% (4) |
| tfidf_cosine | zipf_3_to_4_mid | 8 | 50.0% | n/a | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (4) |
| tfidf_cosine | zipf_below_3_rare | 8 | 50.0% | n/a | 0.0% | 100.0% | 100.0% | 0.0% (0) | 100.0% (4) |
| sentence_transformer_cosine | zipf_5_plus_very_common | 13 | 76.9% | 71.4% | 83.3% | 100.0% | 33.3% | 28.6% (2) | 16.7% (1) |
| sentence_transformer_cosine | zipf_4_to_5_common | 13 | 61.5% | 57.1% | 66.7% | 100.0% | 0.0% | 42.9% (3) | 33.3% (2) |
| sentence_transformer_cosine | zipf_3_to_4_mid | 8 | 75.0% | 66.7% | 100.0% | 100.0% | 0.0% | 50.0% (2) | 0.0% (0) |
| sentence_transformer_cosine | zipf_below_3_rare | 8 | 62.5% | 66.7% | 50.0% | 100.0% | 50.0% | 25.0% (1) | 50.0% (2) |

## Source Band By Case Type

| scorer_id | source_zipf_band_en | manual_case_type | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | zipf_5_plus_very_common | positive_active | 6 | 16.7% | 100.0% | 16.7% | n/a | n/a | n/a (0) | 83.3% (5) |
| tfidf_cosine | zipf_5_plus_very_common | shadow_negative | 4 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_5_plus_very_common | phrase_no_winner | 3 | 100.0% | n/a | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | positive_active | 6 | 33.3% | 100.0% | 33.3% | n/a | n/a | n/a (0) | 66.7% (4) |
| tfidf_cosine | zipf_4_to_5_common | shadow_negative | 4 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_4_to_5_common | phrase_no_winner | 3 | 100.0% | n/a | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | positive_active | 4 | 0.0% | n/a | 0.0% | n/a | n/a | n/a (0) | 100.0% (4) |
| tfidf_cosine | zipf_3_to_4_mid | shadow_negative | 2 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_3_to_4_mid | phrase_no_winner | 2 | 100.0% | n/a | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | positive_active | 4 | 0.0% | n/a | 0.0% | n/a | n/a | n/a (0) | 100.0% (4) |
| tfidf_cosine | zipf_below_3_rare | shadow_negative | 2 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | zipf_below_3_rare | phrase_no_winner | 2 | 100.0% | n/a | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | positive_active | 6 | 83.3% | 100.0% | 83.3% | n/a | n/a | n/a (0) | 16.7% (1) |
| sentence_transformer_cosine | zipf_5_plus_very_common | shadow_negative | 4 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_5_plus_very_common | phrase_no_winner | 3 | 33.3% | 0.0% | n/a | n/a | 33.3% | 66.7% (2) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | positive_active | 6 | 66.7% | 100.0% | 66.7% | n/a | n/a | n/a (0) | 33.3% (2) |
| sentence_transformer_cosine | zipf_4_to_5_common | shadow_negative | 4 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_4_to_5_common | phrase_no_winner | 3 | 0.0% | 0.0% | n/a | n/a | 0.0% | 100.0% (3) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | positive_active | 4 | 100.0% | 100.0% | 100.0% | n/a | n/a | n/a (0) | 0.0% (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | shadow_negative | 2 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_3_to_4_mid | phrase_no_winner | 2 | 0.0% | 0.0% | n/a | n/a | 0.0% | 100.0% (2) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | positive_active | 4 | 50.0% | 100.0% | 50.0% | n/a | n/a | n/a (0) | 50.0% (2) |
| sentence_transformer_cosine | zipf_below_3_rare | shadow_negative | 2 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | zipf_below_3_rare | phrase_no_winner | 2 | 50.0% | 0.0% | n/a | n/a | 50.0% | 50.0% (1) | n/a (0) |

## Case Type

| scorer_id | manual_case_type | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | positive_active | 20 | 15.0% | 100.0% | 15.0% | n/a | n/a | n/a (0) | 85.0% (17) |
| tfidf_cosine | shadow_negative | 12 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| tfidf_cosine | phrase_no_winner | 10 | 100.0% | n/a | n/a | n/a | 100.0% | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | positive_active | 20 | 75.0% | 100.0% | 75.0% | n/a | n/a | n/a (0) | 25.0% (5) |
| sentence_transformer_cosine | shadow_negative | 12 | 100.0% | n/a | n/a | 100.0% | n/a | 0.0% (0) | n/a (0) |
| sentence_transformer_cosine | phrase_no_winner | 10 | 20.0% | 0.0% | n/a | n/a | 20.0% | 80.0% (8) | n/a (0) |

## Approval Source

| scorer_id | approval_id | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | user_step7_repaired_pilot_approval_2026_05_07 | 27 | 55.6% | 100.0% | 14.3% | 100.0% | 100.0% | 0.0% (0) | 85.7% (12) |
| tfidf_cosine | user_step8_deferred_mapping_review_fix_approval_2026_05_07 | 15 | 66.7% | 100.0% | 16.7% | 100.0% | 100.0% | 0.0% (0) | 83.3% (5) |
| sentence_transformer_cosine | user_step7_repaired_pilot_approval_2026_05_07 | 27 | 70.4% | 68.8% | 78.6% | 100.0% | 28.6% | 38.5% (5) | 21.4% (3) |
| sentence_transformer_cosine | user_step8_deferred_mapping_review_fix_approval_2026_05_07 | 15 | 66.7% | 57.1% | 66.7% | 100.0% | 0.0% | 33.3% (3) | 33.3% (2) |

## Trusted Seed v2 Status

| scorer_id | trusted_seed_v2_status | cases | decision | precision | positive allow | shadow abstain | phrase abstain | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | carried_forward_from_v1 | 27 | 55.6% | 100.0% | 14.3% | 100.0% | 100.0% | 0.0% (0) | 85.7% (12) |
| tfidf_cosine | newly_approved_deferred_fix | 15 | 66.7% | 100.0% | 16.7% | 100.0% | 100.0% | 0.0% (0) | 83.3% (5) |
| sentence_transformer_cosine | carried_forward_from_v1 | 27 | 70.4% | 68.8% | 78.6% | 100.0% | 28.6% | 38.5% (5) | 21.4% (3) |
| sentence_transformer_cosine | newly_approved_deferred_fix | 15 | 66.7% | 57.1% | 66.7% | 100.0% | 0.0% | 33.3% (3) | 33.3% (2) |

## Prior Draft Comparison

| scorer | current cases | prior cases | decision delta | positive allow delta | shadow abstain delta | phrase abstain delta | harmful delta | false abstain delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | 42 | 206 | -21.1% | -30.2% | +0.0% | +0.0% | +0 | -23 |
| sentence_transformer_cosine | 42 | 206 | -3.8% | -8.6% | +5.3% | -11.0% | -36 | -7 |

The prior surface used a 206-row agent-draft packet. Deltas show how the trusted v2 denominator differs, not a clean algorithm regression.

## Failure Concentration

| scorer | dimension | value | cases | errors | error rate | harmful | false abstain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tfidf_cosine | manual_case_type | positive_active | 20 | 17 | 85.0% | 0 | 17 |
| tfidf_cosine | no_winner_subtype | not_applicable | 32 | 17 | 53.1% | 0 | 17 |
| tfidf_cosine | approval_id | user_step7_repaired_pilot_approval_2026_05_07 | 27 | 12 | 44.4% | 0 | 12 |
| tfidf_cosine | trusted_seed_v2_status | carried_forward_from_v1 | 27 | 12 | 44.4% | 0 | 12 |
| sentence_transformer_cosine | manual_case_type | phrase_no_winner | 10 | 8 | 80.0% | 8 | 0 |
| sentence_transformer_cosine | approval_id | user_step7_repaired_pilot_approval_2026_05_07 | 27 | 8 | 29.6% | 5 | 3 |
| sentence_transformer_cosine | trusted_seed_v2_status | carried_forward_from_v1 | 27 | 8 | 29.6% | 5 | 3 |
| tfidf_cosine | family_repair_status | aligned_mapping_contexts_rewritten | 12 | 7 | 58.3% | 0 | 7 |
| sentence_transformer_cosine | no_winner_subtype | named_entity_or_title | 7 | 5 | 71.4% | 5 | 0 |
| tfidf_cosine | source_zipf_band_en | zipf_5_plus_very_common | 13 | 5 | 38.5% | 0 | 5 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_4_to_5_common | 13 | 5 | 38.5% | 3 | 2 |
| tfidf_cosine | approval_id | user_step8_deferred_mapping_review_fix_approval_2026_05_07 | 15 | 5 | 33.3% | 0 | 5 |
| tfidf_cosine | family_repair_status | active_sense_corrected | 15 | 5 | 33.3% | 0 | 5 |
| tfidf_cosine | trusted_seed_v2_status | newly_approved_deferred_fix | 15 | 5 | 33.3% | 0 | 5 |
| sentence_transformer_cosine | approval_id | user_step8_deferred_mapping_review_fix_approval_2026_05_07 | 15 | 5 | 33.3% | 3 | 2 |
| sentence_transformer_cosine | trusted_seed_v2_status | newly_approved_deferred_fix | 15 | 5 | 33.3% | 3 | 2 |
| sentence_transformer_cosine | manual_case_type | positive_active | 20 | 5 | 25.0% | 0 | 5 |
| sentence_transformer_cosine | no_winner_subtype | not_applicable | 32 | 5 | 15.6% | 0 | 5 |
| tfidf_cosine | source_zipf_band_en | zipf_3_to_4_mid | 8 | 4 | 50.0% | 0 | 4 |
| tfidf_cosine | source_zipf_band_en | zipf_below_3_rare | 8 | 4 | 50.0% | 0 | 4 |
| tfidf_cosine | family_repair_status | deferred_mapping_fixed_corrected_active_sense | 10 | 4 | 40.0% | 0 | 4 |
| sentence_transformer_cosine | family_repair_status | aligned_mapping_contexts_rewritten | 12 | 4 | 33.3% | 4 | 0 |
| tfidf_cosine | source_zipf_band_en | zipf_4_to_5_common | 13 | 4 | 30.8% | 0 | 4 |
| sentence_transformer_cosine | family_repair_status | active_sense_corrected | 15 | 4 | 26.7% | 1 | 3 |
| sentence_transformer_cosine | no_winner_subtype | metalinguistic_token | 3 | 3 | 100.0% | 3 | 0 |
| sentence_transformer_cosine | family_repair_status | representative_slot_replacement_for_rejected_mapping | 5 | 3 | 60.0% | 1 | 2 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_below_3_rare | 8 | 3 | 37.5% | 1 | 2 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_5_plus_very_common | 13 | 3 | 23.1% | 2 | 1 |
| sentence_transformer_cosine | source_zipf_band_en | zipf_3_to_4_mid | 8 | 2 | 25.0% | 2 | 0 |
| sentence_transformer_cosine | family_repair_status | deferred_mapping_fixed_corrected_active_sense | 10 | 2 | 20.0% | 2 | 0 |

## Sample Warnings

- `small_source_band:zipf_3_to_4_mid:8`
- `small_source_band:zipf_below_3_rare:8`
- `tiny_source_band_case_type_cell:zipf_3_to_4_mid:phrase_no_winner:2`
- `tiny_source_band_case_type_cell:zipf_3_to_4_mid:shadow_negative:2`
- `tiny_source_band_case_type_cell:zipf_below_3_rare:phrase_no_winner:2`
- `tiny_source_band_case_type_cell:zipf_below_3_rare:shadow_negative:2`

## Next Steps

- Use this trusted v2 report as the first reviewed band denominator.
- Run scorer bakeoffs or threshold sweeps on this seed as diagnostics only.
- Expand representative locked data before making a production acceptance claim.
