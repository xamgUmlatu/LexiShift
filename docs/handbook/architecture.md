---
layout: default
title: Architecture Guide
---

<!--
Status: active Pages architecture guide
Role: Mixed
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 site-doc authority note; architecture claims not fully re-audited
Purpose: route GitHub Pages readers to stable architecture contracts, planning docs, rendered diagrams, and code-level source pointers
Source-of-truth: routing guide only; authoritative architecture classification lives in `docs/architecture/README.md` and executable truth remains in source code and tests.
-->

# Architecture Guide

Use this page to navigate stable architecture contracts vs planning docs.

Quick navigation:
- [Home]({{ '/handbook/' | relative_url }}) | [Developer]({{ '/handbook/developer/' | relative_url }}) | [Architecture]({{ '/handbook/architecture/' | relative_url }}) | [Release]({{ '/handbook/release/' | relative_url }}) | [Diagrams]({{ '/handbook/diagrams/' | relative_url }})

## Stability-First Reading Order

1. [Architecture status index](../architecture/README.md)
2. [Extension system map](../architecture/extension_system_map.md)
3. [Extension technical notes](../architecture/chrome_extension_technical.md)
4. [Options controller architecture](../architecture/options_controllers_architecture.md)
5. [SRS LP architecture contract](../architecture/srs_lp_architecture.md)

## Data Layout And Flow

- Data/storage map source: [Developer handbook data layout section](../developer/developer_reference.md)
- Diagram workplan: [../architecture/design_diagram_workplan.md](../architecture/design_diagram_workplan.md)
- Rendered diagrams: [./diagrams/](./diagrams/)

## Open Decision Logs

- CWS/policy working doc: [../architecture/chrome_web_store_review_working_doc.md](../architecture/chrome_web_store_review_working_doc.md)
- Backlog and active improvements: [../TODOs.md](../TODOs.md)

## Source-Of-Truth Files (Code-Level)

- Extension runtime load order: `apps/chrome-extension/manifest.json`
- Options controller composition: `apps/chrome-extension/options/core/bootstrap/controller_graph.js`
- Shared storage defaults: `apps/chrome-extension/shared/settings/settings_defaults.js`
