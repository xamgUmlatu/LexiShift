# LexiShift

Purpose
- Replace words and phrases in text using a curated ruleset.
- Primary use case: full-text replacement (input text is already complete).
- Secondary (future) use case: live text stream replacement.

Design goals
- Deterministic, conservative behavior by default.
- Extensible architecture for GUI tooling and plugins/extensions later.
- Precompute static ruleset expansions (inflections, phrase variants) so runtime is fast.

Implemented features (current)
- Core replacement engine
  - Word/phrase tokenization with whitespace-preserving output.
  - Left-to-right longest-match replacement via trie.
  - Rule-level priority and case-policy handling.
  - Optional precomputed inflection expansion and meaning-aware pipeline.
- SRS + helper core
  - SRS store/scheduler/policy primitives and pair-level settings.
  - Set planning/bootstrap/refresh workflows in helper use-cases.
  - Language-pair rule generation pipelines (`ja_en`, `en_de`) with confidence scoring.
  - Feedback/exposure signal ingestion paths.
- Desktop GUI (PySide6)
  - Profile/ruleset management and editable rules tables.
  - Language-pack management (download/validate/link/manual override).
  - Bulk synonym generation and dataset import/export (JSON + share code).
  - Appearance/theme controls and preview tooling.
- Chrome extension
  - Replaces text on all frames/pages with configurable highlight behavior.
  - Runtime rule sources: local rules + optional helper rules + profile-scoped helper cache fallback.
  - SRS gating, SRS feedback popup, sound feedback, and exposure logging.
  - Profile-first SRS settings model (`srsProfiles`) with selected-profile runtime mirrors.
  - Profile background controls with IndexedDB media storage.
  - Popup module stack for clicked target words (Japanese script, feedback-history, and encounter-history modules above the feedback bar).
  - Module preferences UI (per profile + target language): enable/disable, drag-reorder, module-specific settings, and per-module color tuning with live preview.
  - Fully localized options UI and diagnostics/debug controls.
- BetterDiscord plugin
  - Message/embed text replacement using the same core matching approach.
  - JSON/share-code rules import path and UI settings for highlight/click-to-toggle behavior.

Project layout
- `apps/gui/src/`: PySide6 GUI scaffold.
  - `apps/gui/src/main.py`: main window, menu actions, preview integration.
  - `apps/gui/src/state.py`: app state + dirty tracking.
  - `apps/gui/src/models.py`: list/table models for profiles and rules.
  - `apps/gui/src/dialogs.py`: settings + rule metadata dialogs.
  - `apps/gui/src/dialogs_profiles.py`: profile manager + first-run dialogs.
  - `apps/gui/src/dialogs_code.py`: code export/import and bulk rules dialogs.
  - `apps/gui/src/settings_language_packs.py`: language pack manager UI.
  - `apps/gui/src/utils_paths.py`: cross-platform "reveal in Finder/Explorer" helper.
  - `apps/gui/src/preview.py`: preview worker + highlighter.
- `apps/chrome-extension/`: Chrome extension (content script + options UI).
- `apps/chrome-extension/README.md`: extension folder map and runtime entry points.
- `apps/betterdiscord-plugin/`: BetterDiscord plugin (message replacement).
- `core/lexishift_core/replacement/core.py`: tokenization, normalization, rules, trie, and replacer.
- `core/lexishift_core/replacement/inflect.py`: conservative inflection generation and phrase expansion.
- `core/lexishift_core/replacement/builder.py`: expand rules into inflected variants and build pools.
- `core/lexishift_core/replacement/pipeline.py`: compile exact vs meaning-aware replacers.
- `core/lexishift_core/persistence/storage.py`: dataset persistence + GUI-facing settings scaffolding.
- `core/lexishift_core/persistence/import_export.py`: import/export helpers, including "export as code".
- `core/lexishift_core/persistence/settings.py`: app-level profiles and import/export settings.
- `core/lexishift_core/srs/`: SRS domain primitives and policies (store, scheduler, selector, planning, refresh).
- `core/lexishift_core/helper/`: helper integration layer (paths, profiles, host-facing orchestration).
- `core/lexishift_core/helper/use_cases/`: helper command use-cases (`rulegen`, set planning/init/refresh, signals, reset, diagnostics).
- `core/lexishift_core/frequency/`: generic frequency lexicon loading + provider interfaces.
- `core/lexishift_core/frequency/de/`: DE-specific frequency pack build pipeline and POS-lexicon compilation.
- `core/lexishift_core/rulegen/generation.py`: pair-agnostic rule generation pipeline/scoring.
- `core/lexishift_core/rulegen/pairs/`: pair-specific generators (`ja_en`, `en_de`).
- `core/lexishift_core/__init__.py`: public API exports.
- `data/`: schema definitions and sample rulesets.
- `scripts/dev/dev_utils.py`: convenience re-export of the same public API.
- `scripts/README.md`: script categories and common entry points.
- `core/tests/`: unit tests for replacement, storage, inflection, builder, settings, import/export.
- `core/tests/README.md`: domain-oriented test folder map.

Documentation
- `docs/README.md`: documentation map by purpose.
- `docs/architecture/extension_system_map.md`: one-page extension map (entrypoints, flows, storage, boundaries).
- `docs/architecture/chrome_extension_technical.md`: content script + options architecture, SRS gate, logging.
- `docs/architecture/options_controllers_architecture.md`: options startup/composition graph and controller boundaries.
- `docs/architecture/popup_modules_pattern.md`: popup modules architecture and extension plan.
- `docs/srs/srs_roadmap.md`: SRS workstreams and current status.
- `docs/srs/srs_schema.md`: SRS data schema (settings/items/store).
- `docs/rulegen/rule_generation_technical.md`: precomputed rule generation + confidence scoring.
- `docs/rulegen/synonym_generation_technical.md`: synonym generation pipeline notes.

Core concepts
- Tokenization
  - `Tokenizer` splits text into `Token` objects (word/space/punct).
  - Punctuation and whitespace are preserved in output.
- Normalization
  - `Normalizer` lowercases words for matching.
  - `SynonymNormalizer` can map known synonyms to a canonical token.
- Rules
  - `VocabRule` = single source phrase -> replacement.
  - `MeaningRule` = list of phrases -> single replacement (expanded into `VocabRule`).
  - `RuleMetadata` = GUI-friendly fields (label, description, examples, notes, source).
- Matching
  - `VocabPool` compiles rules into a phrase trie.
  - `Replacer` performs a left-to-right longest-match pass.
  - Only whitespace is allowed between words inside a matched phrase (no punctuation).
- Case handling
  - `case_policy` supports `match`, `as-is`, `lower`, `upper`, `title`.

Primary usage (exact replacement)
```python
from lexishift_core import VocabPool, Replacer, VocabRule

rules = [
    VocabRule(source_phrase="twilight", replacement="gloaming"),
    VocabRule(source_phrase="stunned into silence", replacement="overawed"),
]
pool = VocabPool(rules)
replacer = Replacer(pool)
print(replacer.replace_text("At twilight, she was stunned into silence."))
```

Inflection generation (precompute)
```python
from lexishift_core import (
    VocabRule,
    BuildOptions,
    InflectionSpec,
    FORM_PLURAL,
    FORM_POSSESSIVE,
    build_vocab_pool,
    Replacer,
)

rules = [VocabRule(source_phrase="twilight", replacement="gloaming")]
options = BuildOptions(
    inflection_spec=InflectionSpec(forms=frozenset({FORM_PLURAL, FORM_POSSESSIVE}))
)
pool = build_vocab_pool(rules, options=options)
replacer = Replacer(pool)
print(replacer.replace_text("Twilight's colors fade."))
```

Meaning-aware mode (optional, precomputed)
```python
from lexishift_core import (
    VocabRule,
    MeaningRule,
    VocabPool,
    compile_pipeline,
    ReplacementMode,
)

rules = [VocabRule(source_phrase="twilight", replacement="gloaming")]
meaning_rules = [MeaningRule(source_phrases=("dusk", "evening twilight"), replacement="gloaming")]
pipeline = compile_pipeline(VocabPool(rules), meaning_rules=meaning_rules)
print(pipeline.replace_text("At dusk.", mode=ReplacementMode.MEANING))
```

Persistence and dataset schema
- `VocabDataset` stores:
  - `rules`: `VocabRule` entries
  - `meaning_rules`: `MeaningRule` entries
  - `synonyms`: optional word-level synonym map
  - `settings`: GUI-friendly settings for inflection + learning features
  - `version`: schema version
- `load_vocab_dataset` / `save_vocab_dataset` read/write JSON on disk.
- `build_vocab_pool_from_dataset` compiles rules using dataset settings.

Dataset settings (GUI scaffolding)
- `InflectionSettings`: on/off, global spec, per-rule overrides, irregulars, strictness.
- `LearningSettings`: show original text toggles and highlight controls.
- `VocabSettings`: container for all dataset-level settings.

Synonym sources (local)
- WordNet: point to a directory containing either classic `data.*` files or JSON bundles (`entries-*.json`, `noun.*.json`, `verb.*.json`, `adj.*.json`).
- Moby Thesaurus: point to a comma-separated thesaurus file (headword, synonym, ...).
- Configure paths and options in the Settings dialog (App tab).
- Language packs manager (Settings -> App) handles downloads, validation, and linking.
- Supported packs via language packs: OpenThesaurus (DE), JP WordNet, JMDict, CC-CEDICT.
- Embeddings (optional ranking):
  - For fast daily use, convert large `.vec`/`.bin` files to SQLite once:
    - `python scripts/data/convert_embeddings.py --input /path/to/cc.en.300.vec --output /path/to/cc.en.300.sqlite`
  - Enable embeddings per language-pair in Settings -> App -> Embeddings / Cross-lingual Embeddings (Use button).
  - For cross-lingual similarity, load aligned vectors for both languages in the pair (e.g., `wiki.en.align.vec` + `wiki.de.align.vec`).
  - SQLite conversion also stores a lightweight hash index for fast nearest-neighbor fallback.
  - TODO: hook embeddings into rule-generation scoring (downloads + one-time conversion are wired; scoring integration is pending).
Language packs (Settings -> App)
- Language packs list is shown inside Settings (App tab), with Download/Delete buttons per pack.
- Each row shows language, source, and size (size is listed in the rightmost column).
- Downloads are saved to the app data folder (use the "Open local directory" button at the top of the section).
- If a download fails, the UI shows a "there was a problem" message plus a Wayback mirror link.
- Pack definitions live in `apps/gui/src/language_packs.py` (`LANGUAGE_PACKS`).
- Downloads are extracted, validated, and auto-linked when possible; manual overrides are available via "Select...".

Planned: language selection UX for synonym generation
- Add a language checklist for Replacement-word generation, using the installed language packs.
- Separate toggles for:
  - Monolingual synonyms (same-language replacement).
  - Translation synonyms (cross-language replacement).
- UX hint: use monolingual for in-language rulesets (English→English, Japanese→Japanese).
- Use translation when building cross-language study rulesets (English→Japanese, Chinese→Spanish).

Planned: profiles + rulesets sharing into clients
- Profile metadata + ruleset lists should be selectable from the Chrome extension and BetterDiscord plugin.
- Goal: quick switching between practice scopes (e.g., Spanish practice ruleset vs. domain-specific ruleset).

Dictionary metadata (current + planned)
- See [Dictionary sources (detailed)](#dictionary-sources-detailed) for structured tables and visual labels.
- WordNet (English, JSON bundle)
  - URL: https://en-word.net/static/english-wordnet-2025-json.zip
  - Size: 72.5 MB
  - Format: JSON files such as `entries-a.json`, `adj.all.json`, `noun.act.json`, `verb.body.json`.
- Moby Thesaurus (English)
  - URL: https://archive.org/download/mobythesauruslis03202gut/mthesaur.txt
  - Size: 24.9 MB
  - Format: CSV-style lines (headword, synonym, synonym, ...)
- OpenThesaurus (German)
  - URL: https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/openthesaurus.txt?inline=false
  - Size: 2.6 MB
  - Format: semicolon-delimited synonym groups (one line = one synset).
- Japanese WordNet (Japanese)
  - URL: https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz
  - Size: 29.2 MB
  - Format: tab-delimited lines: `synset_id<TAB>word<TAB>source` (example source tags: `hand`, `mono`, `XXXX`).
  - After download: `wnjpn-all.tab.gz` decompresses to `wnjpn-all.tab`.
- JMDict (Japanese → English)
  - URL: https://www.edrdg.org/pub/Nihongo/JMdict_e.gz
  - Size: 61.6 MB (Unzipped)
  - Format: gzipped XML dictionary.
- CC-CEDICT (Chinese → English)
  - URL: https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip
  - Size: 9.7 MB (Unzipped)
  - Format: zip with `cedict_ts.u8` entries.
- Wiktionary translations (English)
  - URL: https://kaikki.org/dictionary/english/kaikki.org-dictionary-English.jsonl.gz
  - Size: 2.3 GB
  - Format: JSONL with per-entry translations.
  - Status: planned (paused), not exposed in the UI yet.
- Notes:
  - Wired into synonym generation: WordNet (classic + JSON), Moby, OpenThesaurus, JP WordNet, JMDict, CC-CEDICT.
  - Not wired yet: Wiktionary translations (future translation layer).

Dictionary effectiveness (notes)
- WordNet (EN): strong semantic coverage for English synonyms; good baseline for formal/standard words, but may miss slang or modern variants.
- Moby (EN): large list of synonyms but noisy/dated; good for breadth, weaker for precision.
- OpenThesaurus (DE): solid German coverage; can be dated depending on snapshot, good for monolingual German rulesets (DE→DE working well).
- Japanese WordNet: useful for structured Japanese synonyms, but limited coverage vs. modern corpora.
- For higher accuracy/coverage, consider:
  - Wiktionary exports (multilingual, high recall but requires cleanup).
  - Open Multilingual WordNet for cross-lingual synset alignment.
  - Language-specific resources (e.g., CC-CEDICT for Chinese, JMDict for Japanese).
  - Embedding-based neighbors as a fallback for rare words (with ranking threshold).

## Dictionary Sources (Detailed)

Legend
- <span style="background:#E8F5E9;color:#1B5E20;padding:2px 6px;border-radius:6px;">MONO</span> = monolingual synonyms
- <span style="background:#E3F2FD;color:#0D47A1;padding:2px 6px;border-radius:6px;">X-LANG</span> = cross-lingual translation

Installed/Planned Packs (current app list)
| Source | Type | Lang | URL | Size | Format |
| --- | --- | --- | --- | --- | --- |
| WordNet (JSON) | MONO | EN | https://en-word.net/static/english-wordnet-2025-json.zip | 72.5 MB | JSON synset files (`entries-*.json`, `noun.*.json`, `verb.*.json`, `adj.*.json`) |
| Moby Thesaurus | MONO | EN | https://archive.org/download/mobythesauruslis03202gut/mthesaur.txt | 24.9 MB | CSV-like text (headword, synonym, ...) |
| OpenThesaurus | MONO | DE | https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/openthesaurus.txt?inline=false | 2.6 MB | Semicolon-separated synonym lines |
| Japanese WordNet | MONO | JA | https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz | 29.2 MB | Tab-separated synset_id, word, source |
| JMDict | X-LANG | JA→EN | https://www.edrdg.org/pub/Nihongo/JMdict_e.gz | 61.6 MB (Unzipped) | gzipped XML dictionary |
| CC-CEDICT | X-LANG | ZH→EN | https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip | 9.7 MB (Unzipped) | zip with `cedict_ts.u8` |

Cross-lingual dictionary options (future)
| Source | Type | Coverage | Notes |
| --- | --- | --- | --- |
| Open Multilingual WordNet | X-LANG | Many | Synset-aligned across languages (clean semantic mapping). |
| Wiktionary translations | X-LANG | Many | Very broad coverage, requires cleanup and normalization. |
| PanLex | X-LANG | Many | Massive bilingual lexicon, good for mapping but not synonyms. |
| Apertium lexicons | X-LANG | Limited | High-quality bilingual pairs where available. |
| JMDict / CC-CEDICT | X-LANG | JA/EN, ZH/EN | Strong bilingual dictionaries for learning workflows. |

Effectiveness summary (quick guidance)
| Source | Precision | Coverage | Notes |
| --- | --- | --- | --- |
| WordNet (EN) | High | Medium | Great for core synonyms, weak on slang/modern terms. |
| Moby (EN) | Medium | High | Broad but noisy; needs filtering. |
| OpenThesaurus (DE) | Medium-High | Medium | Good monolingual German; snapshot can be dated. |
| JP WordNet | Medium | Medium | Structured but limited vs. modern corpora. |
| Wiktionary | Medium | Very High | Best multilingual breadth, but requires cleanup. |
| PanLex | Medium | Very High | Excellent cross-lingual mapping, not synonym quality. |

Profiles, rulesets, and app settings (GUI scaffolding)
- `Profile` is a named project that owns one or more rulesets (JSON files) and tracks the active ruleset.
- `AppSettings` holds profiles and active profile id.
- `ImportExportSettings` stores user preferences for exporting datasets.
- `SynonymSourceSettings` stores local synonym resource paths and options.
- `load_app_settings` / `save_app_settings` persist app settings to JSON.

Import/export (including "export as code")
- Code export is a compact, reversible string (compressed JSON encoded with a URL-safe alphabet).
- `export_dataset_json` / `import_dataset_json` operate on JSON strings.
- `export_dataset_code` / `import_dataset_code` export/load the ruleset as a compact code string.
- `export_app_settings_json` / `import_app_settings_json` operate on app settings JSON.
- `export_app_settings_code` / `import_app_settings_code` export/load app settings as a compact code string.

SRS and profile capabilities (current state)
- Core domain (`core/lexishift_core/srs`)
  - Scheduling/store primitives, admission refresh, selector, planning, and policy modules.
  - Pair-aware sizing policy (`bootstrap_top_n`, `initial_active_count`, `max_active_items_hint`).
- Helper orchestration (`core/lexishift_core/helper/use_cases`)
  - `initialize_set`, `refresh_set`, `rulegen_job`, `set_planning`, `signals`, `reset_srs`.
  - Pair requirement validation, seed selection, rule publication, and status updates.
- Extension runtime/profile model
  - `srsSelectedProfileId`: extension-local selected profile.
  - `srsProfiles.<profile_id>.languagePrefs`: source/target language + target script prefs.
  - `srsProfiles.<profile_id>.modulePrefs`: popup module preferences (`byId` config + module `order`).
  - `srsProfiles.<profile_id>.srsByPair.<pair>`: pair SRS settings.
  - `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`: planner/profile context signals.
  - `srsProfiles.<profile_id>.uiPrefs`: profile UI prefs, including background controls.
  - Runtime mirrors publish selected profile values for content-script usage.

Testing
- `python -m unittest discover -s core/tests`
- Tests add the core directory to `sys.path` for local runs.

Development health
- Install dev tools: `pip install -r requirements-dev.txt`
- Format Python: `ruff format .`
- Typecheck core: `mypy core/lexishift_core`
- Pre-commit hooks: `pre-commit install`
- CI: `.github/workflows/ci.yml` runs core tests + typecheck on push/PR.

GUI scaffold (PySide6)
- Entry points:
  - `python apps/gui/src/main.py` (recommended)
  - `python apps/gui/src` (runs `apps/gui/src/__main__.py`)
- Features:
  - Profile selector + ruleset selector header; profile manager dialog for adding/removing/editing profiles.
  - Per-profile ruleset list with active ruleset selection and Finder/Explorer reveal.
  - First-run welcome flow for creating a profile.
  - Rule editor backed by `QAbstractTableModel`.
  - Add/delete rules and edit rule metadata.
  - Synonym bulk add from a delimiter-split list of target words/phrases (select dictionaries per run).
  - Per-row delete column in the rule table.
  - Appearance tab with theme selection + “Open themes folder”.
  - Custom themes loaded from `themes/` with per-screen backgrounds and sample assets.

Chrome extension
- Load `apps/chrome-extension/` as an unpacked extension in Chrome.
- Configure rules in options page (JSON array/file import/share code import).
- Replacement runtime
  - Longest-match replacement with configurable behavior flags:
    - `maxOnePerTextBlock`
    - `allowAdjacentReplacements`
    - `maxReplacementsPerPage`
    - `maxReplacementsPerLemmaPerPage`
  - Replaces visible text on all pages/frames and skips editable fields.
- Rule source/runtime behavior
  - Local ruleset normalization and runtime application.
  - Optional helper rules with profile-scoped cache fallback.
  - SRS gate can filter active rules by replacement lemma.
- SRS interaction features
  - Feedback popup for replacement spans with ratings Again/Hard/Good/Easy.
  - Keyboard shortcuts (Ctrl+1/2/3/4) while popup is open.
  - Feedback gating by origin (`srs` vs `ruleset`) and optional feedback sound.
  - Exposure logging to `chrome.storage.local` (independent from debug logging).
- Profile-scoped features in options
  - Selected profile picker and helper profile refresh.
  - Pair-level SRS controls (enabled/max active/bootstrap/initial active/etc.).
  - Profile language prefs and module preferences (including Japanese primary display script).
  - Profile background image upload/remove/enable/opacity/backdrop color with IndexedDB storage.
- Popup modules
  - Feedback popup uses attachable module stack above feedback bar.
  - Japanese script module can show non-primary scripts from replacement metadata.
  - Feedback-history and encounter-history modules can be toggled and reordered.
  - Module order and per-module color preferences are applied to runtime popups.
- Diagnostics and localization
  - Advanced diagnostics actions and helper connectivity checks.
  - Debug logs + focus-word tracing.
  - Fully localized options UI with language selector.
- More detail
  - Extension layout/runtime map: `apps/chrome-extension/README.md`
  - Technical architecture: `docs/architecture/chrome_extension_technical.md`

BetterDiscord plugin
- Copy `apps/betterdiscord-plugin/LexiShift.plugin.js` into your BetterDiscord plugins folder.
- Configure rules in the plugin settings (JSON array, share code, or local file path).
- Optional highlight + color, and click-to-toggle original text.
- Plugin source is modularized under `apps/betterdiscord-plugin/src/`; rebuild with `node apps/betterdiscord-plugin/build_plugin.js`.
- Dev scripts:
  - `npm run build:bd`
  - `npm run watch:bd`
  - `npm run sync:bd`

Packaging (PyInstaller)
- Install deps: `pip install pyside6 pyinstaller`
- Build: `python scripts/build/gui_app.py`
  - Validate bundle resources: `python scripts/build/gui_app.py --validate`
  - Install to `/Applications` (macOS): `python scripts/build/gui_app.py --install` (installs both app bundles)
  - Equivalent: `pyinstaller --clean --noconfirm apps/gui/packaging/pyinstaller.spec`
- Output:
  - macOS: `dist/LexiShift.app` and `dist/LexiShift Helper.app`
    - `LexiShift.app`: main GUI app bundle
    - `LexiShift Helper.app`: helper tray/daemon agent bundle (autostart target)
  - Windows: `dist/LexiShift.exe` (bundle icon uses `apps/gui/resources/ttbn.ico`)
- Note: build Windows binaries on Windows (PyInstaller does not cross-compile).
- Validation helper: `python scripts/build/validate_app_bundle.py --distpath apps/gui/dist`

Installers (macOS DMG / Windows EXE)
- Build installers: `python scripts/build/installer.py`
  - macOS: creates a `.dmg` in `apps/gui/dist/installers/`
  - Windows: creates an Inno Setup `.exe` in `apps/gui/dist/installers/`
- Optional: validate app bundle before packaging with `python scripts/build/installer.py --validate`
- Windows dependency: install Inno Setup and ensure `iscc` is on PATH.
- Unsigned builds will trigger Gatekeeper/SmartScreen warnings; use signing for distribution.

Code signing & notarization (optional but recommended)
- macOS signing (Developer ID):
  - Obtain a “Developer ID Application” certificate in your Apple Developer account.
  - Build with: `python scripts/build/installer.py --mac-sign-identity "Developer ID Application: Your Name (TEAMID)"`
- macOS notarization:
  - Create an app‑specific password in Apple ID.
  - Run with: `python scripts/build/installer.py --mac-sign-identity "Developer ID Application: ..." --notarize --apple-id you@domain.com --team-id TEAMID --notary-password APP_SPECIFIC_PASSWORD`
  - The script submits the DMG to notarytool and staples it.
- Windows signing (Authenticode):
  - Obtain a code signing cert (.pfx) and install the Windows SDK (signtool).
  - Run with: `python scripts/build/installer.py --win-sign-pfx C:\\path\\cert.pfx --win-sign-password YOUR_PASSWORD`
  - Timestamp defaults to `http://timestamp.digicert.com` (override with `--timestamp-url`).

Localization (GUI)
- Locale catalogs live in `apps/gui/resources/i18n/` (base in `en.json`).
- `apps/gui/resources/i18n/locales.json` lists available locales for Settings > Appearance.
- Restart the GUI app after switching language.

Current limitations
- No streaming adapter yet (planned).
- No POS/NER gating yet (possible future accuracy upgrade).
- Inflection generator is conservative and avoids ambiguous doubling.
- TODO (CJK / no-space languages):
  - Detect whether input is likely a no-space language (CJK) using lightweight heuristics.
  - If CJK, choose between:
    - character/n-gram tokenization with a trie that matches sequences, or
    - exact substring replacement without token boundaries.
  - Keep exact substring mode as a user-selectable fallback for mixed-language text.
- TODO (replacement pacing/sensitivity controls):
  - Limit replacements per sentence.
  - Limit replacements per page.
  - Avoid replacing two juxtaposed words.
  - Add settings to adjust sensitivity/strictness for the rules above.
- TODO (Japanese script quality):
  - Check and improve the accuracy of generated romaji for Japanese words.
- TODO (rule generation quality):
  - Improve rulegen quality by making generation/scoring shallower and higher precision.
  - `en-ja` now uses strict JMdict reading match (`surface + reading` from `word_package`); targets with no reading-matched entry currently stay in S but emit no rules.
  - Evaluate a disposal/pruning policy for those unmatched S targets (for example, remove or quarantine after repeated misses).

Plans (ordered by ease/priority)
1. Persist all GUI knowledge inside profiles/rulesets:
   - Store per-profile dictionary selection (mono vs cross-lingual) and language choices.
   - Store synonym settings (thresholds, embeddings) per profile or ruleset where appropriate (currently global).
2. Sync profiles/rulesets into clients:
   - Export active profile + ruleset list + language pack selection to Chrome/BD.
   - Add profile/ruleset switcher in extension/plugin settings.
3. Finish language pack UX polish:
   - Pack-specific validators for edge layouts.
   - Clear handling for external/manual paths vs. app-managed files.
   - Re-enable Wiktionary when we are ready to handle large downloads.
4. Add language selection controls tied to profiles/rulesets:
   - Monolingual vs cross-lingual toggle per profile or per ruleset.
   - Persist target/source language choices for bulk generation.
5. Scale large pack handling:
   - Background indexing for large packs (progress + cancel).
   - Optional cached indexes for fast reloads.
6. Add per-rule exception patterns or context gates if needed.
7. Add streaming/liveness adapter for live text replacement.
8. Localize the BetterDiscord plugin for multiple languages.
9. Consider larger Σ symbol spaces for Share Code to shorten codes.

Known inconsistencies / friction points
- Embedding similarity depends on the selected language pair; auto language detection is still missing.
- Cross-lingual dictionaries (JMDict/CC-CEDICT) are translations, not strict synonyms; they should be surfaced separately in UX and labeling.
- Language determination is missing for CJK/no-space text; replacement quality is limited until CJK tokenization or substring mode is added.
- WordNet classic vs JSON layouts can diverge; validation allows both, but pack-specific parsing rules may be needed.
- Manual language pack paths can point outside the app folder; Delete only removes app-managed files, so UX should clarify that.
- Embeddings fallback requires neighbor-capable formats; SQLite builds without LSH won’t support fallback lookup.
- Profile vs ruleset ownership is still fuzzy in UX; Manage menu ruleset population should make the relationship explicit and consistent.
- Profiles support multiple rulesets, but extensions/plugins still take one ruleset at a time; profile sync is still conceptual.
- GUI spacing/padding is not tuned for all locales; layout density needs a pass.
- Theme colors still need refinement for contrast and visual polish.
- Theme coverage varies by widget; code editor/backgrounds may be obscured by opaque controls.

Notes for future AI contributors
- Keep modules small and composable; avoid mixing GUI concerns into core logic.
- Prefer deterministic behavior in core; add optional layers for meaning/semantics.
- Update this README with any new modules or schema changes.
