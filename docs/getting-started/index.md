---
layout: default
title: LexiShift Guide Moved
permalink: /getting-started/
---

<!--
Status: active compatibility redirect
Role: Redirect / compatibility
Last updated: 2026-06-06
Last verified: 2026-06-06 redirect added for guide route rename
Purpose: preserve old getting-started URLs while the user-facing guide moves to /guide/
Source-of-truth: redirect only; current guide content lives in `docs/guide/index.md`.
-->

<meta http-equiv="refresh" content="0; url={{ '/guide/' | relative_url }}">

<script>
(() => {
  const target = new URL("{{ '/guide/' | relative_url }}", window.location.href);
  target.search = window.location.search;
  target.hash = window.location.hash;
  window.location.replace(target.toString());
})();
</script>

# LexiShift Guide

The guide has moved to [lexishift.app/guide/]({{ '/guide/' | relative_url }}).

Old links to this page are kept as a compatibility route.
