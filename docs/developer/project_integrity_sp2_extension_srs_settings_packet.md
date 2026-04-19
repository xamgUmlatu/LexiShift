# SP2 Extension SRS Settings Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted extension settings contract tests plus controller/settings/doc inspection
Purpose: bound the SP2.2 slice around the extension SRS settings contract so later profile/planner UX changes do not accidentally overstate what the current options UI edits or break the narrow save path that exists today
Source-of-truth: packet only; executable truth still lives in code, tests, docs, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`
- `srs_admission_selective_port_sequence.md`

## Slice

- Track: `SP2`
- Slice: `SP2.2`
- Title: extension SRS settings contract
- Pass type: verification-first with contract-pinning tests and carry-forward note logging

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `apps/chrome-extension/options/controllers/srs/planning_state.js`
- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_settings_contract.py`
- `core/tests/dev/test_extension_srs_profile_schema_contract.py`
- `core/tests/dev/test_extension_srs_action_workflows.py`

Primary contract/docs surface:

- `docs/srs/srs_profile_schema.md`
- `docs/developer/project_integrity_stabilization_backlog.md`
- `docs/developer/srs_admission_selective_port_sequence.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether planner strategy selection is semantically correct once profile context reaches helper code
- preview/rebalance mutation guarantees beyond the planning-state inputs they consume
- due-aware publication/runtime behavior
- helper-side profile interpretation of currently non-UI signal families
- transactional save/error-recovery behavior beyond logging it for a later slice

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- the current options UI only edits a small subset of the broader schema, which makes doc drift easy
- the save path depends on a narrow contract that is easy to break during later UX expansion
- a regression here can silently drop profile signal data without immediately breaking the visible happy path

## Contract Sketch

The intended current extension settings contract is:

1. pair-scoped runtime profile fields are saved under `srsProfiles.<profile_id>.srsByPair.<pair>` and mirrored to top-level runtime keys
2. pair-scoped signal data is saved under `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`
3. the current options UI directly edits only:
   - profile/runtime fields such as enablement, sizing, sound/highlight, semantic fallback, and feedback/exposure toggles
   - `interests`
   - `proficiency.estimated_value`
   - `difficultyPreferences.target_challenge_center`
4. other allowed signal families such as `objectives`, `empiricalTrends`, and `sourcePreferences` are persisted data-ready fields, not first-class options controls today
5. signal persistence is a top-level-family merge, not a deep nested merge
6. because nested merge is shallow, controller/planning-state code must preserve sibling nested keys by copying the existing `proficiency` and `difficultyPreferences` objects before overwriting their UI-owned fields

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Current options save only edits the small UI-owned signal subset rather than rewriting the entire signal schema. | `profile_runtime_controller.js` | `core/tests/dev/test_extension_srs_settings_contract.py` | `verified for this slice` |
| The save path preserves nested sibling keys inside `proficiency` and `difficultyPreferences` by cloning stored objects before updating the UI-owned field. | `profile_runtime_controller.js`, `planning_state.js` | `core/tests/dev/test_extension_srs_settings_contract.py`, `core/tests/dev/test_extension_srs_action_workflows.py` | `verified for this slice` |
| Unmentioned top-level allowed signal families survive a settings save because `updateSrsProfileSignals(...)` merges by top-level family before pruning/saving. | `signals_methods.js` | `core/tests/dev/test_extension_srs_settings_contract.py` | `verified for this slice` |
| Current docs should describe the broader signal schema as persisted/data-ready rather than implying all fields are directly editable in the current options UI. | `docs/srs/srs_profile_schema.md`, `srs_admission_selective_port_sequence.md` | direct doc sync in this slice | `corrected in this slice` |

## Invariants

1. saving the current options form must not delete unedited top-level allowed signal families
2. saving `proficiency.estimated_value` must not delete sibling nested keys already stored under `proficiency`
3. saving `difficultyPreferences.target_challenge_center` must not delete sibling nested keys already stored under `difficultyPreferences`
4. current-form planning overrides must mirror the same narrow UI-owned fields that the controller save path owns
5. schema breadth and UI edit surface must stay explicitly separate in docs and later UX work

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Rich stored signal payload exists before save | unedited top-level families remain after save |
| User edits only interests/proficiency estimate/challenge target | controller emits only that narrow signal update set |
| Stored `proficiency` or `difficultyPreferences` has extra nested keys | save path preserves those sibling keys |
| Planning preview/rebalance reads unsaved current-form values | planning-state resolver mirrors the same narrow field ownership as save |
| Reader consults schema docs for current capability | docs distinguish persisted schema breadth from first-class UI controls |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_extension_srs_settings_contract.py -q`
  - `python3 -m pytest core/tests/dev/test_extension_srs_profile_schema_contract.py -q`

## Planned Action For This Slice

1. pin the controller save payload so later UI edits cannot quietly widen or narrow it by accident
2. pin the settings-layer preservation behavior for unedited top-level signal families
3. keep the broader schema-vs-editable-surface distinction explicit in the packet, while avoiding broad doc churn in already-dirty docs
4. log the partial-write/atomicity risk as a carry-forward note instead of broadening this slice into failure-path redesign

## Outcome

Result:

- no immediate correctness defect found in the SP2.2 save contract
- the current contract is intentionally narrow and internally consistent:
  - controller save edits only first-class UI-owned signal fields
  - controller/planning-state logic preserves sibling nested keys for the edited nested families
  - settings persistence preserves unmentioned top-level allowed signal families
- the main integrity risk is future drift:
  - later UX work can accidentally treat the broader schema as if it were fully editable today
  - later refactors can forget that signal merge is shallow and must preserve nested siblings explicitly
- this slice therefore adds tests and a carry-forward note rather than changing product behavior
