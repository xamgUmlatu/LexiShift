# SP1 Resource Settings Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-17
Last verified: 2026-04-17 targeted persistence/import-export tests plus GUI/state migration tests
Purpose: bound the first SP1 slice around resource-settings serialization authority before any broader panel/runtime cleanup
Source-of-truth: packet only; executable truth still lives in code, tests, and evidence run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.1`
- Title: settings serialization authority
- Pass type: verification-first with targeted coverage additions

## Exact Seam

Primary code surface:

- `core/lexishift_core/persistence/settings.py`
- `apps/gui/src/dialogs.py`
- `apps/gui/src/state.py`

Primary tests/evidence surface:

- `core/tests/persistence/test_settings.py`
- `core/tests/persistence/test_import_export.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`
- `apps/gui/tests/test_state_resource_settings_migration.py`

Primary contract/docs surface:

- `docs/reference/schema.md`
- `docs/developer/feature_state_matrix.md`

## Explicitly Out Of Scope

This slice does not directly review:

- resource download/delete/autolink UX flows
- panel table rendering and status copy
- embedding activation UI transitions beyond what is persisted in settings
- helper/runtime resource resolution after settings have already been normalized

Those belong to later `SP1` or `SP5` slices unless this slice finds a blocking contract violation.

## Risk Score

- likelihood: `high`
- blast radius: `high`
- observability: `medium`
- priority: `very high`

Reasoning:

- silent drift in saved settings can survive across restarts and poison later review work
- managed-id vs manual-path confusion affects GUI, state migration, helper consumers, and operator trust
- some of the higher-level flows already had targeted coverage, but the low-level serialization/import-export seam was still thinner than it should be

## Contract Sketch

The intended contract for resource settings is:

1. app-managed translation and frequency packs persist by pack id
2. manual/external translation and frequency inputs persist in explicit `*_pack_paths` maps
3. app-managed embedding activation persists by pair-level pack ids
4. manual/external embedding inputs persist in explicit manual path maps
5. dialog persistence, state normalization, file serialization, and import/export should all preserve that split rather than rehydrating app-owned artifact paths back into manual fields

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Managed translation/frequency packs should survive settings save/load as ids, not manual paths. | `build_synonym_resource_settings_from_panel(...)`, `_split_managed_pack_paths(...)`, `AppState.update_settings(...)` | `apps/gui/tests/test_main_settings_resource_persistence.py`, `apps/gui/tests/test_state_resource_settings_migration.py` | `verified for this slice` |
| Manual translation/frequency paths should survive save/load separately from managed ids. | `settings_to_dict(...)`, `settings_from_dict(...)`, `_split_managed_pack_paths(...)` | schema docs plus `core/tests/persistence/test_settings.py` | `verified for this slice` |
| Managed embedding activation should survive as pair pack ids while manual embedding paths remain separate. | `_normalize_embedding_pack_settings(...)`, `build_synonym_resource_settings_from_panel(...)` | `apps/gui/tests/test_main_settings_resource_persistence.py`, `apps/gui/tests/test_state_resource_settings_migration.py`, `core/tests/persistence/test_settings.py` | `verified for this slice` |
| App-settings import/export should preserve the same split contract, not just raw JSON save/load. | `export_app_settings_code(...)`, `import_app_settings_code(...)` | `core/tests/persistence/test_import_export.py` | `verified for this slice` |
| The serialized schema should use explicit `language_pack_paths`, `frequency_pack_paths`, and `embedding_pack_paths` fields. | `settings_to_dict(...)`, `settings_from_dict(...)` | `docs/reference/schema.md`, `core/tests/persistence/test_settings.py` | `verified for this slice` |

## Invariants

1. managed translation packs persist in `managed_language_pack_ids`, not in `language_pack_paths`
2. managed frequency packs persist in `managed_frequency_pack_ids`, not in `frequency_pack_paths`
3. managed embedding activation persists in `embedding_pair_pack_ids`, not in manual embedding path maps
4. manual/external translation, frequency, and embedding inputs survive round-trip unchanged
5. explicit serialized field names remain `language_pack_paths`, `frequency_pack_paths`, and `embedding_pack_paths`
6. import/export code paths preserve the same semantics as file save/load

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Happy path: mixed managed/manual settings | managed ids stay in id fields; manual inputs stay in manual maps |
| Stale legacy path path | app-state migration promotes managed app-owned artifact paths into managed ids / pair pack ids |
| Restart round-trip | save -> load preserves the same managed/manual split |
| Import/export round-trip | export code -> import code preserves the same split |
| Secondary/manual coexistence | secondary/manual entries such as `wordnet-en` stay manual and do not get collapsed into managed ids |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/persistence/test_settings.py core/tests/persistence/test_import_export.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_settings_resource_persistence.py apps/gui/tests/test_state_resource_settings_migration.py -q`

## Findings

Before edits, the seam already had good coverage for:

- dialog persistence deriving managed ids and manual maps from the settings panel
- app-state migration of old managed translation/frequency/embedding artifact paths into pack-id-first settings

The main gap was lower in the stack:

- low-level persistence tests were not directly asserting mixed managed/manual translation and frequency fields
- import/export tests were only covering a minimal settings payload and did not exercise the resource-pack split contract

After this slice:

- the mixed managed/manual save-load contract is now asserted directly in `core/tests/persistence/test_settings.py`
- the explicit serialized field names are now asserted directly in `core/tests/persistence/test_settings.py`
- app-settings code export/import now exercises the same resource-pack split contract in `core/tests/persistence/test_import_export.py`
- the targeted GUI/state migration tests remained green, so the higher-level dialog/state normalization seam still agrees with the lower-level persistence seam

## Outcome

Result:

- no correctness defect found in the `SP1.1` serialization authority seam
- evidence strengthened enough to treat this slice as verified
- no side findings were promoted from this slice
