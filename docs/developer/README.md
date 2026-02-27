# Developer Documentation

Purpose:
- Keep developer-facing workflows separate from user onboarding docs.
- Provide a stable place to resume implementation work quickly.
- Point to the architecture/source-of-truth docs used during active development.

## Read This First

1. `../architecture/README.md` (implemented vs WIP architecture map)
2. `../architecture/chrome_web_store_review_working_doc.md` (active policy/product decisions)
3. `../TODOs.md` (current backlog and execution queue)
4. `../architecture/design_diagram_workplan.md` + `../architecture/diagrams/README.md`

## Core Developer Guides

- Developer handbook (primary reference): `developer_reference.md`
- Local setup and day-to-day loops: `local_setup.md`
- Build/release packaging flows: `build_and_release.md`
- AI-assisted rulegen/POS quality loop: `ai_workflow.md`
- Project health gate structure: `project_health_gate_structure.md`
- Project health remediation workstream: `project_health_remediation_workstream.md`
- Script map: `../../scripts/README.md`
- Architecture docs map: `../README.md`

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
2. Check open decisions in `../architecture/chrome_web_store_review_working_doc.md`.
3. Check active tasks in `../TODOs.md`.
4. Check diagram status in `../architecture/diagrams/README.md`.
5. Re-validate assumptions against source-level truth:
   - `../../apps/chrome-extension/manifest.json`
   - `../../apps/chrome-extension/options/core/bootstrap/controller_graph.js`
   - `../../apps/chrome-extension/shared/settings/settings_defaults.js`

## Legacy Content

The previous detailed root README snapshot is preserved here:
- `legacy_root_readme_snapshot.md`

Use it as archive-only reference; use `developer_reference.md` for active work.
