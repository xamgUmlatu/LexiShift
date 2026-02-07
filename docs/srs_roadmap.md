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
- Extension runtime applies local rules and helper SRS rules concurrently.
- Extension-to-helper communication is routed through the extension service worker bridge (single native messaging boundary).
- Runtime diagnostics now include helper/store/ruleset/cache counts plus the last helper rules fetch error from the tab runtime.

### Set planning scaffolding
- `srs_set_strategy.py`: strategy/objective taxonomy.
- `srs_set_policy.py`: centralized sizing policy/defaults/clamps.
- `srs_set_planner.py`: plan metadata + diagnostics.
- `srs_plan_set` helper command: no side effects.
- `srs_initialize` helper command: mutation via executable strategy.
- Bootstrap admission policy now applies explicit POS buckets with centralized coefficients (non-magic constants).
- JP stopword filtering is active from helper-owned `srs/stopwords/stopwords-ja.json` (or sibling fallback path).

### Feedback pipeline
- Extension popup ratings:
  - `1 -> again`
  - `2 -> hard`
  - `3 -> good`
  - `4 -> easy`
- Helper updates item scheduling fields on feedback.
- Extension helper sync now uses a persistent queue with retry/backoff to submit `record_feedback`.
- Signal queue persists event stream for future aggregation.

### Verified E2E slice (current)
- `srs_initialize` mutates helper-owned `S` (`srs_store.json`) and immediately publishes runtime ruleset/snapshot.
- Runtime replacements from helper-generated SRS rules are active in pages (not just debug preview).
- Local rules continue to work concurrently with SRS rules.
- Feedback UI path (`1..4`) is wired through extension sync queue to helper feedback endpoint.

### Remaining to reach full SRS E2E (feedback -> update -> serving)
- Complete deterministic E2E assertion flow:
  - bootstrap/initialize -> observe replacements -> submit feedback -> verify helper scheduling fields changed -> refresh/admit -> verify serving distribution changed.
- Add automatic refresh policy trigger from aggregated feedback thresholds (today refresh is explicit/manual).
- Add stronger observability for feedback effects:
  - before/after snapshots of `next_due`, `stability`, `difficulty`, and active item counts.
- Harden retry/idempotency semantics under helper restart/offline transitions.
- Improve rule generation quality so SRS-serving words are pedagogically precise (see rulegen quality gap below).

### Rulegen quality gap (current)
- Current JA-target rulegen can emit broad/glossy English source phrases that are semantically too general.
- This produces technically valid replacements but weaker pedagogical quality.
- Immediate quality track:
  - stronger generic-gloss demotion and denylist rules,
  - POS/sense-aware filtering before emission,
  - stricter confidence penalties for broad/ambiguous glosses.

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
- `[x]` POS-aware admission biasing/filtering (explicit default order: noun > adjective > verb > adverb > other).
- `[x]` Helper-side stopword filtering for bootstrap candidates (strict JSON-array format).
- `[x]` Initial active subset admission in bootstrap (`initial_active_count`) now mutates persisted `S`.
- `[ ]` Executable `profile_growth` policy.
- `[ ]` Pair-configurable admission coefficients and denylist controls (helper source of truth).

### Workstream C — Signals and adaptive refresh
- `[x]` Signal queue format + append/read utilities.
- `[x]` Feedback event writes from helper path.
- `[~]` Event aggregation design for refresh decisions.
- `[~]` Feedback-window aggregation for admission updates (separate from due scheduling).
- `[ ]` Persist aggregated admission feedback state (per pair, versioned).
- `[ ]` Automatic `adaptive_refresh` trigger policy.
- `[ ]` Explicit policy gate for any non-feedback signals.
- `[x]` Manual/explicit helper refresh action (`srs_refresh`) for feedback-driven admissions.

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
- `[~]` Unified diagnostics surface for plan + snapshot + ruleset.
- `[x]` Initialization diagnostics now include admission profile + weighted preview of admitted items.
- `[x]` Production publish path: `srs_initialize` now runs rulegen once and persists runtime ruleset/snapshot.
- `[x]` Production publish path: `srs_refresh` immediately runs/persists rulegen when new items are admitted.
- `[x]` Options action for explicit refresh+publish flow (non-debug).
- `[x]` Runtime diagnostics surface: helper store/ruleset + extension cache + current tab rule counts.
- `[x]` Extension runtime consumes helper rules through service-worker bridge (single native messaging boundary).
- `[ ]` Rule quality hardening for broad/ambiguous gloss sources.

### Workstream F — Cross-surface consistency
- `[~]` Bundle format for settings/store exists.
- `[ ]` GUI/extension/plugin import/export wiring.
- `[ ]` Conflict handling when multiple surfaces write feedback concurrently.

### Workstream G — End-to-End validation and calibration
- `[ ]` Define deterministic SRS E2E scenario set (bootstrap -> sampled rulegen -> feedback -> resample).
- `[~]` Add helper integration tests for full feedback loop affecting serving priority.
- `[x]` Add deterministic helper test: feedback updates schedule fields and can trigger `retention_low` admission pause.
- `[x]` Add assertion checks for "no schedule mutation from exposure-only events".
- `[ ]` Add diagnostics snapshots for before/after feedback cycles (store + sampled lemmas).
- `[ ]` Add per-pair calibration report for admission/serving distributions.
- `[ ]` Add E2E checks for post-feedback refresh trigger behavior (manual and future automatic).

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
5. Make POS/stopword admission policy pair-configurable without code edits.

### Phase 3 (adaptive refresh)
1. Aggregate feedback trends in bounded windows.
2. Add refresh trigger thresholds and cooldown.
3. Execute `adaptive_refresh` with audit-friendly logs.

### Phase 4 (E2E + profile integration)
1. Lock an E2E test matrix for extension + helper feedback sync paths.
2. Implement profile-signal normalization and pair-level admission bias persistence.
3. Validate that profile adjustments affect admission (`weight 1`) but not due scheduler math (`weight 2`).
4. Add operator-facing diagnostics for admission drift and refresh decisions.

---

## Terminology
- Historical "seed" should be read as "initial set bootstrap."
- `source_type: initial_set` means "item admitted during bootstrap of S."
- Scheduling remains feedback-driven after admission regardless of initial source type.
