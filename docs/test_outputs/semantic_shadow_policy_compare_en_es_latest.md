# en-es Shadow Promotion Policy Comparison

- Status: `ok`
- Generated: `2026-04-10T04:57:14Z`
- Inventory status: `ok`
- Inventory default policy: `same_pos_lenient_v1`

## same_pos_lenient_v1
- Promoted triggers: `111`
- Promoted candidate rows: `285`
- `benchmark_aligned`: `22`
- `same_pos_only`: `89`
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

## support_score_v1
- Promoted triggers: `14`
- Promoted candidate rows: `14`
- `benchmark_aligned`: `14`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `134`
- Samples:
  - `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
  - `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active, active_side_support`)
  - `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active, active_side_support`)
  - `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active, active_side_support`)
  - `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active, active_side_support`)
  - `fondo` / `fund` -> `capital` (`benchmark_target_present, same_pos_as_active, active_side_support`)
  - `llevar` / `take` -> `coger` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active, active_side_support`)
  - `malla` / `net` -> `red` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active, active_side_support`)

## benchmark_backed_v1
- Promoted triggers: `22`
- Promoted candidate rows: `22`
- `benchmark_aligned`: `22`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `126`
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
- Promoted triggers: `14`
- Promoted candidate rows: `14`
- `benchmark_aligned`: `14`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `134`
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
- Promoted triggers: `14`
- Promoted candidate rows: `14`
- `benchmark_aligned`: `14`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `134`
- Samples:
  - `cargo` / `job` -> `trabajo` (`reviewed_trigger_support, benchmark_target_present`)
  - `coger` / `take` -> `llevar` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cuadro` / `table` -> `tabla` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `cura` / `priest` -> `padre` (`benchmark_target_present, same_pos_as_active`)
  - `escuela` / `school` -> `banco` (`benchmark_target_present, same_pos_as_active`)
  - `fondo` / `fund` -> `capital` (`benchmark_target_present, same_pos_as_active`)
  - `llevar` / `take` -> `coger` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
  - `malla` / `net` -> `red` (`reviewed_trigger_support, benchmark_target_present, same_pos_as_active`)
