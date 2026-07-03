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

- `pass` `extension_payload_count`: Extension packet count is inside the expected range.
- `pass` `extension_signal_count`: Extension signal count is inside the expected range.
- `pass` `source_mapping_signal_count`: Source-language signal count is inside the expected range.
- `pass` `target_surface_signal_count`: Target-language signal count is inside the expected range.
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
- `pass` `aggregate_browsing_context_count_min:発酵|はっこう`: `発酵|はっこう` has browsing_context_count >= 3.
- `pass` `aggregate_observation_sources:発酵|はっこう`: `発酵|はっこう` has observation sources ['source_mapping', 'target_surface'].
- `pass` `required_aggregate_target:血圧|けつあつ`: Aggregate store includes `血圧|けつあつ`.
- `pass` `aggregate_source_hit_count_min:血圧|けつあつ`: `血圧|けつあつ` has source_hit_count >= 0.7.
- `pass` `aggregate_observation_sources:血圧|けつあつ`: `血圧|けつあつ` has observation sources ['source_mapping'].
- `pass` `admission_simulation_exists:strong`: Admission simulation includes `strong` strength.
- `pass` `admission_browsing_driven_count_min:strong`: `strong` has enough browsing-driven selections.
- `pass` `admission_row_exists:strong:発酵|はっこう`: `strong` admission rows include `発酵|はっこう`.
- `pass` `admission_selected:strong:発酵|はっこう`: `発酵|はっこう` selected state matches expectation.
- `pass` `admission_lane:strong:発酵|はっこう`: `発酵|はっこう` selected lane is `browsing`.
- `pass` `admission_effective_signal_min:strong:発酵|はっこう`: `発酵|はっこう` has enough effective browsing signal.
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

### Admission Simulation

#### off

- Selected: `する, いる, 言う, 犬`
- Browsing driven count: `0`

| target | lane | selected | neutral rank | final rank | signal | boost |
|---|---:|---:|---:|---:|---:|---:|
| `する` | `general` | True | 1 | 1 | 0.0 | 1.0 |
| `いる` | `general` | True | 2 | 2 | 0.0 | 1.0 |
| `言う` | `general` | True | 3 | 3 | 0.0 | 1.0 |
| `犬` | `general` | True | 4 | 4 | 0.0 | 1.0 |
| `発酵|はっこう` | `not_selected` | False | 5 | 5 | 0.41296 | 1.0 |
| `血圧|けつあつ` | `not_selected` | False | 7 | 7 | 0.0 | 1.0 |
| `麹|こうじ` | `not_selected` | False | 8 | 8 | 0.0 | 1.0 |

#### balanced

- Selected: `する, いる, 言う, 犬`
- Browsing driven count: `0`

| target | lane | selected | neutral rank | final rank | signal | boost |
|---|---:|---:|---:|---:|---:|---:|
| `する` | `general` | True | 1 | 1 | 0.0 | 1.0 |
| `いる` | `general` | True | 2 | 2 | 0.0 | 1.0 |
| `言う` | `general` | True | 3 | 3 | 0.0 | 1.0 |
| `犬` | `general` | True | 4 | 4 | 0.0 | 1.0 |
| `発酵|はっこう` | `not_selected` | False | 5 | 5 | 0.41296 | 1.082976 |
| `血圧|けつあつ` | `not_selected` | False | 7 | 7 | 0.0 | 1.0 |
| `麹|こうじ` | `not_selected` | False | 8 | 8 | 0.0 | 1.0 |

#### strong

- Selected: `発酵, する, いる, 言う`
- Browsing driven count: `1`

| target | lane | selected | neutral rank | final rank | signal | boost |
|---|---:|---:|---:|---:|---:|---:|
| `する` | `general` | True | 1 | 1 | 0.0 | 1.0 |
| `いる` | `general` | True | 2 | 2 | 0.0 | 1.0 |
| `言う` | `general` | True | 3 | 3 | 0.0 | 1.0 |
| `発酵|はっこう` | `browsing` | True | 5 | 5 | 0.41296 | 1.169724 |
| `血圧|けつあつ` | `not_selected` | False | 7 | 7 | 0.0 | 1.0 |
| `麹|こうじ` | `not_selected` | False | 8 | 8 | 0.0 | 1.0 |


## en-es_source_saved_page_currently_unsupported_v1

- Status: `PASS`
- Pair: `en-es`
- Profile: `offline_page_mining`

### Checks

- `pass` `extension_payload_count`: Extension packet count is inside the expected range.
- `pass` `extension_signal_count`: Extension signal count is inside the expected range.
- `pass` `source_mapping_signal_count`: Source-language signal count is inside the expected range.
- `pass` `target_surface_signal_count`: Target-language signal count is inside the expected range.
- `pass` `native_host_ingest_succeeds_without_srs_mutation`: Native-host route persists browsing aggregates without mutating runtime SRS.
- `pass` `absent_payload_target:fermentación`: Payload/store exclude broad or wrong-pair target `fermentación`.

### Documents

| document | side | text chars | ruby pairs | sha256 |
|---|---:|---:|---:|---|
| `en_es_fermentation_article_a` | `source` | 291 | 0 | `b2d005f783ef` |

### Extension Signals

- Packet count: `0`
- Signal count: `0`
- Source signal count: `0`
- Target signal count: `0`

| target | side | source | count | confidence | context |
|---|---:|---:|---:|---:|---:|

### Aggregate Store

| target | reading | source | target | contexts | evidence | signal | sources |
|---|---:|---:|---:|---:|---:|---:|---|
