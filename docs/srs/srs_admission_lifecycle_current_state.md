# SRS Admission Lifecycle Current State

Status: current audit
Last verified: 2026-05-27 by source audit, active-capacity refresh tests, browsing refresh preview tests, fractional browsing-budget tests, SRS lifecycle marker tests, SRS reset suppression-metadata tests, lifecycle-aware scheduler/growth/rulegen tests, admitted-at persistence tests, SRS quality harness with seeded browsing signal and encounter-watch scenario, changed-file gate, and feature-state audit
Purpose: record executable truth for how words enter, remain in, and leave the active SRS path before browsing-based admission can mutate real admission
Source-of-truth: this is a code-backed audit; executable truth lives in the referenced helper/core modules and tests.

## Executive Summary

Browsing signals should enter real SRS mutation only through the existing
`srs_refresh` admission path. That path already owns capacity, due-pressure,
feedback-retention, existing-lemma, POS, pair-resource, inventory, and rulegen
publication checks.

This audit found one important gap and closed it across active SRS serving:
lifecycle suppression and non-active lifecycle states now block candidate
admission, due selection, active-inventory fallback, and rulegen publication. A
helper/native-host writer can now persist durable suppression entries and mark
existing SRS items as `discarded` for discard/block flows. The options
dashboard can now surface admitted SRS items and trigger a confirmed durable
discard for eligible words; its refresh metadata, local filters, pagination, and
learner-facing rule summaries are dashboard-only views of the already-loaded
payload. There is intentionally no cooldown UX in the extension feedback popup.
Restore, mastered, and release actions remain open product work.

## Admission Entry Points

| Entry point | Mutates store | Mutates active inventory | Publishes rulegen | Current role |
| --- | --- | --- | --- | --- |
| `srs_initialize` | Yes | Yes | Yes | Initial `S` bootstrap for a pair/profile. |
| `srs_refresh` | Yes when budget allows | Yes when budget allows | Yes when new items are admitted | Manual profile-growth admission. This is the intended future browsing-influenced mutation point. |
| `srs_rebalance_apply` | Yes when activating new seeds | Yes | Yes when applied | Replaces swappable active items; not full deletion/release. |
| `record_feedback` | Yes | No direct inventory write | No | Scheduler feedback; can create missing store rows and should not be reused as browsing admission. |
| `record_exposure` | Yes | No direct inventory write | No | Passive exposure count; can create missing store rows and should not be reused as browsing admission. |
| `srs_browsing_signal_ingest` | No SRS item mutation | No | No | Opt-in aggregate signal ingest only. |
| `srs_admission_suppress` | Yes when item exists | Yes when item is active | No | Backend durable discard/block primitive: writes suppression, marks existing item `discarded`, and removes it from active inventory. |

Native-host routing is in `scripts/helper/lexishift_native_host.py`. Helper
execution lives mainly in:

- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
- `core/lexishift_core/helper/use_cases/signals.py`

## Initial Bootstrap

`srs_initialize` calls `initialize_srs_set`, which resolves pair capability,
frequency resources, profile id, store, inventory, set sizing, and rulegen
requirements before mutating state.

Sizing is centralized in `core/lexishift_core/srs/set_policy.py`:

- default `bootstrap_top_n`: `800`
- default `initial_active_count`: `40`
- `bootstrap_top_n` clamp: `200..50000`
- `initial_active_count` clamp: `1..5000`
- `initial_active_count` is capped by effective `bootstrap_top_n`

Bootstrap selection is in `core/lexishift_core/helper/rulegen.py`:

- `frequency_bootstrap` is the no-strategy native-host baseline.
- `profile_bootstrap` is executable when requested; options initialize and
  admission preview request it with current profile context.
- Selection policy defaults to deterministic `top_n`; weighted without
  replacement is supported only when explicitly requested by config.
- The helper writes store rows, writes active inventory ids, then publishes
  rulegen outputs for active ids.

Browsing signals should not affect initial bootstrap for MVP. Bootstrap is too
coarse and too sticky for passive browsing history.

## Manual Refresh Admission

`srs_refresh` calls `refresh_srs_set`, then `apply_admission_refresh`.

Refresh budget is controlled by:

- `SrsSettings.max_active_items`, default `40`
- active SRS item count for the pair, counted from active store rows
- `SrsSettings.max_new_items_per_day`, default `8` (currently a per-refresh
  admission cap, not a separate calendar-day ledger)
- current due count from `select_active_items`
- due pressure threshold, default pause above `0.80`
- feedback-window size, default `100`
- low-retention pause below `0.55`
- mid-retention partial admission below `0.70`
- optional request overrides for max active, max new, feedback window, and POS

Candidate selection defaults to `profile_growth`: frequency seeds are converted
through the profile-aware admission scorer, then selected by the same growth
planner used by ordinary SRS admission. Existing lemmas are filtered by
`grow_srs_store`, so refresh does not duplicate already admitted lemmas for the
same pair.

## Automatic Refresh Trigger

Automatic refresh is a trigger layer around the same `profile_growth`
`srs_refresh` path. It does not change FSRS review scheduling and it does not
admit words directly.

The extension feedback sync queue calls `srs_auto_refresh` after a successful
helper feedback flush. The helper reads `srs_signal_queue.json`, compares the
new feedback since the last automatic attempt against the profile/pair policy,
and only then attempts the normal refresh path.

Default trigger policy:

- automatic refresh enabled
- at least `8` feedback events since the last automatic attempt
- at least `6` `good`/`easy` events for the first attempt on a UTC day
- at least `12` new `good`/`easy` events for another attempt on the same UTC day
- `90` minute cooldown between automatic attempts

These values are exposed in the SRS options UI. The same refresh safety gates
still apply after the trigger is eligible: active capacity, due pressure,
retention, POS/lifecycle filtering, suppression, source readiness, and rulegen
publication. `max_new_items_per_day` is still a per-refresh cap unless a future
calendar-day ledger is added.

Helper-owned automatic trigger state lives at
`srs/profiles/<profile_id>/srs_auto_refresh_state.json` and is reset with SRS
data for the selected profile/pair. The state records attempts and successful
applications so the helper does not repeatedly run heavy refresh work for the
same feedback window.

Current lifecycle guard:

- `refresh_srs_set` loads the profile suppression store from
  `srs_admission_suppression.json`.
- Expired entries are pruned during persistent refresh.
- Active suppressed lemmas are passed to `AdmissionRefreshPolicy.blocked_lemmas`.
- `apply_admission_refresh` filters blocked lemmas and non-active store
  lifecycle states before growth selection and reports `blocked_by_lifecycle`
  plus `blocked_lemmas` in diagnostics.
- `grow_srs_store` counts only active store items toward existing active
  capacity and blocks non-active store lemmas from re-admission.
- `select_active_items` ignores non-active lifecycle states, so discarded or
  cleared items do not create due pressure.
- Helper rulegen target loading, word-package loading, and SRS rule metadata
  annotation ignore non-active lifecycle states, so stale inventory ids cannot
  publish discarded or cleared items.

This makes refresh the safest place to add browsing boost later: browsing can
change candidate score pressure, but it still cannot exceed refresh budgets or
override active suppression.

Current browsing preview:

- `preview_browsing_admission_refresh` reuses the same refresh decision,
  allowed-POS filter, lifecycle blocklist, existing-store filter, and candidate
  scoring policy.
- `refresh_srs_set` includes `browsing_admission_preview` in its response.
- The preview reads the profile/pair browsing aggregate store and simulates
  `Off`, `Balanced`, and `Strong`.
- The preview uses fractional small-budget realization, so `Balanced` can earn
  one browsing lane when the computed fractional lane is meaningful and
  browsing signal exists.
- The preview is diagnostic only: `applied_to_actual_admission` is `False`,
  `runtime_srs_mutation` is `False`, and actual refresh selection remains
  neutral until a later gated runtime decision.

## Rebalance

`srs_rebalance_apply` is not a broad admission refresh. It constructs a target
active set and can park swappable active items while activating better
candidates.

Protection rules in `core/lexishift_core/srs/rebalance.py` keep established
items active when any of these hold:

- history count is at least `4`
- stability is at least `14`
- scheduler state is `review` and next due is at least `7` days out

Parked items remain in the store. Rebalance changes active inventory membership;
it is not permanent deletion and not a "fully mastered/released" lifecycle.

Browsing signals should not drive rebalance until the product explicitly wants
passive browsing to displace active words. That is not needed for MVP.

## Release, Mastery, Discard, And Suspend

Current persisted `SrsItem` fields include scheduler state, scheduler step,
stability, difficulty, last review, next due, exposures, history, source type,
confidence, word package metadata, and lifecycle metadata:

- `lifecycle_state`: `active`, `discarded`, or `cleared`;
- `lifecycle_reason`: freeform backend reason such as `user_blocked`;
- `lifecycle_updated_at`: timestamp of the lifecycle marker.

Current related mechanisms:

- FSRS states map to `learning`, `review`, and `relearning`.
- Selector candidates have a `mastered` penalty concept, but no current helper
  path writes a durable mastered flag into SRS store items.
- Rebalance has `active_protected`, `active_swappable`, `retained_parked`, and
  `new_seed` planning states, but these are active-inventory states, not full
  lifecycle states.
- `core/lexishift_core/srs/admission_suppression.py` defines discarded,
  suspended, user-blocked, and manual-cooldown suppression entries. The current
  product direction is not to expose cooldown as a regular learner workflow.
- The helper writer defaults to `user_blocked`, which has no expiry. That better
  matches a future rare "discard this specific word" action than a temporary
  reshow policy.
- `core/lexishift_core/helper/use_cases/admission_suppression.py` writes the
  profile suppression store, marks an existing matching SRS item as
  `lifecycle_state=discarded`, and removes that item from active inventory. If
  the item is not in the SRS store yet, the suppression store still blocks future
  refresh admission.
- `core/lexishift_core/srs/scheduler.py`, `core/lexishift_core/srs/growth.py`,
  and `core/lexishift_core/helper/rulegen.py` all treat non-active lifecycle
  states as ineligible for active serving.
- `reset_srs_data` clears suppression metadata by default when resetting a pair
  or all SRS data. A backend `preserve_lifecycle_metadata` flag exists for a
  future confirmation UX that lets the learner keep durable discard/block
  metadata during reset.

Current visibility/action surface: the options page can list admitted SRS words
for the selected pair/profile through the read-only `srs_items_list`
helper/native-host route. The view separates learner-facing status from
advanced scheduler and lifecycle details, can show read-only published-rule
summaries, can load capped published-rule details for one selected row through
the read-only `srs_item_rule_details` route, and can locally search/filter/sort
and paginate the already-loaded payload. Eligible rows expose a confirmed
Discard action that reuses the existing `srs_admission_suppress` route with
`reason=user_blocked`.

Open gap: full user-facing lifecycle management is still not implemented. The
guard exists, refresh respects it, and dashboard discard can write it, but the
product still needs explicit actions and policy for restore, release, and
mastered-state management. Known words should primarily advance through normal
SRS feedback (`easy`), not through a cooldown UX.

## Encounter Starvation Risk

Interest-tailored admission can admit correct but rarely encountered target
words. For example, a strong Animals preference can admit specialized animal
lemmas whose replacement rules almost never match the learner's normal browsing.
If those words stay active but receive few or no replacement exposures, the
learner may have no natural chance to give `good` or `easy` feedback. They can
then occupy active capacity and slow or block future admission.

Current mitigations:

- the reserved topic lane is capped, so a strong topic preference does not fill
  the whole batch;
- frequency, proficiency/readiness, POS, source, and rulegen gates still apply;
- refresh admission has hard capacity, new-item, due-pressure, and retention
  gates;
- newly admitted items persist `admitted_at`, allowing the dashboard to separate
  newly unseen words from stale-unseen words by age threshold;
- the SRS quality harness now verifies the dashboard encounter-watch contract
  for fresh unseen, stale unseen, legacy age-unknown, reviewed, and
  no-enabled-rule active items;
- the dashboard discard route can remove a specific unwanted active item;
- passive exposure counts exist and are intentionally non-authoritative for
  scheduling.

Current gap:

- there is no automatic stale-active policy that clears, releases, or parks a
  low-exposure item in a way that frees refresh capacity;
- rebalance can change active inventory membership, but refresh capacity is
  currently counted from active lifecycle store items for the pair, so inventory
  parking alone is not enough to solve starvation;
- durable mastered/released semantics remain open.

Before broad tester handoff, this needs an explicit product contract. The
recommended MVP contract is:

1. Keep feedback as the only event that advances FSRS scheduling.
2. Treat passive exposure as evidence for servability/staleness diagnostics,
   not as recall.
3. Use tester-visible diagnostics for active words with zero/low exposure and
   no feedback, including the current `7` day stale-unseen threshold as a
   tuning value rather than a release action.
4. Add or schedule a stale-active release/clear policy that can free admission
   capacity without pretending the user learned the word.
5. Keep manual discard for rare user rejection, not routine cooldown.

## Feedback And Exposure Caveat

The current feedback/exposure helper path uses `create_if_missing=True`.
Therefore a feedback or exposure event can create a store row for a missing
lemma without adding that item to the active inventory.

If an inventory file exists, active publication follows inventory ids and those
new rows do not automatically become active. If no inventory exists, compatibility
fallback can derive active ids from all store rows for that pair.

For browsing-based admission, this means:

- do not route browsing observations through `record_feedback`;
- do not route browsing observations through `record_exposure`;
- keep browsing in its separate aggregate store until an explicit refresh
  admission step consumes it.

## Required Before Runtime Browsing Admission

Before browsing signals can affect actual `srs_refresh`, keep these conditions:

1. Browsing boost applies only inside refresh candidate scoring, after opt-in.
2. Refresh budgets and due-pressure/retention gates remain hard gates.
3. Existing active store lemmas remain filtered out; non-active lifecycle states
   are excluded from active serving.
4. Active suppression remains filtered out.
5. Browsing events never update FSRS scheduling fields.
6. Browsing events never create `SrsItem` rows directly.
7. Diagnostics show neutral score, browsing signal, final score, budget lane,
   and lifecycle suppression counts.
8. User-facing clear/disable controls for browsing signals exist before
   default-on behavior.
