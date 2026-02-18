# Architecture Docs Index

Purpose:
- Make it explicit which architecture docs describe implemented behavior vs WIP/planning behavior.
- Reduce re-onboarding time when resuming work after a break.
- Provide a single jump point for diagram work.

## Status Legend

- `Implemented (As-Is)`: use as current behavior contract.
- `Mixed (As-Is + Target)`: contains both current and planned design.
- `Planning / WIP`: design intent, not runtime truth yet.
- `Draft Decision Log`: active decision record with open questions.

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

## Diagram Work Package

- Diagram preparation/workplan: `design_diagram_workplan.md`
- Diagram files and status tracker: `diagrams/README.md`

## Resume Workflow (When Picking Work Back Up)

1. Read this index first (`architecture/README.md`) to identify stable vs WIP docs.
2. Review open decisions:
   - `chrome_web_store_review_working_doc.md`
3. Check active execution trackers:
   - `native_messaging_checklist.md`
   - `docs/TODOs.md`
4. Continue/update architecture diagrams:
   - `design_diagram_workplan.md`
   - `diagrams/README.md`
