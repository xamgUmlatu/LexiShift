# en-es Semantic Shadow Experiment Matrix

- Status: `ok`
- Generated: `2026-04-22T19:58:14Z`
- Manifest: `docs/test_inputs/semantic_shadow_experiment_matrix_en_es.json`
- Data root: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift`
- Forward pack: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/freedict-es-en/main.sqlite` (freedict)
- Reverse pack: `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-en-es.sqlite` (wiktionary)
- Forward seed max words: `1`
- Neighbor-borrow modes loaded: `True`
- Generalization split manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_generalization_splits_en_es.json`
- Matrix meaning: each row is a full experiment configuration spanning seed admission, promotion scoring, and veto evaluation.
- Forward records with examples: `0 / 185` across `0` targets
- Reverse records with aux text: `2566 / 2566` across `297` triggers

## Summary
| Experiment | Seed Mode | Trigger Filter | Shadow Min | Max Promoted | Gold Prec | Gold Rec | Veto Acc | Abstain Rec | Harmful Allow |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reviewed_auto_control | benchmark_reviewed | 0.0 | 5.0 | 1 | 100.0% | 14.0% | 85.1% | 21.2% | 78.8% |
| source_only_baseline | rulegen_top3_plus_forward_gloss | 0.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| source_only_trigger_filtered | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| source_only_borrowed | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| source_only_borrowed_threshold_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 2.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| source_only_borrowed_threshold_3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| promotion_min_4 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 4.0 | 2 | 84.2% | 32.0% | 86.3% | 36.4% | 63.6% |
| promotion_min_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | n/a | 0.0% | 81.1% | 0.0% | 100.0% |
| promotion_top1 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 1 | 71.4% | 10.0% | 82.9% | 15.2% | 84.8% |
| promotion_top3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 3 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_forward_support_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_forward_support_half | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_forward_support_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 86.7% | 26.0% | 85.7% | 30.3% | 69.7% |
| promotion_same_pos_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_same_pos_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_active_profile_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_active_profile_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_semantic_bridge_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | n/a | 0.0% | 81.1% | 0.0% | 100.0% |
| promotion_semantic_bridge_high | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 85.7% | 24.0% | 85.1% | 27.3% | 72.7% |
| promotion_semantic_bridge_aux_text_on | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_semantic_bridge_aux_text_examples_on | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_cross_pos_penalty_off | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_cross_pos_penalty_strong | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 77.8% | 14.0% | 82.9% | 15.2% | 84.8% |
| promotion_multi_source_candidate_1 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 85.7% | 24.0% | 85.1% | 27.3% | 72.7% |
| promotion_multi_source_candidate_1_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_triplet_core_bonus | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_triplet_forward_bonus | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_triplet_bridge_guard_bonus | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_multi_source_candidate_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_multi_source_plus_forward_neighborhood_2 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_multi_source_plus_forward_neighborhood_3 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.0 | 2 | 88.2% | 30.0% | 86.9% | 36.4% | 63.6% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 88.9% | 16.0% | 84.0% | 18.2% | 81.8% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 88.9% | 16.0% | 84.0% | 18.2% | 81.8% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | 87.5% | 14.0% | 84.0% | 18.2% | 81.8% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_6 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 6.0 | 2 | 87.5% | 14.0% | 84.0% | 18.2% | 81.8% |
| promotion_multi_source_plus_trigger_family_reentry_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 90.9% | 20.0% | 85.1% | 24.2% | 75.8% |
| promotion_multi_source_plus_trigger_family_reentry_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 92.3% | 24.0% | 85.7% | 27.3% | 72.7% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_2_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 90.9% | 20.0% | 85.1% | 24.2% | 75.8% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_3_threshold_5_5 | rulegen_top3_plus_forward_gloss_plus_neighbor_borrow | 0.0 | 5.5 | 2 | 92.3% | 24.0% | 85.7% | 27.3% | 72.7% |
| source_only_forward_reward_off | rulegen_top3_plus_forward_gloss | 0.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_threshold_2 | rulegen_top3_plus_forward_gloss | 2.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_threshold_4 | rulegen_top3_plus_forward_gloss | 4.0 | 5.0 | 2 | 100.0% | 4.0% | 82.3% | 6.1% | 93.9% |
| admission_forward_gloss_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 100.0% | 10.0% | 82.9% | 9.1% | 90.9% |
| admission_forward_gloss_half | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 100.0% | 10.0% | 82.9% | 9.1% | 90.9% |
| admission_forward_gloss_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_multi_source_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_multi_source_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_reverse_shadow_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 100.0% | 4.0% | 82.3% | 6.1% | 93.9% |
| admission_reverse_shadow_high | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_multiword_penalty_off | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |
| admission_multiword_penalty_strong | rulegen_top3_plus_forward_gloss | 3.0 | 5.0 | 2 | 71.4% | 10.0% | 81.7% | 9.1% | 90.9% |

## Generalization
| Experiment | Assigned | Tune Acc | Tune Abstain | Tune Harmful | Held Acc | Held Abstain | Held Harmful | Held-Tune Abstain | Held-Tune Harmful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reviewed_auto_control | 78 | 68.2% | 22.2% | 77.8% | 64.7% | 20.0% | 80.0% | -2.2% | 2.2% |
| source_only_baseline | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| source_only_trigger_filtered | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| source_only_borrowed | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| source_only_borrowed_threshold_2 | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| source_only_borrowed_threshold_3 | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| promotion_min_4 | 78 | 77.3% | 44.4% | 55.6% | 64.7% | 26.7% | 73.3% | -17.8% | 17.8% |
| promotion_min_6 | 78 | 59.1% | 0.0% | 100.0% | 55.9% | 0.0% | 100.0% | 0.0% | 0.0% |
| promotion_top1 | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_top3 | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_forward_support_off | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_forward_support_half | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_forward_support_high | 78 | 75.0% | 38.9% | 61.1% | 61.8% | 20.0% | 80.0% | -18.9% | 18.9% |
| promotion_same_pos_off | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_same_pos_high | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_active_profile_off | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_active_profile_high | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_semantic_bridge_off | 78 | 59.1% | 0.0% | 100.0% | 55.9% | 0.0% | 100.0% | 0.0% | 0.0% |
| promotion_semantic_bridge_high | 78 | 72.7% | 33.3% | 66.7% | 61.8% | 20.0% | 80.0% | -13.3% | 13.3% |
| promotion_semantic_bridge_aux_text_on | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_semantic_bridge_aux_text_examples_on | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_cross_pos_penalty_off | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_cross_pos_penalty_strong | 78 | 65.9% | 16.7% | 83.3% | 58.8% | 13.3% | 86.7% | -3.3% | 3.3% |
| promotion_multi_source_candidate_1 | 78 | 72.7% | 33.3% | 66.7% | 61.8% | 20.0% | 80.0% | -13.3% | 13.3% |
| promotion_multi_source_candidate_1_5 | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_triplet_core_bonus | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_triplet_forward_bonus | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_triplet_bridge_guard_bonus | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_multi_source_candidate_2 | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_multi_source_plus_forward_neighborhood_2 | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_multi_source_plus_forward_neighborhood_3 | 78 | 75.0% | 38.9% | 61.1% | 67.6% | 33.3% | 66.7% | -5.6% | 5.6% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_5_5 | 78 | 65.9% | 16.7% | 83.3% | 61.8% | 20.0% | 80.0% | 3.3% | -3.3% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5 | 78 | 65.9% | 16.7% | 83.3% | 61.8% | 20.0% | 80.0% | 3.3% | -3.3% |
| promotion_multi_source_plus_forward_neighborhood_2_threshold_6 | 78 | 65.9% | 16.7% | 83.3% | 61.8% | 20.0% | 80.0% | 3.3% | -3.3% |
| promotion_multi_source_plus_forward_neighborhood_3_threshold_6 | 78 | 65.9% | 16.7% | 83.3% | 61.8% | 20.0% | 80.0% | 3.3% | -3.3% |
| promotion_multi_source_plus_trigger_family_reentry_2_threshold_5_5 | 78 | 70.5% | 27.8% | 72.2% | 61.8% | 20.0% | 80.0% | -7.8% | 7.8% |
| promotion_multi_source_plus_trigger_family_reentry_3_threshold_5_5 | 78 | 72.7% | 33.3% | 66.7% | 61.8% | 20.0% | 80.0% | -13.3% | 13.3% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_2_threshold_5_5 | 78 | 70.5% | 27.8% | 72.2% | 61.8% | 20.0% | 80.0% | -7.8% | 7.8% |
| promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_3_threshold_5_5 | 78 | 72.7% | 33.3% | 66.7% | 61.8% | 20.0% | 80.0% | -13.3% | 13.3% |
| source_only_forward_reward_off | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_threshold_2 | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_threshold_4 | 78 | 59.1% | 0.0% | 100.0% | 61.8% | 13.3% | 86.7% | 13.3% | -13.3% |
| admission_forward_gloss_off | 78 | 61.4% | 5.6% | 94.4% | 61.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_forward_gloss_half | 78 | 61.4% | 5.6% | 94.4% | 61.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_forward_gloss_high | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_multi_source_off | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_multi_source_high | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_reverse_shadow_off | 78 | 59.1% | 0.0% | 100.0% | 61.8% | 13.3% | 86.7% | 13.3% | -13.3% |
| admission_reverse_shadow_high | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_multiword_penalty_off | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |
| admission_multiword_penalty_strong | 78 | 61.4% | 5.6% | 94.4% | 58.8% | 13.3% | 86.7% | 7.8% | -7.8% |

## Details

### reviewed_auto_control
- Label: `Reviewed-trigger automatic control`
- Seed mode: `benchmark_reviewed`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `1`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`175 / 175`)
- Gold candidate precision / recall / F1: `100.0%` / `14.0%` / `24.6%`
- Gold trigger hit / top1 hit / exact-pool match: `21.2%` / `21.2%` / `3.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `21.2%` / `78.8%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=26`
- Automatic feature slices tracked: `46`
- Harmful-allow miss counts: `seed_missing=0`, `candidate_missing=1`, `promotion_miss=11`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `68.2%` / `22.2%` / `77.8%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `64.7%` / `20.0%` / `80.0%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-3.5%` / `-2.2%` / `2.2%` / `0.0%`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_baseline
- Label: `Source-only lexical baseline`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`277 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=2`, `candidate_missing=1`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_trigger_filtered
- Label: `Source-only with upstream trigger filter`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_borrowed
- Label: `Source-only with borrowed triggers`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_borrowed_threshold_2
- Label: `Borrowed triggers with threshold 2`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `2.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `94.2%` (`275 / 292`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=2`, `candidate_missing=1`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger-filter examples dropped:
  - `acabar` / `quit` score=`1.0` features=['reverse_shadow_support']
  - `camino` / `track` score=`1.0` features=['reverse_shadow_support']
  - `campo` / `ground` score=`1.0` features=['reverse_shadow_support']
  - `casa` / `ground` score=`1.0` features=['reverse_shadow_support']
  - `crear` / `file` score=`1.0` features=['reverse_shadow_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_borrowed_threshold_3
- Label: `Borrowed triggers with threshold 3`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `34.2%` (`100 / 292`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_min_4
- Label: `Borrowed baseline with support min 4`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `4.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `84.2%` / `32.0%` / `46.4%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.3%` / `36.4%` / `63.6%` / `2.1%`
- Veto counts: `false_abstain=3`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=4`, `candidate_missing=2`, `promotion_miss=6`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `77.3%` / `44.4%` / `55.6%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `64.7%` / `26.7%` / `73.3%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-12.6%` / `-17.8%` / `17.8%` / `5.3%`
- Sample harmful-allow rows:
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
  - `llevar` / `take` gold=['coger'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `punto` / `period` promoted=['hora'] cases=['en-es:punto'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_min_6
- Label: `Borrowed baseline with support min 6`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `n/a` / `0.0%` / `n/a`
- Gold trigger hit / top1 hit / exact-pool match: `0.0%` / `0.0%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.1%` / `0.0%` / `100.0%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=33`
- Automatic feature slices tracked: `46`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `59.1%` / `0.0%` / `100.0%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `55.9%` / `0.0%` / `100.0%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-3.2%` / `0.0%` / `0.0%` / `0.0%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_top1
- Label: `Borrowed baseline with top1 promotion`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `1`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `47`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_top3
- Label: `Borrowed baseline with top3 promotion`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `3`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_forward_support_off
- Label: `Borrowed baseline with forward support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"forward_trigger_support": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_forward_support_half
- Label: `Borrowed baseline with forward support half`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"forward_trigger_support": 0.25}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_forward_support_high
- Label: `Borrowed baseline with forward support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `86.7%` / `26.0%` / `40.0%`
- Gold trigger hit / top1 hit / exact-pool match: `30.3%` / `30.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `30.3%` / `69.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=23`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-13.2%` / `-18.9%` / `18.9%` / `5.3%`
- Shadow support weights: `{"forward_trigger_support": 1.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_same_pos_off
- Label: `Borrowed baseline with same-POS reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"same_pos_as_active": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_same_pos_high
- Label: `Borrowed baseline with same-POS reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"same_pos_as_active": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_active_profile_off
- Label: `Borrowed baseline with active-profile support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"active_profile_support": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_active_profile_high
- Label: `Borrowed baseline with active-profile support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"active_profile_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_semantic_bridge_off
- Label: `Borrowed baseline with semantic-bridge support off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `n/a` / `0.0%` / `n/a`
- Gold trigger hit / top1 hit / exact-pool match: `0.0%` / `0.0%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.1%` / `0.0%` / `100.0%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=33`
- Automatic feature slices tracked: `46`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `59.1%` / `0.0%` / `100.0%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `55.9%` / `0.0%` / `100.0%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-3.2%` / `0.0%` / `0.0%` / `0.0%`
- Shadow support weights: `{"semantic_bridge_support": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `camino` / `path` gold=['ruta', 'sendero'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_semantic_bridge_high
- Label: `Borrowed baseline with semantic-bridge support high`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `85.7%` / `24.0%` / `37.5%`
- Gold trigger hit / top1 hit / exact-pool match: `27.3%` / `27.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `27.3%` / `72.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=24`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `72.7%` / `33.3%` / `66.7%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-11.0%` / `-13.3%` / `13.3%` / `5.3%`
- Shadow support weights: `{"semantic_bridge_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_semantic_bridge_aux_text_on
- Label: `Borrowed baseline with semantic-bridge aux text on`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `True` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_semantic_bridge_aux_text_examples_on
- Label: `Borrowed baseline with semantic-bridge aux text and examples on`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `True` / `True`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_cross_pos_penalty_off
- Label: `Borrowed baseline with cross-POS penalty off`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"cross_pos_mismatch_penalty": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_cross_pos_penalty_strong
- Label: `Borrowed baseline with cross-POS penalty strong`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `77.8%` / `14.0%` / `23.7%`
- Gold trigger hit / top1 hit / exact-pool match: `15.2%` / `15.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `15.2%` / `84.8%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=28`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=1`, `candidate_missing=1`, `promotion_miss=10`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.1%` / `-3.3%` / `3.3%` / `5.3%`
- Shadow support weights: `{"cross_pos_mismatch_penalty": -2.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_candidate_1
- Label: `Borrowed baseline with multi-source candidate support 1.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `85.7%` / `24.0%` / `37.5%`
- Gold trigger hit / top1 hit / exact-pool match: `27.3%` / `27.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `27.3%` / `72.7%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=24`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `72.7%` / `33.3%` / `66.7%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-11.0%` / `-13.3%` / `13.3%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_candidate_1_5
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_triplet_core_bonus
- Label: `Borrowed baseline with multi-source 1.5 plus triplet core bonus 1.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "triplet_core_bonus": 1.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_triplet_forward_bonus
- Label: `Borrowed baseline with multi-source 1.5 plus triplet core 1.0 and forward bonus 0.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "triplet_core_bonus": 1.0, "triplet_forward_bonus": 0.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_triplet_bridge_guard_bonus
- Label: `Borrowed baseline with multi-source 1.5 plus triplet core 1.0 and bridge-guard bonus 1.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "triplet_bridge_guard_bonus": 1.0, "triplet_core_bonus": 1.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_candidate_2
- Label: `Borrowed baseline with multi-source candidate support 2.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 2.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_2
- Label: `Borrowed baseline with multi-source 1.5 plus neighborhood overlap 2.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_3
- Label: `Borrowed baseline with multi-source 1.5 plus neighborhood overlap 3.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Gold trigger hit / top1 hit / exact-pool match: `36.4%` / `36.4%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=5`, `candidate_missing=2`, `promotion_miss=5`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
  - `empleo` / `employment` gold=['ocupación'] promoted=[] miss=candidate_missing
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.9%` / `16.0%` / `27.1%`
- Gold trigger hit / top1 hit / exact-pool match: `18.2%` / `18.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `84.0%` / `18.2%` / `81.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=27`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-4.1%` / `3.3%` / `-3.3%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `88.9%` / `16.0%` / `27.1%`
- Gold trigger hit / top1 hit / exact-pool match: `18.2%` / `18.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `84.0%` / `18.2%` / `81.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=27`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-4.1%` / `3.3%` / `-3.3%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_2_threshold_6
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 2.0, threshold 6.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `87.5%` / `14.0%` / `24.1%`
- Gold trigger hit / top1 hit / exact-pool match: `18.2%` / `18.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `84.0%` / `18.2%` / `81.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=27`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-4.1%` / `3.3%` / `-3.3%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 2.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_3_threshold_6
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, threshold 6.0`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `6.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `87.5%` / `14.0%` / `24.1%`
- Gold trigger hit / top1 hit / exact-pool match: `18.2%` / `18.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `84.0%` / `18.2%` / `81.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=27`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `65.9%` / `16.7%` / `83.3%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-4.1%` / `3.3%` / `-3.3%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_trigger_family_reentry_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, trigger-family reentry 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `90.9%` / `20.0%` / `32.8%`
- Gold trigger hit / top1 hit / exact-pool match: `24.2%` / `24.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `24.2%` / `75.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=25`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `70.5%` / `27.8%` / `72.2%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-8.7%` / `-7.8%` / `7.8%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "trigger_family_reentry": 2.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_trigger_family_reentry_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, trigger-family reentry 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `92.3%` / `24.0%` / `38.1%`
- Gold trigger hit / top1 hit / exact-pool match: `27.3%` / `27.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `27.3%` / `72.7%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=24`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `72.7%` / `33.3%` / `66.7%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-11.0%` / `-13.3%` / `13.3%` / `5.3%`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "trigger_family_reentry": 3.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_2_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, trigger-family reentry 2.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `90.9%` / `20.0%` / `32.8%`
- Gold trigger hit / top1 hit / exact-pool match: `24.2%` / `24.2%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.1%` / `24.2%` / `75.8%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=25`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `70.5%` / `27.8%` / `72.2%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-8.7%` / `-7.8%` / `7.8%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5, "trigger_family_reentry": 2.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### promotion_multi_source_plus_forward_neighborhood_3_plus_trigger_family_reentry_3_threshold_5_5
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, trigger-family reentry 3.0, threshold 5.5`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`292 / 292`)
- Gold candidate precision / recall / F1: `92.3%` / `24.0%` / `38.1%`
- Gold trigger hit / top1 hit / exact-pool match: `27.3%` / `27.3%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `85.7%` / `27.3%` / `72.7%` / `0.7%`
- Veto counts: `false_abstain=1`, `harmful_allow=24`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=1`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `72.7%` / `33.3%` / `66.7%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `20.0%` / `80.0%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-11.0%` / `-13.3%` / `13.3%` / `5.3%`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5, "trigger_family_reentry": 3.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
  - `cuadro` / `table` gold=['tabla'] promoted=[] miss=seed_missing
- Sample false-abstain rows:
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### source_only_forward_reward_off
- Label: `Source-only with forward support ablated`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `100.0%` (`277 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=2`, `candidate_missing=1`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Shadow support weights: `{"forward_trigger_support": 0.0}`
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_threshold_2
- Label: `Admission threshold 2`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `2.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `99.3%` (`275 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=2`, `candidate_missing=1`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger-filter examples dropped:
  - `hasta` / `up to` score=`1.0` features=['rulegen_top3_source']
  - `según` / `according to` score=`1.0` features=['rulegen_top3_source']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_threshold_4
- Label: `Admission threshold 4`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `4.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `6.1%` (`17 / 277`)
- Gold candidate precision / recall / F1: `100.0%` / `4.0%` / `7.7%`
- Gold trigger hit / top1 hit / exact-pool match: `6.1%` / `6.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.3%` / `6.1%` / `93.9%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=31`
- Automatic feature slices tracked: `40`
- Harmful-allow miss counts: `seed_missing=9`, `candidate_missing=0`, `promotion_miss=3`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `59.1%` / `0.0%` / `100.0%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `13.3%` / `86.7%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `2.7%` / `13.3%` / `-13.3%` / `0.0%`
- Trigger-filter examples dropped:
  - `acabar` / `finish` score=`3.0` features=['rulegen_top3_source', 'active_side_support']
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=seed_missing
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_forward_gloss_off
- Label: `Admission forward-gloss reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `32.9%` (`91 / 277`)
- Gold candidate precision / recall / F1: `100.0%` / `10.0%` / `18.2%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `9.1%` / `90.9%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=4`, `candidate_missing=0`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `13.3%` / `86.7%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `0.4%` / `7.8%` / `-7.8%` / `0.0%`
- Trigger support weights: `{"forward_gloss_fragment": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`1.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `end` score=`2.0` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_forward_gloss_half
- Label: `Admission forward-gloss reward half`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `32.9%` (`91 / 277`)
- Gold candidate precision / recall / F1: `100.0%` / `10.0%` / `18.2%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.9%` / `9.1%` / `90.9%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=4`, `candidate_missing=0`, `promotion_miss=8`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `13.3%` / `86.7%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `0.4%` / `7.8%` / `-7.8%` / `0.0%`
- Trigger support weights: `{"forward_gloss_fragment": 0.5}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`1.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `end` score=`2.5` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_forward_gloss_high
- Label: `Admission forward-gloss reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"forward_gloss_fragment": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.5` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_multi_source_off
- Label: `Admission multi-source reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"multi_source_support": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_multi_source_high
- Label: `Admission multi-source reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"multi_source_support": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_reverse_shadow_off
- Label: `Admission reverse-shadow reward off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `24.9%` (`69 / 277`)
- Gold candidate precision / recall / F1: `100.0%` / `4.0%` / `7.7%`
- Gold trigger hit / top1 hit / exact-pool match: `6.1%` / `6.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `82.3%` / `6.1%` / `93.9%` / `0.0%`
- Veto counts: `false_abstain=0`, `harmful_allow=31`
- Automatic feature slices tracked: `44`
- Harmful-allow miss counts: `seed_missing=9`, `candidate_missing=0`, `promotion_miss=3`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `59.1%` / `0.0%` / `100.0%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `61.8%` / `13.3%` / `86.7%` / `0.0%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `2.7%` / `13.3%` / `-13.3%` / `0.0%`
- Trigger support weights: `{"reverse_shadow_support": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `end` score=`2.0` features=['forward_gloss_fragment', 'active_side_support', 'reverse_shadow_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=seed_missing
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=seed_missing
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_reverse_shadow_high
- Label: `Admission reverse-shadow reward high`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"reverse_shadow_support": 1.5}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_multiword_penalty_off
- Label: `Admission multiword penalty off`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"multi_word_penalty": 0.0}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']

### admission_multiword_penalty_strong
- Label: `Admission multiword penalty strong`
- Seed mode: `rulegen_top3_plus_forward_gloss`
- Policy: `support_score_v1`
- Trigger filter min: `3.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Seed trigger keep rate: `36.1%` (`100 / 277`)
- Gold candidate precision / recall / F1: `71.4%` / `10.0%` / `17.5%`
- Gold trigger hit / top1 hit / exact-pool match: `9.1%` / `9.1%` / `0.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `81.7%` / `9.1%` / `90.9%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=30`
- Automatic feature slices tracked: `48`
- Harmful-allow miss counts: `seed_missing=3`, `candidate_missing=0`, `promotion_miss=9`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune split veto acc / abstain recall / harmful allow / overblocking: `61.4%` / `5.6%` / `94.4%` / `0.0%`
- Held-out split veto acc / abstain recall / harmful allow / overblocking: `58.8%` / `13.3%` / `86.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-2.5%` / `7.8%` / `-7.8%` / `5.3%`
- Trigger support weights: `{"multi_word_penalty": -2.0}`
- Trigger-filter examples dropped:
  - `acabar` / `cum` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `exhaust` score=`2.0` features=['rulegen_top3_source']
  - `acabar` / `workout` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `accomodate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
  - `acabar` / `terminate` score=`2.0` features=['forward_gloss_fragment', 'active_side_support']
- Sample harmful-allow rows:
  - `camino` / `road` gold=['carretera', 'ruta'] promoted=[] miss=promotion_miss
  - `campo` / `field` gold=['terreno'] promoted=[] miss=promotion_miss
  - `cargo` / `job` gold=['empleo', 'ocupación', 'trabajo'] promoted=[] miss=promotion_miss
  - `carretera` / `road` gold=['camino', 'ruta'] promoted=[] miss=promotion_miss
  - `coger` / `take` gold=['llevar'] promoted=[] miss=promotion_miss
- Sample false-abstain rows:
  - `plaza` / `square` promoted=['cuadro'] cases=['en-es:plaza'] slices=[]
  - `ruta` / `route` promoted=['camino'] cases=['en-es:ruta'] slices=['family:path_route']
- Split-unassigned rows:
  - `agua` / `water` families=[] cases=['en-es:agua']
  - `amigo` / `friend` families=[] cases=['en-es:amigo']
  - `amor` / `love` families=[] cases=['en-es:amor']
  - `amor` / `affection` families=[] cases=['en-es:amor']
  - `canal` / `canal` families=[] cases=['en-es:canal']
