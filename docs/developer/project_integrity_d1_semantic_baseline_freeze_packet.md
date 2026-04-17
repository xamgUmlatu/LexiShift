# D1 Semantic Baseline Freeze Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 protected-file audit plus Phase 0 semantic baseline suite refresh
Purpose: bound the D1 slice around the Phase 0 semantic baseline freeze so later admission-port work can move without accidentally redefining the current semantic publication/runtime base
Source-of-truth: packet only; executable truth still lives in code, tests, semantic-routing docs/schemas, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`

## Slice

- Track: `Wave D`
- Slice: `D1`
- Title: phase-0 semantic baseline freeze refresh
- Pass type: verification-only checkpoint with protected-base reconfirmation

## Exact Seam

Primary protected code surface:

- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/use_cases/semantic_admission.py`

Primary protected doc/schema surface:

- `docs/rulegen/semantic_routing_*`
- `docs/test_inputs/semantic_routing/*`

Primary tests/evidence surface:

- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- due-aware serving semantics
- helper-rule runtime confidence gating
- admission-core scoring or profile-bootstrap quality
- inventory wiring, rebalance behavior, or extension workflow edits beyond confirming they do not displace the semantic base

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- the protected semantic base is now a dependency for every later admission selective-port slice
- if that base drifts silently, later D-phase work can appear locally correct while regressing semantic publication/runtime guarantees
- the risk is more about unnoticed contract erosion than about an obvious crash

## Contract Sketch

The intended current Phase 0 semantic baseline contract is:

1. helper publication still owns one semantic publication family:
   - ruleset
   - snapshot
   - optional semantic inventory
   - publication manifest
2. snapshot and semantic inventory remain generation-aligned through shared `generation_id`
3. helper/native-host still exposes `semantic_admit_batch`
4. browser semantic runtime remains opt-in and default-off
5. only after that base is reconfirmed should later admission slices port inventory, preview, rebalance, or initialize/refresh changes around it

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Protected semantic base files remain the current branch source of truth for publication/runtime semantics. | `helper/rulegen_outputs.py`, `helper/use_cases/semantic_admission.py`, semantic-routing docs/schemas | protected-file worktree audit plus selective-port docs | `verified for this slice` |
| Helper publication still enforces generation-aligned artifact-family validation. | `helper/rulegen_outputs.py` | `core/tests/helper/test_rulegen_outputs.py`, `core/tests/rulegen/test_semantic_publication.py`, publication-contract docs | `verified for this slice` |
| Helper/native-host still preserves the separate `semantic_admit_batch` seam. | `helper/use_cases/semantic_admission.py`, helper engine/native host routing | `core/tests/dev/test_helper_translation_dict_entrypoints.py`, runtime-readiness docs | `verified for this slice` |
| Browser semantic runtime base remains structurally present and default-off. | extension runtime structure + readiness docs | `core/tests/architecture/test_extension_structure.py`, `core/tests/rulegen/test_semantic_routing_runtime_policy.py`, `feature_state_matrix.md` | `verified for this slice` |
| Phase 0 gate definition itself has not drifted since the prior freeze note. | selective-port runbook and current test suite | fresh Phase 0 suite rerun | `verified for this slice` |

## Invariants

1. do not replace the current semantic publication family with admission-port variants
2. do not remove manifest or `generation_id` alignment from helper publication
3. do not collapse `semantic_admit_batch` into broader admission helper flows
4. do not treat later Wave C caveats as reasons to weaken the semantic baseline statement
5. later D-phase ports should build around this base rather than restating it from memory

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Protected-file audit | protected semantic files are not currently displaced by newer admission edits |
| Publication-family baseline | ruleset/snapshot/semantic-inventory/manifest contract still validates |
| Runtime-policy baseline | semantic runtime policy tests still reflect default-off + conservative fallback behavior |
| Native-host baseline | `semantic_admit_batch` still routes separately from newer admission preview/rebalance actions |
| Docs/runbook checkpoint | selective-port Phase 0 note still matches current executable reality |

## Validation Floor

- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. audit the protected semantic file set and schemas for drift
2. rerun the full Phase 0 semantic baseline gate
3. refresh the selective-port Phase 0 checkpoint note so the next admission slices start from an explicit, dated base

## Outcome

Result:

- the protected semantic base files remain untouched in the current worktree
- the protected semantic doc/schema family remains intact
- the Phase 0 semantic baseline suite still matches the earlier gate and reran green on `2026-04-18` (`27 passed`)
- no behavior change was needed for D1
- the value of this slice is a fresh protected-base checkpoint before D3+ admission-port work continues
