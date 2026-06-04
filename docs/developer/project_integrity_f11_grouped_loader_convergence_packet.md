# F11 Grouped Loader Convergence Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted sqlite-support and dictionary resource suites
Purpose: close the `N-011` follow-up by moving translation-grouped auxiliary sqlite reads onto the extracted sqlite-support row/metadata seam without broadening into a loader-family redesign
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_f11_dict_loader_split_packet.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_secondary_pass_plan.md`

## Slice

- Track: `F11`
- Slice: `F11.2`
- Title: grouped translation loader convergence onto the shared sqlite-support row seam
- Pass type: bounded structural follow-through

## Exact Seam

Primary code surface:

- `core/lexishift_core/resources/dict_sqlite_support.py`
- `core/lexishift_core/resources/dict_translation_grouped_loader.py`

Primary tests/evidence surface:

- `core/tests/resources/test_dict_sqlite_support.py`
- `core/tests/resources/test_dict_loaders_freedict_pos.py`
- `core/tests/resources/test_kaikki_sqlite_conversion.py`

## Explicitly Out Of Scope

This slice does not directly review:

- public loader API redesign
- legacy `entries`-table or TEI loader paths
- broader resource-layer abstraction work beyond the auxiliary sqlite seam
- any rulegen, helper, or benchmark behavior above the low-level dictionary loaders

## Contract Sketch

The intended F11 contract after this follow-through is:

1. `dict_sqlite_support.py` owns auxiliary `sense_glosses` row selection, schema probes, ordering, and metadata hydration.
2. both headword-grouped and translation-grouped auxiliary sqlite loaders consume that shared row/metadata seam instead of carrying separate SQL/metadata copies.
3. `dict_translation_grouped_loader.py` remains only as a thin compatibility wrapper that supplies the record factory and metadata builder.
4. public loader behavior does not change: translation-grouped reads still return the same mapping shape and duplicate-row POS backfill behavior.

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Auxiliary sqlite row ordering and metadata hydration now live in one shared support seam. | `dict_sqlite_support.py` | code inspection plus `core/tests/resources/test_dict_sqlite_support.py` | `verified for this slice` |
| Translation-grouped auxiliary sqlite loading still backfills missing POS and preserves first-row metadata after the convergence. | `load_auxiliary_sqlite_gloss_records_by_translation_ordered(...)` | `core/tests/resources/test_dict_sqlite_support.py` | `verified for this slice` |
| Top-level grouped translation loading still works through the public loader surface after the wrapper becomes thin. | `dict_translation_grouped_loader.py`, `dict_loaders.py` | `core/tests/resources/test_dict_loaders_freedict_pos.py` | `verified for this slice` |
| Wider dictionary resource coverage still passes with the shared seam in place. | auxiliary sqlite loaders plus Kaikki sqlite conversion paths | `core/tests/resources/test_kaikki_sqlite_conversion.py` | `verified for this slice` |

## Invariants

1. top-level loader APIs remain unchanged
2. auxiliary sqlite schema probes stay centralized in `dict_sqlite_support.py`
3. auxiliary sqlite row ordering and metadata hydration no longer require parallel maintenance in two modules
4. duplicate translation rows still backfill missing POS without duplicating records

## Validation Floor

- `PYTHONPATH=core python3 -m pytest core/tests/resources/test_dict_sqlite_support.py core/tests/resources/test_dict_loaders_freedict_pos.py core/tests/resources/test_kaikki_sqlite_conversion.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`

## Outcome

Result:

- `dict_sqlite_support.py` now exposes a shared auxiliary sqlite row stream plus a translation-grouped support entrypoint in addition to the existing headword-grouped entrypoint
- `dict_translation_grouped_loader.py` now delegates the full auxiliary sqlite query/metadata path through that shared support seam instead of carrying its own copy
- seam-local coverage now proves the translation-grouped path preserves duplicate-row POS backfill and metadata, not only the headword-grouped path
- the low-level drift risk logged as `N-011` is closed without widening this slice into a broader loader-family refactor
