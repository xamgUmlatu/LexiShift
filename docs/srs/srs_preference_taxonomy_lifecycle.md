# SRS Preference Taxonomy Lifecycle

Status: active planning reference
Role: Planning / WIP
Last updated: 2026-05-19
Last verified: 2026-05-19 by SRS profile schema, topic taxonomy fixture, taxonomy audit tests, and interest-tailored admission docs
Purpose: define how SRS topic/register preferences can expand after release without damaging existing SRS progress
Source-of-truth: lifecycle policy for preference taxonomy changes; executable truth lives in profile storage, SRS store code, taxonomy fixtures, and focused tests.

Related docs:
- `srs_profile_schema.md`
- `srs_hybrid_model_technical.md`
- `srs_interest_tailored_admission_algorithm.md`
- `srs_interest_tailored_data_acquisition_plan.md`
- `srs_topic_preference_decision_matrix_en_es.md`
- `../test_inputs/srs_topic_preference_taxonomy_en_es.json`

## Core Contract

SRS preference expansion must be additive.

The user profile may gain new preference IDs and source packs may gain new
topic/register metadata, but existing SRS review state must not be deleted,
reset, or rescheduled just because the taxonomy becomes richer.

The safety model relies on the existing separation:

| Surface | Owns | Expansion Behavior |
| --- | --- | --- |
| SRS profile signals | user preferences, proficiency, source preferences, inferred trends | Can add new preference IDs or weights. |
| Candidate/source metadata | frequency, POS, topic/register labels, provenance | Can add new labels, overlays, confidence, and coverage. |
| SRS store | admitted items, due dates, ease, interval, status, feedback history | Must remain stable across taxonomy expansion. |

New preferences should affect future admission and diagnostics. They should not
silently rewrite the learner's existing schedule.

## Post-Release Rules

1. Preference IDs are append-only after release.
2. Do not rename or semantically reinterpret an existing ID without an explicit
   alias or migration.
3. Do not reuse an old ID for a narrower, broader, or different concept.
4. Keep each preference family on an explicit internal axis, currently `topic`
   or `register`.
5. The UX may show topics and registers together in one `Interests & Style`
   section, but policy and source review must keep the axis explicit.
6. Preference availability is pair-scoped. Unsupported families should be hidden
   or disabled rather than accepted as empty personalization.
7. New source metadata must carry provenance, license posture, and confidence.
8. Existing admitted items may receive optional metadata backfill, but backfill
   must not reset scheduler fields.
9. Existing profile values should remain readable even if a preference becomes
   unavailable for a given pair.
10. A removed or unavailable preference should degrade to no admission lift, not
    to broken profile loading.

## Safe Expansion Example

If `animals` ships with sparse coverage and later receives a reviewed overlay:

1. Keep the existing `animals` ID.
2. Add new animal metadata to candidate rows or an overlay artifact.
3. Recompute future admission scores from the richer candidate surface.
4. Leave existing `srs_store.json` item scheduler fields unchanged.
5. Optionally add non-scheduling metadata to already-admitted items for
   diagnostics, but do not delete or reset them.

If the old `animals` meaning was wrong and the product needs separate concepts,
add new IDs such as `pets` or `wildlife`. Do not repurpose `animals`.

## Current EN-ES Taxonomy Decisions

The first EN-ES taxonomy fixture is
`../test_inputs/srs_topic_preference_taxonomy_en_es.json`.

Current decisions:

| Decision | Current Policy |
| --- | --- |
| Big topic families | Keep medicine, finance, sports, games, science/technology, law/civics, media/entertainment, travel, arts/humanities, animals, plants/nature, food/cooking, anime/pop culture, and hobbies/crafts in the target surface. |
| Region | Defer until source coverage is clear enough to avoid sparse or misleading UX. |
| Exam prep | Keep `sat_toefl_exam_prep` legal/source gated and scoped to English-target pairs. |
| Register/style | Add `casual_slang_register` and `formal_professional_register` as review-only preference families under the same UX group as topics. |

## Add-A-Preference Checklist

Before a new preference family can be product-facing:

1. Add a stable ID to the taxonomy with `axis`, `ux_group`, `pair_scope`,
   `readiness_state`, and `data_strategy`.
2. Decide whether the family is a normal topic, a register/style preference, a
   region preference, or a legally gated family.
3. Add source-label mappings only for trusted channels, or keep candidate
   signals review-only until sampled.
4. Run the taxonomy audit and focused tests.
5. Measure coverage, difficulty-depth, top examples, source provenance, and
   precision before claiming product readiness.
6. Gate the UI by LP capability/availability.
7. Preserve existing profile and SRS store compatibility.

## Unsafe Changes

These require an explicit migration plan before release:

- renaming `food_cooking` to a different ID without aliasing;
- changing `animals` to mean only pets;
- changing `science_technology` to exclude technology while keeping the same
  ID;
- accepting region preferences without enough region-labeled candidate depth;
- surfacing SAT/TOEFL before an allowed source path exists;
- promoting review-only register tags directly into admission lift without
  allowlisting and sampling.
