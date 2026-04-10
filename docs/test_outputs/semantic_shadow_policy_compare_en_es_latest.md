# en-es Shadow Promotion Policy Comparison

- Status: `ok`
- Generated: `2026-04-10T22:26:14Z`
- Inventory status: `ok`
- Inventory default policy: `same_pos_lenient_v1`

## same_pos_lenient_v1
- Promoted triggers: `126`
- Promoted candidate rows: `318`
- `benchmark_aligned`: `64`
- `same_pos_only`: `62`
- `no_signal`: `0`
- `no_promotion`: `22`
- Samples:
  - `acabar` / `finish` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `acabar` / `end` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `agua` / `water` -> `wata` (`same_pos_as_active`)
  - `amigo` / `friend` -> `parcero` (`same_pos_as_active`)
  - `amor` / `love` -> `nada` (`same_pos_as_active`)
  - `banco` / `bank` -> `terraplén` (`same_pos_as_active`)
  - `banco` / `bench` -> `sillete` (`same_pos_as_active`)
  - `camino` / `road` -> `canal` (`benchmark_target_present, same_pos_as_active`)

## support_score_v1
- Promoted triggers: `45`
- Promoted candidate rows: `64`
- `benchmark_aligned`: `45`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `103`
- Samples:
  - `acabar` / `finish` -> `salir` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `acabar` / `end` -> `salir` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `camino` / `road` -> `canal` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `camino` / `way` -> `canal` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `camino` / `path` -> `canal` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `canal` / `canal` -> `camino` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `canal` / `channel` -> `camino` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)
  - `cargo` / `charge` -> `punto` (`benchmark_target_present, same_pos_as_active, active_side_support, semantic_bridge_support`)

## benchmark_backed_v1
- Promoted triggers: `64`
- Promoted candidate rows: `88`
- `benchmark_aligned`: `64`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `84`
- Samples:
  - `acabar` / `finish` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `acabar` / `end` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `road` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `way` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `path` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `canal` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `channel` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `cargo` / `charge` -> `punto` (`benchmark_target_present, same_pos_as_active`)

## cross_checked_v1
- Promoted triggers: `45`
- Promoted candidate rows: `64`
- `benchmark_aligned`: `45`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `103`
- Samples:
  - `acabar` / `finish` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `acabar` / `end` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `road` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `way` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `path` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `canal` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `channel` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `cargo` / `charge` -> `punto` (`benchmark_target_present, same_pos_as_active`)

## cross_checked_backoff_missing_active_v1
- Promoted triggers: `45`
- Promoted candidate rows: `64`
- `benchmark_aligned`: `45`
- `same_pos_only`: `0`
- `no_signal`: `0`
- `no_promotion`: `103`
- Samples:
  - `acabar` / `finish` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `acabar` / `end` -> `salir` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `road` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `way` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `camino` / `path` -> `canal` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `canal` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `canal` / `channel` -> `camino` (`benchmark_target_present, same_pos_as_active`)
  - `cargo` / `charge` -> `punto` (`benchmark_target_present, same_pos_as_active`)
