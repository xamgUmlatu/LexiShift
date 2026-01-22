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

Roadmap (short)
- Add streaming/liveness adapter for live text replacement.
- Add schema documentation and sample JSON for the GUI.
- Add per-rule exception patterns or context gates if needed.

Notes for future AI contributors
- Keep modules small and composable; avoid mixing GUI concerns into core logic.
- Prefer deterministic behavior in core; add optional layers for meaning/semantics.
- Update this README with any new modules or schema changes.
