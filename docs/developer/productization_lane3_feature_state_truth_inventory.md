# Productization Lane 3 Feature-State Truth Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 read-only semantic runtime and pack-lifecycle truth pass, focused semantic publication/runtime tests, doc-reference check, state check, and diff hygiene
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

## Scope

Lane: Lane 3, feature-state truth pass.

Slice: L3-A, semantic runtime and semantic pack lifecycle.

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

## L3-A Next Work

Next Lane 3 slices should stay narrow:

1. L3-B: SRS admission, refresh, reset, due-aware serving, and publication.
2. L3-C: helper/native-host route matrix, including route availability,
   default data-root behavior, and diagnostics.
3. L3-D: rulegen LP support and onboarding state, with separate
   implemented/default-on/verified rows per pair.
4. L3-E: browser replacement runtime behavior, including DOM scan ordering,
   semantic batching, debug overrides, and failure diagnostics.
5. L3-F: packaging and Windows/macOS parity state.

## Validation

For this slice, use:

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
