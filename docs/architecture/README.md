# Architecture Docs Index

Status: active architecture index
Role: Canonical current
Last updated: 2026-03-21
Last verified: 2026-03-21 architecture-routing review
Source-of-truth: architecture routing/classification guide; defer implementation truth to source code and the linked architecture docs.

Purpose:
- Make it explicit which architecture docs describe implemented behavior vs WIP/planning behavior.
- Reduce re-onboarding time when resuming work after a break.
- Provide a single jump point for diagram work.

## Status Legend

- `Implemented (As-Is)`: use as current behavior contract.
- `Mixed (As-Is + Target)`: contains both current and planned design.
- `Planning / WIP`: design intent, not runtime truth yet.
- `Draft Decision Log`: active decision record with open questions.

## Start Here For Current Architecture

Use these first when you need the current architecture contract:

1. `extension_system_map.md`
2. `options_controllers_architecture.md`
3. `srs_lp_architecture.md`
4. `chrome_extension_technical.md` only after checking this index, because it mixes current behavior with known gaps

## Architecture Docs By Reliability

| Document | Classification | What to trust it for |
|---|---|---|
| `extension_system_map.md` | Implemented (As-Is) | End-to-end file map, runtime boundaries, debugging paths. |
| `chrome_extension_technical.md` | Mixed (As-Is + known gaps) | Module-level runtime behavior and data keys; includes known issues/ongoing areas. |
| `options_controllers_architecture.md` | Implemented (As-Is) | Options controller graph and composition ownership. |
| `srs_lp_architecture.md` | Implemented contract | LP capability contract and cross-layer invariants. |
| `native_messaging_design.md` | Mixed (As-Is + roadmap) | Native helper architecture and protocol contract; includes future-oriented phases. |
| `native_messaging_checklist.md` | Planning tracker (execution status) | Delivery progress by phase (`[x]` / `[~]` / `[ ]`). |
| `popup_modules_pattern.md` | Mixed (As-Is + target API) | Current popup behavior plus future module API direction. |
| `popup_modules_settings_implementation_plan.md` | Planning / WIP | Planned modules settings model and migration path. |
| `sync_design.md` | Planning / WIP | Multi-client sync blueprint (v1/v2/v3). |
| `chrome_web_store_review_working_doc.md` | Draft Decision Log | Product/policy decisions for CWS concerns and open items. |
| `design_diagram_workplan.md` | Planning / WIP | Diagram backlog, maintenance rules, and ownership expectations. |
| `diagrams/README.md` | Runbook / operational | Diagram status tracker plus local render/update workflow. |

## Planning And Decision Surfaces

Treat these as non-current unless separately verified in code or in `../developer/feature_state_matrix.md`:

- `native_messaging_checklist.md`
- `popup_modules_settings_implementation_plan.md`
- `sync_design.md`
- `chrome_web_store_review_working_doc.md`

## Diagram Work Package

- Diagram preparation/workplan: `design_diagram_workplan.md`
- Diagram files and status tracker: `diagrams/README.md`

## Resume Workflow (When Picking Work Back Up)

1. Read this index first (`architecture/README.md`) to identify stable vs WIP docs.
2. Check `../developer/feature_state_matrix.md` if a workflow or architecture claim may still have a known doc/code mismatch.
3. Review open decisions:
   - `chrome_web_store_review_working_doc.md`
4. Check active execution trackers:
   - `native_messaging_checklist.md`
   - `../TODOs.md`
5. Continue/update architecture diagrams:
   - `design_diagram_workplan.md`
   - `diagrams/README.md`
