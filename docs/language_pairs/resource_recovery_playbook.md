# Resource Recovery Playbook (Frequency + Dictionary Baseline)

Status: active recovery playbook
Role: Runbook / operational
Last updated: 2026-02-22
Last verified: 2026-05-14 metadata-only Lane 1 language-pair authority note; recovery commands not rerun
Source-of-truth: operational recovery playbook; current resource requirements and executable truth live in LP resource docs, capability/resource code, audit scripts, and generated audit outputs.

## Purpose

Provide deterministic recovery steps for broken or missing LP resources, especially
frequency SQLite packs used by SRS and rulegen seed paths.

## First Diagnostic Step

Run the frequency integrity/linkage audit:

```bash
python3 scripts/testing/resource_integrity_audit.py
```

Optional JSON artifact:

```bash
python3 scripts/testing/resource_integrity_audit.py \
  --json-out docs/test_outputs/resource_integrity_audit/latest.json
```

Use this report to identify the exact failure mode before changing files.

## Failure Modes and Recovery

### 1) Downloaded but unlinked

Symptoms (audit):
- `FILE_UNLINKED`
- `FREQ_DOWNLOADED_UNLINKED`

Recovery:
1. Open LexiShift settings -> Language Packs -> Frequency Packs.
2. Click `Link local` (or re-download) for the target pack.
3. Save settings.
4. Re-run `resource_integrity_audit.py` and confirm status becomes `linked`.

Notes:
- This is linkage-only; file content may already be valid.

### 2) Linked path is missing

Symptoms (audit):
- `SETTINGS_PATH_MISSING`
- `FREQ_LINK_BROKEN`

Recovery:
1. In settings UI, remove stale link for the affected pack.
2. Re-link to the existing valid file, or download/rebuild the pack.
3. Save settings.
4. Re-run audit.

### 3) Invalid SQLite header / not an SQLite file

Symptoms (audit):
- `SETTINGS_INVALID_SQLITE`
- `FILE_INVALID_SQLITE`
- message contains `Invalid SQLite header` or open failure

Recovery:
1. Delete the broken file.
2. Re-download via settings UI, or rebuild with official converter/build script.
3. Re-link pack if needed.
4. Re-run audit.

### 4) Missing `frequency` table

Symptoms (audit):
- `SETTINGS_INVALID_SQLITE`
- `FILE_INVALID_SQLITE`
- message contains `Missing table 'frequency'`

Recovery:
1. Rebuild the DB from source corpus with the expected converter/pipeline.
2. Verify schema manually:

```bash
sqlite3 /path/to/freq-pack.sqlite ".tables"
sqlite3 /path/to/freq-pack.sqlite "PRAGMA table_info(frequency);"
```

3. Re-link in settings and re-run audit.

### 5) Empty frequency table

Symptoms (audit):
- `SETTINGS_EMPTY_TABLE`
- `FILE_EMPTY_TABLE`

Recovery:
1. Treat as failed conversion/build.
2. Re-run conversion/build script with overwrite.
3. Re-check row count:

```bash
sqlite3 /path/to/freq-pack.sqlite "SELECT COUNT(*) FROM frequency;"
```

4. Re-run audit.

### 6) Pair-level missing default DB

Symptoms (audit):
- `FREQ_MISSING` for an LP

Recovery:
1. Download/build the expected default DB for that pair target language.
2. Link it under `synonyms.frequency_packs` (via settings UI).
3. Re-run audit to verify pair status.

## Pair-Specific Expected Frequency DBs (Current Defaults)

From `core/lexishift_core/helper/lp_capabilities.py`:

- `en-ja`, `ja-ja` -> `freq-ja-bccwj.sqlite`
- `en-en`, `de-en`, `es-en` -> `freq-en-coca.sqlite`
- `en-de`, `de-de` -> `freq-de-default.sqlite`
- `en-es`, `es-es` -> `freq-es-cde.sqlite`
- `en-zh` -> `freq-zh-default.sqlite` (placeholder convention)

## Verification Checklist After Recovery

1. `python3 scripts/testing/resource_integrity_audit.py` shows no `ERROR`.
2. Affected pair row status is `linked` (or expected project state).
3. Frequency table row count is non-zero.
4. Optional POS check:

```bash
python3 scripts/testing/pos_normalization_probe.py \
  --pairs en-ja,en-es,es-en,en-de \
  --top-n 2000
```

This confirms both resource integrity and POS interpretation baseline.
