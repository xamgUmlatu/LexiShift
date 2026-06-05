---
layout: default
title: Cloudflare Distribution Setup
---

# Cloudflare Distribution Setup

Status: active runbook
Role: Runbook / operational
Last updated: 2026-06-05
Last verified: 2026-06-05 live `downloads.lexishift.app` Worker/R2 gate smoke after R2 enablement
Purpose: define the low-cost Cloudflare lane for LexiShift installer downloads, release metadata, and future hosted app data
Source-of-truth: operational runbook; live Cloudflare resource names, DNS records, and billing state must be checked in the Cloudflare dashboard before deployment.
Related docs:
- `../developer/hosting_distribution_roadmap.md`
- `../developer/build_and_release.md`
- `github_pages_setup.md`

Use this when moving LexiShift distribution beyond GitHub Pages-only hosting.
The initial indie/beta goal is to stay near domain cost plus an optional
Workers Paid plan, then add paid database/auth products only when user-specific
server data exists.

## Recommended First Milestone

Keep the first milestone small:

1. Keep GitHub Pages as the public handbook/docs surface.
2. Use Cloudflare DNS for the product domain.
3. Use Cloudflare R2 for installers, release metadata, and hosted app data packs.
4. Add one Worker for the private beta gate before exposing installer objects.
5. Do not add Supabase/Firebase/Postgres until LexiShift needs user-specific
   sync, accounts, entitlements, or support dashboards.

Expected starting cost:
- Cloudflare DNS/Pages/R2 within free-tier usage for a small beta.
- Optional Workers Paid plan: about `$5/month`.
- Domain registration and Apple/Windows signing are separate from hosting.

## Roles By Surface

| Surface | Suggested role | Notes |
| --- | --- | --- |
| GitHub Pages | Docs/manual/handbook | Already wired through `.github/workflows/pages.yml`. |
| `lexishift.app` | Product landing page | Can be Cloudflare Pages later; does not need to move first. |
| `beta.lexishift.app` | Beta landing and gated downloads | Use simple gating for indie beta; avoid per-user paid Access after the free tier. |
| `downloads.lexishift.app` | Gated beta downloads and public release metadata | Route to the `lexishift-download-gate` Worker backed by private R2 objects. |
| `data.lexishift.app` | Hosted app data/resource packs | Back with R2; keep licensing/manual-supply constraints explicit before public hosting. |
| `api.lexishift.app` | Release manifest or signed-link Worker | Add only when static R2-hosted JSON is not enough. |

## R2 Bucket Plan

Start with one bucket:

```text
lexishift-distribution
```

Use object paths that keep immutable versioned assets separate from mutable
channel pointers:

```text
installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg
installers/beta/0.1.0/windows/LexiShift-0.1.0.exe
checksums/beta/0.1.0/SHA256SUMS.txt
releases/beta/latest.json
releases/stable/latest.json
packs/en-es/2026-06-03/manifest.json
packs/en-es/2026-06-03/<pack-file>
```

Use R2 Standard storage for beta and early production. Do not use Infrequent
Access for release assets unless the retrieval pattern is proven cold.

For immutable installers and pack versions, set this when uploading objects:

```text
Cache-Control: public, max-age=31536000, immutable
```

For mutable channel pointers such as `latest.json`, set:

```text
Cache-Control: public, max-age=60
```

## Release Manifest Shape

Host release metadata at:

```text
https://downloads.lexishift.app/releases/beta/latest.json
https://downloads.lexishift.app/releases/stable/latest.json
```

Initial manifest schema:

```json
{
  "schema_version": 1,
  "channel": "beta",
  "version": "0.1.0",
  "published_at": "2026-06-03T00:00:00Z",
  "release_notes_url": "https://lexishift.app/releases/0.1.0",
  "platforms": {
    "macos": {
      "url": "https://downloads.lexishift.app/installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg",
      "sha256": "<sha256>",
      "size_bytes": 0,
      "signed": false,
      "notarized": false
    },
    "windows": {
      "url": "https://downloads.lexishift.app/installers/beta/0.1.0/windows/LexiShift-0.1.0.exe",
      "sha256": "<sha256>",
      "size_bytes": 0,
      "signed": false
    }
  }
}
```

Keep the schema stable even if the app does not consume it yet. It gives the
website, manual test flow, and future updater one shared source of truth.

During private beta, installer URLs in the manifest still use
`https://downloads.lexishift.app/installers/...`, but that domain is owned by
the Worker. The Worker serves `releases/` and `checksums/` publicly and requires
a valid beta session cookie before streaming `installers/beta/...` objects from
R2.

## Cloudflare Dashboard Setup

1. Create or log into the Cloudflare account.
2. Add the product domain, for example `lexishift.app`.
3. Move domain nameservers to Cloudflare.
4. Enable R2 in the Cloudflare dashboard, then create an R2 bucket named
   `lexishift-distribution`.
5. Deploy the `cloudflare/download-gate` Worker.
6. Route `downloads.lexishift.app/*` to the Worker. Do not attach
   `downloads.lexishift.app` directly to public R2 for the private beta.
   Ensure the `downloads` DNS record is proxied through Cloudflare, for example
   as a proxied CNAME to `lexishift.app`, so the Worker route receives traffic.
7. Optional: attach a separate custom domain for hosted app data,
   `data.lexishift.app`, if app data should be isolated from installers.
8. Optional: enable Workers Paid only when the API/gating Worker is ready to
   deploy or the free limits become operationally annoying.

Do not store Cloudflare API tokens, account IDs, signing credentials, or
notarization passwords in the repository.

Automation requires a valid account token with R2 storage access, Worker script
and route access, and DNS record read/edit access for `lexishift.app`. If R2 has
not been enabled in the Cloudflare dashboard, Wrangler bucket creation fails
with Cloudflare API code `10042`.

## Local Upload Commands

Install dependencies only when Cloudflare deployment begins:

```bash
cd cloudflare/download-gate
npm install
```

For local automation, load credentials from a file outside the repo:

```bash
set -a
source ~/.lexishift-secrets/cloudflare.env
set +a
```

Create the bucket if it has not been created in the dashboard:

```bash
npx wrangler r2 bucket create lexishift-distribution
```

If this returns `Please enable R2 through the Cloudflare Dashboard`, open
Cloudflare Dashboard > R2 Object Storage and complete the R2 enablement step
before retrying the command.

Set the shared beta password as a Worker secret. Do not commit it:

```bash
printf '<shared beta password>' | npx wrangler secret put BETA_DOWNLOAD_PASSWORD
```

Deploy the Worker route:

```bash
npm --prefix scripts run test:downloads:gate
npm --prefix scripts run deploy:downloads:gate
```

Upload an installer:

```bash
npx wrangler r2 object put \
  lexishift-distribution/installers/beta/0.1.0/macos/LexiShift-0.1.0.dmg \
  --file apps/gui/dist/installers/LexiShift-0.1.0.dmg
```

Upload the beta manifest:

```bash
npx wrangler r2 object put \
  lexishift-distribution/releases/beta/latest.json \
  --file docs/test_outputs/release_manifests/beta_latest.json
```

Generate a real manifest and checksum file from installer artifacts:

```bash
npm --prefix scripts run release:manifest -- \
  --version 0.1.0 \
  --channel beta \
  --asset macos=apps/gui/dist/installers/LexiShift-0.1.0.dmg \
  --print-wrangler-commands
```

When automating this, prefer a GitHub Actions workflow with a narrowly scoped
Cloudflare API token stored as a GitHub Actions secret.

## Beta Gating Options

For fewer than 100 users, use one of these simple gates:

1. Obscure beta URL plus signed/manual installer links.
2. Shared beta password enforced by a Worker, Access policy, or other
   server-side gate before returning the installer URL.
3. Invite code checked by a small Worker before returning a signed R2 URL.

Do not treat a password embedded in static GitHub Pages HTML or JavaScript as
real privacy. It can be acceptable as a visual affordance for testers, but the
binary URL and token would still be inspectable by anyone who can load the page.

The repo-owned first implementation is `cloudflare/download-gate`. It uses
`BETA_DOWNLOAD_PASSWORD` as a Worker secret and sets an HTTP-only signed cookie
after the password is accepted at `https://downloads.lexishift.app/beta/`.

Avoid Cloudflare Access as long-term product-user auth. It is excellent for
private admin/internal tooling, but per-user pricing is the wrong shape for
normal app customers once the free user tier is exceeded.

## Cost Guardrails

- Keep installers and data packs versioned and immutable.
- Keep `latest.json` small and cache it briefly.
- Bundle app data into fewer larger pack files instead of many tiny fetches.
- Prefer R2 egress-free downloads over S3-style metered egress for installer
  and pack distribution.
- Add a database only after there is a real user-specific data model.
- Keep manual-supply or legally uncertain language resources out of public R2
  paths until the distribution register explicitly allows hosting them.

## Verification

Live gate smoke:

```bash
curl https://downloads.lexishift.app/health
curl -I https://downloads.lexishift.app/beta/
```

Expected:
- `/health` returns `{"ok":true}`
- `/beta/` returns the password gate or beta download list
- `installers/beta/...` redirects to `/beta/` until a valid beta session cookie
  is present

After the first real upload:

```bash
curl -I https://downloads.lexishift.app/releases/beta/latest.json
curl https://downloads.lexishift.app/releases/beta/latest.json
```

Expected:
- `200 OK`
- small JSON body
- short cache on `latest.json`
- installer URLs in the manifest resolve to versioned immutable objects

Before publishing docs changes that alter this runbook or linked Pages routes:

```bash
cd docs
bundle exec jekyll build --trace
```
