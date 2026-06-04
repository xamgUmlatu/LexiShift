# D4 Helper Preview/Rebalance Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted helper preview/rebalance tests plus semantic Phase 0 baseline rerun
Purpose: bound the D4 slice around the additive helper preview/rebalance API surface so later initialize/refresh reconciliation and extension/UI wiring work can build on an explicit entrypoint contract
Source-of-truth: packet only; executable truth still lives in helper code, scripts, native-host routing, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D4`
- Title: admission preview/rebalance helper API
- Pass type: verification-first checkpoint with entrypoint-boundary clarification

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/engine.py`
- `core/lexishift_core/helper/use_cases/admission_preview.py`
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
- `scripts/helper/srs_admission_cli_support.py`
- `scripts/helper/lexishift_helper.py`
- `scripts/helper/lexishift_native_host.py`

Primary tests/evidence surface:

- `core/tests/helper/test_helper_engine.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/dev/test_srs_planner_strategy_contract.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- extension options/controller workflow wiring for preview/rebalance buttons
- initialize-set mutation semantics
- refresh/reset/runtime diagnostics reconciliation
- due-aware serving
- helper-rule runtime confidence gating
- any large helper-engine refactor beyond confirming the current wrapper boundary

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- this is the first externally reachable admission helper surface, so drift here changes what CLI/native-host callers can ask the system to do
- the biggest integrity risk is accidental overlap between the newer preview/rebalance surface and the older semantic helper surface
- failures can stay subtle because they often look like route or payload drift rather than obvious exceptions

## Contract Sketch

The intended current D4 helper-entrypoint contract is:

1. `engine.py` exposes admission preview, rebalance preview, and rebalance apply as thin wrappers around dedicated use cases
2. `admission_preview.py` remains a non-mutating planning/preview surface:
   - it can return planner-only payloads when the requested strategy is not executable
   - when `profile_bootstrap` is requested, helper planning still reports the current effective execution truth rather than pretending bootstrap execution changed wholesale
3. `rebalance_set.py` owns separate preview/apply flows:
   - preview reports inventory-aware rebalance decisions
   - apply can update explicit active inventory and republish the current semantic artifact family
4. CLI exposure remains additive and isolated in `srs_admission_cli_support.py`, with `lexishift_helper.py` registering those commands rather than folding them into unrelated helper plumbing
5. native-host routing exposes:
   - `srs_preview_admission`
   - `srs_rebalance_plan`
   - `srs_rebalance_apply`
   while preserving the separate `semantic_admit_batch` route
6. the extension/UI normalization layer for `profile_context` still belongs to the later D8/Phase 5 slice, not to this helper-entrypoint checkpoint

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper engine exports preview/rebalance as dedicated use-case wrappers rather than replacing broader helper behavior. | `helper/engine.py`, use-case modules | targeted helper-engine tests, direct code audit | `verified for this slice` |
| Admission preview remains non-mutating and still reports the current planner/execution truth for profile-aware bootstrap requests. | `helper/use_cases/admission_preview.py` | `core/tests/helper/test_helper_engine.py`, `core/tests/dev/test_srs_planner_strategy_contract.py` | `verified for this slice` |
| Rebalance preview/apply remain inventory-aware and preserve publication through the current semantic artifact family. | `helper/use_cases/rebalance_set.py` | `core/tests/helper/test_helper_engine.py`, `core/tests/dev/test_srs_planner_strategy_contract.py` | `verified for this slice` |
| CLI help and native-host routing expose the new entrypoints while keeping `semantic_admit_batch` separate. | `srs_admission_cli_support.py`, `lexishift_helper.py`, `lexishift_native_host.py` | `core/tests/dev/test_helper_translation_dict_entrypoints.py` | `verified for this slice` |
| Semantic publication/runtime protections remain intact while the helper surface is audited. | D1 Phase 0 protected suite | semantic baseline rerun during D4 validation | `verified for this slice` |

## Invariants

1. keep preview/rebalance entrypoints additive rather than folding them into the semantic helper seam
2. preserve `semantic_admit_batch` as a distinct native-host/helper route
3. do not confuse preview diagnostics with broader initialize/refresh execution changes
4. keep rebalance publication on the existing semantic artifact family
5. leave extension-side button/workflow normalization to the later D8 slice

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Preview-only helper call | non-mutating preview payload remains available with profile-bootstrap diagnostics |
| Planner-only fallback | non-executable strategy still returns plan-only preview output |
| Rebalance preview/apply | preview and apply stay distinct and inventory-aware |
| CLI registration/help | helper CLI lists the preview/rebalance commands and preview flags |
| Native-host routing | native host routes preview/rebalance separately while keeping `semantic_admit_batch` intact |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/helper/test_helper_engine.py::TestHelperEnginePreviewSrsAdmission core/tests/helper/test_helper_engine.py::TestHelperEngineRebalanceSrsSet core/tests/dev/test_helper_translation_dict_entrypoints.py core/tests/dev/test_srs_planner_strategy_contract.py -q`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify that helper engine, CLI, and native-host entrypoints all still expose the same preview/rebalance contract
2. confirm the semantic helper route remains separate rather than being absorbed into the new admission surface
3. refresh the selective-port Phase 3 note so later D-phase work starts from a dated helper-entrypoint checkpoint

## Outcome

Result:

- helper engine still exposes preview/rebalance through dedicated use-case wrappers instead of rewriting the broader helper surface
- CLI registration still runs through `srs_admission_cli_support.py`, and help output still exposes the preview/rebalance commands and preview-specific flags
- native-host routing still exposes `srs_preview_admission`, `srs_rebalance_plan`, and `srs_rebalance_apply` while preserving `semantic_admit_batch` as a separate request path
- preview remains a planning/diagnostics surface and rebalance remains the inventory-aware apply surface; neither result required a semantic helper contract rewrite
- the semantic Phase 0 suite reran green alongside this slice, so the D4 clarification still sits on top of the protected semantic base
