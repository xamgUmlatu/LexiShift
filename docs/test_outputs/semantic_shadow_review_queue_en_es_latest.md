# en-es Shadow Review Queue

- Status: `ok`
- Generated: `2026-04-09T23:27:43Z`
- Inventory status: `ok`
- Policy: `cross_checked_backoff_missing_active_v1`
- Rows: `6`
- Focus targets: `marco, cuadro, sacar, quitar, coger, llevar, malla, red, banco, pelota`

## Queue
- `coger` / `take` -> `llevar [reviewed_trigger_support, benchmark_target_present, same_pos_as_active]`
- `cuadro` / `table` -> `tabla [reviewed_trigger_support, benchmark_target_present, same_pos_as_active]`
- `llevar` / `take` -> `coger [reviewed_trigger_support, benchmark_target_present, same_pos_as_active]`
- `malla` / `net` -> `red [reviewed_trigger_support, benchmark_target_present, same_pos_as_active]`
- `marco` / `frame` -> `cuadro [benchmark_target_present, same_pos_as_active]`
- `sacar` / `remove` -> `quitar [reviewed_trigger_support, benchmark_target_present, same_pos_as_active]`
