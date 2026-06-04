# SP7 Share Center Compatibility Copy Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 Share Center compatibility-copy pass plus targeted tests
Purpose: bound the next SP7 slice around Share Center export wording so the operator-facing UI now states when `Full profile` and `Profile settings` still use the existing compatibility formats instead of implying a newly narrowed schema
Source-of-truth: packet only; executable truth still lives in the Share Center workflow code, current architecture docs, state ledger, and targeted contract tests
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `project_integrity_sp5_share_import_packet.md`
- `../architecture/options_controllers_architecture.md`
- `../../apps/chrome-extension/options.html`
- `../../apps/chrome-extension/_locales/en/messages.json`
- `../../core/tests/dev/test_extension_share_center_workflow_contract.py`
- `../../core/tests/dev/test_extension_share_center_copy_contract.py`

## Slice

- Track: `SP7`
- Slice: Share Center compatibility-copy follow-through
- Title: Share Center scope-language clarification
- Pass type: UI-copy and state-doc correction

## Exact Seam

Primary UI/code surface:

- `apps/chrome-extension/options.html`
- `apps/chrome-extension/_locales/en/messages.json`
- `apps/chrome-extension/_locales/de/messages.json`
- `apps/chrome-extension/_locales/ja/messages.json`
- `apps/chrome-extension/_locales/zh/messages.json`

Primary docs/evidence surface:

- `apps/chrome-extension/README.md`
- `docs/architecture/options_controllers_architecture.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`
- `core/tests/dev/test_extension_share_center_workflow_contract.py`
- `core/tests/dev/test_extension_share_center_copy_contract.py`

## Explicitly Out Of Scope

This slice does not directly review:

- a new narrowed share schema for full-profile or profile-settings export
- legacy share-code compression/encoding mechanics
- import-scope behavior beyond the already verified reload-vs-sync seam
- removal of the legacy Share Code card

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `medium-high`

Reasoning:

- the workflow seam was already verified, but the remaining mismatch lived in product wording rather than code behavior
- if the Share Center copy keeps sounding narrower than the actual envelopes, future UX or docs work can assume a schema guarantee that does not yet exist

## Contract Sketch

The intended current SP7 Share Center wording contract is:

1. the Share Center can keep the concise labels `Full profile` and `Profile settings`
2. the surrounding export copy must also state that these targets still use the existing compatibility formats
3. docs and state surfaces should match that operator-facing truth
4. a truly narrower profile-settings or full-profile export remains future schema work, not something implied by wording alone

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| The Share Center still forwards `Full profile` to legacy `profile` and `Profile settings` to legacy `srs`. | workflow seam | `test_extension_share_center_workflow_contract.py` | `verified before this slice` |
| The remaining ambiguity was user-facing copy that could be read as a narrower export promise. | Share Center modal copy plus note `N-019` | direct UI/doc inspection before this slice | `verified before this slice` |
| The export modal now states the compatibility-format mapping explicitly. | `options.html`, locale catalogs | `test_extension_share_center_copy_contract.py` | `fixed in this slice` |
| Docs/state surfaces now treat this as resolved wording ambiguity while keeping future schema narrowing explicit. | architecture/state/notes docs | direct doc updates in this slice | `fixed in this slice` |

## Invariants

1. do not silently redefine the legacy `profile` / `srs` envelopes behind existing labels
2. keep operator-facing wording honest about compatibility formats
3. keep future schema narrowing framed as explicit versioned work, not deferred copy debt

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Operator chooses `Full profile` export | modal copy states this is the existing profile share format |
| Operator chooses `Profile settings` export | target hint states this is the existing SRS settings format |
| Future maintainer reads current docs/state | compatibility wording matches the workflow contract and does not imply a narrower shipped schema |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_share_center_workflow_contract.py core/tests/dev/test_extension_share_center_copy_contract.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. add explicit compatibility wording to the Share Center export modal and relevant hints
2. cover that wiring with a small copy contract test
3. refresh architecture/state/docs so `N-019` is resolved as wording clarity, not left as an open ambiguity

## Outcome

Result:

- the Share Center still uses the same compatibility envelopes, but the UI no longer presents those labels as if they were already schema-narrowed exports
- future UX work can now distinguish between the shipped compatibility format and any later schema/version redesign
- `N-019` is resolved as an operator-facing wording fix rather than being left as a standing mismatch between docs and UI
