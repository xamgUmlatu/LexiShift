# Developer Documentation

Status: active developer hub
Role: Canonical current
Last updated: 2026-03-21
Last verified: 2026-03-21 developer-doc routing review
Source-of-truth: developer routing guide; defer runtime truth to source code, `feature_state_matrix.md`, and linked subsystem docs.

Purpose:
- Keep developer-facing workflows separate from user onboarding docs.
- Provide a stable place to resume implementation work quickly.
- Point to the architecture/source-of-truth docs used during active development.

## Read This First

1. `developer_reference.md` (current developer handbook / repo map)
2. `local_setup.md` (current setup + validation runbook)
3. `feature_state_matrix.md` (cross-cutting status, evidence, and known doc/code mismatches)
4. `../architecture/README.md` (implemented vs WIP architecture map)
5. `build_and_release.md` (current build/release runbook when packaging or CI/build surfaces are involved)

## Current Runbooks And References

Use these first when you need current behavior or current operating commands:

- Developer handbook (primary reference): `developer_reference.md`
- Local setup and day-to-day loops: `local_setup.md`
- Build/release packaging flows: `build_and_release.md`
- AI-assisted rulegen/POS quality loop: `ai_workflow.md`
- GenAI workflow architecture and harness policy: `genai_workflow_architecture.md`
- Project health gate structure: `project_health_gate_structure.md`
- Documentation governance + archive policy: `documentation_governance.md`
- Feature state ledger: `feature_state_matrix.md`
- Repo safety commands: `npm --prefix scripts run check` and `npm --prefix scripts run build`
- Canonical doc integrity check: `npm --prefix scripts run check:docs`
- Script map: `../../scripts/README.md`
- Architecture docs map: `../README.md`

## Planning And Workstreams

Treat these as planning/history surfaces unless their own metadata says otherwise:

- Documentation grooming queue: `documentation_grooming_workstream.md`
- Project health remediation workstream: `project_health_remediation_workstream.md`
- Windows GUI parity workstream: `windows_gui_parity_workstream.md`

## Core Code Areas

- GUI app: `../../apps/gui/src/`
- Chrome extension: `../../apps/chrome-extension/`
- BetterDiscord plugin: `../../apps/betterdiscord-plugin/`
- Core engine: `../../core/lexishift_core/`
- Tests: `../../core/tests/`

## Key Technical References

- Extension system map: `../architecture/extension_system_map.md`
- Extension technical details: `../architecture/chrome_extension_technical.md`
- Options controller graph: `../architecture/options_controllers_architecture.md`
- Native messaging design/checklist:
  - `../architecture/native_messaging_design.md`
  - `../architecture/native_messaging_checklist.md`
- SRS LP contract: `../architecture/srs_lp_architecture.md`
- Global schema reference: `../reference/schema.md`
- Glossary: `../reference/glossary.md`

## Resume Workflow (After A Break)

1. Check what is stable vs planning in `../architecture/README.md`.
2. Check current operating commands in `local_setup.md`.
3. Check known status contradictions in `feature_state_matrix.md`.
4. Check open decisions in `../architecture/chrome_web_store_review_working_doc.md` and active tasks in `../TODOs.md`.
5. Re-validate assumptions against source-level truth:
   - `../../apps/chrome-extension/manifest.json`
   - `../../apps/chrome-extension/options/core/bootstrap/controller_graph.js`
   - `../../apps/chrome-extension/shared/settings/settings_defaults.js`

## Archive And History

The previous detailed root README snapshot is preserved here:
- `legacy_root_readme_snapshot.md`

Use it as archive-only reference; use `developer_reference.md` for active work.
