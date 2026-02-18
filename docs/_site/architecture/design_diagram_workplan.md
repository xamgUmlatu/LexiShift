# Design Diagram Workplan

Status: Active  
Last updated: 2026-02-19

This document defines the six core diagrams to build and maintain so architecture state can be resumed quickly with minimal ambiguity.

## Why This Exists

- Architecture docs currently include a mix of implemented and planned behavior.
- Diagram drift is likely unless ownership, sources, and update triggers are explicit.
- Data layout clarity is the main priority for "pick up where we left off" continuity.

## Diagram Conventions

Use these conventions for every diagram:

1. Title prefix:
   - `[AS-IS]` for implemented/current behavior.
   - `[TARGET]` for intended/future behavior.
2. Include a short header comment with:
   - last verified date,
   - source docs used,
   - unresolved questions (if any).
3. Every persistent data node must show:
   - storage backend/path/key,
   - owning component,
   - authority level (`authoritative` vs `cache` vs `telemetry`).
4. Every edge label should include:
   - action verb (read/write/publish/queue/flush),
   - trigger (startup, user action, observer, retry loop),
   - failure behavior (fail-fast/fallback/retry).
5. Keep one diagram per file under `docs/architecture/diagrams/`.

## Diagram Priority Queue (All Required)

| ID | Diagram | First pass | Primary outcome | Known blockers / open checks |
|---|---|---|---|---|
| DG-01 | Data ownership + storage layout | `[AS-IS]` | Clear map of all current persistent data locations and authorities. | URL retained in exposure telemetry (`srsExposureLog`) for now; keep this explicitly documented. |
| DG-02 | Settings propagation (Options -> runtime mirrors -> content runtime) | `[AS-IS]` | Explain profile/pair/mirror flow and avoid key-scope confusion. | Confirm whether popup module prefs are still planning-only or partially implemented before finalizing nodes. |
| DG-03 | Rule resolution + DOM replacement pipeline | `[AS-IS]` | Runtime replacement behavior from settings to rendered spans. | Confirm latest gating precedence when helper rules + local rules are both available. |
| DG-04 | Feedback + eventual sync flow | `[AS-IS]` | End-to-end reliability path for feedback logging, queueing, retry, helper ingestion. | Confirm final queue bounds/retention policy and dropped-event diagnostics copy. |
| DG-05 | SRS init/refresh control flow | `[AS-IS]` then `[TARGET]` | Helper-dependent control actions and artifacts published per profile/pair. | Confirm strategy/cadence policy that is still open in checklist/working docs. |
| DG-06 | Helper availability/degraded-mode state model | `[AS-IS]` then `[TARGET]` | Explicit behavior split: manual rules vs helper-required SRS actions vs eventual retry. | Final UX copy/severity placement and one-click recovery behavior still open. |

## Existing Data Layout Baseline (For DG-01)

Use this as the starting inventory for the data ownership diagram.

### Extension persistent stores

- `chrome.storage.local`
  - `srsProfiles.<profile_id>.*` (profile-scoped settings/signals/prefs)
  - `srsProfileId` / `srsSelectedProfileId` (selected profile/runtime mirror)
  - `srsStore` (local SRS item store)
  - `srsFeedbackLog` (feedback history log)
  - `srsExposureLog` (exposure telemetry log; review policy note below)
  - `helperFeedbackSyncQueue`, `helperFeedbackSyncLock`, `helperFeedbackSyncDropped` (feedback sync reliability path)
  - rules/settings/runtime keys for replacement and diagnostics
- IndexedDB:
  - `profile_media_store` (profile background assets)

### Helper/app-data persistent stores

- App data root:
  - macOS: `~/Library/Application Support/LexiShift/LexiShift/`
  - Windows: `%APPDATA%\\LexiShift\\LexiShift\\`
- Helper inputs:
  - `language_packs/`, `frequency_packs/`, `embeddings/`, `rulesets/`, `profiles/`
- Helper outputs:
  - `srs/srs_settings.json`
  - `srs/profiles/<profile_id>/srs_store.json`
  - `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
  - `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`
  - `srs/profiles/<profile_id>/srs_status.json`
  - `srs/profiles/<profile_id>/srs_signal_queue.json`

## Files To Maintain

- Diagram tracker: `docs/architecture/diagrams/README.md`
- DG-01: `docs/architecture/diagrams/DG-01_data_ownership_storage_as_is.mmd`
- DG-02: `docs/architecture/diagrams/DG-02_settings_propagation_as_is.mmd`
- DG-03: `docs/architecture/diagrams/DG-03_rule_resolution_dom_pipeline_as_is.mmd`
- DG-04: `docs/architecture/diagrams/DG-04_feedback_eventual_sync_as_is.mmd`
- DG-05: `docs/architecture/diagrams/DG-05_srs_init_refresh_control_as_is.mmd`
- DG-06: `docs/architecture/diagrams/DG-06_helper_availability_state_as_is.mmd`

## Maintenance Rules (Keep It Resume-Friendly)

1. When behavior changes, update the affected diagram in the same change set.
2. Update `docs/architecture/diagrams/README.md` with:
   - last verified date,
   - confidence level,
   - any unresolved assumptions.
3. If behavior is not settled, add a parallel `[TARGET]` diagram file rather than editing `[AS-IS]` into uncertainty.
4. Keep unresolved items linked back to:
   - `docs/architecture/chrome_web_store_review_working_doc.md`
   - `docs/TODOs.md`
