---
layout: default
title: Release Guide
---

# Release Guide

This page is the concise release flow for packaging and Chrome Web Store readiness.

Quick navigation:
- [Home]({{ '/handbook/' | relative_url }}) | [Developer]({{ '/handbook/developer/' | relative_url }}) | [Architecture]({{ '/handbook/architecture/' | relative_url }}) | [Release]({{ '/handbook/release/' | relative_url }}) | [Diagrams]({{ '/handbook/diagrams/' | relative_url }})

## Build App Bundles

```bash
python scripts/build/gui_app.py
python scripts/build/gui_app.py --validate
```

Installers:

```bash
python scripts/build/installer.py
python scripts/build/installer.py --validate
```

## CWS Preflight Gate

```bash
npm --prefix scripts run preflight:cws
```

References:
- Upload gate runbook: [../runbooks/cws_upload_gate.md](../runbooks/cws_upload_gate.md)
- Preflight reports folder: [../runbooks/cws_preflight_reports/README.md](../runbooks/cws_preflight_reports/README.md)

## Policy And Decision Context

- Review working doc: [../architecture/chrome_web_store_review_working_doc.md](../architecture/chrome_web_store_review_working_doc.md)
- Native messaging execution checklist: [../architecture/native_messaging_checklist.md](../architecture/native_messaging_checklist.md)
