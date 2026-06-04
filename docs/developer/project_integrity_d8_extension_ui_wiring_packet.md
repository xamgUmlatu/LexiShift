# D8 Extension/UI Admission Wiring Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted extension/controller tests, helper preview/rebalance tests, semantic Phase 0 baseline rerun, and admission preference sanity harness
Purpose: bound the D8 slice around the options/controller admission wiring so saved settings, unsaved form overrides, helper calls, and preview/rebalance execution stay aligned
Source-of-truth: packet only; executable truth still lives in extension/controller code, helper/native-host code, tests, and local validation runs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_secondary_pass_notes.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D8`
- Title: extension/UI admission wiring audit
- Pass type: verification-first checkpoint with evidence hardening

## Exact Seam

Primary code surface:

- `apps/chrome-extension/options/core/settings/signals_methods.js`
- `apps/chrome-extension/options/core/settings/srs_profile_methods.js`
- `apps/chrome-extension/options/controllers/srs/planning_state.js`
- `apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `apps/chrome-extension/options/controllers/srs/actions/planning_state_resolver.js`
- `apps/chrome-extension/options/controllers/srs/actions/admission_preview_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions/rebalance_workflow.js`
- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions_controller.js`
- `apps/chrome-extension/options/core/helper/srs_set_methods.js`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_srs_settings_contract.py`
- `core/tests/dev/test_extension_srs_action_workflows.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/helper/test_helper_engine.py`
- `scripts/testing/srs_admission_preference_sanity.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`

## Explicitly Out Of Scope

This slice does not directly review:

- helper mutation semantics beyond preview/rebalance entrypoint behavior already pinned in D4
- due-aware runtime serving
- runtime diagnostics rendering details
- broader share/import/profile-management UI behavior
- the preventive `actions/workflows.js` maintenance split tracked separately in `F14`

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- this seam crosses saved settings, current-form overrides, controller dispatch, helper transport, and native-host routing
- the most dangerous failure mode is a quiet mismatch where the options UI appears to edit preferences while helper preview/rebalance still runs on stale saved state
- evidence quality also mattered here because docs were already citing a Node-backed workflow test that had not yet been committed into the tree

## Contract Sketch

The intended current extension/UI wiring contract is:

1. `profile_runtime_controller.js` owns persisted options edits for the small UI-owned admission subset:
   - topic interests
   - proficiency estimate
   - challenge target
2. signal persistence remains narrow:
   - only the edited top-level families are rewritten
   - unedited sibling keys inside `proficiency` and `difficultyPreferences` are preserved
   - unrelated signal families remain in `srsSignalsByPair`
3. `planning_state.js` resolves current-form values into an effective profile plus effective signals and emits:
   - normalized `profileContext`
   - `contextMeta.source`
   - `contextMeta.pendingOverrides`
4. `planning_state_resolver.js` prefers current-form planning state when available and otherwise falls back to the saved-profile context builder
5. `admission_preview_workflow.js` and `rebalance_workflow.js` pass normalized `profileContext` through helper-manager calls with explicit triggers
6. preview remains non-mutating; rebalance mutates only on explicit apply
7. `srs_set_methods.js` preserves `profile_context` through the extension-to-helper/native-host boundary
8. preview/rebalance routing remains additive to the older semantic helper surface, not a replacement for it

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Options save only rewrites the current UI-owned admission subset and preserves nested sibling keys. | `profile_runtime_controller.js`, settings methods | `core/tests/dev/test_extension_srs_settings_contract.py` | `verified for this slice` |
| Unsaved form overrides are normalized into effective profile/signals/profile-context state. | `planning_state.js` | `core/tests/dev/test_extension_srs_action_workflows.py` | `verified for this slice` |
| Admission preview forwards normalized sizing plus `profileContext` without mutating stored state. | `admission_preview_workflow.js`, helper preview entrypoint | `core/tests/dev/test_extension_srs_action_workflows.py`, helper preview tests | `verified for this slice` |
| Rebalance preview/apply forwards normalized `profileContext` and only mutates on explicit apply. | `rebalance_workflow.js`, helper rebalance entrypoints | `core/tests/dev/test_extension_srs_action_workflows.py`, helper rebalance tests | `verified for this slice` |
| Extension/helper/native-host routing still preserves preview/rebalance transport separately from semantic helper flows. | `srs_set_methods.js`, native host, helper CLI | `core/tests/dev/test_helper_translation_dict_entrypoints.py` | `verified for this slice` |
| Preference-biased profile context still produces expected admission reranking signals. | profile bootstrap preference logic | `scripts/testing/srs_admission_preference_sanity.py` | `verified for this slice` |
| Semantic publication/runtime protections remain intact while the extension wiring is audited. | D1 Phase 0 protected suite | semantic baseline rerun during D8 validation | `verified for this slice` |
| The workflow test cited by the runbook now exists as committed evidence instead of a doc-only claim. | `core/tests/dev/test_extension_srs_action_workflows.py` | this D8 checkpoint | `fixed in this slice` |

## Invariants

1. saved settings and current-form planning state must not silently diverge
2. preview must stay non-mutating even when it uses current-form overrides
3. rebalance preview and rebalance apply must carry the same normalized planning context
4. helper/native-host transport must preserve `profile_context` fields without renaming drift
5. options save must preserve nested siblings and unrelated signal families
6. extension admission wiring must remain additive to the current semantic runtime contract

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Saved profile only | workflows fall back to saved-profile planning context |
| Unsaved form overrides | preview/rebalance uses current-form values and reports pending overrides |
| Narrow save | only the UI-owned signal subset is rewritten; sibling keys remain |
| Preview path | helper receives normalized `profileContext` and no mutation occurs |
| Rebalance preview/apply | plan and apply both use the same normalized context, with mutation only on apply |
| Native-host routing | extension transport still exposes preview/rebalance commands distinctly |
| Preference sanity | explicit/implicit topic signals still affect reranking as expected |

## Validation Floor

- `node --check apps/chrome-extension/options/controllers/srs/planning_state.js`
- `node --check apps/chrome-extension/options/controllers/srs/profile_runtime_controller.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions/planning_state_resolver.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions/admission_preview_workflow.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions/rebalance_workflow.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions_controller.js`
- `node --check apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `PYTHONPATH=core python3 -m pytest core/tests/dev/test_extension_srs_settings_contract.py core/tests/dev/test_extension_srs_action_workflows.py core/tests/dev/test_helper_translation_dict_entrypoints.py core/tests/architecture/test_extension_structure.py core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py -q`
- `python3 -m pytest core/tests/helper/test_helper_engine.py::TestHelperEnginePreviewSrsAdmission core/tests/helper/test_helper_engine.py::TestHelperEngineRebalanceSrsSet -q`
- `python3 scripts/testing/srs_admission_preference_sanity.py --json-out docs/test_outputs/srs_admission_preference_sanity_latest.json --markdown-out docs/test_outputs/srs_admission_preference_sanity_latest.md`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify that extension settings persistence, current-form planning state, and helper dispatch all still agree on the same admission subset and `profile_context`
2. convert the runbook’s earlier Node-backed workflow claim into committed executable evidence
3. leave the broader workflow-module preventive split to the already-tracked future slice

## Outcome

Result:

- options save still rewrites only the UI-owned admission subset while preserving nested sibling keys and unrelated signal families
- planning-state resolution still turns unsaved form values into normalized `profileContext` plus explicit pending-override metadata
- admission preview and rebalance workflows still forward normalized `profileContext` and expected triggers into helper calls
- helper preview/rebalance entrypoints and native-host routing reran green, so the extension-side contract still lands on the additive D4 helper surface
- the extension/controller validation bundle reran green (`32 passed`)
- targeted helper preview/rebalance tests reran green (`5 passed`)
- the admission preference sanity harness reran green (`status=PASS`, `pass_count=6`)
- the previous doc-only evidence gap is closed by committing `core/tests/dev/test_extension_srs_action_workflows.py`, so the Phase 5 validation note is now backed by real in-tree coverage instead of only chat/history state
