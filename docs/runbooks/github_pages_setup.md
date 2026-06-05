---
layout: default
title: GitHub Pages Setup
---

# GitHub Pages Setup

Status: active runbook
Role: Runbook / operational
Last updated: 2026-06-04
Last verified: 2026-06-04 custom-domain routing update, Pages build, doc-reference check, and local changed-file gate
Purpose: document the active GitHub Pages deployment model and local preview workflow
Source-of-truth: operational runbook; current hosted behavior lives in `.github/workflows/pages.yml` and GitHub repository Pages settings.

Use this after the repository includes `docs/index.md`.

## Required Repo Setting

1. Open repository settings: `Settings -> Pages`.
2. Under `Build and deployment`, select `GitHub Actions`.
3. Under `Custom domain`, enter `lexishift.app`.
4. Save.
5. Enable `Enforce HTTPS` after GitHub reports that HTTPS is available.

This repository now uses a repo-owned Pages workflow in
`.github/workflows/pages.yml`.

The repository also includes `docs/CNAME` as a repo-visible custom-domain
marker, but the GitHub Pages settings value remains the operational control for
the active GitHub Actions deployment model.

## Cloudflare DNS

For the apex domain, create `A` records for `lexishift.app`:

```text
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

For `www.lexishift.app`, create a `CNAME` record to:

```text
xamgUmlatu.github.io
```

Do not create wildcard DNS records such as `*.lexishift.app`.

DNS changes can take up to 24 hours to propagate.

Build contract:
- pull requests touching `docs/**` run a Pages build-only validation job
- pushes to `main` touching `docs/**` build and deploy the site
- the workflow uses the supported `github-pages` dependency set for local parity

## Expected Result

- Site root: `https://lexishift.app/`
- Guide page: `https://lexishift.app/guide/`
- Beta page: `https://lexishift.app/beta/`
- Download page: `https://lexishift.app/download/`
- Repository fallback during transition: `https://xamgUmlatu.github.io/LexiShift/`

GitHub Pages may take several minutes to publish the first build.

## Local Preview (Standardized)

Run from `docs/` using the committed Gemfile:

```bash
cd /Users/takeyayuki/Documents/projects/LexiShift/docs
bundle install
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000 --source .
```

Preview URL:
- `http://127.0.0.1:4000/`

Notes:
- This replaces the previous temporary `/tmp` Gemfile/Bundler flow.
- The committed Gemfile uses the supported `github-pages` gem. When GitHub Pages
  updates, refresh it against `https://pages.github.com/versions/`.
- Hosted deployment is controlled by `.github/workflows/pages.yml`, not by a
  branch-directory selection.
- Repository Pages is now configured to use `GitHub Actions` as the active
  deployment source.
- Before publishing `docs/pack_source_manifest.json` changes, run
  `npm --prefix scripts run quality:pack-sources:audit` so the staged manifest
  and effective pack URLs are validated before deploy.
