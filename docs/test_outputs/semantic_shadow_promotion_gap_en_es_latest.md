# en-es Semantic Shadow Promotion Gap

- Status: `ok`
- Generated: `2026-04-22T20:02:46Z`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Support score min / max promoted: `5.0` / `2`
- Gold trigger rows: `33`
- Rows with promoted gold blocker: `12` (`36.4%`)
- Promotion-miss rows: `7`
- Candidate-missing rows: `14`
- Support score weights: `{"multi_source_candidate_support": 1.5}`

## Promotion-Miss Score Histogram
- score `1.0`: `1`
- score `2.0`: `2`
- score `3.0`: `2`
- score `4.0`: `2`
- score `4.5`: `1`

## Promotion-Miss Reason Signatures
- `benchmark_target_present`: `1`
- `benchmark_target_present+active_side_support+trigger_family_reentry`: `1`
- `benchmark_target_present+active_side_support+trigger_family_reentry+forward_neighborhood_overlap+semantic_bridge_support`: `1`
- `benchmark_target_present+active_side_support+trigger_family_reentry+semantic_bridge_support`: `1`
- `benchmark_target_present+semantic_bridge_support`: `1`
- `reviewed_trigger_support+benchmark_target_present+active_side_support+trigger_family_reentry`: `1`
- `reviewed_trigger_support+benchmark_target_present+active_side_support+trigger_family_reentry+forward_neighborhood_overlap`: `1`
- `reviewed_trigger_support+forward_trigger_support+benchmark_target_present+semantic_bridge_support`: `1`

## Promotion-Miss Semantic Families
- `field_area_country`: `3`
- `net_mesh_network`: `1`
- `path_route`: `1`
- `remove_take_out`: `1`
- `take_carry`: `1`

## Promotion-Miss Examples
- `tierra` / `ground` -> `terreno` score=`4.5` gap=`0.5` family=`field_area_country` reasons=['reviewed_trigger_support', 'forward_trigger_support', 'benchmark_target_present', 'semantic_bridge_support']
- `camino` / `road` -> `carretera` score=`4.0` gap=`1.0` family=`path_route` reasons=['reviewed_trigger_support', 'benchmark_target_present', 'active_side_support', 'trigger_family_reentry']
- `coger` / `take` -> `llevar` score=`4.0` gap=`1.0` family=`take_carry` reasons=['reviewed_trigger_support', 'benchmark_target_present', 'active_side_support', 'trigger_family_reentry', 'forward_neighborhood_overlap']
- `tierra` / `land` -> `terreno` score=`3.0` gap=`2.0` family=`field_area_country` reasons=['benchmark_target_present', 'active_side_support', 'trigger_family_reentry', 'semantic_bridge_support']
- `campo` / `field` -> `terreno` score=`2.0` gap=`3.0` family=`field_area_country` reasons=['benchmark_target_present', 'active_side_support', 'trigger_family_reentry']
- `quitar` / `remove` -> `sacar` score=`2.0` gap=`3.0` family=`remove_take_out` reasons=['benchmark_target_present', 'semantic_bridge_support']
- `malla` / `mesh` -> `rejilla` score=`1.0` gap=`4.0` family=`net_mesh_network` reasons=['benchmark_target_present']

## Candidate-Missing Examples
- `terreno` / `field` gold=['campo'] family=`field_area_country`
- `terreno` / `land` gold=['tierra'] family=`field_area_country`
- `empleo` / `employment` gold=['ocupación'] family=`job`
- `ocupación` / `employment` gold=['empleo'] family=`job`
- `ocupación` / `job` gold=['cargo', 'empleo', 'trabajo'] family=`job`
- `red` / `net` gold=['malla'] family=`net_mesh_network`
- `reja` / `grille` gold=['rejilla'] family=`net_mesh_network`
- `reja` / `mesh` gold=['malla', 'rejilla'] family=`net_mesh_network`
- `rejilla` / `grille` gold=['reja'] family=`net_mesh_network`
- `rejilla` / `mesh` gold=['malla', 'reja'] family=`net_mesh_network`
