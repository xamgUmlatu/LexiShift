# Native Messaging Helper Workstream Checklist

Status key:
- `[ ]` not started
- `[~]` in progress
- `[x]` done

## Phase 0 — Protocol + Schema
- `[x]` Define protocol message envelope + response format.
- `[x]` Define helper output file schemas (ruleset + snapshot + status).
- `[x]` Define storage paths and folder layout.
- `[x]` Add planning/initialization command contracts for set `S`.

## Phase 1 — Helper Core (local-only)
- `[x]` Implement helper CLI entrypoint (`lexishift_helper`).
- `[x]` Implement `status` command (reads/writes `srs_status.json`).
- `[x]` Implement `run_rulegen` command (calls core rulegen pipeline).
- `[x]` Implement `plan_srs_set` command (planner-only response).
- `[x]` Implement `init_srs_set` command (explicit set mutation).
- `[x]` Implement `get_snapshot` command (loads pair snapshot JSON).
- `[x]` Implement `record_feedback` command (append to SRS store).
- `[x]` Implement `record_exposure` command (append to SRS store).
- `[x]` Persist feedback to `srs_signal_queue.json` (authoritative scheduling signal).
- `[x]` Persist exposure telemetry to `srs_signal_queue.json` (non-authoritative).
- `[x]` Add centralized set sizing policy with explicit defaults/clamps.
- `[x]` Add POS-aware bootstrap admission scoring with explicit coefficients (no inline magic numbers).
- `[x]` Add helper-side stopword filtering for bootstrap candidates (strict JSON array format).
- `[x]` Add feedback-window admission refresh policy module (`admission weight` vs `serving priority` separation).
- `[~]` Add richer logging + error reporting to helper.

## Phase 2 — Native Messaging Host
- `[x]` Create native messaging host wrapper for macOS.
- `[x]` Create native messaging host wrapper for Windows.
- `[x]` Validate incoming payloads (schema + allowed commands).
- `[x]` Wire host to helper commands including set planning/init.
- `[x]` Add handshake (`hello`) and version checks.
- `[x]` Add `srs_refresh` helper command route for feedback-driven admissions.

## Phase 3 — Extension Client
- `[x]` Add helper bridge client (getStatus/getSnapshot/getRuleset).
- `[x]` Add helper bridge methods for `srs_plan_set` and `srs_initialize`.
- `[x]` Route helper requests through extension service worker bridge (single native messaging boundary).
- `[x]` Options: “Helper status” + “Refresh now”.
- `[x]` Options: explicit “Initialize S for this pair” action.
- `[x]` Options: explicit “Refresh S + publish rules” action.
- `[x]` Send profile-context scaffold to helper from options flow.
- `[x]` Send explicit sizing controls (`bootstrap_top_n`, `initial_active_count`, `max_active_items_hint`).
- `[x]` Replace rulegen preview to non-mutating helper flow.
- `[x]` Add sampled helper-side rulegen preview using probabilistic sampling from current `S`.
- `[x]` Content script: fetch helper ruleset when SRS enabled.
- `[x]` Fallback to cached ruleset if helper offline.
- `[x]` Persistent feedback sync queue with retry/backoff for `record_feedback`.

## Phase 4 — Background Scheduling
- `[x]` Start helper tray at login on macOS (LaunchAgent).
- `[x]` Schedule periodic rulegen (daemon loop).
- `[ ]` Trigger planner-driven refresh on signal thresholds.
- `[ ]` Add policy to decide bootstrap vs growth vs adaptive refresh.
- `[x]` Publish runtime rules at initialization and after refresh admissions.

## Phase 5 — UI + Diagnostics
- `[~]` Show helper status in GUI app (last sync detail still limited).
- `[x]` Auto-install helper on first launch when fixed ID is available.
- `[x]` Add “Install/Reinstall Helper” repair action in SRS settings.
- `[x]` Show set planning details in options output (strategy/sizing/applied state + bootstrap diagnostics).
- `[x]` Show admission-weight diagnostics in options output (profile + weighted preview).
- `[x]` Add runtime diagnostics action showing helper state, extension cache, and current tab rule counts.
- `[x]` Surface last helper-rules fetch error from tab runtime in diagnostics.
- `[ ]` Add dedicated logs/health view for signal queue + planner decisions.

## Phase 6 — End-to-End QA and refresh loop
- `[ ]` Add E2E native messaging test flow for initialize -> sampled rulegen -> feedback submit -> resample.
- `[ ]` Validate retry/backoff + idempotency semantics under helper restarts.
- `[~]` Add helper-side integration test coverage for feedback-driven admission refresh decisions.
- `[ ]` Add planner-trigger test for threshold-based automatic refresh from aggregated feedback.
- `[ ]` Add explicit service-worker bridge roundtrip tests (options + content runtime request paths).

## Open Questions
- `[x]` Choose SRS store format for current helper implementation (JSON in `srs/`).
- `[ ]` Define rulegen/refresh cadence and thresholds per strategy.
- `[ ]` Decide on shared secret/auth between helper and extension.
