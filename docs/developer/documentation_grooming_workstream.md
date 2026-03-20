# Documentation Grooming Workstream

Status: active
Role: Planning / WIP
Owner: engineering
Last updated: 2026-03-21
Purpose: staged grooming queue for current routing/runbook surfaces, starting in `docs/developer/` and now extending to repo-wide routing docs
Source-of-truth: future grooming queue under `documentation_governance.md`; not a runtime-behavior authority.

## Objective

Turn the documentation methodology into an executable staged grooming queue for maintained routing and runbook surfaces.

This workstream is about:

1. making authority and routing explicit inside the developer-doc layer,
2. normalizing metadata and role labels before broad cleanup,
3. verifying present-tense workflow claims against the current commands and evidence,
4. leaving archive/workstream material clearly separated from current operational docs.

## Completed Slice: `docs/developer/`

Completed in the first slice:

1. metadata normalization on the core runbooks and archive/workstream docs
2. routing cleanup for `docs/developer/README.md` and `developer_reference.md`
3. command/claim verification for the main developer workflow docs
4. live-vs-historical separation for the active health remediation workstream

## Current Starting Point

Current strengths:

1. `docs/README.md`, `docs/developer/README.md`, and `docs/architecture/README.md` already act as routing docs
2. `docs/developer/feature_state_matrix.md` already tracks important workflow-state and doc/code contradictions
3. project-health tooling is already present and integrated into repo-safety commands

Methodology setup already closed:

1. added a repo-wide documentation governance document
2. added a lightweight canonical-doc reference checker and wired it into repo-safety checks
3. refreshed project-health status docs to match the latest advisory watchlist

Remaining follow-on gaps now visible:

1. mixed/planning-heavy docs in `docs/architecture/`, `docs/rulegen/`, `docs/srs/`, and `docs/gui/` still need authority cleanup beyond the routing layer
2. archive/salvage-forward decisions outside `docs/developer/` are not yet reviewed
3. generated evidence and rendered handbook outputs still need continued separation from default planning routes as domain docs are groomed

## Policy Layer Now In Place

Use these docs/scripts first:

1. documentation governance: `documentation_governance.md`
2. canonical doc integrity checker: `../../scripts/dev/check_doc_references.py`
3. architecture classification index: `../architecture/README.md`
4. cross-cutting workflow ledger: `feature_state_matrix.md`
5. project-health policy docs:
   - `project_health_gate_structure.md`
   - `project_health_remediation_workstream.md`

## Completed Slice: Repo-Wide Routing Surfaces (2026-03-21)

Completed in this slice:

1. `README.md`
2. `docs/README.md`
3. `docs/architecture/README.md`
4. `scripts/README.md`

Result:

1. current runbooks and canonical routing docs now appear before planning/history surfaces
2. root/routing docs defer more command detail to maintained runbooks
3. planning/workstream docs remain linked but are not presented as the default current path
4. generated evidence/build outputs remain clearly non-authoritative

## Active Queue: Domain-Level Follow-On Review

After the routing layer is stable, review mixed/planning-heavy domains in this order:

1. `docs/architecture/`
2. `docs/rulegen/`
3. `docs/srs/`
4. `docs/gui/`

Only start those slices after the routing docs above reliably send contributors to the right current surfaces first.

## Validation Loop For This Pass

After each grooming batch:

1. run `npm --prefix scripts run check:docs:report`
2. run `npm --prefix scripts run check:changed:local`
3. run `npm --prefix scripts run check:state` only if the batch changes `feature_state_matrix.md`
4. run `npm --prefix scripts run check` before merging a workflow-heavy batch or after changing command/policy docs that might affect repo safety interpretation

## Good Outcomes

This workstream should leave the repo in a state where:

1. repo routing docs consistently send contributors to current runbooks before planning/history surfaces
2. current runbooks are easy to distinguish from planning docs and archive snapshots
3. routing docs are trustworthy because linked docs declare their role explicitly
4. obsolete material is retired only after value migration

## Non-Goals

1. rewriting all docs in one pass
2. treating every old doc as equally current
3. archiving material before its surviving value is handed forward
