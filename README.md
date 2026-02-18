# LexiShift

LexiShift is a local-first language-learning toolkit for controlled text replacement and SRS-assisted practice.

It combines:
- a desktop GUI app for profile/ruleset authoring,
- a Chrome extension for runtime replacements and SRS interactions,
- a BetterDiscord plugin runtime,
- and a native helper for local SRS/rulegen workflows.

## User Quick Start

1. Open the onboarding guide: `docs/getting-started/README.md`.
2. Create a profile and ruleset in the desktop app.
3. Load the extension from `apps/chrome-extension/` and configure options.
4. (Optional) Enable helper-backed SRS flows for init/refresh/feedback sync.

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
```

Core checks:
```bash
python -m unittest discover -s core/tests
ruff format .
mypy core/lexishift_core
```

Run main surfaces:
```bash
python apps/gui/src/main.py
```
- Chrome extension: load `apps/chrome-extension/` as unpacked.
- BetterDiscord plugin build: `node apps/betterdiscord-plugin/build_plugin.js`.

For full developer workflows, read `docs/developer/README.md`.

## Repository Layout

- `apps/gui/`: desktop app (PySide6)
- `apps/chrome-extension/`: browser runtime + options UI
- `apps/betterdiscord-plugin/`: BetterDiscord runtime
- `core/lexishift_core/`: replacement, SRS, helper, and rulegen core logic
- `scripts/`: build/data/dev/helper/testing scripts
- `docs/`: architecture, schemas, runbooks, and roadmap/TODO docs

## Documentation

User-oriented:
- Getting started guide: `docs/getting-started/README.md`
- Manual entrypoint: `docs/index.md`
- Handbook entrypoint (Pages): `docs/handbook/index.md`
- Rendered diagrams page: `docs/handbook/diagrams.md`

Developer-oriented:
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
