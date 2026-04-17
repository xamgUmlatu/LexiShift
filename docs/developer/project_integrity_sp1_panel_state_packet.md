# SP1 Panel-State Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted panel-state lifecycle tests plus adjacent embedding-resolution and settings-persistence checks
Purpose: bound the second SP1 slice around panel-state lifecycle integrity for managed vs manual resource entries, especially embeddings
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.2`
- Title: panel-state lifecycle integrity
- Pass type: verification with bounded lifecycle fix

## Exact Seam

Primary code surface:

- `apps/gui/src/settings_language_packs_panel_state_mixin.py`
- `apps/gui/src/settings_language_packs.py`
- `apps/gui/src/settings_language_packs_table_mixin.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_language_pack_panel_state_mixin.py`
- `apps/gui/tests/test_language_pack_table_mixin.py`
- `apps/gui/tests/test_settings_resources_tab.py`
- `apps/gui/tests/test_language_pack_embedding_lifecycle.py`

Primary contract/docs surface:

- `docs/reference/schema.md`
- `docs/developer/feature_state_matrix.md`

## Explicitly Out Of Scope

This slice does not directly review:

- settings file serialization authority
- helper/runtime embedding resolution after settings have already been persisted
- frequency/translation delete flows beyond pattern comparison
- large UI copy or layout work

Those remain separate `SP1` / `SP5` work unless this slice finds a blocking mismatch.

## Risk Score

- likelihood: `high`
- blast radius: `medium`
- observability: `high`
- priority: `very high`

Reasoning:

- panel-state bugs often hide behind apparently normal tables until a restart or delete/unlink flow exposes them
- the managed/manual split is especially easy to regress during seed, auto-link, activate, and delete transitions
- stale in-memory pair activation can survive even when files are gone, which is exactly the kind of issue users experience as confusing UX

## Contract Sketch

The intended panel-state contract is:

1. managed app-owned embedding installs should stay under pair-level pack ids
2. manual/external embedding paths should stay in explicit manual path state
3. seed and auto-link flows should not rehydrate managed installed artifacts back into manual maps
4. delete/unlink flows should clear the same activation state that activate/seed flows created
5. status rows should describe installed/manual/active state in a way that reflects the actual panel state

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Seed and auto-link should keep managed embedding installs out of manual path maps. | `LanguagePackPanelStateMixin._seed_embedding_pack_paths(...)`, `LanguagePackPanel._auto_link_downloaded_embeddings(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified in current worktree` |
| Activation should keep installed managed embeddings under pair pack ids. | `LanguagePackPanel._activate_embedding_pack(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified in current worktree` |
| Delete/unlink should clear the same pair activation state even when local files are already absent. | `LanguagePackPanel._delete_embedding_pack(...)` | `apps/gui/tests/test_language_pack_embedding_lifecycle.py` | `verified after fix` |
| Resource-tab copy should make installed-vs-manual intent legible for future UX work. | settings resources tab copy + tab tests | `apps/gui/tests/test_settings_resources_tab.py` | `verified in current worktree` |

## Invariants

1. managed installed embedding artifacts do not remain in `_embedding_pack_paths` after seed/auto-link/activate flows
2. pair-level active ids are cleared when the corresponding embedding pack entry is deleted or unlinked
3. delete fallback paths should not leave stale active installed state behind just because files are already missing
4. manual/external entries remain explicit and are not silently treated as installed app-owned artifacts
5. panel status rendering remains consistent with the underlying activation state

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Seed managed + manual mix | managed installed artifact is promoted to pair pack id; manual entry stays manual |
| Auto-link after download | managed installed artifact does not get copied into the manual map |
| Activate installed pack | active state is represented by pair pack id rather than redundant managed manual-path state |
| Delete with files present | pair activation and local path state are both cleared |
| Delete with files already absent | stale pair activation is still cleared instead of being left behind |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_language_pack_panel_state_mixin.py apps/gui/tests/test_language_pack_embedding_lifecycle.py apps/gui/tests/test_language_pack_table_mixin.py apps/gui/tests/test_settings_resources_tab.py -q`

## Finding

The current in-flight embedding panel-state changes already improved the seed/auto-link/activate paths.

However, the delete fallback still had a lifecycle mismatch:

- when an embedding pack remained active in `_embedding_pair_pack_ids` but its local files were already gone, `_delete_embedding_pack(...)` could take the "no local files" branch and clear only `_embedding_pack_paths`
- this left stale pair-level activation behind, so the panel state could remain semantically active after the user had explicitly tried to remove it

## Planned Action For This Slice

1. preserve the current in-flight seed/auto-link/activate behavior
2. fix the stale-state delete fallback with the smallest coherent lifecycle change
3. add a focused regression test for the no-local-files delete case
4. run the targeted panel-state validation bundle

## Outcome

Result:

- the seed/auto-link/activate behavior under current local panel-state changes remained consistent with the intended managed/manual split
- `_delete_embedding_pack(...)` now clears stale pair-level activation even when the pack's files are already missing
- the new regression test covered the exact stale-delete case that previously contradicted the lifecycle contract
- no additional side findings were promoted from this slice
