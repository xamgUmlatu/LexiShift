# SRS Browsing Admission Saved-Page Admission Pack (en-ja)

- Status: `PASS`
- Scenarios: `4`
- Scenario pass/warn/fail: `4` / `0` / `0`
- Saved-page signals: `130`
- Retained after cheap hygiene: `125`
- Rejected by cheap hygiene: `5`
- Saved-page aggregate items: `124`
- Runtime scope: `preview_only_saved_page_browsing_admission`

## Interpretation

This pack starts after saved-page extraction has produced target-key browsing signals. It tests whether those signals materially affect a real en-ja profile-growth admission frontier, while remaining preview-only.

## Cheap Hygiene

This layer is intentionally narrower than the full admission quality gate. It only rejects obvious non-standalone page-surface strings before temporary aggregate ingest; normal candidate suitability still runs during admission.

| Target | Reasons | Count | Source |
| --- | --- | ---: | --- |
| `注文の多い|ちゅうもんのおおい` | `title_like_modifier_phrase` | 5.0 | `target_surface` |
| `じゃないか` | `particle_phrase_fragment` | 4.0 | `target_surface` |
| `たいもん` | `colloquial_fragment` | 4.0 | `target_surface` |
| `というのは` | `particle_phrase_fragment` | 4.0 | `target_surface` |
| `ませんでした` | `polite_inflected_tail` | 4.0 | `target_surface` |

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
| `裏側|うらがわ` | 5.0 | 0.632412 | 0.0 | 5.0 | 1.0 | `target_surface` |
| `あんまり|あまり` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `ざわざわ` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `東京|とうきょう` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `立派|りっぱ` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `行き|いき` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |
| `西洋料理|せいようりょうり` | 4.0 | 0.568061 | 0.0 | 4.0 | 1.0 | `target_surface` |

## Scenarios

### neutral_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{}`
- Matching signals: `53` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派, 注文`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 3.199282 | 無い, 出来る, 良く, 彼女, 矢張り, 共, 規定, センター |
| `balanced` | 1 | 1 | 3.199282 | クリーム, 無い, 出来る, 良く, 彼女, 矢張り, 共, 規定 |
| `strong` | 3 | 3 | 3.199282 | クリーム, 立派, 注文, 無い, 出来る, 良く, 彼女, 矢張り |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.632412 | 5.0 | 0 | 1.0 | 0.9932 | 1.0 | 0.981913 | 0.616752 | 1.09287 | `True` |
| `立派|りっぱ` | 0.568061 | 4.0 | 0 | 1.0 | 0.793886 | 1.0 | 0.981737 | 0.442739 | 1.05699 | `True` |
| `注文|ちゅうもん` | 0.53365 | 3.535535 | 0 | 1.0 | 0.694827 | 1.0 | 0.979691 | 0.363264 | 1.05568 | `True` |
| `作成|さくせい` | 0.489301 | 3.0 | 0 | 1.0 | 0.457695 | 1.0 | 0.927808 | 0.207783 | 1.041304 | `False` |
| `旦那|だんな` | 0.244651 | 1.0 | 0 | 0.0 | 0.185577 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 3.0 | 0 | 1.0 | 0.504643 | 1.0 | 0.947763 | 0.234024 | 1.040761 | `False` |
| `鍵|かぎ` | 0.244651 | 1.0 | 0 | 0.0 | 0.198415 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.244651 | 1.0 | 0 | 0.0 | 0.204665 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |
| `酢|す` | 0.244651 | 1.0 | 0 | 0.0 | 0.208407 | 1.0 | 0.991961 | 0.0 | 1.0 | `False` |
| `瓶|びん` | 0.244651 | 1.0 | 0 | 0.0 | 0.22027 | 1.0 | 1.003756 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (53 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### neutral_p50_saved_pages

- Status: `pass`
- Proficiency: `0.5`
- Topic weights: `{}`
- Matching signals: `53` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `香水, 立派, 注文`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 3.199282 | 御座る, 旨い, 我々, なお, 当該, 積り, 成す, レベル |
| `balanced` | 1 | 1 | 3.199282 | 香水, 御座る, 旨い, 我々, なお, 当該, 積り, 成す |
| `strong` | 3 | 3 | 3.199282 | 香水, 立派, 注文, 御座る, 旨い, 我々, なお, 当該 |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `香水|こうすい` | 0.53365 | 3.535535 | 0 | 1.0 | 0.981229 | 1.0 | 1.058472 | 0.55425 | 1.045656 | `True` |
| `立派|りっぱ` | 0.568061 | 4.0 | 0 | 1.0 | 0.793886 | 1.0 | 0.981737 | 0.442739 | 1.032769 | `True` |
| `注文|ちゅうもん` | 0.53365 | 3.535535 | 0 | 1.0 | 0.694827 | 1.0 | 0.979691 | 0.363264 | 1.026168 | `True` |
| `壺|つぼ` | 0.244651 | 1.0 | 0 | 0.0 | 0.239274 | 1.0 | 1.022018 | 0.0 | 1.0 | `False` |
| `鉄砲|てっぽう` | 0.244651 | 1.0 | 0 | 0.0 | 0.258931 | 1.0 | 1.040581 | 0.0 | 1.0 | `False` |
| `団子|だんご` | 0.244651 | 1.0 | 0 | 0.0 | 0.259153 | 1.0 | 1.04079 | 0.0 | 1.0 | `False` |
| `紳士|しんし` | 0.244651 | 1.0 | 0 | 0.0 | 0.259153 | 1.0 | 1.04079 | 0.0 | 1.0 | `False` |
| `煉瓦|れんが` | 0.244651 | 1.0 | 0 | 0.0 | 0.260821 | 1.0 | 1.042371 | 0.0 | 1.0 | `False` |
| `鹿|しか` | 0.244651 | 1.0 | 0 | 0.0 | 0.267352 | 1.0 | 1.048594 | 0.0 | 1.0 | `False` |
| `くるくる` | 0.387762 | 2.0 | 0 | 0.0 | 0.562817 | 1.0 | 1.062318 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (53 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### food_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"food_cooking": 1.0}`
- Matching signals: `53` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派, 注文`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 3.199282 | 酒, 味, 茶, パン, 焼く, 肉, コーヒー, ビール |
| `balanced` | 1 | 1 | 3.199282 | クリーム, 酒, 味, 茶, パン, 焼く, 肉, コーヒー |
| `strong` | 3 | 3 | 3.199282 | クリーム, 立派, 注文, 酒, 味, 茶, パン, 焼く |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.632412 | 5.0 | 0 | 1.0 | 0.9932 | 1.0 | 0.981913 | 0.616752 | 1.09287 | `True` |
| `立派|りっぱ` | 0.568061 | 4.0 | 0 | 1.0 | 0.793886 | 1.0 | 0.981737 | 0.442739 | 1.05699 | `True` |
| `注文|ちゅうもん` | 0.53365 | 3.535535 | 0 | 1.0 | 0.694827 | 1.0 | 0.979691 | 0.363264 | 1.05568 | `True` |
| `作成|さくせい` | 0.489301 | 3.0 | 0 | 1.0 | 0.457695 | 1.0 | 0.927808 | 0.207783 | 1.041304 | `False` |
| `旦那|だんな` | 0.244651 | 1.0 | 0 | 0.0 | 0.185577 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 3.0 | 0 | 1.0 | 0.504643 | 1.0 | 0.947763 | 0.234024 | 1.040761 | `False` |
| `鍵|かぎ` | 0.244651 | 1.0 | 0 | 0.0 | 0.198415 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.244651 | 1.0 | 0 | 0.0 | 0.204665 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |
| `酢|す` | 0.244651 | 1.0 | 0 | 0.0 | 0.208407 | 1.0 | 0.991961 | 0.0 | 1.0 | `False` |
| `瓶|びん` | 0.244651 | 1.0 | 0 | 0.0 | 0.22027 | 1.0 | 1.003756 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (53 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### animals_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"animals": 1.0}`
- Matching signals: `53` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派, 注文`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 3.199282 | 馬, 犬, 虫, 牛, 猿, 熊, 虎, 兎 |
| `balanced` | 1 | 1 | 3.199282 | クリーム, 馬, 犬, 虫, 牛, 猿, 熊, 虎 |
| `strong` | 3 | 3 | 3.199282 | クリーム, 立派, 注文, 馬, 犬, 虫, 牛, 猿 |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.632412 | 5.0 | 0 | 1.0 | 0.9932 | 1.0 | 0.981913 | 0.616752 | 1.09287 | `True` |
| `立派|りっぱ` | 0.568061 | 4.0 | 0 | 1.0 | 0.793886 | 1.0 | 0.981737 | 0.442739 | 1.05699 | `True` |
| `注文|ちゅうもん` | 0.53365 | 3.535535 | 0 | 1.0 | 0.694827 | 1.0 | 0.979691 | 0.363264 | 1.05568 | `True` |
| `兎|うさぎ` | 0.334165 | 1.57735 | 0 | 0.0 | 0.378974 | 1.0 | 1.022952 | 0.0 | 1.0 | `False` |
| `鹿|しか` | 0.244651 | 1.0 | 0 | 0.0 | 0.267352 | 1.0 | 1.048594 | 0.0 | 1.0 | `False` |
| `作成|さくせい` | 0.489301 | 3.0 | 0 | 1.0 | 0.457695 | 1.0 | 0.927808 | 0.207783 | 1.041304 | `False` |
| `旦那|だんな` | 0.244651 | 1.0 | 0 | 0.0 | 0.185577 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `ファイル|ふぁいる` | 0.489301 | 3.0 | 0 | 1.0 | 0.504643 | 1.0 | 0.947763 | 0.234024 | 1.040761 | `False` |
| `鍵|かぎ` | 0.244651 | 1.0 | 0 | 0.0 | 0.198415 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.244651 | 1.0 | 0 | 0.0 | 0.204665 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (53 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

## Findings

| Level | Code | Message |
| --- | --- | --- |
| `PASS` | `ALL_SCENARIOS_PASS` | All saved-page browsing admission scenarios satisfied configured expectations. |
