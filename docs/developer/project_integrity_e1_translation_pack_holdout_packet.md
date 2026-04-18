# E1 Translation-Pack Holdout Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted benchmark/runtime contract tests plus harness normalization coverage
Purpose: bound the E1 slice around translation-pack normalization holdouts so later E2-E4 work can distinguish real runtime mismatches from developer-facing compatibility wording
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `data_source_normalization_execution_order.md`
- `feature_state_matrix.md`

## Slice

- Track: `E1`
- Slice: `E1.1`
- Title: translation-pack tooling holdout audit
- Pass type: verification-first with narrow tooling-contract cleanup

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/pair_resources.py`
- `core/lexishift_core/helper/lp_capabilities.py`
- `scripts/testing/rulegen_benchmark_resources.py`
- `scripts/testing/rulegen_benchmark_reporting.py`
- `scripts/testing/srs_journey_harness_support.py`

Primary tests/evidence surface:

- `core/tests/dev/test_rulegen_resource_contracts.py`
- `core/tests/dev/test_rulegen_benchmark_cli.py`
- `core/tests/dev/test_rulegen_benchmark.py`
- `core/tests/dev/test_srs_harness_resource_normalization.py`
- `core/tests/helper/test_pair_resources.py`

Primary contract/docs surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- the frequency-pack follow-through reserved for `E2`
- embedding pack state/runtime cleanup reserved for `E3`
- installed-vs-manual settings copy and broader UX wording reserved for `E4`
- internal provider-shaped adapter field names inside rulegen pair configs
- the still-dirty `rulegen_probe_words.py` split, except to log the remaining holdout

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- translation-pack normalization already landed in runtime helpers and benchmark payloads, so the main remaining risk was false confidence from tooling copy and implied coverage
- if benchmark/help surfaces keep talking in filename-first terms, later UX and docs work can regress back toward the wrong contract even when runtime is already managed-first
- this seam is a good fit for a bounded pass because the likely outcome is evidence tightening plus small copy cleanup, not large behavior change

## Contract Sketch

The intended translation-pack contract after normalization is:

1. managed translation installs resolve by pack identity and manifest before filename fallback
2. benchmark resource resolution must agree with the shared helper/runtime translation-pack resolver on both path and pack identity
3. legacy flat SQLite filenames remain compatibility fallback inputs, not the primary managed contract
4. synthetic harness defaults for the covered translation pairs should stay SQLite-first so developer evidence matches product direction
5. developer-facing benchmark CLI copy should describe manual path flags as overrides, not as the canonical resource model

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Benchmark default translation resolution agrees with helper/runtime translation-pack resolution for manifest-backed installs. | `resolve_pair_translation_packs(...)`, `_resolve_pair_resources_for_benchmark(...)`, `_build_pair_resources_payload(...)` | `core/tests/dev/test_rulegen_resource_contracts.py` | `verified for this slice` |
| Benchmark default translation resolution agrees with helper/runtime translation-pack resolution for legacy flat SQLite defaults. | `resolve_pair_translation_packs(...)`, `_resolve_pair_resources_for_benchmark(...)`, `_build_pair_resources_payload(...)` | `core/tests/dev/test_rulegen_resource_contracts.py` | `verified for this slice` |
| Benchmark artifacts already report translation-pack identity directly instead of forcing filename inference. | `_build_pair_resources_payload(...)` | `core/tests/dev/test_rulegen_benchmark.py` | `already verified before this slice` |
| Covered synthetic SRS harness defaults remain SQLite-first rather than TEI-first. | `create_pair_resources(...)`, `build_pair_resources(...)` | `core/tests/dev/test_srs_harness_resource_normalization.py` | `already verified before this slice` |
| Benchmark CLI copy now frames raw path flags as manual overrides on top of installed-pack defaults. | `_build_parser(...)` in `rulegen_benchmark_reporting.py` | `core/tests/dev/test_rulegen_benchmark_cli.py` | `fixed and verified in this slice` |

## Invariants

1. managed translation-pack manifests win when installed artifacts exist
2. legacy flat SQLite files remain valid fallback inputs for tooling and local compatibility
3. benchmark resource payloads expose pack identity in a way that matches helper/runtime resolution
4. benchmark/help surfaces should not imply TEI or loose filename paths are the normal managed path
5. unresolved probe-side copy or output holdouts must stay explicit until they are cleaned up

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed manifest-backed installs present | benchmark resolution and helper/runtime pack refs choose the same `main.sqlite` artifacts and same pack ids |
| Only legacy flat SQLite defaults present | benchmark resolution and helper/runtime pack refs still agree on the same fallback files and derived pack ids |
| Benchmark JSON/reporting | resource payload carries translation-pack identity directly |
| Synthetic SRS harness | default translation fixtures stay SQLite-first for covered pairs |
| Benchmark CLI | manual override flags are described as compatibility overrides, not the primary contract |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_rulegen_benchmark_cli.py core/tests/dev/test_rulegen_resource_contracts.py core/tests/dev/test_srs_harness_resource_normalization.py -q`
  - `python3 -m pytest core/tests/dev/test_rulegen_benchmark.py core/tests/helper/test_pair_resources.py -q`

## Planned Action For This Slice

1. add seam-local regression coverage tying benchmark translation resolution to the shared helper/runtime contract for both managed and legacy defaults
2. narrow benchmark CLI help text so it reflects the installed-pack default and manual-override status of raw path flags
3. record any remaining probe/tooling holdouts separately instead of mixing them into unrelated refactors

## Outcome

Result:

- no runtime correctness defect was found in the benchmark/runtime translation-pack resolution seam
- benchmark resolution, benchmark resource payload identity, and helper/runtime translation-pack refs now have explicit shared evidence for both manifest-backed and legacy-flat defaults
- synthetic SRS harness coverage remains aligned with the SQLite-first managed direction for the covered translation pairs
- one developer-facing holdout remains outside this clean slice: `rulegen_probe_words.py` still carries a more path-shaped surface below the current split, so that follow-up was logged instead of being mixed into a dirty file during E1
