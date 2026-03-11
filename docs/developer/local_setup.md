# Local Setup And Development Loops

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

Installed pre-commit hooks currently cover:
- whitespace / EOF / YAML / TOML hygiene
- Ruff formatting
- BetterDiscord generated bundle freshness
- changed-only project health gating against the checked-in baseline
- pre-push repo safety via `npm --prefix scripts run check`

`npm --prefix scripts run hooks:install` installs both `pre-commit` and `pre-push` hooks.

## Core Validation Loop

```bash
npm --prefix scripts run check
```

Machine-readable report:

```bash
npm --prefix scripts run check:report
```

Markdown summary from the latest workflow reports:

```bash
npm --prefix scripts run check:summary
```

This stable safety check currently runs:
- Python unit tests under `core/tests`
- `mypy core/lexishift_core`
- BetterDiscord generated bundle freshness check
- `py_compile` for workflow-critical Python entrypoints
- advisory project health checks

Repo-wide style lint is not yet the default `check` gate because `ruff check .` still has existing unrelated debt. Keep that debt explicit instead of making `check` permanently noisy.

Style/debt advisory command:

```bash
npm --prefix scripts run check:style
```

Strict variant for cleanup branches:

```bash
npm --prefix scripts run check:style:strict
```

Changed-scope branch command:

```bash
npm --prefix scripts run check:changed
```

This runs:
- changed-only project health against the checked-in baseline
- Ruff lint/format checks on changed Python files only
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

From `docs/`, use the committed Gemfile (no `/tmp` setup needed):

```bash
cd /Users/takeyayuki/Documents/projects/LexiShift/docs
bundle install
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000 --source .
```

Open:
- `http://127.0.0.1:4000/LexiShift/`

## Where To Go Next

- Architecture status + map: `../architecture/README.md`
- Full docs map: `../README.md`
- Script categories and common entry points: `../../scripts/README.md`
