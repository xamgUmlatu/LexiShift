# SRS Roadmap (Set S + Practice Layer)

## Goal
Build a non-destructive SRS practice layer that:
- Maintains a per-pair set `S` of learnable items.
- Uses due-based scheduling to gate runtime replacements.
- Incorporates user feedback/exposure signals to evolve `S`.

## Current Architecture Snapshot

### Runtime and storage
- Practice gate and scheduler are implemented.
- Canonical helper store path is now:
  - `.../LexiShift/srs/srs_store.json`
- Helper also owns:
  - `srs/srs_settings.json`
  - `srs/srs_status.json`
  - `srs/srs_rulegen_snapshot_<pair>.json`
  - `srs/srs_ruleset_<pair>.json`
  - `srs/srs_signal_queue.json` (new signal stream scaffold)

### New scaffolding (implemented)
- **Set strategy taxonomy**
  - `core/lexishift_core/srs_set_strategy.py`
  - Strategies: `frequency_bootstrap`, `profile_bootstrap`, `profile_growth`, `adaptive_refresh`
- **Set planner**
  - `core/lexishift_core/srs_set_planner.py`
  - Produces plan metadata: effective strategy, execution mode, requirements, notes.
- **Signal queue**
  - `core/lexishift_core/srs_signal_queue.py`
  - Appends `feedback` and `exposure` events for future adaptive policies.
- **Helper planning API**
  - `srs_plan_set` command added to native host/CLI.
- **Helper initialization API (extended)**
  - `srs_initialize` now accepts `strategy`, `objective`, `profile_context`, `trigger`.
  - Current executable mode remains `frequency_bootstrap`; profile strategies are planned fallbacks.
- **Extension options scaffolding**
  - “Initialize S for this pair” sends `profile_context`.
  - `srsProfileSignals` storage key added for future profile signal capture.
  - Details: `docs/srs_set_planning_technical.md`.

---

## Workstream Tracking

Status key:
- `[ ]` not started
- `[~]` in progress
- `[x]` done

### Workstream A — Practice gate + scheduling
- `[x]` Core SRS data model + scheduler + gate.
- `[x]` GUI preview integration.
- `[x]` Extension SRS gating (test dataset mode).
- `[x]` Feedback popup and exposure logging in extension.
- `[~]` Harmonize extension local SRS store with helper-owned SRS store.

### Workstream B — Set `S` generation and growth
- `[x]` Frequency-based bootstrap pipeline (`srs_seed.py`, `srs_growth.py`).
- `[x]` JMDict-filtered JA bootstrap flow for `en-ja`.
- `[x]` Set planner scaffold (`srs_set_planner.py`).
- `[x]` Explicit `srs_initialize` backend action.
- `[~]` Profile-guided scoring/selection logic.
- `[~]` Multi-pair bootstrap policies.

### Workstream C — User signal ingestion and adaptive refresh
- `[x]` Signal queue format + append path (`srs_signal_queue.json`).
- `[x]` Feedback/exposure writes from helper into signal queue.
- `[~]` Aggregation rules (time windows, confidence, decay).
- `[ ]` Automatic adaptive refresh trigger from signal thresholds.

### Workstream D — Profile modeling
- `[x]` Profile schema draft docs.
- `[x]` Extension-side `srsProfileSignals` scaffold and helper payload forwarding.
- `[~]` Profile signal normalization and validation.
- `[ ]` Profile editor UX for interests/proficiency/objectives.

### Workstream E — Rulegen and S integration
- `[x]` Rulegen preview made non-mutating.
- `[x]` Rulegen/initializer terminology updated toward set `S`.
- `[~]` Use planner output to choose rulegen/update workflows.
- `[ ]` Pair-specific policy registry for strategy routing.

### Workstream F — Sync/export
- `[~]` SRS settings/store bundle format exists.
- `[ ]` Cross-surface (GUI/extension/plugin) import/export wiring.
- `[ ]` Conflict handling for concurrent updates.

---

## Near-Term Implementation Plan

### Phase 1 (scaffold complete, logic pending)
- Keep `frequency_bootstrap` as executable baseline.
- Route all set operations through planner output.
- Record all feedback/exposure into signal queue.

### Phase 2 (next logic slice)
- Implement profile-aware candidate weighting:
  - interests/domain bias
  - proficiency/known-word suppression
  - empirical trends weighting
- Add planner-backed `profile_growth` execution mode.

### Phase 3 (adaptive refresh)
- Add aggregation service over signal queue:
  - moving windows
  - per-pair recency weighting
  - trigger thresholds
- Execute `adaptive_refresh` plans automatically.

---

## Data Requirements (MVP -> production)

### Required now
- Frequency packs (pair/language specific).
- Dictionary packs for pair validation and rulegen.
- SRS settings + store + signal queue files.

### Required for profile-guided growth
- Profile context fields:
  - interests
  - proficiency
  - objectives
  - empirical trends
  - source preferences

### Required for adaptive refresh
- Stable ingestion of feedback/exposure signals from all surfaces.
- Signal aggregation policy with bounded memory and retention.

---

## Terminology Notes
- Historical term “seed” is now treated as “initial set bootstrap.”
- `source_type` for bootstrap-created items is now `initial_set`.
- Future source types continue to include `frequency_list`, `user_stream`, `curated`, `extension`.
