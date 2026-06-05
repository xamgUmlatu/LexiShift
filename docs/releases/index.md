---
layout: default
title: LexiShift Releases
---

<!--
Status: active beta release index
Role: Public release index
Last updated: 2026-06-05
Purpose: provide a stable public release-notes route for release manifests and download pages.
-->

<div class="releases-page" markdown="1">

# LexiShift Releases

Release notes will appear here when beta installers are available.

<section class="release-channel-grid">
  <article class="release-channel">
    <span class="status-pill status-pill--live">Live beta</span>
    <h2>Beta 0.1.0</h2>
    <p>
      The macOS beta artifact is live behind the private download gate. This
      build is unsigned and not notarized; use the release notes before sharing
      it with testers.
    </p>
    <a href="{{ '/releases/0.1.0/' | relative_url }}">Read 0.1.0 notes</a>
  </article>
  <article class="release-channel">
    <span class="status-pill">Planned</span>
    <h2>Stable</h2>
    <p>
      Stable release notes stay parked until beta installation, update, and
      support flows have been proven.
    </p>
  </article>
</section>

## Channels

| Channel | Manifest |
| --- | --- |
| Beta | `https://downloads.lexishift.app/releases/beta/latest.json` |
| Stable | `https://downloads.lexishift.app/releases/stable/latest.json` |

## Published Beta Builds

- [0.1.0]({{ '/releases/0.1.0/' | relative_url }}) - macOS private beta, unsigned and not notarized.

## Related Pages

- [Download LexiShift]({{ '/download/' | relative_url }})
- [Beta]({{ '/beta/' | relative_url }})
- [Support]({{ '/support/' | relative_url }})

</div>
