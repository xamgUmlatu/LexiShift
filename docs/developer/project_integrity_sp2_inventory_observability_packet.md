# SP2 Inventory Observability Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 targeted inventory-resolution tests plus current-truth doc sync
Purpose: bound the SP2.7 slice around pair-local active-inventory observability so the current forgiving resolution model is stated explicitly in canonical docs instead of being stronger in code than in the ledger
Source-of-truth: packet only; executable truth still lives in code, tests, diagnostics, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_d3_active_inventory_packet.md`
- `../srs/srs_practice_layer_design.md`
- `feature_state_matrix.md`

## Slice

- Track: `SP2`
- Slice: `SP2.7`
- Title: active-inventory observability truth
- Pass type: verification-first with current-truth promotion

## Exact Seam

Primary code surface:

- `core/lexishift_core/srs/inventory.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`

Primary tests/evidence surface:

- `core/tests/srs/test_srs_inventory.py`
- `core/tests/helper/test_helper_engine.py`

Primary contract/docs surface:

- `docs/developer/feature_state_matrix.md`
- `docs/srs/srs_practice_layer_design.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/developer/project_integrity_secondary_pass_plan.md`

## Explicitly Out Of Scope

This slice does not directly review:

- adding a dedicated drift-repair artifact or repair workflow
- changing initialize/refresh/rebalance publication behavior
- making inventory resolution stricter than the store-backed fallback model
- due-aware serving or helper-rule confidence gating

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `medium-high`

Reasoning:

- the implementation already has a coherent fallback model, but it is easy for later lifecycle or UX work to over-read inventory as a hard authority unless that truth is kept explicit
- the highest risk here is docs/state drift rather than a hidden behavior defect

## Contract Sketch

The intended current SP2.7 inventory contract is:

1. pair-local active inventory is a real persistence seam, but not the only authority for current membership
2. when no pair entry exists, active ids resolve from the store with source `store_fallback`
3. when stored ids are stale, missing ids are dropped during resolution rather than breaking flows
4. helper write paths may backfill inventory metadata from store-derived membership
5. runtime diagnostics is the main operator-facing seam for observing this state through `inventory_source`, timestamps, and stale-id count

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Missing pair inventory falls back to store-derived membership rather than failing resolution. | `resolve_active_item_ids(...)` | `core/tests/srs/test_srs_inventory.py` | `verified for this slice` |
| Stale stored ids are dropped while keeping the inventory resolution path explicit. | `resolve_active_item_ids(...)`, diagnostics join | `core/tests/srs/test_srs_inventory.py`, `core/tests/helper/test_helper_engine.py` | `verified for this slice` |
| Runtime diagnostics remains the canonical operator-facing observability surface for inventory vs store-fallback state. | `runtime_diagnostics.py` | `core/tests/helper/test_helper_engine.py` | `verified for this slice` |
| Canonical docs now describe inventory as a forgiving seam rather than a hard authority. | `feature_state_matrix.md`, `srs_practice_layer_design.md` | direct doc sync in this slice | `corrected in this slice` |

## Invariants

1. do not overstate inventory as stricter authority than the store
2. keep missing-pair fallback and stale-id dropping explicit
3. keep diagnostics as the main observability surface unless a later slice intentionally adds a stronger repair/reporting model
4. do not turn this slice into a publication or runtime-behavior redesign

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Inventory present for pair | active ids resolve from inventory and stale ids are pruned |
| Inventory object exists but pair entry is missing | active ids fall back to store membership |
| Runtime diagnostics read | `inventory_source` and stale-id count remain visible |
| Reader consults canonical docs | docs describe the current forgiving model honestly |

## Validation Floor

- `PYTHONPATH=core python3 -m pytest core/tests/srs/test_srs_inventory.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`

## Planned Action For This Slice

1. add one direct resolver test for missing-pair fallback behavior
2. promote the forgiving active-inventory model into the feature-state ledger and SRS practice doc
3. resolve `N-006` by choosing explicit current-truth promotion over a speculative repair mechanism

## Outcome

Result:

- direct inventory-resolution coverage now pins missing-pair fallback in addition to the existing stale-id pruning behavior
- canonical docs now state plainly that pair-local active inventory is a forgiving seam backed by runtime diagnostics rather than a hard authority
- this resolves the immediate observability/doc-drift concern without broadening the SP2 track into inventory repair redesign
