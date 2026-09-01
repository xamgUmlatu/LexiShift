# CWS Upload Gate (Solo Maintainer)

Status: active runbook
Role: Runbook / operational
Last updated: 2026-09-02
Last verified: 2026-09-02 Chrome Web Store 0.1.1 package submission and final archive inspection
Purpose: define the mandatory lightweight gate before a Chrome Web Store upload
Source-of-truth: operational runbook; current command behavior lives in `scripts/package.json` and the preflight implementation.

This runbook defines the lightweight mandatory gate before Chrome Web Store upload.

## Goal

Catch common release mistakes with one command and one short manual checklist.

## Automated preflight

From repository root:

```bash
npm --prefix scripts run preflight:cws
```

What it checks:
- manifest integrity and referenced files
- icon file dimensions
- locale placeholder coverage for `__MSG_*`
- fixed helper environment IDs are not placeholders
- broad permission posture warnings (`<all_urls>`, `all_frames`, `match_about_blank`)
- literal remote URL presence warnings
- package noise (`.DS_Store`, temp files)

After the gate passes, build the upload package:

```bash
npm --prefix scripts run package:cws -- --version 0.1.1
```

The command emits a deterministic ZIP and adjacent `.sha256` file under
`dist/cws/`. Upload the ZIP, not the containing directory.

Report output:
- Markdown report under:
  - `docs/runbooks/cws_preflight_reports/`

Gate behavior:
- Any `FAIL` check exits non-zero and blocks upload.
- `WARN`/`INFO` do not block upload but must be reviewed.

## Manual checklist (required)

Before upload, confirm all:

- [ ] Preflight report exists for current release candidate and has zero `FAIL`.
- [ ] Permission changes (if any) are intentional and documented in reviewer notes.
- [ ] Privacy policy and store listing text match actual data behavior (especially local sensitive data handling).
- [ ] Helper onboarding was tested in both states: helper available and helper unavailable.
- [ ] Final package is clean (no debug artifacts, no temporary/system files).
- [ ] Final package SHA-256 is recorded from the adjacent generated checksum file.

## Notes for current project state

- Chrome and Brave production helper connections use the same Chrome Web Store
  package ID in `apps/gui/resources/helper_extension_ids.json`; unpacked
  development connections continue to accept user-supplied IDs.
- Local browsing-practice records are disclosed conservatively:
  - replacement-exposure logging is enabled by default and may retain the page
    URL plus original/replacement words in local extension storage
  - feedback records may retain the same local context
  - encounter history may retain a short latest sentence excerpt associated
    with a practiced word
  - the current public privacy policy describes these local records
