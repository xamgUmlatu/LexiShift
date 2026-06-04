# SP5 Options Bootstrap Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted options-bootstrap/runtime contract tests plus structure/doc checks
Purpose: bound the first `SP5` slice around the options bootstrap/module-load seam so the post-split controller graph has direct executable evidence for its fail-fast and boot-order contract
Source-of-truth: packet only; executable truth still lives in the options bootstrap code, architecture tests, and current options-controller docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `../architecture/options_controllers_architecture.md`
- `../architecture/extension_system_map.md`
- `project_integrity_f14_srs_action_workflow_split_packet.md`

## Slice

- Track: `SP5`
- Slice: options bootstrap and module-load contract
- Title: controller graph bootstrap evidence
- Pass type: verification-first slice with narrow doc/test correction

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options.js`
- `apps/chrome-extension/options/core/bootstrap/controller_graph.js`
- `apps/chrome-extension/options/core/bootstrap/controller_graph_elements.js`
- `apps/chrome-extension/options.html`

Primary docs/evidence surface:

- `docs/architecture/options_controllers_architecture.md`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_extension_options_bootstrap_contract.py`

## Explicitly Out Of Scope

This slice does not directly review:

- SRS action preview/rebalance semantics already covered by `D8`
- maintenance workflow split behavior already covered by `F14`
- profile share/import/export payload fidelity
- DOM scan ordering and scan-budget behavior
- broader controller refactors or hotspot splits

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- a broken bootstrap seam prevents the options app from starting at all
- architecture tests already covered file presence and script order, but not the runtime fail-fast/boot-order behavior described in the architecture doc
- `controller_graph_elements.js` had become a live dependency in code and HTML order without being carried through the architecture map or structure test

## Contract Sketch

The intended current bootstrap contract is:

1. `options.html` loads the bootstrap modules in strict dependency order before `options.js`
2. `options.js` fails fast with explicit bootstrap-module errors when required top-level modules are missing
3. `controller_graph.js` fails fast when the graph-elements bootstrap module is unavailable
4. successful boot still calls `eventWiringController.bind()` before `pageInitController.load()`
5. `controller_graph_elements.js` is part of the real bootstrap seam, not an incidental helper file

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Bootstrap files exist and load before `options.js`. | `options.html`, bootstrap files | structure test | `fixed and verified in this slice` |
| `options.js` fails fast when a required bootstrap module is missing. | `options.js` | new Node-backed bootstrap contract test | `verified for this slice` |
| Successful options boot binds events before page init. | `options.js` | new Node-backed bootstrap contract test | `verified for this slice` |
| `controller_graph.js` requires `controller_graph_elements.js` explicitly. | `controller_graph.js` | new Node-backed bootstrap contract test plus updated structure test | `verified for this slice` |
| Architecture doc lists the actual bootstrap seam. | options architecture doc | doc update plus doc-reference check | `fixed in this slice` |

## Invariants

1. options bootstrap dependencies must stay explicit in both code and structure evidence
2. startup should fail loudly on missing required bootstrap modules
3. the options-root startup order remains `bind` then `load`
4. architecture docs must not omit a live bootstrap dependency that the runtime requires

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Missing top-level bootstrap module | `options.js` throws the expected explicit error |
| Missing graph-elements bootstrap module | `controller_graph.js` throws the expected explicit error |
| Successful boot with stubbed dependencies | options root composes the controller graph and calls `bind` before `load` |
| Static load-order inspection | `options.html` lists `controller_graph_elements.js` before `controller_graph.js` and before `options.js` |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_options_bootstrap_contract.py core/tests/architecture/test_extension_structure.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. promote `controller_graph_elements.js` into the explicit bootstrap contract
2. add direct Node-backed runtime tests for fail-fast and successful boot ordering
3. correct the architecture doc and structure test so the documented seam matches the executable one

## Outcome

Result:

- the options bootstrap seam now has direct runtime contract coverage instead of relying only on file-presence and script-order checks
- the architecture map and structure test now treat `controller_graph_elements.js` as a first-class bootstrap dependency
- the post-split options root has executable evidence for the fail-fast and boot-order behavior its docs already claimed
