# Scripts Structure

Status: active script map
Role: Runbook / operational
Last updated: 2026-08-27
Last verified: 2026-08-27 Python environment bootstrap and macOS build/install workflow verification
Purpose: route contributors to the current workflow entrypoints first, then to specialty build/data/testing tools
Source-of-truth: script routing guide; operational behavior is defined by the scripts themselves and `package.json`; by-change-type validation routing lives in `../docs/developer/productization_lane4_validation_gate_inventory.md`.

Scripts are grouped by workflow type so build/release and data tooling stay separated.

## Folders

- `build/`: packaging and build pipelines (GUI app, installers, DE frequency, JA->EN rules, bundle validation).
- `data/`: conversion/import utilities for frequency and embeddings resources.
- `dev/`: local developer workflows and diagnostics (helper cleanup/status, dev cycle, demos).
- `helper/`: helper daemon/native-host entrypoints and native messaging assets.
- `testing/`: language-pair analysis/testing scripts and report generators.

## Start Here

Use the package-script workflow surfaces first when they exist:

- Python environment: `npm --prefix scripts run setup:python` (add `:build` for GUI packaging)
- Repo safety: `npm --prefix scripts run check`
- Branch-scope safety: `npm --prefix scripts run check:changed`
- Canonical doc integrity: `npm --prefix scripts run check:docs`
- Feature-state audit: `npm --prefix scripts run check:state`
- Project structure inventory: `npm --prefix scripts run inventory:structure`
- Generated-output unnecessary audit: `npm --prefix scripts run inventory:unnecessary`
- SRS admission lab: `npm --prefix scripts run dev:srs-admission-lab`
- Build safety: `npm --prefix scripts run build`
- Project health: `npm --prefix scripts run health:project`
- SRS quality harness: `npm --prefix scripts run quality:srs:harness`
- SRS journey harness: `npm --prefix scripts run quality:srs:journey`
- SRS journey edge lane: `npm --prefix scripts run quality:srs:journey:edge`
- SRS journey real-publication lane: `npm --prefix scripts run quality:srs:journey:real`
- SRS journey installed-resource lane: `npm --prefix scripts run quality:srs:journey:installed`
- SRS `en-es` profile-preference lane: `npm --prefix scripts run quality:srs:journey:en-es:profile`

Use the raw script paths below when there is no package-script surface or when you need direct CLI control.
Use `../docs/developer/productization_lane4_validation_gate_inventory.md` when
you need to choose the smallest honest bundle for a specific change type.

## Workflow Entry Points

- Repo safety check (tests + mypy + workflow script compile + advisory project health):
  `dev/dev_workflow_check.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:report`
  - Hosted Ubuntu CI uses `npm --prefix scripts run check:report:ci` to skip the redundant Windows parity audit; Windows parity is enforced in the dedicated Windows job
  - Includes `dev/feature_state_audit.py` so feature-state claims stay structured and evidence-backed
- Feature-state matrix audit:
  `dev/feature_state_audit.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:state`
  - `check:state` compares against `HEAD` so status/default-behavior transitions need matching verification and evidence updates
- Canonical documentation reference integrity check:
  `dev/check_doc_references.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:docs:report`
  - Verifies the canonical routing/policy docs carry top metadata (`Status`, `Role`, `Last updated`) and point at real files so documentation authority stays operable
  - Complements `feature_state_audit.py`, which remains the dedicated structural audit for `docs/developer/feature_state_matrix.md`
- Project structure inventory:
  `dev/project_structure_inventory.py`
  - Exposed via `npm --prefix scripts run inventory:structure`
  - Emits JSON and Markdown under `docs/test_outputs/dev_workflow/`
  - Enumerates repo paths while ignoring local caches/build outputs and reports redundancy/staleness candidates without approving deletion
- Generated-output unnecessary audit:
  `dev/generated_output_unnecessary_audit.py`
  - Exposed via `npm --prefix scripts run inventory:unnecessary`
  - Emits JSON and Markdown under `docs/test_outputs/dev_workflow/`
  - Separates mechanically safe `definite_prune` groups from `review_only` and
    `retain` groups using exact non-output references, retained generated-output
    provenance references, and narrow generated-output rules
- Local SRS admission lab:
  `dev/srs_admission_lab_server.py`
  - Exposed via `npm --prefix scripts run dev:srs-admission-lab`
  - Serves a read-only localhost UI for comparing neutral and preference-shaped
    admission previews without mutating SRS store state
  - Uses the same helper admission preview path as the extension and testing
    harnesses, with per-request temporary helper data roots
- Changed-scope workflow check (changed-only health + changed-file Ruff advisory + generated artifact freshness + rulegen-quality detection):
  `dev/dev_workflow_changed_check.py`
  - Optional JSON report via `--json-out` or `npm --prefix scripts run check:changed:report`
  - Tracks both total changed files and substantive changed files so Python AST-equivalent churn, JSON pretty-print churn, and Markdown/text reflow do not automatically trigger heavy quality loops
  - Runs the canonical documentation reference check when canonical docs change or when referenced source files under `apps/`, `core/`, `scripts/`, or `.github/` move/change materially
  - Uses the changed-file health gate with baseline warning-delta checks, so new/regressed warning debt is blocked alongside new/regressed violations
  - Automatically runs the Windows parity audit when parity-related GUI/helper/build files change
- Workflow Markdown summary renderer for JSON reports:
  `dev/dev_workflow_summary.py`
  - Used by `npm --prefix scripts run check:summary` and CI step summaries
  - Includes first-failure stdout/stderr tails and missing-artifact lists when the JSON report contains them
- CI report gate for JSON workflow artifacts:
  `dev/ci_report_gate.py`
  - Lets CI upload summaries/artifacts first, then fail the job from `check` / `build` / parity / gate JSON status
- Cross-platform Python launcher for npm workflow scripts:
  `dev/run_python.js`
  - Keeps `npm --prefix scripts run check` / `build` / quality wrappers usable on Windows where `python3` may not exist by name
  - Requires Python 3.10 and prefers the repository `.venv`, an active virtualenv, or an explicit interpreter instead of silently accepting an unrelated local Python
- Python environment bootstrap:
  `dev/bootstrap_python_env.js` plus `dev/python_environment.js`
  - `setup:python` creates/synchronizes the Python 3.10 development environment
  - `setup:python:build` adds the maintained GUI packaging dependencies
  - matching `*:check` commands verify the environment without mutating it
- Repo-wide style check (Ruff lint + format check, optional strict mode via `--strict` / `check:style:strict`):
  `dev/dev_workflow_style_check.py`
  - JSON artifact via `npm --prefix scripts run check:style:report`
  - `npm --prefix scripts run check` now runs the strict style gate directly
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
  - On macOS, `npm --prefix scripts run build:gui:install:relaunch` provides the validated build/install/verify/relaunch lifecycle while preserving user data
- Build installers: `build/installer.py`
- Convert embeddings: `data/convert_embeddings.py`
- Convert FreeDict TEI to SQLite: `data/convert_freedict_tei_to_sqlite.py`
- Convert FreeDict Spanish->English to SQLite: `data/convert_freedict_spa_eng_to_sqlite.py`
- Convert FreeDict English->Spanish to SQLite: `data/convert_freedict_eng_spa_to_sqlite.py`
- Convert Kaikki/Wiktionary glosses to compatibility SQLite: `data/convert_kaikki_glosses_to_sqlite.py`
- Convert Kaikki Spanish->English glosses to compatibility SQLite: `data/convert_kaikki_es_en_to_sqlite.py`
- Convert Spanish frequency sample to SQLite: `data/convert_cde_frequency_to_sqlite.py`
- Probe rulegen ranking on fixed words (`hora`, `trabajo`, `様`, `時`) with tunable scoring/caps:
  `testing/rulegen_probe_words.py` (for example `--max-definitions`, `--max-rules-per-target`, `--disable-pos-scoring`, `--reverse-check-enabled`, `--reverse-check-far-hit-penalty`, `--translation-dict-es-en-reverse`; prints reverse-check hit/miss metadata in uncapped/capped views and can probe `en-es` without requiring JMDict when `--japanese-targets ''`)
- Benchmark rulegen parameter sweeps against labeled cases and produce ranked JSON/Markdown reports:
  `testing/rulegen_benchmark.py` (dataset default: `docs/test_inputs/rulegen_benchmark_cases/`, accepts pair-specific translation dictionary overrides such as `--translation-dict-en-es`, emits styled HTML with right-click source labeling, LP-by-LP workflow controls, and skip/done navigation; omit `--pairs` to process all LPs in one run)
- Render Markdown summaries from benchmark JSON artifacts:
  `testing/rulegen_benchmark_summary.py` (also exposed via `npm --prefix scripts run quality:rulegen:benchmark:summary`)
- Focused audit cycle for selected pairs (benchmark -> quality gate -> triage) with sensible defaults for `en-es,en-ja`:
  `testing/rulegen_pair_audit_cycle.py` (also forwards reverse-check tuning values, accepts named reverse-check profiles such as `far-hit-experiment`, and can emit quality-gate JSON)
- First-class `en-es` reverse-check lane:
  `npm --prefix scripts run quality:rulegen:reverse:en-es` plus `npm --prefix scripts run quality:rulegen:reverse:summary`
- Durable `en-es` reverse-check run matrix:
  `npm --prefix scripts run quality:rulegen:reverse:matrix`
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
- Item-level SRS journey harness for deterministic `en-ja` bootstrap -> feedback -> refresh -> publication phase analysis:
  `testing/srs_journey_harness.py` (also exposed via `npm --prefix scripts run quality:srs:journey`)
- Edge-behavior SRS journey lane for duplicate feedback and exposure-only analysis:
  `testing/srs_journey_harness.py --scenario en-ja_edge_behaviors_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:edge`)
- Real-publication SRS journey lane for deterministic candidates plus real helper/rulegen publication:
  `testing/srs_journey_harness.py --scenario en-ja_real_publication_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:real`)
- Installed-resource SRS journey lane for real local packs plus dynamic cohort assignment:
  `testing/srs_journey_harness.py --scenario en-ja_installed_data_journey_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:installed`)
- `en-es` parity journey lanes mirror the same three surfaces with Spanish fixtures and real `en-es` publication:
  `testing/srs_journey_harness.py --scenario en-es_core_journey_v1`, `--scenario en-es_edge_behaviors_v1`, and `--scenario en-es_real_publication_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:en-es`, `quality:srs:journey:en-es:edge`, and `quality:srs:journey:en-es:real`)
- `en-es` installed-resource journey lane mirrors the same real-data review flow with local Spanish packs:
  `testing/srs_journey_harness.py --scenario en-es_installed_data_journey_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:en-es:installed`)
- `en-es` profile-preference journey lane proves profile-aware bootstrap plus feedback-loop continuity:
  `testing/srs_journey_harness.py --scenario en-es_profile_preference_journey_v1` (also exposed via `npm --prefix scripts run quality:srs:journey:en-es:profile`)
- Render Markdown summaries from SRS journey JSON artifacts:
  `testing/srs_journey_summary.py` (also exposed via `npm --prefix scripts run quality:srs:journey:summary`)
- Render interactive HTML pedagogical review surfaces from SRS journey JSON artifacts:
  `testing/srs_journey_html.py` (also exposed via `npm --prefix scripts run quality:srs:journey:html`, `quality:srs:journey:edge:html`, `quality:srs:journey:real:html`, `quality:srs:journey:installed:html`, and the matching `quality:srs:journey:en-es:*:html` commands)
- Dev helper cycle: `dev/dev_cycle.sh`
- Project health gate (architecture maintainability metrics): `dev/check_project_health.js`
  - Supports advisory/global, changed-only scope, baseline delta gating, JSON report output, and baseline snapshot output.
- SRS selector demo against the fixed technical dataset:
  `dev/srs_selector_demo.py`
- Manual embedding similarity probe for operator-provided vector or SQLite files:
  `dev/test_embeddings.py --embeddings /path/to/embeddings.sqlite`
- Semantic-shadow review queue and packet generators for the research-only
  `en-es` shadow-mining lane:
  `testing/semantic_shadow_review_queue_en_es.py` and
  `testing/semantic_shadow_review_packet_en_es.py`
- Manual profile backup/restore helpers:
  `backup_profiles.sh PROFILE_ID [PROFILE_ID ...]` and
  `restore_profiles_backup.sh /full/path/to/profiles_backup_<profile_ids>_<timestamp>`

## Specialty Tools

- Audit licensing headers for `expected-not-verified` packs: `dev/licensing_header_audit.py`
- Download and inspect source archive headers for licensing verification (dev-only): `dev/licensing_source_header_fetch.py`
