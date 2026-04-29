# Semantic Veto System Registry

- Status: `ok`
- Generated: `2026-04-29T19:26:35Z`
- Registry: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/semantic_veto_system_registry_en_es.json`
- Entries: `45`
- Passes: `7`

## Current Candidate

- Candidate: `wave6_auth_frame_raw_sentence_surface_pos_rescue`
- Production status: `research_only`
- Runtime policy change: `none`
- Control: wave6 alternate-phrase semantic surface-POS raw-sentence lane before authorization-frame rows
- Summary: Translation-sense plus alternate-sense phrase evidence, raw-sentence context, semantic phrase prototypes, surface-POS rescue/preemption, deterministic source-backed authorization-frame rows, and replayed rescue gates.
- Active/shadow: `0` harmful / `0` false abstains / `1.0` accuracy
- Phrase/no-winner before replay: `2` harmful
- Rescue replay passing policies: `12`

## Audit

- No registry issues detected.

## Next Passes

- `research_harness` (in_progress): Map each active harness to the exact question it answers.
- `archive_consolidation` (queued_next): Demote or label old artifacts after surviving value is migrated.
- `assumptions` (queued_next): Turn hidden candidate assumptions into explicit evidence-linked rows.
- `best_candidate` (queued_next): Reduce the project to one current candidate, one control, one blocker list, and one next breadth test.
- `data_artifacts` (queued_next): Separate frozen inputs, generated source rows, latest reports, and historical outputs.
- `overfit_leakage` (queued_next): Search specifically for test-shaped behavior and leakage.

## Counts

### Entry States
- `current_candidate`: `5`
- `current_reference`: `4`
- `current_research`: `12`
- `current_runtime`: `16`
- `diagnostic_only`: `1`
- `generated_evidence`: `5`
- `supporting_current`: `2`

### Components
- `candidate_wave6`: `8`
- `decision_research`: `7`
- `diagnostics`: `3`
- `evaluation_data`: `3`
- `process_governance`: `2`
- `runtime_path`: `16`
- `source_admission`: `6`

## Risk Rows

| Artifact | State | Component | Risk | Next Pass |
| --- | --- | --- | --- | --- |
| extension_active_rules_runtime | current_runtime | runtime_path | A ready-rule or inventory availability mismatch can make semantic gating silently fall back before policy scoring runs. | runtime_path |
| extension_apply_settings_pipeline | current_runtime | runtime_path | A propagation mismatch can make ready semantic coverage look inactive, or can apply the wrong fallback policy in the browser gate. | runtime_path |
| extension_background_native_bridge | current_runtime | runtime_path | Native host unavailability, timeout, or permission failures become helper errors that trigger semantic fallback instead of policy scoring. | runtime_path |
| extension_content_script_bootstrap | current_runtime | runtime_path | Bootstrap wiring drift can disconnect tested runtime modules or bypass semantic admission entirely. | runtime_path |
| extension_helper_client | current_runtime | runtime_path | Transport-level failures surface as fallback decisions rather than semantic policy outcomes. | runtime_path |
| extension_helper_rules_runtime | current_runtime | runtime_path | Helper transport errors and helper-cache fallbacks can change whether browser matches reach policy scoring. | runtime_path |
| extension_helper_semantic_cache | current_runtime | runtime_path | Stale or profile-mismatched cached inventory can make semantic admission appear available with outdated evidence. | runtime_path |
| extension_helper_transport | current_runtime | runtime_path | Bridge timeouts or unavailable runtime messaging surface as helper errors and semantic fallback decisions. | runtime_path |
| extension_manifest_runtime_order | current_runtime | runtime_path | Script-order drift can make the semantic gate unavailable or force browser matches down fallback paths before policy scoring. | runtime_path |
| extension_replacement_renderer | current_runtime | runtime_path | The DOM outcome can be misread if filtered-out matches are not distinguished from no lexical match. | runtime_path |
| extension_semantic_gate_runtime | current_runtime | runtime_path | Fallback defaults, inventory errors, or debug overrides can be mistaken for policy decisions if the decision_source is ignored. | runtime_path |
| helper_engine_semantic_entrypoint | current_runtime | runtime_path | Engine-level routing drift can disconnect tested use cases from the native-helper surface. | runtime_path |
| helper_semantic_admission_use_case | current_runtime | runtime_path | Inventory profile or pair mismatches here force fallback decisions before scoring. | runtime_path |
| native_helper_semantic_dispatch | current_runtime | runtime_path | A dispatch mismatch can make browser-side semantic readiness look available while admission requests fail. | runtime_path |
| runtime_policy_code | current_runtime | runtime_path | Research candidates can be mistaken for pair defaults. | runtime_path |
| runtime_scoring_code | current_runtime | runtime_path | Runtime behavior can drift from research lanes if policy ids or context/evidence views are confused. | runtime_path |
| authorization_frame_adapter | current_candidate | candidate_wave6 | Template expansion could become case-shaped if not source-triggered and heldout-checked. | overfit_leakage |
| surface_pos_rescue_sweep | current_candidate | candidate_wave6 | Replay-only candidate can be mistaken for runtime policy. | best_candidate |
| wave6_active_shadow_heldout | current_candidate | evaluation_data | Thresholds chosen on this suite would not be independent promotion evidence. | data_artifacts |
| wave6_phrase_heldout | current_candidate | evaluation_data | Must stay visible separately from active/shadow metrics. | data_artifacts |
| wave6_wiktextract_dataset | current_candidate | evaluation_data | Lives under test_outputs/experiments, so registry must keep its role explicit. | data_artifacts |
| decision_research_lanes_ledger | current_research | decision_research | Can grow without enough component-level classification unless paired with this registry. | research_harness |
| decision_rule_matrix_harness | current_research | decision_research | Multiple axes can be confused if result rows are summarized too aggressively. | research_harness |
| phrase_policy_signal_audit_harness | current_research | decision_research | Signal-only pass results do not validate translation targets, source evidence, or final replace/abstain decisions. | research_harness |
| prototype_ablation_matrix_harness | current_research | decision_research | A good ablation row is not an admitted source batch and can hide leakage or held-out failures. | research_harness |
| prototype_admission_probe_harness | current_research | decision_research | Prototype guard wins can be overread if the evaluation scope is prompt-queue sized or if source provenance is not separated. | research_harness |
| source_margin_policy_sweep | current_research | decision_research | Policy grids can be overread as promotion if not validated on locked heldout suites. | research_harness |
| source_failure_class_mining_harness | current_research | diagnostics | Failure-class mining summarizes evidence; it does not independently validate a candidate or change promotion state. | research_harness |
| heldout_validation_harness | current_research | source_admission | A clean active/shadow suite can hide phrase/no-winner harm if not paired with phrase validation. | data_artifacts |
| non_v10_wave_admission_sweep_harness | current_research | source_admission | Admission-selected waves are discovery artifacts until source support conversion, held-out validation, phrase validation, and failure mining pass. | research_harness |
| source_admission_cycle_harness | current_research | source_admission | Skipping heldout validation can make analysis-only admission look stronger than it is. | research_harness |
| source_frame_gap_plan_harness | current_research | source_admission | A frame-gap plan can be mistaken for accepted evidence if the later generation, leakage, sense admission, and held-out checks are skipped. | research_harness |
| source_row_alignment_audit_harness | current_research | source_admission | Selector-ready row counts can be mistaken for downstream decision quality if not paired with admission and held-out validation. | research_harness |
| alternate_sense_phrase_adapter | supporting_current | candidate_wave6 | Phrase rows must not become broad semantic competitors without a dedicated ablation. | assumptions |
| translation_sense_adapter | supporting_current | candidate_wave6 | Translation-sense text must stay source-backed and not target-lemma-derived. | overfit_leakage |
| decision_rule_comparison_plan | current_reference | decision_research | Can be bypassed if source work is described as decision-rule proof. | assumptions |
| semantic_sentence_veto_algorithm_doc | current_reference | process_governance | Can become stale if code defaults change without doc update. | runtime_path |
| semantic_veto_reconciliation_workstream | current_reference | process_governance | Must stay concise enough to guide later turns. | runtime_path |
| source_admission_program_doc | current_reference | source_admission | Long evidence list can obscure the current best candidate. | research_harness |
| auth_frame_active_shadow_validation | generated_evidence | candidate_wave6 | Breadth is too small for promotion. | best_candidate |
| auth_frame_admission_report | generated_evidence | candidate_wave6 | Admission report is analysis-only without heldout validation. | data_artifacts |
| auth_frame_phrase_validation | generated_evidence | candidate_wave6 | Can be misread as candidate failure if rescue replay context is omitted. | best_candidate |
| auth_frame_rescue_replay_report | generated_evidence | candidate_wave6 | Replay policy has not been promoted to runtime implementation. | best_candidate |
| auth_frame_failure_mining | generated_evidence | diagnostics | Uses unrescued phrase validation as a blocking heldout unless interpreted with rescue replay. | overfit_leakage |
| runtime_diagnostics_semantic_surfaces | diagnostic_only | diagnostics | Diagnostic pass/fail wording can be mistaken for the actual semantic gate decision path. | runtime_path |

## Entries

| Artifact | State | Component | Path | Current Use |
| --- | --- | --- | --- | --- |
| extension_active_rules_runtime | current_runtime | runtime_path | apps/chrome-extension/content/runtime/rules/active_rules_runtime.js | Browser-side readiness gate before any semantic YES/NO batch is attempted. |
| extension_apply_settings_pipeline | current_runtime | runtime_path | apps/chrome-extension/content/runtime/apply_settings_pipeline.js | Settings propagation surface that determines whether the semantic gate sees srsSemanticAdmissionEnabled and the selected fallback policy. |
| extension_background_native_bridge | current_runtime | runtime_path | apps/chrome-extension/background.js | Background service-worker bridge between extension runtime messaging and native helper requests. |
| extension_content_script_bootstrap | current_runtime | runtime_path | apps/chrome-extension/content_script.js | Top-level browser runtime wiring that connects semantic readiness, per-text admission, and DOM replacement rendering. |
| extension_helper_client | current_runtime | runtime_path | apps/chrome-extension/shared/helper/helper_client.js | Shared transport client beneath the browser semantic inventory and admission calls. |
| extension_helper_rules_runtime | current_runtime | runtime_path | apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js | Browser-to-helper bridge used by active-rules readiness and semantic batch admission. |
| extension_helper_semantic_cache | current_runtime | runtime_path | apps/chrome-extension/shared/helper/helper_cache.js | Cached inventory surface that can keep semantic scoring available when the helper inventory request falls back to helper-cache. |
| extension_helper_transport | current_runtime | runtime_path | apps/chrome-extension/shared/helper/helper_transport_extension.js | Content-to-background transport layer for get_semantic_inventory and semantic_admit_batch requests. |
| extension_manifest_runtime_order | current_runtime | runtime_path | apps/chrome-extension/manifest.json | Ensures semantic runtime modules and the native-message bridge are available before content_script.js boots. |
| extension_replacement_renderer | current_runtime | runtime_path | apps/chrome-extension/content/processing/replacements.js | Final browser-side point where an abstained semantic match stays as source text and a replace decision becomes visible DOM. |
| extension_semantic_gate_runtime | current_runtime | runtime_path | apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js | Browser-visible YES/NO gate between lexical match selection and replacement rendering. |
| helper_engine_semantic_entrypoint | current_runtime | runtime_path | core/lexishift_core/helper/engine.py | Runtime helper API surface reached by the native host and helper CLI layers. |
| helper_semantic_admission_use_case | current_runtime | runtime_path | core/lexishift_core/helper/use_cases/semantic_admission.py | Python helper entrypoint for browser semantic_admit_batch requests. |
| native_helper_semantic_dispatch | current_runtime | runtime_path | scripts/helper/lexishift_native_host.py | Native-message dispatch point between the extension transport and Python helper runtime. |
| runtime_policy_code | current_runtime | runtime_path | core/lexishift_core/rulegen/semantic_routing_runtime_policy.py | Production policy resolution; not automatically changed by research artifacts. |
| runtime_scoring_code | current_runtime | runtime_path | core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py | Production code path when semantic admission is active. |
| authorization_frame_adapter | current_candidate | candidate_wave6 | scripts/testing/semantic_authorization_frame_evidence_en_es.py | Current source-backed semantic-class repair for permission-like senses. |
| surface_pos_rescue_sweep | current_candidate | candidate_wave6 | scripts/testing/semantic_surface_pos_rescue_policy_sweep_en_es.py | Current wave6 combined-suite rescue candidate exploration. |
| wave6_active_shadow_heldout | current_candidate | evaluation_data | docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_heldout_cases_v1.json | Current active/shadow heldout suite. |
| wave6_phrase_heldout | current_candidate | evaluation_data | docs/test_inputs/semantic_routing_cases/en_es_source_non_v10_wave6_wiktextract_supported_phrase_cases_v1.json | Current phrase/no-winner heldout suite. |
| wave6_wiktextract_dataset | current_candidate | evaluation_data | docs/test_outputs/experiments/semantic_non_v10_wave_drafts/en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json | Current candidate source input. |
| decision_research_lanes_ledger | current_research | decision_research | docs/test_inputs/semantic_decision_research_lanes_en_es.json | Current research-lane state ledger. |
| decision_rule_matrix_harness | current_research | decision_research | scripts/testing/semantic_decision_rule_matrix_en_es.py | Final-rule and representation matrix; not source admission and not runtime policy. |
| phrase_policy_signal_audit_harness | current_research | decision_research | scripts/testing/semantic_phrase_policy_signal_audit_en_es.py | Signal-only phrase/no-winner audit before promoting phrase cases into end-to-end held-out suites. |
| prototype_ablation_matrix_harness | current_research | decision_research | scripts/testing/semantic_llm_prototype_ablation_matrix_en_es.py | No-spend ablation matrix for source/scorer/context/guard separation. |
| prototype_admission_probe_harness | current_research | decision_research | scripts/testing/semantic_llm_prototype_admission_probe_en_es.py | Mechanism probe for prototype evidence and guard shapes before broader matrix or admission-cycle interpretation. |
| source_margin_policy_sweep | current_research | decision_research | scripts/testing/semantic_source_margin_policy_sweep_en_es.py | Score-surface and threshold research; not source admission and not runtime policy. |
| source_failure_class_mining_harness | current_research | diagnostics | scripts/testing/semantic_source_failure_class_mining_en_es.py | Anti-handcrafting diagnostic before interpreting a clean seed or wave result as promotion evidence. |
| heldout_validation_harness | current_research | source_admission | scripts/testing/semantic_source_heldout_validation_en_es.py | Active/shadow and phrase/no-winner candidate validation. |
| non_v10_wave_admission_sweep_harness | current_research | source_admission | scripts/testing/semantic_non_v10_wave_admission_sweep_en_es.py | Breadth and source-support discovery surface for non-v10 waves. |
| source_admission_cycle_harness | current_research | source_admission | scripts/testing/semantic_source_admission_cycle_en_es.py | Canonical admission wrapper for source rows before held-out validation. |
| source_frame_gap_plan_harness | current_research | source_admission | scripts/testing/semantic_source_frame_gap_plan_en_es.py | Generation-planning surface; not generated evidence and not admission by itself. |
| source_row_alignment_audit_harness | current_research | source_admission | scripts/testing/semantic_source_row_alignment_audit_en_es.py | Source-row quality audit before frame-gap planning and context-conditioned evidence tests. |
| alternate_sense_phrase_adapter | supporting_current | candidate_wave6 | scripts/testing/semantic_wordnet_alternate_sense_phrase_evidence_en_es.py | Wave6 phrase/no-winner coverage foundation. |
| translation_sense_adapter | supporting_current | candidate_wave6 | scripts/testing/semantic_translation_sense_evidence_batch_en_es.py | Wave6 selected-sense source coverage foundation. |
| decision_rule_comparison_plan | current_reference | decision_research | docs/rulegen/semantic_decision_rule_comparison_plan.md | Methodology guardrail before changing decision rules. |
| semantic_sentence_veto_algorithm_doc | current_reference | process_governance | docs/rulegen/semantic_sentence_veto_algorithm.md | Primary algorithm map before runtime-path audits. |
| semantic_veto_reconciliation_workstream | current_reference | process_governance | docs/rulegen/semantic_veto_reconciliation_workstream.md | Top-level reconciliation entrypoint. |
| source_admission_program_doc | current_reference | source_admission | docs/rulegen/semantic_source_admission_program.md | Source-admission orientation and constraints. |
| auth_frame_active_shadow_validation | generated_evidence | candidate_wave6 | docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_heldout_margin000_phrase002_validation_latest.md | Current measured active/shadow result: 0 harmful and 0 false abstains on 38 cases. |
| auth_frame_admission_report | generated_evidence | candidate_wave6 | docs/test_outputs/semantic_source_admission_cycle_auth_frame_non_v10_wave6_wiktextract_supported_latest.md | Evidence for current candidate source-admission status. |
| auth_frame_phrase_validation | generated_evidence | candidate_wave6 | docs/test_outputs/semantic_source_non_v10_wave6_auth_frame_surface_pos_raw_sentence_phrase_margin000_phrase002_validation_latest.md | Shows unrescued phrase/no-winner harm remains visible. |
| auth_frame_rescue_replay_report | generated_evidence | candidate_wave6 | docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_non_v10_wave6_auth_frame_raw_sentence_latest.md | Current combined active/shadow plus phrase/no-winner rescue candidate evidence. |
| auth_frame_failure_mining | generated_evidence | diagnostics | docs/test_outputs/semantic_source_failure_class_mining_non_v10_wave6_auth_frame_latest.md | Keeps promotion posture at review despite clean active/shadow result. |
| runtime_diagnostics_semantic_surfaces | diagnostic_only | diagnostics | core/lexishift_core/helper/use_cases/runtime_diagnostics.py | Diagnostic evidence only; it does not decide browser replace or abstain outcomes. |
