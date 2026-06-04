# SP6 Feature-State Refresh Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted extension workflow contract tests plus state/doc checks
Purpose: bound the first SP6 slice around feature-state contradiction refresh so the canonical ledger now carries the recently verified extension/controller workflow seam instead of leaving that truth distributed only across SP5 packets and architecture docs
Source-of-truth: packet only; executable truth still lives in the extension code, targeted tests, structure checks, and `feature_state_matrix.md`
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `../architecture/options_controllers_architecture.md`
- `../architecture/extension_system_map.md`
- `../architecture/chrome_extension_technical.md`
- `project_integrity_sp5_options_bootstrap_packet.md`
- `project_integrity_sp5_share_import_packet.md`
- `project_integrity_sp5_srs_action_transitions_packet.md`
- `project_integrity_sp5_dom_scan_packet.md`

## Slice

- Track: `SP6`
- Slice: feature-state contradiction refresh
- Title: extension workflow current-truth promotion
- Pass type: verification-first state-ledger correction

## Exact Seam

Primary contract/docs surface:

- `docs/developer/feature_state_matrix.md`
- `docs/architecture/options_controllers_architecture.md`
- `docs/architecture/extension_system_map.md`
- `docs/architecture/chrome_extension_technical.md`

Primary code/evidence surface:

- `apps/chrome-extension/options.js`
- `apps/chrome-extension/options/controllers/rules/share_center/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions/maintenance_workflow.js`
- `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_extension_options_bootstrap_contract.py`
- `core/tests/dev/test_extension_share_center_workflow_contract.py`
- `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py`
- `core/tests/dev/test_extension_dom_scan_runtime_contract.py`

## Explicitly Out Of Scope

This slice does not directly review:

- stale `Last updated` headers or mixed/reference labeling in extension architecture docs
- backlog snapshot wording outside the feature-state ledger
- broader generated-evidence citation hygiene
- new browser E2E automation or helper-latency testing

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `medium-high`

Reasoning:

- the underlying extension seams are now much better verified than the canonical ledger made obvious
- leaving that state implicit increases the chance that later cleanup or UX work re-discovers the same contract from packets and tests instead of a single current-truth row
- the main risk here is state-ledger drift, not hidden runtime breakage

## Contract Sketch

The intended current SP6.1 contract is:

1. the feature-state ledger should carry the verified extension/controller workflow seam as canonical current truth
2. `implemented`, `default-on`, and `verified` should remain separate from narrower known gaps inside that seam
3. Share Center compatibility forwarding must stay explicit as a current limitation, not an invisible schema assumption
4. seam-level controller/runtime tests should be promoted as evidence, but not overstated as full browser E2E proof

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Options bootstrap fail-fast and bind-before-load order are real runtime contracts, not just structure assumptions. | `options.js`, structure test | `core/tests/dev/test_extension_options_bootstrap_contract.py`, `core/tests/architecture/test_extension_structure.py` | `verified before this slice; promoted here` |
| Share Center remains a compatibility bridge to legacy share scopes while preserving bundle target identity and reload-vs-sync behavior. | `share_center/workflows.js` | `core/tests/dev/test_extension_share_center_workflow_contract.py` | `verified before this slice; promoted here` |
| SRS maintenance workflows preserve planning/profile context and explicit transition behavior across initialize/refresh/reset. | `maintenance_workflow.js` | `core/tests/dev/test_extension_srs_maintenance_workflow_contract.py` | `verified before this slice; promoted here` |
| DOM scan ordering and page-budget behavior have direct runtime-contract coverage. | `dom_scan_runtime.js`, manifest-order structure test | `core/tests/dev/test_extension_dom_scan_runtime_contract.py`, `core/tests/architecture/test_extension_structure.py` | `verified before this slice; promoted here` |
| The canonical state ledger now exposes the full extension workflow seam in one place. | `feature_state_matrix.md` | direct doc/state correction in this slice | `fixed in this slice` |

## Invariants

1. current-truth status must not live only in packets when the seam is broad enough to affect later UX and cleanup work
2. Share Center compatibility envelopes must stay explicit until a new schema/version exists
3. seam-level contract coverage must not be described as stronger than it is
4. the state ledger should route readers toward the current architecture docs and direct tests, not replace them

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Reader checks feature-state ledger for extension workflow truth | one canonical row now points to the verified options/share/SRS/DOM-scan seam |
| Reader asks whether Share Center already has narrowed profile schemas | ledger keeps the legacy `profile` / `srs` compatibility mapping explicit |
| Reader uses state ledger to plan later UX work | ledger shows the seam is verified, default-on, and still has a specific schema-narrowing gap |
| Reader interprets test coverage scope | ledger keeps contract coverage separate from full browser E2E claims |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_options_bootstrap_contract.py core/tests/dev/test_extension_share_center_workflow_contract.py core/tests/dev/test_extension_srs_maintenance_workflow_contract.py core/tests/dev/test_extension_dom_scan_runtime_contract.py core/tests/architecture/test_extension_structure.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. confirm the exact missing feature-state surface rather than widening into a broader extension-doc cleanup
2. promote the recently verified extension workflow seam into one canonical ledger row
3. keep the remaining Share Center schema-narrowing gap explicit inside that row
4. log any separate doc-metadata drift as a later SP6 seam instead of folding it into this packet

## Outcome

Result:

- the canonical state ledger now exposes the recently verified extension/controller workflow seam instead of leaving that truth scattered across four SP5 packets
- later cleanup and UX work can recover the current extension workflow contract from `feature_state_matrix.md` without re-reading the entire SP5 sequence
- the remaining compatibility-envelope limitation stays visible as a known gap rather than an implied future behavior
