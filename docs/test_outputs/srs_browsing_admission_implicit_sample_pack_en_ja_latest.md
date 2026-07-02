# SRS Browsing Admission Implicit Sample Pack (en-ja)

- Status: `PASS`
- Scenarios: `7`
- Scenario pass/warn/fail: `7` / `0` / `0`
- Pair: `en-ja`
- Runtime scope: `preview_only_implicit_browsing_admission`

## Interpretation

This pack tests backend implicit personalization after target lemmas are already resolved. It does not validate live browser text extraction.

## Scenarios

### no_history_neutral_p30

- Status: `pass`
- Proficiency: `0.3`
- Topic weights: `{}`
- Signals: `0`
- Matching signals: `0` / aggregate items `0`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 無い, 出来る, 因る, 時, ため, 又, 仕舞う, 彼 |
| `balanced` | 0 | 0 | 無い, 出来る, 因る, 時, ため, 又, 仕舞う, 彼 |
| `strong` | 0 | 0 | 無い, 出来る, 因る, 時, ため, 又, 仕舞う, 彼 |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `EMPTY_STORE_BASELINE`: Empty store preserved neutral selection.

### implicit_food_only_p20

- Status: `pass`
- Proficiency: `0.2`
- Topic weights: `{}`
- Signals: `4`
- Matching signals: `4` / aggregate items `4`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | ある, こと, よう, 思う, 見る, 良い, その, 因る |
| `balanced` | 2 | 2 | 料理, 野菜, ある, こと, よう, 思う, 見る, 良い |
| `strong` | 3 | 3 | 料理, 野菜, 飲む, ある, こと, よう, 思う, 見る |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `SIGNALS_MATCH_CANDIDATES`: Implicit signals matched candidates.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.

Strong browsing rows:
- `料理` signal=1.0 boost=1.200621 selected=True
- `野菜` signal=1.0 boost=1.175447 selected=True
- `飲む` signal=1.0 boost=1.154363 selected=True
- `食べる` signal=1.0 boost=1.162555 selected=False

### explicit_food_only_p20

- Status: `pass`
- Proficiency: `0.2`
- Topic weights: `{"food_cooking": 1.0}`
- Signals: `0`
- Matching signals: `0` / aggregate items `0`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| `balanced` | 0 | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| `strong` | 0 | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `EMPTY_STORE_BASELINE`: Empty store preserved neutral selection.

### explicit_food_plus_food_p20

- Status: `pass`
- Proficiency: `0.2`
- Topic weights: `{"food_cooking": 1.0}`
- Signals: `4`
- Matching signals: `4` / aggregate items `4`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| `balanced` | 2 | 0 | 料理, 食べる, 飲む, 酒, 味, 野菜, パン, 焼く |
| `strong` | 3 | 0 | 料理, 食べる, 野菜, 飲む, 酒, 味, パン, 焼く |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `SIGNALS_MATCH_CANDIDATES`: Implicit signals matched candidates.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.

Strong browsing rows:
- `料理` signal=1.0 boost=1.251254 selected=True
- `食べる` signal=1.0 boost=1.209862 selected=True
- `野菜` signal=1.0 boost=1.219308 selected=True
- `飲む` signal=1.0 boost=1.192954 selected=True

### explicit_food_conflict_medicine_p20

- Status: `pass`
- Proficiency: `0.2`
- Topic weights: `{"food_cooking": 1.0}`
- Signals: `3`
- Matching signals: `3` / aggregate items `3`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 食べる, 飲む, 料理, 酒, 味, 野菜, パン, 焼く |
| `balanced` | 1 | 1 | 治療, 食べる, 飲む, 料理, 酒, 味, 野菜, パン |
| `strong` | 3 | 3 | 治療, 病院, 診断, 食べる, 飲む, 料理, 酒, 味 |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `SIGNALS_MATCH_CANDIDATES`: Implicit signals matched candidates.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.

Strong browsing rows:
- `治療` signal=1.0 boost=1.195474 selected=True
- `病院` signal=1.0 boost=1.205131 selected=True
- `診断` signal=1.0 boost=1.16163 selected=True

### implicit_medicine_only_p45

- Status: `pass`
- Proficiency: `0.45`
- Topic weights: `{}`
- Signals: `4`
- Matching signals: `4` / aggregate items `4`
- Candidate pool: `4782`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 良く, 矢張り, 共, センター, 其々, 此方, サービス, 旨い |
| `balanced` | 2 | 2 | 診断, 治療, 良く, 矢張り, 共, センター, 其々, 此方 |
| `strong` | 3 | 3 | 診断, 治療, 医者, 良く, 矢張り, 共, センター, 其々 |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `SIGNALS_MATCH_CANDIDATES`: Implicit signals matched candidates.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.

Strong browsing rows:
- `診断` signal=1.0 boost=1.159095 selected=True
- `治療` signal=1.0 boost=1.097093 selected=True
- `医者` signal=1.0 boost=1.009257 selected=True
- `病院` signal=1.0 boost=1.002946 selected=False

### suppressed_signal_guard_p30

- Status: `pass`
- Proficiency: `0.3`
- Topic weights: `{}`
- Signals: `2`
- Matching signals: `1` / aggregate items `2`
- Candidate pool: `4781`

| Strength | Browsing lane | Driven | Selected |
| --- | ---: | ---: | --- |
| `off` | 0 | 0 | 無い, 出来る, 因る, 時, ため, 又, 仕舞う, 彼 |
| `balanced` | 1 | 1 | 野菜, 無い, 出来る, 因る, 時, ため, 又, 仕舞う |
| `strong` | 1 | 1 | 野菜, 無い, 出来る, 因る, 時, ため, 又, 仕舞う |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `SIGNALS_MATCH_CANDIDATES`: Implicit signals matched candidates.
- `PASS` `BLOCKED_LEMMAS_NOT_SELECTED`: Blocked lemmas were not selected.

Strong browsing rows:
- `野菜` signal=1.0 boost=1.116282 selected=True

## Findings

| Level | Code | Message |
| --- | --- | --- |
| `PASS` | `ALL_SCENARIOS_PASS` | All implicit browsing scenarios satisfied configured expectations. |
