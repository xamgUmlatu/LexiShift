# Phase 6 POS Inventory Artifacts

This folder stores reproducible POS-inventory audit outputs for installed frequency packs.

Generator:

```bash
python3 scripts/testing/pos_inventory_audit.py \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_YYYY-MM-DD.json
```

Notes:

- The audit reads `meta.metadata` from each frequency SQLite file.
- For DE build outputs, POS inventory is read from `meta.metadata.pos_inventory`.
- Unknown-tag counts (`unknown_pos_inventory_size`) are expected to be non-zero until mapping profiles are expanded.
- Metadata counts are conversion-time snapshots. After mapping changes, regenerate packs (or run runtime probe) to observe updated unknown rates.

Runtime probe artifact example:

- `phase6_pos_probe_after_other_mapping_2026-02-23.json`
