# Language Pair Setup Checklist

Purpose:
- Provide a formal, reusable checklist for implementing a new LP (Language Pair) end-to-end.
- Keep implementation work consistent across GUI, extension, helper, core rulegen, and SRS.

Scope:
- LP means `source-target` key (examples: `en-ja`, `en-de`, `de-en`, `ja-ja`).
- This checklist covers setup for both synonym generation and SRS-backed runtime usage.

Related:
- Core LP architecture contract: `docs/architecture/srs_lp_architecture.md`.
- For extension + helper focused rollout sequencing, see `docs/language_pairs/extension_lp_generalization_checklist.md`.

## 0) Implementation Sequence (Use This Order Every Time)

1. Register LP capability and defaults.
   - Edit: `core/lexishift_core/helper/lp_capabilities.py`
   - Check fallback/resource logic: `core/lexishift_core/helper/pair_resources.py`
   - Validate requirement checks: `core/lexishift_core/helper/engine.py`
2. Register packs and conversion path.
   - Edit pack catalog: `apps/gui/src/language_packs.py`
   - Record source URLs/notes: `docs/language_pairs/language_pack_urls.txt`
   - Add/verify converter scripts: `scripts/data/` (for example `convert_*_to_sqlite.py`)
3. Implement rulegen support for LP.
   - Register adapter mode: `core/lexishift_core/rulegen/adapters.py`
   - Add pair pipeline: `core/lexishift_core/rulegen/pairs/<pair>.py`
   - Add shared morphology/normalization helpers if needed: `core/lexishift_core/rulegen/utils.py`
   - Add dictionary loader updates for new formats: `core/lexishift_core/resources/dict_loaders.py`
4. Ensure SRS init/refresh assumptions are LP-safe.
   - Seed/frequency behavior: `core/lexishift_core/srs/seed.py`
   - Frequency column fallback behavior: `core/lexishift_core/frequency/providers.py`
   - Rulegen publish orchestration: `core/lexishift_core/helper/rulegen.py`
5. Wire GUI + extension pair plumbing.
   - GUI selectable pairs: `apps/gui/src/dialogs.py`
   - GUI pack->pair routing: `apps/gui/src/main.py` (`_pair_for_pack`)
   - Options action bindings: `apps/chrome-extension/options/controllers/page/events/srs_bindings.js`
   - Options helper workflows: `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
   - Runtime rendering for metadata-driven display (if needed): `apps/chrome-extension/content/processing/replacements.js`
6. Add targeted tests before merge.
   - Capability/resource tests: `core/tests/helper/test_lp_capabilities.py`, `core/tests/helper/test_helper_engine.py`, `core/tests/helper/test_helper_daemon.py`
   - Rulegen adapter tests: `core/tests/rulegen/test_rulegen_adapters.py`, `core/tests/helper/test_helper_rulegen.py`
   - Persistence/schema tests (if metadata changes): `core/tests/persistence/test_storage.py`
7. Update docs and rollout status.
   - LP requirements matrix: `docs/language_pairs/lp_resource_requirements.md`
   - Extension LP checklist status: `docs/language_pairs/extension_lp_generalization_checklist.md`
   - SRS roadmap snapshot: `docs/srs/srs_roadmap.md`
   - Changelog: `CHANGELOG.md`

## LP Definition

- [ ] LP key is defined as `source-target` (directional), for example `en-de`.
- [ ] LP direction policy is explicitly decided and documented:
  - [ ] Directional (`en-de` is distinct from `de-en`), or
  - [ ] Canonicalized (multiple directions normalized to one key).
- [ ] LP is added/verified in glossary terminology (`LP = Language Pair`).

## 1) Planning And Source Selection

- [ ] Target use-case is identified:
  - [ ] Monolingual synonym LP (for example `de-de`), or
  - [ ] Cross-lingual translation LP (for example `en-de`).
- [ ] Dictionary sources selected:
  - [ ] Primary source
  - [ ] Secondary source (optional)
- [ ] Frequency source selected for SRS bootstrap/growth.
- [ ] Required files and formats are documented (CSV/TSV/XML/SQLite/etc).
- [ ] Licensing and redistribution constraints are confirmed.

## 2) Pack Registration And Validation

- [ ] Dictionary pack(s) are registered in `apps/gui/src/language_packs.py`.
- [ ] Required extracted files are declared (`required_files`) where applicable.
- [ ] Download/extract/link validation works from Settings -> App.
- [ ] Frequency pack is registered if SRS bootstrap depends on it.
- [ ] Optional embedding packs are mapped to the LP if ranking is required.
- [ ] Converter script exists for non-native formats and is documented in:
  - `scripts/data/`
  - `docs/language_pairs/language_pack_urls.txt`

## 3) Pair Plumbing Across Surfaces

- [ ] GUI SRS pair controls include LP in `apps/gui/src/dialogs.py`.
- [ ] Bulk synonym pack-to-pair mapping handles LP in `apps/gui/src/main.py` (`_pair_for_pack`).
- [ ] Extension language-prefs path resolves LP correctly from source/target.
- [ ] No unintended pair collapsing occurs unless explicitly intended.
- [ ] Profile-scoped pair settings persist and reload correctly.
- [ ] Helper capability + pair resource resolution matches GUI/extension pair expectations:
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/helper/pair_resources.py`

## 4) Rule Generation Implementation

- [ ] Rulegen path exists for LP (not placeholder/empty output).
- [ ] LP-specific source loader/pipeline is implemented in core rulegen modules.
- [ ] Generated rules carry `metadata.language_pair = <LP>`.
- [ ] Confidence/scoring behavior is defined (threshold, ranking, filters).
- [ ] Ambiguity/noise filters are applied (stopwords, punctuation, variant filtering as needed).
- [ ] Adapter registration and pair mode routing are wired:
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/helper/lp_capabilities.py` (`rulegen_mode`)
- [ ] If LP needs morphology-aware rendering, metadata contract is implemented and persisted:
  - generation: `core/lexishift_core/rulegen/generation.py`
  - variant expansion: `core/lexishift_core/rulegen/utils.py`
  - persistence: `core/lexishift_core/persistence/storage.py`

## 5) SRS Initialize And Refresh Support

- [ ] `srs_initialize` works for LP without unrelated hard dependencies.
- [ ] `srs_refresh` works for LP and can publish updated ruleset/snapshot.
- [ ] Pair-specific source defaults are configured in native-host command handling.
- [ ] Stopwords path resolution works for LP target language (if applicable).
- [ ] Pair-level planning path (`srs_plan_set`) returns executable plan where expected.
- [ ] Seed/frequency assumptions are validated for LP frequency DB schema:
  - `core/lexishift_core/srs/seed.py`
  - `core/lexishift_core/frequency/providers.py`

## 6) Runtime Integration

- [ ] Helper runtime diagnostics report LP paths/counts correctly.
- [ ] Extension runtime fetches and applies helper ruleset for LP.
- [ ] Gate/scheduler uses LP-scoped items only (no cross-pair leakage).
- [ ] Feedback/exposure events persist with correct LP key.
- [ ] Runtime display behavior matches metadata contract (if used):
  - `apps/chrome-extension/content/processing/replacements.js`
  - `docs/reference/schema.md`

## 7) Background Automation (If Used)

- [ ] Helper daemon supports LP in its supported-pairs registry.
- [ ] Scheduled jobs have LP-appropriate input sources and defaults.
- [ ] Status reporting (`last_pair`, target/rule counts) reflects LP runs.

## 8) Testing Checklist

- [ ] Unit tests:
  - [ ] pack-to-pair mapping
  - [ ] source loader/parser for LP dictionaries
  - [ ] rulegen outputs for LP
- [ ] Integration tests:
  - [ ] initialize -> ruleset/snapshot published
  - [ ] feedback -> refresh admission behavior
  - [ ] diagnostics non-zero counts for LP after publish
- [ ] Runtime tests:
  - [ ] extension consumes LP rules
  - [ ] LP-specific gate behavior validated

## 9) Documentation Checklist

- [ ] Update `docs/language_pairs/dictionary_matrix_checklist.md` LP capability rows.
- [ ] Update README support matrix and known limitations.
- [ ] Update technical notes for pair mapping and rulegen behavior.
- [ ] Record migration notes if LP direction policy changed.

## 10) Definition Of Done (LP)

- [ ] LP can be selected in UI and persisted per profile.
- [ ] LP initialize path succeeds and publishes non-empty ruleset for valid inputs.
- [ ] LP refresh path can admit items and republish runtime artifacts.
- [ ] Runtime diagnostics show non-zero pair counts after initialization.
- [ ] Test suite includes LP coverage and passes.
- [ ] Documentation reflects LP as implemented (or explicitly partial).

## LP Rollout Record (Fill Per LP)

LP key: `________`

Owner: `________`

Date: `________`

Direction policy: `Directional | Canonicalized`

Primary dictionaries: `________`

Frequency source: `________`

Status: `Not started | In progress | Implemented | Partial`

Notes:
- `________`
