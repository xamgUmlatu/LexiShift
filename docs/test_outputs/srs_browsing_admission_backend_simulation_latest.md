# SRS Browsing Admission Backend Simulation

- Status: `ok`
- Decision: `srs_browsing_admission_backend_simulation_ready`
- Pair: `en-es`
- Aggregate items retained: `8`
- Admission budget: `6`
- Runtime SRS mutation: `False`
- Raw text stored: `False`
- URL stored: `False`

## Ingest

- `input_signal_count`: `13`
- `accepted_signal_count`: `12`
- `dropped_signal_count`: `1`
- `capped_signal_count`: `2`
- `pruned_item_count`: `5`
- `retained_item_count`: `8`

## Aggregate Store Preview

| Lemma | Signal | Raw | Source | Target | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| `hipoteca` | 0.6017 | 4.5 | 4.5 | 0.0 | 0.9 |
| `préstamo` | 0.5681 | 4.0 | 4.0 | 0.0 | 0.8 |
| `salud` | 0.5681 | 4.0 | 0.0 | 4.0 | 0.0 |
| `diagnóstico` | 0.4893 | 3.0 | 3.0 | 0.0 | 0.75 |
| `tratamiento` | 0.3878 | 2.0 | 0.0 | 2.0 | 0.0 |
| `interés` | 0.309 | 1.4 | 1.4 | 0.0 | 0.7 |
| `clínica` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 |
| `cocina` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 |

## Strength Simulation

| Strength | Browsing Budget | Browsing Lane Share | Relevant Share | Driven Share | Selected |
| --- | ---: | ---: | ---: | ---: | --- |
| `off` | 0 | 0.0 | 0.0 | 0.0 | casa, ser, banco, perro, gato, comida |
| `balanced` | 1 | 0.166667 | 0.166667 | 0.166667 | hipoteca, casa, ser, banco, perro, gato |
| `strong` | 2 | 0.333333 | 0.333333 | 0.333333 | hipoteca, préstamo, casa, ser, banco, perro |

## Findings

| Severity | Finding | Detail |
| --- | --- | --- |
| `info` | `packet_cap_applied` | Signals beyond the per-packet cap were dropped. |
| `info` | `per_signal_count_cap_applied` | Large repeated counts were capped before aggregation. |
| `info` | `preset_browsing_share_is_monotonic` | Off, Balanced, and Strong increase browsing-lane share as intended. |
