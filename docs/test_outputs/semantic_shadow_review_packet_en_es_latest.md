# en-es Shadow Review Packet

- Status: `ok`
- Generated: `2026-04-10T00:54:55Z`
- Provisional runtime policy: `cross_checked_v1`

## How To Read This Packet
- `Active Support` is what the active target currently has for that English trigger from forward pack evidence.
- `Shadow` is the competing Spanish target that the current shadow miner would test against.
- `Provisional Keep Rows` are the surviving blockers under the current strict policy.
- `Provisional Drop Rows` are rows that a looser benchmark-backed policy would allow, but the strict policy currently drops.

## Policy Snapshot
- `same_pos_lenient_v1`: triggers=`111` candidates=`284`
- `benchmark_backed_v1`: triggers=`19` candidates=`19`
- `cross_checked_v1`: triggers=`11` candidates=`11`
- `cross_checked_backoff_missing_active_v1`: triggers=`11` candidates=`11`

## Provisional Keep Rows
| Target | Trigger | Active Support | Shadow | Reasons | Recommendation |
|---|---|---|---|---|---|
| `coger` | `take` | `verb: to take (matched take)` | `llevar` | `reviewed_trigger_support, benchmark_target_present, same_pos_as_active` | `keep` |
| `cuadro` | `table` | `noun: table (matched table)` | `tabla` | `reviewed_trigger_support, benchmark_target_present, same_pos_as_active` | `keep` |
| `llevar` | `take` | `verb: to take (matched take)` | `coger` | `reviewed_trigger_support, benchmark_target_present, same_pos_as_active` | `keep` |
| `malla` | `net` | `noun: net (matched net)` | `red` | `reviewed_trigger_support, benchmark_target_present, same_pos_as_active` | `keep` |
| `marco` | `frame` | `noun: frame (matched frame)` | `cuadro` | `benchmark_target_present, same_pos_as_active` | `keep` |
| `sacar` | `remove` | `verb: to remove (matched remove)` | `quitar` | `reviewed_trigger_support, benchmark_target_present, same_pos_as_active` | `keep` |

## Provisional Drop Rows
| Target | Trigger | Active Support | Shadow | Drop Reason | Recommendation |
|---|---|---|---|---|---|
| `acabar` | `end` | `verb: to end (matched end)` | `parte` | `cross_pos_without_reviewed_trigger` | `drop` |
| `caso` | `matter` | `none` | `punto` | `missing_active_pos` | `drop_for_now` |
| `coger` | `catch` | `verb: to catch (matched catch)` | `vista` | `cross_pos_without_reviewed_trigger` | `drop` |
| `libro` | `book` | `noun: book (matched book)` | `sacar` | `cross_pos_without_reviewed_trigger` | `drop` |
| `plaza` | `square` | `none` | `cuadro` | `missing_active_pos` | `drop_for_now` |
| `punto` | `period` | `intj: period (matched period)` | `hora` | `cross_pos_without_reviewed_trigger` | `drop` |
| `subir` | `rise` | `none` | `salir` | `missing_active_pos` | `drop_for_now` |
| `tabla` | `board` | `noun: board (matched board)` | `subir` | `cross_pos_without_reviewed_trigger` | `drop` |

## Current Recommendation
- Keep the `Provisional Keep Rows` in the `en-es` blocker set.
- Keep the `Provisional Drop Rows` dropped for now.
- Treat missing active evidence as a reason to stay conservative, not to widen the policy.
