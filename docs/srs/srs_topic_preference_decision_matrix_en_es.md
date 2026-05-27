# en-es SRS Topic Preference Decision Matrix

Status: active decision aid
Role: Planning / WIP
Last updated: 2026-05-23
Last verified: 2026-05-23 from `srs_topic_signal_inventory_en_es_current_latest`, `srs_admission_expansion_audit_en_es_spalex_10k_latest`, `srs_topic_family_depth_audit_en_es_latest`, animals/plants overlay artifacts, food/cooking audit/review/overlay/full-source packet artifacts, Wikidata natural-taxonomy candidate and overlay artifacts, local SRS admission lab topic-depth diagnostics, topic coverage pause snapshot, and preference taxonomy lifecycle review
Purpose: lay out the current trusted source-topic surface so product preferences can be selected deliberately
Source-of-truth: decision aid; executable inventory lives in `scripts/testing/srs_topic_signal_inventory_en_es.py` and the latest generated artifacts.

Related docs:
- `srs_topic_coverage_pause_state_en_es.md`
- `srs_interest_tailored_data_acquisition_plan.md`
- `srs_interest_tailored_admission_algorithm.md`
- `srs_preference_taxonomy_lifecycle.md`
- `../test_inputs/srs_topic_preference_taxonomy_en_es.json`
- `../test_outputs/srs_topic_signal_inventory_en_es_current_latest.md`
- `../test_outputs/srs_topic_preference_taxonomy_en_es_current_latest.md`
- `../test_outputs/srs_topic_family_depth_audit_en_es_latest.md`
- `../test_outputs/srs_animals_plants_existing_signal_audit_en_es_current_latest.md`
- `../test_outputs/srs_animals_plants_existing_signal_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_food_cooking_existing_signal_audit_en_es_current_latest.md`
- `../test_outputs/srs_food_cooking_signal_review_packet_en_es_current_latest.md`
- `../test_outputs/srs_food_cooking_source_capacity_audit_en_es_latest.md`
- `../test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.md`
- `../test_inputs/srs_food_cooking_full_source_review_labels_en_es.json`
- `../test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.md`
- `../test_outputs/srs_food_cooking_full_source_review_precision_summary_en_es_latest.md`
- `srs_food_cooking_signal_review_and_coverage_plan_en_es.md`

## Decision Frame

The current installed `freq-es-cde` pack has no native topic columns. The
installed Kaikki/Wiktionary pack can still enrich it with explicit
`sense_topics` for `234 / 1,984` current CDE lemmas (`11.8%`).

That gives us a real topic surface, but it is not a finished product taxonomy.
The product taxonomy should be ours. Current source coverage tells us how much
implementation work remains; it should not decide what users are allowed to
care about.

1. choose user-facing preference families,
2. map source labels into those families,
3. assign confidence/weight per mapping,
4. mark high-value but under-covered topics as P0 enrichment targets,
5. keep unsupported or legally gated preferences unavailable until sourced.

Use these source channels differently:

| Source Channel | Current Use | Reason |
| --- | --- | --- |
| `sense_topics` | Candidate source for product-topic mappings | Sense-level labels are the cleanest currently installed topic signal. |
| `sense_tags`, `sense_categories`, `entry_tags`, `entry_categories` | Review-only inventory | These channels are broad and noisy: grammar, register, maintenance categories, and Wiktionary housekeeping dominate. |
| SAT/TOEFL source data | Not present yet | These are product-aligned only after legal/source review identifies allowed data. |

Current UX policy: topics and register/style preferences can share one
user-facing `Interests & Style` section, but the internal taxonomy keeps an
explicit `axis` so source policy can treat topics and registers differently.
Region is deferred for now because source coverage is likely sparse and
misleading. SAT/TOEFL should use explicit SAT/TOEFL wording only for
English-target pairs after legal/source review.

## Recommended Product Preference Families

This is the practical v0 shortlist. "Adopt" means the topic family is plausible
as a product preference once the mapping file, source provenance, and tests are
in place. "P0 enrichment" means the product should support the topic, but the
current trusted source labels are not enough by themselves.

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
| `anime_manga_pop_culture` | adjacent labels only: `entertainment` 20, `media` 9, `film` 1, `television` 2, `gaming` 1 | weak/adjacent | P0 enrichment | High UX value. Needs public sources, curated seed lists, or embedding/gloss inference; do not pretend broad media tags mean anime. |
| `hobbies_crafts` | `hobbies` 41, plus narrow labels such as `sewing` 1, `textiles` 2, `arts` 5, `games` 24 | medium but ambiguous | P0 enrichment | Users care about hobbies, but `hobbies` is too broad/polysemous to use directly without review. |
| `education_academic` | `education` 2, `higher_education` 1, plus possible academic aliases from `grammar`, `linguistics`, `mathematics`, and `sciences` | weak | Defer or parent-only | Needs a clearer taxonomy before becoming user-facing. |
| `food_cooking` | `food` 2, `cooking` 2 | weak direct support; reviewed overlay PoC has 37 rows | P0 enrichment | Strong user-delight topic. Current trusted support is small, but reviewed labels now prove a narrow overlay path. Broader coverage still needs public recipe/food lexicons, a larger allowed frontier, or embedding inference before strong product claims. |
| `psychology_emotions` | `psychology` 1, `human_sciences` 17 | weak | Defer until overlay | Emotions are product-aligned but not directly present in trusted current-CDE topics. |
| `animals` | `animals` 1, `zoology` 1, plus allowlisted animal categories/glosses in review-only channels | weak direct support | P0 enrichment | Strong user-delight topic. Keep separate from botany/plants; broad science labels should not substitute for it. |
| `plants_nature` | `botany` 5, plus allowlisted plant categories/glosses in review-only channels | weak direct support | P0 enrichment | Keep plants/botany distinct from animals. Useful for gardening/nature interests, but broad natural-science labels are too broad for strong lift. |
| `casual_slang_register` | register/tag channels only; not trusted for automatic lift yet | review-only | Add as register axis | Strong UX value, but source tags need allowlisting and sampling before admission lift. |
| `formal_professional_register` | register/tag channels only; not trusted for automatic lift yet | review-only | Add as register axis | Useful for workplace/professional goals. Treat beside topics in UX, but keep separate internally. |
| `sat_toefl_exam_prep` | none in current trusted source data | none | Legal/source gated | Add only after allowed vocabulary, skill, or exam-prep data is identified. Do not infer from current Wiktionary labels. |

## Product-First P0 Set

The first product taxonomy should include both utility topics and topics users
will enjoy choosing. The implementation can assign each family a readiness
state, but the UX roadmap should not drop high-delight topics just because
current trusted labels are sparse.

| P0 Family | Readiness Now | Main Path To Usable Coverage |
| --- | --- | --- |
| `medicine_health` | source-ready | trusted `sense_topics`, then health/medicine overlay |
| `finance_business` | source-ready | trusted `sense_topics`, then business/finance aliases |
| `sports_fitness` | source-ready | trusted `sense_topics`, then sport/fitness aliases |
| `games` | source-ready | trusted `sense_topics`, then game subtopic aliases |
| `music_media_entertainment` | source-ready | trusted `sense_topics`, then media/pop-culture aliases |
| `animals` | P0 enrichment | animal lexicons, allowlisted Wiktionary animal categories, embeddings over glosses |
| `plants_nature` | P0 enrichment | plant/nature lexicons, botany labels, allowlisted Wiktionary plant categories, embeddings over glosses |
| `food_cooking` | P0 enrichment | food/cooking lexicons, recipe-domain sources, embeddings over glosses |
| `anime_manga_pop_culture` | P0 enrichment | legally usable fandom/pop-culture sources, curated seed lists, embeddings |
| `hobbies_crafts` | P0 enrichment | curated hobby taxonomy, craft/activity lexicons, reviewed broad `hobbies` labels |
| `casual_slang_register` | review-only | allowlisted register tags, corpus/register sources, and manual precision checks |
| `formal_professional_register` | review-only | allowlisted formal/professional labels, workplace-domain overlays, and manual precision checks |
| `travel_places_transport` | partial | travel overlay plus existing geography/transport labels |
| `arts_literature_humanities` | partial | literature/art overlays plus existing humanities labels |
| `sat_toefl_exam_prep` | legal/source gated | allowed exam-prep vocabulary or internal skill taxonomy |

The first machine-readable taxonomy/mapping artifact is
`../test_inputs/srs_topic_preference_taxonomy_en_es.json`. Its current installed
source audit validates the taxonomy and keeps `animals` separate from
`plants_nature`: trusted current CDE `sense_topics` map only `1 / 1,984`
lemmas to `animals` and `5 / 1,984` lemmas to `plants_nature`. The focused
existing-signal audit expands the local, read-only inventory to `38` animal
candidates and `22` plants/nature candidates using Tier A topics, Tier B
primary-sense exact noun translations, Tier C allowlisted categories/tags, and
Tier D review-gated gloss/translation patterns. That is useful evidence for
enrichment design, not a promoted overlay or admission behavior change. The
editable signal policy is tracked in
`docs/test_inputs/srs_animals_plants_signal_policy_en_es.json`.

The first food/cooking confidence audit is
`../test_outputs/srs_food_cooking_existing_signal_audit_en_es_current_latest.md`.
It keeps the same read-only posture and expands the current CDE food/cooking
inventory from `2` trusted `sense_topics` rows to `46` existing-source
candidates. Only `2` candidates are high-confidence primary translations; `42`
rows remain review-required because food categories and glosses are often
sense-specific. Food/cooking is allowed to overlap animals or plants/nature
when the evidence supports a culinary sense, but that overlap is not automatic
product lift.

The first food/cooking review packet is
`../test_outputs/srs_food_cooking_signal_review_packet_en_es_current_latest.md`.
Because the current conservative candidate universe is only `46` rows, the
packet includes all `46 / 46` candidates across `16 / 16` review cells instead
of sampling a subset. This packet is a precision-calibration surface, not a
coverage-complete food vocabulary target; recall expansion still needs broader
food lexicons, legally usable recipe/food sources, or embedding-assisted
candidate discovery.

The first labels are stored in
`../test_inputs/srs_food_cooking_signal_review_labels_en_es_current.json`: `19`
strong accepts, `18` light accepts, `6` secondary/obscure rejects, and `3`
wrong-topic rejects. The current-CDE source-capacity audit reports `2,122` local
Kaikki/Wiktionary food-signal lemmas under the same policy, with only `46`
inside the current frequency frontier. That makes the current frontier the
first recall bottleneck for food/cooking.

The first food/cooking overlay PoC is
`../test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.md`.
It converts the `37` accepted review labels into a provenance-bearing candidate
overlay (`19` strong, `18` light), excludes all `9` rejected labels, and runs
the existing profile-bootstrap reranker with a `food_cooking` interest. The
preview moves reviewed food/cooking rows into the top profile preview by `+7`
without mutating helper state or enabling default runtime admission.

The first full-source food/cooking expansion packet is
`../test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.md`.
It samples `96` review rows from the installed local Kaikki food/cooking
candidates outside the already-reviewed current frontier. Labels in
`../test_inputs/srs_food_cooking_full_source_review_labels_en_es.json` accept
`91 / 96` guarded rows (`54` strong, `37` light) and reject `5`. This gives a
precision-calibration surface for deciding whether the broader policy can
support a 10k-style frontier.

The full-source precision summary is
`../test_outputs/srs_food_cooking_full_source_review_precision_summary_en_es_latest.md`.
It records the current flow assessment as positive: discovery, review labels,
diagnostic overlay behavior, and runtime admission are separated correctly. The
next risk-reduction step is policy guards for the caught false-positive
classes before any broad overlay promotion.

The current product-facing food/cooking checkpoint is the SPALEX 10k audit and
review packet:

- `../test_outputs/srs_food_cooking_existing_signal_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_food_cooking_source_capacity_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_food_cooking_signal_review_packet_en_es_spalex_10k_latest.md`

This finds `265 / 10,000` food/cooking candidates, with `219` review-required
rows and a deterministic `96`-row packet covering `62 / 62` evidence cells.
Prior labels match `42 / 96` packet lemmas by lemma, but the packet remains
pending review before any precision or overlay claim. For UX/admission
decisions, this 10k surface should take priority over the 2k/current baseline.

The same read-only confidence audit over the rebuilt SPALEX 10k frontier finds
more absolute candidates but still sparse coverage: `172 / 10,000` animal
candidates (`1.7%`) and `138 / 10,000` plants/nature candidates (`1.4%`). This
means the larger source gives enough examples for validation and overlay design,
but it does not remove the need for product-owned animal and plant overlays or
embedding-assisted enrichment. The SPALEX audit also applies a secondary-sense
penalty, because some Tier A/C hits are polysemous headwords where the
animal/plant sense is real but not necessarily the dominant learner-facing
sense.

The first review packet is generated at
`docs/test_outputs/srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.md`.
It samples `96` rows from the full `310` SPALEX candidate universe, covering
`96 / 125` evidence cells with `56` animal rows and `40` plants/nature rows.
Agent review labels are stored separately in
`docs/test_inputs/srs_animals_plants_signal_review_labels_en_es_spalex_10k.json`
and merged into the generated packet for QA. These labels are a calibration
surface only; no sampled row is promoted until it is converted into a reviewed,
provenance-bearing overlay or policy artifact.

The first executable overlay PoC is generated at
`docs/test_outputs/srs_animals_plants_topic_overlay_poc_en_es_spalex_10k_latest.md`.
It creates an overlay candidate with `84` accepted rows (`49` animals, `35`
plants/nature). For the runnable preview, only strong accepted rows are injected
into `profile_topics` because the current profile-bootstrap scorer consumes
topic presence rather than scalar topic membership. Against the SPALEX 10k seed
frontier, the overlay preview increases topic-labeled rows in the top profile
preview by `+24` for `animals` and `+19` for `plants_nature`. This proves the
review-label-to-profile-admission path works, but it is not a default runtime
admission change.

The current paused topic-coverage state is recorded in
`srs_topic_coverage_pause_state_en_es.md`. It adds the Wikidata
natural-taxonomy overlay to the standard lab/readiness overlay stack, promotes
`39` reviewed source-prep rows (`20` animals, `19` plants/nature), keeps
Wikidata out of runtime, and treats Animals, Plants/Nature, and Food/Cooking as
MVP/lab acceptable but intentionally incomplete. Use that pause snapshot before
resuming any further topic-coverage work.

A focused animal low-confidence spot check is recorded at
`docs/srs/srs_animals_low_confidence_spot_check_en_es.md`. The review supports
the current conservative posture: low-confidence rows preserve useful recall for
manual QA, but should not be automatically promoted.

## Admission Lab Exit Checkpoint

The current admission mechanics are acceptable enough to pause admission tuning
and move the workstream back to source coverage. The tested behavior is:

- topic preference strength moves matching candidates when usable topic rows
  exist;
- the readiness gate suppresses words that are far too easy or too hard for the
  profile;
- topic relevance widens the readiness band, but does not override source
  depth;
- the lab now reports realized preferred-topic share and topic depth by
  difficulty band, so coverage failures are visible instead of being mistaken
  for scorer failures.

The strongest current example is `animals`. In the dev-only Zipf-bridge
augmented EN-ES lab frontier, the active animal support surface had `33 / 4,123`
topic candidates. Its difficulty depth was shallow: `30` animal candidates in
`0.00-0.20`, `3` in `0.20-0.40`, and `0` above `0.40`; max animal difficulty
was about `0.282`. As a result, animal preference produced `10 / 10` animal
sample rows around proficiency `0.25`, `3 / 10` around `0.55`, and no animal
sample rows around `0.65` or `0.80`.

Decision:

- do not keep micro-tuning the admission scalar/readiness math for this issue;
- treat high-proficiency animal dropoff as a topic-depth/source-coverage gap;
- improve animal coverage through reviewed overlays, additional legal source
  data, or validated inference before expecting strong animal behavior across
  all proficiency bands;
- use the same topic-depth lens for every main product topic before claiming
  broad interest-tailored SRS quality.

## Main-Topic Coverage Focus

The next coverage pass should evaluate all main product families with the same
questions, not only raw row counts:

1. How many trusted or reviewed candidates does the family have in the current
   baseline and the 10k expansion frontier?
2. Are candidates distributed across difficulty bands, or concentrated only in
   beginner/common vocabulary?
3. Are top examples actually good user-facing examples, or noisy/polysemous
   source labels?
4. Is source/license/provenance clean enough for product use?
5. Should the family be enabled normally, enabled with limited-support UX,
   treated as enrichment-only, or kept unavailable?

Current posture:

| Family Group | Families | Coverage Posture | Next Work |
| --- | --- | --- | --- |
| Source-ready utility topics | `medicine_health`, `finance_business`, `sports_fitness`, `games`, `law_politics_civics`, `music_media_entertainment`, `science_technology` | Enough trusted/source-topic support to keep validating profile lift. | Add per-family depth/precision diagnostics over the 10k frontier before product claims. |
| Partial parent topics | `arts_literature_humanities`, `travel_places_transport` | `arts_literature_humanities` is strict-MVP visible after calibration; `travel_places_transport` stays hidden as a future beta candidate despite selector correctness. | Keep travel documented for follow-up; do not expose it in the first tester-facing picker. |
| P0 enrichment topics | `animals`, `food_cooking`, `plants_nature`, `anime_manga_pop_culture`, `hobbies_crafts` | `animals` and `food_cooking` are strict-MVP visible because overlays make them product-useful; `plants_nature` stays hidden beta; anime/hobbies remain source-blocked. | Build or source overlays/inference, then rerun depth/precision checks before promoting hidden families. |
| Register/style preferences | `casual_slang_register`, `formal_professional_register` | UX-relevant but should start review-only because current trusted coverage comes from topic labels, not register-safe signals. | Inventory allowlisted register signals separately, sample precision, then decide whether to enable. |
| Legal/source gated | `sat_toefl_exam_prep` | Product-aligned but unavailable until allowed data is identified. | Resolve legal source path before surfacing as a preference. |

The first broad family-depth audit is
`../test_outputs/srs_topic_family_depth_audit_en_es_latest.md`. Against the
installed current CDE frontier it reports:

- measurable trusted coverage for `9` topic families:
  `science_technology`, `medicine_health`, `law_politics_civics`,
  `sports_fitness`, `music_media_entertainment`, `travel_places_transport`,
  `finance_business`, `games`, and `arts_literature_humanities`;
- thin trusted coverage for `plants_nature` (`5` rows), `food_cooking` (`2`
  rows after adding direct `food`/`cooking` mappings), and `animals` (`1` row);
- no trusted current-CDE coverage for `anime_manga_pop_culture`,
  `hobbies_crafts`, or `sat_toefl_exam_prep`;
- review-only register signals for `casual_slang_register` (`85` candidates)
  and `formal_professional_register` (`5` candidates).

The targeted food/cooking confidence audit confirms that the broad trusted
audit is conservative rather than exhaustive: existing local categories,
primary translations, and narrow gloss/translation patterns produce `46`
current-CDE food/cooking candidates, with `42` intentionally review-required
before any overlay or admission lift.
The companion review packet includes all `46` rows; labels accept `37` rows as
real food/cooking signals and reject `9` secondary, obscure, or wrong-topic
rows. The overlay PoC proves those accepted labels can lift a `food_cooking`
profile preview, while the rejects show that Tier D gloss/example patterns and
noisy overlap categories should stay review-gated. A source-capacity audit
shows `2,076` additional local food-signal lemmas outside the current frequency
frontier.

The latest food/cooking checkpoint is the labeled full-source review packet
over those outside-frontier candidates. It does not promote any row; the
purpose is to find whether the broad source policy remains precise when it sees
the much larger local candidate pool. The initial label result is promising
(`91 / 96` accepted after the guard pass), but it still exposes botanical or
fodder overlap, zoological fish terms, proper-name-first entries, and eater
glosses that need policy handling before product lift.

The latest product-facing food/cooking checkpoint is the SPALEX 10k packet. It
finds `265 / 10,000` food/cooking candidates and samples `96` rows across
`62 / 62` evidence cells. It is intentionally unlabeled for now; the next food
work should review that 10k packet rather than continuing to reason only from
the 2k/current baseline.

This is the acceptance boundary for moving on from admission: the admission
algorithm can remain as-is unless a structural bug appears. The next quality
bar is topic coverage and topic precision across the product taxonomy.

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
| Product-desired overlay label | curated animal/cooking/anime source -> matching family | source-dependent |
| Embedding-inferred label | gloss/example embedding -> matching family | low-to-medium until validated |
| Legally gated exam prep | `sat`, `toefl` | unavailable until sourced |

## Suggested v0 Decision

The current strict-MVP picker should expose only taxonomy families with
`mvp_picker_visibility=strict_mvp_visible`:

- `medicine_health`
- `finance_business`
- `sports_fitness`
- `games`
- `law_politics_civics`
- `music_media_entertainment`
- `science_technology`
- `arts_literature_humanities`
- `animals`
- `food_cooking`

Treat these as P0 product goals that remain hidden from the ordinary first
picker until coverage or UX posture improves:

- `plants_nature`
- `anime_manga_pop_culture`
- `hobbies_crafts`
- `travel_places_transport`

Keep these as planned but not current-CDE-ready:

- `education_academic`
- `psychology_emotions`
- `sat_toefl_exam_prep`

Add these as register/style preferences in the same UX section, but keep them
review-only until source precision is proven:

- `casual_slang_register`
- `formal_professional_register`

Do not start region preferences in this pass.

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
