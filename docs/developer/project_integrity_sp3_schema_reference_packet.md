# SP3 Schema-Reference Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted semantic helper/runtime seam tests plus schema/doc reference checks
Purpose: close the remaining `SP3` semantic contract wording drift so shipped pointer, inventory, and helper/runtime batch schemas are described as current implementation seams instead of planning-only placeholders
Source-of-truth: packet only; executable truth still lives in semantic publication/runtime code, tests, and the current semantic contract docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_sp3_fallback_gating_packet.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_data_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../reference/schema.md`
- `../test_inputs/semantic_routing/README.md`

## Slice

- Track: `SP3`
- Slice: schema-reference reconciliation
- Title: semantic contract current-truth wording
- Pass type: verification-first doc/state reconciliation

## Exact Seam

Primary doc/schema surface:

- `docs/test_inputs/semantic_routing/semantic_admission.schema.json`
- `docs/test_inputs/semantic_routing/semantic_inventory.schema.json`
- `docs/test_inputs/semantic_routing/semantic_admit_batch_request.schema.json`
- `docs/test_inputs/semantic_routing/semantic_admit_batch_response.schema.json`
- `docs/test_inputs/semantic_routing/README.md`
- `docs/reference/schema.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`

Evidence surface:

- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`

## Explicitly Out Of Scope

This slice does not directly review:

- new semantic runtime logic or publication fields
- broader LP parity or rollout-readiness claims
- research-only schemas such as LLM intake, evidence batches, or local overrides
- semantic research-doc evidence routing outside the current schema-reference cluster

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `medium`

Reasoning:

- the defect was documentation-only, but it touched the canonical schema references that future runtime and UX work will consult first
- contradictory planning-vs-shipped wording weakens confidence in the actual seam and encourages duplicate reinvestigation

## Contract Sketch

The current semantic schema-reference contract is:

1. `semantic_admission.schema.json` describes the shipped emitted-rule pointer shape
2. `semantic_inventory.schema.json` describes the shipped helper sidecar publication shape
3. `semantic_admit_batch_request.schema.json` and `semantic_admit_batch_response.schema.json` describe the shipped helper/runtime batch seam used by the browser extension semantic-admission path
4. broader rollout breadth, LP parity, and research-only evidence lanes remain future-facing, but those are separate questions from whether these schema references are current

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Rule metadata can currently emit `semantic_admission` pointers. | semantic publication code, schema/reference docs | semantic publication tests, ruleset schema doc | `verified for this slice` |
| Helper publication currently writes semantic inventory sidecars. | helper publication/runtime diagnostics code | helper publication tests, publication contract docs | `verified for this slice` |
| Helper/native-host and browser runtime currently use `semantic_admit_batch`. | helper semantic admission entrypoint, native-host routing, semantic gate runtime | helper engine test, native-host entrypoint test, runtime gate contract test | `verified for this slice` |
| Schema reference docs should describe those seams as current, not planning-only. | schema JSON descriptions plus contract docs | this doc pass, doc reference check, current-truth runtime/publication docs | `fixed in this slice` |

## Invariants

1. shipped semantic schema references must not be labeled planning-only
2. current-vs-future language must distinguish between payload shape already in use and rollout breadth still not ready
3. semantic contract docs should agree with `feature_state_matrix.md` and the shipped helper/runtime tests

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Reader checks schema JSON descriptions directly | descriptions say current schema reference for shipped seams |
| Reader starts from semantic schema README | shipped vs planning surfaces are separated explicitly |
| Reader starts from semantic contract docs | publication, data, and runtime docs all point to the same current schema status |
| Reader checks state ledger against contract docs | no present-tense contradiction remains for pointer/inventory/batch schema status |

## Validation Floor

- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_helper_engine.py::TestHelperEngineSemanticInventoryLoad core/tests/dev/test_helper_translation_dict_entrypoints.py core/tests/dev/test_extension_semantic_gate_runtime_contract.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`
- `git diff --check --cached`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. identify every semantic schema/reference surface still using planning-only wording for shipped seams
2. update those schema descriptions and contract docs to current-truth language
3. keep future-facing rollout and research surfaces explicit so the fix does not overstate readiness
4. resolve the carry-forward note once the wording drift is gone

## Outcome

Result:

- shipped pointer, inventory, and helper/runtime batch schemas now read as current schema references
- semantic publication/data/runtime docs now distinguish implemented payload shape from still-future rollout breadth
- the semantic schema README now explicitly separates shipped seams from planning/research schemas
- the earlier SP3 holdout note is resolved instead of left as another rediscovery trap
