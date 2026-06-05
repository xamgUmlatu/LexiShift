---
layout: default
title: LexiShift 0.1.0 Beta
---

<!--
Status: active beta release notes
Role: Tester-facing release notes
Last updated: 2026-06-05
Purpose: document the first private beta artifact linked from the hosted release manifest.
-->

<div class="releases-page" markdown="1">

# LexiShift 0.1.0 Beta

This is the first private beta artifact for invited testers. It is intended to
prove the desktop install path, local-first setup flow, helper handoff, and
early feedback loop before signing and production distribution are finished.

<section class="release-channel-grid">
  <article class="release-channel">
    <span class="status-pill status-pill--live">Live beta</span>
    <h2>macOS</h2>
    <p>
      The macOS artifact is available through the private beta gate at
      <code>https://downloads.lexishift.app/beta/</code>.
    </p>
  </article>
  <article class="release-channel">
    <span class="status-pill status-pill--pending">Unsigned</span>
    <h2>Signing status</h2>
    <p>
      This build is not Apple Developer ID signed or notarized yet. macOS may
      require Control-click &gt; Open after download.
    </p>
  </article>
  <article class="release-channel">
    <span class="status-pill">Planned</span>
    <h2>Windows</h2>
    <p>
      Windows packaging remains pending for a Windows build host. Signing is not
      required to run a beta build, but SmartScreen warnings are expected until
      signing is added.
    </p>
  </article>
</section>

## Download

| Item | URL |
| --- | --- |
| Beta gate | `https://downloads.lexishift.app/beta/` |
| Release manifest | `https://downloads.lexishift.app/releases/beta/latest.json` |
| Checksum file | `https://downloads.lexishift.app/checksums/beta/0.1.0/SHA256SUMS.txt` |

## Tester Notes

- Use the private beta password from your invite; it is not published on this
  public site.
- Verify the SHA-256 checksum after downloading the artifact.
- On macOS, use Control-click &gt; Open if Gatekeeper blocks the unsigned app.
- Replace older beta builds manually. There is no auto-update path yet.
- Send feedback through the [support page]({{ '/support/' | relative_url }}).

## Known Limitations

- macOS signing and notarization are not done yet.
- Windows beta packaging has not been published yet.
- Chrome extension distribution is separate from the desktop app download lane.
- User accounts, sync, and cloud backup are outside this beta milestone.

## Related Pages

- [Download LexiShift]({{ '/download/' | relative_url }})
- [Beta]({{ '/beta/' | relative_url }})
- [Guide]({{ '/guide/' | relative_url }})

</div>
