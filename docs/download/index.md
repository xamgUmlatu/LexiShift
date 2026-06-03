---
layout: default
title: Download LexiShift
---

# Download LexiShift

Status: staging
Role: Public download page
Last updated: 2026-06-04
Purpose: route users to signed installer assets, checksums, and release metadata after R2 distribution is live.

Installer downloads are not live yet.

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
