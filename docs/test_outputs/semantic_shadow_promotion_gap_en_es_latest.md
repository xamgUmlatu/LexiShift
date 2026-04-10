# en-es Semantic Shadow Promotion Gap

- Status: `ok`
- Generated: `2026-04-10T23:41:24Z`
- Seed mode: `rulegen_top3_plus_forward_gloss_plus_neighbor_borrow`
- Policy: `support_score_v1`
- Support score min / max promoted: `5.0` / `2`
- Gold trigger rows: `33`
- Rows with promoted gold blocker: `19` (`57.6%`)
- Promotion-miss rows: `7`
- Candidate-missing rows: `7`
- Support score weights: `{"multi_source_candidate_support": 1.5}`

## Promotion-Miss Score Histogram
- score `1.5`: `1`
- score `3.0`: `2`
- score `3.5`: `3`
- score `4.0`: `1`

## Promotion-Miss Reason Signatures
- `forward_trigger_support+benchmark_target_present+same_pos_as_active+active_side_support`: `3`
- `benchmark_target_present+same_pos_as_active+active_side_support`: `2`
- `benchmark_target_present+same_pos_as_active+active_side_support+semantic_bridge_support`: `1`
- `forward_trigger_support+benchmark_target_present+active_side_support`: `1`

## Promotion-Miss Semantic Families
- `net_mesh_network`: `3`
- `field_area_country`: `2`
- `job`: `1`
- `table_board_chart`: `1`

## Promotion-Miss Examples
- `reja` / `grille` -> `rejilla` score=`4.0` gap=`1.0` family=`net_mesh_network` reasons=['benchmark_target_present', 'same_pos_as_active', 'active_side_support', 'semantic_bridge_support']
- `red` / `net` -> `malla` score=`3.5` gap=`1.5` family=`net_mesh_network` reasons=['forward_trigger_support', 'benchmark_target_present', 'same_pos_as_active', 'active_side_support']
- `tabla` / `table` -> `cuadro` score=`3.5` gap=`1.5` family=`table_board_chart` reasons=['forward_trigger_support', 'benchmark_target_present', 'same_pos_as_active', 'active_side_support']
- `trabajo` / `work` -> `empleo` score=`3.5` gap=`1.5` family=`job` reasons=['forward_trigger_support', 'benchmark_target_present', 'same_pos_as_active', 'active_side_support']
- `campo` / `field` -> `terreno` score=`3.0` gap=`2.0` family=`field_area_country` reasons=['benchmark_target_present', 'same_pos_as_active', 'active_side_support']
- `malla` / `mesh` -> `rejilla` score=`3.0` gap=`2.0` family=`net_mesh_network` reasons=['benchmark_target_present', 'same_pos_as_active', 'active_side_support']
- `tierra` / `ground` -> `terreno` score=`1.5` gap=`3.5` family=`field_area_country` reasons=['forward_trigger_support', 'benchmark_target_present', 'active_side_support']

## Candidate-Missing Examples
- `terreno` / `field` gold=['campo'] family=`field_area_country`
- `empleo` / `employment` gold=['ocupación'] family=`job`
- `ocupación` / `employment` gold=['empleo'] family=`job`
- `reja` / `mesh` gold=['malla', 'rejilla'] family=`net_mesh_network`
- `rejilla` / `grille` gold=['reja'] family=`net_mesh_network`
- `rejilla` / `mesh` gold=['malla', 'reja'] family=`net_mesh_network`
- `ruta` / `road` gold=['camino', 'carretera'] family=`path_route`
