# SP1 Secondary Lexical Runtime Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-21
Last verified: 2026-04-21 targeted bulk-rules, persistence, and doc-state checks
Purpose: bound the SP1 follow-up seam around `wordnet-en` / `moby-en` runtime-consumer drift so these two packs remain explicit compatibility exceptions while downstream GUI logic resolves them through one shared effective-path contract
Source-of-truth: packet only; executable truth still lives in code, tests, and current state/docs
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `project_integrity_sp1_secondary_language_resources_packet.md`
- `feature_state_matrix.md`
- `data_source_normalization_execution_order.md`
- `../reference/schema.md`

## Slice

- Track: `SP1`
- Slice: `SP1.6`
- Title: secondary lexical runtime-consumer reconciliation
- Pass type: narrow compatibility-contract follow-through

## Exact Seam

Primary code surface:

- `core/lexishift_core/persistence/settings.py`
- `apps/gui/src/main_bulk_rules_mixin.py`

Primary tests/evidence surface:

- `core/tests/persistence/test_settings.py`
- `apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py`
- `apps/gui/tests/test_language_pack_panel_state_mixin.py`
- `apps/gui/tests/test_main_settings_resource_persistence.py`

Primary docs/state surface:

- `docs/developer/data_source_normalization_execution_order.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/reference/schema.md`

## Explicitly Out Of Scope

This slice does not directly review:

- promotion of the whole secondary lexical family into the managed-pack model
- removal of the persisted `wordnet_dir` / `moby_path` schema fields
- semantic/pedagogical quality of WordNet or Moby
- broader secondary-pack decisions for `openthesaurus-de`, `odenet-de`, `jp-wordnet`, `jmdict-ja-en`, or `cc-cedict-zh-en`

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `medium-high`

Reasoning:

- the panel/persistence seam already had explicit precedence coverage, but bulk synonym generation was still reading the legacy dedicated fields directly
- that meant a future cleanup could update the shared binding/manual-path map correctly while a downstream consumer quietly kept following the older aliases

## Contract Sketch

The intended current contract is:

1. `wordnet-en` and `moby-en` remain explicit compatibility exceptions inside `SynonymSourceSettings`
2. the effective runtime path for those two packs is resolved from one shared helper:
   - prefer `language_pack_paths` entries when present
   - fall back to legacy `wordnet_dir` / `moby_path` only when the shared map is absent
3. downstream consumers should use that helper instead of reading the legacy fields directly
4. this slice does not claim those two packs are now first-class normalized managed packs

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Panel state and dialog persistence already treat `wordnet-en` / `moby-en` as shared binding-map entries with legacy-field fallback. | panel-state and dialog persistence | existing GUI tests from `SP1.5` | `verified before this slice` |
| Bulk synonym expansion was still reading `settings.wordnet_dir` / `settings.moby_path` directly instead of the binding-map-first effective path contract. | `main_bulk_rules_mixin.py` | direct code inspection before this slice | `verified before this slice` |
| A shared effective-path helper now keeps runtime consumers aligned with the same precedence contract used by panel state. | `settings.py`, `main_bulk_rules_mixin.py` | new persistence and bulk-rules tests | `fixed in this slice` |
| Docs now state that these two sources are explicit compatibility exceptions rather than stealth members of a normalized managed-pack family. | data-source normalization docs and state ledger | direct doc update in this slice | `fixed in this slice` |

## Invariants

1. `wordnet-en` and `moby-en` remain manual/compatibility secondary resources, not managed pack ids
2. shared `language_pack_paths` entries win over stale legacy fields
3. downstream runtime consumers should not invent their own precedence rules for these two packs
4. later family-wide promotion still requires an explicit product/runtime decision

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| Legacy-only settings | runtime can still resolve `wordnet-en` / `moby-en` through `wordnet_dir` / `moby_path` |
| Binding-map-first settings | runtime prefers `language_pack_paths["wordnet-en"]` / `language_pack_paths["moby-en"]` |
| Bulk synonym defaults | `wordnet-en` / `moby-en` are selected when only the binding-map entries exist |
| Future cleanup reads the docs | these two packs are clearly documented as compatibility exceptions, not normalized managed family members |

## Validation Floor

- `PYTHONPATH=/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src:/Users/takeyayuki/Documents/projects/LexiShift/core python3 -m pytest apps/gui/tests/test_main_bulk_rules_translation_pack_resolution.py apps/gui/tests/test_language_pack_panel_state_mixin.py apps/gui/tests/test_main_settings_resource_persistence.py core/tests/persistence/test_settings.py -q`
- `python3 scripts/dev/check_doc_references.py`
- `git diff --check`
- `npm --prefix scripts run check:state`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. add one shared effective-path helper for `wordnet-en` / `moby-en`
2. switch bulk-rules synonym generation/default-selection logic to that helper
3. close the note by documenting these two packs as compatibility exceptions instead of leaving the runtime-consumer choice implicit

## Outcome

Result:

- `wordnet-en` and `moby-en` still remain explicit compatibility aliases in settings schema and docs
- the practical drift risk is lower because runtime bulk-rules logic now follows the same binding-map-first contract as the panel and dialog layers
- the broader secondary lexical family promotion question remains separate instead of being quietly answered by ad hoc consumer behavior
