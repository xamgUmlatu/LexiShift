# Semantic Routing HTML

Status: active local preview guide
Role: Runbook / operational
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 auxiliary README note; local server flow not rerun
Purpose: explain how to serve and inspect the auxiliary semantic-routing HTML preview pages
Source-of-truth: preview guide only; diagram source lives in `docs/rulegen/semantic_routing_veto_e2e_diagram.mmd` and semantic runtime truth lives in code, tests, and canonical semantic-veto docs.

Serve the `docs/` directory locally and open:

- `/semantic_routing_html/`
- `/semantic_routing_html/veto_e2e.html`

Quick start:

```bash
cd docs
python3 -m http.server 8000
```

Then open:

- `http://127.0.0.1:8000/semantic_routing_html/`

The veto diagram page fetches its Mermaid source from:

- `docs/rulegen/semantic_routing_veto_e2e_diagram.mmd`
