# Phase 6 POS Inventory Artifacts

This folder stores reproducible POS-inventory audit outputs for installed frequency packs.

Generator:

```bash
python3 scripts/testing/pos_inventory_audit.py \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_YYYY-MM-DD.json
```

Final verification bundle (2026-02-23):

```bash
python3 scripts/testing/pos_inventory_audit.py \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json

python3 scripts/testing/pos_normalization_probe.py \
  --pairs en-ja,en-es,es-en,en-de \
  --top-n 1000 \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json

python3 scripts/testing/resource_integrity_audit.py \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_resource_integrity_2026-02-23_final.json

pytest -q \
  core/tests/pos/test_pos_normalization.py \
  core/tests/rulegen/test_rulegen_pos_metadata.py \
  core/tests/srs/test_srs_seed.py \
  core/tests/srs/test_srs_admission_policy.py \
  core/tests/srs/test_srs_admission_refresh.py \
  core/tests/frequency/test_frequency_sqlite_converter.py \
  core/tests/resources/test_dict_loaders_freedict_pos.py \
  > docs/test_outputs/phase6_pos_inventory/phase6_targeted_tests_2026-02-23_final.txt
```

Notes:

- The audit reads `meta.metadata` from each frequency SQLite file.
- For DE build outputs, POS inventory is read from `meta.metadata.pos_inventory`.
- Unknown-tag counts (`unknown_pos_inventory_size`) are expected to be non-zero until mapping profiles are expanded.
- Metadata counts are conversion-time snapshots. After mapping changes, regenerate packs (or run runtime probe) to observe updated unknown rates.

Runtime probe artifact example:

- `phase6_pos_probe_after_other_mapping_2026-02-23.json`

Final bundle artifacts:

- `phase6_pos_inventory_2026-02-23_final.json`
- `phase6_pos_probe_2026-02-23_final.json`
- `phase6_resource_integrity_2026-02-23_final.json`
- `phase6_targeted_tests_2026-02-23_final.txt`
- `phase6_verification_2026-02-23_final.md`
