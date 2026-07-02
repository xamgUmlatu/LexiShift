# SRS Browsing Admission Backend Simulation

- Status: `ok`
- Decision: `srs_browsing_admission_backend_simulation_ready`
- Pair: `en-ja`
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
- `input_signal_count`: `12`
- `accepted_signal_count`: `12`
- `dropped_signal_count`: `0`
- `capped_signal_count`: `2`
- `pruned_item_count`: `5`
- `retained_item_count`: `8`

## Suppression Guard

- Active suppressed lemmas: `1`
- Runtime SRS mutation: `False`
- Suppressed fixture rows: `旅行` (suspended)

## Aggregate Store Preview

| Lemma | Signal | Raw | Source | Target | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| `料理` | 0.6017 | 4.5 | 4.5 | 0.0 | 0.9 |
| `病院` | 0.5681 | 4.0 | 0.0 | 4.0 | 0.0 |
| `野菜` | 0.5681 | 4.0 | 4.0 | 0.0 | 0.8 |
| `診断` | 0.4893 | 3.0 | 3.0 | 0.0 | 0.75 |
| `治療` | 0.3878 | 2.0 | 0.0 | 2.0 | 0.0 |
| `金利` | 0.309 | 1.4 | 1.4 | 0.0 | 0.7 |
| `会社` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 |
| `切捨て確認` | 0.2447 | 1.0 | 0.0 | 1.0 | 0.0 |

## Strength Simulation

| Strength | Browsing Budget | Browsing Lane Share | Relevant Share | Driven Share | Selected |
| --- | ---: | ---: | ---: | ---: | --- |
| `off` | 0 | 0.0 | 0.166667 | 0.0 | する, いる, 言う, 犬, 猫, 会社 |
| `balanced` | 1 | 0.166667 | 0.166667 | 0.0 | 会社, する, いる, 言う, 犬, 猫 |
| `strong` | 2 | 0.333333 | 0.333333 | 0.166667 | 会社, 料理, する, いる, 言う, 犬 |

## Probability Preview

The deterministic column is exact for this read-only simulation. The approximate column estimates inclusion probability if the lane uses weighted sampling without replacement.

| Strength | Lemma | Selected | Suppressed | Deterministic P | Approx P | Browsing P | General P |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `off` | `する` | True | - | 1.0 | 0.513809 | 0.0 | 0.513809 |
| `off` | `いる` | True | - | 1.0 | 0.49958 | 0.0 | 0.49958 |
| `off` | `言う` | True | - | 1.0 | 0.477452 | 0.0 | 0.477452 |
| `off` | `犬` | True | - | 1.0 | 0.454345 | 0.0 | 0.454345 |
| `off` | `猫` | True | - | 1.0 | 0.446418 | 0.0 | 0.446418 |
| `off` | `会社` | True | - | 1.0 | 0.438376 | 0.0 | 0.438376 |
| `off` | `料理` | False | - | 0.0 | 0.369687 | 0.0 | 0.369687 |
| `off` | `野菜` | False | - | 0.0 | 0.36053 | 0.0 | 0.36053 |
| `balanced` | `する` | True | - | 1.0 | 0.451716 | 0.0 | 0.451716 |
| `balanced` | `いる` | True | - | 1.0 | 0.438376 | 0.0 | 0.438376 |
| `balanced` | `言う` | True | - | 1.0 | 0.417756 | 0.0 | 0.417756 |
| `balanced` | `会社` | True | - | 1.0 | 0.495845 | 0.18462 | 0.381692 |
| `balanced` | `犬` | True | - | 1.0 | 0.396378 | 0.0 | 0.396378 |
| `balanced` | `猫` | True | - | 1.0 | 0.38908 | 0.0 | 0.38908 |
| `balanced` | `料理` | False | - | 0.0 | 0.428391 | 0.160278 | 0.319288 |
| `balanced` | `野菜` | False | - | 0.0 | 0.416571 | 0.153153 | 0.311057 |
| `strong` | `する` | True | - | 1.0 | 0.381692 | 0.0 | 0.381692 |
| `strong` | `いる` | True | - | 1.0 | 0.369687 | 0.0 | 0.369687 |
| `strong` | `言う` | True | - | 1.0 | 0.35124 | 0.0 | 0.35124 |
| `strong` | `会社` | True | - | 1.0 | 0.542242 | 0.32753 | 0.319288 |
| `strong` | `犬` | True | - | 1.0 | 0.332253 | 0.0 | 0.332253 |
| `strong` | `猫` | False | - | 0.0 | 0.325802 | 0.0 | 0.325802 |
| `strong` | `料理` | True | - | 1.0 | 0.487358 | 0.302662 | 0.264859 |
| `strong` | `野菜` | False | - | 0.0 | 0.470601 | 0.286758 | 0.257756 |

## Findings

| Severity | Finding | Detail |
| --- | --- | --- |
| `info` | `per_signal_count_cap_applied` | Large repeated counts were capped before aggregation. |
| `info` | `preset_browsing_share_is_monotonic` | Off, Balanced, and Strong increase browsing-lane share as intended. |
| `info` | `off_strength_matches_neutral_baseline` | No-history/off-strength admission preserves neutral ordering. |
| `info` | `suppressed_lemmas_not_selected` | Browsing signals do not override active admission suppression. |
