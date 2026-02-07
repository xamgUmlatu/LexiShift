# LexiShift Companion Helper + Native Messaging (Option A)

This document defines the design and implementation workstream for a local companion helper
that performs SRS growth + rulegen and serves results to the browser extension (and later the plugin),
without shipping large datasets inside the extension.

## Goals
- Run rulegen locally as S grows, without requiring the user to open the GUI app.
- Keep large dictionaries/frequency packs on disk (GUI app data), not in the extension.
- Allow extension to fetch rulegen outputs and report feedback (plus optional exposure telemetry).
- Ensure privacy-first, offline operation.
- Be extensible to the BetterDiscord plugin later.

## Non-goals (for this phase)
- Cloud hosting or user accounts.
- Full multi-device sync.
- Complex conflict resolution across multiple devices.
- Shipping dictionaries inside extension bundles.

## Architecture Overview
Components:
1) **GUI App** (LexiShift): offers install/config UI for the background helper.
2) **Companion Helper** (background process): owns rulegen, SRS store, rule snapshots.
3) **Native Messaging Host**: bridges extension ↔ helper using Chrome native messaging.
4) **Extension**: applies rules, sends feedback, requests snapshots.

Data sources live in the GUI app data dir:
- `language_packs/`, `frequency_packs/`, `embeddings/`, `rulesets/`, etc.

Shared outputs written by helper:
- `srs/srs_store.json`
- `srs/srs_rulegen_snapshot_<pair>.json`
- `srs/srs_ruleset_<pair>.json`
- `srs/srs_status.json` (health + last_run metadata)
- `srs/srs_signal_queue.json` (signal stream; feedback authoritative for scheduling)

## Workstream Breakdown (Phases)

Tracking checklist: see `docs/native_messaging_checklist.md`.

### Phase 0 — Protocol + Schema (doc only)
- Define message types and payloads (this doc).
- Define storage outputs and versioning.
- Confirm data paths (macOS + Windows).

### Phase 1 — Helper Core (local-only)
- Implement `lexishift_helper` CLI:
  - `status`: reads health + last_rulegen.
  - `run_rulegen`: uses current S + rulegen pipeline to refresh outputs.
  - `plan_srs_set`: returns set planning decision for pair/profile context.
  - `init_srs_set`: explicit set initialization command.
  - `get_snapshot`: returns concise preview (target lemma → sources).
  - `record_feedback`: append to SRS store.
  - `record_exposure`: optional telemetry path.
- Outputs JSON files in a stable schema.

### Phase 2 — Native Messaging Host
- Provide a native messaging host wrapper:
  - Validates incoming messages.
  - Calls helper core commands.
  - Writes replies back to extension.
  - Script: `scripts/helper/lexishift_native_host.py`.
  - Manifest templates: `scripts/helper/native_messaging/`.

### Phase 3 — Extension Client
- Implement a client bridge:
  - `getStatus()`
  - `getRulegenSnapshot(pair)`
  - `getRuleset(pair)`
  - `planSrsSet(payload)`
  - `initializeSrs(payload)`
  - `recordFeedback(payload)`
  - `recordExposure(payload)`
- Use a persistent feedback sync queue in extension storage for `record_feedback`:
  - retry with backoff
  - bounded queue
  - optional dropped-event archive for diagnostics
- Options page uses the snapshot for “Show target rules…”.
- Content script reads ruleset from helper when enabled (with fallback to last local ruleset).

### Phase 4 — Background Scheduling
- Helper runs periodically:
  - timer (e.g., hourly), or
  - on feedback batch thresholds, or
  - on preference changes.
- GUI app can trigger `run_rulegen` explicitly.
 - Helper tray app (menubar/tray) owns lifetime + status UI.
 - macOS LaunchAgent starts the helper tray mode (`--helper-tray`) at login (tray app spawns the daemon).

### Phase 5 — UI + Diagnostics
- Options page:
  - “Helper status” (connected / last sync / last error).
  - “Refresh now” button.
- Logs routed to extension dev console (debug only).

## Message Protocol (Native Messaging)
Envelope:
- `id`: string (request id)
- `type`: string (command)
- `version`: integer (protocol version)
- `payload`: object

Response:
- `id`: string (match request)
- `ok`: boolean
- `data`: object | null
- `error`: { code, message } | null

Commands (MVP):
- `hello` → returns helper version, protocol version.
- `status` → returns last_run timestamps, active pair, counts.
- `get_ruleset` → returns ruleset for a `pair`.
- `get_snapshot` → returns preview for `pair`.
- `record_feedback` → accept SRS feedback payload.
- `record_exposure` → accept exposure telemetry batch.
- `trigger_rulegen` → recompute now for pair (optional).
- `srs_plan_set` → plan strategy for set S (no mutation).
- `srs_initialize` → initialize set S for a pair (mutation).
- `srs_reset` → clear SRS progress for pair/all.

Sizing contract for `srs_plan_set` and `srs_initialize`:
- `bootstrap_top_n` (preferred bootstrap size input)
- `initial_active_count` (declared initial active subset size)
- `max_active_items_hint` (workload hint from profile/UI)
- `set_top_n` remains accepted as a compatibility alias for bootstrap size

## Snapshot Schema (MVP)
`srs_rulegen_snapshot_<pair>.json`:
- `version`
- `generated_at`
- `pair`
- `targets`: [
  - `lemma`
  - `sources`: [string]
  - `confidence`: number (0..1) optional
]
- `stats`: { target_count, rule_count, source_count }

## Ruleset Schema (MVP)
`srs_ruleset_<pair>.json`:
- `version`
- `generated_at`
- `pair`
- `rules`: [{ source_phrase, replacement, confidence, tags, enabled }]

## Storage + Paths
Use existing LexiShift app data root:
- macOS: `~/Library/Application Support/LexiShift/LexiShift/`
- Windows: `%APPDATA%\\LexiShift\\LexiShift\\`

Helper should read from:
- `language_packs/`
- `frequency_packs/`
- `rulesets/`
- `profiles/`

Helper should write:
- `srs/` (new folder)
  - `srs_store.json`
  - `srs_rulegen_snapshot_<pair>.json`
  - `srs_ruleset_<pair>.json`
  - `srs_status.json`
  - `srs_signal_queue.json`

## Security + Trust
- Native messaging host manifest should allow only LexiShift extension id.
- Helper validates message types + payload schema.
- Optional shared secret stored in app data for handshake.
- No external network calls required.

## Failure Modes + Fallbacks
- If helper unavailable, extension falls back to:
  - last cached ruleset in storage.
  - fixed test dataset for SRS sampling.
- Options UI shows “Helper offline” status.

## Testing Plan
- Unit tests for protocol validation + snapshot formatting.
- Integration tests for helper CLI outputs.
- Manual test:
  1) Start helper
  2) Options → “Show target rules…”
  3) Confirm snapshot matches ruleset.

## Open Questions
- How frequently should rulegen run?
- Should we allow manual override per profile/pair?
- How should profile-driven planning and adaptive refresh be scheduled?

## GUI Install UX
- **Automatic** install on first launch if a fixed extension ID is available and the bundled helper host exists.
- App menu (LexiShift) → “Install/Reinstall LexiShift Helper…” as a repair tool.
- Settings → SRS: “Helper status” + “Install/Reinstall Helper” as a repair tool.
- Extension IDs are read from `apps/gui/resources/helper_extension_ids.json` (fixed IDs for prod, plus dev/unpacked entries).
- If the helper host script is missing (dev), the GUI prompts for the script path.

## Bundling the Helper Host
- The GUI app bundles `lexishift_native_host.py` plus `lexishift_core` into `resources/helper/`.
- The helper manifest points to the bundled script path, so no extra download is required.
- For onefile builds, the installer copies the helper into the LexiShift app data directory to keep the manifest path stable after the app exits.

## Current Status
- Helper auto-install runs on launch when a fixed ID is available; manual install remains as repair (App menu + SRS settings).
- Native messaging host exists; install writes the host manifest for the provided extension ID.
- Helper supports set planning (`srs_plan_set`) and explicit set initialization (`srs_initialize`).
- Feedback writes to `srs/srs_signal_queue.json` for future adaptive set updates.
- Exposure writes remain available as telemetry and are non-authoritative for scheduling.
