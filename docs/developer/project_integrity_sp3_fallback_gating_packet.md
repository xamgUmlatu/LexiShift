# SP3 Fallback/Gating Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-20
Last verified: 2026-04-20 targeted helper/runtime gate contract tests, semantic helper/runtime suite rerun, and doc/state hygiene checks
Purpose: bound the second `SP3` slice so the shipped semantic-admission gate stays explicit about which matches are merely eligible, which are actually helper-scored, and how malformed or unavailable helper paths fail
Source-of-truth: packet only; executable truth still lives in the browser runtime, helper batch entrypoint, tests, and the current semantic runtime docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `project_integrity_sp3_publication_family_packet.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_data_contract.md`

## Slice

- Track: `SP3`
- Slice: fallback and eligible-match gating
- Title: semantic gate readiness boundary
- Pass type: verification-first slice with narrow contract hardening

## Exact Seam

Primary code surface:

- `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `core/lexishift_core/helper/use_cases/semantic_admission.py`

Primary tests/evidence surface:

- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/helper/test_rulegen_outputs.py`

## Explicitly Out Of Scope

This slice does not directly review:

- broader semantic publication/schema wording cleanup across all research docs
- new decision-policy heuristics or semantic-shadow promotion rules
- soft-affordance DOM UX beyond the current keep-original behavior
- broader helper-cache lifecycle or manifest-family drift, already covered by the earlier SP3 packet

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- the semantic gate sits on the helper/runtime boundary and quietly controls whether replacements survive to the DOM
- the current design intentionally distinguishes `eligible` from `ready`, which is easy to flatten incorrectly in docs or future refactors
- malformed batch payload filtering would have hidden caller mistakes by degrading silently instead of failing loudly

## Contract Sketch

The intended current runtime contract is:

1. only SRS-origin matches that already carry `metadata.semantic_admission` are semantically eligible
2. eligibility is broader than helper scoring readiness
3. non-ready eligible matches resolve locally through the configured fallback policy and never call helper scoring
4. only ready eligible matches are grouped by `pair` + `profile_id` and sent to helper `semantic_admit_batch`
5. if semantic inventory or helper transport is unavailable, even ready matches fall back locally
6. helper `semantic_admit_batch` should treat malformed `matches` payloads as request errors, not partial-success batches

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| The browser runtime counts eligible matches separately from ready matches. | `semantic_gate_runtime.js`, runtime diagnostics wiring | new runtime gate contract test, runtime-readiness doc, diagnostics contract test | `verified for this slice` |
| Only ready matches are sent to helper `semantic_admit_batch`. | `semantic_gate_runtime.js` | new runtime gate contract test, runtime-readiness doc | `verified for this slice` |
| Inventory/service failure for ready matches resolves locally through fallback policy. | `semantic_gate_runtime.js`, helper runtime bridge | new runtime gate contract test, helper/runtime policy suite | `verified for this slice` |
| Helper batch entrypoint should reject malformed mixed-item payloads instead of silently dropping bad rows. | `helper/use_cases/semantic_admission.py`, helper engine tests | new helper engine regression test | `fixed in this slice` |
| Current-truth docs should say that only ready eligible matches are batched. | `feature_state_matrix.md`, runtime-readiness docs | doc wording update plus state check | `fixed in this slice` |

## Invariants

1. `eligible` and `ready` are not interchangeable counters
2. a non-ready eligible match must never consume helper scoring
3. ready matches may still fall back locally when inventory or helper transport is unavailable
4. runtime keeps only `decision=replace` matches in the shipped DOM path
5. helper batch requests must fail loudly on malformed item shapes rather than silently changing batch cardinality

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Eligible + ready SRS match | helper request happens once, policy decision is applied, counters record both `eligible` and `ready` |
| Eligible but non-ready SRS match | no helper request for that row, fallback decision is created locally, row counts as `eligible` but not `ready` |
| Ready match with inventory unavailable | no helper batch call, fallback decision is created locally, default legacy fallback preserves replacement behavior |
| Ruleset-origin or no-pointer match | semantic gate ignores the row entirely |
| Malformed helper request payload | helper entrypoint rejects the request instead of silently dropping invalid rows |

## Validation Floor

- `python3 -m pytest core/tests/dev/test_extension_semantic_gate_runtime_contract.py core/tests/helper/test_helper_engine.py::TestHelperEngineSemanticInventoryLoad core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 -m pytest core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`
- `git diff --check --cached`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. confirm the shipped runtime actually separates eligibility from helper-scoring readiness
2. add a direct runtime contract test for ready-only batching and local fallback on inventory failure
3. harden the helper batch entrypoint so malformed mixed-item payloads do not degrade silently
4. tighten current-truth docs so the batched-vs-eligible distinction stays explicit

## Outcome

Result:

- the shipped runtime contract is now directly tested at the JS seam instead of being inferred only from prose and indirect diagnostics coverage
- docs now say plainly that eligibility is counted broadly, while only ready eligible matches are batched to helper scoring
- helper `semantic_admit_batch` now rejects malformed mixed-item payloads instead of silently dropping invalid rows
- one broader wording holdout remains outside this slice and was logged in `project_integrity_secondary_pass_notes.md`: the standalone semantic batch schema/data-contract docs still carry older planning-oriented wording even though the helper/runtime seam is now shipped
