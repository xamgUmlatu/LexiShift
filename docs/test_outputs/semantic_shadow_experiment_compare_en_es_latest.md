# en-es Semantic Shadow Experiment Compare

- Status: `ok`
- Generated: `2026-04-11T02:49:16Z`
- Frontier read: `flat_no_row_level_change`
- Meaning: compare the current control row against a candidate row and measure exact row-level fixes, regressions, and slice deltas.

## Overall
- Row outcomes: `improved=0`, `regressed=0`, `stable_correct=156`, `stable_incorrect=19`
- Ambiguous-row changes: `fixed_harmful_allow=0`, `persistent_harmful_allow=15`
- Clear-row changes: `introduced_false_abstain=0`, `persistent_false_abstain=4`

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

### Candidate
- Experiment: `promotion_semantic_bridge_aux_text_on`
- Label: `Borrowed baseline with semantic-bridge aux text on`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Semantic-bridge aux text / examples: `True` / `False`
- Gold precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`

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
| feature:feature_reviewed_trigger_support_count:none | 13 | 13 | 13 | 100.0% | 54.5% | seed=6 cand=1 promo=6 |
| feature:feature_multi_source_candidate_count:none | 13 | 13 | 13 | 100.0% | 54.5% | seed=6 cand=1 promo=6 |
| feature:feature_semantic_bridge_candidate_count:none | 22 | 13 | 13 | 59.1% | 13.6% | seed=6 cand=1 promo=6 |
| feature:feature_active_support_mode:active_candidates | 24 | 9 | 9 | 37.5% | -8.0% | seed=0 cand=1 promo=8 |
| feature:feature_active_candidate_count:one | 24 | 9 | 9 | 37.5% | -8.0% | seed=0 cand=1 promo=8 |
| feature:feature_inventory_entry:present | 27 | 9 | 9 | 33.3% | -12.1% | seed=0 cand=1 promo=8 |
| feature:feature_same_pos_candidate_count:none | 8 | 8 | 8 | 100.0% | 54.5% | seed=6 cand=1 promo=1 |
| feature:feature_benchmark_target_present_count:none | 7 | 7 | 7 | 100.0% | 54.5% | seed=6 cand=1 promo=0 |
| feature:feature_trigger_family_candidate_count:none | 7 | 7 | 7 | 100.0% | 54.5% | seed=6 cand=1 promo=0 |
| feature:feature_forward_neighborhood_candidate_count:none | 7 | 7 | 7 | 100.0% | 54.5% | seed=6 cand=1 promo=0 |
| feature:feature_shadow_candidate_count:none | 7 | 7 | 7 | 100.0% | 54.5% | seed=6 cand=1 promo=0 |
| feature:feature_candidate_source_family_count:none | 7 | 7 | 7 | 100.0% | 54.5% | seed=6 cand=1 promo=0 |

### False-Abstain Buckets
| Bucket | Clear Rows | False Abstain | Persistent | Rate | Lift Vs Global |
| --- | ---: | ---: | ---: | ---: | ---: |
| feature:feature_reviewed_trigger_support_count:one | 5 | 4 | 4 | 80.0% | 77.2% |
| feature:feature_multi_source_candidate_count:one | 6 | 4 | 4 | 66.7% | 63.8% |
| feature:feature_candidate_source_family_count:two_to_three | 36 | 4 | 4 | 11.1% | 8.3% |
| feature:feature_inventory_entry:present | 101 | 4 | 4 | 4.0% | 1.1% |
| feature:feature_active_support_mode:active_candidates | 101 | 4 | 4 | 4.0% | 1.1% |
| feature:feature_active_candidate_count:one | 101 | 4 | 4 | 4.0% | 1.1% |
| feature:feature_candidate_source_family_signature:forward_index+reverse_lookup+semantic_bridge | 6 | 3 | 3 | 50.0% | 47.2% |
| feature:feature_benchmark_target_present_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.9% |
| feature:feature_trigger_family_candidate_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.9% |
| feature:feature_forward_neighborhood_candidate_count:two_to_three | 16 | 3 | 3 | 18.8% | 15.9% |
| feature:feature_candidate_pos_count:two_to_three | 56 | 3 | 3 | 5.4% | 2.5% |
| feature:feature_shadow_candidate_count:four_plus | 73 | 3 | 3 | 4.1% | 1.3% |

## Fixed Harmful-Allow Rows
- None

## Introduced False-Abstain Rows
- None

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
- None
