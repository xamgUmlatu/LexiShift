# Native Messaging Helper Workstream Checklist

Status key:
- [ ] not started
- [~] in progress
- [x] done

## Phase 0 — Protocol + Schema
- [x] Define protocol message envelope + response format.
- [x] Define helper output file schemas (ruleset + snapshot + status).
- [x] Define storage paths and folder layout.

## Phase 1 — Helper Core (local-only)
- [x] Implement helper CLI entrypoint (`lexishift_helper`).
- [x] Implement `status` command (reads/writes `srs_status.json`).
- [x] Implement `run_rulegen` command (calls core rulegen pipeline).
- [x] Implement `get_snapshot` command (loads `srs_rulegen_snapshot.json`).
- [x] Implement `record_feedback` command (append to SRS store).
- [x] Implement `record_exposure` command (append to SRS store).
- [~] Add logging + error reporting to helper.

## Phase 2 — Native Messaging Host
- [x] Create native messaging host wrapper for macOS.
- [x] Create native messaging host wrapper for Windows.
- [x] Validate incoming payloads (schema + allowed commands).
- [x] Wire host to helper CLI commands.
- [x] Add handshake (`hello`) and version checks.

## Phase 3 — Extension Client
- [ ] Add helper bridge client (getStatus/getSnapshot/getRuleset).
- [ ] Options: “Helper status” + “Refresh now”.
- [ ] Replace rulegen preview button to read helper snapshot.
- [ ] Content script: fetch helper ruleset when SRS enabled.
- [ ] Fallback to cached ruleset if helper offline.

## Phase 4 — Background Scheduling
- [ ] Start helper at login (LaunchAgent / Task Scheduler).
- [ ] Schedule periodic rulegen (timer).
- [ ] Trigger rulegen on feedback batch thresholds.

## Phase 5 — UI + Diagnostics
- [ ] Show helper status + last sync time in GUI app.
- [ ] Add “Install Helper” action in SRS settings.
- [ ] Add logs/health view (optional).

## Open Questions
- [ ] Choose SRS store format for MVP (SQLite vs JSON).
- [ ] Define rulegen refresh cadence and thresholds.
- [ ] Decide on shared secret / auth between helper and extension.
