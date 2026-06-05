---
layout: default
title: LexiShift Beta
---

<!--
Status: active beta entrypoint
Role: Beta entrypoint
Last updated: 2026-06-06
Purpose: provide the public beta entrypoint for tester-facing install and support links while hosted distribution is live.
-->

<div class="beta-page" markdown="1">
  <section class="beta-hero">
    <div class="beta-hero__copy">
      <p class="beta-kicker">Desktop beta</p>
      <h1>Try LexiShift before the production release.</h1>
      <p class="beta-lede">
        LexiShift is a local-first desktop app for language-learning workflows.
        This first beta is informal: directly invited testers can install the
        app, try the setup flow, and send back plain-language feedback.
      </p>
      <div class="beta-actions">
        <a class="beta-button beta-button--primary" href="{{ '/download/' | relative_url }}">Download beta app</a>
        <a class="beta-button" href="{{ '/tester-notes/' | relative_url }}">Read tester notes</a>
      </div>
    </div>
    <div class="beta-release-card" aria-label="Beta release status">
      <div class="beta-release-card__header">
        <span>Current beta</span>
        <strong>0.1.0</strong>
      </div>
      <dl>
        <div>
          <dt>Download status</dt>
          <dd>macOS beta live behind password gate</dd>
        </div>
        <div>
          <dt>Primary platform</dt>
          <dd>macOS first</dd>
        </div>
        <div>
          <dt>Distribution</dt>
          <dd>Cloudflare Worker plus private R2</dd>
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
        The beta should prove that a directly invited tester can install the
        app, open it, follow the first setup path, and say where the experience
        becomes unclear.
      </p>
    </div>
    <div class="beta-check-grid">
      <div class="beta-check">
        <strong>Install flow</strong>
        <span>Download, open, and complete the first setup pass.</span>
      </div>
      <div class="beta-check">
        <strong>Local behavior</strong>
        <span>Confirm the app works without accounts, sync, or cloud state.</span>
      </div>
      <div class="beta-check">
        <strong>Release trust</strong>
        <span>Make the unsigned macOS warning clear before launch.</span>
      </div>
    </div>
  </section>

## Install

1. Open the [download page]({{ '/download/' | relative_url }}).
2. Open the private beta gate if you have been invited.
3. Enter the shared beta password from your invite.
4. Download the macOS installer.
5. Use Control-click > Open if macOS blocks the unsigned app.
6. Follow the short [tester notes]({{ '/tester-notes/' | relative_url }}) or the full [LexiShift guide]({{ '/guide/' | relative_url }}).
7. Send feedback through the same private thread where you received the link.

## Before You Install

- Beta builds may change quickly and may require manual replacement.
- Hosted installer links point to versioned files on `downloads.lexishift.app`.
- A shared password is acceptable only as a server-side beta gate, not as static
  JavaScript on GitHub Pages.
- The current macOS beta is unsigned and not notarized; macOS may require
  Control-click > Open.
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
- Tester notes: [Tester Notes]({{ '/tester-notes/' | relative_url }})
- Privacy summary: [Privacy]({{ '/privacy/' | relative_url }})
- Release notes: [Releases]({{ '/releases/' | relative_url }})

</div>
