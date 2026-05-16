# en-es SRS Topic Preference Decision Matrix

Status: active decision aid
Role: Planning / WIP
Last updated: 2026-05-17
Last verified: 2026-05-17 from `srs_topic_signal_inventory_en_es_current_latest`
Purpose: lay out the current trusted source-topic surface so product preferences can be selected deliberately
Source-of-truth: decision aid; executable inventory lives in `scripts/testing/srs_topic_signal_inventory_en_es.py` and the latest generated artifacts.

Related docs:
- `srs_interest_tailored_data_acquisition_plan.md`
- `srs_interest_tailored_admission_algorithm.md`
- `../test_outputs/srs_topic_signal_inventory_en_es_current_latest.md`

## Decision Frame

The current installed `freq-es-cde` pack has no native topic columns. The
installed Kaikki/Wiktionary pack can still enrich it with explicit
`sense_topics` for `234 / 1,984` current CDE lemmas (`11.8%`).

That gives us a real topic surface, but it is not a finished product taxonomy.
The product taxonomy should be ours:

1. choose user-facing preference families,
2. map source labels into those families,
3. assign confidence/weight per mapping,
4. keep unsupported or legally gated preferences unavailable until sourced.

Use these source channels differently:

| Source Channel | Current Use | Reason |
| --- | --- | --- |
| `sense_topics` | Candidate source for product-topic mappings | Sense-level labels are the cleanest currently installed topic signal. |
| `sense_tags`, `sense_categories`, `entry_tags`, `entry_categories` | Review-only inventory | These channels are broad and noisy: grammar, register, maintenance categories, and Wiktionary housekeeping dominate. |
| SAT/TOEFL source data | Not present yet | These are product-aligned only after legal/source review identifies allowed data. |

## Recommended Product Preference Families

This is the practical v0 shortlist. "Adopt" means the topic family is plausible
as a product preference once the mapping file, source provenance, and tests are
in place. It does not mean the current app behavior changes now.

| Product Preference Family | Source Labels In Current Trusted Data | Current CDE Support | Proposed Decision | Notes |
| --- | --- | ---: | --- | --- |
| `medicine_health` | `medicine` 42, `anatomy` 20, `pathology` 7, `dentistry` 2, `healthcare` 1, `physiology` 1, `oncology` 1, `pharmacology` 1 | strong | Adopt v0 | Best first vertical. Use exact `medicine` as high confidence; child labels can add scalar lift. |
| `finance_business` | `finance` 24, `business` 23, `economics` 2, `banking` 1, `accounting` 1, `management` 1 | strong | Adopt v0 | Clear user value and clean product framing. |
| `sports_fitness` | `sports` 33, `ball_games` 15, `soccer` 8, `baseball` 3, `basketball` 3, `exercise` 2, `martial_arts` 2, `boxing` 1, `swimming` 1 | strong | Adopt v0 | Keep as one family first; split by sport only if later data justifies it. |
| `games` | `games` 24, `card_games` 5, `video_games` 2, `gaming` 1 | medium | Adopt v0 | Distinct from sports; useful for user interest personalization. |
| `law_politics_civics` | `government` 24, `politics` 22, `law` 15 | strong | Adopt v0 | Consider exposing `law` and `politics` separately if UX has room. |
| `music_media_entertainment` | `entertainment` 20, `music` 15, `media` 9, `publishing` 5, `broadcasting` 3, `theater` 2, `television` 2, `film` 1, `radio` 1 | strong | Adopt v0 | Product could expose `music` separately and keep the others under media/entertainment. |
| `science_technology` | `sciences` 78, `natural_sciences` 59, `physical_sciences` 34, `engineering` 21, `mathematics` 20, `biology` 13, `physics` 10, `chemistry` 10, `computing` 8 | strong | Adopt as parent family | High coverage, but broad labels should have lower confidence than specific labels such as `computing` or `chemistry`. |
| `travel_places_transport` | `geography` 14, `transport` 11, `nautical` 9, `aerospace` 3, `aeronautics` 2, `aviation` 2, `automotive` 1, `vehicles` 1 | medium | Adopt as parent family | This is the closest current source surface to travel. It needs aliases and maybe a future travel-domain overlay. |
| `arts_literature_humanities` | `arts` 5, `art` 3, `literature` 3, `history` 3, `philosophy` 7, `architecture` 4, `linguistics` 7 | medium | Adopt as parent family | Literature alone is sparse in current CDE; humanities as a parent is more viable. |
| `education_academic` | `education` 2, `higher_education` 1, plus possible academic aliases from `grammar`, `linguistics`, `mathematics`, and `sciences` | weak | Defer or parent-only | Needs a clearer taxonomy before becoming user-facing. |
| `food_cooking` | `food` 2, `cooking` 2 | weak | Defer until expansion | Product-aligned, but current trusted support is too small for a meaningful current-CDE preference. |
| `psychology_emotions` | `psychology` 1, `human_sciences` 17 | weak | Defer until overlay | Emotions are product-aligned but not directly present in trusted current-CDE topics. |
| `animals_nature` | `animals` 1, `zoology` 1, `botany` 5, plus broader natural-science labels | weak | Defer or map under science | Needs more direct animal/nature support before user-facing use. |
| `sat_toefl_exam_prep` | none in current trusted source data | none | Legal/source gated | Add only after allowed vocabulary, skill, or exam-prep data is identified. Do not infer from current Wiktionary labels. |

## Labels That Should Not Become User Preferences Directly

Some labels are useful internally but should not appear directly as user
preferences in v0:

| Source Label Type | Examples | Recommended Use |
| --- | --- | --- |
| Broad parent labels | `sciences`, `natural_sciences`, `physical_sciences`, `human_sciences`, `lifestyle`, `hobbies` | Parent/weighting labels only. Do not treat as precise interests. |
| Narrow niche labels | `heraldry`, `monarchy`, `nobility`, `bullfighting`, `pool`, `snooker` | Map only if a product family needs them; otherwise defer. |
| Sensitive or policy-sensitive labels | `sex`, `sexuality`, `firearms`, `weaponry`, `war`, `military` | Defer from default UX; require explicit policy decision before exposure. |
| Internal linguistic labels | `grammar`, `typography`, `linguistics` | Useful for academic/language-learning overlays, but not a general user preference by default. |
| Noisy non-topic channels | grammatical tags, register tags, Wiktionary maintenance categories | Keep review-only until allowlisted and sampled. |

## First Mapping Shape

The mapping layer should be explicit and scalar. A source label can contribute
to more than one product topic, and broad labels should contribute less than
specific labels.

Example:

```json
{
  "source_label": "anatomy",
  "source_channel": "sense_topics",
  "product_topics": {
    "medicine_health": 0.75,
    "science_technology": 0.25
  },
  "confidence": 0.80,
  "policy": "trusted_sense_topic_mapping_v1"
}
```

Suggested initial confidence pattern:

| Mapping Type | Example | Suggested Weight |
| --- | --- | ---: |
| Exact domain to product family | `medicine` -> `medicine_health` | `0.90` |
| Child domain to product family | `pathology` -> `medicine_health` | `0.75` |
| Broad parent to product family | `sciences` -> `science_technology` | `0.35` |
| Ambiguous or polysemous source label | `lifestyle`, `hobbies` | `0.00` until reviewed |
| Legally gated exam prep | `sat`, `toefl` | unavailable until sourced |

## Suggested v0 Decision

Adopt these first as user-facing or near-user-facing preferences:

- `medicine_health`
- `finance_business`
- `sports_fitness`
- `games`
- `law_politics_civics`
- `music_media_entertainment`
- `science_technology`
- `travel_places_transport`
- `arts_literature_humanities`

Keep these as planned but not current-CDE-ready:

- `education_academic`
- `food_cooking`
- `psychology_emotions`
- `animals_nature`
- `sat_toefl_exam_prep`

## Complete Trusted Current-CDE Source Topic List

These are all `137` canonical `sense_topics` found by joining current CDE lemmas
to installed Kaikki/Wiktionary. Counts are lemma counts within the current
`1,984`-lemma CDE surface.

### Count 10+

`sciences` (78), `lifestyle` (69), `natural_sciences` (59), `medicine` (42),
`hobbies` (41), `physical_sciences` (34), `sports` (33), `finance` (24),
`government` (24), `games` (24), `business` (23), `politics` (22),
`engineering` (21), `mathematics` (20), `entertainment` (20), `anatomy` (20),
`human_sciences` (17), `music` (15), `law` (15), `ball_games` (15),
`geography` (14), `biology` (13), `transport` (11), `physics` (10),
`chemistry` (10).

### Count 5-9

`military` (9), `nautical` (9), `war` (9), `media` (9), `soccer` (8),
`heraldry` (8), `monarchy` (8), `nobility` (8), `computing` (8),
`geology` (8), `electrical_engineering` (7), `linguistics` (7),
`philosophy` (7), `pathology` (7), `electricity` (6),
`electromagnetism` (6), `energy` (6), `electronics` (5), `botany` (5),
`publishing` (5), `card_games` (5), `arts` (5).

### Count 2-4

`architecture` (4), `geometry` (4), `grammar` (4), `mysticism` (4),
`mythology` (4), `art` (3), `linear_algebra` (3), `history` (3),
`literature` (3), `aerospace` (3), `religion` (3), `bullfighting` (3),
`agriculture` (3), `christianity` (3), `broadcasting` (3), `baseball` (3),
`basketball` (3), `manufacturing` (3), `education` (2), `typography` (2),
`video_games` (2), `climbing` (2), `folklore` (2), `aeronautics` (2),
`aviation` (2), `astronomy` (2), `dentistry` (2), `exercise` (2),
`economics` (2), `cooking` (2), `food` (2), `theater` (2),
`television` (2), `cosmetics` (2), `genetics` (2), `textiles` (2),
`metallurgy` (2), `mineralogy` (2), `sex` (2), `sexuality` (2),
`martial_arts` (2).

### Count 1

`banking` (1), `american_football` (1), `football` (1), `bowling` (1),
`mechanical_engineering` (1), `mechanics` (1), `technology` (1),
`gaming` (1), `higher_education` (1), `film` (1), `animals` (1),
`zoology` (1), `oncology` (1), `psychology` (1), `accounting` (1),
`astronautics` (1), `communications` (1), `graphical_user_interface` (1),
`telecommunications` (1), `telephony` (1), `hydrography` (1),
`hydrology` (1), `oceanography` (1), `healthcare` (1), `physiology` (1),
`automotive` (1), `vehicles` (1), `climatology` (1), `meteorology` (1),
`weather` (1), `construction` (1), `fantasy` (1), `mining` (1),
`management` (1), `archaeology` (1), `swimming` (1), `boxing` (1),
`radio` (1), `sewing` (1), `pool` (1), `snooker` (1), `firearms` (1),
`tools` (1), `weaponry` (1), `biochemistry` (1), `microbiology` (1),
`cytology` (1), `fencing` (1), `pharmacology` (1).
