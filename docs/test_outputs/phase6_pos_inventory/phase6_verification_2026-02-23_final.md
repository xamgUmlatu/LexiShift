# Phase 6 POS Verification (Final Bundle)

Date (UTC): 2026-02-23

## Commands Run

1. `python3 -m venv .venv && .venv/bin/pip install simplemma` (local runtime dependency for DE lemmatization build path)
2. `PYTHONPATH=core .venv/bin/python -m lexishift_core.frequency.de.pipeline --overwrite --drop-proper-nouns`
3. `python3 scripts/testing/pos_inventory_audit.py --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json`
4. `python3 scripts/testing/pos_normalization_probe.py --pairs en-ja,en-es,es-en,en-de --top-n 1000 --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json`
5. `python3 scripts/testing/resource_integrity_audit.py --json-out docs/test_outputs/phase6_pos_inventory/phase6_resource_integrity_2026-02-23_final.json`
6. `pytest -q core/tests/pos/test_pos_normalization.py core/tests/rulegen/test_rulegen_pos_metadata.py core/tests/srs/test_srs_seed.py core/tests/srs/test_srs_admission_policy.py core/tests/srs/test_srs_admission_refresh.py core/tests/frequency/test_frequency_sqlite_converter.py core/tests/resources/test_dict_loaders_freedict_pos.py`

## Results

- Targeted tests: `36 passed in 0.19s`
- POS pair probe:
  - `en-ja`: `mapped_rate=1.000`, `bucket_mismatch_rate=0.000`
  - `en-es`: `mapped_rate=1.000`, `bucket_mismatch_rate=0.000`
  - `es-en`: `mapped_rate=1.000`, `bucket_mismatch_rate=0.000`
  - `en-de`: `mapped_rate=1.000`, `bucket_mismatch_rate=0.000`
- POS inventory audit warnings:
  - `freq-de-default.sqlite`: unknown tag inventory present (`ZUS`, `S`, `PA2:PRD:GRU`, ...)
  - `freq-en-coca.sqlite`: unknown tag inventory present (`u`)
  - `freq-ja-bccwj.sqlite`: unknown tag inventory present (`接尾辞-名詞的-一般`, `接頭辞`, ...)
- Resource integrity audit warnings:
  - Missing `freq-zh-default.sqlite` for inactive `en-zh` placeholder pair

## Interpretation

- POS normalization architecture and tests are complete for implemented pairs.
- Active SRS pairs have valid linked frequency DBs in local settings; DE pack recovery is complete.
- Remaining warning is outside active verification scope (`en-zh` placeholder resource not provisioned).
