# SP2 Settings Save Failure Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 targeted extension settings failure tests plus controller/binding inspection
Purpose: bound the SP2.6 slice around SRS settings save-failure visibility so the current multi-step save path is operator-visible and honestly framed without broadening into transactional redesign
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_sp2_extension_srs_settings_packet.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `SP2`
- Slice: `SP2.6`
- Title: settings save failure visibility
- Pass type: bounded failure-path explicitness fix with contract-pinning tests

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `apps/chrome-extension/options/controllers/page/events/srs_bindings.js`
- `apps/chrome-extension/_locales/en/messages.json`
- `apps/chrome-extension/_locales/de/messages.json`
- `apps/chrome-extension/_locales/ja/messages.json`
- `apps/chrome-extension/_locales/zh/messages.json`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_settings_contract.py`

Primary contract/docs surface:

- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/developer/project_integrity_secondary_pass_plan.md`

## Explicitly Out Of Scope

This slice does not directly review:

- transactional rollback or cross-write compensation for SRS settings saves
- planner strategy, due-aware serving, or helper-side profile interpretation
- widening the current options UI edit surface
- inventory drift repair/reporting beyond late save failure visibility

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- the save path already performs three distinct writes, so late failures can leave partly updated state even when the visible form looks simple
- the immediate correctness gap was not that the save order existed, but that the failure mode was not clearly surfaced at the UI binding boundary
- a narrow explicitness fix materially improves operator trust without the risk of redesigning persistence order mid-pass

## Contract Sketch

The intended current SP2.6 save-failure contract is:

1. `saveSrsSettings()` still uses the current write order:
   - pair/profile persistence
   - runtime publish
   - signal persistence
2. the save path still is not transactional and does not attempt rollback
3. once profile persistence succeeds, later failures are annotated as partial-save failures rather than looking like generic save errors
4. SRS settings field changes route through the shared async listener wrapper, so those failures reach the normal status/error surface instead of bypassing it as raw rejected promises
5. the success path and the narrow UI-owned save payload remain unchanged

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Late signal-persistence failure after earlier save phases is surfaced as an explicit partial-save error. | `profile_runtime_controller.js` | `core/tests/dev/test_extension_srs_settings_contract.py` | `verified for this slice` |
| SRS settings change inputs now bind through the shared async listener wrapper with the settings-save failure fallback. | `srs_bindings.js` | `core/tests/dev/test_extension_srs_settings_contract.py` | `verified for this slice` |
| User-facing status copy exists for both generic save failure and partial-save failure. | extension locale files | direct code inspection plus targeted test fallback assertions | `verified for this slice` |

## Invariants

1. keep the current save order explicit rather than implicitly claiming atomicity
2. make late failures operator-visible at the same binding layer used by other async page actions
3. preserve the existing success-path payload and signal-merge contract
4. do not widen this slice into persistence redesign or helper behavior changes

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Normal field-change save | success path remains unchanged |
| Late signal-persistence failure | error is marked as partial save |
| Settings input change binding | async wrapper owns the error path for settings saves too |
| Localized status surface | failure keys exist for the supported extension locales |

## Validation Floor

- `node --check apps/chrome-extension/options/controllers/page/events/srs_bindings.js`
- `node --check apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `PYTHONPATH=core python3 -m pytest core/tests/dev/test_extension_srs_settings_contract.py -q`
- `python3 scripts/dev/check_doc_references.py`

## Planned Action For This Slice

1. annotate late save failures inside `saveSrsSettings()` without reordering persistence
2. route settings change bindings through `bindAsyncListener`
3. document the slice as an explicit visibility fix rather than a transactional guarantee

## Outcome

Result:

- SRS settings field changes now use the shared async binding path, so save failures reach the normal status/error surface
- `saveSrsSettings()` now rethrows late failures as explicit partial-save errors once earlier writes have already committed
- the save path still is not transactional, and this packet keeps that current truth explicit instead of overstating the guarantee
- targeted Node-backed settings contract coverage reran green (`4 passed`)
