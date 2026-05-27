# en-es SRS Topic Coverage Pause State

Status: active pause snapshot
Role: Current closeout note
Last updated: 2026-05-27
Last verified: 2026-05-27 by Wikidata natural-taxonomy overlay generation, release-readiness regeneration, SRS admission lab smoke, en-es admission calibration artifact generation, focused tests, SRS quality harness, changed-file gate, and doc-reference check
Purpose: record the accepted temporary stopping point for en-es topic coverage so future work can resume deliberately without re-litigating this cleanup slice
Source-of-truth: closeout note only; executable truth lives in SRS/helper code, overlay artifacts, generated readiness reports, tests, and the topic taxonomy fixture.
Current MVP recommendation: `srs_topic_mvp_recommendations_en_es.md`
Beta-topic deep dive: `srs_beta_topic_deep_dive_en_es.md`

## Current Decision

Pause en-es topic coverage expansion here.

The current topic system is good enough for MVP validation of the personalized
admission concept, but it is not comprehensive content coverage. We should not
continue polishing individual topic inventories until higher-priority product
work is handled.

Current product decision: strict MVP only. The first tester-facing topic picker
should exclude beta topics (`plants_nature` and `travel_places_transport`) until
we intentionally add a beta/limited topic affordance or improve their coverage
enough for ordinary visibility.

The key product conclusion is:

- topic preference strength can visibly move matching words in admission
  previews;
- topic data is now carried by provenance-bearing overlays rather than ad hoc
  lab state;
- Animals, Plants/Nature, and Food/Cooking remain intentionally incomplete;
- future coverage enrichment can add more overlays without invalidating user
  SRS progress, because preferences affect future admission scoring and do not
  rewrite existing review history.

## Internalized Data

The latest Wikidata natural-taxonomy pass is internalized as a normal overlay:

- candidate audit:
  `../test_outputs/srs_wikidata_natural_taxonomy_candidates_en_es_latest.md`
- promoted overlay:
  `../test_outputs/srs_wikidata_natural_taxonomy_topic_overlay_en_es_spalex_10k_latest.md`
- converter:
  `../../scripts/testing/srs_wikidata_natural_taxonomy_topic_overlay_en_es.py`
- focused test:
  `../../core/tests/dev/test_srs_wikidata_natural_taxonomy_topic_overlay_en_es.py`

The overlay promotes `39` rows:

| Topic | Rows |
| --- | ---: |
| `animals` | 20 |
| `plants_nature` | 19 |

`rubio` is explicitly excluded from promotion because it is an alias-only fish
candidate that is more likely to behave as a general adjective in learner
content.

Wikidata remains build/source-prep only:

- no runtime Wikidata calls;
- no user install requirement;
- no bundled raw Wikidata dump;
- source provenance records Wikidata structured data as CC0;
- promoted rows are packaged LexiShift overlay data.

## Current Overlay Stack

The local SRS admission lab and release-readiness classifier now include these
default overlay artifacts:

1. `../test_outputs/srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json`
2. `../test_outputs/srs_food_cooking_topic_overlay_en_es_spalex_10k_latest.json`
3. `../test_outputs/srs_wikidata_natural_taxonomy_topic_overlay_en_es_spalex_10k_latest.json`
4. `../test_outputs/srs_source_topic_overlay_en_es_spalex_10k_latest.json`
5. `../test_outputs/srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.json`

The wiring lives in:

- `../../scripts/dev/srs_admission_lab_server.py`
- `../../scripts/testing/srs_topic_release_readiness_en_es.py`

## Release-Readiness Snapshot

The current generated readiness report is:

- `../test_outputs/srs_topic_release_readiness_en_es_latest.md`
- MVP recommendation note: `srs_topic_mvp_recommendations_en_es.md`

After adding the Wikidata overlay:

| Topic | Effective Rows | Runtime Overlay Rows | Bands | Current Status |
| --- | ---: | ---: | ---: | --- |
| `animals` | 100 | 100 | 2 | `release_candidate_limited_depth` |
| `plants_nature` | 34 | 34 | 1 | `beta_limited_candidate` |
| `food_cooking` | 73 | 73 | 2 | `limited_release_candidate` |

Interpretation:

- `animals` is acceptable for MVP lab validation with limited-depth copy.
- `plants_nature` remains hidden for the strict MVP; it is usable only as
  beta/limited if a future beta affordance is added, because it still has thin
  depth and only one source difficulty band.
- `travel_places_transport` remains hidden for the strict MVP; it is the safer
  future beta candidate, but it still has shallow depth and broad-label
  precision risk.
- `food_cooking` is acceptable for MVP lab validation, but still clumpy and
  sparse compared with an ideal user-delight topic.
- `anime_manga_pop_culture` and `hobbies_crafts` remain hidden/source-blocked.
- `sat_toefl_exam_prep` remains legal/source gated and is relevant only for
  English-target LPs after source review.

## What We Proved

1. The product-owned topic taxonomy can stay separate from source labels.
2. Topic weights are preference strength, not exact share targets.
3. Stronger topic preference can move matching words into admission previews.
4. Proficiency/readiness gating prevents preference lift from fully ignoring
   learner level.
5. Reviewed overlays can add topic evidence without changing the admission
   algorithm.
6. Wikidata can provide useful natural-taxonomy seed data when consumed at
   build/source-prep time and filtered before promotion.
7. The same overlay path can support future LP/topic expansion without
   destroying existing SRS state.

## What We Did Not Prove

1. Topic coverage is comprehensive.
2. Animal, plant, food, hobby, or pop-culture inventories are complete enough
   for a polished content catalogue.
3. High-proficiency users will always see rich topic supply in every topic.
4. Topic preference strength maps to a stable realized percentage of admitted
   topic words.
5. Register/style preferences are ready for ordinary topic-style product
   exposure.
6. SAT/TOEFL can be shipped without a legally reviewed English-target source.
7. Rare topic words cannot starve active SRS capacity by being admitted and
   then rarely encountered in ordinary browsing.

These are acceptable open gaps for the pause point.

## Resume Criteria

Resume topic coverage work only when one of these becomes a product priority:

- a release decision requires visible topic/support copy;
- a target topic feels obviously broken in lab or user testing;
- a new legally usable source is identified;
- a new LP needs topic-signal onboarding;
- the admission algorithm needs more calibrated realized-share diagnostics than
  the current en-es ranked, weighted, top-k, and reserved-lane calibration
  artifact provides.

Best next work if resumed:

1. run sampled precision review for the current Animals and Food/Cooking overlay
   stacks;
2. add difficulty-band enrichment for high-value limited-depth topics;
3. identify source-backed paths for Hobbies/Crafts and Pop Culture;
4. build English-target SAT/TOEFL source review only after legal/source approval;
5. use `../test_outputs/srs_admission_calibration_en_es_latest.md` to inspect
   realized and expected topic-share diagnostics before changing topic coverage
   or sampling policy; current MVP implementation uses a capped reserved topic
   lane over full-pool weighted sampling for explicit topic preferences.

## Verification Commands

Most recent closeout validation used:

```bash
node scripts/dev/run_python.js ../core/tests/dev/test_srs_wikidata_natural_taxonomy_topic_overlay_en_es.py
node scripts/dev/run_python.js ../core/tests/dev/test_srs_admission_lab_server.py
node scripts/dev/run_python.js ../core/tests/dev/test_srs_topic_release_readiness_en_es.py
node scripts/dev/run_python.js testing/srs_quality_harness.py --json-out ../docs/test_outputs/srs_quality_latest.json
node scripts/dev/run_python.js dev/dev_workflow_changed_check.py --scope local
node scripts/dev/run_python.js dev/check_doc_references.py
git diff --check
```

The local admission lab entrypoint is:

```bash
node scripts/dev/run_python.js dev/srs_admission_lab_server.py --port 8766
```
