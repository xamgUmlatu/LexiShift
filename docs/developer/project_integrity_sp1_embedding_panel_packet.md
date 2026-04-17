# SP1 Embedding Panel Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 packet grounded in current embedding panel-state diffs, table/status behavior, downstream embedding resolution, and targeted GUI tests
Purpose: bound the third SP1 slice around embedding panel-state seed/auto-link/activation coherence so managed/manual state remains trustworthy during future GUI work
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.3`
- Title: embedding panel-state coherence
- Pass type: verification and checkpoint of the in-flight panel-state split

## Exact Seam

Primary code surface:

- `apps/gui/src/settings_language_packs_panel_state_mixin.py`
- `apps/gui/src/settings_language_packs_transfer_mixin.py`
- `apps/gui/src/settings_language_packs_table_mixin.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_language_pack_panel_state_mixin.py`
- `apps/gui/tests/test_language_pack_table_mixin.py`
- `apps/gui/tests/test_settings_resources_tab.py`
- `apps/gui/tests/test_main_embedding_pack_resolution.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`

Primary contract/docs surface:

- `docs/reference/schema.md`
- `docs/developer/feature_state_matrix.md`

## Explicitly Out Of Scope

This slice does not directly review:

- persistence/file serialization authority for resource settings
- delete/unlink fallback logic already handled in `SP1.2`
- translation/frequency panel-state parity
- broader resources-tab UI redesign or copy rewrites beyond verifying current contract language

## Risk Score

- likelihood: `medium-high`
- blast radius: `medium`
- observability: `high`
- priority: `high`

Reasoning:

- seed and auto-link mistakes can look harmless until they silently rehydrate managed artifacts back into the wrong state bucket
- this seam is very UX-visible because the table/status view is the operator's mental model of what is installed, manual, and active
- if we leave it ambiguous now, later UX work will keep compensating for state ambiguity instead of improving interaction design

## Contract Sketch

The intended embedding panel-state contract is:

1. app-managed installed embeddings should not be rehydrated into the manual `embedding_pack_paths` map
2. pair-level active embedding state should remain under `embedding_pair_pack_ids` for managed installs
3. manual/external embedding inputs should remain explicit compatibility/import paths
4. seed and auto-link flows should preserve the same installed/manual distinction that persistence and runtime now assume
5. resources-tab copy should reinforce that distinction so future UX changes build on the right mental model

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Seed should promote managed installed embedding artifacts into pair pack ids instead of restoring them into the manual map. | `LanguagePackPanelStateMixin._seed_embedding_pack_paths(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified in current worktree` |
| Auto-link should not copy installed managed embeddings into the manual map. | `LanguagePackPanelTransferMixin._auto_link_downloaded_embeddings(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified in current worktree` |
| Activate should keep managed installed embeddings active without polluting the manual map. | `LanguagePackPanel._activate_embedding_pack(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py`, `apps/gui/tests/test_language_pack_table_mixin.py` | `verified in current worktree` |
| Downstream replacement-filter resolution should still find the right embedding artifact after the panel-state split. | `MainWindowReplacementFilterMixin._embedding_paths_for_pair(...)` | `apps/gui/tests/test_main_embedding_pack_resolution.py` | `verified in current worktree` |
| The resources tab should communicate installed-vs-manual behavior clearly enough for later UX work to preserve the intended contract. | resources-tab copy + tab tests | `apps/gui/tests/test_settings_resources_tab.py` | `verified in current worktree` |

## Invariants

1. installed managed embedding artifacts do not get restored into `_embedding_pack_paths` during seed or auto-link
2. active managed embeddings are represented as pair-level pack ids
3. manual embedding paths remain explicit and are not silently upgraded into installed managed state
4. table/status rendering stays aligned with the underlying activation model
5. downstream embedding resolution still works with the split panel-state representation

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Seed mixed settings | managed installed artifacts are promoted to pair ids; manual paths remain manual |
| Auto-link after download | installed artifact is not copied into the manual map |
| Activate installed embedding | panel shows active installed state without redundant manual-path state |
| Active manual embedding | panel still distinguishes active manual state cleanly |
| Downstream runtime use | replacement-filter path resolution still finds the same pack after the split |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_language_pack_panel_state_mixin.py apps/gui/tests/test_language_pack_table_mixin.py apps/gui/tests/test_settings_resources_tab.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_embedding_pack_resolution.py apps/gui/tests/test_main_settings_resource_persistence.py -q`

## Finding

The in-flight embedding panel-state changes were coherent with the broader resource-settings contract.

Most importantly:

- seed now promotes managed installed embedding paths back into pair-level pack ids
- auto-link no longer repopulates the manual map for installed managed embeddings
- activate still yields the expected active-installed state in the table view
- downstream embedding resolution and settings persistence remained green against the split representation

No additional correctness defect was found in this slice beyond the stale-delete issue already fixed in `SP1.2`.

## Outcome

Result:

- the current local embedding panel-state split is now explicitly verified as a bounded SP1 slice
- the panel-state/UI seam and the downstream consumer seam still agree on the same installed/manual contract
- the resources-tab copy assertions now serve as guardrails for future UX work so product language does not drift back toward ambiguous path-first semantics
