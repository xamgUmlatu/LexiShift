# SP6 Semantic Evidence Routing Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 semantic readiness doc cleanup plus doc-safety checks
Purpose: bound the next SP6 slice around generated-evidence reference hygiene so semantic readiness prose summarizes the meaning of the current research outputs without treating artifact filenames as architecture truth
Source-of-truth: packet only; semantic runtime truth still lives in code, tests, `feature_state_matrix.md`, and the semantic research/runbook docs routed here
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_shadow_testing_architecture.md`
- `../rulegen/semantic_routing_implementation_roadmap.md`
- `feature_state_matrix.md`
- `project_integrity_sp3_schema_reference_packet.md`

## Slice

- Track: `SP6`
- Slice: generated-evidence references that need narrower wording
- Title: semantic readiness evidence routing
- Pass type: doc-routing correction

## Exact Seam

Primary contract/docs surface:

- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

Supporting evidence surface:

- `docs/developer/feature_state_matrix.md`
- `docs/rulegen/semantic_routing_implementation_roadmap.md`
- current semantic-shadow / sentence-veto artifacts under `docs/test_outputs/`

## Explicitly Out Of Scope

This slice does not directly review:

- the numeric correctness of the semantic-shadow results
- broader cleanup of every semantic planning or testing doc
- feature-state ledger wording
- evidence-artifact normalization or JSON churn

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `medium`

Reasoning:

- the runtime-readiness doc is a mixed authority surface, so inline artifact filenames inside argument prose can make generated outputs feel more canonical than they are
- the risk is not loss of evidence, but readers reconstructing product truth from whichever latest artifact path they notice first

## Contract Sketch

The intended current SP6 evidence-routing contract is:

1. readiness docs should summarize what current evidence means
2. research runbooks should own the detailed artifact filename inventory and experiment workflow
3. generated outputs can still support the argument, but file paths should not do the argumentative work inside architecture/readiness prose

## Claim-To-Evidence Map

| Claim | Owning docs/evidence | Evidence surface | Current status |
|---|---|---|---|
| `semantic_routing_runtime_readiness.md` is the mixed readiness boundary doc, not the artifact index for every current semantic experiment. | readiness doc routing plus document map | direct doc inspection | `verified before this slice` |
| `semantic_shadow_testing_architecture.md` is already the right authority for detailed artifact filenames and workflow lanes. | testing-architecture routing note and primary-file sections | direct doc inspection | `verified before this slice` |
| The problematic drift was inline readiness prose that named many `docs/test_outputs/...` files directly instead of routing readers back to the testing-architecture surface. | readiness doc section audit | direct doc inspection | `verified before this slice` |
| The readiness conclusions can remain intact after removing inline filename-level argument weight. | readiness doc edit | direct doc correction in this slice | `fixed in this slice` |

## Invariants

1. keep the readiness conclusions unchanged unless the evidence meaning itself is wrong
2. preserve artifact discoverability, but route filename authority to the research/runbook surface
3. do not turn this cleanup into a semantic-results rewrite

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Reader wants shipped runtime truth | readiness doc still gives the same current boundary without making filenames part of the argument |
| Reader wants exact current artifact paths | readiness doc routes them to `semantic_shadow_testing_architecture.md` |
| Reader compares semantic planning/readiness docs | contract, roadmap, and testing docs now have cleaner role separation |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. keep the cleanup to the readiness doc instead of rewriting multiple semantic docs at once
2. replace inline artifact-path narration with summary wording
3. add one explicit routing line back to the testing-architecture doc
4. resolve `N-017` if the readiness-vs-artifact authority split is now explicit enough

## Outcome

Result:

- semantic readiness prose now summarizes what the current mining and promotion evidence means instead of reading like a rolling artifact directory
- the detailed filename inventory remains available in the testing-architecture doc, which is the right operational authority for that layer
- this reduces the chance that readers mistake the latest generated output path for the architecture claim itself
