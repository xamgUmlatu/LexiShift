# Developer Handbook

Status: Active handbook
Role: Canonical current
Last updated: 2026-05-15
Last verified: 2026-05-15 Lane 4 validation-gate routing review and doc-reference check
Purpose: developer-facing repository map and current source-of-truth routing for implementation work
Source-of-truth: developer reference guide; command details defer to `local_setup.md`, `build_and_release.md`, and `productization_lane4_validation_gate_inventory.md`, and runtime claims verify in source code and `feature_state_matrix.md`.

This document is the primary developer-facing reference for LexiShift implementation work.
Use it as a map and routing handbook, not as the only authority for fast-moving command surfaces.

## 1. Purpose

Use this handbook to:
- understand the current system quickly,
- find source-of-truth files for each subsystem,
- run local development and validation loops,
- resume work after a break without re-discovering context.

## 2. System Surfaces

LexiShift has four main runtime surfaces:

1. Desktop GUI app (`apps/gui/src/`)
- Authoring surface for profiles, rulesets, language packs, and settings.

2. Chrome extension (`apps/chrome-extension/`)
- Primary runtime for webpage replacement, SRS interactions, and helper bridge requests.

3. BetterDiscord plugin (`apps/betterdiscord-plugin/`)
- Runtime replacement surface for Discord messages.

4. Native helper (`scripts/helper/` + `core/lexishift_core/helper/`)
- Local SRS set planning/initialization/refresh, rulegen publication, and feedback ingestion.

## 3. Repository Map (Developer-Focused)

Core code areas:
- `core/lexishift_core/replacement/`: tokenizer, matcher, trie replacement, inflection and pipeline.
- `core/lexishift_core/srs/`: SRS store/scheduler/selection/planning/refresh policies.
- `core/lexishift_core/helper/`: helper orchestration, profile/path contracts, use-cases.
- `core/lexishift_core/rulegen/`: pair-agnostic + pair-specific rule generation.

App/runtime code:
- `apps/gui/src/`: PySide6 desktop app.
- `apps/chrome-extension/content/`: replacement runtime, DOM scan, popup UI modules.
- `apps/chrome-extension/options/`: options controllers and bootstrap graph.
- `apps/chrome-extension/shared/`: cross-runtime settings, helper, SRS, profile utilities.
- `apps/betterdiscord-plugin/src/`: plugin runtime implementation.

Operational and tooling:
- `scripts/build/`: build and installer pipelines.
- `scripts/data/`: conversion tools (frequency/embeddings/dictionaries).
- `scripts/dev/`: local diagnostics and helper workflow scripts.
- `scripts/helper/`: helper and native messaging host entrypoints.
- `scripts/testing/`: test/report scripts.
- `core/tests/`: primary automated tests.

## 4. Data Ownership And Storage Layout (Current)

Extension-side persistent stores:

1. `chrome.storage.local`
- settings and runtime mirrors,
- `srsProfiles.<profile_id>.*` profile-scoped state,
- `srsStore`, `srsFeedbackLog`, `srsExposureLog`,
- helper feedback sync queue keys (`helperFeedbackSyncQueue`, `helperFeedbackSyncLock`, `helperFeedbackSyncDropped`).

2. IndexedDB
- `profile_media_store` for profile background assets.

Helper/app-data stores (profile-first under app data root):
- `srs/srs_settings.json`
- `srs/profiles/<profile_id>/srs_store.json`
- `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
- `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`
- `srs/profiles/<profile_id>/srs_status.json`
- `srs/profiles/<profile_id>/srs_signal_queue.json`

Current policy notes to keep explicit:
- sentence-history module records: no URL field,
- exposure telemetry (`srsExposureLog`) currently retains URL for now.

For maintained data diagrams, use:
- `../architecture/design_diagram_workplan.md`
- `../architecture/diagrams/README.md`

## 5. Local Setup And Validation Entry Points

Use `local_setup.md` as the current runbook for setup, repo safety, style, parity, and branch-scope loops.
Keep this handbook focused on the minimum entrypoints needed to resume work quickly.

Create environment:

```bash
npm --prefix scripts run setup:python
npm --prefix scripts run hooks:install
```

Add GUI packaging dependencies when needed:

```bash
npm --prefix scripts run setup:python:build
```

Default local safety loop:

```bash
npm --prefix scripts run check
```

Default branch-scope loop:

```bash
npm --prefix scripts run check:changed:local
```

Build/package safety loop when those surfaces are touched:

```bash
npm --prefix scripts run build
```

Specialty runbooks, policies, and ledgers live in:

- `local_setup.md`
- `build_and_release.md`
- `productization_lane4_validation_gate_inventory.md`
- `documentation_governance.md`
- `feature_state_matrix.md`
- `project_health_gate_structure.md`
- `project_integrity_stabilization_runbook.md`
- `project_integrity_stabilization_backlog.md`
- `ai_workflow.md`

## 6. Runtime Development Loops

### Desktop GUI

```bash
python apps/gui/src/main.py
```

### Chrome extension

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Load unpacked: `apps/chrome-extension/`.
4. Use options/debug flows to validate state and helper paths.

### BetterDiscord plugin

```bash
node apps/betterdiscord-plugin/build_plugin.js
```

Optional dev helpers:

```bash
node apps/betterdiscord-plugin/watch_plugin.js
node apps/betterdiscord-plugin/sync_plugin.js
```

## 7. Core Engineering Flows

### A) Replacement runtime changes

Primary touchpoints:
- `apps/chrome-extension/content/processing/`
- `apps/chrome-extension/content/runtime/`
- `apps/chrome-extension/content/ui/`

Reference docs:
- `../architecture/extension_system_map.md`
- `../architecture/chrome_extension_technical.md`

### B) Options/settings/controller changes

Primary touchpoints:
- `apps/chrome-extension/options/core/bootstrap/controller_graph.js`
- `apps/chrome-extension/options/controllers/`
- `apps/chrome-extension/options/core/settings/`

Reference docs:
- `../architecture/options_controllers_architecture.md`

### C) Helper/SRS flow changes

Primary touchpoints:
- `core/lexishift_core/helper/use_cases/`
- `scripts/helper/lexishift_native_host.py`
- `apps/chrome-extension/shared/helper/`
- `apps/chrome-extension/options/controllers/srs/actions/`

Reference docs:
- `../architecture/native_messaging_design.md`
- `../architecture/native_messaging_checklist.md` (planning/execution tracker, not current behavior authority)
- `../architecture/srs_lp_architecture.md`

## 8. Build And Release

Use:
- `build_and_release.md`

Key gate before CWS upload:

```bash
npm --prefix scripts run preflight:cws
```

Runbook and reports:
- `../runbooks/cws_upload_gate.md`
- `../runbooks/cws_preflight_reports/`

## 9. Testing And Diagnostics

Core tests:

```bash
python -m unittest discover -s core/tests
```

Syntax-check changed extension files as needed:

```bash
node --check <changed_js_file>
```

Helper diagnostics scripts:
- `../../scripts/dev/check_helper_status.sh`
- `../../scripts/dev/cleanup_helper.sh`

Rulegen quality workflow references:
- `ai_workflow.md`
- `genai_workflow_architecture.md`
- `feature_state_matrix.md`

SRS workflow references:
- `../../scripts/testing/srs_quality_harness.py`
- `../../scripts/testing/srs_journey_harness.py`
- `../../scripts/testing/srs_journey_summary.py`
- `../../scripts/testing/srs_journey_html.py`
- `../srs/srs_journey_harness_workstream.md`
- `../../scripts/testing/rulegen_pair_audit_cycle.py`
- `../../scripts/testing/rulegen_auto_audit.py`
- `../../scripts/dev/dev_workflow_check.py`
- `../../scripts/dev/dev_workflow_build.py`

Extension architecture debug references:
- `../architecture/extension_system_map.md` (fast debug paths)
- `../architecture/chrome_extension_technical.md`

## 10. Architecture Reliability Map

Use this classification first when reading architecture docs:
- implemented/as-is contract,
- mixed as-is + target,
- planning/WIP,
- draft decision log.

For broader documentation authority, archive, and salvage-forward rules, use:
- `documentation_governance.md`

Source:
- `../architecture/README.md`

## 11. Resume Workflow

When resuming after a break:

1. Read `feature_state_matrix.md` for current status, evidence, and known contradictions.
2. Read `local_setup.md` for the current operating loops before changing code.
3. Read `../architecture/README.md`.
4. Read `../architecture/chrome_web_store_review_working_doc.md` for open policy/product decisions and `../TODOs.md` for active backlog.
5. Re-check source-level truth in:
   - `../../apps/chrome-extension/manifest.json`
   - `../../apps/chrome-extension/options/core/bootstrap/controller_graph.js`
   - `../../apps/chrome-extension/shared/settings/settings_defaults.js`

## 12. Canonical References

Current routing and runbooks:
- Developer hub: `README.md`
- Local setup and validation runbook: `local_setup.md`
- Build/release runbook: `build_and_release.md`
- AI workflow: `ai_workflow.md`
- GenAI workflow architecture: `genai_workflow_architecture.md`

Policy and state:
- Documentation governance: `documentation_governance.md`
- Feature state ledger: `feature_state_matrix.md`
- Project health gate structure: `project_health_gate_structure.md`

Planning and workstreams:
- Documentation grooming handoff: `documentation_grooming_workstream.md`
- Project health remediation workstream: `project_health_remediation_workstream.md`
- Windows GUI parity workstream: `windows_gui_parity_workstream.md`

Reference maps:
- Architecture map: `../architecture/README.md`
- Docs structure map: `../README.md`
- Script map: `../../scripts/README.md`
- Glossary: `../reference/glossary.md`
- Global schema: `../reference/schema.md`
- SRS roadmap: `../srs/srs_roadmap.md`
- Backlog: `../TODOs.md`

## 13. Legacy Snapshot

Historical root README snapshot (archival):
- `legacy_root_readme_snapshot.md`
