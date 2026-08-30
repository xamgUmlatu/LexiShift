# SRS Browsing Admission Runtime Smoke

- Status: `PASS`
- Pair: `en-ja`
- Scope: `isolated_extension_payload_native_host_helper_admission_smoke`
- Live user data touched: `False`
- Admission budget: `4`

## Checks

- `pass` `extension_payload_is_privacy_safe`: Extension packet has only hashed/bucketed context keys and no raw private strings.
- `pass` `native_host_ingest_succeeds_without_srs_mutation`: Native-host route persists only the browsing aggregate store.
- `pass` `multi_context_signal_survives_ingest`: Repeated exposures across separate contexts become per-target context evidence.
- `pass` `ruby_target_surface_survives_ingest`: Ruby page mining emits reading-aware target-surface evidence.
- `pass` `source_mapping_survives_ingest`: Conservative source-language mining emits mapped evidence and rejects ambiguous source terms.
- `pass` `single_context_high_count_is_not_enough`: A high count from one context is gated out before admission boost.
- `pass` `strong_preset_can_move_context_supported_interest`: Context-supported browsing interest can enter through the browsing lane.
- `pass` `opt_out_maintains_existing_store`: An opt-out packet decays existing aggregate state without adding new evidence.

## Extension Payload

- Accepted exposures: `25`
- Packet count: `1`
- Signal count: `8`
- Ruby signal count: `1`
- Source signal count: `2`
- Context key prefixes: `ctxh, pageh`
- Private strings absent: `True`

| target | side | source | count | context |
|---|---:|---:|---:|---:|
| `会社` | `replacement_exposure` | `replacement_exposure` | 5 | `pageh` |
| `料理` | `replacement_exposure` | `replacement_exposure` | 5 | `ctxh` |
| `料理` | `replacement_exposure` | `replacement_exposure` | 5 | `ctxh` |
| `発酵|はっこう` | `source` | `source_mapping` | 3 | `pageh` |
| `発酵|はっこう` | `target` | `target_surface` | 2 | `pageh` |
| `辛い|つらい` | `replacement_exposure` | `replacement_exposure` | 2 | `ctxh` |
| `辛い|つらい` | `replacement_exposure` | `replacement_exposure` | 2 | `ctxh` |
| `発酵|はっこう` | `source` | `source_mapping` | 1 | `pageh` |

## Aggregate Before Maintenance

| target | reading | source | target | repl | contexts | evidence | signal | sources |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `会社` | `` | 0.0 | 0.0 | 5.0 | 1 | 2.584963 | 0.317636 | `replacement_exposure` |
| `料理` | `` | 0.0 | 0.0 | 10.0 | 2 | 5.169925 | 0.482068 | `replacement_exposure` |
| `発酵` | `はっこう` | 2.32 | 2.0 | 0.0 | 3 | 3.699063 | 0.546151 | `source_mapping, target_surface` |
| `辛い` | `つらい` | 0.0 | 0.0 | 4.0 | 2 | 1.901955 | 0.229992 | `replacement_exposure` |

## Strong Admission Rows

- Selected: `料理, する, いる, 言う`
- Browsing driven count: `1`

| target | lane | selected | contexts | count_mult | effective_signal | boost |
|---|---:|---:|---:|---:|---:|---:|
| `する` | `general` | True | 0 | 0.0 | 0.0 | 1.0 |
| `いる` | `general` | True | 0 | 0.0 | 0.0 | 1.0 |
| `言う` | `general` | True | 0 | 0.0 | 0.0 | 1.0 |
| `料理` | `browsing` | True | 2 | 1.0 | 0.466849 | 1.204389 |
| `発酵` | `not_selected` | False | 3 | 1.0 | 0.41296 | 1.169724 |
| `会社` | `not_selected` | False | 1 | 0.0 | 0.0 | 1.0 |
| `辛い` | `not_selected` | False | 2 | 0.0 | 0.0 | 1.0 |

## Maintenance

- Response status: `skipped`
- Reason: `browsing_admission_not_opted_in`
- Runtime SRS mutation: `False`
- Aggregate items after: `4`
