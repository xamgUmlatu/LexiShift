# SP3 Publication-Family Coherence Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-20
Last verified: 2026-04-20 targeted helper diagnostics drift tests, semantic publication/runtime protection rerun, doc/state checks, and staged repo-safety gate
Purpose: bound the first `SP3` slice so helper semantic diagnostics reports the current publication family honestly instead of trusting only the manifest's stored validation bit
Source-of-truth: packet only; executable truth still lives in helper publication/reset/diagnostics code, tests, and the current semantic publication/runtime docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `project_integrity_d7_runtime_diagnostics_packet.md`

## Slice

- Track: `SP3`
- Slice: publication-family coherence
- Title: helper manifest drift revalidation
- Pass type: verification-first slice with one narrow observability fix

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`

Primary tests/evidence surface:

- `core/tests/helper/test_helper_engine.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- extension cache/runtime diagnostics rendering
- semantic fallback decision behavior
- new semantic publication fields or manifest schema expansion
- broader shadow-mined blocker publication

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `high`
- priority: `high`

Reasoning:

- helper diagnostics is the only shipped surface that claims authority for semantic publication-family coherence
- before this slice, a snapshot/semantic-inventory generation drift could still report `publication_manifest_family_valid=true` because diagnostics only echoed the stored manifest validation bit
- that is exactly the kind of quiet false-green state the secondary pass is supposed to catch

## Contract Sketch

The intended current publication-family diagnostics contract is:

1. helper publication writes a manifest for one ruleset/snapshot/semantic-inventory family
2. helper diagnostics reports the current live state of that family
3. manifest-family validity must therefore reflect current artifact coherence, not only what was true when the manifest was written
4. extension cache/runtime diagnostics may stay best-effort and aggregate, but helper diagnostics should be the authoritative current-family view

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper publication still writes one shared `generation_id` across snapshot, semantic inventory, and manifest. | `helper/rulegen_outputs.py`, publication tests | `core/tests/helper/test_rulegen_outputs.py`, semantic publication suite | `verified for this slice` |
| Reset still removes semantic inventories and publication manifests with the pair/profile family. | `helper/use_cases/reset.py`, helper reset tests | `core/tests/helper/test_helper_engine.py` | `verified for this slice` |
| Helper diagnostics now recomputes current manifest-family validity against live artifacts instead of only echoing manifest validation. | `helper/use_cases/runtime_diagnostics.py`, new drift test | `core/tests/helper/test_helper_engine.py` | `fixed in this slice` |
| Current semantic publication/runtime protections remain intact while diagnostics authority is tightened. | semantic publication/runtime suites | `core/tests/rulegen/test_semantic_publication.py`, `core/tests/rulegen/test_semantic_routing_runtime_policy.py`, helper entrypoint tests | `verified for this slice` |

## Invariants

1. helper diagnostics must not report a healthy publication family when live helper artifacts already drifted
2. manifest-family validity should depend on current artifact existence plus current generation/checksum coherence
3. reset must continue to remove the manifest family it claims to delete
4. the fix should improve observability without changing semantic runtime default behavior

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Fresh valid publication family | helper diagnostics reports matching generation ids and `publication_manifest_family_valid=true` |
| Live generation drift after publication | helper diagnostics reports `publication_manifest_family_valid=false` and exposes the mismatch in `publication_manifest_errors` |
| Store-fallback inventory path with valid semantic family | diagnostics still reports inventory fallback separately from semantic publication coherence |
| Reset of pair/profile family | semantic inventory and manifest disappear together |

## Validation Floor

- `PYTHONPATH=core python3 -m pytest core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics -q`
- `python3 -m pytest core/tests/helper/test_rulegen_outputs.py core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`
- `git diff --check --cached`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. confirm whether helper diagnostics can false-green a drifted publication family
2. make helper diagnostics recompute current family validity from the live files
3. add a direct regression test for generation drift
4. tighten current-truth docs so the authority claim matches the code

## Outcome

Result:

- helper diagnostics no longer trusts only the manifest's stored `family_valid` bit
- it now recomputes publication-family validity against the live ruleset/snapshot/semantic-inventory files and surfaces drift through `publication_manifest_errors`
- a direct regression test now proves that snapshot/semantic-inventory generation drift flips the helper payload to `publication_manifest_family_valid=false`
- semantic publication/runtime protections stayed green while the diagnostics authority path was tightened
