# SRS Roadmap (Set S + Practice Layer)

Related design:
- `docs/srs_hybrid_model_technical.md`

## Goal
Ship a non-destructive SRS layer where:
- `S` is the active study inventory
- scheduling is feedback-driven (1..4 ratings)
- planner strategies control admission/growth of `S`
- rulegen/debug uses current helper-managed `S`

## Current architecture snapshot

### Runtime and storage
- Practice gate and scheduler are implemented.
- Canonical helper store path:
  - `.../LexiShift/srs/srs_store.json`
- Helper also owns:
  - `srs/srs_settings.json`
  - `srs/srs_status.json`
  - `srs/srs_rulegen_snapshot_<pair>.json`
  - `srs/srs_ruleset_<pair>.json`
  - `srs/srs_signal_queue.json`

### Set planning scaffolding
- `srs_set_strategy.py`: strategy/objective taxonomy.
- `srs_set_policy.py`: centralized sizing policy/defaults/clamps.
- `srs_set_planner.py`: plan metadata + diagnostics.
- `srs_plan_set` helper command: no side effects.
- `srs_initialize` helper command: mutation via executable strategy.

### Feedback pipeline
- Extension popup ratings:
  - `1 -> again`
  - `2 -> hard`
  - `3 -> good`
  - `4 -> easy`
- Helper updates item scheduling fields on feedback.
- Extension helper sync now uses a persistent queue with retry/backoff to submit `record_feedback`.
- Signal queue persists event stream for future aggregation.

---

## Workstream tracking

Status key:
- `[ ]` not started
- `[~]` in progress
- `[x]` done

### Workstream A — Review scheduler and practice gate
- `[x]` Core SRS item model + scheduler update function.
- `[x]` Runtime gate integration for active/due items.
- `[x]` Feedback ingestion from extension popup.
- `[~]` Formal lifecycle statuses (`new/learning/review/mature/relearn/suspended`).
- `[ ]` Daily/session budget policy hardening (`max_active`, `max_new_per_day`).

### Workstream B — Set `S` admission and initialization
- `[x]` Frequency bootstrap pipeline for initial `S`.
- `[x]` JMDict-filtered JA bootstrap flow (`en-ja`).
- `[x]` Planner scaffold (`srs_plan_set` + extended `srs_initialize`).
- `[x]` Centralized sizing policy (`bootstrap_top_n`, `initial_active_count`, clamps, diagnostics notes).
- `[~]` Profile-aware weighting in `profile_bootstrap`.
- `[~]` POS-aware admission biasing/filtering (e.g., nouns up, particles/auxiliaries near zero at bootstrap).
- `[x]` Initial active subset admission in bootstrap (`initial_active_count`) now mutates persisted `S`.
- `[ ]` Executable `profile_growth` policy.

### Workstream C — Signals and adaptive refresh
- `[x]` Signal queue format + append/read utilities.
- `[x]` Feedback event writes from helper path.
- `[~]` Event aggregation design for refresh decisions.
- `[ ]` Automatic `adaptive_refresh` trigger policy.
- `[ ]` Explicit policy gate for any non-feedback signals.

### Workstream D — Profile modeling
- `[x]` Profile schema draft and extension scaffold key (`srsProfileSignals`).
- `[~]` Profile signal normalization/validation.
- `[ ]` Profile editor UX (interests/proficiency/objectives/constraints).
- `[ ]` Pair-specific planner policy registry.

### Workstream E — Rulegen and S integration
- `[x]` Rulegen preview made non-mutating.
- `[x]` Helper initialize action exposed in options.
- `[x]` Ensure debug rulegen scopes to current helper-managed `S` only.
- `[x]` Add sampled rulegen debug path (helper-side probabilistic sampling from current `S`).
- `[ ]` Unified diagnostics surface for plan + snapshot + ruleset.

### Workstream F — Cross-surface consistency
- `[~]` Bundle format for settings/store exists.
- `[ ]` GUI/extension/plugin import/export wiring.
- `[ ]` Conflict handling when multiple surfaces write feedback concurrently.

---

## Near-term sequence

### Phase 1 (stabilize model contract)
1. Keep feedback as the only scheduling event.
2. Lock sizing contract (`bootstrap_top_n`, `initial_active_count`, `max_active_items_hint`) and document all clamps/defaults.
3. Document lifecycle statuses and migration path.
4. Keep frequency bootstrap as executable baseline.

### Phase 2 (admission quality)
1. Implement profile-aware scoring for bootstrap/growth admission.
2. Make `initial_active_count` executable in active/frontier serving policy.
3. Add planner diagnostics for why each item entered `S`.
4. Add policy knobs for per-pair new-item pace.

### Phase 3 (adaptive refresh)
1. Aggregate feedback trends in bounded windows.
2. Add refresh trigger thresholds and cooldown.
3. Execute `adaptive_refresh` with audit-friendly logs.

---

## Terminology
- Historical "seed" should be read as "initial set bootstrap."
- `source_type: initial_set` means "item admitted during bootstrap of S."
- Scheduling remains feedback-driven after admission regardless of initial source type.
