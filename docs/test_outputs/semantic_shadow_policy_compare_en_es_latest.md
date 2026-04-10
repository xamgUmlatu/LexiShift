# en-es Shadow Promotion Policy Comparison

- Status: `ok`
- Generated: `2026-04-10T01:58:05Z`
- Inventory status: `ok`
- Inventory default policy: `same_pos_lenient_v1`

## same_pos_lenient_v1
- Promoted triggers: `111`
- Promoted candidate rows: `284`
- `benchmark_aligned`: `19`
- `same_pos_only`: `92`
- `no_signal`: `0`
- `no_promotion`: `37`
- Samples:
  - `acabar` / `finish` -> `ultimar` (`same_pos_as_active`)
  - `acabar` / `end` -> `parte` (`benchmark_target_present`)
  - `agua` / `water` -> `wata` (`same_pos_as_active`)
  - `amigo` / `friend` -> `parcero` (`same_pos_as_active`)
  - `amor` / `love` -> `nada` (`same_pos_as_active`)
  - `banco` / `bank` -> `terraplén` (`same_pos_as_active`)
  - `banco` / `bench` -> `sillete` (`same_pos_as_active`)
  - `camino` / `road` -> `ruta` (`same_pos_as_active`)

## benchmark_backed_v1
- Promoted triggers: `19`
- Promoted candidate rows: `19`
- `benchmark_aligned`: `19`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `129`
- Samples:
  - `acabar` / `end` -> `parte` (`benchmark_target_present`)
  - `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
  - `caso` / `matter` -> `punto` (`benchmark_target_present`)
  - `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `coger` / `catch` -> `vista` (`benchmark_target_present`)
  - `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active`)
  - `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active`)

## cross_checked_v1
- Promoted triggers: `11`
- Promoted candidate rows: `11`
- `benchmark_aligned`: `11`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `137`
- Samples:
  - `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
  - `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active`)
  - `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active`)
  - `fondo` / `fund` -> `capital` (`benchmark_target_present, same_pos_as_active`)
  - `llevar` / `take` -> `coger` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `malla` / `net` -> `red` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)

## cross_checked_backoff_missing_active_v1
- Promoted triggers: `11`
- Promoted candidate rows: `11`
- `benchmark_aligned`: `11`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `137`
- Samples:
  - `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
  - `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active`)
  - `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active`)
  - `fondo` / `fund` -> `capital` (`benchmark_target_present, same_pos_as_active`)
  - `llevar` / `take` -> `coger` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `malla` / `net` -> `red` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
