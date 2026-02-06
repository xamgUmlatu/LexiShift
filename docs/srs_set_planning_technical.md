# SRS Set Planning Technical Notes

## Purpose
Define the architecture for planning how set `S` is initialized and updated, without forcing full strategy logic implementation up front.

## Modules

- `core/lexishift_core/srs_set_strategy.py`
  - Strategy and objective constants.
  - Normalization helpers.
- `core/lexishift_core/srs_set_planner.py`
  - Planning request/response data structures.
  - `build_srs_set_plan(...)` planner function.
- `core/lexishift_core/srs_signal_queue.py`
  - Signal event model (`feedback`, `exposure`).
  - Queue load/save/append/summarize helpers.
- `core/lexishift_core/helper_engine.py`
  - `plan_srs_set(...)` (planner-only API).
  - `initialize_srs_set(...)` (mutation API with plan metadata).

## Strategy matrix

- `frequency_bootstrap`
  - Status: executable.
  - Behavior: initialize `S` from frequency + dictionary constraints.
- `profile_bootstrap`
  - Status: scaffolded.
  - Behavior: planner currently falls back to `frequency_bootstrap`.
- `profile_growth`
  - Status: planner-only.
  - Behavior: no mutation yet; returns required fields/notes.
- `adaptive_refresh`
  - Status: planner-only.
  - Behavior: no mutation yet; depends on signal aggregation.

## Native helper API

- `srs_plan_set`
  - Input: `pair`, `strategy`, `objective`, `set_top_n`, `replace_pair`, `profile_context`, `trigger`.
  - Output: plan metadata + signal summary + existing pair counts.
  - Side effects: none.

- `srs_initialize`
  - Input: `pair`, data sources, plus planning inputs above.
  - Output: same plan metadata + mutation result (`applied`, counts).
  - Side effects: updates `srs_store.json` only when plan is executable and mode is supported.

## Signal queue model

Path:
- `srs/srs_signal_queue.json`

Event types:
- `feedback`
- `exposure`

Current producers:
- `apply_feedback(...)` in helper engine.
- `apply_exposure(...)` in helper engine.

Current consumers:
- Planner summaries (`summarize_signal_events`).

Future consumers:
- Adaptive refresh orchestration service.

## Extension scaffolding

- New options action:
  - “Initialize S for this pair”
- Planner context source:
  - `srsProfileSignals[pair]` from extension storage.
  - `srsMaxActive` constraint.
- Payload now includes:
  - `strategy: "profile_bootstrap"`
  - `objective: "bootstrap"`
  - `profile_context`
  - `trigger: "options_initialize_button"`

## Planned next implementation steps

1. Implement profile-aware candidate weighting for `profile_bootstrap`.
2. Add signal-window aggregation and thresholds for `adaptive_refresh`.
3. Add dedicated UI to edit `srsProfileSignals`.
4. Add reconciliation between extension local SRS logs and helper store/signal queue.
