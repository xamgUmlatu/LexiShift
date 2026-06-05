---
layout: default
title: Download LexiShift
---

<!--
Status: active beta access
Role: Public download page
Last updated: 2026-06-05
Purpose: route testers to beta access, installer assets, checksums, and release metadata while private distribution is active.
-->

<div class="download-page">
  <section class="download-status">
    <div>
      <p class="beta-kicker">Beta download status</p>
      <h2>Private beta downloads are live.</h2>
      <p>
        Invited testers can open the Cloudflare download gate, enter the shared
        beta password, and download the current macOS beta artifact. Checksums
        and release metadata are public so the file can be verified.
      </p>
      <div class="beta-actions">
        <a class="beta-button beta-button--primary" href="https://downloads.lexishift.app/beta/">Open beta gate</a>
        <a class="beta-button" href="{{ '/getting-started/' | relative_url }}">Preview setup steps</a>
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
        The beta password is enforced by a Cloudflare Worker before the
        installer object is streamed from private R2 storage. GitHub Pages stays
        public and intentionally does not contain the password or direct binary
        object access.
      </p>
    </div>
    <div class="download-steps">
      <ol>
        <li>Invite testers directly through a private thread.</li>
        <li>Send <code>https://downloads.lexishift.app/beta/</code> with the shared beta password.</li>
        <li>Keep the binary behind the server-side gate.</li>
        <li>Use the manifest and checksum file to verify the downloaded artifact.</li>
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
        Each posted installer should be treated as a specific release artifact,
        not a generic download. Match the version, checksum, and release notes
        before replacing an older build. The current macOS beta is unsigned and
        not notarized, so macOS may require Control-click > Open.
      </p>
    </div>
    <ol class="download-steps">
      <li>Download the platform-specific installer.</li>
      <li>Compare the SHA-256 checksum with the value in the manifest or checksum file.</li>
      <li>Check whether the build is signed or notarized for your platform.</li>
      <li>Read the release notes for known limitations and rollback notes.</li>
    </ol>
  </section>

  <section class="beta-section">
    <h2>How downloads will be published</h2>
    <div class="site-card-grid">
      <article class="site-card">
        <h3>Gated beta link</h3>
        <p>
          The private beta uses a shared password checked by the Cloudflare
          Worker before the installer object is returned from R2.
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

## Related Pages

- [Beta]({{ '/beta/' | relative_url }})
- [Releases]({{ '/releases/' | relative_url }})
- [Getting Started]({{ '/getting-started/' | relative_url }})
- [Support]({{ '/support/' | relative_url }})
