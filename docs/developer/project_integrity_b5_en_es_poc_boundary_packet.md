# B5 en-es Publication PoC Boundary Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 targeted semantic publication/runtime pytest suite, doc/state checks, and staged repo-safety gate
Purpose: bound the `B5` slice so the current `en-es` `status=ready` publication is described as a batch-local emitted-sibling PoC rather than broad shadow-mined runtime readiness
Source-of-truth: packet only; executable truth still lives in semantic publication/runtime code, tests, and the current semantic contract docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `feature_state_matrix.md`
- `../reference/schema.md`
- `../rulegen/semantic_routing_data_contract.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_implementation_roadmap.md`
- `../rulegen/semantic_routing_en_es_publish_checklist.md`

## Slice

- Track: `Wave B`
- Slice: `B5`
- Title: `en-es` publication PoC boundary cleanup
- Pass type: doc-contract tightening with boundary verification

## Exact Seam

Primary doc surface:

- `docs/reference/schema.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
- `docs/developer/feature_state_matrix.md`

Primary tests/evidence surface:

- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- other-LP parity sizing or rollout estimates
- new mined blocker publication logic
- phrase-preemption publication
- default-on semantic runtime rollout
- chat/plugin semantic runtime readiness

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- the implementation boundary is subtle because `status=ready` now exists in one real path, but only in a narrow publication family
- if docs overstate what `en-es` proves today, later cleanup can accidentally treat the PoC as evidence for broader shadow publication or multi-LP readiness
- this slice is mostly documentation, but it protects future product and UX work from inheriting the wrong launch boundary

## Contract Sketch

The intended current boundary is:

1. all current active rulegen LPs can emit stable semantic-admission pointer ids, but only `en-es` currently reaches `status=ready`
2. current `en-es` `status=ready` promotion is limited to sibling senses already present in the same emitted batch
3. the resulting published `competition_sets` are a batch-local emitted-sibling PoC, not broad mined blocker inventory
4. broader shadow-mined blocker publication remains a separate evidence and generalization track, even for `en-es`
5. the current `en-es` PoC must not be described as LP-parity readiness or as end-to-end default runtime readiness

## Claim-To-Evidence Map

| Claim | Owning docs/tests | Evidence surface | Current status |
|---|---|---|---|
| Current schema/docs still allow stable semantic-admission pointers across LPs while keeping `status=ready` narrow. | schema + semantic contract docs | doc audit in this slice | `verified for this slice` |
| Current `en-es` `status=ready` publication is batch-local emitted-sibling behavior, not broad mined blocker publication. | publication/runtime/checklist docs | doc audit plus publication/runtime suite | `verified for this slice` |
| Helper/runtime protections still assume limited ready coverage rather than broad shadow readiness. | semantic publication/runtime tests | targeted pytest bundle | `verified for this slice` |
| Future parity and broader shadow publication remain separate work rather than being silently implied by the PoC. | roadmap + feature-state matrix | doc audit in this slice | `verified for this slice` |

## Invariants

1. every current-truth doc that mentions `en-es` `status=ready` should identify it as the batch-local emitted-sibling PoC
2. no current-truth doc should equate that PoC with broad shadow-mined blocker publication
3. no current-truth doc should use the PoC as evidence of LP parity
4. the launch boundary remains helper-local and semantic-gate default-off

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Reader checks the schema | sees that `status=ready` exists for `en-es` only as a narrow batch-local PoC |
| Reader checks LP strength | sees that `en-es` has the strongest current pointer, but not broad runtime-ready publication |
| Reader checks runtime readiness | sees that published readiness is narrower than true mined shadow promotion |
| Reader checks rollout roadmap | sees that batch-local `en-es` launch is separate from broad blocker publication and other-LP parity |

## Validation Floor

- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `npm --prefix scripts run check:state`
- `git diff --check --cached`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. normalize the current-truth wording around the `en-es` `status=ready` PoC
2. make the negative boundary explicit: not broad shadow-mined blocker publication, not phrase-preemption publication, not LP parity
3. checkpoint the slice in a packet so later semantic cleanup has a durable claim boundary

## Outcome

Result:

- current-truth docs now describe the `en-es` `status=ready` subset consistently as a batch-local emitted-sibling PoC
- the docs now state more explicitly that this PoC is not broad shadow-mined blocker publication and not LP-parity readiness
- the semantic publication/runtime protection suite reran so the wording cleanup stayed grounded in current executable behavior
