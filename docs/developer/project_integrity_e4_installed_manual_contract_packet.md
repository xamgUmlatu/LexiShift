# E4 Installed-vs-Manual Contract Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted helper CLI help tests plus existing GUI/settings contract tests
Purpose: bound the E4 slice around the remaining installed-vs-manual contract language so helper/UI copy stays aligned with the managed-pack-first settings/runtime model
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_stabilization_backlog.md`
- `data_source_normalization_execution_order.md`
- `feature_state_matrix.md`

## Slice

- Track: `E4`
- Slice: `E4.1`
- Title: installed-vs-manual UI contract cleanup
- Pass type: verification-first with narrow helper copy correction

## Exact Seam

Primary code surface:

- `scripts/helper/lexishift_helper.py`
- `scripts/helper/srs_admission_cli_support.py`

Primary tests/evidence surface:

- `core/tests/dev/test_helper_translation_dict_entrypoints.py`
- `core/tests/dev/test_helper_frequency_entrypoints.py`
- `core/tests/dev/test_rulegen_benchmark_cli.py`
- `apps/gui/tests/test_settings_resources_tab.py`
- `apps/gui/tests/test_language_pack_table_mixin.py`

Primary contract/docs surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/developer/project_integrity_secondary_pass_plan.md`

## Explicitly Out Of Scope

This slice does not directly review:

- execution-layer field renames such as `set_source_db`
- the path-shaped `rulegen_probe_words.py` developer surface already logged in `N-008`
- extension/controller formatter copy in dirty SRS action files
- any further managed-pack resolution changes in runtime/settings code

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the underlying managed-pack behavior was already largely correct, but copy drift can still teach the wrong contract to users and future maintainers
- the seam is user-facing and cross-surface, so inconsistencies tend to survive unless they are checked deliberately
- recent E1-E3 work reduced behavioral risk enough that the remaining value here came from making the visible contract uniformly explicit

## Contract Sketch

The intended installed-vs-manual contract after the normalization work is:

1. installed app-managed language, frequency, and embedding packs are the default product path
2. manual translation dictionaries, frequency databases, and embedding files remain explicit compatibility/import overrides
3. GUI/settings surfaces should label installed vs manual state directly instead of implying generic path selection is normal
4. helper CLI flags that accept raw paths should describe those inputs as manual overrides layered on top of installed-pack defaults
5. lower-level path-shaped execution fields may still exist temporarily, but they should not be overread as the canonical managed-resource contract

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper translation-dictionary flags describe manual overrides on top of installed language-pack defaults. | `build_parser(...)`, `register_srs_preview_and_rebalance_commands(...)` | `core/tests/dev/test_helper_translation_dict_entrypoints.py` | `fixed and verified in this slice` |
| Helper frequency override flags describe manual overrides on top of installed frequency-pack defaults. | `build_parser(...)`, `register_srs_preview_and_rebalance_commands(...)` | `core/tests/dev/test_helper_frequency_entrypoints.py` | `verified for this slice` |
| Benchmark CLI help describes installed language/frequency packs as the default contract. | `rulegen_benchmark.py` help surface | `core/tests/dev/test_rulegen_benchmark_cli.py` | `verified for this slice` |
| Settings/resources descriptions tell users to prefer installed packs and keep manual paths for compatibility/import scenarios. | settings dialog/resource tabs | `apps/gui/tests/test_settings_resources_tab.py` | `verified for this slice` |
| Resource tables distinguish installed managed artifacts from manual/external paths. | language/frequency/embedding table rendering | `apps/gui/tests/test_language_pack_table_mixin.py` | `verified for this slice` |

## Invariants

1. managed installed packs remain the default visible contract
2. manual path inputs are framed as compatibility/import overrides rather than the primary UX
3. helper, benchmark, and settings surfaces should agree on the installed-vs-manual story
4. installed/manual status labels should stay explicit in the resource tables
5. any remaining path-first diagnostics fields should be treated as transitional execution detail, not the user-facing source of truth

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Helper `run_rulegen` / SRS CLI help | translation and frequency path flags describe manual overrides with installed-pack defaults |
| Benchmark CLI help | installed language and frequency packs are named as the default path |
| Settings resources tab | descriptions explicitly prefer installed packs and describe manual paths as compatibility/import surfaces |
| Resource table status | managed rows show `Installed` / `Active (Installed)` while external paths show `Manual` / `Active (Manual)` |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/dev/test_helper_translation_dict_entrypoints.py core/tests/dev/test_helper_frequency_entrypoints.py core/tests/dev/test_rulegen_benchmark_cli.py -q`
  - `PYTHONPATH=apps/gui/src:core python3 -m pytest apps/gui/tests/test_settings_resources_tab.py apps/gui/tests/test_language_pack_table_mixin.py -q`

## Planned Action For This Slice

1. verify whether the visible installed-vs-manual story is already consistent across benchmark, helper, and GUI surfaces
2. correct any remaining helper/UI wording that still presents raw path inputs without the installed-default framing
3. log narrower diagnostics-only holdouts instead of widening this slice into extension/controller refactors

## Outcome

Result:

- the core managed-resource behavior was already consistent across benchmark and GUI/settings surfaces
- the main lagging surface was helper translation-dictionary help text, which now clearly states that installed language packs are the default and raw translation paths are manual overrides
- existing GUI/status and benchmark evidence already matched the intended contract, so E4 stayed narrow rather than reopening runtime or settings logic
- one smaller holdout remains logged for later work: extension-side SRS diagnostics still expose raw `set_source_db` lines without the same installed-default framing
