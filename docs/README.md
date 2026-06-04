# Documentation Structure

Status: active docs routing
Role: Canonical current
Last updated: 2026-06-04
Last verified: 2026-06-04 hosting/distribution roadmap routing review and clean-checkout doc-reference check
Purpose: route contributors to the current documentation surfaces before planning, archive, or generated evidence
Source-of-truth: routing guide only; defer implementation truth to source code, `developer/feature_state_matrix.md`, and linked domain docs.

This directory is organized by purpose to keep architecture, schema, and operations docs discoverable.

## Quick Start (5 Minutes)

If you need current developer workflow truth first:

1. `developer/README.md`
2. `developer/local_setup.md`
3. `developer/feature_state_matrix.md`
4. `architecture/README.md`

If you need to understand how the extension works end-to-end, read in this order:

1. `architecture/README.md` (implemented vs WIP map)
2. `architecture/extension_system_map.md`
3. `architecture/chrome_extension_technical.md`
4. `architecture/options_controllers_architecture.md`
5. `architecture/popup_modules_pattern.md` only for popup details, and only after noting that it is a mixed current + target doc

If you need SRS/core behavior next:

1. `srs/README.md`
2. `architecture/srs_lp_architecture.md`
3. `srs/srs_schema.md`
4. `srs/srs_set_planning_technical.md`

## Current Routing And References

Use these first when you need current behavior, current runbooks, or current source-of-truth routing:

- Developer docs hub: `developer/README.md`
- Developer handbook: `developer/developer_reference.md`
- Local setup loop: `developer/local_setup.md`
- Build/release workflows: `developer/build_and_release.md`
- Hosting/distribution roadmap: `developer/hosting_distribution_roadmap.md`
- Documentation governance + archive policy: `developer/documentation_governance.md`
- Feature state ledger: `developer/feature_state_matrix.md`
- AI-assisted quality loop (rulegen/POS): `developer/ai_workflow.md`
- GenAI workflow architecture: `developer/genai_workflow_architecture.md`
- Project health gate structure: `developer/project_health_gate_structure.md`
- Project integrity stabilization runbook: `developer/project_integrity_stabilization_runbook.md`
- Architecture status index: `architecture/README.md`
- Script map: `../scripts/README.md`

## Planning, Workstreams, And History

Treat these as planning/history surfaces unless their own metadata says otherwise:

- Documentation grooming handoff: `developer/documentation_grooming_workstream.md`
- Project integrity stabilization backlog: `developer/project_integrity_stabilization_backlog.md`
- Project health remediation workstream: `developer/project_health_remediation_workstream.md`
- Productization Lane 2 code disposition inventory: `developer/productization_lane2_code_disposition_inventory.md`
- Windows GUI parity workstream: `developer/windows_gui_parity_workstream.md`
- GUI docs authority map: `gui/README.md`
- GUI app fix workstream: `gui/gui_app_fix_workstream.md`
- GUI UX decision log: `gui/gui_ux_decisions.md`
- Diagram workplan (all six core diagrams): `architecture/design_diagram_workplan.md`
- Consolidated TODO backlog: `TODOs.md`

## Folders

- `architecture/`: system and extension architecture, integration design, and implementation plans.
- `archive/`: historical or superseded docs retained after current-truth value is routed elsewhere.
- `developer/`: developer setup, build/release workflows, and resume checklist.
- `handbook/`: GitHub Pages-friendly handbook entrypoints (developer, architecture, release, diagrams).
- `gui/`: desktop GUI UX workstreams, fix plans, and implementation notes.
- `srs/`: SRS-specific design, roadmap, schema, and technical notes.
- `rulegen/`: rule generation and synonym generation technical docs.
- `language_pairs/`: language-pair rollout checklists and LP resource requirements.
- `reference/`: stable reference docs and schemas.
- `runbooks/`: troubleshooting and packaging/operations notes.
- `test_outputs/`: generated evaluation outputs and reports; evidence, not primary planning authority.

## Domain Starting Points

- Handbook home (Pages): `handbook/index.md`
- Handbook diagrams (rendered): `handbook/diagrams.md`
- GitHub Pages setup + local preview runbook: `runbooks/github_pages_setup.md`
- Cloudflare distribution setup: `runbooks/cloudflare_distribution_setup.md`
- Hosting/distribution roadmap: `developer/hosting_distribution_roadmap.md`
- Extension architecture: `architecture/chrome_extension_technical.md`
- Extension system map: `architecture/extension_system_map.md`
- Options architecture: `architecture/options_controllers_architecture.md`
- Popup module architecture (mixed current + target): `architecture/popup_modules_pattern.md`
- Diagram status tracker + files: `architecture/diagrams/README.md`
- SRS docs authority map: `srs/README.md`
- SRS roadmap: `srs/srs_roadmap.md`
- Language-pair docs authority map: `language_pairs/README.md`
- Rulegen technical design: `rulegen/rule_generation_technical.md`
- Semantic/rulegen authority map: `rulegen/semantic_rulegen_authority_map.md`
- Rulegen LP onboarding operating model: `rulegen/lp_onboarding_operating_model.md`
- Rulegen LP onboarding checklist template: `rulegen/lp_onboarding_checklist_template.md`
- Rulegen LP support guide (mechanism stack + LP bring-up): `rulegen/rulegen_lp_support_guide.md`
- Rulegen congruity implementation plan (top-3 + scoring): `rulegen/rulegen_congruity_implementation_plan.md`
- POS normalization workstream (SRS + rulegen + LP onboarding): `rulegen/pos_normalization_workstream.md`
- LP data inventory matrix (all databases/resources): `language_pairs/lp_data_inventory_matrix.md`
- Data source licensing + distribution register: `language_pairs/data_source_licensing_and_distribution.md`
- POS source + pipeline reference (all languages): `language_pairs/pos_source_and_pipeline_reference.md`
- LP resource recovery playbook (invalid/unlinked packs): `language_pairs/resource_recovery_playbook.md`
- New language/pair rollout playbook: `language_pairs/language_pair_setup_checklist.md`
- Global app schema: `reference/schema.md`
- Glossary: `reference/glossary.md`
- Chrome Web Store upload gate runbook: `runbooks/cws_upload_gate.md`

## Resume After A Break

Use this order when resuming work:

1. `developer/README.md` (current routing)
2. `developer/feature_state_matrix.md` (current status, evidence, contradictions)
3. `architecture/README.md` (what is solid vs WIP)
4. `developer/local_setup.md` (current operating commands)
5. `architecture/chrome_web_store_review_working_doc.md` and `TODOs.md` (open decisions and backlog)

## Source Of Truth Rules

- Runtime load order truth: `apps/chrome-extension/manifest.json` and script tags in `apps/chrome-extension/options.html`.
- Controller composition truth: `apps/chrome-extension/options/core/bootstrap/controller_graph.js`.
- Storage defaults truth: `apps/chrome-extension/shared/settings/settings_defaults.js`.
- Use `developer/documentation_governance.md` before broad doc cleanup or archive work.
- Treat `test_outputs/`, generated Jekyll site output, and the local Jekyll cache as generated evidence/build outputs, not default planning entrypoints.
- This `docs/` folder should describe behavior, not replace source-level truth.
