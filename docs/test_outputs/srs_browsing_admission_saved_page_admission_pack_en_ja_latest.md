# SRS Browsing Admission Saved-Page Admission Pack (en-ja)

- Status: `PASS`
- Scenarios: `4`
- Scenario pass/warn/fail: `4` / `0` / `0`
- Saved-page signals: `130`
- Saved-page aggregate items: `129`
- Runtime scope: `preview_only_saved_page_browsing_admission`

## Interpretation

This pack starts after saved-page extraction has produced target-key browsing signals. It tests whether those signals materially affect a real en-ja profile-growth admission frontier, while remaining preview-only.

## Saved-Page Aggregate

| Target | Raw | Signal | Source | Target | Reading | Sources |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `いらっしゃい` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `がたがた|ガタガタ` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `ください` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `それから` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `クリーム` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `二人|ふたり` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `何か|なにか` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `料理店|りょうりてん` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `早く|はやく` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `注文の多い|ちゅうもんのおおい` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `裏側|うらがわ` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `あんまり|あまり` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `ざわざわ` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `じゃないか` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `たいもん` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `というのは` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |

## Scenarios

### neutral_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{}`
- Matching signals: `9` / aggregate items `129`
- Candidate pool: `10951`
- Strong added vs off: `作成, クリーム, 注文, 立派`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 16.34127 | 無い, 出来る, 良く, 彼女, 矢張り, 共, 規定, センター |
| `balanced` | 2 | 2 | 16.34127 | 作成, クリーム, 無い, 出来る, 良く, 彼女, 矢張り, 共 |
| `strong` | 4 | 4 | 16.34127 | 作成, クリーム, 注文, 立派, 無い, 出来る, 良く, 彼女 |

Strong browsing rows:

| Target | Raw | Effective | Quality | Specificity | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `作成|さくせい` | 0.489301 | 0.453978 | 1.0 | 0.927808 | 1.090243 | `True` |
| `クリーム|くりーむ` | 0.632412 | 0.620974 | 1.0 | 0.981913 | 1.093506 | `True` |
| `注文|ちゅうもん` | 0.53365 | 0.522812 | 1.0 | 0.979691 | 1.080135 | `True` |
| `立派|りっぱ` | 0.568061 | 0.557686 | 1.0 | 0.981737 | 1.071786 | `True` |
| `旦那|だんな` | 0.244651 | 0.236788 | 1.0 | 0.96786 | 1.038816 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 0.463741 | 1.0 | 0.947763 | 1.080771 | `False` |
| `鍵|かぎ` | 0.244651 | 0.240168 | 1.0 | 0.981678 | 1.036383 | `False` |
| `酢|す` | 0.244651 | 0.242684 | 1.0 | 0.991961 | 1.034518 | `False` |
| `兎|うさぎ` | 0.334165 | 0.341835 | 1.0 | 1.022952 | 1.039086 | `False` |
| `瓶|びん` | 0.244651 | 0.245569 | 1.0 | 1.003756 | 1.032322 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.

### neutral_p50_saved_pages

- Status: `pass`
- Proficiency: `0.5`
- Topic weights: `{}`
- Matching signals: `9` / aggregate items `129`
- Candidate pool: `10951`
- Strong added vs off: `香水, 壺, 鉄砲, 団子`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 16.34127 | 御座る, 旨い, 我々, なお, 当該, 積り, 成す, レベル |
| `balanced` | 2 | 2 | 16.34127 | 香水, 壺, 御座る, 旨い, 我々, なお, 当該, 積り |
| `strong` | 4 | 4 | 16.34127 | 香水, 壺, 鉄砲, 団子, 御座る, 旨い, 我々, なお |

Strong browsing rows:

| Target | Raw | Effective | Quality | Specificity | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `香水|こうすい` | 0.53365 | 0.564853 | 1.0 | 1.058472 | 1.04653 | `True` |
| `壺|つぼ` | 0.244651 | 0.250037 | 1.0 | 1.022018 | 1.0288 | `True` |
| `鉄砲|てっぽう` | 0.244651 | 0.254579 | 1.0 | 1.040581 | 1.02507 | `True` |
| `団子|だんご` | 0.244651 | 0.25463 | 1.0 | 1.04079 | 1.025027 | `True` |
| `紳士|しんし` | 0.244651 | 0.25463 | 1.0 | 1.04079 | 1.025027 | `False` |
| `否|いな` | 0.244651 | 0.245883 | 1.0 | 1.005039 | 1.03166 | `False` |
| `煉瓦|れんが` | 0.244651 | 0.255017 | 1.0 | 1.042371 | 1.024703 | `False` |
| `鹿|しか` | 0.244651 | 0.256539 | 1.0 | 1.048594 | 1.023413 | `False` |
| `錠|じょう` | 0.244651 | 0.261268 | 1.0 | 1.067923 | 1.0193 | `False` |
| `くるくる` | 0.387762 | 0.411926 | 1.0 | 1.062318 | 1.017879 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.

### food_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"food_cooking": 1.0}`
- Matching signals: `9` / aggregate items `129`
- Candidate pool: `10951`
- Strong added vs off: `作成, クリーム, 注文, 立派`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 16.34127 | 酒, 味, 茶, パン, 焼く, 肉, コーヒー, ビール |
| `balanced` | 2 | 2 | 16.34127 | 作成, クリーム, 酒, 味, 茶, パン, 焼く, 肉 |
| `strong` | 4 | 4 | 16.34127 | 作成, クリーム, 注文, 立派, 酒, 味, 茶, パン |

Strong browsing rows:

| Target | Raw | Effective | Quality | Specificity | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `作成|さくせい` | 0.489301 | 0.453978 | 1.0 | 0.927808 | 1.090243 | `True` |
| `クリーム|くりーむ` | 0.632412 | 0.620974 | 1.0 | 0.981913 | 1.093506 | `True` |
| `注文|ちゅうもん` | 0.53365 | 0.522812 | 1.0 | 0.979691 | 1.080135 | `True` |
| `立派|りっぱ` | 0.568061 | 0.557686 | 1.0 | 0.981737 | 1.071786 | `True` |
| `旦那|だんな` | 0.244651 | 0.236788 | 1.0 | 0.96786 | 1.038816 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 0.463741 | 1.0 | 0.947763 | 1.080771 | `False` |
| `鍵|かぎ` | 0.244651 | 0.240168 | 1.0 | 0.981678 | 1.036383 | `False` |
| `酢|す` | 0.244651 | 0.242684 | 1.0 | 0.991961 | 1.034518 | `False` |
| `兎|うさぎ` | 0.334165 | 0.341835 | 1.0 | 1.022952 | 1.039086 | `False` |
| `瓶|びん` | 0.244651 | 0.245569 | 1.0 | 1.003756 | 1.032322 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.

### animals_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"animals": 1.0}`
- Matching signals: `9` / aggregate items `129`
- Candidate pool: `10951`
- Strong added vs off: `鹿, 作成, クリーム`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 16.34127 | 馬, 犬, 虫, 牛, 猿, 熊, 虎, 兎 |
| `balanced` | 2 | 1 | 16.34127 | 兎, 鹿, 馬, 犬, 虫, 牛, 猿, 熊 |
| `strong` | 4 | 3 | 16.34127 | 兎, 鹿, 作成, クリーム, 馬, 犬, 虫, 牛 |

Strong browsing rows:

| Target | Raw | Effective | Quality | Specificity | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `兎|うさぎ` | 0.334165 | 0.341835 | 1.0 | 1.022952 | 1.048858 | `True` |
| `鹿|しか` | 0.244651 | 0.256539 | 1.0 | 1.048594 | 1.029266 | `True` |
| `作成|さくせい` | 0.489301 | 0.453978 | 1.0 | 0.927808 | 1.090243 | `True` |
| `クリーム|くりーむ` | 0.632412 | 0.620974 | 1.0 | 0.981913 | 1.093506 | `True` |
| `注文|ちゅうもん` | 0.53365 | 0.522812 | 1.0 | 0.979691 | 1.080135 | `False` |
| `立派|りっぱ` | 0.568061 | 0.557686 | 1.0 | 0.981737 | 1.071786 | `False` |
| `旦那|だんな` | 0.244651 | 0.236788 | 1.0 | 0.96786 | 1.038816 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 0.463741 | 1.0 | 0.947763 | 1.080771 | `False` |
| `鍵|かぎ` | 0.244651 | 0.240168 | 1.0 | 0.981678 | 1.036383 | `False` |
| `酢|す` | 0.244651 | 0.242684 | 1.0 | 0.991961 | 1.034518 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.

## Findings

| Level | Code | Message |
| --- | --- | --- |
| `PASS` | `ALL_SCENARIOS_PASS` | All saved-page browsing admission scenarios satisfied configured expectations. |
