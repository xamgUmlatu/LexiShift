# POS Source And Pipeline Reference

Status: active reference for POS behavior across SRS, rulegen, converters, and audits.
Last updated: 2026-03-22

## Purpose

This document is the single entrypoint for answering:

- where POS comes from for each language/source
- how raw POS becomes canonical POS
- where canonical POS affects runtime behavior
- where unknown tags are surfaced

Use this doc first before editing POS code.

## Canonical POS Contract

Canonical tags:

- `noun`
- `adjective`
- `verb`
- `adverb`
- `pronoun`
- `determiner`
- `adposition`
- `conjunction`
- `interjection`
- `numeral`
- `punctuation`
- `other`

Admission buckets (coarse):

- `noun`
- `adjective`
- `verb`
- `adverb`
- `other` (everything else)

Implementation:

- normalization: `core/lexishift_core/pos/normalization.py`
- admission bucket policy: `core/lexishift_core/srs/admission_policy.py`

## POS Source Matrix (Current Active Packs)

| Pack / source | Language target | Raw POS field | Normalization provider/profile | Converter/build path | Unknown tag inventory location |
| --- | --- | --- | --- | --- | --- |
| `freq-en-coca` | EN | `frequency.pos` | provider=`freq-en-coca`, profile=`compact-latin` | `scripts/data/convert_frequency_to_sqlite.py` and GUI path in `apps/gui/src/language_packs.py` | `meta.metadata.unknown_pos_inventory_*` |
| `freq-ja-bccwj` | JA | `frequency.pos` | provider=`freq-ja-bccwj`, profile=`bccwj` | `scripts/data/convert_bccwj_frequency_to_sqlite.py` and GUI path in `apps/gui/src/language_packs.py` | `meta.metadata.unknown_pos_inventory_*` |
| `freq-es-cde` | ES | `frequency.pos` | provider=`freq-es-cde`, profile=`freq-es-cde` | `scripts/data/convert_cde_frequency_to_sqlite.py` and GUI path in `apps/gui/src/language_packs.py` | `meta.metadata.unknown_pos_inventory_*` |
| `freq-de-default` | DE | `frequency.pos` (from compiled POS lexicon join) | provider=`freq-de-default`, profile=`freq-de-default` | `core/lexishift_core/frequency/de/build.py` and `core/lexishift_core/frequency/de/pipeline.py` | `meta.metadata.pos_inventory.unknown_pos_inventory_*` |
| FreeDict translation SQLite | EN/DE/ES pair pipelines | `entries.pos` (TEI `gramGrp/pos`) | provider includes `freedict`, profile=`freedict` | `scripts/data/convert_freedict_tei_to_sqlite.py` | `meta.metadata.unknown_pos_inventory_*` |
| Kaikki/Wiktionary compatibility SQLite (`wiktionary-es-en`) | EN/ES pair pipelines | `entries.pos` (derived from Kaikki record `pos`; native `pos_title` preserved in auxiliary metadata) | provider includes `wiktionary` / `kaikki`, profile=`wiktionary` | `scripts/data/convert_kaikki_glosses_to_sqlite.py` and GUI path in `apps/gui/src/language_packs.py` | converter metadata in `meta.metadata`; runtime unknown-tag behavior visible through the `wiktionary` normalization profile |

## Runtime POS Data Flow

1. Frequency row load -> seed candidate

- file: `core/lexishift_core/srs/seed.py`
- reads raw POS from `pos` column
- calls `normalize_pos(...)`
- stores:
  - `pos_raw`
  - `pos_canonical`
  - `pos_source_profile`
  - `pos_matched_rule`
  - `pos_mapped`

2. Admission weighting

- file: `core/lexishift_core/srs/admission_policy.py`
- uses canonical POS bucket when mapped
- fallback: raw-tag heuristics
- canonical `other` is a valid override and maps to bucket `other`

3. Rule generation scoring

- files:
  - `core/lexishift_core/rulegen/generation.py`
  - pair adapters in `core/lexishift_core/rulegen/pairs/`
- score behavior:
  - exact canonical match: `1.0`
  - compatibility-class match: `0.5`
  - unknown/missing: `0.0`

4. Refresh/selection optional POS filters

- files:
  - `core/lexishift_core/srs/selector.py`
  - `core/lexishift_core/srs/admission_refresh.py`
  - `core/lexishift_core/srs/growth.py`
- optional `allowed_pos` controls candidate filtering
- diagnostics include:
  - `filtered_by_pos`
  - `admitted_by_pos_bucket`
  - `unknown_pos_seen`

## Database Metadata Contract (POS)

Frequency converter/build metadata is written to `meta` table key `metadata`.

Expected POS fields (generic converter path):

- `rows_with_pos`
- `rows_without_pos`
- `pos_inventory_size`
- `pos_inventory_top`
- `unknown_pos_inventory_size`
- `unknown_pos_inventory_top`
- `pos_source_provider`
- `pos_mapping_profile`
- `pos_mapping_available`
- `pos_columns_resolved`

DE build path:

- same inventory keys under `meta.metadata.pos_inventory`

FreeDict converter:

- same top-level inventory keys in `meta.metadata`

Kaikki/Wiktionary converter:

- current converter writes general converter statistics in `meta.metadata`
- normalized POS for runtime comes from `entries.pos`
- richer source POS context is preserved in auxiliary tables:
  - `entry_meta.pos`
  - `entry_meta.pos_title`

## DE Flow Asymmetry (Important)

DE is intentionally more complex than EN/JA/ES frequency conversion.

Why:

- Leipzig frequency source does not provide canonical lemma POS aligned for our target schema.
- We enrich DE POS via LanguageTool resources and a compile/decompile pipeline.

DE POS source options:

- `german_dict` (preferred): decompile Morfologik `german.dict`, convert to TSV, compile to compact lexicon.
- `eig_sonstige` (fallback): merge legacy `EIG.txt` + `sonstige.txt`, compile to compact lexicon.

Isolation boundary:

- all DE-specific complexity is contained in:
  - `core/lexishift_core/frequency/de/`
  - DE branch in `core/lexishift_core/frequency/de/pipeline.py`
- runtime SRS/rulegen consumes DE the same way as other languages through normalized POS metadata.

Recommendation:

- keep DE asymmetry isolated in build-time tooling
- avoid introducing DE-only runtime branches beyond normalization profiles

## Unknown Tag Policy

Rules:

- unknown tags must map to canonical `other` (never crash/fail hard)
- unknown tags must be visible in converter/build metadata
- mapping updates require:
  - normalization rule update in `core/lexishift_core/pos/normalization.py`
  - unit tests in `core/tests/pos/test_pos_normalization.py`
  - rerun inventory audit and confirm unknown count changes

Do not guess mappings when source tag semantics are unclear.

Recent explicit `other` mappings (2026-02-23):

- compact-latin profile: `u -> other` (mapped)
- bccwj profile: `接頭辞 -> other` (mapped)
- bccwj profile: `接尾辞-* -> other` via head-token mapping (mapped)

Note:

- converter metadata unknown counts are snapshot-at-conversion values.
- runtime probe (`pos_normalization_probe.py`) reflects current normalization logic immediately.

Current Wiktionary profile note:

- `wiktionary` is now a first-class source profile in `core/lexishift_core/pos/normalization.py`.
- It intentionally uses generic + compact token matching rather than reusing the `freedict` profile by name.
- This keeps Kaikki/Wiktionary POS provenance explicit in candidate metadata and future audits.

## Audit Commands

Integrity/link audit:

```bash
python3 scripts/testing/resource_integrity_audit.py
```

POS inventory audit (recommended Phase 6 artifact):

```bash
python3 scripts/testing/pos_inventory_audit.py \
  --json-out docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_YYYY-MM-DD.json
```

Pair-level canonical/bucket probe:

```bash
python3 scripts/testing/pos_normalization_probe.py \
  --pairs en-ja,en-es,es-en,en-de \
  --top-n 2000
```

## First Files To Read For POS Changes

1. `core/lexishift_core/pos/normalization.py`
2. `core/lexishift_core/srs/seed.py`
3. `core/lexishift_core/srs/admission_policy.py`
4. `core/lexishift_core/rulegen/generation.py`
5. `docs/language_pairs/lp_data_inventory_matrix.md`
6. `docs/rulegen/pos_normalization_workstream.md`
