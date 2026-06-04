# F14 SRS Action Workflow Split Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted extension factory/runtime tests plus JS syntax checks
Purpose: bound the F14 slice around the preventive split of SRS maintenance actions out of the extension workflow controller so the hotspot shrinks without leaving the factory seam half-connected
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_d8_extension_ui_wiring_packet.md`
- `srs_admission_selective_port_sequence.md`

## Slice

- Track: `F14`
- Slice: `F14.1`
- Title: SRS action maintenance workflow split integration
- Pass type: bounded structural split with runtime factory repair

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
- `apps/chrome-extension/options.html`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_action_workflows.py`
- `core/tests/architecture/test_extension_structure.py`

Primary contract/docs surface:

- `docs/developer/project_integrity_secondary_pass_plan.md`
- `docs/developer/project_integrity_d8_extension_ui_wiring_packet.md`
- `docs/developer/project_integrity_stabilization_backlog.md`

## Explicitly Out Of Scope

This slice does not directly review:

- admission preview and rebalance behavior already covered in `D8`
- the copy-only extension diagnostics holdout logged in `N-010`
- unrelated options-loader churn such as the rules profile-share split
- broader SRS controller architecture beyond this maintenance extraction seam

## Risk Score

- likelihood: `high`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the local split already introduced a real runtime wiring bug in the factory layer
- the blast radius is bounded to SRS option actions, but those are user-facing maintenance operations
- plain syntax checks stayed green, so the failure mode was easy to miss without a runtime factory test

## Contract Sketch

The intended F14 contract after the split is:

1. `workflows.js` remains the thin top-level factory that composes sub-workflows and exports the stable public action API
2. maintenance-heavy actions (`initializeSet`, `refreshSetNow`, `runRuntimeDiagnostics`, `previewSampledRulegen`, `resetSrsData`) live in `maintenance_workflow.js`
3. shared callbacks and dependencies such as `confirmFn`, `markRulesetUpdatedNow`, output setters, and planning-state helpers are resolved once in `workflows.js` and passed coherently into the sub-workflow factories
4. `options.html` loads `maintenance_workflow.js` before `workflows.js` so the factory can bind the extracted module at runtime
5. the split must not change the exported workflow names or silently break action-controller integration

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| The top-level workflow factory still exports the same action API after the split. | `createWorkflows(...)` in `workflows.js` | `core/tests/dev/test_extension_srs_action_workflows.py` | `verified for this slice` |
| Shared callbacks are threaded into both rebalance and maintenance sub-workflow factories without runtime `ReferenceError`s. | `createWorkflows(...)` wiring | `core/tests/dev/test_extension_srs_action_workflows.py` | `fixed and verified in this slice` |
| The maintenance module loads before the top-level workflow factory in the options page. | `options.html` script order | `core/tests/architecture/test_extension_structure.py` | `verified for this slice` |
| The extracted maintenance module stays syntactically valid alongside the slimmed top-level factory. | `maintenance_workflow.js`, `workflows.js` | `node --check` validation | `verified for this slice` |

## Invariants

1. the public SRS action workflow API remains stable after the split
2. shared callbacks are defined before they are passed into sub-workflows
3. the maintenance module is loaded before the top-level workflow factory
4. the split reduces hotspot pressure without broadening controller scope
5. runtime factory wiring must be proven by execution, not only by syntax checks

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Workflow factory composition | `createWorkflows(...)` returns the same action functions after rebalance and maintenance delegation |
| Shared callback threading | rebalance and maintenance factories receive the same `confirmFn` and `markRulesetUpdatedNow` instances |
| Options page load order | `maintenance_workflow.js` is listed before `workflows.js` and `actions_controller.js` |
| JS syntax validation | extracted module and top-level factory both parse cleanly |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted checks:
  - `node --check apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
  - `node --check apps/chrome-extension/options/controllers/srs/actions/workflows.js`
  - `PYTHONPATH=core python3 -m pytest core/tests/dev/test_extension_srs_action_workflows.py core/tests/architecture/test_extension_structure.py -q`

## Planned Action For This Slice

1. inspect the in-progress local split and identify whether it is already coherent or still half-integrated
2. repair only the factory/load-order seam needed to make the split safe
3. add one runtime factory test so the split cannot regress behind syntax-only checks

## Outcome

Result:

- the local extraction of maintenance actions out of `workflows.js` is now coherent enough to keep
- the slice fixed a real runtime factory bug where `confirmFn` and `markRulesetUpdatedNow` were passed before definition
- the extension now has direct runtime coverage for the workflow factory seam in addition to the earlier preview/rebalance module tests
- the split remains bounded: maintenance actions moved behind `maintenance_workflow.js`, while the top-level controller API and the separate copy-only diagnostics follow-up stayed out of scope
