# D7 Runtime Diagnostics Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted diagnostics tests, synthetic SRS harness rerun, semantic Phase 0 baseline rerun, and one local `en-es` diagnostics smoke
Purpose: bound the D7 slice around the runtime diagnostics join point so inventory state and semantic publication state stay explicit, coherent, and separately testable
Source-of-truth: packet only; executable truth still lives in helper code, tests, local validation runs, and the current semantic publication contract
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D7`
- Title: runtime diagnostics join point
- Pass type: verification-first checkpoint with one narrow test-hardening improvement

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/helper/engine.py`
- `core/lexishift_core/helper/pair_resources.py`

Primary tests/evidence surface:

- `core/tests/helper/test_helper_engine.py`
- `core/tests/srs/test_srs_lp_e2e.py`
- `scripts/testing/srs_quality_harness.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- extension/UI rendering or consumption of diagnostics
- initialize/refresh/reset mutation semantics beyond using them as evidence producers
- due-aware serving as a shipped product claim
- helper-rule runtime confidence gating
- changing the diagnostics payload schema or adding new fields

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- diagnostics is the main operator-facing join point for store, active inventory, ruleset, snapshot, semantic inventory, and publication-manifest state
- if this payload drifts, the system can look healthy while hiding missing resources, stale inventory ids, or a broken publication family
- the highest-risk failure mode is a payload that still returns successfully while silently dropping one side of the inventory/publication story

## Contract Sketch

The intended current diagnostics contract is:

1. normalize pair/profile and resolve the current pair capability plus default resource paths
2. report missing runtime inputs without turning diagnostics itself into a hard gate
3. report store existence, pair-local counts, and word-package counts
4. report active-inventory existence, source, timestamps, and stale item-id count
5. report ruleset and snapshot counts plus snapshot `generation_id`
6. report semantic inventory existence, pointer modes, default unavailable reason, counts, and `generation_id`
7. report publication-manifest existence, validation state, error list/count, and `generation_id`
8. keep explicit inventory and store-fallback views distinguishable in the same payload

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Missing pair resources stay explicit in diagnostics for supported LPs. | `helper/use_cases/runtime_diagnostics.py` | direct helper diagnostics tests for `en-ja`, `en-de`, `en-es` | `verified for this slice` |
| Explicit inventory state, store-fallback state, and stale inventory ids remain visible in one payload. | `runtime_diagnostics.py`, `resolve_active_item_ids(...)` | direct helper diagnostics tests | `verified for this slice` |
| Semantic inventory and publication-manifest state still travel together through diagnostics. | `runtime_diagnostics.py` | direct helper diagnostics tests plus LP E2E assertions | `verified for this slice` |
| Real initialize/refresh publication for supported LPs still yields a diagnosable semantic family. | initialize/refresh plus diagnostics seam | `core/tests/srs/test_srs_lp_e2e.py`, local `en-es` smoke | `verified for this slice` |
| Broader SRS publication/runtime quality remains green except for the known due-aware warning. | synthetic SRS harness | `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json` | `verified for this slice` |
| Semantic publication/runtime protections remain intact while diagnostics are audited. | D1 Phase 0 protected suite | semantic baseline rerun during D7 validation | `verified for this slice` |

## Invariants

1. keep diagnostics read-only and tolerant of missing artifacts
2. keep inventory state and semantic publication state visible in the same payload
3. keep explicit inventory and store-fallback distinguishable
4. keep publication-family coherence visible through `generation_id`, validation state, and manifest error count
5. keep due-aware serving caveats explicit instead of laundering them through diagnostics

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Missing runtime files | missing inputs stay explicit without crashing diagnostics |
| Existing inventory/publication files | counts, timestamps, semantic state, and manifest validation all appear |
| Store fallback | diagnostics still reports active items and semantic publication state even without an inventory file |
| LP initialize/refresh E2E | manifest path exists, semantic inventory exists, and diagnostics reports a coherent generation family |
| Local `en-es` smoke | real initialize, feedback, refresh, and diagnostics all complete with a valid manifest family |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_with_missing_files core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_reports_missing_en_de_frequency_pack core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_reports_missing_en_es_frequency_pack core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_reports_missing_en_ja_jmdict core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_with_existing_files core/tests/helper/test_helper_engine.py::TestHelperEngineRuntimeDiagnostics::test_runtime_diagnostics_reports_store_fallback_inventory_with_publication_state core/tests/srs/test_srs_lp_e2e.py::TestSrsLpE2E::test_en_ja_e2e_initialize_and_refresh_publish_outputs core/tests/srs/test_srs_lp_e2e.py::TestSrsLpE2E::test_en_de_e2e_initialize_and_refresh_publish_outputs -q`
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- local `en-es` diagnostics smoke in a temp workspace using synthetic `freq-es-cde.sqlite`, explicit forward `spa-eng.tei`, default reverse `eng-spa.tei`, initialize with `initial_active_count=10`, refresh after repeated good/easy feedback, then `get_srs_runtime_diagnostics(...)`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify that diagnostics still reports resource, store, inventory, snapshot, semantic inventory, and publication-manifest state in one payload
2. tighten the LP E2E assertions so publication-manifest existence and generation-family coherence stop being implicit
3. keep extension/UI consumers and due-aware runtime behavior out of scope

## Outcome

Result:

- `runtime_diagnostics.py` still joins active inventory state and semantic publication state into one read-only payload
- direct diagnostics coverage reran green (`8 passed`) across missing-resource, existing-files, store-fallback, and LP E2E scenarios
- the D7 test hardening now makes LP E2E publication-manifest existence explicit and asserts manifest/semantic `generation_id` coherence plus zero manifest errors
- the synthetic SRS quality harness reran with `pass=15 warn=1 fail=0`; the remaining warning is still the known due-aware publication caveat, not a diagnostics regression
- a local tempdir `en-es` smoke also succeeded with `refresh_applied=True`, `refresh_added_items=8`, `refresh_rules=18`, `inventory_source=inventory`, `semantic_inventory_exists=True`, `publication_manifest_exists=True`, and a shared `generation_id` with `publication_manifest_family_valid=True`
- the semantic Phase 0 baseline suite reran green (`27 passed`), so the D7 checkpoint still sits on top of the protected semantic base
