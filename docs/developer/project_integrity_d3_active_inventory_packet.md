# D3 Active Inventory Persistence Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted inventory tests plus semantic Phase 0 baseline rerun
Purpose: bound the D3 slice around the explicit active-inventory seam so later preview, initialize, refresh, and diagnostics reconciliation work can build on a dated persistence contract instead of inferring it from scattered consumers
Source-of-truth: packet only; executable truth still lives in code, tests, helper use cases, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `srs_admission_selective_port_sequence.md`
- `srs_admission_merge_seam_map.md`
- `feature_state_matrix.md`
- `../srs/srs_profile_schema.md`

## Slice

- Track: `Wave D`
- Slice: `D3`
- Title: explicit active inventory persistence
- Pass type: verification-first checkpoint with seam-boundary clarification

## Exact Seam

Primary code surface:

- `core/lexishift_core/srs/inventory.py`
- `core/lexishift_core/srs/__init__.py`
- `core/lexishift_core/helper/paths.py`

First-layer consumer surface audited for boundary truth:

- `core/lexishift_core/helper/use_cases/rulegen_job.py`
- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`

Primary tests/evidence surface:

- `core/tests/srs/test_srs_inventory.py`
- `core/tests/helper/test_helper_profiles.py`
- `core/tests/helper/test_helper_engine.py`

Boundary-protection surface:

- Phase 0 semantic baseline suite from D1
- `core/tests/rulegen/test_semantic_publication.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_rulegen_outputs.py`
- `core/tests/architecture/test_extension_structure.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

## Explicitly Out Of Scope

This slice does not directly review:

- rebalance plan/apply execution details
- initialize-set mutation semantics
- refresh-set admission/update semantics
- reset cleanup semantics beyond profile-local inventory path isolation
- due-aware serving
- helper-rule runtime confidence gating
- any broad refactor of helper SRS use cases

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- this seam now sits underneath several helper flows, so a wrong assumption here can quietly skew later D-phase reviews
- the main risk is not a crash; it is overclaiming the inventory as authoritative or isolated when the current behavior is deliberately forgiving
- semantic publication can still regress indirectly if later slices mistake this persistence seam for a broader publication rewrite

## Contract Sketch

The intended current active-inventory contract is:

1. every profile gets its own additive inventory file at `srs/profiles/<profile_id>/srs_inventory.json`
2. each pair entry stores explicit `active_item_ids` plus optional lifecycle timestamps:
   - `last_initialized_at`
   - `last_refreshed_at`
   - `last_rebalanced_at`
3. serialization normalizes pair ids and item ids, deduplicates item membership, and keeps the payload versioned
4. resolution is intentionally forgiving:
   - missing inventory or missing pair entry falls back to store-derived membership
   - stale item ids referenced by inventory are dropped during resolution rather than breaking helper flows
5. first-layer consumers already exist:
   - rulegen can read active inventory and can backfill it from the store
   - runtime diagnostics can report inventory vs store-fallback state
6. those first-layer consumers do not yet collapse D3 into the broader D5/D6 reconciliation work; later phases still own the full mutation/runtime join-point review

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Inventory persistence is profile-scoped and additive rather than reusing semantic artifact paths. | `helper/paths.py` | `core/tests/helper/test_helper_profiles.py`, targeted profile-isolation helper test | `verified for this slice` |
| Inventory payloads normalize, round-trip, and support pair update/removal operations. | `srs/inventory.py` | `core/tests/srs/test_srs_inventory.py` | `verified for this slice` |
| Inventory resolution prefers explicit inventory when present but falls back to the store when absent, while dropping stale ids safely. | `srs/inventory.py`, runtime diagnostics | `core/tests/srs/test_srs_inventory.py`, `core/tests/helper/test_helper_engine.py` runtime diagnostics coverage | `verified for this slice` |
| Rulegen already has additive inventory-aware behavior without redefining the semantic publication family. | `helper/use_cases/rulegen_job.py` | targeted `core/tests/helper/test_helper_engine.py` rulegen inventory coverage | `verified for this slice` |
| Semantic publication/runtime protections remain intact while this seam is audited. | D1 Phase 0 protected suite | semantic baseline rerun during D3 validation | `verified for this slice` |

## Invariants

1. keep explicit active inventory separate from semantic inventory/publication artifacts
2. do not treat forgiving fallback/backfill behavior as proof that later lifecycle reconciliation is done
3. do not claim the inventory file is the only source of truth when current resolution still tolerates store-derived fallback
4. preserve profile-local isolation for inventory paths and reset behavior
5. keep the semantic Phase 0 baseline green while clarifying this seam

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Direct inventory roundtrip | payload persists `active_item_ids` and lifecycle timestamps cleanly |
| Missing/stale inventory | store fallback and stale-id dropping remain safe and explicit |
| Profile-local path isolation | inventory file path stays under profile-local SRS storage |
| Rulegen consumer touchpoint | inventory can constrain `active_item_ids` and backfill from the store |
| Runtime diagnostics touchpoint | diagnostics distinguish explicit inventory from store-fallback state |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/srs/test_srs_inventory.py core/tests/helper/test_helper_profiles.py core/tests/helper/test_helper_engine.py -k "rulegen_uses_inventory_active_ids_when_present or rulegen_backfills_inventory_after_bootstrap_publish or runtime_diagnostics_with_existing_files or runtime_diagnostics_reports_store_fallback_inventory_with_publication_state or reset_pair_scopes_to_profile" -q`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify the explicit inventory persistence/helpers rather than assuming they are still isolated
2. confirm where the seam already has additive consumers and where later phases still own reconciliation
3. refresh the selective-port Phase 2 note so the next D-phase slice inherits the actual current boundary

## Outcome

Result:

- explicit active inventory remains a real, profile-local persistence seam
- the core inventory module still owns normalization, roundtrip persistence, pair updates/removal, and forgiving resolution
- the seam is slightly broader than the older Phase 2 wording implied:
  - `run_rulegen_job` already consumes active inventory when present and can backfill it from store-derived membership
  - runtime diagnostics already reports `inventory` vs `store_fallback` state and stale-id counts
- that consumer presence is still additive; it does not replace the semantic publication family or finish the later initialize/refresh/reset/runtime reconciliation work
- the semantic Phase 0 suite reran green alongside this slice, so the D3 clarification does not rely on semantic regressions being ignored
