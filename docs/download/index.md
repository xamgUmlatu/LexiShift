---
layout: default
title: Download LexiShift
---

<!--
Status: active beta access
Role: Public download page
Last updated: 2026-06-06
Purpose: route testers to beta access, installer assets, checksums, and release metadata while private distribution is active.
-->

<div class="download-page">
  <section class="download-status">
    <div>
      <p class="beta-kicker">Beta download status</p>
      <h2>Private beta downloads are live.</h2>
      <p>
        Invited testers can open the download gate, enter the beta password
        from their private invite, and download the current macOS beta. This
        first beta is intentionally informal: install it, try the basic flow,
        and send back what happened.
      </p>
      <div class="beta-actions">
        <a class="beta-button beta-button--primary" href="https://downloads.lexishift.app/beta/">Open beta gate</a>
        <a class="beta-button" href="{{ '/tester-notes/' | relative_url }}">Read tester notes</a>
      </div>
    </div>
    <div class="download-status__badge">
      <strong>Invited testers only</strong>
      <span>macOS 0.1.0 is live; password required</span>
    </div>
  </section>

  <section class="beta-section beta-section--split">
    <div>
      <h2>Access model for the first beta</h2>
      <p>
        The public website explains the install path, but the actual app file
        stays behind the private download gate. The shared password is sent
        privately and is not published on this page.
      </p>
    </div>
    <div class="download-steps">
      <ol>
        <li>Open <code>https://downloads.lexishift.app/beta/</code>.</li>
        <li>Enter the beta password from the private invite.</li>
        <li>Download the macOS installer.</li>
        <li>Use the unsigned-app instructions below if macOS blocks first launch.</li>
      </ol>
    </div>
  </section>

  <section class="beta-section">
    <h2>Beta download slots</h2>
    <div class="download-table" role="region" aria-label="Planned LexiShift beta downloads" tabindex="0">
      <table>
        <thead>
          <tr>
            <th>Platform</th>
            <th>Installer</th>
            <th>Status</th>
            <th>Verification</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>macOS</td>
            <td><code>LexiShift-0.1.0.dmg</code></td>
            <td><span class="status-pill status-pill--live">Live beta</span></td>
            <td>Gated download, SHA-256 checksum, unsigned, not notarized</td>
          </tr>
          <tr>
            <td>Windows</td>
            <td><code>LexiShift-0.1.0.exe</code></td>
            <td><span class="status-pill">Planned</span></td>
            <td>Gate, SHA-256, and signing status pending</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <section class="beta-section beta-section--split">
    <div>
      <h2>Before installing a beta build</h2>
      <p>
        The current macOS beta is unsigned and not notarized. That is expected
        for this first casual test, but it means macOS may show a warning the
        first time the app is opened.
      </p>
    </div>
    <ol class="download-steps">
      <li>Download <code>LexiShift-0.1.0.dmg</code> from the beta gate.</li>
      <li>Open the DMG and drag LexiShift into Applications if prompted.</li>
      <li>If macOS blocks the app, Control-click LexiShift and choose Open.</li>
      <li>If it still will not open, check System Settings -> Privacy &amp; Security for the allow/open option.</li>
    </ol>
  </section>

  <section class="beta-section">
    <h2>How downloads will be published</h2>
    <div class="site-card-grid">
      <article class="site-card">
        <h3>Gated beta link</h3>
        <p>
          The private beta uses a shared password checked before the installer
          object is returned from private storage.
        </p>
      </article>
      <article class="site-card">
        <h3>Versioned installers</h3>
        <p>
          Installer URLs will include channel, version, platform, and filename
          so a build can be referenced and verified after newer builds ship.
        </p>
      </article>
      <article class="site-card">
        <h3>Short-cache manifest</h3>
        <p>
          <code>latest.json</code> points to the current beta or stable build
          and should be treated as release metadata, not an installer.
        </p>
      </article>
    </div>
  </section>
</div>

The beta release manifest is:

```text
https://downloads.lexishift.app/releases/beta/latest.json
```

The private beta gate is:

```text
https://downloads.lexishift.app/beta/
```

The planned stable release manifest is:

```text
https://downloads.lexishift.app/releases/stable/latest.json
```

## Verification

Each published installer should have:

- a server-side beta gate if access is limited to invited testers,
- a versioned immutable download URL,
- a SHA-256 checksum,
- signed/notarized status for macOS,
- signed status for Windows,
- release notes linked from the manifest.

For casual invited testers, checksum verification is optional. If the file was
downloaded from the beta gate, the most important check is whether the app
opens and the setup flow is understandable.

## Related Pages

- [Beta]({{ '/beta/' | relative_url }})
- [Releases]({{ '/releases/' | relative_url }})
- [Getting Started]({{ '/getting-started/' | relative_url }})
- [Tester Notes]({{ '/tester-notes/' | relative_url }})
- [Support]({{ '/support/' | relative_url }})
