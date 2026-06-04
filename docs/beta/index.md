---
layout: default
title: LexiShift Beta
---

<!--
Status: staging
Role: Beta entrypoint
Last updated: 2026-06-05
Purpose: provide the public beta entrypoint for tester-facing install and support links once hosted distribution is live.
-->

<div class="beta-page" markdown="1">
  <section class="beta-hero">
    <div class="beta-hero__copy">
      <p class="beta-kicker">Desktop beta</p>
      <h1>Try LexiShift before the production release.</h1>
      <p class="beta-lede">
        LexiShift is a local-first desktop app for language-learning workflows.
        This beta is for early testers who are comfortable with fast-moving
        builds, manual updates, and clear issue reports.
      </p>
      <div class="beta-actions">
        <a class="beta-button beta-button--primary" href="{{ '/download/' | relative_url }}">Download beta app</a>
        <a class="beta-button" href="{{ '/getting-started/' | relative_url }}">Read setup guide</a>
      </div>
    </div>
    <div class="beta-release-card" aria-label="Beta release status">
      <div class="beta-release-card__header">
        <span>Current beta</span>
        <strong>Preparing</strong>
      </div>
      <dl>
        <div>
          <dt>Download status</dt>
          <dd>Not posted yet</dd>
        </div>
        <div>
          <dt>Primary platform</dt>
          <dd>macOS first</dd>
        </div>
        <div>
          <dt>Distribution</dt>
          <dd>R2-backed downloads planned</dd>
        </div>
        <div>
          <dt>Update model</dt>
          <dd>Manual beta downloads</dd>
        </div>
      </dl>
    </div>
  </section>

  <section class="beta-section">
    <h2>Release Flow</h2>
    <div class="release-flow" aria-label="LexiShift beta release flow">
      <div class="release-flow__step">
        <strong>1</strong>
        <span>Build installer</span>
      </div>
      <div class="release-flow__step">
        <strong>2</strong>
        <span>Generate checksum and manifest</span>
      </div>
      <div class="release-flow__step">
        <strong>3</strong>
        <span>Upload to downloads host</span>
      </div>
      <div class="release-flow__step">
        <strong>4</strong>
        <span>Publish release notes</span>
      </div>
      <div class="release-flow__step">
        <strong>5</strong>
        <span>Tester installs and reports</span>
      </div>
    </div>
  </section>

  <section class="beta-section beta-section--split">
    <div>
      <h2>What this beta is for</h2>
      <p>
        The beta should prove that a real tester can install the app, open it,
        follow the setup flow, understand the current limitations, and send a
        useful report when something breaks.
      </p>
    </div>
    <div class="beta-check-grid">
      <div class="beta-check">
        <strong>Install flow</strong>
        <span>Download, verify, open, and complete the first setup pass.</span>
      </div>
      <div class="beta-check">
        <strong>Local behavior</strong>
        <span>Confirm the app works without accounts, sync, or cloud state.</span>
      </div>
      <div class="beta-check">
        <strong>Release trust</strong>
        <span>Check version, checksum, release notes, and signing status.</span>
      </div>
    </div>
  </section>

## Install

1. Open the [download page]({{ '/download/' | relative_url }}).
2. Confirm the page says an installer is live.
3. Choose the installer for your platform.
4. Verify the SHA-256 checksum listed beside the installer.
5. Follow the [getting started guide]({{ '/getting-started/' | relative_url }}).
6. Send feedback through the [support page]({{ '/support/' | relative_url }}).

## Before You Install

- Beta builds may change quickly and may require manual replacement.
- Hosted installer links will point to versioned files on `downloads.lexishift.app`.
- The app is being treated as local-first; account, sync, and backup features are not part of this beta lane.
- Publicly hosted app data must stay inside the project's distribution and licensing rules.
- Use the [release notes]({{ '/releases/' | relative_url }}) before replacing an older build.

<section class="beta-section">
  <h2>Beta boundaries</h2>
  <div class="beta-card-grid">
    <article class="beta-card">
      <h3>No production promise yet</h3>
      <p>
        The beta page should make the app easy to try, not imply that every
        production release concern is finished.
      </p>
    </article>
    <article class="beta-card">
      <h3>No hidden backend requirement</h3>
      <p>
        Tester downloads should work without a LexiShift account. A backend can
        be added later when user-specific cloud data exists.
      </p>
    </article>
    <article class="beta-card">
      <h3>No unclear data hosting</h3>
      <p>
        Language resources with unresolved or manual-supply distribution status
        should not be linked as public app downloads.
      </p>
    </article>
  </div>
</section>

## Help

- Support: [Support]({{ '/support/' | relative_url }})
- Privacy summary: [Privacy]({{ '/privacy/' | relative_url }})
- Release notes: [Releases]({{ '/releases/' | relative_url }})

</div>
