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
- Matching signals: `9` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 2.281747 | 無い, 出来る, 良く, 彼女, 矢張り, 共, 規定, センター |
| `balanced` | 1 | 1 | 2.281746 | クリーム, 無い, 出来る, 良く, 彼女, 矢張り, 共, 規定 |
| `strong` | 2 | 2 | 2.281746 | クリーム, 立派, 無い, 出来る, 良く, 彼女, 矢張り, 共 |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.629384 | 4.94873 | 0 | 1.0 | 0.983016 | 1.0 | 0.981913 | 0.607504 | 1.091478 | `True` |
| `立派|りっぱ` | 0.565154 | 3.958984 | 0 | 1.0 | 0.785745 | 1.0 | 0.981737 | 0.435957 | 1.056117 | `True` |
| `注文|ちゅうもん` | 0.530817 | 3.499282 | 0 | 1.0 | 0.687702 | 1.0 | 0.979691 | 0.357631 | 1.054817 | `False` |
| `作成|さくせい` | 0.486576 | 2.969238 | 0 | 0.0 | 0.453002 | 1.0 | 0.927808 | 0.0 | 1.0 | `False` |
| `旦那|だんな` | 0.242836 | 0.989746 | 0 | 0.0 | 0.183675 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `鍵|かぎ` | 0.242836 | 0.989746 | 0 | 0.0 | 0.196381 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.242836 | 0.989746 | 0 | 0.0 | 0.202567 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |
| `酢|す` | 0.242836 | 0.989746 | 0 | 0.0 | 0.20627 | 1.0 | 0.991961 | 0.0 | 1.0 | `False` |
| `瓶|びん` | 0.242836 | 0.989746 | 0 | 0.0 | 0.218011 | 1.0 | 1.003756 | 0.0 | 1.0 | `False` |
| `否|いな` | 0.242836 | 0.989746 | 0 | 0.0 | 0.219311 | 1.0 | 1.005039 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### neutral_p50_saved_pages

- Status: `pass`
- Proficiency: `0.5`
- Topic weights: `{}`
- Matching signals: `9` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `香水, 立派`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 2.281742 | 御座る, 旨い, 我々, なお, 当該, 積り, 成す, レベル |
| `balanced` | 1 | 1 | 2.281742 | 香水, 御座る, 旨い, 我々, なお, 当該, 積り, 成す |
| `strong` | 2 | 2 | 2.281742 | 香水, 立派, 御座る, 旨い, 我々, なお, 当該, 積り |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `香水|こうすい` | 0.530817 | 3.499277 | 0 | 1.0 | 0.971166 | 1.0 | 1.058472 | 0.545654 | 1.044948 | `True` |
| `立派|りっぱ` | 0.565153 | 3.958979 | 0 | 1.0 | 0.785744 | 1.0 | 0.981737 | 0.435956 | 1.032266 | `True` |
| `壺|つぼ` | 0.242836 | 0.989745 | 0 | 0.0 | 0.23682 | 1.0 | 1.022018 | 0.0 | 1.0 | `False` |
| `鉄砲|てっぽう` | 0.242836 | 0.989745 | 0 | 0.0 | 0.256276 | 1.0 | 1.040581 | 0.0 | 1.0 | `False` |
| `団子|だんご` | 0.242836 | 0.989745 | 0 | 0.0 | 0.256495 | 1.0 | 1.04079 | 0.0 | 1.0 | `False` |
| `紳士|しんし` | 0.242836 | 0.989745 | 0 | 0.0 | 0.256495 | 1.0 | 1.04079 | 0.0 | 1.0 | `False` |
| `煉瓦|れんが` | 0.242836 | 0.989745 | 0 | 0.0 | 0.258146 | 1.0 | 1.042371 | 0.0 | 1.0 | `False` |
| `鹿|しか` | 0.242836 | 0.989745 | 0 | 0.0 | 0.26461 | 1.0 | 1.048594 | 0.0 | 1.0 | `False` |
| `くるくる` | 0.385341 | 1.979489 | 0 | 0.0 | 0.557045 | 1.0 | 1.062318 | 0.0 | 1.0 | `False` |
| `錠|じょう` | 0.242836 | 0.989745 | 0 | 0.0 | 0.283998 | 1.0 | 1.067923 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### food_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"food_cooking": 1.0}`
- Matching signals: `9` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 2.281738 | 酒, 味, 茶, パン, 焼く, 肉, コーヒー, ビール |
| `balanced` | 1 | 1 | 2.281737 | クリーム, 酒, 味, 茶, パン, 焼く, 肉, コーヒー |
| `strong` | 2 | 2 | 2.281737 | クリーム, 立派, 酒, 味, 茶, パン, 焼く, 肉 |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.629383 | 4.948717 | 0 | 1.0 | 0.983013 | 1.0 | 0.981913 | 0.607501 | 1.091477 | `True` |
| `立派|りっぱ` | 0.565153 | 3.958974 | 0 | 1.0 | 0.785743 | 1.0 | 0.981737 | 0.435955 | 1.056117 | `True` |
| `注文|ちゅうもん` | 0.530816 | 3.499272 | 0 | 1.0 | 0.687701 | 1.0 | 0.979691 | 0.357629 | 1.054817 | `False` |
| `作成|さくせい` | 0.486575 | 2.96923 | 0 | 0.0 | 0.453001 | 1.0 | 0.927808 | 0.0 | 1.0 | `False` |
| `旦那|だんな` | 0.242836 | 0.989743 | 0 | 0.0 | 0.183674 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `鍵|かぎ` | 0.242836 | 0.989743 | 0 | 0.0 | 0.19638 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.242836 | 0.989743 | 0 | 0.0 | 0.202566 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |
| `酢|す` | 0.242836 | 0.989743 | 0 | 0.0 | 0.206269 | 1.0 | 0.991961 | 0.0 | 1.0 | `False` |
| `瓶|びん` | 0.242836 | 0.989743 | 0 | 0.0 | 0.21801 | 1.0 | 1.003756 | 0.0 | 1.0 | `False` |
| `否|いな` | 0.242836 | 0.989743 | 0 | 0.0 | 0.21931 | 1.0 | 1.005039 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

### animals_p35_saved_pages

- Status: `pass`
- Proficiency: `0.35`
- Topic weights: `{"animals": 1.0}`
- Matching signals: `9` / aggregate items `124`
- Candidate pool: `10951`
- Strong added vs off: `クリーム, 立派`
- Hygiene rejected candidate matches: `0`
- Hygiene rejected selected: `0`

| Strength | Browsing lane | Driven | Signal volume | Selected |
| --- | ---: | ---: | ---: | --- |
| `off` | 0 | 0 | 2.281733 | 馬, 犬, 虫, 牛, 猿, 熊, 虎, 兎 |
| `balanced` | 1 | 1 | 2.281732 | クリーム, 馬, 犬, 虫, 牛, 猿, 熊, 虎 |
| `strong` | 2 | 2 | 2.281732 | クリーム, 立派, 馬, 犬, 虫, 牛, 猿, 熊 |

Strong browsing rows:

| Target | Signal | Evidence | Ctx | Count | Salience | Quality | Specificity | Effective | Boost | Selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `クリーム|くりーむ` | 0.629382 | 4.948709 | 0 | 1.0 | 0.983012 | 1.0 | 0.981913 | 0.6075 | 1.091477 | `True` |
| `立派|りっぱ` | 0.565152 | 3.958968 | 0 | 1.0 | 0.785742 | 1.0 | 0.981737 | 0.435954 | 1.056117 | `True` |
| `兎|うさぎ` | 0.331943 | 1.561169 | 0 | 0.0 | 0.375086 | 1.0 | 1.022952 | 0.0 | 1.0 | `False` |
| `鹿|しか` | 0.242836 | 0.989742 | 0 | 0.0 | 0.264609 | 1.0 | 1.048594 | 0.0 | 1.0 | `False` |
| `注文|ちゅうもん` | 0.530816 | 3.499267 | 0 | 1.0 | 0.6877 | 1.0 | 0.979691 | 0.357628 | 1.054817 | `False` |
| `作成|さくせい` | 0.486575 | 2.969226 | 0 | 0.0 | 0.453 | 1.0 | 0.927808 | 0.0 | 1.0 | `False` |
| `旦那|だんな` | 0.242836 | 0.989742 | 0 | 0.0 | 0.183674 | 1.0 | 0.96786 | 0.0 | 1.0 | `False` |
| `鍵|かぎ` | 0.242836 | 0.989742 | 0 | 0.0 | 0.19638 | 1.0 | 0.981678 | 0.0 | 1.0 | `False` |
| `折角|せっかく` | 0.242836 | 0.989742 | 0 | 0.0 | 0.202566 | 1.0 | 0.988152 | 0.0 | 1.0 | `False` |
| `酢|す` | 0.242836 | 0.989742 | 0 | 0.0 | 0.206269 | 1.0 | 0.991961 | 0.0 | 1.0 | `False` |

Findings:
- `PASS` `MONOTONIC_STRENGTH`: Browsing lane share is monotonic.
- `PASS` `PREVIEW_ONLY`: Browsing preview did not mutate SRS.
- `PASS` `STRONG_BROWSING_LANE`: Strong preset realized browsing lane.
- `PASS` `MIN_MATCHING_SIGNAL_COUNT`: Saved-page aggregate matched enough real admission candidates (9 >= 5).
- `PASS` `EFFECTIVE_SIGNAL_FIELDS_PRESENT`: Strong preview rows expose raw and effective browsing signal fields.
- `PASS` `HYGIENE_REJECTED_SIGNALS_NOT_SELECTED`: No hygiene-rejected saved-page signals were selected.

## Findings

| Level | Code | Message |
| --- | --- | --- |
| `PASS` | `ALL_SCENARIOS_PASS` | All saved-page browsing admission scenarios satisfied configured expectations. |
