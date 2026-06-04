# G2 Evidence Wording Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 doc-ahead-of-evidence audit plus doc-safety checks
Purpose: close the remaining `N-007` evidence-hygiene tail by reclassifying older inspection-only checkpoint rows that still read as executable verification
Source-of-truth: packet only; executable truth still lives in code, tests, harness artifacts, and the canonical docs they support
Related docs:
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `documentation_governance.md`

## Slice

- Track: `G2`
- Slice: `G2.1`
- Title: inspection-only checkpoint row reclassification
- Pass type: evidence-wording hygiene only

## Exact Seam

Primary docs surface:

- `docs/developer/project_integrity_b6_semantic_roadmap_pruning_packet.md`
- `docs/developer/project_integrity_b5_en_es_poc_boundary_packet.md`
- `docs/developer/project_integrity_b4_semantic_diagnostics_packet.md`
- `docs/developer/project_integrity_d1_semantic_baseline_freeze_packet.md`

Primary notes surface:

- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether the underlying product behavior is correct
- whether additional executable tests should exist for those seams
- broader generated-artifact routing, already handled separately in `SP6`
- any current-truth row in `feature_state_matrix.md`

## Contract Sketch

The intended contract for checkpoint wording is:

1. executable claims supported by tests, harnesses, or direct runtime artifacts can stay `verified for this slice`
2. rows supported only by doc audit, code inspection, worktree audit, or notes routing should be marked as clarification rather than executable verification
3. a packet can mix verified and clarified rows as long as the evidence surface is explicit row by row

## Claim-To-Evidence Map

| Claim | Owning packet rows | Evidence surface | Current status after this slice |
|---|---|---|---|
| Semantic doc-ownership/routing rows should not read like executable proof. | `B6`, `B5` doc-audit rows | packet wording audit | `clarified in this slice` |
| Architecture-boundary claims based on code/doc inspection should stay explicit about that lower evidence floor. | `B4` helper-authority row | packet wording audit | `clarified in this slice` |
| Freeze-note branch-authority claims based on protected-file audit should not be labeled as runtime verification. | `D1` source-of-truth row | packet wording audit | `clarified in this slice` |

## Invariants

1. a present-tense claim should not be labeled `verified` when its cited evidence is only inspection or doc audit
2. reclassifying evidence wording must not imply a behavior change
3. executable and non-executable evidence can coexist in one packet, but the row labels must distinguish them

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:changed:staged`

## Outcome

Result:

- inspection-only rows in the targeted older packets now use `clarified in this slice` instead of `verified for this slice`
- executable rows in those packets were left unchanged
- `N-007` is now closed as a wording/authority-hygiene result rather than as a new product-behavior review
