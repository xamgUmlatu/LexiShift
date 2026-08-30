# SRS Learner-Difficulty LP Onboarding Playbook

Status: reusable onboarding playbook
Role: Cross-language-pair learner-difficulty method
Last updated: 2026-06-30
Last verified: 2026-06-30 from the packaged en-ja corrected ranking, product admission sample pack, full-range sample pack, SRS quality harness, and committed learner-difficulty sidecar artifacts.
Purpose: preserve the en-ja learner-difficulty lessons so future language-pair difficulty rankings start from the right mathematical and product assumptions.
Source-of-truth: method and checklist only. Runtime truth lives in SRS/helper code, packaged resources, pair resource resolvers, tests, and generated acceptance artifacts.

## Core Target

The scalar is presentation priority:

```text
presentation_level(item) in [0, 1]
```

It should answer:

```text
At approximately what learner proficiency should this item become reasonable to
show by default?
```

It is not pure frequency, pure rarity, pure orthographic complexity, pure
intrinsic difficulty, or a complete curriculum. A very useful word can be early
even when it is longer or structurally harder. A frequent form can be unsuitable
as a standalone SRS vocabulary item.

This target must remain usable with one simple user proficiency setting from
`0.00` to `1.00`. The model may use lanes, gates, source arbitration, and
manual corrections internally, but the exported product surface still needs a
single ordering spine plus admission metadata.

## What en-ja Taught Us

1. Frequency is the first useful spine, not the target.

   Frequency and exposure usually move in the right direction, but they fail on
   grammar items, rare readings of common surfaces, compound-heavy components,
   domain terms, and orthographic variants.

2. Pedagogical evidence dominates the early ladder.

   For the first large learner-facing slice, usefulness and curricular presence
   matter more than raw structural burden. JLPT, lesson vocabulary, beginner
   sources, and high-confidence teaching lists are strongest as early upper
   bounds, not as hard lower bounds.

3. Exact item identity matters.

   Future LPs must distinguish:

   ```text
   surface-only support
   reading/pronunciation-specific support
   dictionary-entry family support
   normalized/base-form support
   broad source-family support
   ```

   The en-ja `而して/しこうして`, `外国/とつくに`, `明日/あした`, and
   common-kanji rare-reading cases showed that family evidence can pollute a
   specific item if the model cannot tell which form or reading the source
   actually supports.

4. Raw flags are facts, not penalties.

   Domain labels, dialect labels, abbreviation flags, proper-name overlap,
   script-form labels, and dictionary restrictions should not automatically
   increase difficulty. They become late-placement or restricted-admission
   evidence only when gated by weak ordinary-vocabulary support, rarity, or a
   source-backed reason that the item is not a good default standalone card.

5. Admission metadata is separate from scalar score.

   Some rows should keep a score but route differently:

   - `display_only`: show a better written form while preserving the item.
   - `restricted_admission`: do not treat the row as ordinary standalone
     vocabulary, but keep it as structured knowledge.
   - `exclude_standalone_srs`: remove the row from default standalone
     admission because clearer rows should carry the teachable meanings.
   - `topic_stretch_allowed`: decide whether topic preference may pull the row
     earlier than similarly scored general vocabulary.

6. Qualitative band review is not optional.

   Metrics detect many mistakes, but they under-sample the exact product pain:
   what the learner actually sees around each proficiency setting. Every
   candidate needs random and risk-weighted samples across thin bands, plus
   product-style admission samples with neutral and topic-biased profiles.

7. Manual correction layers are product infrastructure, not failure.

   A good automatic model still needs a small explicit correction layer for
   common written-form UX, overloaded standalone rows, rare readings, and
   rows where source truth is insufficient. Corrections should be typed and
   reviewable, not buried in model constants.

8. Holdout score is necessary but not sufficient.

   en-ja repeatedly showed that calibration wins can fail holdout, and that
   tiny score changes can still create meaningful order improvements. Promotion
   decisions need cross-split metrics, qualitative samples, and product
   admission samples.

## Required Onboarding Sequence

Use this sequence for a new learner-difficulty LP. Do not start with a giant
formula sweep.

1. Define the item identity.

   Specify what the SRS item is for the LP:

   ```text
   surface
   lemma
   pronunciation/reading
   dictionary entry id
   normalized/base form
   script/display forms
   ```

   If the LP lacks one of these fields, document the loss of precision before
   modeling.

2. Build the signal palette.

   Enumerate every available signal in one palette table. Each signal needs:

   ```text
   source
   extraction endpoint
   exactness level
   polarity
   coverage
   intended modeling role
   redistribution/license posture
   ```

   Do not sweep a signal until its endpoint and polarity have been audited.

3. Separate source roles.

   At minimum, classify signals into these roles:

   ```text
   pedagogical anchors
   exposure/commonness
   exact form or pronunciation support
   dictionary-entry family support
   morphology/base-form support
   orthographic or phonological burden
   lexical ambiguity or dictionary complexity
   routing/admission/topic facts
   source knownness and missingness
   ```

4. Create calibration and holdout labels.

   Labels should include ordinary rows, early rows, middle-band rows, domain
   rows, source-edge cases, and upper-tail rows. Keep a fresh holdout set that
   is not used for hand-tuning.

5. Build the simplest defensible baseline.

   Start with a frequency/exposure spine plus pedagogical anchors. This is the
   comparison anchor for all future work.

6. Audit structured failures before adding broad complexity.

   For each failure group, ask:

   ```text
   Is the row truly scored wrong, or is it an admission/display issue?
   Which source claimed the wrong thing?
   Is the evidence exact, family-level, or broad?
   Does the fix target only this failure family?
   What rows would regress?
   ```

7. Add only source-backed shapes.

   Good shapes are conditional:

   ```text
   trust pedagogical evidence when exact and early;
   trust exposure when exact and ordinary;
   use burden when ordinary evidence is weak;
   use family/base rescue only when it cannot override exact support;
   use routing flags as gates, not raw scalar penalties.
   ```

8. Keep manual corrections typed.

   Corrections should use structured fields such as:

   ```text
   correction_types
   display_form
   admission_override
   topic_stretch_allowed
   correction_status
   correction_rationale
   ```

   The goal is not to hide errors. The goal is to preserve a clean distinction
   between model learning, display policy, and product admission policy.

9. Generate product acceptance packs.

   Before runtime promotion, generate:

   ```text
   full-range thin-band samples
   risk-weighted samples
   first-N review samples for early learner UX
   neutral proficiency profiles from 0.00 to 1.00
   representative topic-preference profiles
   old-problem sentinel checks
   runtime difficulty mismatch checks
   ```

10. Package the accepted artifact.

    Runtime should read a packaged resource by default and allow an explicit
    experiment override. Seed/frontier caches must include a fingerprint of the
    packaged difficulty resource so stale difficulty data does not leak into
    admission.

## Model Shape Guidance

The default future-LP shape should be source arbitration plus bounded
corrections:

```text
pedagogical_estimate = f(pedagogical exact and trusted evidence)
exposure_estimate    = f(frequency, priority, corpus/commonness evidence)
burden_estimate      = f(script, reading, morphology, ambiguity)
route_estimate       = f(admission/display/topic facts)

base = choose_or_blend(pedagogical_estimate, exposure_estimate, confidence)

score = clamp(base + bounded_conditional_corrections)

admission = route(route_estimate, manual_corrections, candidate_classifier)
display   = choose_display_form(score_row, source_forms, manual_corrections)
```

Avoid defaulting to a flat weighted sum unless it wins cross-split metrics and
qualitative review. Flat sums tend to make every signal global, while this
problem is mostly conditional.

## Acceptance Criteria

A new LP difficulty ranking is ready for product-style testing when:

- source endpoints and signal polarity are audited;
- calibration and holdout labels exist;
- the baseline and proposed model are both reproducible;
- major failure groups are documented;
- qualitative samples across the full `0.00-1.00` range look coherent;
- early learner samples are manually reviewed;
- admission/display overrides are typed and explainable;
- topic-preference samples do not pull unsuitable rows into ordinary admission;
- SRS quality harness passes for supported pairs;
- generated runtime resources are packaged, fingerprinted, and tested.

It is not ready merely because one sweep wins calibration.

## Cleanup Before Starting The Next Plan

Before moving from difficulty ranking to another product plan, do this cleanup:

1. Commit or explicitly ignore the accepted runtime resource, manual correction
   file, scripts, and compact evidence artifacts.
2. Leave bulky duplicate CSVs, matrices, and exploratory bakeoff outputs
   uncommitted unless a document directly depends on them as canonical
   evidence.
3. Keep one acceptance candidate doc current, and route older experiment docs
   through it instead of treating every `latest` artifact as canonical.
4. Verify the packaged resource path is the runtime default and the environment
   variable remains an experiment override.
5. Regenerate a product admission pack after any correction-layer change.
6. Re-run the SRS quality harness after any runtime/admission/publication
   change.
7. Record topic coverage gaps separately from difficulty-ranking quality.

For the current en-ja checkpoint, the largest nonblocking cleanup item is the
untracked generated `docs/test_outputs` debris from exploratory runs. Those
files should be deleted, archived outside the repo, or intentionally committed
only if they become canonical evidence. They are not required for the packaged
runtime ranking.
