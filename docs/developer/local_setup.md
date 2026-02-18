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
```

## Core Validation Loop

```bash
python -m unittest discover -s core/tests
ruff format .
mypy core/lexishift_core
```

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
