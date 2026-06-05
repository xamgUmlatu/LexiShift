# LexiShift

Status: active repo entrypoint
Role: Canonical current
Last updated: 2026-03-21
Last verified: 2026-03-21 repo-entry routing review
Purpose: user/developer entry routing for the maintained product and documentation surfaces
Source-of-truth: entry routing only; defer runtime behavior to source code and `docs/developer/feature_state_matrix.md`.

LexiShift is a local-first language-learning toolkit for controlled text replacement and SRS-assisted practice.

It combines:
- a desktop GUI app for profile/ruleset authoring,
- a Chrome extension for runtime replacements and SRS interactions,
- a BetterDiscord plugin runtime,
- and a native helper for local SRS/rulegen workflows.

## User Quick Start

1. Open the guide: `docs/guide/README.md`.
2. Create a profile in the desktop app.
3. Load the extension from `apps/chrome-extension/` and configure options.
4. Start Vocabulary Practice for the profile and language pair you want to test.

If you prefer the GitHub Pages manual view, use `docs/index.md` (and its linked pages).

## Developer Quick Start

Prerequisites:
- Python 3.10+
- Node.js 20+
- Chrome (for extension testing)

Setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
npm --prefix scripts run hooks:install
```

Default local safety loop:
```bash
npm --prefix scripts run check
```

Build/package safety when those surfaces are touched:
```bash
npm --prefix scripts run build
```

Current developer entrypoints:
- `docs/developer/README.md`
- `docs/developer/local_setup.md`
- `docs/developer/build_and_release.md`
- `docs/developer/feature_state_matrix.md`

Run main surfaces:
- Desktop GUI: `python apps/gui/src/main.py`
- Chrome extension: load `apps/chrome-extension/` as unpacked
- BetterDiscord plugin build: `node apps/betterdiscord-plugin/build_plugin.js`

## Repository Layout

- `apps/gui/`: desktop app (PySide6)
- `apps/chrome-extension/`: browser runtime + options UI
- `apps/betterdiscord-plugin/`: BetterDiscord runtime
- `core/lexishift_core/`: replacement, SRS, helper, and rulegen core logic
- `scripts/`: build/data/dev/helper/testing scripts
- `docs/`: architecture, schemas, runbooks, and roadmap/TODO docs

## Documentation

Current user/developer routing:
- User guide: `docs/guide/README.md`
- Manual entrypoint: `docs/index.md`
- Handbook entrypoint (Pages): `docs/handbook/index.md`
- Rendered diagrams page: `docs/handbook/diagrams.md`
- Developer docs hub: `docs/developer/README.md`
- Developer handbook: `docs/developer/developer_reference.md`
- Architecture map/status: `docs/architecture/README.md`
- Documentation map: `docs/README.md`
- Script map: `scripts/README.md`

Planning and decisions:
- Consolidated backlog: `docs/TODOs.md`
- CWS review working doc: `docs/architecture/chrome_web_store_review_working_doc.md`
- Diagram workplan: `docs/architecture/design_diagram_workplan.md`

## Legacy Snapshot

The previous root README snapshot is preserved at:
- `docs/developer/legacy_root_readme_snapshot.md`
