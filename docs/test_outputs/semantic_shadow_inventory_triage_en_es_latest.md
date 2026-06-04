# en-es Semantic Shadow Inventory Triage

- Status: `ok`
- Generated: `2026-04-09T22:26:17Z`
- Inventory status: `ok`
- Triggers scanned: `148`
- Triggers with any promotion: `90`
- Promoted candidate rows: `221`

## Top-1 Promotion Buckets
- `benchmark_aligned`: `19`
- `same_pos_only`: `71`
- `no_signal`: `0`
- `no_promotion`: `58`

## Candidate Bucket Counts
- `benchmark_aligned`: `19`
- `same_pos_only`: `202`
- `no_signal`: `0`

## Targets With No-Signal Top-1 Promotions
- None

## Benchmark-Aligned Top-1 Examples
- `acabar` / `end` -> `parte` (`benchmark_target_present`)
- `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
- `caso` / `matter` -> `punto` (`benchmark_target_present`)
- `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present`)
- `coger` / `catch` -> `vista` (`benchmark_target_present`)
- `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
- `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active`)
- `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active`)
- `fondo` / `fund` -> `capital` (`benchmark_target_present, same_pos_as_active`)
- `libro` / `book` -> `sacar` (`benchmark_target_present`)
- `llevar` / `take` -> `coger` (`reviewed_trigger_support, benchmark_target_present`)
- `malla` / `net` -> `red` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
- `marco` / `frame` -> `cuadro` (`benchmark_target_present, same_pos_as_active`)
- `plaza` / `square` -> `cuadro` (`benchmark_target_present`)
- `punto` / `point` -> `fondo` (`benchmark_target_present, same_pos_as_active`)
- `punto` / `period` -> `hora` (`benchmark_target_present`)
- `sacar` / `remove` -> `quitar` (`reviewed_trigger_support, benchmark_target_present`)
- `subir` / `rise` -> `salir` (`benchmark_target_present`)
- `tabla` / `board` -> `subir` (`benchmark_target_present`)

## Same-POS-Only Top-1 Examples
- `agua` / `water` -> `wata` (`same_pos_as_active`)
- `amigo` / `friend` -> `parcero` (`same_pos_as_active`)
- `amor` / `love` -> `nada` (`same_pos_as_active`)
- `banco` / `bank` -> `terraplén` (`same_pos_as_active`)
- `banco` / `bench` -> `sillete` (`same_pos_as_active`)
- `camino` / `road` -> `ruta` (`same_pos_as_active`)
- `camino` / `way` -> `vía` (`same_pos_as_active`)
- `camino` / `path` -> `trocha` (`same_pos_as_active`)
- `campo` / `field` -> `ámbito` (`same_pos_as_active`)
- `campo` / `countryside` -> `provincia` (`same_pos_as_active`)
- `campo` / `country` -> `zona` (`same_pos_as_active`)
- `canal` / `canal` -> `caz` (`same_pos_as_active`)
- `canal` / `channel` -> `álveo` (`same_pos_as_active`)
- `cargo` / `charge` -> `figura` (`same_pos_as_active`)
- `cargo` / `position` -> `puesto` (`same_pos_as_active`)
- `cargo` / `post` -> `publicación` (`same_pos_as_active`)
- `casa` / `house` -> `teatro` (`same_pos_as_active`)
- `caso` / `case` -> `vitrina` (`same_pos_as_active`)
- `ciudad` / `city` -> `urbe` (`same_pos_as_active`)
- `clave` / `key` -> `tecla` (`same_pos_as_active`)

## No-Signal Top-1 Examples
- None
