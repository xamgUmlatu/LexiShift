# SP1 Translation/Frequency Panel Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted translation/frequency lifecycle tests plus surrounding panel-state and persistence checks
Purpose: bound the fourth SP1 slice around translation/frequency panel-state lifecycle parity so those families have the same level of evidence as the embedding seam
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.4`
- Title: translation/frequency panel-state lifecycle parity
- Pass type: verification-first with lifecycle regression coverage

## Exact Seam

Primary code surface:

- `apps/gui/src/settings_language_packs.py`
- `apps/gui/src/settings_language_packs_panel_state_mixin.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py`
- `apps/gui/tests/test_language_pack_panel_state_mixin.py`
- `apps/gui/tests/test_language_pack_table_mixin.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`

Primary contract/docs surface:

- `docs/reference/schema.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/data_source_normalization_execution_order.md`

## Explicitly Out Of Scope

This slice does not directly review:

- embedding panel-state behavior already handled in `SP1.2` and `SP1.3`
- resource settings file serialization authority already handled in `SP1.1`
- helper/runtime translation or frequency resolution beyond confirming the panel-state contract they consume
- broader resource-tab UI changes

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- translation/frequency state drift is highly user-visible when delete/unlink does the wrong thing
- the underlying code already looked cleaner than the embedding seam, but it lacked direct lifecycle tests
- this is exactly the kind of family-parity gap that makes later UX work inconsistent

## Contract Sketch

The intended translation/frequency panel-state contract is:

1. managed translation state lives in language-resource bindings and managed ids, not stale path maps
2. managed frequency state lives in dedicated managed-id state, not in manual path maps
3. manual/external translation and frequency inputs remain explicit compatibility/import paths
4. delete and unlink flows should clear the same state that select/auto-link/set-managed flows create
5. when local files are already gone, delete should still clear the remembered state instead of leaving stale managed/manual selection behind

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Mixed managed/manual translation and frequency state stays split in panel-state helpers and persistence. | `LanguagePackPanelStateMixin`, `build_synonym_resource_settings_from_panel(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py`, `apps/gui/tests/test_main_settings_resource_persistence.py` | `verified for this slice` |
| Translation unlink should clear the binding state even when only an external/manual path remains. | `LanguagePackPanel._delete_language_pack(...)`, `LanguagePackPanelStateMixin._clear_language_pack_entry(...)` | `apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py` | `verified for this slice` |
| Frequency delete should clear managed-id state even when local files are already absent. | `LanguagePackPanel._delete_frequency_pack(...)`, `LanguagePackPanelStateMixin._clear_frequency_pack_entry(...)` | `apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py` | `verified for this slice` |
| Frequency unlink should clear manual external-path state cleanly. | `LanguagePackPanel._delete_frequency_pack(...)`, `LanguagePackPanelStateMixin._clear_frequency_pack_entry(...)` | `apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py` | `verified for this slice` |

## Invariants

1. translation unlink removes the active binding and leaves no stale managed/manual language-pack state for that pack
2. frequency delete with missing files still removes managed frequency ids
3. frequency unlink removes manual external-path state cleanly
4. family behavior remains consistent with the installed-vs-manual contract already documented in the state ledger and schema docs

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Translation manual unlink | external/manual binding is cleared after confirmation |
| Frequency managed delete with files gone | managed id is cleared even without local files to remove |
| Frequency manual unlink | manual external-path entry is cleared after confirmation |
| Mixed managed/manual persistence | panel-state helpers and persistence still agree on the same split contract |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_language_pack_translation_frequency_lifecycle.py apps/gui/tests/test_language_pack_panel_state_mixin.py apps/gui/tests/test_language_pack_table_mixin.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_settings_resource_persistence.py -q`

## Planned Action For This Slice

1. add direct lifecycle tests for translation/frequency delete and unlink parity
2. keep behavior unchanged unless those tests expose a real state-cleanup bug
3. run the targeted bundle and either fix the seam or checkpoint it as verified

## Outcome

Result:

- no correctness defect found in the translation/frequency lifecycle seam
- delete and unlink behavior already matched the intended managed/manual contract
- the main gain from this slice was raising the evidence level to match the embedding seam
- no side findings were promoted from this slice
