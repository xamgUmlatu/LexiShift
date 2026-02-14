# Scripts Structure

Scripts are grouped by workflow type so build/release and data tooling stay separated.

## Folders

- `build/`: packaging and build pipelines (GUI app, installers, DE frequency, JA->EN rules, bundle validation).
- `data/`: conversion/import utilities for frequency and embeddings resources.
- `dev/`: local developer workflows and diagnostics (helper cleanup/status, dev cycle, demos).
- `helper/`: helper daemon/native-host entrypoints and native messaging assets.
- `testing/`: language-pair analysis/testing scripts and report generators.

## Common Entry Points

- Build app bundle: `build/gui_app.py`
- Build installers: `build/installer.py`
- Convert embeddings: `data/convert_embeddings.py`
- Convert FreeDict TEI to SQLite: `data/convert_freedict_tei_to_sqlite.py`
- Convert FreeDict Spanish->English to SQLite: `data/convert_freedict_spa_eng_to_sqlite.py`
- Convert FreeDict English->Spanish to SQLite: `data/convert_freedict_eng_spa_to_sqlite.py`
- Convert Spanish frequency sample to SQLite: `data/convert_cde_frequency_to_sqlite.py`
- Dev helper cycle: `dev/dev_cycle.sh`
