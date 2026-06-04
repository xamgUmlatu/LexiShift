# SP1 Translation Runtime Resolution Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted translation helper and bulk-rules consumer tests
Purpose: bound the seventh SP1 slice around translation runtime resolution authority so managed translation pack ids remain authoritative even when stale same-key manual paths survive in settings
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.7`
- Title: translation runtime resolution authority
- Pass type: bounded fix with consumer-resolution precedence coverage

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/translation_packs.py`
- `apps/gui/src/main_bulk_rules_mixin.py`

Primary tests/evidence surface:

- `core/tests/helper/test_translation_packs.py`
- `apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py`
- `apps/gui/tests/test_state_resource_settings_migration.py`

Primary contract/docs surface:

- `docs/developer/feature_state_matrix.md`
- `docs/developer/data_source_normalization_execution_order.md`
- `docs/reference/schema.md`

## Explicitly Out Of Scope

This slice does not directly review:

- frequency consumer resolution, which already uses managed-first resolution
- embedding runtime resolution, already handled in `SP1.6`
- translation semantic quality or bulk-rule generation correctness after the artifact path is chosen
- broader secondary lexical pack normalization decisions

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the persistence and panel layers already try to keep managed translation state id-first, but this helper still allowed a stale same-key manual path to override the managed artifact
- that defect would be subtle because the UI could look correct while runtime consumers quietly read the wrong resource
- the seam is narrow and local, which makes it a good candidate for a bounded fix

## Contract Sketch

The intended translation runtime resolution contract is:

1. managed translation pack ids resolve to manifest-backed installed artifacts when available
2. a stale configured path under the same pack id must not override a present managed artifact
3. if no installed artifact is available, the configured path may remain as a compatibility fallback
4. unrelated manual entries, including secondary lexical paths, remain untouched
5. bulk-rules and other translation consumers should see the same artifact identity that the managed settings contract implies

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Managed translation pack ids resolve to manifest-backed installed artifacts. | `resolve_configured_language_pack_paths(...)` | `core/tests/helper/test_translation_packs.py`, `apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py` | `verified for this slice` |
| A same-key configured manual path does not override a present managed artifact. | `resolve_configured_language_pack_paths(...)` | `core/tests/helper/test_translation_packs.py`, `apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py` | `fixed and verified in this slice` |
| A configured path still acts as a compatibility fallback when the managed artifact is absent. | `resolve_configured_language_pack_paths(...)` | `core/tests/helper/test_translation_packs.py` | `verified for this slice` |
| State migration still removes stale managed artifact paths from saved settings before this helper is reached. | `AppState._normalize_resource_settings(...)` | `apps/gui/tests/test_state_resource_settings_migration.py` | `already verified before this slice` |

## Invariants

1. managed translation pack ids are authoritative when a managed artifact exists
2. stale same-key manual paths cannot shadow a present managed translation artifact
3. configured translation paths remain available as compatibility fallbacks when no managed artifact exists
4. unrelated manual entries such as secondary resources are preserved
5. consumer-facing translation resolution agrees with the pack-id-first persistence contract

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed translation pack present | managed id resolves to installed artifact |
| Managed pack present plus same-key configured path | installed artifact still wins |
| Managed pack missing but configured path present | configured path remains available as fallback |
| Mixed managed plus secondary manual entries | secondary manual entries remain untouched |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/helper/test_translation_packs.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py apps/gui/tests/test_state_resource_settings_migration.py -q`

## Planned Action For This Slice

1. pin same-key managed-vs-manual precedence explicitly in helper and consumer-adjacent tests
2. adjust translation-path resolution so managed artifacts overwrite same-key configured paths when the artifact exists
3. keep compatibility fallback behavior when no managed artifact exists

## Outcome

Result:

- found and fixed a correctness gap in translation runtime resolution authority
- managed translation artifacts now override stale same-key configured paths when present
- compatibility fallback behavior remains in place when no managed artifact exists
- the translation consumer seam now matches the managed-first authority already used by frequency and embedding resolution
