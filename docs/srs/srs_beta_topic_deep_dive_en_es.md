# en-es SRS Beta Topic Deep Dive

Status: current analysis
Last updated: 2026-05-27
Scope: `plants_nature` and `travel_places_transport`
Inputs:

- `../test_outputs/srs_topic_release_readiness_en_es_latest.md`
- `../test_outputs/srs_topic_family_depth_audit_en_es_latest.md`
- `../test_outputs/srs_admission_calibration_en_es_latest.md`
- `../test_outputs/srs_animals_plants_topic_overlay_poc_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_source_topic_precision_review_en_es_spalex_10k_latest.md`
- `srs_topic_mvp_recommendations_en_es.md`

## Bottom Line

Neither beta topic currently looks like an admission-algorithm failure.

Both beta topics match the reserved topic-lane expectation in the latest
calibration report:

| Topic | Reserved-lane observed | Expected | Status |
| --- | ---: | ---: | --- |
| `plants_nature` | `5 / 10` | `5 / 10` | `matches` |
| `travel_places_transport` | `5 / 10` | `5 / 10` | `matches` |

The failure risk is content quality and depth:

- `plants_nature` is likely to feel shallow because there are too few reviewed
  rows and only one release-readiness difficulty band.
- `travel_places_transport` is likely to feel uneven because broad source
  labels such as geography, nautical, and transport contain real travel words
  mixed with obscure or secondary-sense words.

## Failure Modes

Use these definitions when deciding whether beta topics can ship:

| Failure mode | Meaning | Current result |
| --- | --- | --- |
| Selector failure | The topic preference does not move matching words into admission as expected. | Low risk for both topics. Calibration matches expected counts. |
| Capacity failure | There are too few eligible topic candidates to fill the reserved lane. | Low immediate risk for both topics. Plants has `28` active support candidates in the calibration report; travel has `30`. |
| Depth failure | The topic works for one narrow difficulty band but does not support smooth progression. | High risk for both topics. Release readiness reports one source difficulty band for each. |
| Precision failure | Topic evidence promotes words that do not feel like the topic in the user's expected sense. | Moderate for plants; high for source-derived travel labels, lower for the curated travel overlay. |
| Product-expectation failure | The user sees the topic as a polished course/catalogue and expects broad coverage. | High if exposed without beta/limited copy. |

## Plants / Nature

Recommendation: keep as beta/optional unless the picker can clearly label it as
limited. Do not present it as a fully polished nature or gardening catalogue.

Evidence:

- Release status: `beta_limited_candidate`.
- Recommended visibility: `beta_visible_or_hidden`.
- Effective candidates: `34`.
- Source trusted candidates: `29`.
- Reviewed overlay candidates: `34`.
- Source non-empty difficulty bands: `1`.
- Source max difficulty: `0.151442`.
- Calibration reserved lane: observed `5 / 10`, expected `5 / 10`.
- Ranked preview can surface obvious plant words such as `haya`, `árbol`,
  `flor`, `hierba`, `col`, `pino`, `parra`, `plátano`, `roble`, and
  `calabaza`.

Certainty:

- Selector failure: low certainty. The selector is doing what the policy says.
- MVP-normal-topic failure: high certainty if exposed with no caveat. The
  release gate objectively marks it beta-limited, and the inventory has only
  one difficulty band.
- Beta-topic failure: medium. It can probably work as a small/limited interest,
  but users who love plants may exhaust or notice repetition quickly.

Likely causes:

1. The trusted source surface for plants is narrow. Current strong evidence is
   mostly botany/plant-name evidence, not broad nature vocabulary.
2. Difficulty depth is shallow in the release frontier. The topic is mostly
   easy/common according to the current release-readiness scoring.
3. The topic overlaps naturally with food/cooking for fruits, vegetables, and
   crops. That overlap is acceptable, but it means plants/nature may not feel
   distinct unless the topic has enough trees, flowers, gardening, landscape,
   and botany terms.
4. Several candidates are polysemous or awkward as user-facing nature examples,
   such as `haya`, `col`, `calabaza`, `marrón`, `naranja`, or `rosa`.

Expected improvement work:

| Work | Goal | Estimate |
| --- | --- | --- |
| Sample precision review for the merged plants overlay | Remove or down-rank obvious polysemy/food-only pollution. | Small, hours. |
| Add `20-40` reviewed high-confidence plant/nature rows | Reach the limited-release floor and reduce repetition. | Small to medium, about half a day to one day if sources are ready. |
| Add difficulty-band enrichment | Add mid/harder trees, plants, landscape, gardening, and botany terms so high-proficiency users do not get only easy words. | Medium, one to two days depending on source quality. |
| Decide overlap policy with food/cooking | Allow dual tags for crops/fruits, but keep plants/nature examples from feeling like only grocery vocabulary. | Small product/policy decision. |

Best source directions:

- Continue using reviewed Wikidata/natural-taxonomy rows for plant entities.
- Add a small curated, source-backed list of common tree, flower, garden, and
  landscape vocabulary.
- Prefer reviewed lemma lists only; meanings should still come from existing
  LexiShift dictionary/frequency sources.

Promotion target:

- Minimum for ordinary limited release: `>= 50` effective reviewed rows and at
  least `2` difficulty bands.
- Better target before calling it polished: `75-100` reviewed rows with examples
  across easy, mid, and harder bands.

## Travel / Places / Transport

Recommendation: beta/optional is reasonable if beta topics are exposed. If the
first tester experience should be conservative, keep it hidden until a direct
travel overlay is expanded and broad source-label noise is reduced.

Evidence:

- Release status: `beta_limited_candidate`.
- Recommended visibility: `beta_visible_or_hidden`.
- Effective candidates: `132`.
- Source trusted candidates: `132`.
- Reviewed overlay candidates: `30`.
- Source non-empty difficulty bands: `1`.
- Source max difficulty: `0.167956`.
- Source precision review: `7 / 9` accepted, `2 / 9` rejected.
- Calibration reserved lane: observed `5 / 10`, expected `5 / 10`.
- Curated/obvious overlay examples include `aeropuerto`, `albergue`,
  `alojamiento`, `autobús`, `avión`, `barco`, `billete`, `calle`, `camino`,
  `carretera`, `ciudad`, `equipaje`, `hotel`, `mapa`, `pasaporte`, `país`,
  `taxi`, `viajar`, `viaje`, `visado`, and `vuelo`.

Certainty:

- Selector failure: low certainty. The selector is doing what the policy says.
- MVP-normal-topic failure: medium-high. The first batch looks good, but the
  release gate marks the topic beta-limited because the depth signal is shallow
  and the runtime overlay has only `30` reviewed direct rows.
- Precision failure from broad source labels: high enough to matter. The source
  precision review rejected examples such as `plutón` and `bonanza`, and
  marked several accepted examples as light/specialized rather than clean
  travel vocabulary.
- Beta-topic failure: low-medium. It is more viable than plants as a beta topic
  because the obvious travel overlay has many intuitive user-facing words.

Likely causes:

1. The parent family is broad: travel, places, geography, nautical, aerospace,
   vehicles, and transport are related but not identical.
2. Source labels include secondary or obscure senses. Examples already rejected
   include planet/geography and narrow nautical meanings.
3. The curated direct travel overlay is good but small: `30` rows.
4. The release-readiness depth artifact still sees only one difficulty band,
   so the topic may skew toward obvious/common travel words.

Expected improvement work:

| Work | Goal | Estimate |
| --- | --- | --- |
| Expand the direct travel overlay from `30` rows to `50-75` rows | Make the topic viable without relying heavily on noisy geography/nautical labels. | Small to medium, half a day to one day. |
| Tighten broad label promotion | Demote or require review for geography/nautical/transport labels that are secondary-sense or non-travel. | Medium, one day. |
| Add difficulty-band enrichment | Add mid/harder but still ordinary travel terms, not obscure nautical/geology terms. | Medium, one to two days. |
| Consider split or copy refinement | Decide whether the UX says "Travel & Transport" rather than the broader "Travel, Places & Transport". | Small product decision. |

Best source directions:

- Keep the current direct overlay path for obvious travel vocabulary.
- Use reviewed public word lists only for lemmas, with meanings still resolved
  through existing LexiShift sources.
- Treat raw geography/nautical/transport labels as candidate evidence, not
  automatic strong topic evidence.

Promotion target:

- Minimum for ordinary limited release: `>= 50` direct or reviewed runtime rows
  and at least `2` difficulty bands.
- Better target before calling it polished: `75-100` reviewed direct travel
  rows, with a clear policy for geography/place names and transport jargon.

## Recommendations

1. Do not classify either beta topic as a selector failure.
2. Keep both out of the default polished topic set unless the UI has a beta or
   limited-depth affordance.
3. If only one beta topic is exposed, expose `travel_places_transport` first.
   Its first-batch examples are more obviously aligned with user expectations.
4. Do not expose `plants_nature` as an ordinary topic until it has at least
   limited-release depth. It is important, but still too shallow for confident
   normal exposure.
5. The fastest useful improvement is not algorithm work. It is curated/reviewed
   overlay expansion plus regeneration of:
   - `srs_topic_release_readiness_en_es_latest`
   - `srs_admission_calibration_en_es_latest`
   - a focused lab smoke at multiple proficiency values.

## Decision Threshold

Move a beta topic into the ordinary MVP-visible set when all are true:

1. Release readiness is at least `limited_release_candidate`.
2. Runtime/reviewed overlay rows are at least `50`.
3. Source or overlay depth covers at least `2` difficulty bands.
4. Reserved topic-lane calibration still matches expected count.
5. Manual lab review does not show obvious clumping, repetition, or sense
   pollution in the first few batches.
