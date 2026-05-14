# Semantic And Rulegen Authority Map

Status: active authority map
Role: Canonical current
Last updated: 2026-05-14
Last verified: 2026-05-14 Lane 1 semantic/rulegen authority and reverse-check archive pass against the listed docs; runtime behavior and benchmark claims were not re-audited
Purpose: route semantic-veto, semantic-routing, and rulegen cleanup work to the right current, planning, evidence, or historical source before productization closure continues
Source-of-truth: routing map only; implementation truth still lives in code, tests, generated artifacts, `docs/developer/feature_state_matrix.md`, and the owning domain docs listed below.

## Use This First For Semantic/Rulegen Cleanup

This map exists because the semantic-veto and rulegen areas now have many
detailed docs. Some describe shipped or operator-accepted behavior. Some are
planning surfaces. Some are generated evidence ledgers. Some preserve old
research lessons.

Do not pick the most detailed or newest `latest` artifact as authority. Choose
the row that matches the claim being checked.

## Current Authority Order

| Claim Being Checked | Start Here | Role In Cleanup | Do Not Use It For |
| --- | --- | --- | --- |
| Cross-cutting implemented/default-on/verified status | `docs/developer/feature_state_matrix.md` | Current status ledger for product claims, evidence paths, and known gaps. | Replacing source-code or test inspection. |
| Rulegen core behavior and LP mechanism shape | `docs/rulegen/rule_generation_technical.md`, `docs/rulegen/rulegen_lp_support_guide.md`, `docs/developer/rulegen_test_pipeline.md` | Mixed current reference for rulegen pipeline, LP support, and quality-loop operation. | Treating historical implementation-plan sections as fresh verification. |
| Rulegen scoring, candidate filtering, POS, or LP tuning validation | `AGENTS.md`, `docs/developer/ai_workflow.md`, `docs/developer/rulegen_test_pipeline.md` | Canonical quality-loop routing for benchmark, gate, triage, and targeted tests. | Updating baselines or thresholds without explicit rationale. |
| Reverse-check policy and dated experiments | `docs/developer/feature_state_matrix.md`, `docs/rulegen/reverse_check_rollout_matrix.md`, `docs/rulegen/reverse_check_scoring_phase1.md` | Current status plus historical evidence for default-off reverse-check scoring. | Treating dated March 2026 case reviews as current default policy. |
| POS normalization current behavior | `docs/rulegen/pos_normalization_workstream.md`, `docs/language_pairs/pos_source_and_pipeline_reference.md`, `docs/developer/feature_state_matrix.md` | Completed workstream reference plus current POS source/pipeline routing. | Assuming every downstream rulegen/SRS consumer fully uses POS metadata. |
| Semantic-routing runtime contract | `docs/rulegen/semantic_routing_runtime_readiness.md`, `docs/rulegen/semantic_routing_publication_contract.md`, `docs/developer/feature_state_matrix.md` | Current shipped seam, publication contract, readiness boundary, and product-state ledger. | Claiming full automatic semantic-routing or LP parity. |
| Semantic-veto current denominator and generation queue posture | `docs/rulegen/semantic_veto_denominator_current_state.md` | Canonical current answer for active-only denominator, queue exhaustion, and current pack posture. | Choosing a new corpus source or launching new paid generation. |
| Corpus/SRS expansion decision path | `docs/rulegen/semantic_veto_srs_corpus_expansion_plan.md` | Planning reference for no-spend source audits, candidate pack naming, and denominator refresh before generation. | Promoting a new frequency pack as default. |
| Semantic-veto artifact classification | `docs/rulegen/semantic_veto_artifact_authority_audit.md`, `docs/rulegen/semantic_veto_reconciliation_workstream.md` | Registry and reconciliation routing so generated artifacts do not become accidental runtime truth. | Changing runtime policy or accepting a candidate because one report looks good. |
| Older semantic-veto findings that still matter | `docs/rulegen/semantic_veto_archive_consolidation.md`, `docs/rulegen/semantic_veto_local_output_disposition.md` | Historical/support ledger for superseded or retained artifact lessons. | Steering current candidate selection unless promoted through fresh registry evidence. |
| Operator smoke of the current private semantic pack | `docs/rulegen/semantic_pack_operator_smoke_runbook.md`, `docs/rulegen/semantic_veto_active_only_tranche_runbook.md` | Operational install/smoke and future active-only tranche procedure. | End-user release claims or cloud distribution planning. |
| Semantic-shadow and source-heavy research harnesses | `docs/rulegen/semantic_shadow_testing_architecture.md`, `docs/rulegen/semantic_shadow_source_intake_plan.md` | Research workflow and source-intake discipline. | Runtime publication without separate readiness and publication-contract checks. |

## Current Semantic-Veto Posture

For productization closure, use this as the default posture unless a later
verified update changes the owning docs:

- tranche-011 is the latest operator-accepted automated product checkpoint for
  the active-only pack;
- tranche-003 remains the latest hands-on browser-extension smoke;
- the active-only paid generation queue is exhausted under the current reviewed
  `570` replacement-family denominator;
- the current installed Spanish SRS source universe is `1,984` distinct
  non-empty lemmas from a `2,000` row frequency DB;
- no current installed candidate reaches a 5k or 10k Spanish learner-target
  source size;
- SRS learner-target counts and semantic-veto replacement-family counts must
  stay separate in product docs;
- further corpus expansion is source-data and denominator work before it is an
  LLM-generation task.

## Generated Evidence Rule

Generated evidence can support a claim only when the owning doc or ledger says
how to interpret it.

Examples:

- `docs/test_outputs/semantic_veto_denominator_audit_en_es_latest.json`
  supports the current denominator doc.
- `docs/test_outputs/semantic_veto_srs_corpus_expansion_audit_en_es_latest.md`
  supports the current expansion planning doc.
- `docs/test_outputs/semantic_veto_system_registry_latest.md` supports the
  semantic-veto reconciliation registry, not runtime policy by itself.
- rulegen benchmark, gate, and triage outputs support rulegen quality claims
  only through the canonical rulegen quality loop.

The filename suffix `latest` is a convenience label, not authority.

## Safe Cleanup Sequence

When cleaning semantic or rulegen docs during Lane 1:

1. identify the claim type in the authority table above,
2. verify whether the doc is current, mixed, planning, generated evidence, or
   archive/support,
3. migrate any surviving current-truth claim into the owning current doc before
   demoting or archiving the older doc,
4. keep generated artifacts as evidence pointers unless the owning doc says they
   are the current rendered summary,
5. run `python3 scripts/dev/check_doc_references.py` and `git diff --check`
   after routing edits.

## Reverse-Check Archive Status

The dated reverse-check snapshots have been moved to the archive:

- `docs/archive/rulegen/reverse_check_en_es_case_review_2026-03-13.md`,
- `docs/archive/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`,
- `docs/archive/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`.

The active reverse-check references remain:

- `docs/rulegen/reverse_check_rollout_matrix.md`,
- `docs/rulegen/reverse_check_scoring_phase1.md`,
- `docs/rulegen/rulegen_lp_support_guide.md`,
- `docs/developer/feature_state_matrix.md`.

Current policy/status belongs in those active references. The archive files
preserve how the March 2026 `en-es` review widened the benchmark and isolated
`cuadro` as the remaining non-reverse failure class.
