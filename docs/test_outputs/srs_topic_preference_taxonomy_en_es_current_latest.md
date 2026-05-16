# en-es SRS Topic Preference Taxonomy Audit

- Status: `ok`
- Decision: `srs_topic_preference_taxonomy_validated`
- Generated: `2026-05-16T21:08:25+00:00`
- Rows measured: `1984`
- Unique lemmas measured: `1984`

## Findings

- `PASS` `schema_version_present`: Taxonomy schema is present.
- `PASS` `family_ids_unique`: Product topic family ids are unique.
- `PASS` `source_label_mappings_valid`: Source-label mappings reference known families and valid weights.
- `PASS` `excluded_labels_not_mapped_positive`: Excluded broad labels are not positively mapped.
- `PASS` `animals_nature_seed_labels_present`: Animals/nature includes the current trusted CDE seed labels.
- `PASS` `exam_prep_legal_gated`: SAT/TOEFL remains legal/source gated.
- `PASS` `animals_nature_current_signal_available`: Current installed sources provide some animals/nature seed coverage.

## Current Installed-Source Coverage

| Family | Rows | Share | Top Source Labels |
| --- | ---: | ---: | --- |
| `science_technology` | 120 | 6.0% | sciences=78, natural_sciences=59, physical_sciences=34, engineering=21, mathematics=20 |
| `medicine_health` | 43 | 2.2% | medicine=42, anatomy=20, pathology=7, dentistry=2, oncology=1 |
| `law_politics_civics` | 38 | 1.9% | government=24, politics=22, law=15 |
| `sports_fitness` | 33 | 1.7% | sports=33, ball_games=15, soccer=8, baseball=3, basketball=3 |
| `music_media_entertainment` | 28 | 1.4% | entertainment=20, music=15, media=9, publishing=5, broadcasting=3 |
| `travel_places_transport` | 27 | 1.4% | geography=14, transport=11, nautical=9, aerospace=3, aeronautics=2 |
| `finance_business` | 25 | 1.3% | business=23, finance=5, economics=2, banking=1, accounting=1 |
| `arts_literature_humanities` | 23 | 1.2% | linguistics=7, philosophy=7, arts=5, architecture=4, art=3 |
| `games` | 23 | 1.2% | games=21, card_games=5, video_games=2, gaming=1 |
| `animals_nature` | 5 | 0.3% | botany=5, zoology=1 |
| `anime_manga_pop_culture` | 0 | 0.0% | none |
| `food_cooking` | 0 | 0.0% | none |
| `hobbies_crafts` | 0 | 0.0% | none |
| `sat_toefl_exam_prep` | 0 | 0.0% | none |

## Animals/Nature Samples

| Lemma | Score | Source Labels |
| --- | ---: | --- |
| `estilo` | 0.385 | `botany` |
| `coral` | 0.7225 | `botany, zoology` |
| `vaina` | 0.385 | `botany` |
| `viudo` | 0.385 | `botany` |
| `cogollo` | 0.385 | `botany` |

## Limitations

- This report validates taxonomy shape and measures current source coverage only.
- It does not mutate frequency packs or write profile_topics overlays.
- Current coverage comes from installed Kaikki/Wiktionary sense_topics only.
- Curated overlays and embedding inference still need separate source/provenance decisions.
