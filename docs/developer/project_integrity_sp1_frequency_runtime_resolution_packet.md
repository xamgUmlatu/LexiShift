# SP1 Frequency Runtime Resolution Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted frequency helper and SRS consumer tests
Purpose: bound the eighth SP1 slice around frequency runtime resolution authority so the SRS consumer path is explicitly verified to honor the same managed-first contract as the resource settings layer
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.8`
- Title: frequency runtime resolution authority
- Pass type: verification-first with helper and SRS consumer precedence coverage

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/frequency_packs.py`
- `apps/gui/src/main_srs_mixin.py`

Primary tests/evidence surface:

- `core/tests/helper/test_frequency_packs.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`
- `apps/gui/tests/test_state_resource_settings_migration.py`

Primary contract/docs surface:

- `docs/developer/feature_state_matrix.md`
- `docs/developer/data_source_normalization_execution_order.md`
- `docs/reference/schema.md`

## Explicitly Out Of Scope

This slice does not directly review:

- translation runtime resolution already handled in `SP1.7`
- embedding runtime resolution already handled in `SP1.6`
- SRS growth/admission semantics after a frequency artifact path has already been resolved
- frequency data quality or POS-profile semantics beyond artifact identity and authority order

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- this seam feeds SRS growth, so a silent authority-order bug here could make the SRS path consume a stale file while the settings surface still looks correct
- the helper already appears managed-first, but that behavior was not explicitly pinned for same-key precedence and compatibility fallback
- this is exactly the kind of state-to-runtime seam that benefits from a narrow verification packet

## Contract Sketch

The intended frequency runtime resolution contract is:

1. managed frequency pack ids resolve to manifest-backed installed artifacts when available
2. a stale configured path under the same frequency pack key must not override a present managed artifact
3. if the managed artifact is absent, the configured path remains a compatibility fallback
4. the SRS consumer path should inherit the same authority order as the helper resolver it delegates to
5. state migration should still strip stale managed artifact paths from saved settings before normal runtime resolution where possible

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Managed frequency pack ids resolve to manifest-backed installed artifacts. | `resolve_configured_frequency_pack(...)`, `MainWindow._resolve_frequency_pack_for_pair(...)` | `core/tests/helper/test_frequency_packs.py`, `apps/gui/tests/test_main_settings_resource_persistence.py` | `verified for this slice` |
| A same-key configured manual path does not override a present managed frequency artifact. | `resolve_configured_frequency_pack(...)`, `MainWindow._resolve_frequency_pack_for_pair(...)` | `core/tests/helper/test_frequency_packs.py`, `apps/gui/tests/test_main_settings_resource_persistence.py` | `verified for this slice` |
| A configured path remains a compatibility fallback when the managed artifact is absent. | `resolve_configured_frequency_pack(...)`, `MainWindow._resolve_frequency_pack_for_pair(...)` | `core/tests/helper/test_frequency_packs.py`, `apps/gui/tests/test_main_settings_resource_persistence.py` | `verified for this slice` |
| State migration still removes stale managed frequency artifact paths from saved settings. | `AppState._normalize_resource_settings(...)` | `apps/gui/tests/test_state_resource_settings_migration.py` | `already verified before this slice` |

## Invariants

1. managed frequency pack ids are authoritative when a managed artifact exists
2. stale same-key configured paths cannot shadow a present managed frequency artifact
3. configured frequency paths remain available as compatibility fallbacks when the managed artifact is missing
4. the SRS consumer path agrees with the helper-level authority order
5. runtime resolution stays aligned with the pack-id-first settings contract established in earlier SP1 slices

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed frequency pack present | managed id resolves to installed artifact |
| Managed pack present plus same-key configured path | installed artifact still wins |
| Managed pack missing but configured path present | configured path remains available as fallback |
| Migrated settings | stale managed artifact paths are removed before normal runtime resolution |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/helper/test_frequency_packs.py -q`
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_settings_resource_persistence.py apps/gui/tests/test_state_resource_settings_migration.py -q`

## Planned Action For This Slice

1. add helper-level same-key precedence and fallback tests for frequency resolution
2. add SRS consumer tests so `_resolve_frequency_pack_for_pair(...)` is covered by the same authority scenarios
3. keep behavior unchanged unless those tests expose a real defect

## Outcome

Result:

- no correctness defect found in the frequency runtime resolution seam
- helper and SRS consumer paths now have explicit evidence for managed-first authority and compatibility fallback
- this brings the frequency consumer seam up to the same evidence level as the embedding and translation runtime slices
