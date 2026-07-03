# SRS Browsing Admission Saved-Page Pack en-ja

- Status: `pass`
- Pair: `en-ja`
- Runtime scope: `saved_page_to_browsing_aggregate`
- Raw text stored in aggregate report: `False`

## Inputs

- `en_rabbit_wikipedia_summary` side=`source` chars=`38` ruby_pairs=`0` sha256=`45dc3f598aaa874b4dc51dc4baafd303d81dfd3a4366183d6d1f566e08a5e105`
- `ja_chuumon_no_ooi_ryouriten_aozora` side=`target` chars=`6090` ruby_pairs=`106` sha256=`7add6054faf2f74d376949483e9fc8151c118c154f2478ad26f0f264173c42e0`

## Signal Summary

- Total signals: `130`
- Source-mapping signals: `4`
- Target-surface signals: `126`

### Top Signals

| Target | Source | Count | Confidence | Evidence |
|---|---:|---:|---:|---|
| `ラビット` | `source_mapping` | 1 | 0.57735 | `rabbit` |
| `兎|うさぎ` | `source_mapping` | 1 | 0.57735 | `rabbit` |
| `哺乳類|ほにゅうるい` | `source_mapping` | 1 | 0.57735 | `mammal` |
| `獣類|じゅうるい` | `source_mapping` | 1 | 0.57735 | `mammal` |
| `二人|ふたり` | `target_surface` | 22 | 1.0 | `二人` |
| `いらっしゃい` | `target_surface` | 11 | 1.0 | `いらっしゃい` |
| `がたがた|ガタガタ` | `target_surface` | 9 | 1.0 | `がたがた` |
| `ください` | `target_surface` | 9 | 1.0 | `ください` |
| `早く|はやく` | `target_surface` | 9 | 1.0 | `早く` |
| `クリーム` | `target_surface` | 8 | 1.0 | `クリーム` |
| `それから` | `target_surface` | 6 | 1.0 | `それから` |
| `何か|なにか` | `target_surface` | 6 | 1.0 | `何か` |
| `料理店|りょうりてん` | `target_surface` | 6 | 1.0 | `料理店` |
| `注文|ちゅうもん` | `target_surface` | 6 | 0.707107 | `注文` |
| `注文の多い|ちゅうもんのおおい` | `target_surface` | 5 | 1.0 | `注文の多い` |
| `裏側|うらがわ` | `target_surface` | 5 | 1.0 | `裏側` |
| `香水|こうすい` | `target_surface` | 5 | 0.707107 | `香水` |
| `あんまり|あまり` | `target_surface` | 4 | 1.0 | `あんまり` |
| `ざわざわ` | `target_surface` | 4 | 1.0 | `ざわざわ` |
| `じゃないか` | `target_surface` | 4 | 1.0 | `じゃないか` |

## Aggregate Store

- Items: `129`

| Target | Source | Target | Replacement | Reading Conf. | Sources |
|---|---:|---:|---:|---:|---|
| `いらっしゃい` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `がたがた|ガタガタ` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `ください` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `それから` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `クリーム` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `二人|ふたり` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `何か|なにか` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `料理店|りょうりてん` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `早く|はやく` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |
| `注文の多い|ちゅうもんのおおい` | 0.0 | 5.0 | 0.0 | 1.0 | `target_surface` |

## Findings

- `pass` source_mapping_signals_present: `{'count': 4}`
- `pass` target_surface_signals_present: `{'count': 126}`
- `pass` required_observation_source:source_mapping: `{'observed_sources': ['source_mapping', 'target_surface']}`
- `pass` required_observation_source:target_surface: `{'observed_sources': ['source_mapping', 'target_surface']}`
- `pass` helper_aggregate_store_populated: `{'count': 129}`
- `pass` target_ruby_pairs_detected: `{'count': 106}`
- `pass` helper_privacy_contract: `{'raw_text_stored': False, 'url_stored': False, 'runtime_srs_mutation': False, 'private_payload_fields_ignored': 0}`
