# en-es Semantic Shadow Experiment Compare

- Status: `ok`
- Generated: `2026-04-12T23:55:35Z`
- Generalization split manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_generalization_splits_en_es.json`
- Frontier read: `still_open_meaningful_positive_delta`
- Meaning: compare the current control row against a candidate row and measure exact row-level fixes, regressions, and slice deltas.

## Overall
- Row outcomes: `improved=2`, `regressed=1`, `stable_correct=155`, `stable_incorrect=17`
- Ambiguous-row changes: `fixed_harmful_allow=2`, `persistent_harmful_allow=13`
- Clear-row changes: `introduced_false_abstain=1`, `persistent_false_abstain=4`

## Experiments

### Control
- Experiment: `source_only_borrowed`
- Label: `Source-only with borrowed triggers`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Gold precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune veto acc / abstain recall / harmful allow / overblocking: `79.5%` / `55.6%` / `44.4%` / `3.8%`
- Held-out veto acc / abstain recall / harmful allow / overblocking: `73.5%` / `53.3%` / `46.7%` / `10.5%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-6.0%` / `-2.2%` / `2.2%` / `6.7%`
- Split-unassigned rows: agua/water families=[]; amigo/friend families=[]; amor/love families=[]; amor/affection families=[]; canal/canal families=[]

### Candidate
- Experiment: `promotion_multi_source_candidate_1_5`
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Gold precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune veto acc / abstain recall / harmful allow / overblocking: `84.1%` / `66.7%` / `33.3%` / `3.8%`
- Held-out veto acc / abstain recall / harmful allow / overblocking: `73.5%` / `53.3%` / `46.7%` / `10.5%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-10.6%` / `-13.3%` / `13.3%` / `6.7%`
- Split-unassigned rows: agua/water families=[]; amigo/friend families=[]; amor/love families=[]; amor/affection families=[]; canal/canal families=[]

## Deltas
- Gold precision delta: `-3.6%`
- Gold recall delta: `4.0%`
- Veto accuracy delta: `0.6%`
- Abstain recall delta: `6.1%`
- Harmful allow delta: `-6.1%`
- Overblocking delta: `0.7%`

## Best Ambiguous Slice Gains
| Slice | Rows | Harmful Allow Count | Abstain Recall Delta | Accuracy Delta |
| --- | ---: | ---: | ---: | ---: |
| dimension:semantic_family:field_area_country | 11 | 4 -> 2 | 33.3% | 18.2% |
| tag:family:field_area_country | 11 | 4 -> 2 | 33.3% | 18.2% |
| feature:feature_candidate_pos_count:two_to_three | 70 | 7 -> 5 | 14.3% | 1.4% |
| feature:feature_candidate_source_family_signature:forward_index+reverse_lookup | 22 | 6 -> 4 | 13.3% | 4.5% |
| dimension:tier:smoke | 93 | 6 -> 4 | 11.8% | 2.2% |
| dimension:overlap_target_count:2 | 20 | 11 -> 9 | 10.0% | 10.0% |
| feature:feature_semantic_bridge_candidate_count:none | 134 | 13 -> 11 | 9.1% | 0.7% |
| feature:feature_active_candidate_count:one | 125 | 9 -> 7 | 8.3% | 0.8% |
| feature:feature_active_support_mode:active_candidates | 125 | 9 -> 7 | 8.3% | 0.8% |
| feature:feature_shadow_candidate_count:four_plus | 97 | 7 -> 5 | 8.3% | 1.0% |

## Clear-Slice Regressions
| Slice | Rows | False Abstain Count | Overblocking Delta | Accuracy Delta |
| --- | ---: | ---: | ---: | ---: |
| feature:feature_reviewed_trigger_support_count:one | 18 | 4 -> 5 | 20.0% | 0.0% |
| feature:feature_multi_source_candidate_count:one | 18 | 4 -> 5 | 16.7% | 0.0% |
| feature:feature_candidate_source_family_signature:forward_index+reverse_lookup | 22 | 1 -> 2 | 14.3% | 4.5% |
| feature:feature_same_pos_candidate_count:one | 12 | 0 -> 1 | 9.1% | -8.3% |
| feature:feature_benchmark_target_present_count:one | 31 | 1 -> 2 | 4.2% | 0.0% |
| feature:feature_forward_neighborhood_candidate_count:one | 31 | 1 -> 2 | 4.2% | 0.0% |
| feature:feature_trigger_family_candidate_count:one | 31 | 1 -> 2 | 4.2% | 0.0% |
| dimension:reviewed_expectation:expected_only | 35 | 0 -> 1 | 3.7% | -2.9% |
| feature:feature_candidate_source_family_count:two_to_three | 61 | 4 -> 5 | 2.8% | 1.6% |
| feature:feature_candidate_pos_count:two_to_three | 70 | 3 -> 4 | 1.8% | 1.4% |

## Automatic Bucket Read
- Meaning: candidate-side automatic feature buckets ranked by error concentration; this is a diagnostic read, not yet a routing policy.
- Minimum bucket rows shown: `3`
- Excluded downstream buckets: `['feature_promoted_target_count']`

### Harmful-Allow Buckets
| Bucket | Ambiguous Rows | Harmful Allow | Persistent | Rate | Lift Vs Global | Miss Mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| feature:feature_reviewed_trigger_support_count:none | 13 | 13 | 13 | 100.0% | 60.6% | seed=6 cand=1 promo=6 |
| feature:feature_multi_source_candidate_count:none | 13 | 13 | 13 | 100.0% | 60.6% | seed=6 cand=1 promo=6 |
| feature:feature_semantic_bridge_candidate_count:none | 22 | 11 | 11 | 50.0% | 10.6% | seed=6 cand=1 promo=4 |
| feature:feature_benchmark_target_present_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_trigger_family_candidate_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_forward_neighborhood_candidate_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_shadow_candidate_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_candidate_source_family_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_candidate_source_family_signature:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_candidate_pos_count:none | 7 | 7 | 7 | 100.0% | 60.6% | seed=6 cand=1 promo=0 |
| feature:feature_same_pos_candidate_count:none | 8 | 7 | 7 | 87.5% | 48.1% | seed=6 cand=1 promo=0 |
| feature:feature_active_support_mode:active_candidates | 24 | 7 | 7 | 29.2% | -10.2% | seed=0 cand=1 promo=6 |

### False-Abstain Buckets
| Bucket | Clear Rows | False Abstain | Persistent | Rate | Lift Vs Global |
| --- | ---: | ---: | ---: | ---: | ---: |
| feature:feature_reviewed_trigger_support_count:one | 5 | 5 | 4 | 100.0% | 96.5% |
| feature:feature_multi_source_candidate_count:one | 6 | 5 | 4 | 83.3% | 79.8% |
| feature:feature_candidate_source_family_count:two_to_three | 36 | 5 | 4 | 13.9% | 10.4% |
| feature:feature_inventory_entry:present | 101 | 5 | 4 | 5.0% | 1.4% |
| feature:feature_active_support_mode:active_candidates | 101 | 5 | 4 | 5.0% | 1.4% |
| feature:feature_active_candidate_count:one | 101 | 5 | 4 | 5.0% | 1.4% |
| feature:feature_candidate_source_family_signature:forward_index+reverse_lookup+semantic_bridge | 6 | 3 | 3 | 50.0% | 46.5% |
| feature:feature_benchmark_target_present_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.2% |
| feature:feature_trigger_family_candidate_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.2% |
| feature:feature_forward_neighborhood_candidate_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.2% |
| feature:feature_candidate_pos_count:two_to_three | 56 | 4 | 3 | 7.1% | 3.6% |
| feature:feature_shadow_candidate_count:four_plus | 73 | 4 | 3 | 5.5% | 2.0% |

## Fixed Harmful-Allow Rows
- `terreno` / `ground` control=harmful_allow candidate=true_abstain control_promoted=[] candidate_promoted=['tierra', 'fondo'] miss=promotion_miss cases=['en-es:terreno'] tags=['family:field_area_country']
- `terreno` / `land` control=harmful_allow candidate=true_abstain control_promoted=[] candidate_promoted=['tierra'] miss=promotion_miss cases=['en-es:terreno'] tags=['family:field_area_country']

## Introduced False-Abstain Rows
- `punto` / `period` control=true_allow candidate=false_abstain control_promoted=[] candidate_promoted=['hora'] cases=['en-es:punto']

## Persistent Harmful-Allow Rows
- `campo` / `field` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:campo'] tags=['family:field_area_country']
- `empleo` / `employment` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=candidate_missing cases=['en-es:empleo'] tags=['family:job']
- `malla` / `mesh` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:malla'] tags=['family:net_mesh_network']
- `ocupación` / `employment` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:ocupación'] tags=['family:job']
- `red` / `net` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:red'] tags=['family:net_mesh_network']
- `reja` / `grille` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:reja'] tags=['family:net_mesh_network']
- `reja` / `mesh` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:reja'] tags=['family:net_mesh_network']
- `rejilla` / `grille` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:rejilla'] tags=['family:net_mesh_network']
- `rejilla` / `mesh` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:rejilla'] tags=['family:net_mesh_network']
- `ruta` / `road` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:ruta'] tags=['family:path_route']

## Regressed Rows
- `punto` / `period` control=true_allow candidate=false_abstain control_promoted=[] candidate_promoted=['hora'] cases=['en-es:punto']
