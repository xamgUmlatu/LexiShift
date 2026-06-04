# E2 Frequency-Pack Holdout Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted helper/runtime frequency contract tests plus helper CLI help coverage
Purpose: bound the E2 slice around frequency-pack normalization holdouts so later E3-E4 work can separate true runtime defects from remaining path-shaped helper surfaces
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `data_source_normalization_execution_order.md`
- `feature_state_matrix.md`

## Slice

- Track: `E2`
- Slice: `E2.1`
- Title: frequency-pack tooling and diagnostics holdout audit
- Pass type: verification-first with narrow helper/help-text cleanup

## Exact Seam

Primary code surface:

- `core/lexishift_core/helper/use_cases/runtime_diagnostics.py`
- `core/lexishift_core/helper/lp_capabilities.py`
- `scripts/helper/lexishift_helper.py`
- `scripts/helper/lexishift_native_host.py`
- `scripts/helper/srs_admission_cli_support.py`

Primary tests/evidence surface:

- `core/tests/dev/test_frequency_runtime_contracts.py`
- `core/tests/dev/test_helper_frequency_entrypoints.py`
- `core/tests/helper/test_frequency_packs.py`

Primary contract/docs surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

## Explicitly Out Of Scope

This slice does not directly review:

- settings/runtime managed-id authority already covered in `SP1.8`
- translation-pack follow-through already covered in `E1`
- embedding pack follow-through reserved for `E3`
- broader installed-vs-manual wording work reserved for `E4`
- renaming execution-layer `set_source_db` fields inside helper jobs and native-host payloads

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- managed frequency resolution was already stronger than the remaining helper wording suggested, so the main risk was contract drift rather than an obvious live failure
- runtime diagnostics are a cross-layer join point, which makes explicit evidence more valuable than inference from lower-level pack tests alone
- the helper CLI still presented raw SQLite overrides without saying they were compatibility/manual inputs layered on top of installed-pack defaults

## Contract Sketch

The intended frequency-pack contract after the SP1 resolution work is:

1. managed frequency installs resolve by pack identity and manifest before legacy flat filename fallback
2. helper CLI and native-host default resolution should inherit that same managed-first contract
3. runtime diagnostics should report the resolved frequency artifact plus pack identity/provider/profile coherently
4. legacy flat `freq-*.sqlite` files remain compatibility fallback inputs, not the primary managed contract
5. developer-facing helper help text should describe raw frequency paths as manual overrides, not as the normal managed path

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper CLI default resource resolution chooses manifest-backed frequency artifacts when installed. | `_resolve_pair_resource_paths(...)` in `lexishift_helper.py` | `core/tests/dev/test_frequency_runtime_contracts.py` | `verified for this slice` |
| Native-host default resource resolution chooses manifest-backed frequency artifacts when installed. | `_resolve_pair_resource_paths(...)` in `lexishift_native_host.py` | `core/tests/dev/test_frequency_runtime_contracts.py` | `verified for this slice` |
| Helper CLI and native-host default resource resolution still fall back to legacy flat frequency filenames when no manifest-backed install exists. | `_resolve_pair_resource_paths(...)` in helper/native-host entrypoints | `core/tests/dev/test_frequency_runtime_contracts.py` | `verified for this slice` |
| Runtime diagnostics report manifest-backed frequency artifact path plus pack identity/provider/profile coherently. | `get_srs_runtime_diagnostics(...)` | `core/tests/dev/test_frequency_runtime_contracts.py` | `verified for this slice` |
| Helper CLI subcommands now describe `--set-source-db` as a manual override on top of installed frequency-pack defaults. | `build_parser(...)`, `register_srs_preview_and_rebalance_commands(...)` | `core/tests/dev/test_helper_frequency_entrypoints.py` | `fixed and verified in this slice` |

## Invariants

1. managed frequency-pack manifests win when installed artifacts exist
2. helper/default entrypoints inherit the same managed-first contract as the lower-level resolver
3. legacy flat frequency SQLite files remain valid compatibility fallbacks
4. runtime diagnostics expose both the raw execution path and the normalized frequency-pack identity
5. helper/help surfaces should not imply that raw frequency SQLite paths are the primary managed contract

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Managed manifest-backed frequency install present | helper CLI, native host, and runtime diagnostics all resolve the same `main.sqlite` artifact and same pack identity |
| Only legacy flat frequency file present | helper CLI and native host still resolve the fallback `freq-*.sqlite` file |
| Runtime diagnostics for managed install | `set_source_db`, `frequency_pack_path`, and frequency pack identity/provider/profile remain coherent |
| Helper CLI help text | `--set-source-db` is framed as a manual override, not the default contract |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_frequency_runtime_contracts.py core/tests/dev/test_helper_frequency_entrypoints.py -q`
  - `python3 -m pytest core/tests/helper/test_frequency_packs.py -q`

## Planned Action For This Slice

1. add seam-local regression coverage for helper/native-host default frequency resolution and runtime diagnostics under managed installs plus legacy fallback
2. narrow helper CLI help text so the raw frequency path override is clearly manual/compatibility-oriented
3. record any remaining path-first helper API holdouts separately instead of expanding this slice into a broader rename

## Outcome

Result:

- no runtime correctness defect was found in the frequency-pack resolution seam
- helper entrypoints, native-host defaults, and runtime diagnostics now have direct shared evidence for managed-first frequency-pack resolution plus legacy-flat fallback
- helper CLI copy now matches the installed-pack-first contract already established by the lower-level resolver
- one broader holdout remains outside this slice: execution-layer helper/native-host APIs still use the path-first `set_source_db` field name, so that follow-up was logged instead of being mixed into a wider rename during E2
