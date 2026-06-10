# Extension LP Generalization Checklist

Status: active mixed rollout checklist
Role: Mixed
Last updated: 2026-06-10
Last verified: 2026-06-10 en-ja advisory rulegen acceptance, SRS/runtime journey smoke, installed-resource journey smoke, and targeted SRS/extension/helper contract tests
Source-of-truth: mixed rollout checklist; current implementation truth lives in `docs/architecture/srs_lp_architecture.md`, helper/SRS/rulegen code, tests, and `docs/developer/feature_state_matrix.md`.

Purpose:
- Generalize SRS behavior for the Chrome extension so it works with the selected LP (Language Pair), not just `en-ja`.
- Keep scope limited to extension + helper + core SRS/rulegen paths.
- BetterDiscord plugin is explicitly out of scope for this checklist.

Architecture contract:
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/architecture/srs_lp_architecture.md`

Status baseline (current):
- Extension UI resolves LP dynamically from source/target language inputs.
- Helper SRS bootstrap/rulegen paths use LP capabilities for requirement resolution.
- Pair-specific rulegen is implemented for `en-ja`, `en-de`, `en-es`, and `es-en`.
- Learning Languages uses the source-stack registry for setup resources; `en-de`
  now exposes `freq-de-default`, `freq-en-leipzig-default`, `freedict-de-en`,
  `freedict-en-de`, and an explicit non-blocking semantic-reference pending
  row.
- Installed helper/resource smoke on 2026-06-08 verified active profile
  `suisui`, daemon pairs `en-de`/`en-es`, clean active status, and valid local
  SQLite artifacts for the required en-de resources.

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
| `en-ja` | JMDict | BCCWJ (`freq-ja-bccwj`) | `stopwords-ja.json` (optional fallback search path) | Advisory rulegen accepted for current stage; SRS/runtime and installed-resource smoke passed; semantic-veto breadth-stress gate passes; default-on and representative veto coverage pending |
| `de-en` | FreeDict (`freedict-en-de`) | English frequency (`freq-en-leipzig-default`; `freq-en-coca` fallback) | `stopwords-en.json` for target-side seed filtering (optional) | Baseline adapter implemented; benchmark/tuning still pending |
| `en-de` | FreeDict (`freedict-de-en`) plus reverse FreeDict (`freedict-en-de`) for reverse-check experiments | German frequency (`freq-de-default`) plus English source prior (`freq-en-leipzig-default`; `freq-en-coca` fallback) | `stopwords-de.json` (optional fallback exists) | Runtime/SRS beta implemented; installed smoke passed; scoped rulegen quality accepted for beta/advisory use; semantic reference pack pending |
| `en-es` | Wiktionary (`wiktionary-es-en`) primary; FreeDict (`freedict-es-en`) fallback | Spanish frequency (`freq-es-spalex-v1`) | `stopwords-es.json` (missing) | Implemented; CDE retired from runtime fallback |
| `es-en` | FreeDict (`freedict-en-es`) | English frequency (`freq-en-leipzig-default`; `freq-en-coca` fallback) | `stopwords-en.json` (optional) | Implemented baseline |
| `es-es` | Spanish monolingual source (TBD) | Spanish frequency (`freq-es-spalex-v1`) | `stopwords-es.json` (missing) | Missing monolingual adapter/source |
| `en-en` | WordNet, Moby | English frequency (`freq-en-leipzig-default`; `freq-en-coca` fallback) | `stopwords-en.json` (optional) | Data available, SRS pipeline missing |
| `de-de` | OdeNet, OpenThesaurus | German frequency (`freq-de-default`) | `stopwords-de.json` (optional fallback exists) | Frequency path is now available through the German target stack; monolingual adapter/source-ranking pipeline missing |
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

- [ ] Keep `docs/language_pairs/language_pair_setup_checklist.md` as the generic template.
- [ ] Update `docs/language_pairs/dictionary_matrix_checklist.md` with implemented LPs and blockers.
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

- [x] Introduce pair capability/source registry used by helper commands.
- [x] Remove unconditional JMDict requirement from non-`en-ja` paths.
- [x] Implement `de-en` first baseline adapter path (it can reuse existing EN frequency pack).
- [x] Add Learning Languages setup-resource readiness for `en-de` and `en-es`
      using the shared source-stack registry.
- [x] Add German frequency pack workflow to unlock `en-de` SRS/runtime beta.
- [x] Improve `en-de` rulegen quality enough for the scoped advisory gate to
      pass with the Leipzig top3-first preset.
- [x] Document that the current scoped `en-de` result is accepted for
      beta/advisory use while machine delta-baseline promotion remains separate.
- [ ] Decide later whether to promote an `en-de` machine delta baseline before
      using delta checks as a release signal.
- [ ] Generate/evaluate a real `en-de` semantic/veto reference pack before
      claiming semantic parity with `en-es`.
- [ ] Expand en-de topic coverage beyond the current limited supported-topic
      subset if product sampling needs broader preference coverage.
