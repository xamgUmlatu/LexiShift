# en-es Semantic Shadow Experiment Compare

- Status: `ok`
- Generated: `2026-04-11T01:01:22Z`
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
- Gold precision / recall / F1: `78.6%` / `44.0%` / `56.4%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.1%` / `54.5%` / `45.5%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=15`

### Candidate
- Experiment: `promotion_multi_source_candidate_1_5`
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Gold precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`

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
| dimension:tier:smoke | 93 | 6 -> 4 | 11.8% | 2.2% |
| dimension:overlap_target_count:2 | 20 | 11 -> 9 | 10.0% | 10.0% |
| dimension:reviewed_expectation:top1_expected | 140 | 11 -> 9 | 8.0% | 1.4% |
| dimension:pos:noun | 60 | 15 -> 13 | 6.9% | 3.3% |
| dimension:trigger_shape:unigram | 164 | 15 -> 13 | 6.1% | 0.6% |
| dimension:overlap_topology:shared_trigger | 33 | 15 -> 13 | 6.1% | 6.1% |

## Clear-Slice Regressions
| Slice | Rows | False Abstain Count | Overblocking Delta | Accuracy Delta |
| --- | ---: | ---: | ---: | ---: |
| dimension:reviewed_expectation:expected_only | 35 | 0 -> 1 | 3.7% | -2.9% |
| dimension:tier:hard | 82 | 2 -> 3 | 1.5% | -1.2% |
| dimension:trigger_shape:unigram | 164 | 4 -> 5 | 0.8% | 0.6% |
| dimension:overlap_target_count:1 | 142 | 4 -> 5 | 0.7% | -0.7% |
| dimension:overlap_topology:singleton_trigger | 142 | 4 -> 5 | 0.7% | -0.7% |

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
