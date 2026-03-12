---
layout: default
title: GitHub Pages Setup
---

# GitHub Pages Setup

Use this after the repository includes `docs/index.md`.

## Required Repo Setting

1. Open repository settings: `Settings -> Pages`.
2. Under `Build and deployment`, select `GitHub Actions`.
3. Save.

This repository now uses a repo-owned Pages workflow in
`.github/workflows/pages.yml`.

Build contract:
- pull requests touching `docs/**` run a Pages build-only validation job
- pushes to `main` touching `docs/**` build and deploy the site
- the workflow uses the supported `github-pages` dependency set for local parity

## Expected Result

- Site root: `https://xamgUmlatu.github.io/LexiShift/`
- Getting started page: `https://xamgUmlatu.github.io/LexiShift/getting-started/`

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
