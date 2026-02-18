# Architecture Diagrams Tracker

Status: Active  
Last updated: 2026-02-19

This folder tracks the six high-priority architecture diagrams used to maintain continuity across work sessions.

## Diagram Status Matrix

| ID | File | Scope | Status | Confidence | Last verified |
|---|---|---|---|---|---|
| DG-01 | `DG-01_data_ownership_storage_as_is.mmd` | Data ownership + storage layout | Draft skeleton | Medium | 2026-02-19 |
| DG-02 | `DG-02_settings_propagation_as_is.mmd` | Settings propagation (Options -> runtime mirrors -> content) | Draft skeleton | Medium | 2026-02-19 |
| DG-03 | `DG-03_rule_resolution_dom_pipeline_as_is.mmd` | Rule resolution + DOM replacement pipeline | Draft skeleton | Medium | 2026-02-19 |
| DG-04 | `DG-04_feedback_eventual_sync_as_is.mmd` | Feedback + eventual sync queue/retry path | Draft skeleton | Medium | 2026-02-19 |
| DG-05 | `DG-05_srs_init_refresh_control_as_is.mmd` | SRS initialize/refresh helper control flow | Draft skeleton | Medium | 2026-02-19 |
| DG-06 | `DG-06_helper_availability_state_as_is.mmd` | Helper availability and degraded mode state model | Draft skeleton | Medium | 2026-02-19 |

## Update Checklist

When a diagram is updated:

1. Confirm whether the update is `[AS-IS]` or `[TARGET]`.
2. Re-check source docs and current code paths.
3. Update this table (`Status`, `Confidence`, `Last verified`).
4. If unresolved assumptions remain, document them in:
   - `docs/architecture/design_diagram_workplan.md`
   - `docs/architecture/chrome_web_store_review_working_doc.md` (if policy/product-impacting)

## Quick View Options

Fast local render (no project setup needed, uses `npx`):

```bash
npx -y @mermaid-js/mermaid-cli \
  -i docs/architecture/diagrams/DG-01_data_ownership_storage_as_is.mmd \
  -o /tmp/DG-01.svg
```

Batch render all diagram files:

```bash
for f in docs/architecture/diagrams/*.mmd; do
  base="$(basename "$f" .mmd)"
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "/tmp/${base}.svg"
done
```

Render all diagrams directly into GitHub Pages assets:

```bash
mkdir -p docs/assets/diagrams
for f in docs/architecture/diagrams/*.mmd; do
  base="$(basename "$f" .mmd)"
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "docs/assets/diagrams/${base}.svg"
done
```

Pages view:
- `../../handbook/diagrams.md`
