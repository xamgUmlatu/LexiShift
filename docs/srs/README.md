# SRS Documentation Authority Map

Status: active SRS routing
Role: Canonical current
Last updated: 2026-05-23
Last verified: 2026-05-23 browsing/admission lifecycle routing update plus doc-reference check
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
| Runtime practice-layer boundary | `docs/srs/srs_practice_layer_design.md` | Mixed design reference for helper publication/runtime gating and due-only publication gaps. | Claiming a due-only publication artifact exists. |
| Persisted SRS settings/store/signal shape | `docs/srs/srs_schema.md` | Mixed schema reference separating implemented fields from planned extensions. | Assuming planned schema sections are already written by runtime. |
| Profile signal and request shapes | `docs/srs/srs_profile_schema.md` | Mixed schema reference for extension profile storage and helper `profile_context`. | Claiming profile strategies are default execution paths. |
| Set planning, sizing policy, and strategy behavior | `docs/srs/srs_set_planning_technical.md` | Mixed technical reference for planner modules, helper APIs, sizing clamps, and current strategy status. | Treating `profile_growth` as broad admission execution. |
| Admission lifecycle and refresh mutation boundaries | `docs/srs/srs_admission_lifecycle_current_state.md` | Current code-backed audit for initial admission, refresh growth, rebalance, feedback/exposure caveats, and suppression guards. | Claiming discard/suspend UI or full mastered/released lifecycle exists. |
| Admitted-words dashboard and lifecycle UX policy | `docs/srs/srs_admitted_words_dashboard_plan.md` | Mixed product/implementation contract for the read-only admitted-words dashboard, advanced-details boundary, and deferred discard/restore controls. | Claiming destructive lifecycle actions are shipped. |
| Preference taxonomy lifecycle | `docs/srs/srs_preference_taxonomy_lifecycle.md` | Planning policy for adding topic/register preferences without damaging existing SRS progress. | Claiming a preference family is sourced, default-on, or broadly supported. |
| en-es topic coverage pause state | `docs/srs/srs_topic_coverage_pause_state_en_es.md` | Current closeout snapshot for the paused topic-coverage slice, including overlay stack, readiness status, and resume criteria. | Treating topic coverage as comprehensive or default product copy. |
| Browsing-based admission | `docs/srs/srs_browsing_based_admission_plan.md` | Planning workstream for opt-in, local-only browsing word signals that can influence future admission within SRS budget/lifecycle gates. | Claiming passive browsing changes scheduling, review state, or current default behavior. |
| Selector, personalization, and required data | `docs/srs/srs_selector_technical.md`, `docs/srs/srs_interest_tailored_admission_algorithm.md`, `docs/srs/srs_interest_tailored_data_acquisition_plan.md`, `docs/srs/srs_topic_signal_lp_generalization_runbook.md`, `docs/srs/srs_curriculum_notes.md` | Planning/WIP surfaces for future ranking, data acquisition, personalization, and reusable topic-signal onboarding lessons. | Current product or runtime behavior claims. |
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
- `srs_admission_lifecycle_current_state.md` is the current code-backed audit
  for admission mutation and lifecycle guard behavior.
- `srs_selector_technical.md`, `srs_interest_tailored_admission_algorithm.md`,
  `srs_interest_tailored_data_acquisition_plan.md`,
  `srs_topic_signal_lp_generalization_runbook.md`,
  `srs_preference_taxonomy_lifecycle.md`, and `srs_curriculum_notes.md`
  remain planning surfaces only.
- `srs_topic_coverage_pause_state_en_es.md` is the current closeout snapshot
  for the paused en-es topic coverage work; it records the accepted incomplete
  state but does not make topic coverage comprehensive or default-on.
- `srs_admitted_words_dashboard_plan.md` records the read-only user-facing
  admitted-words dashboard decision and deferred lifecycle action policy.
- `srs_browsing_based_admission_plan.md` is a planning workstream only; it
  records the intended opt-in word-signal design and the boundary that passive
  browsing must not mutate review scheduling.
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
- due-aware serving is implemented through helper rulegen SRS due metadata plus
  extension runtime gating when regenerated helper rules carry that metadata;
- helper publication still uses the broader active/admitted inventory rather
  than a dedicated due-only artifact;
- metadata-free cached helper rules remain active as a legacy compatibility
  fallback until regenerated;
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
