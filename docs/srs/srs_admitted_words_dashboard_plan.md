# SRS Admitted Words Dashboard Plan

Status: active implementation contract
Role: Mixed product decision plus current dashboard implementation contract
Last updated: 2026-05-26
Last verified: 2026-05-26 helper/options dashboard tests, durable discard
workflow tests, and SRS quality harness
Purpose: document the user-facing SRS admitted-words dashboard decision, the
current dashboard lifecycle action contract, and deferred lifecycle actions
Source-of-truth: product decision and UI contract live here; executable truth
lives in helper endpoints, options-page code, tests, and
`docs/developer/feature_state_matrix.md`.

## Decision

The admitted-words viewer is a user-facing learning dashboard, not a developer
diagnostic panel.

Default view should show useful learner concepts:

- total admitted words for the selected profile/pair;
- active words;
- due now and due soon words;
- queued admitted words that are not currently active;
- removed words, including discarded or cleared items;
- per-word display text, due status, review count, exposure count, and source
  label.

Technical details belong behind an Advanced details toggle:

- item id;
- lifecycle state/reason/update timestamp;
- scheduler state and step;
- confidence, stability, and difficulty;
- normalized word-package details when needed later.

## Lifecycle UX Policy

The SRS feedback popup remains a review-feedback surface. It should not grow
regular cooldown controls.

Current product direction:

- known words should normally move forward through SRS feedback such as `easy`;
- if a learner dislikes a specific word, the dashboard can durably discard it
  and block it from refresh admission;
- discard should be rare and explicit, not a routine temporary cooldown flow;
- reset SRS data clears discard/block suppression metadata by default, matching
  a fresh start;
- a later reset confirmation may offer "keep discarded words" by using the
  existing backend `preserve_lifecycle_metadata` flag.

## Current Implementation Contract

Read/listing path:

- helper/native-host exposes `srs_items_list`;
- the endpoint is pair/profile scoped and read-only;
- the endpoint reads `srs_store.json` and `srs_inventory.json`;
- active membership uses the existing active-inventory resolver, including
  store fallback when no pair inventory exists;
- non-active lifecycle states are visible in the dashboard but remain ineligible
  for active serving elsewhere;
- options.html exposes a Learning words dashboard with Refresh words and an
  Advanced details toggle.

The listing endpoint should not:

- mutate SRS items;
- write lifecycle states;
- admit new words;
- change due scheduling;
- publish rulegen outputs.

Discard path:

- dashboard rows for eligible active/queued/due words expose a small Discard
  action;
- the action confirms before mutation;
- the action calls the existing `srs_admission_suppress` helper/native-host
  route with `reason=user_blocked`;
- the helper writes durable suppression metadata, marks an existing matching
  SRS item `discarded`, and removes it from active inventory;
- the dashboard refreshes after discard so the word appears as removed/
  discarded.

## Deferred Work

Next product slices, after dashboard discard is stable:

1. Search/filter/sort for large admitted sets.
2. Optional right-click popup discard affordance, kept discrete beside review
   ratings.
3. A confirmed restore/undo policy if discarded items should ever return.
4. Full mastered/released lifecycle semantics, if normal FSRS feedback is not
   enough for known-word dropoff.

## Release Boundary

The dashboard is acceptable for MVP when:

- the read-only endpoint and options UI are covered by focused tests;
- dashboard discard is covered by focused workflow tests and uses the existing
  suppression route;
- SRS quality harness still passes after the helper route lands;
- the feature-state matrix records dashboard discard separately from
  restore/mastery/release controls;
- docs do not claim restore/mastery UX is shipped.
