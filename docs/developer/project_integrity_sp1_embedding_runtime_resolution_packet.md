# SP1 Embedding Runtime Resolution Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted embedding helper/runtime resolution tests
Purpose: bound the sixth SP1 slice around embedding runtime resolution so saved managed/manual embedding state is verified all the way through the replacement-filter consumer path
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.6`
- Title: embedding runtime resolution authority
- Pass type: verification-first with consumer-resolution precedence coverage

## Exact Seam

Primary code surface:

- `apps/gui/src/main_replacement_filter_mixin.py`
- `core/lexishift_core/helper/embedding_packs.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_main_embedding_pack_resolution.py`
- `core/tests/helper/test_embedding_packs.py`
- `apps/gui/tests/test_state_resource_settings_migration.py`

Primary contract/docs surface:

- `docs/developer/feature_state_matrix.md`
- `docs/developer/data_source_normalization_execution_order.md`
- `docs/reference/schema.md`

## Explicitly Out Of Scope

This slice does not directly review:

- embedding panel-state lifecycle already handled in `SP1.2` and `SP1.3`
- translation or frequency consumer-resolution seams
- embedding-index load performance or replacement-ranking semantics after paths have already been resolved
- broader decisions about retaining manual vector/sqlite compatibility paths long-term

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- this seam is downstream of the persistence and panel-state work already verified, so a drift here would make the UI look correct while runtime consumption silently loads the wrong artifact
- the current contract is deliberately transitional because managed pack ids and manual compatibility paths can coexist
- the replacement filter is user-visible, but subtle path-authority mistakes can still hide behind "embeddings missing" or apparently valid fallback behavior

## Contract Sketch

The intended embedding runtime resolution contract is:

1. pack-id-first managed embedding activation should resolve through manifest-backed installed artifacts when available
2. a stale configured pack path should not override a present installed artifact for the same pack id
3. if a managed artifact is not present, the configured pack path can still act as a compatibility fallback for that pack id
4. pair-level manual embedding paths should append after pack-id-resolved artifacts
5. duplicate paths should be suppressed so the same SQLite file is not loaded twice

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Managed embedding pack ids resolve to manifest-backed installed SQLite artifacts when present. | `resolve_embedding_pack_artifact(...)`, `MainWindow._embedding_paths_for_pair(...)` | `core/tests/helper/test_embedding_packs.py`, `apps/gui/tests/test_main_embedding_pack_resolution.py` | `verified for this slice` |
| A configured fallback path does not override a present installed artifact for the same pack id. | `resolve_embedding_pack_artifact(...)`, `MainWindow._embedding_paths_for_pair(...)` | `core/tests/helper/test_embedding_packs.py`, `apps/gui/tests/test_main_embedding_pack_resolution.py` | `verified for this slice` |
| Managed embedding activation can still fall back to a configured pack path when the installed artifact is absent. | `resolve_embedding_pack_artifact(...)`, `MainWindow._embedding_paths_for_pair(...)` | `core/tests/helper/test_embedding_packs.py`, `apps/gui/tests/test_main_embedding_pack_resolution.py` | `verified for this slice` |
| Pair-level manual embedding paths append after pack-id-resolved artifacts without duplicate loads. | `MainWindow._embedding_paths_for_pair(...)` | `apps/gui/tests/test_main_embedding_pack_resolution.py` | `verified for this slice` |

## Invariants

1. pack-id-backed managed embedding activation prefers manifest-backed SQLite artifacts
2. stale compatibility paths do not override a live managed artifact for the same pack id
3. missing managed artifacts can still fall back to explicit configured pack paths during migration/compatibility scenarios
4. pair-level manual embedding paths remain additional inputs, not replacements for pack-id authority
5. the same physical SQLite path is returned at most once per pair resolution

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed pack present | pack id resolves to installed artifact |
| Managed pack present plus stale configured path | installed artifact still wins |
| Managed pack missing but configured path present | configured path acts as compatibility fallback |
| Pair-level duplicate manual path | duplicate path is returned only once |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_embedding_pack_resolution.py -q`
  - `python3 -m pytest core/tests/helper/test_embedding_packs.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_state_resource_settings_migration.py -q`

## Planned Action For This Slice

1. strengthen helper-level evidence for manifest preference and configured fallback
2. strengthen GUI consumer-level evidence for manifest preference, fallback, and duplicate suppression
3. keep behavior unchanged unless those tests expose a real authority-order bug

## Outcome

Result:

- no correctness defect found in the embedding runtime resolution seam
- the consumer path now has explicit evidence for manifest-first authority, compatibility fallback, and duplicate suppression
- this narrows future UX work because pack-id-first embedding activation can now rely on an explicit runtime contract instead of ad hoc path precedence assumptions
