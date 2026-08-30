# Resource Recovery Playbook (Frequency + Dictionary Baseline)

Status: active recovery playbook
Role: Runbook / operational
Last updated: 2026-06-08
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

## Source-Stack Registry

LP onboarding source choices now have a machine-readable registry:

- `core/lexishift_core/helper/source_stacks.py`

Use that file as the first code-level answer for "what data does this LP use?"
It records default frequency, translation, reverse-check, POS overlay, and
candidate enrichment resources by role.

The Settings -> Language Packs -> Learning Languages setup cards consume the
same registry, filtered to resource families the current GUI can install or
open for manual setup (`frequency`, `language`, `pos_overlay`, and
`semantic_pack`). Runtime
diagnostics expose the full stack under `source_stack`, with missing hard resources separated from
recommended enrichment:

- `source_stack_missing_required`
- `source_stack_missing_recommended`

Current notable behavior:

- `en-de` setup shows `freq-de-default`, `freedict-de-en`, and
  `freedict-en-de`, plus a pending semantic reference row so the missing
  sentence-veto reference pack is explicit but non-blocking.
- `en-es` setup keeps the existing three visible resources:
  `freq-es-spalex-v1`, `wiktionary-es-en`, and `freedict-es-en`, plus
  recommended POS enrichment `pos-es-ud-ancora-v1` and the recommended
  `en-es-active-only-combined-full-v1-tranche-011` semantic reference pack.
- `pos-es-ud-ancora-v1` is a first-class learning-pair setup resource. It is
  shown as recommended rather than required for pair readiness.
- The `en-es` semantic reference install writes only the pair-level pack copy
  under `language_packs/en-es/semantic_packs/<pack_id>/`; profile-local runtime
  semantic artifacts are still created by the normal SRS publication/refresh
  path after that reference is installed.

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
- `en-en`, `de-en`, `es-en` -> managed `freq-en-leipzig-default/main.sqlite`;
  legacy/manual fallback `freq-en-coca.sqlite`
- `en-de`, `de-de` -> `freq-de-default.sqlite`
- `en-es`, `es-es` -> `freq-es-spalex-v1.sqlite` or managed
  `freq-es-spalex-v1/main.sqlite`. `freq-es-cde` is retired from runtime
  fallback and should remain only as a historical/manual benchmark artifact.
- `en-zh` -> `freq-zh-default.sqlite` (placeholder convention)

## Spanish POS Overlay Recovery

`freq-es-spalex-v1` is frequency-only. For en-es/es-es admission POS parity,
use Settings -> Language Packs -> Learning Languages to download
`pos-es-ud-ancora-v1`, or rebuild the clean POS overlay from UD Spanish AnCora:

```bash
PYTHONPATH=core python3 scripts/data/build_ud_ancora_pos_overlay_es.py \
  --download-sources \
  --source-dir /tmp/lexishift-ud-ancora-source \
  --pack-root "$HOME/Library/Application Support/LexiShift/LexiShift/pos_packs/pos-es-ud-ancora-v1" \
  --overwrite \
  --write-sidecars
```

The helper discovers this installed overlay automatically for Spanish-target SRS
pairs. The overlay is keyed by Spanish word form to match SPALEX `spelling`.

## Semantic Reference Pack Recovery

For `en-es`, use Settings -> Language Packs -> Learning Languages to install
the recommended sentence-veto semantic reference pack. This copies the local
reference inventory into:

```text
$DATA_ROOT/language_packs/en-es/semantic_packs/en-es-active-only-combined-full-v1-tranche-011/semantic_inventory.json
```

After installing the reference pack, refresh or republish the Vocabulary
Practice story so normal rulegen can attach semantic evidence to eligible rules.
For `en-de`, the Learning Languages card intentionally shows the semantic
reference row as pending because no comparable reference pack is declared yet.

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
