# SP1 Secondary Language Resources Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-18
Last verified: 2026-04-18 targeted panel-state and persistence tests for `wordnet-en` / `moby-en` compatibility
Purpose: bound the fifth SP1 slice around the remaining dedicated secondary lexical resource settings so future cleanup can rely on an explicit compatibility contract instead of inferred behavior
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.5`
- Title: secondary language-resource compatibility
- Pass type: verification-first with precedence and round-trip coverage

## Exact Seam

Primary code surface:

- `apps/gui/src/settings_language_packs_panel_state_mixin.py`
- `apps/gui/src/settings_language_packs_support.py`
- `apps/gui/src/dialogs.py`

Primary tests/evidence surface:

- `apps/gui/tests/test_language_pack_panel_state_mixin.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`
- `apps/gui/tests/test_language_pack_table_mixin.py`

Primary contract/docs surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/feature_state_matrix.md`
- `docs/reference/schema.md`

## Explicitly Out Of Scope

This slice does not directly review:

- whether `wordnet-en` / `moby-en` should remain product features long-term
- broader secondary lexical pack normalization for `openthesaurus-de`, `odenet-de`, `jp-wordnet`, `jmdict-ja-en`, or `cc-cedict-zh-en`
- semantic quality or pedagogical value of the underlying WordNet/Moby resources
- downstream runtime-family unification beyond the settings compatibility contract consumed today

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- these two sources still bridge the old dedicated-field shape and the newer shared binding map
- if precedence or round-trip behavior drifts, later UX cleanup can silently overwrite or drop a user-selected resource
- the current behavior is transitional, so the main risk is not obvious breakage but accidental contract drift during future cleanup

## Contract Sketch

The intended compatibility contract for `wordnet-en` and `moby-en` is:

1. in panel state they behave as manual secondary language-resource bindings
2. legacy `wordnet_dir` / `moby_path` fields still seed those bindings when older settings are loaded
3. if both the dedicated legacy field and the shared `language_pack_paths` entry exist, the shared binding-map entry wins
4. dialog persistence derives both `language_pack_paths` and the dedicated `wordnet_dir` / `moby_path` fields from the same manual binding state
5. this duplication is transitional compatibility, not evidence that these packs are already normalized like translation/frequency/embedding managed packs

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Legacy dedicated `wordnet_dir` / `moby_path` values should seed manual secondary bindings when no shared binding entry exists. | `LanguagePackPanelStateMixin._seed_language_pack_paths(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified for this slice` |
| Shared `language_pack_paths` secondary entries should take precedence over stale dedicated legacy fields when both are present. | `LanguagePackPanelStateMixin._seed_language_pack_paths(...)` | `apps/gui/tests/test_language_pack_panel_state_mixin.py` | `verified for this slice` |
| Dialog persistence should round-trip both secondary bindings back into `language_pack_paths` plus the dedicated `wordnet_dir` / `moby_path` compatibility fields. | `build_synonym_resource_settings_from_panel(...)`, `split_language_resource_bindings(...)` | `apps/gui/tests/test_main_settings_resource_persistence.py` | `verified for this slice` |
| Secondary manual rows should remain visibly manual in the language-pack table. | `LanguagePackPanel._refresh_language_pack_table(...)` | `apps/gui/tests/test_language_pack_table_mixin.py` | `already verified before this slice` |

## Invariants

1. `wordnet-en` and `moby-en` never collapse into managed language-pack ids
2. legacy dedicated fields can still hydrate manual secondary binding state
3. explicit binding-map/manual-path entries win over older dedicated-field values when both are present
4. persistence rebuilds `wordnet_dir` and `moby_path` from the same manual binding state it stores in `language_pack_paths`
5. the panel and persistence layers agree on the same effective path for each secondary resource after round-trip

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Legacy-only settings | `wordnet_dir` / `moby_path` seed manual secondary bindings even without `language_pack_paths` entries |
| Mixed legacy + binding-map settings | shared `language_pack_paths` values win over stale dedicated fields |
| Panel persistence | manual secondary bindings serialize back into both `language_pack_paths` and dedicated compatibility fields |
| Table rendering | active secondary binding remains labeled as manual rather than installed/managed |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_language_pack_panel_state_mixin.py apps/gui/tests/test_main_settings_resource_persistence.py apps/gui/tests/test_language_pack_table_mixin.py -q`

## Planned Action For This Slice

1. pin legacy-field seeding and precedence behavior with focused panel-state tests
2. pin persistence behavior for both secondary bindings, not just `wordnet-en`
3. log any broader secondary-family contract issues that do not belong to this narrow slice

## Outcome

Result:

- no correctness defect found in the `wordnet-en` / `moby-en` compatibility seam
- the current behavior is deliberate but transitional: panel state is binding-map-first, while downstream compatibility still expects `wordnet_dir` / `moby_path`
- evidence is now explicit for legacy-field seeding, binding-map precedence, and persistence round-trip
- one broader follow-up was logged in `project_integrity_secondary_pass_notes.md` so the dedicated-field exception does not get lost during later normalization work
