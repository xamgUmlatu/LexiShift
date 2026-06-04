---
layout: default
title: Release Guide
---

<!--
Status: active Pages release guide
Role: Runbook / operational
Last updated: 2026-06-03
Last verified: 2026-06-03 hosting/distribution roadmap routing review and doc-reference check; release commands not rerun
Purpose: provide a concise Pages guide for packaging, installer validation, and Chrome Web Store readiness checks
Source-of-truth: user-facing release guide only; current build/release truth lives in build scripts, CWS runbooks, preflight outputs, and feature-state evidence.
-->

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
- Hosting/distribution roadmap: [../developer/hosting_distribution_roadmap.md](../developer/hosting_distribution_roadmap.md)
- Cloudflare distribution setup: [../runbooks/cloudflare_distribution_setup.md](../runbooks/cloudflare_distribution_setup.md)
- Upload gate runbook: [../runbooks/cws_upload_gate.md](../runbooks/cws_upload_gate.md)
- Preflight reports folder: [../runbooks/cws_preflight_reports/README.md](../runbooks/cws_preflight_reports/README.md)

## Policy And Decision Context

- Review working doc: [../architecture/chrome_web_store_review_working_doc.md](../architecture/chrome_web_store_review_working_doc.md)
- Native messaging execution checklist: [../architecture/native_messaging_checklist.md](../architecture/native_messaging_checklist.md)
