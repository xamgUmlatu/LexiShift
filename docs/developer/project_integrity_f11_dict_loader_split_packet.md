# F11 Dict Loader Split Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted sqlite-support tests plus existing dictionary resource suites
Purpose: bound the F11 slice around the auxiliary sqlite extraction from `dict_loaders.py` so the hotspot shrinks without broadening into loader-family redesign
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `project_health_remediation_workstream.md`

## Slice

- Track: `F11`
- Slice: `F11.1`
- Title: auxiliary sqlite-support extraction from `dict_loaders.py`
- Pass type: bounded structural split with seam-local coverage

## Exact Seam

Primary code surface:

- `core/lexishift_core/resources/dict_loaders.py`
- `core/lexishift_core/resources/dict_sqlite_support.py`
- `core/lexishift_core/resources/dict_translation_grouped_loader.py`

Primary tests/evidence surface:

- `core/tests/resources/test_dict_sqlite_support.py`
- `core/tests/resources/test_dict_loaders_freedict_pos.py`
- `core/tests/resources/test_kaikki_sqlite_conversion.py`

Primary contract/docs surface:

- `docs/developer/project_integrity_secondary_pass_plan.md`
- `docs/developer/project_health_remediation_workstream.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- broader translation-loader family convergence beyond the compatibility import fix in `dict_translation_grouped_loader.py`
- adjacent local benchmark/probe/helper test edits already in progress elsewhere in the worktree
- provider-level rulegen behavior or semantic publication logic
- TEI/XML parser behavior outside the existing top-level `dict_loaders.py` paths

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the extraction is structurally straightforward, but dictionary loaders sit under multiple runtime and conversion paths
- a mismatch here would show up across several consumers, even if the immediate code move is modest
- existing tests covered the behavior indirectly, but the extracted module itself had no direct contract before this slice

## Contract Sketch

The intended F11 contract after the split is:

1. `dict_loaders.py` remains the top-level public loader surface for XML, legacy sqlite, and auxiliary sqlite dictionary paths
2. auxiliary sqlite schema helpers and `sense_glosses`-based record/headword/base-form loaders live in `dict_sqlite_support.py`
3. the extracted sqlite support stays generic by accepting the record factory and metadata builder from the caller
4. top-level loader behavior does not change; it only delegates the auxiliary sqlite branch to the extracted module
5. the grouped-by-translation loader may reuse extracted sqlite schema probes, but its grouped query path can remain separate for now
6. other low-level loader-family duplication should remain explicit until a later consolidation pass

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| The extracted sqlite-support module can detect auxiliary schema shape and provide headword/base-form views directly. | `dict_sqlite_support.py` | `core/tests/resources/test_dict_sqlite_support.py` | `verified for this slice` |
| The extracted sqlite-support record loader still hydrates metadata and backfills missing POS on duplicate translations. | `load_auxiliary_sqlite_gloss_records_ordered(...)` | `core/tests/resources/test_dict_sqlite_support.py` | `verified for this slice` |
| Top-level auxiliary sqlite loading through `dict_loaders.py` still behaves the same after delegation. | `load_freedict_sqlite_gloss_records_ordered(...)` and related helpers | `core/tests/resources/test_dict_loaders_freedict_pos.py`, `core/tests/resources/test_kaikki_sqlite_conversion.py` | `verified for this slice` |
| The grouped-by-translation loader still works after the schema-probe helpers move out of `dict_loaders.py`. | `dict_translation_grouped_loader.py` | `core/tests/resources/test_dict_loaders_freedict_pos.py` | `verified for this slice` |

## Invariants

1. top-level dictionary loader behavior remains unchanged
2. auxiliary sqlite schema helpers are extracted without changing the public loader API
3. metadata hydration for `sense_glosses` rows stays intact
4. duplicate translation rows still backfill POS without duplicating records
5. grouped translation loading remains runtime-compatible after the helper extraction
6. loader-family duplication outside this seam remains explicit rather than being silently half-consolidated

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Basic auxiliary sqlite schema | extracted helpers detect tables/columns and load headwords/base forms directly |
| Auxiliary sqlite duplicate translation rows | extracted record loader backfills missing POS and preserves metadata |
| Top-level auxiliary sqlite loader path | existing resource suites still pass through `dict_loaders.py` after the extraction |
| Legacy sqlite / XML paths | remain untouched by the extraction |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=core python3 -m pytest core/tests/resources/test_dict_sqlite_support.py core/tests/resources/test_dict_loaders_freedict_pos.py core/tests/resources/test_kaikki_sqlite_conversion.py -q`

## Planned Action For This Slice

1. commit the extracted auxiliary sqlite-support module and the delegating `dict_loaders.py` changes
2. add one direct test file for the extracted module so the split is not justified only by indirect coverage
3. log adjacent loader-family duplication instead of widening this slice into a redesign

## Outcome

Result:

- the auxiliary sqlite branch of `dict_loaders.py` now lives behind a dedicated support module without changing the top-level loader API
- the extracted module has direct seam-local coverage in addition to the existing resource suites
- the one runtime regression exposed by the split was a private-helper import in `dict_translation_grouped_loader.py`, which is now closed by importing shared schema probes from the extracted module
- one adjacent duplication remains explicitly logged for later review: `dict_translation_grouped_loader.py` still carries its own grouped auxiliary sqlite query logic
