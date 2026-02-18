---
layout: default
title: GitHub Pages Setup
---

# GitHub Pages Setup

Use this after the repository includes `docs/index.md`.

## Required Repo Setting

1. Open repository settings: `Settings -> Pages`.
2. Under `Build and deployment`, select `Deploy from a branch`.
3. Select `main` branch and `/docs` folder.
4. Save.

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
- `http://127.0.0.1:4000/LexiShift/`

Notes:
- This replaces the previous temporary `/tmp` Gemfile/Bundler flow.
- If you changed `baseurl` behavior, verify links from handbook root and diagrams pages.
