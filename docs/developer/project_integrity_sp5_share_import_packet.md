# SP5 Share/Import Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted Share Center workflow contract tests plus doc-reference/diff safety checks
Purpose: bound the second `SP5` slice around Share Center export/import forwarding so the post-split controller seam has direct executable evidence for payload-target preservation and reload-vs-sync behavior
Source-of-truth: packet only; executable truth still lives in the Share Center workflow modules, the legacy share controller / rules manager, and current extension controller docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `../architecture/options_controllers_architecture.md`
- `../project_health_remediation_workstream.md`
- `project_integrity_secondary_pass_notes.md`

## Slice

- Track: `SP5`
- Slice: profile share/import/export payload fidelity
- Title: Share Center workflow forwarding contract
- Pass type: verification-first slice with narrow current-truth doc correction

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/controllers/rules/share_controller.js`
- `apps/chrome-extension/options/controllers/rules/share_center/workflows.js`
- `apps/chrome-extension/options/controllers/rules/share_center/selection.js`
- `apps/chrome-extension/options/core/rules_manager.js`
- `apps/chrome-extension/options/core/rules_manager/base_methods.js`
- `apps/chrome-extension/options/core/rules_manager/profile_share_methods.js`
- `apps/chrome-extension/options/core/rules_manager/profile_share_module_methods.js`
- `apps/chrome-extension/options/core/rules_manager/ruleset_methods.js`
- `apps/chrome-extension/options/core/rules_manager/bundle_methods.js`

Primary docs/evidence surface:

- `apps/chrome-extension/README.md`
- `docs/architecture/options_controllers_architecture.md`
- `core/tests/dev/test_extension_share_center_workflow_contract.py`

## Explicitly Out Of Scope

This slice does not directly review:

- legacy share-code compression/encoding mechanics
- broader GUI/core import-export flows already covered in earlier packets
- removal of the legacy share-code card
- introduction of a brand-new narrowed schema for `Full profile` or `Profile settings`
- DOM scan ordering or SRS workflow transitions, which remain later `SP5` slices

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `low`
- priority: `high`

Reasoning:

- the Share Center split moved selection, file I/O, and import/export orchestration into new modules, but there was no direct extension-side contract test around what those modules actually forward to the legacy share backend
- payload-scope mistakes are easy to miss because export/import still "work" while silently carrying the wrong scope, wrong identity fields, or the wrong post-import refresh behavior
- future UX work will likely touch this seam again, so current compatibility boundaries need to be explicit

## Contract Sketch

The intended current contract is:

1. the Share Center owns selection, file export/import workflow, and status messaging, not the canonical share schema itself
2. `Full profile` export still forwards to the legacy `profile` share envelope for compatibility
3. custom selection export preserves the receiving-side identity fields:
   - ruleset: `rulesetPath`, `rulesetName`
   - SRS pair: `srsPair`
   - module: `moduleId`, `targetLanguage`
   - appearance: `appearance_theme`
   - mixed selection: `bundleTargets` with stable kind mapping
4. import forwards the raw payload text plus current `profileId` and `helperManager` into the legacy share controller
5. imports that only affect rulesets/modules resync the current profile without a hard page reload
6. imports that touch profile settings, SRS pair progress, or appearance still force a reload because they mutate broader runtime state

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Full-mode Share Center export still maps to legacy `profile`. | `share_center/workflows.js`, `share_controller.js`, `rules_manager.js` | new Node-backed workflow contract test | `verified for this slice` |
| Multi-target export preserves bundle target identity fields across the controller seam. | `share_center/workflows.js`, `selection.js` | new Node-backed workflow contract test | `verified for this slice` |
| Import forwards raw payload text plus current profile/helper context. | `share_center/workflows.js`, `share_controller.js` | new Node-backed workflow contract test | `verified for this slice` |
| Ruleset/modules-only imports resync without reload, while broader bundle/profile-setting imports still reload. | `share_center/workflows.js` | new Node-backed workflow contract test | `verified for this slice` |
| Canonical architecture docs describe the current legacy-compatibility scope mapping explicitly. | options controller architecture doc | doc update plus doc-reference check | `fixed in this slice` |

## Invariants

1. Share Center must stay a compatibility bridge over `rulesShareController`, not an implicit second share-schema authority
2. selection-target exports must preserve the exact ids/paths/pairs the receiving side expects
3. reload-vs-sync behavior must stay explainable from the returned import scope/result, not from incidental UI side effects
4. future narrowing of `Full profile` or `Profile settings` exports must use an explicit new schema/version, not a silent reinterpretation of legacy envelopes

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Full-mode export | forwards `scope: "profile"` with the current profile id |
| Mixed custom export | forwards `scope: "bundle"` plus stable `bundleTargets` entries for each supported selected node |
| Ruleset import | syncs current profile and avoids hard reload |
| Bundle import with only rulesets/modules | syncs current profile and avoids hard reload |
| Bundle import with profile settings or SRS pair data | schedules reload instead of relying on partial in-place resync |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_share_center_workflow_contract.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. add direct Node-backed coverage for Share Center export/import forwarding
2. make the legacy-scope compatibility mapping explicit in current architecture docs
3. capture the remaining schema-narrowing question as a carry-forward note instead of silently treating it as resolved

## Outcome

Result:

- the Share Center split now has direct executable evidence for the controller-level forwarding contract it relies on
- future UX work can distinguish between two different concerns:
  - the workflow seam, which is now verified directly
  - the legacy-scope payload design, which remains an explicit compatibility choice rather than an undocumented assumption
- the remaining "narrower profile schema" question is preserved as a carry-forward note instead of being lost between passes
