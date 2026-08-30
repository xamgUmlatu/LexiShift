# SRS Set Planning Technical Notes

Status: active mixed technical reference
Role: Mixed
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 normalization plus SRS-adjacent doc/code/test read; set-planning content not fully re-audited
Purpose: document current SRS planning modules, helper APIs, sizing policy, strategy status, and planned follow-through
Source-of-truth: mixed technical reference; current planning/mutation truth lives in SRS planner/policy code, helper use cases, and SRS harness/tests.

Related design:
- `docs/srs/srs_hybrid_model_technical.md`

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

- `core/lexishift_core/srs/set_strategy.py`
  - Strategy/objective constants and normalization.
- `core/lexishift_core/srs/set_planner.py`
  - Request/response model and planning logic.
- `core/lexishift_core/srs/set_policy.py`
  - Centralized sizing policy defaults, clamps, and normalization.
- `core/lexishift_core/srs/signal_queue.py`
  - Event queue storage and summarization.
- `core/lexishift_core/helper/engine.py`
  - `plan_srs_set(...)` planner API.
  - `initialize_srs_set(...)` mutation API.

## Strategy matrix

- `frequency_bootstrap`
  - Status: executable.
  - Behavior: initialize `S` from frequency + dictionary constraints.

- `profile_bootstrap`
  - Status: executable when requested.
  - Behavior: applies profile-aware scoring and capped reserved topic-lane
    selection to the frequency seed frontier. Options initialize and admission
    preview explicitly request this strategy.

- `profile_growth`
  - Status: executable for refresh/growth admission and dedicated rebalance.
  - Behavior: refresh/growth admission reuses the profile-bootstrap utility
    model over the current eligible seed frontier, then applies the normal SRS
    capacity, due-pressure, retention, POS, and lifecycle gates before adding
    new items into `S`. Dedicated rebalance preview/apply also keep
    `profile_growth` as the effective strategy for inventory-aware replacement.

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
  - Current execution note:
    - `strategy_requested="profile_bootstrap"` reports
      `strategy_effective="profile_bootstrap"` and executes the profile-aware
      reserved topic-lane selector over the frequency seed frontier while
      returning profile-bootstrap diagnostics.

## Sizing policy (implemented)

All sizing normalization is centralized in `srs/set_policy.py` to avoid duplicated magic numbers.

Current constants:
- `DEFAULT_BOOTSTRAP_TOP_N = None` (all available seed rows)
- `MIN_BOOTSTRAP_TOP_N = 200` for explicit finite overrides
- `MAX_BOOTSTRAP_TOP_N = 50000` for explicit finite overrides
- `DEFAULT_INITIAL_ACTIVE_COUNT = 40`
- `MIN_INITIAL_ACTIVE_COUNT = 1`
- `MAX_INITIAL_ACTIVE_COUNT = 5000`

Resolution algorithm:
1. Resolve requested bootstrap size from `bootstrap_top_n`; if missing, use `set_top_n`; if still missing/invalid, use all available seed rows.
2. Clamp explicit finite bootstrap size to `200..50000`.
3. Resolve `max_active_items_hint` (optional), clamp to `1..5000` when present.
4. Resolve `initial_active_count`; if missing/invalid, use `max_active_items_hint` when present, otherwise default to `40`.
5. Clamp `initial_active_count` to `1..5000`; if an explicit finite bootstrap size is present, clamp again so it never exceeds that size.
6. Emit policy notes in planner output whenever defaults/clamps are applied.

Current mutation behavior:
- Bootstrap builds the candidate pool from all available seed rows by default, or from explicit `bootstrap_top_n` when a finite override is supplied, then admits only `initial_active_count` unique lemmas into persisted inventory `S`.
- Helper-driven SRS flows cache source-normalized seed rows under
  `srs/cache/seed_frontiers/` so full-frontier bootstrap does not repeat
  frequency/JMDict/POS/package/classification work on every request. The cache
  is keyed by source freshness and seed config, excludes profile-specific
  scoring, and falls back to rebuilding on miss, stale key, or corrupt file.
- Cache preparation is also available as a profile-independent lifecycle
  operation. `srs_seed_cache_status` and `srs_seed_cache_prepare` report or
  warm the cache for a pair, while resource-pack warmup maps installed packs to
  affected SRS pairs. Cache writes use a single-flight lock, stale cache cleanup
  keeps old fingerprints bounded, and blocked warmups report missing companion
  resources without changing admission behavior.
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
- Planner diagnostics now normalize `profile_context` and expose profile-bootstrap summaries.
- Current helper execution resolves that path to
  `strategy_effective="profile_bootstrap"` /
  `execution_mode="profile_bootstrap"`.

## Planned implementation steps

1. Add feedback-window aggregation for `adaptive_refresh`.
2. Add policy registry by pair/domain to route strategy defaults.
3. Expand UI diagnostics for profile signal coverage and planner decisions.
