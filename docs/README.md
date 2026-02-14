# Documentation Structure

This directory is organized by purpose to keep architecture, schema, and operations docs discoverable.

## Quick Start (5 Minutes)

If you need to understand how the extension works end-to-end, read in this order:

1. `architecture/extension_system_map.md`
2. `architecture/chrome_extension_technical.md`
3. `architecture/options_controllers_architecture.md`
4. `architecture/popup_modules_pattern.md`

If you need SRS/core behavior next:

1. `architecture/srs_lp_architecture.md`
2. `srs/srs_schema.md`
3. `srs/srs_set_planning_technical.md`

## Folders

- `architecture/`: system and extension architecture, integration design, and implementation plans.
- `gui/`: desktop GUI UX workstreams, fix plans, and implementation notes.
- `srs/`: SRS-specific design, roadmap, schema, and technical notes.
- `rulegen/`: rule generation and synonym generation technical docs.
- `language_pairs/`: language-pair rollout checklists and LP resource requirements.
- `reference/`: stable reference docs and schemas.
- `runbooks/`: troubleshooting and packaging/operations notes.
- `test_outputs/`: generated evaluation outputs and reports.

## Starting Points

- Extension architecture: `architecture/chrome_extension_technical.md`
- Extension system map: `architecture/extension_system_map.md`
- Options architecture: `architecture/options_controllers_architecture.md`
- Popup module architecture: `architecture/popup_modules_pattern.md`
- GUI app fix workstream: `gui/gui_app_fix_workstream.md`
- GUI UX decision log: `gui/gui_ux_decisions.md`
- SRS roadmap: `srs/srs_roadmap.md`
- Rulegen technical design: `rulegen/rule_generation_technical.md`
- Global app schema: `reference/schema.md`
- New language/pair rollout playbook: `language_pairs/language_pair_setup_checklist.md`

## Source Of Truth Rules

- Runtime load order truth: `apps/chrome-extension/manifest.json` and script tags in `apps/chrome-extension/options.html`.
- Controller composition truth: `apps/chrome-extension/options/core/bootstrap/controller_graph.js`.
- Storage defaults truth: `apps/chrome-extension/shared/settings/settings_defaults.js`.
- This `docs/` folder should describe behavior, not replace source-level truth.
