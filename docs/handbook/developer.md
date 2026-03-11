---
layout: default
title: Developer Workflow
---

# Developer Workflow

This page is the quick daily loop for LexiShift contributors.

Quick navigation:
- [Home]({{ '/handbook/' | relative_url }}) | [Developer]({{ '/handbook/developer/' | relative_url }}) | [Architecture]({{ '/handbook/architecture/' | relative_url }}) | [Release]({{ '/handbook/release/' | relative_url }}) | [Diagrams]({{ '/handbook/diagrams/' | relative_url }})

## Prerequisites

- Python 3.10+
- Node.js 20+
- Chrome (for extension tests)

## First-Time Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
npm --prefix scripts run hooks:install
```

## Daily Validation Loop

```bash
npm --prefix scripts run check
```

## Build Safety

```bash
npm --prefix scripts run build
```

## Run Surfaces

Desktop app:
```bash
python apps/gui/src/main.py
```

BetterDiscord plugin build:
```bash
node apps/betterdiscord-plugin/build_plugin.js
```

Chrome extension:
1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Load unpacked extension folder `apps/chrome-extension/`.

## Canonical Developer References

- Developer docs hub: [../developer/README.md](../developer/README.md)
- Developer handbook: [../developer/developer_reference.md](../developer/developer_reference.md)
- AI-assisted quality loop: [../developer/ai_workflow.md](../developer/ai_workflow.md)
- GenAI workflow architecture: [../developer/genai_workflow_architecture.md](../developer/genai_workflow_architecture.md)
- Feature state ledger: [../developer/feature_state_matrix.md](../developer/feature_state_matrix.md)
- Local setup detail: [../developer/local_setup.md](../developer/local_setup.md)
- Script categories: [../../scripts/README.md](../../scripts/README.md)

## Quality Automation

Rulegen/POS workflow wrappers:

```bash
python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-es
python3 scripts/testing/rulegen_auto_audit.py --base-ref origin/main
```

## Local Pages Preview

```bash
cd /Users/takeyayuki/Documents/projects/LexiShift/docs
bundle install
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000 --source .
```

Open:
- `http://127.0.0.1:4000/LexiShift/`
