# Local Setup And Development Loops

Status: active runbook
Role: Runbook / operational
Last updated: 2026-03-17
Last verified: 2026-03-17 package-script inventory review + local repo-safety runs
Purpose: current setup, validation, and day-to-day development entrypoints for contributors
Source-of-truth: workflow runbook; operational behavior is defined by `scripts/package.json`, `AGENTS.md`, and the scripts under `scripts/dev/` and `scripts/testing/`.

Use this page for current local setup and day-to-day validation loops.
For cross-cutting workflow status or known contradictions, defer to `feature_state_matrix.md`.

## Prerequisites

- Python 3.10+
- Node.js 20+
- Chrome (for extension runtime tests)
- BetterDiscord (optional, for plugin runtime tests)

## First-Time Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
npm --prefix scripts run hooks:install
```

GUI packaging / hosted macOS build-validation deps:

```bash
pip install -r requirements-build.txt
```

Installed pre-commit hooks currently cover:
- whitespace / EOF / YAML / TOML hygiene
- Ruff lint
- Ruff formatting
- BetterDiscord generated bundle freshness
- feature-state ledger structure/evidence audit
- changed-only project health gating against the checked-in baseline
- pre-push repo safety via `npm --prefix scripts run check` (including strict Windows parity audit)

`npm --prefix scripts run hooks:install` installs both `pre-commit` and `pre-push` hooks.
Current split:
- `pre-commit`: hygiene fixers, Ruff lint/format, BetterDiscord freshness, changed-only project health
- `pre-push`: repo safety via `npm --prefix scripts run check`

## Core Validation Loop

```bash
npm --prefix scripts run check
```

Machine-readable report:

```bash
npm --prefix scripts run check:report
```

Failed commands now keep stdout/stderr tail lines in the JSON report so CI artifact summaries can show the first actionable failure without relying only on raw hosted logs.

Feature-state discipline audit:

```bash
npm --prefix scripts run check:state
```

This compares the current ledger against `HEAD` and fails if status/default-behavior transitions do not bring matching verification/evidence updates.

Markdown summary from the latest workflow reports:

```bash
npm --prefix scripts run check:summary
```

Windows GUI parity audit:

```bash
npm --prefix scripts run check:windows:parity
npm --prefix scripts run check:windows:parity:summary
```

`npm --prefix scripts run check` already runs the strict parity audit. Use the standalone commands when you need the dedicated parity artifacts or are iterating on Windows-only workflow changes.

Rulegen artifact summaries:

```bash
npm --prefix scripts run quality:rulegen:benchmark:summary
npm --prefix scripts run quality:rulegen:gate:summary
npm --prefix scripts run quality:rulegen:triage:summary
```

This stable safety check currently runs:
- Python unit tests under `core/tests`
- `mypy core/lexishift_core`
- BetterDiscord generated bundle freshness check
- `py_compile` for workflow-critical Python entrypoints
- advisory project health checks

Repo-wide style lint is now part of the default `check` gate because the repo-wide Ruff debt was reduced to a clean baseline. Use the standalone style commands when you want dedicated artifacts or a style-only loop.

Style/debt advisory command:

```bash
npm --prefix scripts run check:style
npm --prefix scripts run check:style:report
npm --prefix scripts run check:style:summary
```

Strict variant for cleanup branches:

```bash
npm --prefix scripts run check:style:strict
```

The Ruff workflow scripts try the selected Python's `-m ruff` entrypoint first and then fall back to a standalone `ruff` executable on `PATH`. If neither exists, advisory style commands report `unavailable`, while strict variants still fail so the environment issue does not get mistaken for product debt.

Changed-scope branch command:

```bash
npm --prefix scripts run check:changed
```

`check:changed` reports both all touched files and substantive changed files. Heavier follow-on loops, such as rulegen audit inference, now key off the substantive set so Python AST-equivalent churn, JSON pretty-print churn, and Markdown/text reflow stay cheap.

This runs:
- changed-only project health against the checked-in baseline
- Ruff lint/format checks on changed Python files only
- feature-state transition audit when `docs/developer/feature_state_matrix.md` changes
- BetterDiscord generated bundle freshness when relevant files changed
- rulegen quality-loop detection, with a dry-run command when rulegen/POS quality work is detected

Machine-readable branch report:

```bash
npm --prefix scripts run check:changed:report
```

If branch-scope output is noisy on a long-running branch, use `check:changed:local` or `check:changed:staged` for the day-to-day loop and keep `check:changed` as the broader integration view.

Local working-tree scope:

```bash
npm --prefix scripts run check:changed:local
```

Staged-only scope:

```bash
npm --prefix scripts run check:changed:staged
```

## Build Safety

```bash
npm --prefix scripts run build
```

Machine-readable build report:

```bash
npm --prefix scripts run build:report
```

Failed build commands now keep stdout/stderr tail lines and missing-artifact details in the JSON report for the same reason.

This is the full build contract. Hosted macOS CI uses the same entrypoint.

CI-safe build report:

```bash
npm --prefix scripts run build:ci:report
```

This is the explicit non-macOS partial lane. It keeps the same report format while recording skipped GUI validation on unsupported hosts.

Synthetic SRS quality harness:

```bash
npm --prefix scripts run quality:srs:harness
npm --prefix scripts run quality:srs:summary
```

Item-level SRS journey harness:

```bash
npm --prefix scripts run quality:srs:journey
npm --prefix scripts run quality:srs:journey:summary
npm --prefix scripts run quality:srs:journey:html
npm --prefix scripts run quality:srs:journey:edge
npm --prefix scripts run quality:srs:journey:edge:summary
npm --prefix scripts run quality:srs:journey:edge:html
npm --prefix scripts run quality:srs:journey:real
npm --prefix scripts run quality:srs:journey:real:summary
npm --prefix scripts run quality:srs:journey:real:html
npm --prefix scripts run quality:srs:journey:installed
npm --prefix scripts run quality:srs:journey:installed:summary
npm --prefix scripts run quality:srs:journey:installed:html
npm --prefix scripts run quality:srs:journey:en-es
npm --prefix scripts run quality:srs:journey:en-es:summary
npm --prefix scripts run quality:srs:journey:en-es:html
npm --prefix scripts run quality:srs:journey:en-es:edge
npm --prefix scripts run quality:srs:journey:en-es:edge:summary
npm --prefix scripts run quality:srs:journey:en-es:edge:html
npm --prefix scripts run quality:srs:journey:en-es:real
npm --prefix scripts run quality:srs:journey:en-es:real:summary
npm --prefix scripts run quality:srs:journey:en-es:real:html
npm --prefix scripts run quality:srs:journey:en-es:installed
npm --prefix scripts run quality:srs:journey:en-es:installed:summary
npm --prefix scripts run quality:srs:journey:en-es:installed:html
```

This build safety currently runs:
- BetterDiscord plugin bundle build
- GUI PyInstaller build + bundle validation

## Runtime Surfaces

### Desktop GUI

```bash
python apps/gui/src/main.py
```

Alternate entrypoint:
```bash
python apps/gui/src
```

### Chrome Extension

1. Open `chrome://extensions`.
2. Enable developer mode.
3. Load unpacked extension folder: `apps/chrome-extension/`.
4. Open extension options and verify settings/state flow.

### BetterDiscord Plugin

Build plugin bundle:
```bash
node apps/betterdiscord-plugin/build_plugin.js
```

Optional helper scripts:
```bash
node apps/betterdiscord-plugin/watch_plugin.js
node apps/betterdiscord-plugin/sync_plugin.js
```

## Helper / Native Messaging Local Checks

Useful scripts:
- `scripts/dev/check_helper_status.sh`
- `scripts/dev/cleanup_helper.sh`
- `scripts/dev/dev_cycle.sh`

## CWS Upload Preflight Gate

```bash
npm --prefix scripts run preflight:cws
```

Reference:
- `../runbooks/cws_upload_gate.md`

## GitHub Pages Local Preview

From `docs/`, use the committed GitHub Pages Gemfile (no `/tmp` setup needed):

```bash
cd /Users/takeyayuki/Documents/projects/LexiShift/docs
bundle install
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000 --source .
```

Open:
- `http://127.0.0.1:4000/`

Notes:
- `docs/Gemfile` is pinned to the supported `github-pages` dependency set rather
  than a separate local Jekyll version.
- When GitHub Pages updates, refresh the Gemfile against
  `https://pages.github.com/versions/`.
- Hosted docs deployment is controlled by `.github/workflows/pages.yml`.
- Pull requests touching `docs/**` should now expect a dedicated Pages build
  validation workflow in GitHub Actions.

## Where To Go Next

- Architecture status + map: `../architecture/README.md`
- Full docs map: `../README.md`
- Script categories and common entry points: `../../scripts/README.md`
