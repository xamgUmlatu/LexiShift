# B6 Semantic Roadmap Pruning Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-19 doc-reference check, diff hygiene, and staged repo-safety gate
Purpose: bound the `B6` slice so semantic-routing planning docs have clearer ownership boundaries between current contract truth, near-term sequencing, launch operation, and research evaluation lanes
Source-of-truth: packet only; executable and canonical truth still lives in the semantic contract docs, `feature_state_matrix.md`, launch runbooks, and research-plan docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `../rulegen/semantic_routing_data_contract.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_implementation_roadmap.md`
- `../rulegen/semantic_routing_en_es_publish_checklist.md`
- `../rulegen/semantic_routing_generalization_evaluation_plan.md`
- `../rulegen/semantic_shadow_testing_architecture.md`

## Slice

- Track: `Wave B`
- Slice: `B6`
- Title: semantic roadmap pruning pass
- Pass type: doc-ownership tightening and overlap reduction

## Exact Seam

Primary doc surface:

- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md`
- `docs/rulegen/semantic_routing_generalization_evaluation_plan.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`

Secondary tracking surface:

- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- semantic publication or runtime code behavior
- new launch criteria or broader blocker-generation policy
- generated artifact accuracy or benchmark validity
- other-LP parity sizing

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `medium-high`

Reasoning:

- the semantic doc family had accumulated enough overlap that readers could reconstruct "current truth" by averaging multiple docs together
- that creates a quiet integrity risk even when each individual doc is locally reasonable
- pruning ownership is low-risk to implementation behavior, but high-value for future cleanup, UX work, and follow-on agents

## Contract Sketch

The intended semantic doc ownership after `B6` is:

1. data/publication contract docs own the current artifact and schema truth
2. runtime-readiness owns the shipped browser seam and the remaining readiness boundary
3. the implementation roadmap owns near-term phase ordering only
4. the `en-es` checklist owns the first controlled launch operation
5. generalization and semantic-shadow docs own research evaluation and harness workflow, not shipped or launch truth

## Claim-To-Evidence Map

| Claim | Owning docs | Evidence surface | Current status |
|---|---|---|---|
| Data contract now routes sequencing/launch questions away from itself. | `semantic_routing_data_contract.md` | doc audit in this slice | `clarified in this slice` |
| Publication contract now makes clear that launch operation belongs in the checklist. | `semantic_routing_publication_contract.md` | doc audit in this slice | `clarified in this slice` |
| Runtime-readiness now owns shipped seam + readiness floor, not step-by-step implementation sequencing. | `semantic_routing_runtime_readiness.md` | doc audit in this slice | `clarified in this slice` |
| Roadmap now owns phase order without re-documenting the full current checkpoint or launch runbook. | `semantic_routing_implementation_roadmap.md` | doc audit in this slice | `clarified in this slice` |
| A follow-up reminder now exists for broader evidence-path hygiene in semantic research docs. | `project_integrity_secondary_pass_notes.md` | notes ledger update | `captured for later` |

## Invariants

1. readers should not need to average multiple semantic docs to determine who owns current truth versus future plan
2. exact launch commands and fallback posture should live in the launch checklist, not the roadmap
3. sequencing should live in the roadmap, not in runtime-readiness
4. research evidence lanes should remain distinguishable from current shipped or launch-ready contract claims

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. tighten routing notes in the contract docs
2. prune duplicated sequencing prose from runtime-readiness
3. shrink the roadmap's repeated current-state and launch sections into ownership references plus a concise starting point
4. capture any adjacent reminder that should survive beyond this slice

## Outcome

Result:

- semantic doc ownership is now more explicit across current contract, roadmap, launch checklist, and research-plan documents
- runtime-readiness no longer doubles as an implementation plan
- the roadmap no longer restates the full current checkpoint or launch runbook
- one follow-up evidence-path reminder was captured in the secondary-pass notes for a later `G2` pass
