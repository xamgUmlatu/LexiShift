# en-es Semantic Shadow Experiment Compare

- Status: `ok`
- Generated: `2026-04-11T01:22:15Z`
- Frontier read: `mixed_but_positive`
- Meaning: compare the current control row against a candidate row and measure exact row-level fixes, regressions, and slice deltas.

## Overall
- Row outcomes: `improved=1`, `regressed=0`, `stable_correct=157`, `stable_incorrect=17`
- Ambiguous-row changes: `fixed_harmful_allow=0`, `persistent_harmful_allow=13`
- Clear-row changes: `introduced_false_abstain=0`, `persistent_false_abstain=4`

## Experiments

### Control
- Experiment: `promotion_multi_source_candidate_1_5`
- Label: `Borrowed baseline with multi-source candidate support 1.5`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.0` / `2`
- Gold precision / recall / F1: `75.0%` / `48.0%` / `58.5%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `89.7%` / `60.6%` / `39.4%` / `3.5%`
- Veto counts: `false_abstain=5`, `harmful_allow=13`
- Shadow support weights: `{"multi_source_candidate_support": 1.5}`

### Candidate
- Experiment: `promotion_multi_source_plus_forward_neighborhood_3_threshold_5_5`
- Label: `Borrowed baseline with multi-source 1.5, neighborhood overlap 3.0, threshold 5.5`
- Seed mode / policy: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow` / `support_score_v1`
- Trigger filter min: `0.0`
- Shadow support min / max promoted: `5.5` / `2`
- Gold precision / recall / F1: `80.0%` / `48.0%` / `60.0%`
- Veto accuracy / abstain recall / harmful allow / overblocking: `90.3%` / `60.6%` / `39.4%` / `2.8%`
- Veto counts: `false_abstain=4`, `harmful_allow=13`
- Shadow support weights: `{"forward_neighborhood_overlap": 3.0, "multi_source_candidate_support": 1.5}`

## Deltas
- Gold precision delta: `5.0%`
- Gold recall delta: `0.0%`
- Veto accuracy delta: `0.6%`
- Abstain recall delta: `0.0%`
- Harmful allow delta: `0.0%`
- Overblocking delta: `-0.7%`

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
