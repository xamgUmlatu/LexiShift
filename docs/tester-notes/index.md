---
layout: default
title: LexiShift Tester Notes
---

<!--
Status: active beta tester handoff
Role: Public tester-facing install checklist
Last updated: 2026-09-02
Purpose: give directly invited testers a short install and feedback checklist without publishing private beta credentials.
-->

<div class="tester-notes-page" markdown="1">

# LexiShift Tester Notes

This is a small, informal beta. If you were sent this page directly, the goal is
not to perform a full QA pass. The useful thing is to try the app like a normal
person and say what was confusing, broken, or surprisingly smooth.

## Install Both Parts

1. Open the [download gate](https://downloads.lexishift.app/beta/).
2. Enter the beta password from the private message.
3. Download `LexiShift-0.1.1.dmg`.
4. Open the DMG and drag LexiShift into Applications if prompted.
5. Open LexiShift.
6. Install the unlisted LexiShift Chrome extension from the Store link in your
   invitation. The link becomes available after Chrome Web Store review.
7. Open the extension's Options page.

The macOS build is unsigned for now. If macOS says it cannot verify the app,
Control-click LexiShift and choose Open. If macOS still blocks it, open System
Settings -> Privacy & Security and use the option to allow or open the app.

## Connect The App And Extension

The desktop app supplies local language and dictionary data; the extension
changes words on webpages. For the intended beta experience, both should be
running and using the same profile.

1. In LexiShift, create or select a profile and choose a language pair.
2. If prompted, use the app's browser-connection action for Chrome.
3. In extension Options, select the same profile and open Vocabulary Practice.
4. Start or resume a story and keep the desktop app available while testing.
5. Open a normal webpage and look for replaced words.

If the main setup is blocked, use the [small test-set tool]({{ '/test-sets/' | relative_url }})
to download a five-word manual ruleset and verify the extension independently.
That fixture is diagnostic; LR stories and Vocabulary Practice are the main beta.

## What To Try

Use the connected app and extension for a short first pass. A useful test can be
as simple as:

1. Launch LexiShift.
2. Create or open a profile.
3. Start Vocabulary Practice for one language pair.
4. Open a webpage and interact with one replaced word or popup.
5. Stop when anything feels confusing or broken and send a note.

Do not worry about testing every feature. Short, honest reactions are more
useful than trying to force a complete checklist.

## What To Send Back

Send feedback in the same private thread where you received the beta link.
Helpful notes include:

- what Mac you used, if you know it;
- whether the app and extension installed;
- whether the extension reported that its local helper was connected;
- the first step that felt unclear;
- any error message, copied exactly or shown in a screenshot;
- whether replacements appeared on a webpage;
- whether you were able to get to a point where the connected experience felt usable.

Avoid sending private text, browsing content, local files, or logs unless asked.
Screenshots are useful, but crop or blur anything personal first.

## Known Rough Edges

- The macOS app is not signed or notarized yet.
- Updates are manual; a new beta means downloading a new app file.
- Windows is not published through this beta gate yet.
- Account sync and cloud backup are not part of this beta.
- The Chrome extension is unlisted and its invitation link will not work until
  Chrome Web Store review is complete.

## Useful Links

- [Download LexiShift]({{ '/download/' | relative_url }})
- [Guide]({{ '/guide/' | relative_url }})
- [0.1.1 Release Notes]({{ '/releases/0.1.1/' | relative_url }})
- [Privacy]({{ '/privacy/' | relative_url }})
- [Support]({{ '/support/' | relative_url }})

</div>
