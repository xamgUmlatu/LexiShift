# Productization Lane 3 Feature-State Truth Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 read-only semantic runtime, semantic pack-lifecycle, SRS admission/publication, helper/native-host route, rulegen LP onboarding, and browser replacement runtime truth passes; focused semantic, SRS, helper route, native-host, rulegen onboarding, browser runtime, and parity tests; SRS quality harness; doc-reference check; state check; and diff hygiene
Purpose: record feature-state reconciliation slices so implemented, default-on, verified, and still-planned claims stay separate before expansion resumes
Source-of-truth: inventory only; current runtime truth still lives in source code, tests, generated evidence, `feature_state_matrix.md`, and seam-specific canonical docs.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane1_doc_disposition_inventory.md`
- `productization_lane2_code_disposition_inventory.md`
- `feature_state_matrix.md`
- `documentation_governance.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../rulegen/semantic_veto_denominator_current_state.md`
- `../rulegen/semantic_veto_srs_corpus_expansion_plan.md`
- `../rulegen/rulegen_lp_support_guide.md`
- `../rulegen/lp_onboarding_operating_model.md`
- `../rulegen/lp_onboarding_checklist_template.md`
- `../architecture/chrome_extension_technical.md`
- `../architecture/extension_system_map.md`

## Scope

Lane: Lane 3, feature-state truth pass.

Completed slices:

1. L3-A: semantic runtime and semantic pack lifecycle.
2. L3-B: SRS admission, refresh, reset, and publication.
3. L3-C: helper/native-host route state.
4. L3-D: rulegen LP support and onboarding state.
5. L3-E: browser replacement runtime behavior.

This pass reconciles status claims only. It does not change runtime behavior,
promotion thresholds, generated artifacts, corpus sources, or semantic-veto
expansion posture.

Explicitly out of scope:

1. promoting active-only packs as a general user default,
2. changing semantic decision policy thresholds,
3. adding phrase-preemption inventory publication,
4. changing SRS admission, due serving, or helper publication behavior,
5. archiving old semantic research artifacts.

## Truth Labels

Use these labels for every Lane 3 slice:

| Label | Meaning |
| --- | --- |
| Implemented | Source code exists and is wired into the intended caller. |
| Default-on | A normal runtime path reaches it without a developer/operator-only action. |
| Default-on when capable | Runtime reaches it automatically only after required local capability artifacts exist. |
| Verified | Repeatable tests, harnesses, smokes, or generated evidence cover the claim. |
| Operator-only | Available through explicit debug, CLI, native-host, or profile-local install action. |
| Research-only | Evidence-producing or planning path, not current product behavior. |
| Planned | Design target with no current wired implementation. |

## L3-A Read-Only Inputs

Primary docs:

- `feature_state_matrix.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../rulegen/semantic_veto_denominator_current_state.md`

Primary code and tests:

- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/use_cases/semantic_admission.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/rulegen/semantic_publication.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_policy.py`
- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_batch.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
- `apps/chrome-extension/content/runtime/apply_settings_pipeline.js`
- `apps/chrome-extension/options/controllers/srs/actions/semantic_pack_install_workflow.js`
- `apps/chrome-extension/options/core/helper/diagnostics_methods.js`
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
- `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py`
- `core/tests/helper/test_helper_rulegen.py`

## L3-A Claim Ledger

| Claim | Implemented | Default State | Verified | Current Disposition |
| --- | --- | --- | --- | --- |
| Rules can carry `metadata.semantic_admission` pointers. | Yes. `semantic_publication.py` annotates rulegen results and preserves existing pointers. | Default-on for helper rulegen publication metadata generation. | Yes. Semantic publication tests cover ready and unavailable pointer shapes. | Current product seam. Keep in `feature_state_matrix.md` as implemented/default-on-when-capable/verified. |
| Helper rulegen can publish a semantic inventory sidecar. | Yes. `run_rulegen_for_pair` builds `semantic_inventory`, and `write_rulegen_outputs` publishes the generation-aligned family when provided. | Default-on in helper rulegen output generation, but readiness depends on emitted semantic content. | Yes. Helper and publication tests cover sidecar, manifest, stale-sidecar removal, and validation behavior. | Current product seam. Do not treat sidecar presence alone as runtime readiness. |
| `en-es` emitted-rule sibling context can promote active rules to `status=ready`. | Yes. Broader `semantic_context_targets` can supply sibling competition context without widening the visible ruleset. | Explicit helper-side PoC mode, not general LP default readiness. | Yes. Focused helper/rulegen and semantic-publication tests cover the promotion. | Narrow PoC. Keep the boundary explicit: this is not broad shadow mining or LP parity. |
| Browser runtime activates semantic admission from capability, not a normal visible user toggle. | Yes. Active-rule resolution computes `active`, `published_unready`, `unavailable`, or `error`, then injects `srsSemanticAdmissionEnabled` into the apply settings pipeline. | Default-on when capable: SRS enabled, ready SRS-origin rules exist, and semantic inventory resolves. | Yes. Runtime diagnostics and semantic gate contract tests cover active and published-unready states. | Current product seam. Docs should not describe this as a user preference. |
| Runtime semantic gating only submits ready SRS-origin matches to helper scoring. | Yes. `semantic_gate_batch.js` checks SRS origin, semantic pointer presence, `status=ready`, inventory resolution, and helper service availability. | Default-on when capable, with legacy fallback for unavailable ready-rule scoring. | Yes. Extension semantic-gate contract tests cover ready batching, non-ready fallback, context reuse, and helper fallback. | Current product seam. This is product behavior, not research-only behavior. |
| Runtime decision policy exists for helper-side semantic scoring. | Yes. `semantic_routing_runtime_policy.py` defines named production policies and fallback decisions; runtime requests surface the resolved `decision_policy_id`. | Active only for capable semantic publications; `active_only` `en-es` inventories can default to `en_es_sentence_veto_v2`. | Yes. Runtime policy/scoring tests and extension gate tests cover the path. | Current product seam, but not a complete UX policy. Keep visible affordance claims separate. |
| Visible browser behavior supports a rendered soft-affordance UX. | No. `soft_affordance` is a recorded/reserved non-replace outcome; DOM apply currently keeps original text unless the effective decision is `replace`. | Not default-on. | Partially verified as non-replace filtering/diagnostics, not as UI. | Planned/partial. The accurate gap is rendered soft affordance and product policy, not absence of all runtime decision policy. |
| Named semantic pack install is available from CLI/native-host/options debug flow. | Yes. The helper client and options workflow can call `installSemanticPack` with named pack ids and an explicit data root or default-root opt-in. | Operator-only. It overwrites profile-local semantic publication files after confirmation. | Yes. Existing installer, named-pack resolver, and native-host routing tests cover the route. | Current operator checkpoint, not a normal end-user default. |
| Tranche-011 active-only pack is a general shipped semantic-runtime default. | No. It is the latest operator-accepted product checkpoint, not a default publication for all users or LPs. | Operator-only / evidence checkpoint. | Verified by generated follow-through evidence and installer tests, not by broad default rollout. | Keep as controlled checkpoint. Do not expand product claims from it. |
| Fully mined shadow competition sets are default for all LPs. | No. Current default output does not include broad mined shadow sets. | Not default-on. | Research artifacts show feasibility and current gaps. | Planned/research-only. Needs automatic mining, promotion policy, and per-LP readiness before rollout. |
| Phrase-preemption inventory is published as part of runtime semantic packs. | No. Phrase-control exists in scoring/policy research and runtime scoring helpers, but publication still reports phrase inventory as not published. | Not default-on. | Research and policy tests cover phrase-control behavior; publication side remains a named gap. | Planned. Keep separate from semantic-veto serving and shadow mining. |

## L3-A Corrections Applied

This slice updates current docs to avoid two common status mistakes:

1. Do not say "no runtime decision policy" without qualification. A runtime
   decision policy surface exists; what is missing is a productized rendered
   soft-affordance UX and broader rollout policy.
2. Do not say semantic admission is simply "default-on" or "off." The accurate
   state is default-on when capable, with explicit operator-only semantic pack
   install for checkpoint packs.

## L3-B Read-Only Inputs

Primary docs:

- `feature_state_matrix.md`
- `../srs/README.md`
- `../srs/srs_roadmap.md`
- `../srs/srs_set_planning_technical.md`
- `../srs/srs_hybrid_model_technical.md`
- `../srs/srs_practice_layer_design.md`

Primary code and tests:

- `core/lexishift_core/helper/use_cases/initialize_set.py`
- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
- `core/lexishift_core/helper/use_cases/reset.py`
- `core/lexishift_core/helper/use_cases/rulegen_job.py`
- `core/lexishift_core/helper/rulegen.py`
- `core/lexishift_core/helper/rulegen_outputs.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/srs/admission_refresh.py`
- `core/lexishift_core/srs/inventory.py`
- `core/lexishift_core/srs/scheduler.py`
- `core/lexishift_core/srs/rebalance.py`
- `apps/chrome-extension/shared/srs/srs_gate.js`
- `scripts/testing/srs_quality_harness.py`
- `scripts/testing/srs_quality_summary.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/srs/test_srs_inventory.py`
- `core/tests/srs/test_srs_rebalance.py`
- `core/tests/srs/test_srs_feedback_simulation.py`
- `core/tests/srs/test_srs_lp_e2e.py`
- `core/tests/dev/test_extension_srs_runtime_gate_contract.py`

## L3-B Claim Ledger

| Claim | Implemented | Default State | Verified | Current Disposition |
| --- | --- | --- | --- | --- |
| Frequency bootstrap initializes `S` and publishes helper runtime artifacts. | Yes. `initialize_srs_set` resolves pair resources, writes the profile store/inventory, runs helper rulegen over active ids, and publishes ruleset/snapshot/semantic inventory family when available. | Default executable initialization path. | Yes. Helper tests, LP E2E tests, and SRS quality harness cover bootstrap publication. | Current product seam. Keep `frequency_bootstrap` as implemented/default-on/verified. |
| Profile bootstrap is the default helper initialization strategy. | No. Profile scoring/diagnostics exist, but helper initialization still executes the frequency-bootstrap baseline when mutation is required. | Not default-on. | Partially verified as planner/scoring diagnostics and strategy-contract tests. | Implemented but not default execution. Do not mark as shipped helper behavior yet. |
| Refresh can admit new items and republish helper artifacts. | Yes. `refresh_srs_set` applies admission refresh, merges active ids, persists store/inventory when configured, runs rulegen, and writes updated publication artifacts. | Default explicit/manual refresh path, not automatic adaptive refresh. | Yes. Helper tests, feedback simulation, LP E2E tests, and SRS quality harness cover refresh publication. | Current product seam. Keep automatic adaptive refresh separate. |
| Profile growth is a broad growth-admission strategy for `S`. | No. `profile_growth` is executable through rebalance preview/apply, but not general refresh/admission execution. | Not default-on. | Verified for rebalance-specific behavior. | Keep as implemented-for-rebalance only. Do not use it as the general growth-admission status. |
| Pair-local active inventory is the runtime publication input. | Yes. Initialize, refresh, rebalance, and rulegen job flows resolve/backfill pair-local `active_item_ids`; helper rulegen filters to those ids when provided. | Default-on, with store fallback when inventory is missing or stale. | Yes. Inventory tests, helper tests, diagnostics tests, and current SRS harness cover this. | Current product seam. Inventory remains forgiving, not strict authority. |
| Reset removes pair/profile SRS publication artifacts. | Yes. `reset_srs_data` removes store items by scope, pair inventory, ruleset, snapshot, semantic inventory, and publication manifest. | Default maintenance route behind options workflow confirmation. | Yes. Helper reset tests and extension maintenance workflow tests cover reset behavior. | Current product seam. Keep double-confirmed UI workflow separate from helper reset implementation. |
| Runtime SRS gate serves only due items. | No. The scheduler can compute due queues, but helper publication writes active/admitted inventory and extension `srs_gate.js` accepts all helper-published SRS rules. | Not default-on. | Verified as an intentional gap: SRS quality harness warns on broader-than-due publication, and extension gate contract tests assert all helper rules are accepted. | Planned. Do not mark due-aware serving shipped until helper publication and extension gating use an explicit due subset. |
| Feedback changes scheduling and can influence future admissions. | Yes. Feedback updates scheduler fields and signal events; refresh admission uses feedback-window signals to pause/resume growth. | Default-on for explicit feedback/refresh flow, not automatic refresh triggering. | Yes. Feedback simulation and SRS quality harness cover growth/pause/growth behavior. | Current explicit lifecycle seam. Automatic adaptive refresh remains planned. |
| Runtime confidence gating filters helper-published rules after publication. | No. Rulegen can filter by `confidence_threshold` before emission, but extension helper-rule runtime does not apply a live confidence threshold. | Not default-on. | Verified as absent by extension helper-rule confidence contract tests and feature-state audit. | Planned. Keep generation-time confidence filtering distinct from runtime gating. |
| Synthetic SRS quality harness is a full LP/user-runtime coverage gate. | No. It covers synthetic bootstrap/publication/runtime diagnostics for `en-ja` and `en-de`, plus an `en-ja` feedback-cycle scenario. | Default required SRS workflow gate for SRS changes, with limited scenario coverage. | Yes. Harness emits stable latest JSON and explicit warning counts. | Current quality gate with known scope limits. It does not prove `en-es`/`es-en` SRS parity or due-aware serving. |

## L3-B Corrections Applied

No feature-state status change was needed in this slice. The current matrix
already keeps the main SRS boundaries separate:

1. `frequency_bootstrap` is shipped; `profile_bootstrap` is implemented but not
   default helper execution.
2. refresh publication is implemented; automatic adaptive refresh is still
   planned.
3. active inventory publication is implemented; due-only serving is still
   planned.
4. generation-time confidence filtering exists; runtime helper-rule confidence
   gating is still planned.

The value of this slice is the compact claim ledger above, which gives future
agents a smaller SRS truth packet before any runtime or publication edits.

## L3-C Read-Only Inputs

Primary docs:

- `feature_state_matrix.md`
- `../architecture/native_messaging_design.md`
- `../developer/windows_gui_parity_workstream.md`
- `../developer/project_integrity_sp6_feature_state_refresh_packet.md`
- `../developer/project_integrity_sp7_share_center_copy_packet.md`

Primary code and tests:

- `scripts/helper/lexishift_native_host.py`
- `scripts/helper/lexishift_helper.py`
- `apps/chrome-extension/background.js`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/shared/helper/helper_transport_extension.js`
- `apps/chrome-extension/shared/helper/helper_error_copy.js`
- `apps/chrome-extension/options/core/helper/base_methods.js`
- `apps/chrome-extension/options/core/helper/diagnostics_methods.js`
- `apps/chrome-extension/options/core/helper/srs_set_methods.js`
- `apps/gui/src/helper_installer.py`
- `apps/gui/src/helper_connections_dialog.py`
- `apps/gui/src/helper_connection_inspection.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/dev/test_helper_installer_native_messaging.py`
- `core/tests/dev/test_helper_browser_connections.py`
- `core/tests/dev/test_extension_helper_error_localization_contract.py`
- `core/tests/dev/test_extension_helper_error_surface_contract.py`
- `core/tests/dev/test_extension_helper_status_profile_contract.py`
- `core/tests/dev/test_native_host_startup_logging.py`

## L3-C Route Ledger

| Claim | Implemented | Default State | Verified | Current Disposition |
| --- | --- | --- | --- | --- |
| Native host protocol is available through the extension service-worker bridge. | Yes. `background.js` bridges extension messages to `chrome.runtime.sendNativeMessage`; `helper_transport_extension.js` exposes the bridge to extension pages/runtime code. | Default-on when the browser native-messaging host is configured. | Yes. Extension helper error and status/profile contract tests cover bridge behavior. | Current product seam. Keep bridge failure handling explicit. |
| Helper client and native host expose matching route names. | Mostly yes. Client/native host cover `hello`, `status`, ruleset/snapshot, semantic inventory/admission, SRS diagnostics, feedback/exposure, rulegen, SRS initialize/plan/preview/refresh/rebalance/reset, profiles, profile rulesets, open data dir, and semantic pack install. | Default-on for configured helper routes; route use still depends on calling surface. | Yes. Native-host, helper-entrypoint, SRS workflow, semantic pack, and diagnostics tests cover representative routes. | Current route surface. Keep route additions contract-tested. |
| Semantic pack install can mutate the platform default data root without an explicit operator decision. | No. Native host requires `payload.data_root` or `payload.allow_default_data_root`; options UI requires a data root unless the default-root checkbox is enabled. | Operator-only. | Yes. CLI/native-host tests cover the explicit data-root guard, named pack resolution, and profile-local publication output. | Current safety seam. Preserve fail-closed behavior around profile-local publication mutation. |
| Helper/native-host diagnostics expose route health and runtime publication state. | Yes. `srs_diagnostics`, `status`, extension options diagnostics, and runtime last-state formatting expose store/ruleset/snapshot/cache, semantic inventory/capability, generation ids, helper/cache source, and route errors. | Default-on for explicit diagnostics actions and runtime reports. | Yes. Helper engine, SRS action formatter, SRS runtime diagnostics, and helper status/profile contract tests cover this. | Current product seam. Diagnostics are observability, not proof of every planned behavior. |
| Native-host startup/import failures have deterministic local evidence. | Yes. `lexishift_native_host.py` writes startup import/runtime tracebacks to `logs/native_host.log` under the LexiShift data root. | Default-on for native-host startup failures. | Yes. `test_native_host_startup_logging.py` covers the log path behavior. | Current support seam. Keep browser transport error and local host log concepts separate. |
| Browser connection manager can install, inspect, and auto-repair helper manifests. | Yes. GUI helper connection code writes manifests, tracks fixed-ID and unpacked-dev rows, wraps workspace hosts with a pinned interpreter, and auto-repairs known stale states. | Default-on in GUI connection surfaces and startup repair for saved connections. | Yes. Browser connection, helper installer, and Windows parity tests cover install/inspect/repair contracts. | Current product seam. Still not a release certification. |
| Same-browser production and unpacked-dev extensions can use different host paths simultaneously. | No. Native messaging still uses one manifest per browser host name, so allowed origins in the same browser share one host path. | Not supported. | Verified as a documented known gap through feature-state/native-messaging docs and installer behavior. | Known limitation. Do not claim independent same-browser host paths. |
| GUI/native-host install can prove the extension is installed and active in the browser. | No. The app can verify manifest/origin/host freshness, but cannot prove the extension is currently installed and enabled. | Not supported. | Recorded as a feature-state known gap. | Known limitation. Keep connection health distinct from extension-install health. |
| Windows native-host install parity is covered by the normal repo gate. | Yes. Windows parity audit covers GUI/helper/build parity, native-host executable expectations, manifest registry behavior, and CI-safe checks. | Default-on through repo safety gates. | Yes. `check:windows:parity` and helper installer tests cover the contract. | Current verification seam, not complete release certification. |

## L3-C Corrections Applied

No feature-state status change was needed in this slice. Current docs already
separate implemented helper/native-host route behavior from the remaining
operational limits:

1. a configured native-messaging host is required before extension helper routes
   are actually reachable;
2. semantic pack install remains explicit and operator-controlled because it
   mutates profile-local helper artifacts;
3. one browser manifest owns all allowed origins for that browser, so prod and
   unpacked-dev origins still share one host path;
4. manifest freshness does not prove the browser extension is installed or
   active;
5. Windows parity is a required safety gate, not full release certification.

## L3-D Read-Only Inputs

Primary docs:

- `feature_state_matrix.md`
- `../rulegen/rulegen_lp_support_guide.md`
- `../rulegen/lp_onboarding_operating_model.md`
- `../rulegen/lp_onboarding_checklist_template.md`
- `../rulegen/rule_generation_technical.md`
- `../rulegen/rulegen_congruity_implementation_plan.md`
- `../rulegen/pos_normalization_workstream.md`
- `../developer/ai_workflow.md`
- `../developer/genai_workflow_architecture.md`
- `../developer/rulegen_test_pipeline.md`
- `../language_pairs/de_en_workstream_roadmap.md`
- `../language_pairs/en_de_workstream_roadmap.md`
- `../test_inputs/rulegen_lp_profiles/README.md`
- `../test_inputs/rulegen_benchmark_cases/README.md`

Primary code and tests:

- `core/lexishift_core/helper/lp_capabilities.py`
- `core/lexishift_core/rulegen/adapters.py`
- `core/lexishift_core/rulegen/pairs/__init__.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/en_de.py`
- `core/lexishift_core/rulegen/pairs/en_ja.py`
- `core/lexishift_core/rulegen/pairs/es_en.py`
- `core/lexishift_core/rulegen/pairs/de_en.py`
- `docs/test_inputs/rulegen_lp_profiles/en_es.json`
- `docs/test_inputs/rulegen_lp_profiles/en_de.json`
- `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
- `docs/test_inputs/rulegen_benchmark_cases/en_de.json`
- `docs/test_inputs/rulegen_benchmark_cases/en_ja.json`
- `docs/test_inputs/rulegen_benchmark_cases/es_en.json`
- `docs/test_inputs/rulegen_benchmark_presets.json`
- `scripts/dev/check_rulegen_lp_profiles.py`
- `scripts/dev/check_rulegen_lp_conformance.py`
- `scripts/dev/scaffold_rulegen_lp.py`
- `core/tests/dev/test_check_rulegen_lp_conformance.py`
- `core/tests/dev/test_scaffold_rulegen_lp.py`
- `core/tests/dev/test_rulegen_benchmark_dataset.py`
- `core/tests/dev/test_rulegen_benchmark_cli.py`
- `core/tests/rulegen/test_rulegen_adapters.py`
- `core/tests/helper/test_lp_capabilities.py`

## L3-D Pair State Ledger

| Pair | Runtime Rulegen Mode | LP Profile | Dedicated Latest Benchmark Lane | Current Disposition |
| --- | --- | --- | --- | --- |
| `en-es` | Yes: `en_es`. | Yes: `docs/test_inputs/rulegen_lp_profiles/en_es.json`. | Yes: `docs/test_outputs/rulegen_benchmark_en_es_latest.json` plus canonical summary/gate/triage artifacts. | Primary strict/canonical lane. Still known-red on quality floor and rule volume, so expansion should not treat it as fully solved. |
| `en-de` | Yes: `en_de`. | Yes: `docs/test_inputs/rulegen_lp_profiles/en_de.json`. | Yes: `docs/test_outputs/rulegen_benchmark_en_de_latest.json` plus dedicated advisory gate/triage artifacts. | First advisory profiled lane. It is implemented/verified, but not repo-wide hard-gated or accepted as a quality baseline. |
| `en-ja` | Yes: `en_ja`. | No machine-readable LP profile yet. | No dedicated `rulegen_benchmark_en_ja_latest.json`; benchmark cases exist under `rulegen_benchmark_cases/en_ja.json`. | Runtime support exists, but current onboarding/profile/gate state is not at profiled-lane parity. |
| `es-en` | Yes: `es_en`. | No machine-readable LP profile yet. | No dedicated `rulegen_benchmark_es_en_latest.json`; benchmark cases exist under `rulegen_benchmark_cases/es_en.json`. | Runtime support exists, but current onboarding/profile/gate state is not at profiled-lane parity. |
| `de-en` | Yes: `de_en`. | No machine-readable LP profile yet. | No LP-specific benchmark case file or dedicated latest lane. | Baseline helper/rulegen enablement only. Do not treat as benchmarkable or promotable without a new onboarding slice. |

## L3-D Claim Ledger

| Claim | Implemented | Default State | Verified | Current Disposition |
| --- | --- | --- | --- | --- |
| Runtime rulegen support exists for all pairs listed by helper capabilities. | Yes. `supported_rulegen_pairs()` currently returns `en-ja`, `de-en`, `en-de`, `en-es`, and `es-en`, and adapter registrations exist for those modes. | Default-on when the helper route is configured and the pair's required dictionary resources are present. | Yes. LP capability and adapter tests cover the registry and representative generation paths. | Current product seam. Runtime support is not the same as benchmark/profile maturity. |
| Machine-readable LP profiles cover every runtime-supported rulegen pair. | No. The active profile directory currently contains only `en_es.json` and `en_de.json`. | Not default-on for unprofiled pairs. | Yes. Profile and conformance checks pass for exactly two profiles. | Known onboarding gap. Do not claim profile-owned onboarding for `en-ja`, `es-en`, or `de-en` yet. |
| The LP conformance audit proves profiled pairs line up with repo wiring. | Yes. It checks case-file naming, latest artifact presence, preset pair targeting, wrapper command pair mention, pair-module symbols, pair exports, adapter registration, and helper capability registration. | Explicit repo-safety command, not a substitute for rulegen quality results. | Yes. `check_rulegen_lp_conformance.py` and focused tests cover the contract. | Current governance seam. It proves wiring shape for profiled pairs, not quality parity. |
| Benchmark case files imply a full promoted benchmark lane. | No. `en-ja` and `es-en` have case files, but no dedicated latest benchmark/gate/triage lane comparable to `en-es` or `en-de`. | Not promoted by case-file presence alone. | Verified by current benchmark-case directory and latest artifact inventory. | Keep case authoring, latest artifacts, and promotion status separate. |
| `en-de` is mature enough to join the strict required pair gate. | No. It has a profiled advisory lane, but the current feature-state matrix still records it as outside `required_benchmark_pairs` with quality gaps and missing accepted baseline. | Advisory, not hard-gated. | Yes. Dedicated latest artifacts and state docs record the advisory lane. | Current improvement frontier, not a release-quality default. |
| The LP scaffold can safely complete central wiring for a new pair by itself. | No. It can generate profiles, case stubs, optional roadmap/code/test stubs, integration handoff, and preset starter text, but central adapter/preset/export/capability wiring remains a follow-up. | Operator-only scaffold. | Yes. Scaffold tests and conformance tests cover generated shape and explicit handoff behavior. | Current safe scaffold. Preserve the handoff boundary until a stronger registry updater exists. |
| A new expansion pair can start from tuning immediately. | No. The onboarding model requires source audit, scaffold, benchmarkability, baseline evidence, and then isolated mechanisms. | Not supported. | Verified by onboarding docs and profile/conformance gates. | Expansion should begin with profile/case/gate readiness, not scoring changes. |

## L3-D Corrections Applied

No feature-state status change was needed in this slice. The current docs
already separate the strict `en-es` lane, the advisory `en-de` lane, and the
baseline `de-en` enablement slice. This inventory adds the compact
cross-pair truth table so future expansion does not flatten four different
states into one word like "supported":

1. runtime rulegen mode,
2. machine-readable LP profile coverage,
3. benchmark case ownership,
4. dedicated latest benchmark/gate/triage artifacts,
5. promotion or hard-gate readiness.

## L3-E Read-Only Inputs

Primary docs:

- `feature_state_matrix.md`
- `../architecture/chrome_extension_technical.md`
- `../architecture/extension_system_map.md`
- `../developer/project_integrity_sp5_dom_scan_packet.md`
- `../developer/project_integrity_b4_semantic_diagnostics_packet.md`
- `../developer/project_integrity_d7_runtime_diagnostics_packet.md`
- `../rulegen/semantic_routing_runtime_readiness.md`
- `../rulegen/semantic_routing_publication_contract.md`
- `../rulegen/semantic_pack_operator_smoke_runbook.md`

Primary code and tests:

- `apps/chrome-extension/content/runtime/apply_settings_pipeline.js`
- `apps/chrome-extension/content/runtime/apply_runtime_actions.js`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`
- `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
- `apps/chrome-extension/content/runtime/dom_scan/scan_order.js`
- `apps/chrome-extension/content/runtime/dom_scan/page_budget_tracker.js`
- `apps/chrome-extension/content/runtime/dom_scan/semantic_node_scheduler.js`
- `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_batch.js`
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/processing/replacement_semantic_override.js`
- `core/tests/dev/test_extension_dom_scan_runtime_contract.py`
- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
- `core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py`
- `core/tests/dev/test_extension_helper_rule_confidence_contract.py`
- `core/tests/dev/test_extension_replacements_contract.py`
- `core/tests/dev/test_extension_srs_runtime_gate_contract.py`
- `core/tests/architecture/test_extension_structure.py`

## L3-E Runtime Ledger

| Claim | Implemented | Default State | Verified | Current Disposition |
| --- | --- | --- | --- | --- |
| Browser runtime resolves active rules from local rules plus helper/cache SRS rules. | Yes. `active_rules_runtime.js` merges profile/custom rules with helper rules, tags origins, applies the SRS gate, and reports helper/cache source and errors. | Default-on when SRS is enabled and helper/cache rules are available. | Yes. Helper-rule confidence, SRS runtime gate, and diagnostics contract tests cover the behavior. | Current product seam. Source/origin diagnostics are important because local and SRS rules can coexist. |
| Extension runtime filters helper-published SRS rules by due state. | No. The current SRS gate accepts all helper-published SRS rules and records helper-ruleset mode. | Not default-on. | Yes. The SRS runtime gate contract test asserts future-due and due helper rules both remain active. | Known product gap already tracked by L3-B. Keep due-serving separate from browser rule activation. |
| Extension runtime filters helper-published rules by confidence after publication. | No. Confidence filtering happens before helper emission; already-emitted helper rules stay eligible if enabled. | Not default-on. | Yes. The helper-rule confidence contract test keeps low- and high-confidence emitted rules active. | Known product gap already tracked by L3-B. Keep generation-time confidence filtering separate from runtime filtering. |
| Full DOM scans are raw DOM order unless page budgets are enabled. | No. `scan_order.js` always prioritizes visible and near-viewport nodes before far-offscreen nodes when viewport geometry is available; page budgets add deterministic within-band distribution. | Default-on for full scans. | Yes. DOM scan runtime contract tests cover visible-first stable ordering without budgets and page/profile distribution with budgets. | Corrected in this slice. Do not describe scan ordering as budget-only behavior. |
| Page budgets seed from existing replacements and preserve ordered rendering. | Yes. `page_budget_tracker.js` seeds from `.lexishift-replacement` spans and `dom_scan_runtime.js` builds budget state before full-scan reordering and per-node processing. | Default-on when page/lemma caps are configured. | Yes. DOM scan runtime contract tests cover seeding, updating, and full-scan ordering. | Current product seam. Mutation scans still process mutation-provided nodes rather than full-scan distribution. |
| Semantic scan batching preserves final page-budget behavior. | Yes. `semantic_node_scheduler.js` uses concurrent batches when safe; for budgeted scans it preflights semantic decisions, then renders serially with result overrides against the live page budget. | Default-on when semantic admission is active. | Yes. DOM scan and replacement override tests cover preflight/reuse with page-budget rendering. | Current performance seam. Keep the two-phase budgeted path explicit. |
| Semantic helper calls are batched and inventory resolution is reused. | Yes. `semantic_gate_batch.js` groups by pair/profile/fallback policy, reuses inventory resolution with a TTL, chunks helper requests, and sends `fit_scope=per_match`. | Default-on when semantic admission is active. | Yes. Semantic gate and diagnostics tests cover ready-only helper batching, fallback counts, policy ids, and performance metrics. | Current product seam. Helper batching changes must preserve per-match scoring semantics. |
| Debug semantic decision override is a product user control. | No. It only applies when debug is enabled and records `debug_override` metadata/metrics. | Debug-only. | Yes. Semantic gate and diagnostics tests cover override fields and counts. | Debug aid only. Do not treat it as a supported reading-mode policy. |
| `soft_affordance` is rendered in the page. | No. It is counted/reserved as a non-replace decision; the DOM still replaces only effective `replace` decisions and keeps original text otherwise. | Not default-on. | Verified by semantic gate filtering and replacement-span contract tests. | Planned UI gap. Keep soft-affordance schema/metrics separate from rendered UX. |
| Runtime semantic diagnostics persist for all normal users. | No. Apply-time last-state persistence is gated behind `debugEnabled`; options diagnostics can surface the persisted/debug runtime state plus helper/cache diagnostics when available. | Debug/operator diagnostics, not always-on telemetry. | Yes. Runtime diagnostics contract tests cover persistence with debug on and skip behavior with debug off. | Current observability seam. Do not rely on always-present tab runtime state for normal sessions. |

## L3-E Corrections Applied

This slice fixes stale scan-order wording in the extension architecture docs and
DOM scan packet:

1. visible/near-viewport priority is default full-scan behavior,
2. page budgets add deterministic within-band distribution, rather than being
   the only reason scan order changes,
3. semantic batching is current product behavior, but budgeted scans still use
   a preflight-plus-serial-render path to preserve final page-budget semantics,
4. debug decision overrides and runtime last-state persistence remain
   debug/operator observability, not normal reading-mode controls.

## Lane 3 Next Work

Next Lane 3 slices should stay narrow:

1. L3-F: packaging and Windows/macOS parity state.

## Validation

For L3-A, use:

```bash
python3 -m pytest \
  core/tests/rulegen/test_semantic_publication.py \
  core/tests/rulegen/test_semantic_routing_runtime_policy.py \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py \
  core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py \
  core/tests/helper/test_helper_rulegen.py

python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

For L3-D, use:

```bash
PYTHONPATH=core python3 -c "from lexishift_core.helper.lp_capabilities import supported_rulegen_pairs; print(','.join(supported_rulegen_pairs()))"
python3 scripts/dev/check_rulegen_lp_profiles.py
python3 scripts/dev/check_rulegen_lp_conformance.py

python3 -m pytest \
  core/tests/dev/test_check_rulegen_lp_conformance.py \
  core/tests/dev/test_scaffold_rulegen_lp.py \
  core/tests/dev/test_rulegen_benchmark_dataset.py \
  core/tests/dev/test_rulegen_benchmark_cli.py \
  core/tests/rulegen/test_rulegen_adapters.py \
  core/tests/helper/test_lp_capabilities.py

python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

For L3-E, use:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_dom_scan_runtime_contract.py \
  core/tests/dev/test_extension_semantic_gate_runtime_contract.py \
  core/tests/dev/test_extension_srs_runtime_diagnostics_contract.py \
  core/tests/dev/test_extension_helper_rule_confidence_contract.py \
  core/tests/dev/test_extension_replacements_contract.py \
  core/tests/dev/test_extension_srs_runtime_gate_contract.py \
  core/tests/architecture/test_extension_structure.py

python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

For L3-C, use:

```bash
python3 -m pytest \
  core/tests/dev/test_helper_translation_dict_entrypoints.py \
  core/tests/dev/test_helper_installer_native_messaging.py \
  core/tests/dev/test_helper_browser_connections.py \
  core/tests/dev/test_extension_helper_error_localization_contract.py \
  core/tests/dev/test_extension_helper_error_surface_contract.py \
  core/tests/dev/test_extension_helper_status_profile_contract.py \
  core/tests/dev/test_native_host_startup_logging.py

npm --prefix scripts run check:windows:parity
python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

For L3-B, use:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json

python3 scripts/testing/srs_quality_summary.py \
  --quality-json docs/test_outputs/srs_quality_latest.json \
  --markdown-out docs/test_outputs/srs_quality_summary_latest.md

python3 -m pytest \
  core/tests/helper/test_helper_engine.py \
  core/tests/srs/test_srs_inventory.py \
  core/tests/srs/test_srs_rebalance.py \
  core/tests/srs/test_srs_feedback_simulation.py \
  core/tests/srs/test_srs_lp_e2e.py \
  core/tests/dev/test_extension_srs_runtime_gate_contract.py

python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```
