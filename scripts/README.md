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
- Probe rulegen ranking on fixed words (`hora`, `trabajo`, `様`, `時`) with tunable scoring/caps:
  `testing/rulegen_probe_words.py` (for example `--max-definitions`, `--max-rules-per-target`, `--disable-pos-scoring`)
- Benchmark rulegen parameter sweeps against labeled cases and produce ranked JSON/Markdown reports:
  `testing/rulegen_benchmark.py` (dataset default: `docs/test_inputs/rulegen_benchmark_cases.json`, emits styled HTML with right-click source labeling, LP-by-LP workflow controls, and skip/done navigation; omit `--pairs` to process all LPs in one run)
- Focused audit cycle for selected pairs (benchmark -> quality gate -> triage) with sensible defaults for `en-es,en-ja`:
  `testing/rulegen_pair_audit_cycle.py`
- Apply exported HTML label overrides back into benchmark dataset cases:
  `testing/apply_rulegen_label_overrides.py`
- Gate benchmark/POS artifacts against quality floors, delta budgets, and POS drift guardrails:
  `testing/rulegen_quality_gate.py` (policy default: `docs/test_inputs/rulegen_quality_policy.json`)
- Extract FAIL/REVIEW benchmark cases from best runs and write triage artifacts:
  `testing/rulegen_benchmark_triage.py`
- Dev helper cycle: `dev/dev_cycle.sh`
- Project health gate (architecture maintainability metrics): `dev/check_project_health.js`
- Audit licensing headers for `expected-not-verified` packs: `dev/licensing_header_audit.py`
- Download and inspect source archive headers for licensing verification (dev-only): `dev/licensing_source_header_fetch.py`
