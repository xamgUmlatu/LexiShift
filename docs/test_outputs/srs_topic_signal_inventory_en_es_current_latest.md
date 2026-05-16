# en-es SRS Topic Signal Inventory

- Status: `ok`
- Decision: `srs_topic_signal_inventory_completed`
- Generated: `2026-05-16T19:37:11+00:00`
- Candidate packs: `1`

## Scope

This is a read-only inventory of topic/tag/category signals available for SRS enrichment. It does not write overlays, change SRS admission, or promote any new preference category.

## Findings

- `PASS` `kaikki_signal_source_available`: Kaikki/Wiktionary signal DB exists.
- `PASS` `trusted_topics_available:current_cde`: Explicit sense-topic rows can enrich this candidate pack.
- `PASS` `review_only_signals_expand_surface:current_cde`: Tags/categories expose more candidate rows, but require mapping before use.

## Candidate Audits

### `current_cde`

- exists: `True`
- rows: `2000`
- unique lemmas: `1984`
- trusted profile signal rows: `234` (11.8%)
- review-only signal rows: `1890` (95.3%)
- any available signal rows: `1890` (95.3%)

#### Channel Coverage

| Channel | Policy | Rows | Share | Distinct Topics | Top Topics |
| --- | --- | ---: | ---: | ---: | --- |
| `sense_topics` | `trusted_profile_signal` | 234 | 11.8% | 137 | sciences=78, lifestyle=69, natural_sciences=59, medicine=42, hobbies=41 |
| `sense_tags` | `review_only_inventory_signal` | 1526 | 76.9% | 113 | masculine=887, feminine=667, transitive=149, by_personal_gender=95, colloquial=64 |
| `sense_categories` | `review_only_inventory_signal` | 1395 | 70.3% | 1326 | pages_with_entries=833, spanish_entries_with_incorrect_language_header=833, spanish_lemmas=832, spanish_terms_with_ipa_pronunciation=764, spanish_nouns=407 |
| `entry_tags` | `review_only_inventory_signal` | 0 | 0.0% | 0 | none |
| `entry_categories` | `review_only_inventory_signal` | 1110 | 55.9% | 1678 | pages_with_entries=1110, spanish_entries_with_incorrect_language_header=1095, spanish_lemmas=1095, spanish_terms_with_ipa_pronunciation=1072, spanish_nouns=765 |

#### Top Trusted Topics

| Topic | Count |
| --- | ---: |
| `sciences` | 78 |
| `lifestyle` | 69 |
| `natural_sciences` | 59 |
| `medicine` | 42 |
| `hobbies` | 41 |
| `physical_sciences` | 34 |
| `sports` | 33 |
| `finance` | 24 |
| `government` | 24 |
| `games` | 24 |
| `business` | 23 |
| `politics` | 22 |
| `engineering` | 21 |
| `mathematics` | 20 |
| `entertainment` | 20 |
| `anatomy` | 20 |
| `human_sciences` | 17 |
| `music` | 15 |
| `law` | 15 |
| `ball_games` | 15 |

#### Product Topic Examples

| Topic | Trusted Count | Review-Only Count |
| --- | ---: | ---: |
| `medicine` | 42 | 0 |
| `finance` | 24 | 0 |
| `business` | 23 | 0 |
| `sports` | 33 | 0 |
| `games` | 24 | 0 |
| `music` | 15 | 0 |
| `literature` | 3 | 0 |
| `psychology` | 1 | 0 |
| `education` | 2 | 0 |
| `law` | 15 | 0 |
| `politics` | 22 | 0 |
| `technology` | 1 | 0 |
| `computing` | 8 | 0 |
| `food` | 2 | 0 |

## Planned Preference Families

- product topic examples: `medicine, health, finance, business, sports, games, music, literature, psychology, education, law, politics, technology, computing, science, travel, food, emotions`
- exam preferences requiring source/legal review: `sat, toefl`
- exam policy: SAT and TOEFL should be preference families only after a legal source decision identifies allowed vocabulary/skill data. They are not inferred from current Wiktionary topic labels.

## Limitations

- This audit inventories available signals only; it does not create a normalized topic overlay.
- Kaikki categories are broad and noisy, so they should not be promoted into profile topics without allowlist mapping and sample review.
- SAT and TOEFL preferences need legally allowed exam-prep source data or an internally defined skill taxonomy before product use.
- Counts depend on the installed local Kaikki/Wiktionary pack and should be refreshed when that resource changes.
