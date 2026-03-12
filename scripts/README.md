# Scripts Structure

Scripts are grouped by workflow type so build/release and data tooling stay separated.

## Folders

- `build/`: packaging and build pipelines (GUI app, installers, DE frequency, JA->EN rules, bundle validation).
- `data/`: conversion/import utilities for frequency and embeddings resources.
- `dev/`: local developer workflows and diagnostics (helper cleanup/status, dev cycle, demos).
- `helper/`: helper daemon/native-host entrypoints and native messaging assets.
- `testing/`: language-pair analysis/testing scripts and report generators.

## Common Entry Points

- Repo safety check (tests + mypy + workflow script compile + advisory project health):
  `dev/dev_workflow_check.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:report`
  - Includes `dev/feature_state_audit.py` so feature-state claims stay structured and evidence-backed
- Feature-state matrix audit:
  `dev/feature_state_audit.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:state`
  - `check:state` compares against `HEAD` so status/default-behavior transitions need matching verification and evidence updates
- Changed-scope workflow check (changed-only health + changed-file Ruff advisory + generated artifact freshness + rulegen-quality detection):
  `dev/dev_workflow_changed_check.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:changed:report`
  - Automatically runs the Windows parity audit when parity-related GUI/helper/build files change
- Workflow Markdown summary renderer for JSON reports:
  `dev/dev_workflow_summary.py`
  - Used by `npm --prefix scripts run check:summary` and CI step summaries
- Cross-platform Python launcher for npm workflow scripts:
  `dev/run_python.js`
  - Keeps `npm --prefix scripts run check` / `build` / quality wrappers usable on Windows where `python3` may not exist by name
- Repo-wide style/debt advisory check (Ruff lint + format check, optional strict mode via `--strict` / `check:style:strict`):
  `dev/dev_workflow_style_check.py`
  - JSON artifact via `npm --prefix scripts run check:style:report`
- Repo-wide style/debt Markdown summary renderer:
  `dev/dev_workflow_style_summary.py`
  - Used by `npm --prefix scripts run check:style:summary` and CI advisory summaries
- Repo build safety (BetterDiscord bundle + GUI PyInstaller build/validate):
  `dev/dev_workflow_build.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run build:report`
  - Verifies expected build artifacts in the JSON report instead of relying on exit codes alone
  - `--ci-safe` skips intentionally unsupported build surfaces on the current host while keeping the same report format
- Windows GUI parity audit:
  `dev/windows_parity_audit.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:windows:parity`
  - The strict parity audit now runs inside `npm --prefix scripts run check`
  - Windows CI uses the strict variant so parity regressions fail the hosted workflow
- Windows GUI parity Markdown summary renderer:
  `dev/windows_parity_summary.py`
  - Used by `npm --prefix scripts run check:windows:parity:summary` and Windows CI summaries
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
- Render Markdown summaries from benchmark JSON artifacts:
  `testing/rulegen_benchmark_summary.py` (also exposed via `npm --prefix scripts run quality:rulegen:benchmark:summary`)
- Focused audit cycle for selected pairs (benchmark -> quality gate -> triage) with sensible defaults for `en-es,en-ja`:
  `testing/rulegen_pair_audit_cycle.py` (also forwards reverse-check tuning values and can emit quality-gate JSON)
- Change-aware audit wrapper that infers touched pairs, writes dated artifacts, updates `*_latest` aliases, and stores a manifest:
  `testing/rulegen_auto_audit.py`
- Apply exported HTML label overrides back into benchmark dataset cases:
  `testing/apply_rulegen_label_overrides.py`
- Gate benchmark/POS artifacts against quality floors, delta budgets, and POS drift guardrails:
  `testing/rulegen_quality_gate.py` (policy default: `docs/test_inputs/rulegen_quality_policy.json`)
- Render Markdown summaries from quality-gate JSON artifacts:
  `testing/rulegen_quality_gate_summary.py` (also exposed via `npm --prefix scripts run quality:rulegen:gate:summary`)
- Extract FAIL/REVIEW benchmark cases from best runs and write triage artifacts:
  `testing/rulegen_benchmark_triage.py`
- Render Markdown summaries from triage JSON artifacts:
  `testing/rulegen_benchmark_triage_summary.py` (also exposed via `npm --prefix scripts run quality:rulegen:triage:summary`)
- Synthetic SRS quality harness for bootstrap/publication/runtime diagnostics plus feedback-cycle behavior:
  `testing/srs_quality_harness.py` (also exposed via `npm --prefix scripts run quality:srs:harness`)
- Render Markdown summaries from SRS quality JSON artifacts:
  `testing/srs_quality_summary.py` (also exposed via `npm --prefix scripts run quality:srs:summary`)
- Dev helper cycle: `dev/dev_cycle.sh`
- Project health gate (architecture maintainability metrics): `dev/check_project_health.js`
  - Supports advisory/global, changed-only scope, baseline delta gating, JSON report output, and baseline snapshot output.
- Audit licensing headers for `expected-not-verified` packs: `dev/licensing_header_audit.py`
- Download and inspect source archive headers for licensing verification (dev-only): `dev/licensing_source_header_fetch.py`
