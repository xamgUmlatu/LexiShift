# SRS Browsing Admission Offline Page Mining

- Status: `PASS`
- Scope: `offline_saved_page_extension_js_native_ingest`
- Config: `docs/test_inputs/srs_browsing_admission_offline_page_mining_cases.json`
- Live user data touched: `False`

## en-ja_source_and_ruby_saved_pages_v1

- Status: `PASS`
- Pair: `en-ja`
- Profile: `offline_page_mining`

### Checks

- `pass` `extension_payload_count`: At least one extension packet was built from saved pages.
- `pass` `extension_signal_count`: Saved pages produced the expected minimum signal volume.
- `pass` `source_mapping_signal_count`: Source-language pages produced mapped target-language signals.
- `pass` `target_surface_signal_count`: Target-language ruby pages produced reading-aware target signals.
- `pass` `native_host_ingest_succeeds_without_srs_mutation`: Native-host route persists browsing aggregates without mutating runtime SRS.
- `pass` `required_payload_target:発酵|はっこう`: Payload includes `発酵|はっこう`.
- `pass` `required_payload_target:血圧|けつあつ`: Payload includes `血圧|けつあつ`.
- `pass` `required_payload_target:麹|こうじ`: Payload includes `麹|こうじ`.
- `pass` `absent_payload_target:光|ひかり`: Payload/store exclude broad or wrong-pair target `光|ひかり`.
- `pass` `absent_payload_target:軽い|かるい`: Payload/store exclude broad or wrong-pair target `軽い|かるい`.
- `pass` `absent_payload_target:仕事|しごと`: Payload/store exclude broad or wrong-pair target `仕事|しごと`.
- `pass` `absent_payload_target:fermentación`: Payload/store exclude broad or wrong-pair target `fermentación`.
- `pass` `required_aggregate_target:発酵|はっこう`: Aggregate store includes `発酵|はっこう`.
- `pass` `aggregate_source_hit_count_min:発酵|はっこう`: `発酵|はっこう` has source_hit_count >= 2.3.
- `pass` `aggregate_target_hit_count_min:発酵|はっこう`: `発酵|はっこう` has target_hit_count >= 2.0.
- `pass` `aggregate_observation_sources:発酵|はっこう`: `発酵|はっこう` has observation sources ['source_mapping', 'target_surface'].
- `pass` `required_aggregate_target:血圧|けつあつ`: Aggregate store includes `血圧|けつあつ`.
- `pass` `aggregate_source_hit_count_min:血圧|けつあつ`: `血圧|けつあつ` has source_hit_count >= 0.7.
- `pass` `aggregate_observation_sources:血圧|けつあつ`: `血圧|けつあつ` has observation sources ['source_mapping'].
- `pass` `private_string_absent:value_sha256_0558a31a2463`: Raw page text and raw context identifiers are absent from extension packets.
- `pass` `private_string_absent:value_sha256_78f8a9c86e0f`: Raw page text and raw context identifiers are absent from extension packets.
- `pass` `private_string_absent:value_sha256_c1fa2a3d0c55`: Raw page text and raw context identifiers are absent from extension packets.

### Documents

| document | side | text chars | ruby pairs | sha256 |
|---|---:|---:|---:|---|
| `en_ja_fermentation_article_a` | `source` | 291 | 0 | `b2d005f783ef` |
| `en_ja_fermentation_article_b` | `source` | 117 | 0 | `b28be7406309` |
| `ja_fermentation_ruby_note` | `target` | 46 | 3 | `4e5f867aa22a` |

### Extension Signals

- Packet count: `1`
- Signal count: `5`
- Source signal count: `3`
- Target signal count: `2`

| target | side | source | count | confidence | context |
|---|---:|---:|---:|---:|---:|
| `発酵|はっこう` | `source` | `source_mapping` | 3 | 0.58 | `pageh` |
| `発酵|はっこう` | `target` | `target_surface` | 2 | 1 | `pageh` |
| `発酵|はっこう` | `source` | `source_mapping` | 1 | 0.58 | `pageh` |
| `血圧|けつあつ` | `source` | `source_mapping` | 1 | 0.72 | `pageh` |
| `麹|こうじ` | `target` | `target_surface` | 1 | 1 | `pageh` |

### Aggregate Store

| target | reading | source | target | contexts | evidence | signal | sources |
|---|---:|---:|---:|---:|---:|---:|---|
| `発酵` | `はっこう` | 2.32 | 2.0 | 3 | 3.699063 | 0.546151 | `source_mapping, target_surface` |
| `血圧` | `けつあつ` | 0.72 | 0.0 | 1 | 0.782409 | 0.203996 | `source_mapping` |
| `麹` | `こうじ` | 0.0 | 1.0 | 1 | 1.0 | 0.244651 | `target_surface` |
