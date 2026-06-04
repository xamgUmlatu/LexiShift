# SP2 Planner Strategy Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted planner/helper contract tests plus planner/helper/doc inspection
Purpose: bound the SP2.3 slice around SRS planner strategy truth so docs and the state ledger reflect the currently executable strategy split instead of flattening every non-frequency lane into the same status
Source-of-truth: packet only; executable truth still lives in code, tests, docs, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../srs/srs_set_planning_technical.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `SP2`
- Slice: `SP2.3`
- Title: planner strategy truth
- Pass type: verification-first with contract-pinning tests and narrow state/doc correction

## Exact Seam

Primary code surface:

- `core/lexishift_core/srs/set_planner.py`
- `core/lexishift_core/helper/use_cases/set_planning.py`
- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/admission_preview.py`
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
- `core/lexishift_core/helper/engine.py`
- `apps/chrome-extension/options/core/helper/srs_set_methods.js`

Primary tests/evidence surface:

- `core/tests/srs/test_srs_set_planner.py`
- `core/tests/dev/test_srs_planner_strategy_contract.py`
- `core/tests/helper/test_helper_engine.py`

Primary contract/docs surface:

- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_profile_schema.md`
- `docs/developer/feature_state_matrix.md`
- `docs/srs/srs_roadmap.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether profile-bootstrap scoring quality is good enough to replace frequency-bootstrap execution
- due-aware serving or refresh semantics
- refresh/adaptive-refresh execution wiring
- broader roadmap cleanup beyond the minimal truth corrections needed for the current contract

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- the current planner taxonomy spans multiple helper entrypoints, so it is easy for summary docs to collapse them incorrectly
- the most likely failure here is not a crash, but wrong present-tense claims about what is executable today
- that kind of mismatch makes later UX and lifecycle work harder because reviewers start from the wrong baseline

## Contract Sketch

The intended current planner-strategy contract is:

1. `frequency_bootstrap` is the baseline executable bootstrap lane
2. `profile_bootstrap` is executable only via fallback to the frequency-bootstrap execution path; diagnostics and preview ranking can still reflect profile-bootstrap context
3. `profile_growth` is not a general growth-admission strategy yet, but the dedicated rebalance helper lane is executable today:
   - planner marks `strategy_requested="profile_growth"`
   - planner keeps `strategy_effective="profile_growth"`
   - dedicated rebalance preview/apply use `execution_mode="rebalance_preview"` / `rebalance_apply`
4. `adaptive_refresh` remains planner-only
5. current top-level summary docs and the state ledger should distinguish:
   - bootstrap/initialize/admission-preview truth
   - rebalance preview/apply truth
   - future general growth/adaptive-refresh work

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper planning for `profile_bootstrap` still resolves to effective frequency bootstrap. | `set_planner.py`, `set_planning.py`, `initialize_set.py`, `admission_preview.py` | `core/tests/srs/test_srs_set_planner.py`, `core/tests/dev/test_srs_planner_strategy_contract.py`, `core/tests/helper/test_helper_engine.py` | `verified for this slice` |
| Dedicated rebalance preview/apply keeps `profile_growth` as the effective strategy instead of collapsing back to frequency bootstrap. | `set_planner.py`, `rebalance_set.py`, `helper/engine.py`, extension helper wiring | `core/tests/srs/test_srs_set_planner.py`, `core/tests/dev/test_srs_planner_strategy_contract.py`, `core/tests/helper/test_helper_engine.py` | `verified for this slice` |
| `adaptive_refresh` still remains planner-only. | `set_planner.py` | `core/tests/srs/test_srs_set_planner.py` | `verified for this slice` |
| State/doc summaries should not describe every `profile_growth` path as planner-only. | `feature_state_matrix.md`, `srs_set_planning_technical.md`, `srs_profile_schema.md` | doc/code inspection plus this packet | `corrected in this slice` |

## Invariants

1. `strategy_requested` and `strategy_effective` must stay distinct whenever a requested strategy falls back to another executable lane
2. bootstrap planning and rebalance planning must not be summarized as if they share the same execution truth
3. `profile_bootstrap` fallback behavior must remain explicit until helper initialization actually runs the profile-bootstrap execution path
4. `profile_growth` should only be described as executable where the dedicated rebalance preview/apply lane actually exists
5. `adaptive_refresh` should remain clearly non-executable until helper wiring lands

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| `plan_srs_set` requests `profile_bootstrap` | effective strategy remains `frequency_bootstrap` |
| `srs_initialize` / admission preview use `profile_bootstrap` | execution still follows the frequency-bootstrap lane while returning profile diagnostics |
| `plan_srs_rebalance` requests `profile_growth` with objective `rebalance` | plan is executable and keeps effective strategy `profile_growth` |
| `apply_srs_rebalance` runs the same lane | plan payload upgrades to `rebalance_apply` without pretending the strategy fell back |
| `adaptive_refresh` requested | planner remains non-executable |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_srs_planner_strategy_contract.py -q`
  - `python3 -m pytest core/tests/srs/test_srs_set_planner.py -q`
- state/doc integrity:
  - `npm --prefix scripts run check:state`
  - `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. pin the helper-boundary contract for bootstrap vs rebalance strategy behavior
2. tighten the nearest current-truth docs and state ledger so they no longer flatten `profile_growth` into planner-only everywhere
3. leave broader roadmap/planning cleanup for later slices unless current-tense wording is materially wrong

## Outcome

Result:

- the main contradiction was real but narrow:
  - bootstrap/initialize/admission-preview still resolve through frequency-bootstrap execution
  - dedicated rebalance preview/apply already expose an executable `profile_growth` lane
- no product-code bug needed fixing
- this slice therefore adds focused contract coverage and corrects the state/doc summaries that had collapsed the rebalance lane into planner-only behavior
