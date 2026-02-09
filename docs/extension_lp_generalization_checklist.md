# Extension LP Generalization Checklist

Purpose:
- Generalize SRS behavior for the Chrome extension so it works with the selected LP (Language Pair), not just `en-ja`.
- Keep scope limited to extension + helper + core SRS/rulegen paths.
- BetterDiscord plugin is explicitly out of scope for this checklist.

Architecture contract:
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/srs_lp_architecture.md`

Status baseline (current):
- Extension UI resolves LP dynamically from source/target language inputs.
- Helper SRS bootstrap/rulegen paths use LP capabilities for requirement resolution.
- Pair-specific rulegen is implemented for `en-ja` and `en-de`.

## 1) LP Strategy And Direction Policy

- [ ] Decide LP direction policy for SRS/runtime:
  - [ ] Directional keys (`en-de` distinct from `de-en`).
  - [ ] Canonicalized keys (normalize both into one key).
- [ ] Document the policy in LP docs and enforce it in mapping functions.
- [ ] Ensure pack-to-pair mapping and runtime pair filtering use the same policy.

## 2) Data Source Matrix (Required Inputs)

Use this matrix to determine what must exist before a pair can be marked implemented.

| LP | Rule source(s) | Bootstrap/growth frequency source | Stopwords file | Current status |
| --- | --- | --- | --- | --- |
| `en-ja` | JMDict | BCCWJ (`freq-ja-bccwj`) | `stopwords-ja.json` (optional fallback search path) | Partial/implemented |
| `de-en` | FreeDict (`freedict-de-en`) | English frequency (`freq-en-coca`) | `stopwords-en.json` (optional) | Data mostly available, pipeline missing |
| `en-de` | FreeDict (`freedict-en-de`) | German frequency pack (missing today) | `stopwords-de.json` (missing) | Blocked by missing frequency + pipeline |
| `en-en` | WordNet, Moby | English frequency (`freq-en-coca`) | `stopwords-en.json` (optional) | Data available, SRS pipeline missing |
| `de-de` | OdeNet, OpenThesaurus | German frequency pack (missing today) | `stopwords-de.json` (missing) | Blocked by missing frequency + pipeline |
| `ja-ja` | JP WordNet (tab/sqlite) | BCCWJ (`freq-ja-bccwj`) | `stopwords-ja.json` (optional fallback search path) | Data mostly available, SRS pipeline missing |
| `en-zh` | CC-CEDICT | Chinese frequency pack (missing today) | `stopwords-zh.json` (missing) | Blocked by missing frequency + pipeline |

Checklist for each LP row:
- [ ] Dictionary source is downloadable/linkable in language pack manager.
- [ ] Frequency pack exists and converts to SQLite.
- [ ] Seed selection can validate/normalize target lemmas for LP.
- [ ] Rulegen emits non-empty rules for valid targets.

## 3) Pair-Aware Source Resolution (Helper)

- [ ] Replace global defaults (`JMdict_e`, `freq-ja-bccwj.sqlite`) with pair-aware resolution.
- [ ] Add pair capability checks before initialize/refresh/rulegen.
- [ ] Return clear, pair-specific errors for missing source files.
- [ ] Ensure non-`en-ja` pairs do not fail due to unrelated JMDict checks.

## 4) Rulegen Coverage By LP

- [ ] Keep existing `en-ja` path as reference implementation.
- [ ] Add pair-specific rulegen adapters for new LPs (or a generic adapter when feasible).
- [ ] Verify output orientation is correct (`source_phrase` language vs `replacement` language).
- [ ] Persist `metadata.language_pair` consistently for all generated rules.

## 5) SRS Initialize/Refresh Generalization

- [ ] `srs_initialize` supports selected LP with LP-specific sources.
- [ ] `srs_refresh` supports selected LP with LP-specific candidate pool.
- [ ] Growth/admission uses LP-scoped inputs only.
- [ ] Runtime publish writes LP-specific ruleset/snapshot artifacts.

## 6) Extension Runtime And Options

- [ ] Confirm options always pass selected LP in helper requests.
- [ ] Confirm content script fetches helper rules by selected LP + profile.
- [ ] Add capability indicator in options for LP readiness (`ready`, `missing sources`, `unsupported`).
- [ ] Prevent initialize/refresh actions when LP requirements are unmet.

## 7) Testing (Extension-Focused)

- [ ] Unit tests:
  - [ ] LP mapping and direction normalization.
  - [ ] Pair-aware source resolution.
  - [ ] Rule orientation per LP.
- [ ] Integration tests:
  - [ ] initialize -> publish -> extension fetch for LP.
  - [ ] feedback -> refresh -> publish for LP.
  - [ ] diagnostics counts for selected LP.
- [ ] Regression tests:
  - [ ] Existing `en-ja` behavior unchanged.

## 8) Docs And Operational Readiness

- [ ] Keep `docs/language_pair_setup_checklist.md` as the generic template.
- [ ] Update `docs/dictionary_matrix_checklist.md` with implemented LPs and blockers.
- [ ] Update README capability matrix with extension-supported LPs.
- [ ] Record migration notes when LP direction policy changes.

## 9) Definition Of Done (Extension LP)

- [ ] User selects LP in extension options and it persists.
- [ ] Initialize succeeds for LP with valid configured sources.
- [ ] Refresh succeeds and can publish new LP rules.
- [ ] Content script applies helper LP rules for selected profile.
- [ ] Diagnostics show non-zero LP counts after bootstrap.
- [ ] Tests pass for LP path and `en-ja` regression suite.

## Immediate Work Queue (Recommended Order)

- [ ] Introduce pair capability/source registry used by helper commands.
- [ ] Remove unconditional JMDict requirement from non-`en-ja` paths.
- [ ] Implement `de-en` first (it can reuse existing EN frequency pack).
- [ ] Add extension-side LP readiness messaging using helper diagnostics.
- [ ] Add German frequency pack to unlock `en-de` and `de-de`.
