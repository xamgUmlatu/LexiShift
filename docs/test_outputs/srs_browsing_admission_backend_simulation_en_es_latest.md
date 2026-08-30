# SRS Browsing Admission Backend Simulation

- Status: `ok`
- Decision: `srs_browsing_admission_backend_simulation_ready`
- Pair: `en-es`
- Aggregate items retained: `8`
- Admission budget: `6`
- Runtime SRS mutation: `False`
- Raw text stored: `False`
- URL stored: `False`
- Helper-persisted fixture: `True`
- Opt-in required: `True`

## Ingest

- `helper_status`: `ok`
- `private_payload_fields_ignored`: `0`
- `input_signal_count`: `13`
- `accepted_signal_count`: `12`
- `dropped_signal_count`: `1`
- `capped_signal_count`: `2`
- `pruned_item_count`: `5`
- `retained_item_count`: `8`

## Suppression Guard

- Active suppressed lemmas: `1`
- Runtime SRS mutation: `False`
- Suppressed fixture rows: `viaje` (suspended)

## Aggregate Store Preview

| Target Key | Lemma | Signal | Raw | Source | Target | Source Conf. | Reading Conf. | Sources |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `hipoteca` | `hipoteca` | 0.6017 | 4.5 | 4.5 | 0.0 | 0.9 | 1.0 | source_mapping |
| `préstamo` | `préstamo` | 0.5681 | 4.0 | 4.0 | 0.0 | 0.8 | 1.0 | source_mapping |
| `salud` | `salud` | 0.5681 | 4.0 | 0.0 | 4.0 | 0.0 | 1.0 | target_surface |
| `diagnóstico` | `diagnóstico` | 0.4893 | 3.0 | 3.0 | 0.0 | 0.75 | 1.0 | source_mapping |
| `tratamiento` | `tratamiento` | 0.3878 | 2.0 | 0.0 | 2.0 | 0.0 | 1.0 | target_surface |
| `interés` | `interés` | 0.309 | 1.4 | 1.4 | 0.0 | 0.7 | 1.0 | source_mapping |
| `clínica` | `clínica` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 | 1.0 | target_surface |
| `cocina` | `cocina` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 | 1.0 | target_surface |

## Strength Simulation

| Strength | Browsing Budget | Browsing Lane Share | Relevant Share | Driven Share | Selected |
| --- | ---: | ---: | ---: | ---: | --- |
| `off` | 0 | 0.0 | 0.0 | 0.0 | casa, ser, banco, perro, gato, comida |
| `balanced` | 1 | 0.166667 | 0.166667 | 0.166667 | hipoteca, casa, ser, banco, perro, gato |
| `strong` | 2 | 0.333333 | 0.333333 | 0.333333 | hipoteca, préstamo, casa, ser, banco, perro |

## Probability Preview

The deterministic column is exact for this read-only simulation. The approximate column estimates inclusion probability if the lane uses weighted sampling without replacement.

| Strength | Lemma | Selected | Suppressed | Deterministic P | Approx P | Browsing P | General P |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `off` | `casa` | True | - | 1.0 | 0.513809 | 0.0 | 0.513809 |
| `off` | `ser` | True | - | 1.0 | 0.49958 | 0.0 | 0.49958 |
| `off` | `banco` | True | - | 1.0 | 0.477452 | 0.0 | 0.477452 |
| `off` | `perro` | True | - | 1.0 | 0.454345 | 0.0 | 0.454345 |
| `off` | `gato` | True | - | 1.0 | 0.446418 | 0.0 | 0.446418 |
| `off` | `comida` | True | - | 1.0 | 0.438376 | 0.0 | 0.438376 |
| `off` | `hipoteca` | False | - | 0.0 | 0.369687 | 0.0 | 0.369687 |
| `off` | `préstamo` | False | - | 0.0 | 0.36053 | 0.0 | 0.36053 |
| `balanced` | `casa` | True | - | 1.0 | 0.451716 | 0.0 | 0.451716 |
| `balanced` | `ser` | True | - | 1.0 | 0.438376 | 0.0 | 0.438376 |
| `balanced` | `banco` | True | - | 1.0 | 0.417756 | 0.0 | 0.417756 |
| `balanced` | `perro` | True | - | 1.0 | 0.396378 | 0.0 | 0.396378 |
| `balanced` | `gato` | True | - | 1.0 | 0.38908 | 0.0 | 0.38908 |
| `balanced` | `comida` | False | - | 0.0 | 0.381692 | 0.0 | 0.381692 |
| `balanced` | `hipoteca` | True | - | 1.0 | 0.453431 | 0.197064 | 0.319288 |
| `balanced` | `préstamo` | False | - | 0.0 | 0.440919 | 0.188496 | 0.311057 |
| `strong` | `casa` | True | - | 1.0 | 0.381692 | 0.0 | 0.381692 |
| `strong` | `ser` | True | - | 1.0 | 0.369687 | 0.0 | 0.369687 |
| `strong` | `banco` | True | - | 1.0 | 0.35124 | 0.0 | 0.35124 |
| `strong` | `perro` | True | - | 1.0 | 0.332253 | 0.0 | 0.332253 |
| `strong` | `gato` | False | - | 0.0 | 0.325802 | 0.0 | 0.325802 |
| `strong` | `hipoteca` | True | - | 1.0 | 0.531115 | 0.362184 | 0.264859 |
| `strong` | `comida` | False | - | 0.0 | 0.319288 | 0.0 | 0.319288 |
| `strong` | `préstamo` | True | - | 1.0 | 0.513078 | 0.343987 | 0.257756 |

## Findings

| Severity | Finding | Detail |
| --- | --- | --- |
| `info` | `packet_cap_applied` | Signals beyond the per-packet cap were dropped. |
| `info` | `per_signal_count_cap_applied` | Large repeated counts were capped before aggregation. |
| `info` | `preset_browsing_share_is_monotonic` | Off, Balanced, and Strong increase browsing-lane share as intended. |
| `info` | `off_strength_matches_neutral_baseline` | No-history/off-strength admission preserves neutral ordering. |
| `info` | `suppressed_lemmas_not_selected` | Browsing signals do not override active admission suppression. |
