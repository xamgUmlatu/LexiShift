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

## 3) Pair Plumbing Across Surfaces

- [ ] GUI SRS pair controls include LP in `apps/gui/src/dialogs.py`.
- [ ] Bulk synonym pack-to-pair mapping handles LP in `apps/gui/src/main.py` (`_pair_for_pack`).
- [ ] Extension language-prefs path resolves LP correctly from source/target.
- [ ] No unintended pair collapsing occurs unless explicitly intended.
- [ ] Profile-scoped pair settings persist and reload correctly.

## 4) Rule Generation Implementation

- [ ] Rulegen path exists for LP (not placeholder/empty output).
- [ ] LP-specific source loader/pipeline is implemented in core rulegen modules.
- [ ] Generated rules carry `metadata.language_pair = <LP>`.
- [ ] Confidence/scoring behavior is defined (threshold, ranking, filters).
- [ ] Ambiguity/noise filters are applied (stopwords, punctuation, variant filtering as needed).

## 5) SRS Initialize And Refresh Support

- [ ] `srs_initialize` works for LP without unrelated hard dependencies.
- [ ] `srs_refresh` works for LP and can publish updated ruleset/snapshot.
- [ ] Pair-specific source defaults are configured in native-host command handling.
- [ ] Stopwords path resolution works for LP target language (if applicable).
- [ ] Pair-level planning path (`srs_plan_set`) returns executable plan where expected.

## 6) Runtime Integration

- [ ] Helper runtime diagnostics report LP paths/counts correctly.
- [ ] Extension runtime fetches and applies helper ruleset for LP.
- [ ] Gate/scheduler uses LP-scoped items only (no cross-pair leakage).
- [ ] Feedback/exposure events persist with correct LP key.

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
