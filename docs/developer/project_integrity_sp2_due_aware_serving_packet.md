# SP2 Due-Aware Serving Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted harness/runtime-gate contract tests plus helper/runtime/doc inspection
Purpose: bound the SP2.4 slice around due-aware serving so the current contract is stated honestly: due queues exist, but helper publication and runtime gating still operate on the broader active/admitted inventory
Source-of-truth: packet only; executable truth still lives in code, tests, docs, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../srs/srs_practice_layer_design.md`
- `../srs/srs_hybrid_model_technical.md`

## Slice

- Track: `SP2`
- Slice: `SP2.4`
- Title: due-aware serving
- Pass type: verification-first with current-truth promotion

## Exact Seam

Primary code surface:

- `core/lexishift_core/srs/scheduler.py`
- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `apps/chrome-extension/shared/srs/srs_gate.js`

Primary tests/evidence surface:

- `core/tests/dev/test_srs_quality_harness.py`
- `core/tests/dev/test_srs_quality_summary.py`
- `core/tests/dev/test_extension_srs_runtime_gate_contract.py`
- `core/tests/helper/test_helper_engine.py`

Primary contract/docs surface:

- `docs/srs/srs_practice_layer_design.md`
- `docs/srs/srs_roadmap.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether due-aware publication should become the future product contract
- scheduler math quality or FSRS tuning
- refresh policy details beyond the admitted-vs-due-vs-published relationship
- redesign of helper publication artifacts

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `high`
- priority: `very high`

Reasoning:

- the due-aware question spans scheduler state, helper publication, runtime gating, and test evidence
- if current docs overstate due-aware behavior, later UX/product work will be built on a false runtime assumption
- the mismatch is easy to miss because each layer looks locally reasonable on its own

## Contract Sketch

The intended current due-aware serving contract is:

1. scheduler code can derive a due queue from `next_due`
2. helper initialize/refresh/rebalance publication runs rulegen against active inventory ids, not a separately materialized due subset
3. runtime SRS gating accepts the helper-published SRS ruleset wholesale and does not derive a due-only subset at extension runtime
4. harness and journey evidence intentionally surface "published broader than due" as an explicit warning instead of pretending the due-aware contract is already implemented
5. current truth should therefore remain:
   - due-aware serving is a planned contract
   - current shipped publication/runtime behavior is admitted-inventory serving with due-aware warnings and diagnostics around it

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Scheduler can derive a due queue from stored SRS state. | `scheduler.py` | `scripts/testing/srs_quality_harness.py`, `docs/srs/srs_hybrid_model_technical.md` | `verified for this slice` |
| Helper publication uses active inventory ids rather than a due-only subset. | `initialize_set.py`, `refresh_set.py`, `rebalance_set.py`, `helper/rulegen.py` | `core/tests/helper/test_helper_engine.py`, `scripts/testing/srs_quality_harness.py` | `verified for this slice` |
| Runtime gate accepts the helper-published SRS ruleset as active and does not apply due-only filtering. | `srs_gate.js` | `core/tests/dev/test_extension_srs_runtime_gate_contract.py` | `verified for this slice` |
| Harness intentionally treats broader-than-due publication as a warning, not a hidden pass condition. | `srs_quality_harness.py`, `srs_quality_summary.py` | `core/tests/dev/test_srs_quality_harness.py`, `core/tests/dev/test_srs_quality_summary.py` | `verified for this slice` |
| State/docs should keep due-aware serving explicitly planned until helper publication and runtime gating actually narrow to due state. | `feature_state_matrix.md`, practice/roadmap docs | doc/code inspection plus this packet | `promoted in this slice` |

## Invariants

1. existence of a due queue must not be conflated with due-aware publication
2. helper publication scope should be described from the actual `active_item_ids` contract, not from scheduler intent alone
3. runtime gate behavior should be described from the active helper ruleset contract, not from future due-serving policy
4. harness warnings about broader-than-due publication must remain explicit until the executable contract changes
5. docs and state ledger should not claim end-to-end due-aware serving before a due-specific artifact or runtime filter exists

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Scheduler selects due items from store state | due queue exists and is non-empty in synthetic scenarios |
| Helper publishes after initialize/refresh | publication target counts stay bounded by admitted store/inventory counts |
| Runtime consumes helper SRS rules | gate accepts all helper SRS rules as active without due filtering |
| Feedback-cycle scenario | harness can surface broader-than-due publication as a warning |
| Current-truth docs/state | due-aware serving remains explicitly planned, not silently treated as shipped |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_extension_srs_runtime_gate_contract.py -q`
  - `python3 -m pytest core/tests/dev/test_srs_quality_harness.py -q`
  - `python3 -m pytest core/tests/dev/test_srs_quality_summary.py -q`
- state/doc integrity:
  - `npm --prefix scripts run check:state`
  - `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. verify the admitted-vs-due-vs-published relationship from code and harness evidence
2. pin the runtime-gate side explicitly so later readers cannot infer hidden due filtering
3. promote the due-aware warning from the secondary-pass notes into the state ledger/current-truth packet rather than leaving it as a floating caveat

## Outcome

Result:

- no hidden due-aware serving implementation was found
- current behavior is internally consistent once described correctly:
  - scheduler builds due queues
  - helper publication still targets the active/admitted inventory
  - runtime gate accepts the helper-published SRS ruleset as active
  - harness warns when published scope is broader than due
- this slice therefore promotes the warning into explicit current truth instead of treating it as an unresolved mystery
