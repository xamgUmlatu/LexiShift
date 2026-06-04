# D6 Refresh/Reset Reconciliation Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted refresh/reset tests, synthetic SRS harness rerun, semantic Phase 0 baseline rerun, and one local `en-es` refresh+reset smoke
Purpose: bound the D6 slice around refresh-time inventory/publication mutation and reset-time cleanup so later runtime-diagnostics work can build on an explicit refresh/reset contract
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
- Slice: `D6`
- Title: refresh/reset reconciliation
- Pass type: verification-first checkpoint with refresh/reset boundary pinning

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/use_cases/refresh_set.py`
- `core/lexishift_core/helper/use_cases/reset.py`
- `core/lexishift_core/helper/use_cases/signals.py`
- `core/lexishift_core/helper/rulegen_outputs.py`

Primary tests/evidence surface:

- `core/tests/helper/test_helper_engine.py`
- `core/tests/srs/test_srs_feedback_simulation.py`
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

- runtime-diagnostics payload joining
- extension/UI workflow wiring
- initialize semantics beyond using its output as D6 setup context
- due-aware serving as a shipped product claim
- helper-rule runtime confidence gating

## Risk Score

- likelihood: `medium`
- blast radius: `high`
- observability: `medium`
- priority: `high`

Reasoning:

- refresh is the main post-bootstrap mutation path that can silently drift inventory membership away from publication outputs
- reset is the cleanup path that has to remove both the new active-inventory state and the older semantic publication artifacts without crossing profile boundaries
- the most dangerous failure mode is partial cleanup or partial refresh publication that still leaves enough files around to look superficially healthy

## Contract Sketch

The intended current refresh/reset contract is:

1. refresh evaluates admission using the existing store, signal queue, pair policy, and candidate pool
2. when refresh admits new items:
   - store changes persist
   - explicit active inventory merges the newly admitted ids
   - `last_refreshed_at` is stamped
   - follow-up rulegen runs against the updated active inventory
   - publication still uses the current semantic artifact family
3. when refresh does not admit new items:
   - low-retention or other no-op decisions remain explicit in the payload
   - if the pair is on store fallback, refresh can still backfill inventory metadata without pretending publication happened
4. reset remains profile-scoped cleanup:
   - pair reset removes only that pair’s items, inventory membership, snapshot, ruleset, semantic inventory, and publication manifest
   - full reset clears the whole profile-local SRS surface
5. reset cleanup must not disturb unrelated profile data
6. D6 still does not claim that runtime diagnostics are fully reconciled; that remains the D7 join point

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Refresh merges newly admitted ids into explicit inventory and preserves allowed-POS / retention gating semantics. | `helper/use_cases/refresh_set.py` | targeted helper-engine refresh tests | `verified for this slice` |
| Refresh publication still writes ruleset/snapshot/semantic inventory/manifest when admission is applied. | `refresh_set.py`, `helper/rulegen_outputs.py` | targeted helper-engine refresh tests, `core/tests/srs/test_srs_feedback_simulation.py`, synthetic harness | `verified for this slice` |
| Refresh no-op paths remain explicit and do not masquerade as publication success. | `refresh_set.py` | targeted helper-engine refresh/feedback-cycle tests | `verified for this slice` |
| Reset removes pair/profile-scoped inventory and semantic publication artifacts cleanly. | `helper/use_cases/reset.py` | targeted helper-engine reset tests, local `en-es` smoke cleanup | `verified for this slice` |
| Broader SRS publication/runtime quality remains green except for the known due-aware warning. | synthetic SRS harness | `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json` | `verified for this slice` |
| Semantic publication/runtime protections remain intact while refresh/reset are audited. | D1 Phase 0 protected suite | semantic baseline rerun during D6 validation | `verified for this slice` |

## Invariants

1. keep refresh publication on the current semantic artifact family
2. keep reset cleanup pair/profile-scoped and additive to existing helper status/store behavior
3. do not treat refresh success as proof that runtime diagnostics are already fully reconciled
4. keep due-aware serving caveats explicit instead of laundering them through refresh evidence
5. keep no-op refresh decisions distinct from successful publication runs

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Normal refresh admission | new items enter `S`, active inventory grows, and publication runs |
| Allowed-POS refresh | admitted candidates honor the requested POS filter |
| Low-retention refresh | no-op decision remains explicit and inventory does not drift |
| Pair-policy default refresh | helper still resolves current policy defaults |
| Pair reset / full reset | cleanup removes only the intended profile/pair artifacts |
| Local LP smoke | real `en-es` refresh publication and reset cleanup both work in one temp workspace |
| Semantic baseline protection | semantic publication/runtime suite still passes unchanged |

## Validation Floor

- `python3 -m pytest core/tests/helper/test_helper_engine.py -k "test_reset_pair_removes_only_that_pair or test_reset_all_removes_all_pairs or test_reset_pair_scopes_to_profile or test_refresh_adds_new_items_when_feedback_and_capacity_allow or test_refresh_respects_allowed_pos_filter or test_refresh_pauses_admission_for_low_retention or test_refresh_uses_pair_policy_defaults or test_feedback_updates_schedule_and_blocks_low_retention_admission or test_good_feedback_allows_admission_and_publishes_rulegen_outputs" core/tests/srs/test_srs_feedback_simulation.py -q`
- `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
- `python3 -m pytest core/tests/rulegen/test_semantic_publication.py core/tests/rulegen/test_semantic_routing_runtime_policy.py core/tests/helper/test_rulegen_outputs.py core/tests/architecture/test_extension_structure.py core/tests/dev/test_helper_translation_dict_entrypoints.py -q`
- local `en-es` refresh+reset smoke in a temp workspace using synthetic `freq-es-cde.sqlite`, explicit forward `spa-eng.tei`, default reverse `eng-spa.tei`, initialize with `initial_active_count=10`, refresh after good/easy feedback, then pair reset
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check --cached`

## Planned Action For This Slice

1. verify that refresh still mutates explicit inventory and publishes through the current semantic family only when admission is applied
2. verify that reset removes the new inventory seam and the semantic publication artifacts together
3. keep runtime-diagnostics claims out of this slice so D7 still has a clear boundary

## Outcome

Result:

- refresh still merges newly admitted ids into explicit active inventory, stamps `last_refreshed_at`, and republishes through the current semantic artifact family when admission is applied
- refresh still preserves no-op behavior for low-retention cases and other non-applied decisions
- reset still removes pair/profile-scoped inventory membership, semantic inventory, and publication manifests without crossing profile boundaries
- targeted refresh/reset helper coverage plus feedback simulation reran green (`9 passed`)
- the synthetic SRS quality harness reran with `pass=15 warn=1 fail=0`; the remaining warning is still the known due-aware publication caveat, not a refresh/reset regression
- a local tempdir `en-es` smoke also succeeded with `refresh_applied=True`, `refresh_added_items=2`, `refresh_rules=12`, then `reset_removed_inventory_pairs=1`, `reset_removed_semantic_inventories=1`, and `reset_removed_publication_manifests=1`
- the semantic Phase 0 baseline suite reran green (`27 passed`), so the D6 checkpoint still sits on top of the protected semantic base
