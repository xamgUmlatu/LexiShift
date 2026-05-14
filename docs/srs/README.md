# SRS Documentation Authority Map

Status: active SRS routing
Role: Canonical current
Last updated: 2026-05-15
Last verified: 2026-05-15 Lane 1 SRS supersession review against SRS docs, feature-state SRS entries, and doc-reference checks; SRS behavior and harness artifacts were not rerun
Purpose: route SRS cleanup work to the right current, mixed, planning, schema, or harness document without treating roadmap text as implementation truth
Source-of-truth: SRS documentation routing only; implementation truth lives in SRS/helper/extension code, tests, generated SRS artifacts, and `docs/developer/feature_state_matrix.md`.

## Use This First For SRS Doc Cleanup

The SRS folder intentionally contains mixed surfaces. Some docs describe current
runtime behavior. Some preserve target architecture. Some are planning notes for
future personalization and harness work.

Do not treat the roadmap, schema drafts, or planning notes as proof that a
behavior is implemented, default-on, or verified. Use the claim type below.

## Current Authority Order

| Claim Being Checked | Start Here | Role In Cleanup | Do Not Use It For |
| --- | --- | --- | --- |
| Implemented/default-on/verified SRS status | `docs/developer/feature_state_matrix.md` | Current status ledger for planner strategies, active inventory, due-aware serving, and helper-rule confidence gating. | Replacing code/test inspection. |
| LP capability contract for SRS | `docs/architecture/srs_lp_architecture.md` | Canonical LP/SRS architecture contract, centered on `lp_capabilities.py`. | Pair-specific tuning or roadmap status. |
| Current SRS roadmap and remaining work | `docs/srs/srs_roadmap.md` | Mixed current snapshot plus roadmap workstream tracker. | Claiming roadmap checkboxes are verified implementation without feature-state or test evidence. |
| SRS model semantics (`S`, due set, passive exposure, feedback) | `docs/srs/srs_hybrid_model_technical.md` | Mixed model reference for the adopted hybrid inventory/scheduling model. | Exact persisted schema truth when code/tests differ. |
| Runtime practice-layer boundary | `docs/srs/srs_practice_layer_design.md` | Mixed design reference for helper publication/runtime gating and due-only gaps. | Marking due-aware serving shipped end to end. |
| Persisted SRS settings/store/signal shape | `docs/srs/srs_schema.md` | Mixed schema reference separating implemented fields from planned extensions. | Assuming planned schema sections are already written by runtime. |
| Profile signal and request shapes | `docs/srs/srs_profile_schema.md` | Mixed schema reference for extension profile storage and helper `profile_context`. | Claiming profile strategies are default execution paths. |
| Set planning, sizing policy, and strategy behavior | `docs/srs/srs_set_planning_technical.md` | Mixed technical reference for planner modules, helper APIs, sizing clamps, and current strategy status. | Treating `profile_growth` as broad admission execution. |
| Selector and personalization algorithm ideas | `docs/srs/srs_selector_technical.md`, `docs/srs/srs_curriculum_notes.md` | Planning/WIP surfaces for future ranking and personalization. | Current product or runtime behavior claims. |
| SRS journey and synthetic quality harness work | `docs/srs/srs_journey_harness_workstream.md`, `scripts/testing/srs_quality_harness.py` | Harness planning plus executable quality-harness entrypoints. | Broad LP coverage claims beyond the harness-supported scenarios. |

## Supersession Decision

This review does not archive any SRS docs.

Current disposition:

- `srs_roadmap.md` remains the SRS workstream tracker, but status-sensitive
  claims must route through `feature_state_matrix.md`.
- `srs_schema.md` and `srs_profile_schema.md` remain active mixed schema
  references because they separate implemented shapes from planned extension
  fields.
- `srs_hybrid_model_technical.md`, `srs_practice_layer_design.md`, and
  `srs_set_planning_technical.md` remain mixed current-plus-target references.
- `srs_selector_technical.md` and `srs_curriculum_notes.md` remain planning
  surfaces only.
- `srs_journey_harness_workstream.md` remains a harness workstream, not the
  required default SRS quality gate.

## Current SRS Posture

For productization closure, preserve these boundaries unless a later verified
update changes the owning docs:

- default bootstrap execution remains `frequency_bootstrap`;
- `profile_bootstrap` has implemented scoring/diagnostics but is not the helper
  initialization default path;
- `profile_growth` is executable for rebalance preview/apply, not broad
  growth-admission into `S`;
- due-aware serving is still planned end to end: scheduler code can build due
  queues, but helper publication and extension gating still use the broader
  active/admitted inventory;
- helper-rule confidence gating at runtime remains planned;
- SRS harness coverage is useful but limited to the scenarios documented in the
  harness and feature-state entries.

## Safe Cleanup Sequence

When cleaning SRS docs during Lane 1:

1. classify the claim type with the table above,
2. migrate surviving current-truth text into the owning current or mixed doc
   before demoting older notes,
3. keep planned schema and roadmap sections visibly separate from implemented
   behavior,
4. update `docs/developer/feature_state_matrix.md` only when status, default
   behavior, evidence, or known gaps materially change,
5. run `python3 scripts/dev/check_doc_references.py`, `git diff --check`, and
   `npm --prefix scripts run check:state` if feature-state evidence or status
   paths change.
