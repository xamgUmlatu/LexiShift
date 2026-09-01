---
layout: default
title: LexiShift 0.1.1 Beta
---

<!--
Status: active beta release notes
Role: Tester-facing release notes
Last updated: 2026-09-02
Purpose: document the coordinated desktop and Chrome extension beta release.
-->

<div class="releases-page" markdown="1">

# LexiShift 0.1.1 Beta

This release coordinates the macOS desktop app, local helper, and Chrome
extension around the production Web Store extension ID. It is intended for a
small family-and-friends beta focused on whether the connected vocabulary
practice experience works and is understandable.

<section class="release-channel-grid">
  <article class="release-channel">
    <span class="status-pill status-pill--live">Live beta</span>
    <h2>macOS</h2>
    <p>
      The 0.1.1 macOS artifact is available through the private beta gate at
      <code>https://downloads.lexishift.app/beta/</code>.
    </p>
  </article>
  <article class="release-channel">
    <span class="status-pill status-pill--pending">Review pending</span>
    <h2>Chrome extension</h2>
    <p>
      Version 0.1.1 has been submitted as an unlisted Chrome Web Store beta.
      Invited testers receive the installation link after approval.
    </p>
  </article>
  <article class="release-channel">
    <span class="status-pill status-pill--pending">Unsigned</span>
    <h2>Signing status</h2>
    <p>
      The macOS build is not Apple Developer ID signed or notarized yet. macOS
      may require Control-click &gt; Open after download.
    </p>
  </article>
</section>

## What Changed

- The packaged app and helper recognize the production Chrome Web Store item.
- Vocabulary Practice and LR stories provide the primary beta learning flow.
- Replacement limits include page-wide and per-sentence controls.
- Popups use viewport-aware placement and grouped, collapsible dictionary entries.
- Optional imported dictionaries can be enabled and prioritized per language pair.
- A public five-word [test-set tool]({{ '/test-sets/' | relative_url }}) provides
  a small diagnostic path when the connected story flow needs troubleshooting.

## Download And Verification

| Item | URL |
| --- | --- |
| Beta gate | `https://downloads.lexishift.app/beta/` |
| Release manifest | `https://downloads.lexishift.app/releases/beta/latest.json` |
| Checksum file | `https://downloads.lexishift.app/checksums/beta/0.1.1/SHA256SUMS.txt` |

The macOS SHA-256 is:

```text
fcb4add5c8a22c4a04049c4f0bf89ae3d95a2f3b77647fc281a9939ccdb651ac
```

## Known Limitations

- macOS signing and notarization are not done yet.
- Windows is not published through the beta gate yet.
- Chrome Web Store approval is still pending.
- Updates are manual; there is no automatic desktop updater yet.
- User accounts, sync, and cloud backup are outside this beta.

## Related Pages

- [Beta overview]({{ '/beta/' | relative_url }})
- [Download LexiShift]({{ '/download/' | relative_url }})
- [Tester Notes]({{ '/tester-notes/' | relative_url }})
- [Guide]({{ '/guide/' | relative_url }})

</div>
