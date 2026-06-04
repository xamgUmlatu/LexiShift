---
layout: default
title: Download LexiShift
---

<!--
Status: active beta access staging
Role: Public download page
Last updated: 2026-06-05
Purpose: route testers to beta access, signed installer assets, checksums, and release metadata as private distribution comes online.
-->

<div class="download-page">
  <section class="download-status">
    <div>
      <p class="beta-kicker">Beta download status</p>
      <h2>Private beta access is being staged.</h2>
      <p>
        The public CTA now leads here. The actual installer link should stay
        limited to invited testers until the first beta build has versioned
        assets, checksums, and release notes.
      </p>
      <div class="beta-actions">
        <a class="beta-button beta-button--primary" href="{{ '/support/' | relative_url }}">Request beta access</a>
        <a class="beta-button" href="{{ '/getting-started/' | relative_url }}">Preview setup steps</a>
      </div>
    </div>
    <div class="download-status__badge">
      <strong>Invited testers only</strong>
      <span>Download link pending first signed artifact</span>
    </div>
  </section>

  <section class="beta-section beta-section--split">
    <div>
      <h2>Access model for the first beta</h2>
      <p>
        A shared password can be useful as light beta friction, but only when
        the installer itself is protected by a server-side gate. A password
        written into a static GitHub Pages page is not private because the page
        source and linked files can be inspected.
      </p>
    </div>
    <div class="download-steps">
      <ol>
        <li>Invite testers directly through a private thread.</li>
        <li>Send the gated download URL only after the build is ready.</li>
        <li>Protect the binary with a server-side password, signed URL, or invite-code check.</li>
        <li>Keep checksums and release notes public enough for testers to verify the file.</li>
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
            <td><span class="status-pill status-pill--pending">Preparing</span></td>
            <td>Gate, SHA-256, signing, and notarization status pending</td>
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
        before replacing an older build. If a tester link asks for a password,
        it should be protecting the hosted file, not just hiding a link in page
        JavaScript.
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
        <h3>Gated beta link</h3>
        <p>
          The first private beta can use a shared password or invite code, but
          the check should happen before the installer URL is returned.
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
          <code>latest.json</code> will point to the current beta or stable
          build and should be treated as release metadata, not an installer.
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
