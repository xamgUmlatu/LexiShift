# Licensing Header Audit Artifacts

This directory stores JSON outputs from:

- `/Users/takeyayuki/Documents/projects/LexiShift/scripts/dev/licensing_header_audit.py`
- `/Users/takeyayuki/Documents/projects/LexiShift/scripts/dev/licensing_source_header_fetch.py`

## What the audit does

The audit script reads:

- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/data_source_licensing_and_distribution.md`
- `/Users/takeyayuki/Documents/projects/LexiShift/docs/language_pairs/language_pack_urls.txt`

Then, for rows matching a status filter (default: `expected-not-verified`), it:

1. Expands pack IDs (including grouped embedding IDs).
2. Resolves source download URLs from the URL registry.
3. Downloads a small byte range from evidence/source URLs and captures text preview lines.
4. Scans preview lines for license/copyright keywords.
5. Probes local artifact headers under `$DATA_ROOT` when the artifact path is concrete.

The output file is:

- `latest.json`
- `downloaded_headers_latest.json`

## Run

```bash
python /Users/takeyayuki/Documents/projects/LexiShift/scripts/dev/licensing_header_audit.py \
  --json-out /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/licensing_header_audit/latest.json
```

Use `--skip-remote` for offline parsing/local-only checks.

To download source archives and inspect extracted member headers:

```bash
python /Users/takeyayuki/Documents/projects/LexiShift/scripts/dev/licensing_source_header_fetch.py \
  --json-out /Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/licensing_header_audit/downloaded_headers_latest.json
```
