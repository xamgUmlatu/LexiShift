# LexiShift Download Gate

Cloudflare Worker for private beta installer distribution.

The Worker owns `https://downloads.lexishift.app/*`, reads installer and
manifest objects from the private `lexishift-distribution` R2 bucket, and gates
`/installers/beta/...` behind a shared beta password.

## Required Secrets

Set these locally or in CI before deployment:

```bash
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
```

Set the beta password as a Worker secret. Do not commit it:

```bash
printf '<shared beta password>' | npx wrangler secret put BETA_DOWNLOAD_PASSWORD
```

## Deploy

```bash
npm install
npm test
npx wrangler r2 bucket create lexishift-distribution
npx wrangler deploy
```

## Routes

- `GET /health` returns a small JSON health response.
- `GET /beta/` renders the beta gate form or download list.
- `POST /beta/session` checks `BETA_DOWNLOAD_PASSWORD` and sets an HTTP-only
  signed session cookie.
- `POST /beta/logout` clears the beta session cookie.
- `GET /releases/beta/latest.json` serves the public release manifest from R2.
- `GET /checksums/...` serves checksum files from R2.
- `GET /installers/beta/...` requires a valid beta session and streams the R2
  object as a download.

The Worker intentionally does not make the R2 bucket public. If a future stable
channel should be public, add that as an explicit route rule instead of exposing
the whole bucket.
