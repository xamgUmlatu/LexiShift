# GUI Documentation Authority Map

Status: active GUI routing
Role: Canonical current
Last updated: 2026-05-15
Last verified: 2026-05-15 Lane 1 GUI supersession review against GUI docs, `apps/gui/src/`, GUI tests, and doc-reference checks; GUI behavior was not fully re-audited
Purpose: route GUI cleanup work to the right source, decision log, snapshot, or planning doc without treating old workstream notes as current implementation truth
Source-of-truth: GUI documentation routing only; implementation truth lives in `apps/gui/src/`, `apps/gui/tests/`, generated/build evidence, and relevant feature-state entries.

## Use This First For GUI Doc Cleanup

The GUI docs are intentionally not a full current architecture manual. They
preserve a workstream plan, a structure snapshot, accepted UX decisions, and
profile/ruleset refactor notes.

Use source and tests for current behavior. Use these docs to understand why a
shape exists and which cleanup path was intended.

## Current Authority Order

| Claim Being Checked | Start Here | Role In Cleanup | Do Not Use It For |
| --- | --- | --- | --- |
| Current GUI behavior or structure | `apps/gui/src/`, `apps/gui/tests/` | Source/test truth for actual desktop behavior. | Replacing runtime inspection or focused GUI tests. |
| Cross-cutting product/build/platform state | `docs/developer/feature_state_matrix.md`, `docs/developer/windows_gui_parity_workstream.md` | Status/evidence for build, packaging, Windows parity, helper install, and resource-pack surfaces. | Fine-grained widget layout claims. |
| Current GUI documentation routing | `docs/gui/README.md` | This authority map. | Implementation truth by itself. |
| GUI fix backlog and accepted progress snapshot | `docs/gui/gui_app_fix_workstream.md` | Planning/WIP queue and historical progress context. | Claiming a bug still exists or is fixed without checking source/tests. |
| GUI structure after the Utility Dock work | `docs/gui/gui_current_structure.md` | Snapshot reference only. | Current structure authority without a fresh source audit. |
| Accepted UX rationale | `docs/gui/gui_ux_decisions.md` | Decision rationale log. | Proof that all referenced behavior is still implemented. |
| Profile/ruleset extraction plan | `docs/gui/profile_ruleset_refactor_notes.md` | Refactor notes and intended service boundaries. | Proof that all coupling has been removed. |

## Supersession Decision

This review does not archive any GUI docs.

Current disposition:

- `gui_current_structure.md` stays in place as a dated snapshot because its main
  seams still exist, but it is not promoted to current architecture authority.
- `gui_app_fix_workstream.md` stays as planning/WIP history and cleanup queue.
- `gui_ux_decisions.md` stays as decision rationale.
- `profile_ruleset_refactor_notes.md` stays as refactor planning context.

## Current GUI Posture

For productization closure, preserve these boundaries unless a later verified
update changes the owning docs:

- current GUI behavior is source/test truth, not doc snapshot truth;
- profile/ruleset behavior is split across main-window mixins, dialogs, service
  helpers, and tests;
- resource-pack GUI behavior is tied to the data-source normalization docs and
  GUI resource-pack tests;
- Windows/build packaging claims route through build/parity docs and feature
  state, not the GUI workstream notes.

## Safe Cleanup Sequence

When cleaning GUI docs during Lane 1:

1. classify whether the claim is current behavior, UX rationale, historical
   snapshot, or planning work,
2. verify current behavior in `apps/gui/src/` and `apps/gui/tests/` before
   promoting any snapshot text,
3. migrate surviving current-truth claims into this map or a current
   architecture doc before archiving a GUI doc,
4. avoid rewriting user-facing GUI claims unless a focused GUI test or source
   read supports the change,
5. run `python3 scripts/dev/check_doc_references.py` and `git diff --check`
   after routing edits.
