# en-es Semantic Shadow Experiment Compare

- Status: `ok`
- Generated: `2026-04-22T20:00:41Z`
- Generalization split manifest: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_routing_generalization_splits_en_es.json`
- Frontier read: `flat_no_row_level_change`
- Meaning: compare the current control row against a candidate row and measure exact row-level fixes, regressions, and slice deltas.

## Overall
- Row outcomes: `improved=0`, `regressed=0`, `stable_correct=152`, `stable_incorrect=23`
- Ambiguous-row changes: `fixed_harmful_allow=0`, `persistent_harmful_allow=21`
- Clear-row changes: `introduced_false_abstain=0`, `persistent_false_abstain=2`

## Experiments

### Control
- Experiment: `promotion_multi_source_candidate_1_5`
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Gold precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Split-unassigned rows: agua/water families=[]; amigo/friend families=[]; amor/love families=[]; amor/affection families=[]; canal/canal families=[]

### Candidate
- Experiment: `promotion_triplet_core_bonus`
- Label: `Borrowed baseline with multi-source 1.5 plus triplet core bonus 1.0`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `False` / `False`
- Gold precision / recall / F1: `88.2%` / `30.0%` / `44.8%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `86.9%` / `36.4%` / `63.6%` / `1.4%`
- Veto counts: `false_abstain=2`, `harmful_allow=21`
- Shadow support weights: `{"multi_source_candidate_support": 1.5, "triplet_core_bonus": 1.0}`
- Generalization split coverage: `assigned=78`, `unassigned=97`
- Tune veto acc / abstain recall / harmful allow / overblocking: `75.0%` / `38.9%` / `61.1%` / `0.0%`
- Held-out veto acc / abstain recall / harmful allow / overblocking: `67.6%` / `33.3%` / `66.7%` / `5.3%`
- Held-out minus tune acc / abstain recall / harmful allow / overblocking: `-7.4%` / `-5.6%` / `5.6%` / `5.3%`
- Split-unassigned rows: agua/water families=[]; amigo/friend families=[]; amor/love families=[]; amor/affection families=[]; canal/canal families=[]

## Deltas
- Gold precision delta: `0.0%`
- Gold recall delta: `0.0%`
- Veto accuracy delta: `0.0%`
- Abstain recall delta: `0.0%`
- Harmful allow delta: `0.0%`
- Overblocking delta: `0.0%`

## Automatic Bucket Read
- Meaning: candidate-side automatic feature buckets ranked by error concentration; this is a diagnostic read, not yet a routing policy.
- Minimum bucket rows shown: `3`
- Excluded downstream buckets: `['feature_promoted_target_count']`

### Harmful-Allow Buckets
| Bucket | Ambiguous Rows | Harmful Allow | Persistent | Rate | Lift Vs Global | Miss Mix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| feature:feature_same_pos_candidate_count:none | 33 | 21 | 21 | 63.6% | 0.0% | seed=11 cand=3 promo=7 |
| feature:feature_reviewed_trigger_support_count:none | 18 | 18 | 18 | 100.0% | 36.4% | seed=11 cand=3 promo=4 |
| feature:feature_multi_source_candidate_count:none | 19 | 18 | 18 | 94.7% | 31.1% | seed=11 cand=3 promo=4 |
| feature:feature_active_support_mode:none | 22 | 16 | 16 | 72.7% | 9.1% | seed=11 cand=2 promo=3 |
| feature:feature_active_candidate_count:none | 22 | 16 | 16 | 72.7% | 9.1% | seed=11 cand=2 promo=3 |
| feature:feature_semantic_bridge_candidate_count:none | 18 | 15 | 15 | 83.3% | 19.7% | seed=11 cand=1 promo=3 |
| feature:feature_forward_neighborhood_candidate_count:none | 14 | 14 | 14 | 100.0% | 36.4% | seed=11 cand=1 promo=2 |
| feature:feature_benchmark_target_present_count:none | 12 | 12 | 12 | 100.0% | 36.4% | seed=11 cand=1 promo=0 |
| feature:feature_trigger_family_candidate_count:none | 12 | 12 | 12 | 100.0% | 36.4% | seed=11 cand=1 promo=0 |
| feature:feature_candidate_pos_count:none | 12 | 12 | 12 | 100.0% | 36.4% | seed=11 cand=1 promo=0 |
| feature:feature_inventory_entry:missing | 11 | 11 | 11 | 100.0% | 36.4% | seed=11 cand=0 promo=0 |
| feature:feature_shadow_candidate_count:none | 11 | 11 | 11 | 100.0% | 36.4% | seed=11 cand=0 promo=0 |

### False-Abstain Buckets
| Bucket | Clear Rows | False Abstain | Persistent | Rate | Lift Vs Global |
| --- | ---: | ---: | ---: | ---: | ---: |
| feature:feature_reviewed_trigger_support_count:one | 5 | 2 | 2 | 40.0% | 38.6% |
| feature:feature_multi_source_candidate_count:one | 8 | 2 | 2 | 25.0% | 23.6% |
| feature:feature_candidate_source_family_count:two_to_three | 40 | 2 | 2 | 5.0% | 3.6% |
| feature:feature_candidate_pos_count:two_to_three | 61 | 2 | 2 | 3.3% | 1.9% |
| feature:feature_shadow_candidate_count:four_plus | 84 | 2 | 2 | 2.4% | 1.0% |
| feature:feature_active_support_mode:active_candidates | 89 | 2 | 2 | 2.2% | 0.8% |
| feature:feature_active_candidate_count:one | 89 | 2 | 2 | 2.2% | 0.8% |
| feature:feature_inventory_entry:present | 115 | 2 | 2 | 1.7% | 0.3% |
| feature:feature_same_pos_candidate_count:none | 142 | 2 | 2 | 1.4% | 0.0% |
| feature:feature_semantic_bridge_candidate_count:two_to_three | 11 | 1 | 1 | 9.1% | 7.7% |
| feature:feature_benchmark_target_present_count:two_to_three | 14 | 1 | 1 | 7.1% | 5.7% |
| feature:feature_trigger_family_candidate_count:two_to_three | 14 | 1 | 1 | 7.1% | 5.7% |

## Fixed Harmful-Allow Rows
- None

## Introduced False-Abstain Rows
- None

## Persistent Harmful-Allow Rows
- `camino` / `road` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:camino'] tags=['family:path_route']
- `campo` / `field` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:campo'] tags=['family:field_area_country']
- `coger` / `take` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:coger'] tags=['family:take_carry', 'hazard:phrase_sensitive', 'hazard:slang_leakage']
- `cuadro` / `table` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:cuadro'] tags=['family:table_board_chart']
- `empleo` / `employment` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=candidate_missing cases=['en-es:empleo'] tags=['family:job']
- `malla` / `mesh` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:malla'] tags=['family:net_mesh_network']
- `ocupación` / `employment` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:ocupación'] tags=['family:job']
- `ocupación` / `job` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=seed_missing cases=['en-es:ocupación'] tags=['family:job']
- `quitar` / `remove` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=promotion_miss cases=['en-es:quitar'] tags=['family:remove_take_out', 'hazard:phrase_sensitive']
- `red` / `net` control=harmful_allow candidate=harmful_allow control_promoted=[] candidate_promoted=[] miss=candidate_missing cases=['en-es:red'] tags=['family:net_mesh_network']

## Regressed Rows
- None
