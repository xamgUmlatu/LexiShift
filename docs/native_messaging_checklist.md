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
- `[~]` Add richer logging + error reporting to helper.

## Phase 2 — Native Messaging Host
- `[x]` Create native messaging host wrapper for macOS.
- `[x]` Create native messaging host wrapper for Windows.
- `[x]` Validate incoming payloads (schema + allowed commands).
- `[x]` Wire host to helper commands including set planning/init.
- `[x]` Add handshake (`hello`) and version checks.

## Phase 3 — Extension Client
- `[x]` Add helper bridge client (getStatus/getSnapshot/getRuleset).
- `[x]` Add helper bridge methods for `srs_plan_set` and `srs_initialize`.
- `[x]` Options: “Helper status” + “Refresh now”.
- `[x]` Options: explicit “Initialize S for this pair” action.
- `[x]` Send profile-context scaffold to helper from options flow.
- `[x]` Send explicit sizing controls (`bootstrap_top_n`, `initial_active_count`, `max_active_items_hint`).
- `[x]` Replace rulegen preview to non-mutating helper flow.
- `[x]` Content script: fetch helper ruleset when SRS enabled.
- `[x]` Fallback to cached ruleset if helper offline.
- `[x]` Persistent feedback sync queue with retry/backoff for `record_feedback`.

## Phase 4 — Background Scheduling
- `[x]` Start helper tray at login on macOS (LaunchAgent).
- `[x]` Schedule periodic rulegen (daemon loop).
- `[ ]` Trigger planner-driven refresh on signal thresholds.
- `[ ]` Add policy to decide bootstrap vs growth vs adaptive refresh.

## Phase 5 — UI + Diagnostics
- `[~]` Show helper status in GUI app (last sync detail still limited).
- `[x]` Auto-install helper on first launch when fixed ID is available.
- `[x]` Add “Install/Reinstall Helper” repair action in SRS settings.
- `[~]` Show set planning details in options output.
- `[ ]` Add dedicated logs/health view for signal queue + planner decisions.

## Open Questions
- `[x]` Choose SRS store format for current helper implementation (JSON in `srs/`).
- `[ ]` Define rulegen/refresh cadence and thresholds per strategy.
- `[ ]` Decide on shared secret/auth between helper and extension.
