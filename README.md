# LexiShift

Purpose
- Replace words and phrases in text using a curated ruleset.
- Primary use case: full-text replacement (input text is already complete).
- Secondary (future) use case: live text stream replacement.

Design goals
- Deterministic, conservative behavior by default.
- Extensible architecture for GUI tooling and plugins/extensions later.
- Precompute static ruleset expansions (inflections, phrase variants) so runtime is fast.

Project layout
- `apps/gui/src/`: PySide6 GUI scaffold.
  - `apps/gui/src/main.py`: main window, menu actions, preview integration.
  - `apps/gui/src/state.py`: app state + dirty tracking.
  - `apps/gui/src/models.py`: list/table models for profiles and rules.
  - `apps/gui/src/dialogs.py`: profiles, metadata, settings dialogs.
  - `apps/gui/src/preview.py`: preview worker + highlighter.
- `apps/chrome-extension/`: Chrome extension (content script + options UI).
- `apps/betterdiscord-plugin/`: BetterDiscord plugin (message replacement).
- `core/lexishift_core/core.py`: tokenization, normalization, rules, trie, and replacer.
- `core/lexishift_core/inflect.py`: conservative inflection generation and phrase expansion.
- `core/lexishift_core/builder.py`: expand rules into inflected variants and build pools.
- `core/lexishift_core/pipeline.py`: compile exact vs meaning-aware replacers.
- `core/lexishift_core/storage.py`: dataset persistence + GUI-facing settings scaffolding.
- `core/lexishift_core/import_export.py`: import/export helpers, including "export as code".
- `core/lexishift_core/settings.py`: app-level profiles and import/export settings.
- `core/lexishift_core/__init__.py`: public API exports.
- `data/`: schema definitions and sample rulesets.
- `scripts/dev_utils.py`: convenience re-export of the same public API.
- `core/tests/`: unit tests for replacement, storage, inflection, builder, settings, import/export.

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
- WordNet: point to a directory containing `data.noun`, `data.verb`, `data.adj`, `data.adv`.
- Moby Thesaurus: point to a comma-separated thesaurus file (headword, synonym, ...).
- Configure paths and options in the Settings dialog (App tab).
- Embeddings (optional ranking):
  - For fast daily use, convert large `.vec`/`.bin` files to SQLite once:
    - `python scripts/convert_embeddings.py --input /path/to/cc.en.300.vec --output /path/to/cc.en.300.sqlite`
  - Point “Embeddings file” in Settings to the `.db`/`.sqlite` output.
  - SQLite conversion also stores a lightweight hash index for fast nearest-neighbor fallback.
Language packs (Settings -> App)
- Language packs list is shown inside Settings (App tab), with a Download button per pack.
- Each row shows language, source, and size (size is listed in the rightmost column).
- Downloads are saved to the app data folder (use the "Open local directory" button at the top of the section).
- If a download fails, the UI shows a "there was a problem" message plus a Wayback mirror link.
- Placeholder pack entries live in `apps/gui/src/dialogs.py` (`LANGUAGE_PACKS`); replace URLs and sizes with real values.
- After download, point WordNet/Moby fields at the downloaded files as needed (auto-wiring can be added later).
Planned: auto-hook downloaded dictionaries
- Downloaded packs should be auto-linked as their local resource.
- Archive packs should be extracted and validated on completion, then the Settings UI should show the resolved path.
- Validation rules (per pack) should map to the expected file layout; we may need structure notes for each pack.

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

Dictionary metadata (planned sources)
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
  - Size: (fill exact size)
  - Format: semicolon-delimited synonym groups (one line = one synset).
- Japanese WordNet (Japanese)
  - URL: https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz
  - Size: (fill exact size)
  - Format: tab-delimited lines: `synset_id<TAB>word<TAB>source` (example source tags: `hand`, `mono`, `XXXX`).
  - After download: `wnjpn-all.tab.gz` decompresses to `wnjpn-all.tab`.
- Notes:
  - These are not wired into synonym generation yet (except English WordNet/Moby).
  - The app should auto-link downloaded packs after extraction + validation.

Dictionary effectiveness (notes)
- WordNet (EN): strong semantic coverage for English synonyms; good baseline for formal/standard words, but may miss slang or modern variants.
- Moby (EN): large list of synonyms but noisy/dated; good for breadth, weaker for precision.
- OpenThesaurus (DE): solid German coverage; can be dated depending on snapshot, good for monolingual German rulesets.
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
- Features (initial scaffold):
  - Profile selector + ruleset selector header; profile manager dialog for adding/removing/editing profiles.
  - Per-profile ruleset list with active ruleset selection and Finder/Explorer reveal.
  - First-run welcome flow for creating a profile.
  - Rule editor backed by `QAbstractTableModel`.
  - Add/delete rules and edit rule metadata.
  - Synonym bulk add from a delimiter-split list of target words/phrases (uses local sources from Settings).
  - Per-row delete column in the rule table.

Chrome extension
- Load `apps/chrome-extension/` as an unpacked extension in Chrome.
- Configure rules in the extension options page (JSON array or file import).
- Display options include highlight color and click-to-toggle original text.
- Share code import/export supports compressed codes (CJK short codes).
- Advanced debug tools are tucked under a collapsible section (optional).
- Replaces visible text on all pages (including frames), skips editable fields.
- Notes:
  - File import is a one-time read; re-import after changes.
  - Reload pages to apply rule changes immediately.

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
- Build: `python scripts/build_gui_app.py`
  - Equivalent: `pyinstaller --clean --noconfirm apps/gui/packaging/pyinstaller.spec`
- Output:
  - macOS: `dist/LexiShift.app` (bundle icon uses `apps/gui/resources/ttbn.icns`)
  - Windows: `dist/LexiShift.exe` (bundle icon uses `apps/gui/resources/ttbn.ico`)
- Note: build Windows binaries on Windows (PyInstaller does not cross-compile).

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

Roadmap (short)
- Add streaming/liveness adapter for live text replacement.
- Add schema documentation and sample JSON for the GUI.
- Add per-rule exception patterns or context gates if needed.

Notes for future AI contributors
- Keep modules small and composable; avoid mixing GUI concerns into core logic.
- Prefer deterministic behavior in core; add optional layers for meaning/semantics.
- Update this README with any new modules or schema changes.
