# E1 Translation Heuristics Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 targeted helper/resource contract tests plus doc-reference gate
Purpose: bound the next translation-normalization slice around generic helper heuristics so manifest-backed pack identity stays primary and fallback filename guessing is narrower and more honest
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_e1_translation_pack_holdout_packet.md`
- `data_source_normalization_execution_order.md`

## Slice

- Track: `E1`
- Slice: `E1.2`
- Title: generic translation heuristic narrowing
- Pass type: verification-first with bounded helper fallback cleanup

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/lp_capabilities.py`
- `core/lexishift_core/helper/translation_packs.py`

Primary tests/evidence surface:

- `core/tests/helper/test_lp_capabilities.py`
- `core/tests/helper/test_translation_packs.py`
- `core/tests/helper/test_pair_resources.py`
- `core/tests/dev/test_rulegen_resource_contracts.py`

Primary contract/docs surface:

- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/developer/data_source_normalization_execution_order.md`

## Explicitly Out Of Scope

This slice does not directly review:

- pair-local `freedict_*` field names in `en_es.py`, `en_de.py`, or other rulegen pair modules
- helper/native-host payload renames that already landed in earlier E1/E2 slices
- benchmark/probe copy cleanup that was just finished in `N-008`
- TEI/manual-path phase-out decisions beyond narrowing the fallback search heuristics here

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the runtime is already mostly manifest-first, but the generic fallback helpers still decide identity using broad filename/provider guesses
- if those guesses are too loose, diagnostics and helper payloads can claim the wrong provider identity or pick up stale nested files in ways that are hard to notice
- this is still a bounded seam because it is helper resolution and metadata shaping, not scoring logic

## Contract Sketch

The intended contract for this slice is:

1. manifest-backed translation installs remain the primary source of pack identity
2. direct legacy root-level filenames remain an explicit compatibility fallback
3. nested fallback discovery should stay narrow to expected managed-pack roots, not arbitrary unrelated directories
4. translation-pack metadata should only claim `freedict` or `wiktionary` when the path or manifest actually supports that claim
5. unknown manual paths may still be usable, but their derived identity should stay generic rather than pretending to be a known provider

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Manifest-backed translation installs determine provider and pack identity correctly. | `build_translation_pack_ref(...)`, `resolve_pair_translation_packs(...)` | `core/tests/helper/test_translation_packs.py`, `core/tests/dev/test_rulegen_resource_contracts.py` | `verified before edit` |
| Default translation resolution prefers manifest-backed artifacts over legacy flat filenames. | `default_translation_dictionary_path(...)`, `default_reverse_translation_dictionary_path(...)` | `core/tests/helper/test_lp_capabilities.py` | `verified before edit` |
| Legacy direct-root filenames remain valid fallback inputs. | `default_translation_dictionary_path(...)`, `default_reverse_translation_dictionary_path(...)` | `core/tests/helper/test_lp_capabilities.py`, `core/tests/helper/test_pair_resources.py` | `verified before edit` |
| Generic helper metadata may still over-claim provider identity for unknown manual paths. | `infer_translation_pack_provider(...)`, `build_translation_pack_ref(...)` | no current test proving the safer behavior | `uncertain and likely too loose` |
| Nested legacy discovery is broader than necessary today. | `default_translation_dictionary_path(...)`, `default_reverse_translation_dictionary_path(...)` | no current regression test for search scope | `uncertain and likely too loose` |

## Invariants

1. managed manifests win when present
2. pair defaults still resolve the same known managed or legacy resources after the slice
3. helper/runtime/benchmark pack identity remain aligned for known FreeDict and Wiktionary paths
4. unknown manual paths do not get mislabeled as a known provider without supporting evidence
5. compatibility fallback does not silently expand to unrelated nested files

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed manifest-backed install | manifest provider and pack id still win |
| Legacy flat root-level SQLite or TEI file | default resolution still finds the known compatibility filename |
| Managed pack root without manifest but with legacy raw file inside | narrow fallback still finds the expected compatibility file when it lives under the expected pack root |
| Unrelated nested directory containing a legacy filename | default resolution should not accidentally treat it as the canonical pair default |
| Manual custom filename/path with no provider hint | pack metadata should remain generic rather than falsely claiming FreeDict |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/helper/test_translation_packs.py core/tests/helper/test_lp_capabilities.py -q`
  - `python3 -m pytest core/tests/helper/test_pair_resources.py core/tests/dev/test_rulegen_resource_contracts.py -q`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. narrow provider inference in `translation_packs.py` so it uses manifest or explicit path hints before falling back to a generic provider
2. narrow nested fallback search in `lp_capabilities.py` so it stays within the expected translation-pack roots for the pair instead of scanning arbitrary nested files
3. add seam-local regression tests proving the intended fallback boundary

## Outcome

Result:

- manifest-backed translation identity remained unchanged for the covered helper/runtime seams
- direct legacy root-level filenames remained valid fallback inputs
- translation-pack metadata no longer defaults unknown manual paths to `freedict`; unsupported manual names now stay generic unless the path or manifest provides a known provider hint
- compatibility fallback search for default translation dictionaries is now limited to declared pack roots for the pair instead of arbitrary nested directories under `language_packs_dir`
- one additional provider-shaped holdout was logged for later review: semantic publication capability codes in `lp_capabilities.py` still use `freedict_gloss` wording
