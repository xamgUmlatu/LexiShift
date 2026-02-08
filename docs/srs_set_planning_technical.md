# SRS Set Planning Technical Notes

Related design:
- `docs/srs_hybrid_model_technical.md`

## Purpose
Define how set `S` is planned and mutated:
- bootstrap `S` initially
- grow/refresh `S` over time
- keep scheduling and admission responsibilities separated

## Scope boundary
- Planner chooses strategy and returns execution metadata.
- Scheduler handles review timing from feedback.
- Planner must not treat passive display as a scheduling event.

## Modules

- `core/lexishift_core/srs_set_strategy.py`
  - Strategy/objective constants and normalization.
- `core/lexishift_core/srs_set_planner.py`
  - Request/response model and planning logic.
- `core/lexishift_core/srs_set_policy.py`
  - Centralized sizing policy defaults, clamps, and normalization.
- `core/lexishift_core/srs_signal_queue.py`
  - Event queue storage and summarization.
- `core/lexishift_core/helper_engine.py`
  - `plan_srs_set(...)` planner API.
  - `initialize_srs_set(...)` mutation API.

## Strategy matrix

- `frequency_bootstrap`
  - Status: executable.
  - Behavior: initialize `S` from frequency + dictionary constraints.

- `profile_bootstrap`
  - Status: scaffolded fallback.
  - Behavior: planner accepts profile context, currently executes as frequency bootstrap.

- `profile_growth`
  - Status: planner-only.
  - Behavior: returns requirements/notes; no mutation yet.

- `adaptive_refresh`
  - Status: planner-only.
  - Behavior: intended to refresh `S` using aggregated feedback trends.
  - Current scaffold note: planner diagnostics may still request both `feedback_signals` and `exposure_signals`; exposure remains non-authoritative unless policy changes.

## Native helper API

- `srs_plan_set`
  - Input:
    - `pair`, `strategy`, `objective`, `replace_pair`, `profile_context`, `trigger`
    - sizing: `bootstrap_top_n` (preferred), `initial_active_count`, `max_active_items_hint`
    - compatibility: `set_top_n` (legacy alias for bootstrap size)
  - Output: plan metadata, signal summary, existing pair counts.
  - Side effects: none.

- `srs_initialize`
  - Input: same planning fields + sources (`jmdict_path`, `set_source_db`).
  - Output: plan metadata + mutation result (`applied`, counts).
  - Side effects: updates helper-owned `srs/profiles/<profile_id>/srs_store.json` only when plan is executable.

## Sizing policy (implemented)

All sizing normalization is centralized in `srs_set_policy.py` to avoid duplicated magic numbers.

Current constants:
- `DEFAULT_BOOTSTRAP_TOP_N = 800`
- `MIN_BOOTSTRAP_TOP_N = 200`
- `MAX_BOOTSTRAP_TOP_N = 50000`
- `DEFAULT_INITIAL_ACTIVE_COUNT = 40`
- `MIN_INITIAL_ACTIVE_COUNT = 1`
- `MAX_INITIAL_ACTIVE_COUNT = 5000`

Resolution algorithm:
1. Resolve requested bootstrap size from `bootstrap_top_n`; if missing, use `set_top_n`; if invalid, default to `800`.
2. Clamp bootstrap size to `200..50000`.
3. Resolve `max_active_items_hint` (optional), clamp to `1..5000` when present.
4. Resolve `initial_active_count`; if missing/invalid, use `max_active_items_hint` when present, otherwise default to `40`.
5. Clamp `initial_active_count` to `1..5000`, then clamp again so it never exceeds effective bootstrap size.
6. Emit policy notes in planner output whenever defaults/clamps are applied.

Current mutation behavior:
- Bootstrap builds candidate pool from `bootstrap_top_n`, then admits only `initial_active_count` unique lemmas into persisted inventory `S`.
- Items outside that admitted subset are excluded from `S` (implicit zero probability in sparse representation).
- Review scheduling still remains feedback-driven and due-based after admission.

## Event model

Queue path:
- `srs/profiles/<profile_id>/srs_signal_queue.json`

Event types supported by storage:
- `feedback`
- `exposure` (telemetry)

Policy decision for SRS scheduling:
- feedback is authoritative
- exposure is non-authoritative telemetry unless policy explicitly opts in later

## Extension/options integration

- Options action: "Initialize S for this pair".
- Current payload includes:
  - `strategy: "profile_bootstrap"`
  - `objective: "bootstrap"`
  - `profile_context`
  - `bootstrap_top_n`
  - `initial_active_count`
  - `max_active_items_hint`
  - `trigger: "options_initialize_button"`
- Current executable fallback remains frequency bootstrap.

## Planned implementation steps

1. Implement profile-aware candidate weighting for `profile_bootstrap`.
2. Implement executable `profile_growth` for controlled admission into `S`.
3. Add feedback-window aggregation for `adaptive_refresh`.
4. Add policy registry by pair/domain to route strategy defaults.
5. Add UI surfaces to edit profile signals and inspect planner diagnostics.
