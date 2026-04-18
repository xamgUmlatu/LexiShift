# E3 Embedding-Pack Holdout Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted migration/runtime contract tests plus lower-level embedding-pack resolver coverage
Purpose: bound the E3 slice around the managed embedding migration/runtime seam so later E4 work can keep wording cleanup separate from actual runtime correctness
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `data_source_normalization_execution_order.md`
- `feature_state_matrix.md`

## Slice

- Track: `E3`
- Slice: `E3.1`
- Title: embedding-pack settings/runtime split audit
- Pass type: verification-first with seam-local evidence closure

## Exact Seam

Primary code surface:

- `apps/gui/src/state.py`
- `apps/gui/src/main_replacement_filter_mixin.py`
- `core/lexishift_core/helper/embedding_packs.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_state_resource_settings_migration.py`
- `apps/gui/tests/test_main_embedding_pack_resolution.py`
- `apps/gui/tests/test_embedding_settings_runtime_contract.py`
- `core/tests/helper/test_embedding_packs.py`

Primary contract/docs surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/project_integrity_secondary_pass_plan.md`

## Explicitly Out Of Scope

This slice does not directly review:

- settings-panel seed/auto-link activation behavior already covered in `SP1.6` and `SP1.7`
- raw embedding download/conversion lifecycle behavior already covered by earlier embedding normalization work
- broader installed-vs-manual wording cleanup reserved for `E4`
- any rename of transient/manual embedding path fields that still exist for import/debug compatibility

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- the lower-level embedding resolver and GUI migration logic were already individually covered, which lowered the chance of a fresh blatant defect
- the seam still sits at a cross-layer join point where a missed mismatch would silently drop embeddings or keep stale manual state alive
- without a stitched contract test, docs could overstate what had been directly proven in-tree

## Contract Sketch

The intended embedding-pack contract after the SP1 normalization work is:

1. app-managed embedding installs live as manifest-backed SQLite artifacts under `embedding_packs/<pack-id>/main.sqlite`
2. old saved managed embedding artifact paths should migrate out of `embedding_pack_paths` and `embedding_pair_paths` on load
3. active managed embeddings should persist by pair-level pack id in `embedding_pair_pack_ids`
4. runtime replacement-filter loading should resolve those pack ids back through the manifest-backed installed artifact before considering any manual fallback path
5. manual embedding paths remain explicit import/debug compatibility inputs and should stay separate from the managed pack-id contract

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Loading older settings migrates managed embedding artifact paths out of the manual maps and into pair-level pack ids. | `_normalize_embedding_pack_settings(...)` in `state.py` | `apps/gui/tests/test_state_resource_settings_migration.py`, `apps/gui/tests/test_embedding_settings_runtime_contract.py` | `verified for this slice` |
| Runtime replacement-filter resolution can consume the migrated pair-level pack ids and land on the installed manifest-backed SQLite artifact. | `MainWindow._embedding_paths_for_pair(...)` plus `resolve_embedding_pack_artifact(...)` | `apps/gui/tests/test_main_embedding_pack_resolution.py`, `apps/gui/tests/test_embedding_settings_runtime_contract.py`, `core/tests/helper/test_embedding_packs.py` | `verified for this slice` |
| A present installed artifact wins over stale configured pack-path state for the same embedding pack id. | `resolve_embedding_pack_artifact(...)`, `MainWindow._embedding_paths_for_pair(...)` | `apps/gui/tests/test_main_embedding_pack_resolution.py`, `core/tests/helper/test_embedding_packs.py` | `verified for this slice` |
| Manual embedding paths stay distinct from the managed pack-id resolution path. | `_normalize_embedding_pack_settings(...)`, `MainWindow._embedding_paths_for_pair(...)` | existing panel/runtime tests plus the new stitched contract test's empty-manual-map assertions | `verified for this slice` |

## Invariants

1. app-managed embedding activation persists by pair-level pack id, not by installed artifact path
2. load-time normalization removes app-owned embedding artifacts from the manual path maps
3. runtime resolution after a load still reaches the same installed SQLite artifact
4. installed manifest-backed artifacts win over stale configured paths for the same managed pack id
5. manual embedding paths remain explicit compatibility inputs rather than becoming the source of truth for managed installs

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Legacy settings contain managed embedding artifact path in both pack and pair maps | load migrates the artifact out of manual maps, keeps the correct pair-level pack id, and runtime still resolves the installed artifact |
| Managed manifest-backed install present | runtime chooses the installed `main.sqlite` artifact for the active pair |
| Managed pack id plus stale configured path | runtime still prefers the installed manifest-backed artifact |
| Manual path support remains separate | normalization and runtime do not require manual maps for managed-pack activation |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=apps/gui/src:core python3 -m pytest apps/gui/tests/test_embedding_settings_runtime_contract.py apps/gui/tests/test_state_resource_settings_migration.py apps/gui/tests/test_main_embedding_pack_resolution.py -q`
  - `python3 -m pytest core/tests/helper/test_embedding_packs.py -q`

## Planned Action For This Slice

1. add one seam-local contract test that saves legacy managed embedding-path settings, reloads them through `AppState`, and resolves runtime embedding paths for the same pair
2. avoid production-code churn unless that stitched test exposes a real mismatch
3. record this slice as an evidence-closure checkpoint if the seam already behaves correctly

## Outcome

Result:

- no runtime correctness defect was found in the embedding migration/runtime seam
- the repo now has a direct save-load-resolve contract test covering the managed embedding path migration claim that earlier docs were making indirectly
- existing lower-level migration and runtime-resolution tests remain valid and now have an explicit join-point proof above them
- broader transient/manual embedding-path cleanup stays reserved for later wording/lifecycle work rather than being mixed into this bounded E3 slice
