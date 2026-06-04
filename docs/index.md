---
layout: default
title: LexiShift
---

<!--
Status: active Pages entrypoint
Role: Canonical current
Last updated: 2026-06-05
Last verified: 2026-06-05 beta/download site pass, Pages build, and doc-reference check
Purpose: route visitors into beta downloads, setup docs, support, privacy, and the repository documentation map
Source-of-truth: Pages navigation entrypoint only; implementation truth remains in source code, canonical developer docs, architecture docs, and feature-state evidence.
-->

<div class="site-home">
  <section class="site-hero">
    <div>
      <p class="beta-kicker">Local-first language learning tools</p>
      <h2>Beta Access And Docs</h2>
      <p class="site-hero__lede">
        LexiShift is a desktop-centered beta for building language-learning
        replacement rules, reviewing vocabulary, and testing local-first study
        workflows before the production release.
      </p>
      <div class="site-actions">
        <a class="beta-button beta-button--primary" href="{{ '/beta/' | relative_url }}">Beta overview</a>
        <a class="beta-button" href="{{ '/download/' | relative_url }}">Download status</a>
        <a class="beta-button" href="{{ '/getting-started/' | relative_url }}">Setup guide</a>
      </div>
    </div>
    <aside class="site-status" aria-label="Current LexiShift beta status">
      <span class="status-pill status-pill--pending">Preparing first beta</span>
      <dl>
        <div>
          <dt>App</dt>
          <dd>Desktop beta, macOS first</dd>
        </div>
        <div>
          <dt>Downloads</dt>
          <dd>Installer links not public yet</dd>
        </div>
        <div>
          <dt>Hosting</dt>
          <dd>GitHub Pages now, R2 downloads planned</dd>
        </div>
      </dl>
    </aside>
  </section>

  <section class="beta-section">
    <h2>Start Here</h2>
    <div class="site-card-grid">
      <article class="site-card">
        <h3>Download Path</h3>
        <p>
          Check the current beta status, planned platform installers, and the
          verification details each posted build must include.
        </p>
        <a href="{{ '/download/' | relative_url }}">Open download page</a>
      </article>
      <article class="site-card">
        <h3>Setup Guide</h3>
        <p>
          Follow the current walkthrough for first launch, profiles, rulesets,
          runtime surfaces, SRS setup, and troubleshooting.
        </p>
        <a href="{{ '/getting-started/' | relative_url }}">Read setup guide</a>
      </article>
      <article class="site-card">
        <h3>Beta Support</h3>
        <p>
          See what to include in a useful issue report and how privacy works for
          screenshots, logs, and local diagnostic files.
        </p>
        <a href="{{ '/support/' | relative_url }}">Get support info</a>
      </article>
    </div>
  </section>

  <section class="beta-section beta-section--split">
    <div>
      <h2>What is available now</h2>
      <p>
        The site is live as the public beta front door. The first installer
        links, checksums, and release manifest will be added after a release
        artifact is built, verified, and uploaded to the downloads host.
      </p>
    </div>
    <ol class="download-steps">
      <li>Use the beta page to understand the testing boundary.</li>
      <li>Use the download page to confirm whether an installer is live.</li>
      <li>Use the setup guide after installing a posted beta build.</li>
      <li>Use the support and privacy pages before sending diagnostics.</li>
    </ol>
  </section>

</div>

## Documentation

- [Handbook Home](./handbook/)
- [Release Guide](./handbook/release/)
- [Architecture Diagrams](./handbook/diagrams/)
- [Privacy](./privacy/)
- [Support](./support/)
- [Releases](./releases/)

- [Documentation Structure (Repository View)](https://github.com/xamgUmlatu/LexiShift/blob/main/docs/README.md)
- [Full `docs/` Tree (Repository View)](https://github.com/xamgUmlatu/LexiShift/tree/main/docs)
- [Developer Docs Hub (Repository View)](https://github.com/xamgUmlatu/LexiShift/blob/main/docs/developer/README.md)
- [Handbook (Repository View)](https://github.com/xamgUmlatu/LexiShift/tree/main/docs/handbook)

## Setup Note

If this page returns `404`, GitHub Pages is not enabled yet for the repository.
Follow: [GitHub Pages Setup Runbook](./runbooks/github_pages_setup/)
