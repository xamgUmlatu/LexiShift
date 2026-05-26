# SRS Admission Lifecycle Current State

Status: current audit
Last verified: 2026-05-26 by source audit, browsing refresh preview tests, fractional browsing-budget tests, SRS lifecycle marker tests, SRS reset suppression-metadata tests, lifecycle-aware scheduler/growth/rulegen tests, SRS quality harness with seeded browsing signal, changed-file gate, and feature-state audit
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
| `srs_refresh` | Yes when budget allows | Yes when budget allows | Yes when new items are admitted | Manual growth admission. This is the intended future browsing-influenced mutation point. |
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

- `frequency_bootstrap` is the default native-host strategy.
- `profile_bootstrap` is implemented but not the default helper init strategy.
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
- `SrsSettings.max_new_items_per_day`, default `8`
- current due count from `select_active_items`
- due pressure threshold, default pause above `0.80`
- feedback-window size, default `100`
- low-retention pause below `0.55`
- mid-retention partial admission below `0.70`
- optional request overrides for max active, max new, feedback window, and POS

Candidate selection uses frequency seeds converted to selector candidates.
Existing lemmas are filtered by `grow_srs_store`, so refresh does not duplicate
already admitted lemmas for the same pair.

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
