# SP1 Data-Source Download Packet

Status: planned packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 current download/catalog code review plus surrounding architecture/runbook review
Purpose: capture the agreed implementation plan for making pack download URLs remotely configurable and making download/install failures explicit enough to diagnose without shipping a new app build for every upstream URL change
Source-of-truth: packet only; executable truth still lives in code, tests, and the current bundled pack catalog until a later implementation slice lands
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `data_source_normalization_architecture.md`
- `../runbooks/github_pages_setup.md`

## Slice

- Track: `SP1`
- Slice: `carry-forward`
- Title: data-source download UX and remote source manifest
- Pass type: design-first with bounded implementation sequencing

## Exact Seam

Primary code surface:

- `apps/gui/src/language_packs_catalog.py`
- `apps/gui/src/language_packs.py`
- `apps/gui/src/settings_language_packs.py`
- `apps/gui/src/settings_language_packs_transfer_mixin.py`

Primary docs surface:

- `docs/developer/data_source_normalization_architecture.md`
- `docs/runbooks/github_pages_setup.md`
- `docs/developer/project_integrity_secondary_pass_notes.md`

Primary future validation surface:

- existing path/panel lifecycle tests under `apps/gui/tests/`
- new targeted transfer/catalog tests for remote override validation and failure classification

## Explicitly Out Of Scope

This slice does not directly review:

- a user bug-reporting or support-ticket workflow for failed downloads
- replacing the bundled pack catalog as the main schema/identity source
- a general-purpose remote config platform beyond pack-download metadata
- background auto-repair or auto-redownload behavior
- non-pack network health checks unrelated to resource downloads

## Current Observation

The current download seam is functional but too static and too generic:

1. `language_packs_catalog.py` hardcodes primary URLs and Wayback/archive fallbacks inside the shipped app build.
2. `LanguagePackDownloadThread` and `FrequencyPackDownloadThread` read `pack.url` directly and return raw exception strings upward.
3. `LanguagePackPanelTransferMixin` currently maps nearly every non-cancelled failure to one generic failed state plus one generic archive link.
4. When an upstream URL changes or disappears, the normal repair path is a code edit plus new app build instead of a lighter operational update.

## Terminology

To avoid collisions between three different metadata layers:

- bundled pack catalog: the code-owned dataclass declarations in `language_packs_catalog.py`
- installed pack manifest: the per-pack `manifest.json` written under the installed pack root after a successful install/build
- remote source manifest: a lightweight hosted JSON overlay keyed by `pack_id` that can refresh mutable download fields without redefining pack identity or build behavior

## Agreed Direction

The agreed interim design is:

1. keep the bundled pack catalog as the baseline schema and offline fallback
2. add a lightweight remote source manifest, hosted on GitHub Pages for now
3. fetch that manifest on app startup and again before a manual download attempt when the cached copy is stale or missing
4. cache the last-known-good manifest locally for 24 hours
5. classify failures into explicit user-facing buckets before they reach the settings panel copy
6. keep URL health checks as an internal development/test workflow, not as end-user repair UX

This keeps the solution lightweight while separating transport churn from app releases.

## Remote Source Manifest Contract

The remote source manifest should be an overlay, not a replacement.

It should:

- be keyed by `pack_id`
- allow only mutable transport fields to change without a code deploy
- be schema-validated before use
- be cached only after the full document validates
- ignore unknown `pack_id` values rather than mutating unrelated runtime state

Recommended mutable fields:

- `url`
- `wayback_url`
- `filename`
- optional `mirrors`
- optional `expected_content_type`
- optional `sha256`
- optional `disabled`
- optional `disabled_reason`
- optional `note`

Fields that should stay code-owned:

- `pack_id`
- provider identity
- pair/source-direction identity
- `build_mode`
- `required_files`
- `sqlite_filename`
- parsing/build configuration

Illustrative shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-19T00:00:00Z",
  "ttl_hours": 24,
  "packs": {
    "freedict-en-de": {
      "url": "https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz",
      "wayback_url": "https://web.archive.org/web/*/https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz",
      "filename": "freedict-eng-deu-1.9-fd1.src.tar.xz",
      "expected_content_type": "application/x-xz"
    }
  }
}
```

## Resolution And Fallback Order

Recommended behavior:

1. load the bundled pack catalog first
2. overlay a cached remote source manifest only if it is valid and still fresh
3. refresh the remote source manifest asynchronously on app startup
4. before a user-triggered download, refresh again if the cache is stale or absent
5. if remote refresh fails, keep using the last-known-good cache
6. if no valid cache exists, fall back to bundled catalog values only
7. never let a malformed remote manifest partially mutate the active catalog

Operational consequence:

- the settings panel should remain usable offline
- a bad hosted manifest should degrade back to the shipped catalog instead of breaking downloads globally

## Failure Taxonomy

The settings panel should stop treating every failure as the same generic event.

Minimum failure classes:

| Failure class | Typical cause | Expected user-facing behavior |
|---|---|---|
| `offline` | no internet, DNS failure, refused connection | say the app could not reach the source and suggest retrying after connectivity returns |
| `timeout` | slow or stalled upstream | say the download timed out and can be retried |
| `not_found` | HTTP 404 or removed artifact | say the source URL is no longer valid and offer the archive/mirror hint when available |
| `forbidden_or_blocked` | HTTP 403/451 or host-level blocking | say the source could not be accessed from the current network and offer the archive/mirror hint when relevant |
| `content_mismatch` | wrong content type, empty response, missing required file after extraction | say the source responded, but not with the expected pack data |
| `checksum_mismatch` | hosted file changed unexpectedly | say the download completed but failed integrity verification |
| `write_failure` | permission/disk/path problems | say the app could not save the download locally |
| `conversion_failure` | archive unpack/build-to-SQLite step failed | say the source downloaded but install/build failed locally |
| `cancelled` | user/app cancellation | keep the muted cancelled state already used today |
| `unknown` | uncategorized exception | keep a generic fallback with the log path |

Important UX rule:

- the archive/Wayback link should be conditional on source-side failure classes, not the universal answer for every local error

## GitHub Pages Hosting Model

GitHub Pages is acceptable as the first lightweight transport layer because it avoids shipping a new app build when URLs change, while staying repo-owned and easy to audit.

Recommended approach:

- publish the remote source manifest as JSON under the existing docs site
- keep the JSON schema stable even if the hosting target changes later
- use the Pages workflow/runbook already documented in `../runbooks/github_pages_setup.md`
- keep a bundled copy of the default values in the app so Pages outages do not break install UX

This is still a repo/content update, but it is materially lighter than a new desktop release for every upstream URL repair.

## Health Audit Workflow

The repo should have a lightweight, developer-facing URL audit script for these pack sources.

Recommended properties:

- reads the same remote source manifest schema the app will consume
- validates manifest schema before probing URLs
- checks each active URL with `HEAD` and falls back to `GET` when needed
- records HTTP status, redirect target, content-type, and content-length when available
- optionally validates checksum or required-file expectations when the manifest provides them
- writes JSON and Markdown outputs for handoff

Recommended posture:

- keep it out of the default repo-safety gate because external networks are noisy
- allow it as an explicit dev/test command and later as an optional scheduled CI health check

Current explicit command:

```bash
npm --prefix scripts run quality:pack-sources:audit
```

Current default outputs:

- `docs/test_outputs/pack_source_url_audit/latest.json`
- `docs/test_outputs/pack_source_url_audit/latest.md`

Current scope note:

- the implemented audit validates the current manifest schema, probes effective primary plus archive URLs, and enforces `expected_content_type` when provided
- checksum enforcement can layer on later if `sha256` becomes a first-class manifest input

## Bite-Sized Implementation Order

1. Add a `pack_id`-keyed overlay resolver around the existing bundled catalog objects without changing download behavior yet.
2. Add the remote source-manifest fetch/cache layer with schema validation and last-known-good fallback.
3. Add download failure classification between the downloader threads and the transfer/status mixin.
4. Update settings-panel copy so source-side, local-write, and conversion failures produce different messages.
5. Restrict the archive/Wayback hint to the relevant failure classes.
6. Add the developer URL-health audit script and a short operator runbook note once the manifest contract is real.

## Acceptance Criteria

This plan is successful when the later implementation slice achieves all of the following:

1. broken upstream URLs can be repaired through the hosted manifest without shipping a new app build
2. a malformed or unreachable remote manifest does not prevent the panel from using bundled defaults
3. 404, offline, local-write, and conversion failures no longer collapse into one generic message
4. pack identity and build-shape fields remain code-owned and cannot be changed by the hosted overlay
5. future UX work can reason about an explicit download/install state machine instead of arbitrary raw exception strings

## Why This Helps Later UX Work

This plan is not only about fixing broken URLs.

It also makes later UX work easier because:

- download state becomes explicit: resolve source metadata, download, extract/convert, validate, link
- each failure stage has a clear boundary, so future copy/progress indicators can be improved without reverse-engineering exception strings
- pack transport maintenance becomes decoupled from the deeper resource-selection and panel-state code
- test coverage can target distinct failure classes instead of one catch-all error surface
