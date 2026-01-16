# VocabReplacer

Purpose
- Replace words and phrases in text using a curated vocabulary pool.
- Primary use case: full-text replacement (input text is already complete).
- Secondary (future) use case: live text stream replacement.

Design goals
- Deterministic, conservative behavior by default.
- Extensible architecture for GUI tooling and plugins/extensions later.
- Precompute static vocab pools (inflections, expansions) so runtime is fast.

Project layout
- `gui_app/`: PySide6 GUI scaffold.
  - `gui_app/main.py`: main window, toolbar actions, preview integration.
  - `gui_app/state.py`: app state + dirty tracking.
  - `gui_app/models.py`: list/table models for profiles and rules.
  - `gui_app/dialogs.py`: profiles, metadata, settings dialogs.
  - `gui_app/preview.py`: preview worker + highlighter.
- `chrome_extension/`: Chrome extension (content script + options UI).
- `betterdiscord_plugin/`: BetterDiscord plugin (message replacement).
- `vocab_replacer/core.py`: tokenization, normalization, rules, trie, and replacer.
- `vocab_replacer/inflect.py`: conservative inflection generation and phrase expansion.
- `vocab_replacer/builder.py`: expand rules into inflected variants and build pools.
- `vocab_replacer/pipeline.py`: compile exact vs meaning-aware replacers.
- `vocab_replacer/storage.py`: dataset persistence + GUI-facing settings scaffolding.
- `vocab_replacer/import_export.py`: import/export helpers, including "export as code".
- `vocab_replacer/settings.py`: app-level profiles and import/export settings.
- `vocab_replacer/__init__.py`: public API exports.
- `tools.py`: convenience re-export of the same public API.
- `tests/`: unit tests for replacement, storage, inflection, builder, settings, import/export.

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
from vocab_replacer import VocabPool, Replacer, VocabRule

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
from vocab_replacer import (
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
from vocab_replacer import (
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

Profiles and app settings (GUI scaffolding)
- `Profile` lists dataset path + metadata (name, tags, enabled).
- `AppSettings` holds profiles and active profile id.
- `ImportExportSettings` stores user preferences for exporting datasets.
- `SynonymSourceSettings` stores local synonym resource paths and options.
- `load_app_settings` / `save_app_settings` persist app settings to JSON.

Import/export (including "export as code")
- Code export is a compact, reversible string (compressed JSON encoded with a URL-safe alphabet).
- `export_dataset_json` / `import_dataset_json` operate on JSON strings.
- `export_dataset_code` / `import_dataset_code` export/load the vocab pool as a compact code string.
- `export_app_settings_json` / `import_app_settings_json` operate on app settings JSON.
- `export_app_settings_code` / `import_app_settings_code` export/load app settings as a compact code string.

Testing
- `python -m unittest`
- Tests add the repo root to `sys.path` for local runs.

GUI scaffold (PySide6)
- Entry points:
  - `python -m gui_app` (recommended)
  - `python -m gui_app.main`
  - `python gui_app/main.py` (works from repo root or from `gui_app/`)
- Features (initial scaffold):
  - Profile list (with active/disabled indicators).
  - Profile manager dialog (add/remove/edit profiles).
  - First-run welcome flow for creating a profile.
  - Rule editor backed by `QAbstractTableModel`.
  - Add/delete rules and edit rule metadata.
  - Synonym bulk add from a delimiter-split list of target words/phrases (uses local sources from Settings).
  - Per-row delete column in the rule table.

Chrome extension
- Load `chrome_extension/` as an unpacked extension in Chrome.
- Configure rules in the extension options page (JSON array).
- Replaces visible text on all pages, skips editable fields.

BetterDiscord plugin
- Copy `betterdiscord_plugin/VocabReplacer.plugin.js` into your BetterDiscord plugins folder.
- Configure rules in the plugin settings (JSON array).
- Plugin source is modularized under `betterdiscord_plugin/src/`; rebuild with `node betterdiscord_plugin/build_plugin.js`.
- Dev scripts:
  - `npm run build:bd`
  - `npm run watch:bd`
  - `npm run sync:bd`
  - Settings dialog for app import/export defaults and dataset inflection/learning options.
  - Dirty-state tracking to control Save prompts.
  - Preview pane with background worker (`QThread`) and highlight overlay.
  - Import/export for vocab pools (JSON/Code).
  - Import/export for profile settings (JSON/Code).

Packaging (PyInstaller)
- Install deps: `pip install pyside6 pyinstaller`
- Build: `pyinstaller --clean --noconfirm packaging/pyinstaller.spec`
- Output:
  - macOS: `dist/VocabReplacer.app` (bundle icon uses `ttbn.icns`)
  - Windows: `dist/VocabReplacer.exe` (requires a `.ico` at `packaging/ttbn.ico`)
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
