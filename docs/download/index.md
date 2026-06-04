---
layout: default
title: Download LexiShift
---

<!--
Status: staging
Role: Public download page
Last updated: 2026-06-05
Purpose: route users to signed installer assets, checksums, and release metadata after R2 distribution is live.
-->

<div class="download-page">
  <section class="download-status">
    <div>
      <p class="beta-kicker">Beta download status</p>
      <h2>Installer downloads are not live yet.</h2>
      <p>
        This page is ready to become the beta download surface once the first
        installer is uploaded to <code>downloads.lexishift.app</code>. Until
        then, use it as the checklist for what each posted build must include.
      </p>
    </div>
    <div class="download-status__badge">Preparing first beta</div>
  </section>

  <section class="beta-section">
    <h2>Planned beta downloads</h2>
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
            <td><span class="status-pill status-pill--pending">Preparing</span></td>
            <td>SHA-256, signing, and notarization status pending</td>
          </tr>
          <tr>
            <td>Windows</td>
            <td><code>LexiShift-0.1.0.exe</code></td>
            <td><span class="status-pill">Planned</span></td>
            <td>SHA-256 and signing status pending</td>
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
        before replacing an older build.
      </p>
    </div>
    <ol class="download-steps">
      <li>Download the platform-specific installer.</li>
      <li>Compare the SHA-256 checksum with the value on this page.</li>
      <li>Check whether the build is signed or notarized for your platform.</li>
      <li>Read the release notes for known limitations and rollback notes.</li>
    </ol>
  </section>

  <section class="beta-section">
    <h2>How downloads will be published</h2>
    <div class="site-card-grid">
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
          <code>latest.json</code> will point to the current beta or stable
          build and should be treated as release metadata, not an installer.
        </p>
      </article>
      <article class="site-card">
        <h3>Checksum first</h3>
        <p>
          Each download row should show the same SHA-256 value recorded in the
          release manifest and checksum file.
        </p>
      </article>
    </div>
  </section>
</div>

The planned beta release manifest is:

```text
https://downloads.lexishift.app/releases/beta/latest.json
```

The planned stable release manifest is:

```text
https://downloads.lexishift.app/releases/stable/latest.json
```

## Verification

Each published installer should have:

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
