# Productization Lane 2 Semantic Testing Script Registry

Status: active registry
Role: Planning / WIP
Last updated: 2026-05-16
Last verified: 2026-05-16 read-only unreferenced-script review confirmed the semantic-shadow review queue is an active generated-evidence producer and refreshed script routing
Purpose: classify semantic testing and research scripts before any Lane 2 split, quarantine, archive, or deletion work
Source-of-truth: script registry only; executable truth lives in the scripts, tests, generated artifacts, package scripts, `feature_state_matrix.md`, and semantic/rulegen authority docs.
Related docs:
- `productization_lane2_code_disposition_inventory.md`
- `productization_closure_roadmap.md`
- `project_health_remediation_workstream.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../../scripts/README.md`

## Scope

This registry covers `scripts/testing/semantic*.py`.

It does not cover:

1. rulegen benchmark/gate/triage scripts,
2. SRS quality/journey scripts,
3. non-semantic resource/POS audits,
4. production semantic runtime modules under `core/` or `apps/chrome-extension/`.

Those surfaces should get separate Lane 2 registries only if cleanup pressure
appears there.

## Guardrails

1. Do not delete a script because it lacks exact filename references. Many
   testing scripts import support modules by Python module stem.
2. Do not run paid or live LLM requests during cleanup validation.
3. Keep generated evidence artifacts tied to their producing script until a
   replacement script and migration note exist.
4. Preserve current public import surfaces when splitting heavily imported
   support modules.
5. Route current product claims through `feature_state_matrix.md` and
   `../rulegen/semantic_rulegen_authority_map.md`; this registry is not runtime
   policy.

## Registry Labels

| Label | Meaning |
| --- | --- |
| Current harness | Stable local harness used to produce current evidence or verify a current claim. |
| Support library | Imported by multiple scripts/tests; split with compatibility facade first. |
| Active no-spend experiment | Useful local/source/audit experiment that does not spend model budget or change defaults. |
| Paid/LLM runner | Script that can execute live model requests or prepare live-request artifacts; requires safety guard preservation. |
| Research/prototype | Exploratory scorer/source/policy script that informs planning but is not product authority. |
| Historical evidence generator | Script mainly preserved to reproduce or interpret older generated artifacts. |
| Registry needed | Family is too dense to classify safely from filename alone. |
| Retire candidate | Possible future archive/delete candidate after exact import/reference/artifact review. |

No script is marked final-delete in this v0 registry.

## Family Scan

Commands used:

```bash
find scripts/testing -maxdepth 1 -type f -name 'semantic*.py' -print

find scripts/testing -maxdepth 1 -type f -name 'semantic*.py' -print \
  | sed 's#scripts/testing/##;s#.py$##'
```

Family counts:

| Family | Count | Initial Read | Default Disposition |
| --- | ---: | --- | --- |
| `semantic_veto_*` | 131 | Densest family; includes denominator, SRS bridge, generation planning/runs, scoring, formula, sampling, product-scope, and repair scripts. | Registry needed before deletion or moves. Keep current denominator/SRS expansion scripts. |
| `semantic_llm_*` | 31 | Prompt, generation, prototype, preflight, downstream, source insertion, reviewed-example, and support scripts. | Paid/LLM runner or research/prototype; preserve safety guards. |
| `semantic_shadow_*` | 23 | Shadow inventory, policy, source, proxy, embedding, and experiment scripts. | Research/prototype or historical evidence generator; classify against feature-state references. |
| `semantic_routing_*` | 19 | Sentence-veto harness/sweep/support plus generalization-bound evaluation and split support modules. | Current harness/support library; first structural split target. |
| `semantic_source_*` | 13 | Source admission, failure-class mining, held-out validation, margin policy, frame gap, and split support scripts. | Active no-spend experiment or research/prototype. |
| `semantic_decision_*` | 10 | Decision-rule matrix support/data/rendering/evaluation modules. | Support library / historical evidence generator; classify as a group. |
| `semantic_non_v10_*` | 7 | Non-v10 inventory/source/wave builder, admission sweep, and split support modules. | Active no-spend experiment; registry before retention decision. |
| `semantic_example_*` | 4 | Example frame batch merge and source adapter helpers. | Support/evidence helper; classify with LLM/source lanes. |
| `semantic_phrase_*` | 3 | Phrase containment and replay helpers. | Research/prototype; likely support for phrase-control analysis. |
| `semantic_reverse_aux_*` | 2 | Reverse-aux example/text lanes. | Research/prototype or historical evidence generator. |
| `semantic_surface_*` | 2 | Surface-POS rescue policy support/validation. | Research/prototype; tied to prototype scorer evidence. |
| `semantic_translation_*` | 1 | Translation sense evidence batch. | Research/prototype. |
| `semantic_authorization_*` | 1 | Authorization frame evidence. | Research/prototype. |
| WordNet/Wiktextract named scripts | 7 | Source-adapter/evidence lanes that do not share one prefix. | Active no-spend experiment where cited; registry needed for the rest. |

## Priority File Registry

| Script | Current Classification | Evidence / Reference | Lane 2 Action |
| --- | --- | --- | --- |
| `scripts/testing/semantic_veto_srs_corpus_expansion_audit_en_es.py` | Current harness | `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`, focused test added under `core/tests/dev/` | Keep. It is the current no-spend Spanish SRS corpus source-readiness audit. |
| `scripts/testing/semantic_veto_srs_zipf_bridge_en_es.py` | Current harness | `../rulegen/semantic_veto_srs_corpus_expansion_plan.md` | Keep. It bridges candidate SRS corpus rows into denominator planning. |
| `scripts/testing/semantic_veto_denominator_audit_en_es.py` | Current harness | `../rulegen/semantic_veto_denominator_current_state.md` | Keep. It supports current denominator posture. |
| `scripts/testing/semantic_veto_system_registry_summary.py` | Current harness / generated summary helper | `../rulegen/semantic_rulegen_authority_map.md` generated-evidence rule references system registry output | Keep pending broader semantic-veto artifact registry review. |
| `scripts/testing/semantic_routing_sentence_veto_support.py` | Support library | Former project-health violation; imported by many scripts and tests | Split complete. Preserve compatibility facade. |
| `scripts/testing/semantic_routing_sentence_veto_harness.py` | Current harness | `feature_state_matrix.md` semantic sentence-veto evidence references | Keep. Validate with focused tests before touching scorer behavior. |
| `scripts/testing/semantic_routing_sentence_veto_sweep.py` | Current harness / sweep | `feature_state_matrix.md` semantic sentence-veto evidence references | Keep. Do not collapse into support module during first split. |
| `scripts/testing/semantic_routing_sentence_veto_reporting.py` | Support/report helper | Former near-limit warning | Reporting-table split complete. Preserve public render helpers. |
| `scripts/testing/semantic_routing_generalization_bound_en_es.py` | Current harness | Former project-health violation; referenced by semantic routing generalization docs and tests | Config and confidence-corridor splits complete. |
| `scripts/testing/semantic_llm_prompt_bakeoff_en_es.py` | Paid/LLM runner | Former project-health violation; feature-state and prompt plans cite it | Split complete and warning cleared. Keep CLI/import compatibility and validate future changes with no-live replay/safety tests before any live run. |
| `scripts/testing/semantic_llm_prompt_preflight_en_es.py` | Paid/LLM guard / preflight | Feature-state and tests cite live command examples | Keep. Treat as safety perimeter around live prompt runner. |
| `scripts/testing/semantic_llm_prompt_cost_estimate_en_es.py` | Paid/LLM guard / cost estimator | Feature-state prompt workflow references | Keep. Preserve cost/safety checks before any live-run tooling changes. |
| `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py` | Research/prototype | Former near-limit warning; feature-state and semantic source docs cite it | Support split complete. Registry expansion should still classify whether it remains active research. |
| `scripts/testing/semantic_wordnet_example_frame_batch_en_es.py` | Active no-spend experiment | Former near-limit warning; semantic source docs cite it as current offline source lane | Support split complete. Keep as current offline source lane. |
| `scripts/testing/semantic_source_failure_class_mining_en_es.py` | Research/prototype | Former near-limit warning | Support split complete. Registry expansion should classify the source-analysis family. |
| `scripts/testing/semantic_source_margin_policy_sweep_en_es.py` | Research/prototype | Former near-limit warning | I/O split complete. Preserve artifact-producing defaults. |
| `scripts/testing/semantic_non_v10_wave_builder_en_es.py` | Research/prototype | Former near-limit warning | I/O split complete. Registry expansion should classify against current non-v10 evidence needs. |

## Evidence Expansion Checkpoint

This checkpoint expands the registry past the original project-health hotlist.
It is still a classification pass only: no files are deleted, moved, or
relabelled as product authority.

Read-only evidence scan:

```bash
rg -n "semantic_decision_|semantic_non_v10_|semantic_example_|semantic_phrase_|semantic_reverse_aux_|semantic_surface_|semantic_translation_|semantic_authorization_|semantic_wordnet_|semantic_wiktextract_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'

rg -n "semantic_shadow_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'
```

Expanded family ledger:

| Family | Evidence Found | Current Disposition | Lane 2 Action |
| --- | --- | --- | --- |
| `semantic_decision_*` | 10 scripts; refs in `semantic_decision_rule_comparison_plan.md`, `semantic_sentence_veto_algorithm.md`, `semantic_decision_research_lanes_en_es.json`, `semantic_veto_system_registry_en_es.json`; test coverage in `test_semantic_decision_rule_matrix_en_es.py`; imported by veto scoring/objective probes. | Keep as decision-rule evidence matrix and support library. | No archive/delete. Future cleanup should keep the matrix entrypoint stable and split only if health pressure returns. |
| `semantic_shadow_*` | 23 scripts; refs in `feature_state_matrix.md`, `semantic_shadow_testing_architecture.md`, `semantic_shadow_source_intake_plan.md`, runtime-readiness docs, and routing HTML state; generated artifact family is large. | Keep as active research harness / historical evidence generator. | Build a dedicated shadow sub-registry before any quarantine move. Do not delete from filename age alone. |
| `semantic_non_v10_*` | 7 scripts; refs in source-admission, weakness-triage, wave7, and system-registry docs; 7 focused tests; imported by `semantic_veto_llm_data_priority_target_family_construction_en_es.py`. | Keep as active no-spend source/wave-builder lane. | Preserve draft/artifact ownership and the new I/O/support split. |
| `semantic_example_*` | 4 scripts; refs in feature-state, source-admission, shadow-source, routing input docs; 2 focused tests; imported by 17 semantic/source/veto scripts. | Keep as high-fanout evidence/source adapter support. | Not a quarantine candidate. Treat support modules as shared API. |
| `semantic_phrase_*` | 3 scripts; refs in source-admission, weakness-triage, expansion, and system-registry docs; 2 focused tests; imported by prototype admission, margin sweep, and WordNet phrase miner. | Keep as phrase-control research/support. | Revisit only after phrase/no-winner policy is superseded. |
| `semantic_reverse_aux_*` | 2 scripts; refs in feature-state, LLM prompt/source plans, shadow-source plan, routing input docs; 2 focused tests; imported by prompt, source-insertion, reviewed-example, Wiktextract, and WordNet support scripts. | Keep as current no-spend fixture and historical evidence generator. | Do not archive until replacement fixture ownership is explicit. |
| `semantic_surface_*` | 2 scripts; refs in current wave6/wave7 and system-registry docs; 2 focused tests. | Keep as source-class rescue policy evidence. | Quarantine only after current rescue evidence is superseded and registry references are migrated. |
| `semantic_translation_*` | 1 script; refs in current wave6/wave7 and system-registry docs; focused test exists. | Keep as translation-sense source-class probe. | Same migration requirement as `semantic_surface_*`. |
| `semantic_authorization_*` | 1 script; refs in decision-research lanes and current veto registry docs; focused test exists. | Keep as authorization-frame source-class evidence. | Same migration requirement as `semantic_surface_*`. |
| `semantic_wordnet_*` | 5 scripts; refs in source-admission, shadow-source, weakness-triage, current wave docs, and system registry; 7 focused tests; imported by 17 semantic/veto scripts. | Keep as high-fanout source adapter and evidence lane. | Not a quarantine candidate. Treat `semantic_wordnet_source_adapter_support.py` as shared API. |
| `semantic_wiktextract_*` | 2 scripts; refs in source-admission, shadow-source, weakness-triage, wave7, and system-registry docs; 2 focused tests. | Keep as Wiktextract source/evidence lane. | Keep until source-family registry says a replacement exists. |

Result:

- no family in this expansion pass qualifies for `Delete candidate`;
- no family should be moved to archive until generated artifact ownership is
  mapped;
- this led to the semantic-veto sub-registry below; the next remaining
  sub-registry work is `semantic_llm_*` and `semantic_shadow_*`.

## Semantic-Veto Sub-Registry Checkpoint

This checkpoint classifies the `131` `semantic_veto_*` scripts into working
subfamilies. It does not decide final archive/delete status.

Read-only evidence scan:

```bash
find scripts/testing -maxdepth 1 -type f -name 'semantic_veto_*.py' -print

rg -n "execute-live|OPENAI|Responses|responses|api_key|estimated_cost|cost|live" \
  scripts/testing/semantic_veto_*.py

rg -n "semantic_veto_evidence_gap_generation_run|semantic_veto_llm_pilot_generation_run|semantic_veto_active_only_scale_tranche_requests|semantic_veto_active_only_full_generation_plan|semantic_veto_system_registry_summary|semantic_veto_srs_corpus_expansion_audit" \
  docs/rulegen docs/developer core/tests --glob '!docs/test_outputs/**'
```

Subfamily ledger:

| Subfamily | Count | Evidence Found | Current Disposition | Lane 2 Action |
| --- | ---: | --- | --- | --- |
| `active_only` | 9 | Active-only generation plan, pack builder, source packaging, inventory replay, helper smoke, live-page scan, and tranche request tooling. Referenced by the active-only tranche runbook, queueing plan, product-quality goals, and 7 focused tests. | Current operator/checkpoint tooling with paid-spend adjacency. | Keep. Preserve spend-guard wording and post-generation admission/packaging chain. |
| `srs_bridge_case_mix` | 4 | SRS case mix prior, SRS corpus expansion audit, Zipf bridge, and rendering support. Referenced by the expansion plan, denominator doc, authority map, and 3 focused tests. | Current no-spend denominator/source-readiness path. | Keep. This is the bridge back to corpus expansion. |
| `system_registry` | 1 | Registry renderer/auditor referenced by reconciliation, active-only tranche, wave7, and authority docs; focused test exists. | Current generated-summary helper / reconciliation gate. | Keep. Run before semantic-veto archive or candidate-state edits. |
| `denominator_zipf_expansion` | 6 | Denominator audit, Zipf boundary/expansion, curve-guided expansion, and deferred mapping scripts. Ten doc refs and 7 focused tests. | Current/research denominator and expansion support. | Keep. Do not archive until denominator and expansion docs explicitly supersede outputs. |
| `evidence_gap_generation` | 23 | Request planning, live/replay generation runner, safety, admission, postprocess, score contribution, prompt variant summaries. Seven doc refs and 10 focused tests. | Paid/LLM runner plus admission/postprocess support. | Keep with safety perimeter. Any cleanup must preserve `--execute-live`, cost ceilings, replay mode, raw response bundles, and append-only journals. |
| `llm_pilot_threshold` | 12 | LLM pilot generation/admission/scoring/failure review plus threshold bakeoff. Three doc refs and 8 focused tests. | Paid/LLM runner and historical/current comparator lane. | Keep for now; possible future quarantine only after system-registry artifact ownership maps this lane as superseded. |
| `product_quality_scope` | 15 | Product objective, product quality, product-scope filters/banding/bakeoffs/readiness. Five doc refs, 10 focused tests, and high script-fanout. | Product-quality research and current candidate interpretation support. | Keep. Not an archive candidate while product-quality docs and tranche tooling import it. |
| `representative_sampling` | 11 | Representative bands, gap plans, target family construction, sampling design/materialization/scoring. Five doc refs and 8 focused tests. | Sampling methodology and denominator breadth research. | Keep. Quarantine only after current sampling methodology is migrated to a canonical doc or newer harness. |
| `difficulty_stratification` | 6 | Difficulty stratification core/common/frequency/rendering/summary. Three doc refs, 4 focused tests, and 10 script importers. | Research support and shared scoring/reporting utilities. | Keep. Shared support modules make filename-age cleanup unsafe. |
| `formula_shape_weight` | 11 | Formula shape bakeoff, formula weight surface, repaired full-band formula sweep. Five doc refs, 3 focused tests, 6 script importers. | Research/prototype scoring comparator. | Keep until product-quality and assumption ledgers mark the formula comparators superseded. |
| `full_family` | 11 | Agent/human review packet, manual authoring, repair pool/pilot, representative sample, score surface, trusted eval seed. Three doc refs, 9 focused tests, 3 script importers. | Full-family review and repair evidence. | Keep. Archive only after surviving repair/review lessons are migrated. |
| `heuristic_translation` | 11 | Heuristic difficulty surface/group pilots and translation-ambiguity heuristic scripts. Five doc refs, 4 focused tests, 6 script importers. | Diagnostic/research comparator. | Keep; later quarantine candidate if system registry marks newer source-class evidence as the sole current lane. |
| `llm_data_priority` | 3 | LLM data-priority inventory bridge, scan, and target-family construction. Three doc refs and 3 focused tests. | Active prioritization support for generation planning. | Keep. It feeds representative target construction and should stay near the current queue docs. |
| `wave7_bound_gap` | 3 | Wave7 residual bound ladder, current evidence ceiling, and upstream gap audit. Two doc refs and 3 focused tests. | Diagnostic/current-wave crack-finding support. | Keep as current-wave diagnostic until the wave7 docs are closed or superseded. |
| `veto_only` | 3 | Veto-only candidate selection, probe, and validation. Three doc refs, 3 focused tests, and 12 script importers. | Comparator/negative-control support. | Keep. Import fanout blocks quarantine without migration. |
| `trusted_seed_performance` | 2 | Trusted-seed v2 band performance and rendering. Two doc refs and a focused test. | Historical/current seed comparator. | Possible later quarantine, not deletion, after registry ownership is explicit. |

Immediate semantic-veto disposition:

- `Keep`: `active_only`, `srs_bridge_case_mix`, `system_registry`,
  `denominator_zipf_expansion`, `product_quality_scope`,
  `representative_sampling`, and `llm_data_priority`.
- `Keep with paid-spend safety`: `evidence_gap_generation` and
  `llm_pilot_threshold`.
- `Keep as comparator / diagnostic until superseded`: `difficulty_stratification`,
  `formula_shape_weight`, `full_family`, `heuristic_translation`,
  `wave7_bound_gap`, `veto_only`, and `trusted_seed_performance`.
- `Delete candidate`: none.

Semantic-veto stop rule:

Do not move or delete any `semantic_veto_*` script until the system registry,
owning doc, focused tests, and generated artifacts agree that its surviving
value is migrated or intentionally retired.

## Semantic-LLM Sub-Registry Checkpoint

This checkpoint classifies the `31` `semantic_llm_*` scripts. The primary risk
is not dead code; it is accidentally weakening no-spend/live-spend boundaries
while cleaning up old prompt and source experiments.

Read-only evidence scan:

```bash
find scripts/testing -maxdepth 1 -type f -name 'semantic_llm_*.py' -print

rg -n "execute-live|OPENAI|Responses|responses|api_key|estimated_cost|cost|live" \
  scripts/testing/semantic_llm_*.py
```

Subfamily ledger:

| Subfamily | Count | Evidence Found | Current Disposition | Lane 2 Action |
| --- | ---: | --- | --- | --- |
| `prompt_runner_safety` | 11 | Prompt bakeoff runner, common/intake/journal/safety helpers, preflight, cost estimate, downstream/failure diagnostics, reporting, and smoke scripts. Seven doc refs, 9 focused tests, and 23 script importers. | Paid/LLM runner plus safety perimeter and no-spend replay/diagnostic support. | Keep. Preserve `--execute-live`, replay mode, cost ceilings, API-key preflight, immutable bundles, raw responses, and append-only live journals. |
| `prototype_admission` | 9 | Prototype ablation/admission config/probe/rendering/summary plus surface-POS support. Ten doc refs, 3 focused tests, and 5 script importers. | Active no-spend research/prototype admission lane. | Keep as research support. Do not present as runtime policy. |
| `example_frame_generation` | 9 | Example-frame contract, generation plan/prompts/run, quality gate, leakage audit, remediation plan, and sense discrimination audit. Seven doc refs, 12 focused tests, and one script importer. | Source-generation lane with live-run path plus no-spend contract/quality gates. | Keep with safety perimeter; generation runner cleanup must preserve prompt-runner safety helpers. |
| `reviewed_source_insertion` | 2 | Reviewed example-frame batch and source-insertion probe. Five doc refs and 3 focused tests. | No-spend fixture/source-insertion support. | Keep. It anchors reviewed positive fixtures for downstream/prototype checks. |

Immediate semantic-LLM disposition:

- `Keep with paid-spend safety`: `prompt_runner_safety` and
  `example_frame_generation`.
- `Keep as active no-spend research/support`: `prototype_admission` and
  `reviewed_source_insertion`.
- `Delete candidate`: none.

Semantic-LLM stop rule:

Do not move or collapse any script that participates in live execution,
preflight, cost estimation, replay, response normalization, or journal writing
unless focused no-spend tests still prove that live spend remains opt-in and
replay validation remains available.

## Semantic-Shadow Sub-Registry Checkpoint

This checkpoint classifies the `23` `semantic_shadow_*` scripts. These scripts
are research harnesses and generated-evidence producers; they should not be
treated as runtime product authority.

Read-only evidence scan:

```bash
find scripts/testing -maxdepth 1 -type f -name 'semantic_shadow_*.py' -print

rg -n "semantic_shadow_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'
```

Subfamily ledger:

| Subfamily | Count | Evidence Found | Current Disposition | Lane 2 Action |
| --- | ---: | --- | --- | --- |
| `inventory_policy_review` | 8 | Inventory, triage, policy compare/gap queue, `semantic_shadow_review_queue_en_es.py` / `semantic_shadow_review_packet_en_es.py`, promotion gap, and coverage gap scripts. Referenced by `feature_state_matrix.md`, runtime-readiness docs, weakness-triage docs, and `semantic_shadow_testing_architecture.md`; imported by the gold-proxy script. | Active research workflow / generated-evidence producer. | Keep. Add focused tests before code moves; docs alone are not enough to refactor this lane. |
| `gold_veto_seed_proxy` | 4 | Gold proxy, seed compare, forward-seed sweep, and veto-proxy compare scripts. Referenced by feature-state, generalization, weakness-triage, shadow architecture, routing HTML; imported by generalization-bound and shadow sweep scripts. | Active comparator/proxy evidence lane. | Keep. Not product authority; retain until generalization evidence is superseded. |
| `sweep_candidate_sources` | 5 | Embedding bridge, frequency, representative pruning, support-score, and trigger-support sweeps. Referenced by feature-state, weakness-triage, routing HTML. | Research candidate-source sweeps. | Keep as research. Future quarantine needs artifact ownership and a replacement summary. |
| `experiment_matrix_compare` | 6 | Experiment matrix/runner/support and compare/runner/support scripts. Referenced by feature-state, publish checklist, generalization plan, weakness-triage, and shadow architecture; `test_semantic_shadow_experiment_compare_support.py` covers support helpers. | Research experiment orchestration. | Keep. Existing focused test covers support helpers only; add tests before behavioral refactors. |

Immediate semantic-shadow disposition:

- `Keep as research / generated evidence`: all four subfamilies.
- `Quarantine candidate`: none yet, because current docs still route readers
  through this harness family.
- `Delete candidate`: none.

Semantic-shadow test gap:

Most `semantic_shadow_*` scripts are documented and artifact-producing, but only
the experiment-compare support helper has direct focused script-level coverage
in this scan. Any future code move in this family should add targeted tests or
stay documentation-only.

## Source-Admission And Named Adapter Sub-Registry Checkpoint

This checkpoint classifies the remaining lower-density source/admission scripts
that sit around semantic-veto, semantic-LLM, and semantic-shadow work. It covers
`33` scripts across `semantic_source_*`, `semantic_wordnet_*`,
`semantic_wiktextract_*`, `semantic_example_*`, `semantic_reverse_aux_*`,
`semantic_phrase_*`, `semantic_surface_*`, `semantic_translation_*`, and
`semantic_authorization_*`.

Read-only evidence scan:

```bash
find scripts/testing -maxdepth 1 -type f \( \
  -name 'semantic_source_*.py' -o \
  -name 'semantic_wordnet_*.py' -o \
  -name 'semantic_wiktextract_*.py' -o \
  -name 'semantic_example_*.py' -o \
  -name 'semantic_reverse_aux_*.py' -o \
  -name 'semantic_phrase_*.py' -o \
  -name 'semantic_surface_*.py' -o \
  -name 'semantic_translation_*.py' -o \
  -name 'semantic_authorization_*.py' \
\) -print | sort

rg -n "semantic_source_|semantic_wordnet_|semantic_wiktextract_|semantic_example_|semantic_reverse_aux_|semantic_phrase_|semantic_surface_|semantic_translation_|semantic_authorization_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'
```

Subfamily ledger:

| Subfamily | Count | Evidence Found | Current Disposition | Lane 2 Action |
| --- | ---: | --- | --- | --- |
| `source_admission_policy` | 8 | Admission cycle, heldout validation, margin policy support/sweep/I/O/rendering, source reference lane, and row-alignment audit. Twelve doc refs, 6 focused tests, and 5 script importers. | Active no-spend source admission and policy evidence. | Keep. Any behavior change belongs in a targeted source-admission pass, not cleanup. |
| `source_failure_gap` | 4 | Failure-class mining support/rendering and source-frame gap planning. Eleven doc refs and 2 focused tests. | Current diagnostic/source-gap research support. | Keep. Quarantine only after source-gap findings are migrated to a newer planning doc or harness. |
| `source_class_probes` | 5 | Authorization-frame evidence, source-class frame evidence, surface-POS rescue sweep/validation, and translation-sense evidence. Five doc refs and 5 focused tests. | Source-class evidence probes for current wave docs and the semantic-veto system registry. | Keep. These are not runtime policy; keep tied to registry evidence. |
| `example_frame_core` | 4 | Example-frame batch merge, evidence support, source-adapter support, and sentence-bank pilot. Six doc refs, 2 focused tests, and 17 script importers. | High-fanout support library / evidence fixture layer. | Keep. Treat support modules as shared API. |
| `wordnet_adapter_evidence` | 5 | WordNet source adapter, example-frame batch, alternate-sense phrase evidence, phrase-control miner, and support split. Nine doc refs, 7 focused tests, and 17 script importers. | High-fanout source adapter and evidence lane. | Keep. Not a quarantine candidate while non-v10, veto, and source scripts import it. |
| `wiktextract_adapter_evidence` | 2 | Wiktextract example-frame batch and translation-support scripts. Five doc refs and 2 focused tests. | Active source/evidence lane. | Keep. Archive only after source-family registry records a replacement. |
| `reverse_aux_fixture` | 2 | Reverse-aux text pilot and example-frame batch. Seven doc refs, 2 focused tests, and 7 script importers. | No-spend fixture and historical evidence generator. | Keep until replacement fixture ownership is explicit. |
| `phrase_control_support` | 3 | Phrase containment support, phrase policy signal audit, and prototype policy replay. Five doc refs, 2 focused tests, and 3 script importers. | Phrase-control support/research lane. | Keep until phrase/no-winner policy is superseded. |

Immediate source/admission disposition:

- `Keep as support/API`: `example_frame_core`, `wordnet_adapter_evidence`,
  `reverse_aux_fixture`, and `phrase_control_support`.
- `Keep as active no-spend evidence`: `source_admission_policy`,
  `source_failure_gap`, `source_class_probes`, and
  `wiktextract_adapter_evidence`.
- `Delete candidate`: none.

Source/admission stop rule:

Do not move source adapter or example-frame support modules without checking
script importers. Their value is often module-stem import compatibility, not
exact filename references.

## Candidate Sub-Registries

The next registry expansion should be split by family, not by alphabetical file
order:

1. deeper semantic-veto, semantic-LLM, semantic-shadow, and source-admission
   generated-artifact ownership if quarantine/archive action is desired,
2. any future registry for lower-risk non-semantic testing scripts if project
   health or dead-code pressure appears there.

Each sub-registry should record:

1. producing command,
2. default output artifacts,
3. tests that import the script,
4. docs that cite it,
5. whether it is current, historical, or experimental,
6. whether it can spend money or alter runtime defaults.

## First Code-Split Candidate

`semantic_routing_sentence_veto_support.py` was the first split. The import
surface is preserved by the facade at the original path.

Observed internal seams:

1. dataset loading,
2. base report construction,
3. sweep report construction,
4. ladder ranking and simulation,
5. weak-active overlay simulation,
6. phrase-leak probe reporting,
7. focus-case payload helpers.

Completed split shape:

1. `semantic_routing_sentence_veto_support.py` remains the compatibility facade,
2. dataset/base-report helpers moved to
   `semantic_routing_sentence_veto_common.py`,
3. sweep helpers moved to `semantic_routing_sentence_veto_sweep_support.py`,
4. ladder helpers moved to `semantic_routing_sentence_veto_ladder_support.py`,
5. weak-active/phrase-leak overlay helpers moved to
   `semantic_routing_sentence_veto_overlay_support.py`,
6. existing import names are re-exported,
7. focused sentence-veto tests and project-health report passed after the split.

## Validation Bundle For Registry-Only Edits

```bash
python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

## Validation Bundle For The First Code Split

```bash
python3 -m pytest \
  core/tests/dev/test_semantic_routing_sentence_veto_support.py \
  core/tests/dev/test_semantic_routing_sentence_veto_ladder.py \
  core/tests/dev/test_semantic_routing_sentence_veto_weak_active_probe.py \
  core/tests/dev/test_semantic_routing_sentence_veto_phrase_leak_probe.py \
  -q

npm --prefix scripts run health:project:report
```

Add any additional tests for helpers touched during the split.
