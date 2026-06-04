# SP5 SRS Action Transitions Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted SRS action transition contract tests plus structure/doc checks
Purpose: bound the third `SP5` slice around post-split SRS action transitions so the options-controller seam has direct executable evidence for initialize/refresh/reset transition behavior and for the full SRS action script stack the runtime now depends on
Source-of-truth: packet only; executable truth still lives in the SRS action workflow modules, current structure tests, and the options controller architecture map
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_f14_srs_action_workflow_split_packet.md`
- `project_integrity_d8_extension_ui_wiring_packet.md`
- `../architecture/options_controllers_architecture.md`

## Slice

- Track: `SP5`
- Slice: SRS workflow action transitions
- Title: post-split SRS action transition contract
- Pass type: verification-first slice with narrow current-truth doc correction

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions/rebalance_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions_controller.js`
- `apps/chrome-extension/options.html`

Primary docs/evidence surface:

- `core/tests/dev/test_extension_srs_action_workflows.py`
- `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py`
- `core/tests/architecture/test_extension_structure.py`
- `docs/architecture/options_controllers_architecture.md`

## Explicitly Out Of Scope

This slice does not directly review:

- helper-side inventory correctness already covered under `SP2`
- planner strategy quality or admission/rebalance heuristics
- runtime diagnostics formatter copy or sampled-rulegen presentation
- broader SRS schema/persistence semantics already covered in `SP2`
- DOM scan ordering and scan-budget behavior, which remains the final `SP5` slice

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the SRS action surface is now split across multiple workflow modules, but earlier direct coverage was concentrated on planning-context forwarding and the factory seam
- transition bugs here are easy to miss because the UI still renders and the helper paths may still work while buttons, status text, or ruleset-freshness side effects drift
- the static structure/doc map had also fallen behind the actual action-module stack loaded by `options.html`

## Contract Sketch

The intended current contract is:

1. the full SRS action module stack loads before `actions_controller.js`, not just the final `formatters/shared/workflows` subset
2. `initializeSet()` forwards current effective sizing plus `profileContext`, emits success vs plan-only status, and only marks ruleset freshness when initialization both applies and publishes
3. `refreshSetNow()` short-circuits cleanly on preflight failure, restores button state, and can still mark ruleset freshness even when admissions are a no-op if helper publication occurred
4. `resetSrsData()` requires two confirmations, does not load/helper-dispatch on cancellation, and maps outdated-helper command errors into a stable user-facing status
5. the architecture map should list the real split action modules and the current `srsActionsController` scope instead of the older partial stack

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Full SRS action script stack loads before the controller. | `options.html` | updated structure test | `fixed and verified in this slice` |
| Initialize forwards effective sizing/profile context and only marks ruleset freshness on published apply. | `maintenance_workflow.js` | new Node-backed maintenance contract test | `verified for this slice` |
| Refresh short-circuits on preflight failure and can still refresh ruleset freshness on no-op publication. | `maintenance_workflow.js` | new Node-backed maintenance contract test | `verified for this slice` |
| Reset requires double confirmation and maps outdated-helper failures into the explicit fallback status. | `maintenance_workflow.js` | new Node-backed maintenance contract test | `verified for this slice` |
| Architecture docs list the actual split action modules and current controller ownership. | options controller architecture doc | doc update plus doc-reference check | `fixed in this slice` |

## Invariants

1. SRS action transitions must remain explainable from helper result shape plus explicit controller policy
2. preflight failure and cancellation paths must restore button state and avoid accidental helper mutation
3. ruleset-freshness timestamps should only move when the current action contract says publication occurred
4. structure tests and architecture docs must describe the full split action stack, not a stale subset

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Initialize success | forwards sizing/profile context, sets success status, marks ruleset freshness |
| Initialize plan-only | keeps plan-only/default status and does not mark ruleset freshness |
| Refresh preflight block | helper refresh is skipped and button state recovers |
| Refresh no-op with publication | status remains no-op/default while ruleset freshness still updates |
| Reset cancelled | no settings load and no helper dispatch |
| Reset outdated helper | fallback error copy is surfaced and button state recovers |
| Static script order | every action submodule loads before `actions_controller.js` |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_srs_action_workflows.py core/tests/dev/test_extension_srs_maintenance_workflow_contract.py core/tests/architecture/test_extension_structure.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. add direct transition coverage for the post-split maintenance action module
2. tighten the static load-order test to the full SRS action stack
3. correct the architecture map so it matches the actual split module graph and controller ownership

## Outcome

Result:

- the post-split SRS action seam now has direct executable coverage for the high-risk initialize/refresh/reset transition paths, not only planning-context forwarding and factory composition
- the static structure check now guards the full action-module stack loaded by `options.html`
- the architecture map no longer under-describes the current SRS action split
- future UX work on this area can build on explicit transition contracts instead of rediscovering them from runtime behavior
