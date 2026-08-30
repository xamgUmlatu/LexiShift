# CWS Upload Gate (Solo Maintainer)

Status: active runbook
Role: Runbook / operational
Last updated: 2026-08-31
Last verified: 2026-08-31 Chrome Web Store production ID wiring and preflight rerun
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

## Notes for current project state

- Chrome and Brave production helper connections use the same Chrome Web Store
  package ID in `apps/gui/resources/helper_extension_ids.json`; unpacked
  development connections continue to accept user-supplied IDs.
- Sentence-history data policy is currently conservative:
  - default OFF
  - no URL retention in sentence/history records
