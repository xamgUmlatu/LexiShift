# LexiShift Getting Started

<!--
Status: active fallback onboarding guide
Role: Runbook / operational
Last updated: 2026-06-06
Last verified: 2026-06-06 user-facing structure pass; screenshot capture still pending
Purpose: provide the repository-view fallback onboarding guide when the rendered GitHub Pages manual is unavailable
Source-of-truth: user-facing fallback guide only; current behavior truth lives in source code, tests, and canonical developer/domain docs.
-->

This page is the fallback version of the user-facing onboarding guide. The
rendered guide is the preferred version when GitHub Pages is available.

Rendered guide: `https://lexishift.app/getting-started/`
Short invited-tester notes: `https://lexishift.app/tester-notes/`

LexiShift helps you practice vocabulary while reading normal text. Use the
desktop app to choose what you want to learn, then use the browser or chat tools
to see those words appear in context.

## Sections

1. Quick Start
2. Install and Open LexiShift
3. Make Your First Setup
4. Add Your First Replacements
5. Try Replacements in a Browser
6. Save, Export, and Back Up
7. Grow Your Vocabulary List
8. Optional Chat Setup
9. Optional Study Mode
10. Troubleshooting and FAQ

## 1. Quick Start

If you only want to see whether LexiShift makes sense, follow this path first.

1. Install the desktop app and open it.
2. Create a profile for the language or reading goal you want to try.
3. Add a few replacements, save them, and try them in a real reading place.

First beta note: the current macOS build is unsigned. If macOS blocks the first
launch, Control-click LexiShift and choose Open.

> Screenshot placeholder: `images/ch01-first-launch-workspace.png`
> Capture: first app window and main setup controls.

## 2. Install and Open LexiShift

Start from the download page or the private beta link you were given.

1. Download the current build from `https://lexishift.app/download/` or the private beta gate.
2. Open the downloaded file.
3. Move LexiShift into Applications if macOS asks.
4. Open LexiShift from Applications.

Unsigned beta: if macOS says the app cannot be verified, Control-click the app
and choose Open. If needed, check System Settings -> Privacy & Security for the
allow/open option.

> Screenshot placeholder: `images/ch02-install-open.png`
> Capture: DMG/app install step and first launch warning if present.

## 3. Make Your First Setup

LexiShift keeps your work in profiles and rulesets.

- Profile: a workspace for one goal, such as Spanish reading practice or a specific topic.
- Ruleset: the list of words or phrases LexiShift should replace for that profile.

1. Create a profile for the language or reading goal you want to test.
2. Create a ruleset inside that profile.
3. Choose the source and target languages if the app asks.
4. Save before moving on.

> Screenshot placeholder: `images/ch03-first-setup.png`
> Capture: profile selector and first ruleset setup.

## 4. Add Your First Replacements

A replacement tells LexiShift what text to look for and what learning word to
show instead. Start small so the result is easy to understand.

- Add one common word or short phrase.
- Choose the replacement you want to see while reading.
- Save the ruleset.
- Add only a few examples before testing them somewhere real.

Good first test: use words you already recognize. The point is to confirm the
replacement flow, not to build a huge vocabulary list on day one.

> Screenshot placeholder: `images/ch04-manual-rule-editing.png`
> Capture: rules table with one simple source and replacement pair.

## 5. Try Replacements in a Browser

The desktop app is where you set up your words. The browser extension is where
those words appear while you read web pages.

1. Install or enable the LexiShift Chrome extension when it is available for your test.
2. Open the extension options.
3. Choose the same profile you created in the desktop app.
4. Open a normal web page and check whether your replacements appear.

If you are only testing the desktop app right now, you can stop after creating
and saving a few replacements. The browser path can be tested separately.

> Screenshot placeholder: `images/ch05-browser-setup.png`
> Capture: extension options and a simple replacement on a page.

## 6. Save, Export, and Back Up

LexiShift is local-first. Your profiles, rulesets, and study state live on your
machine unless you export or share them.

- Save after editing replacements.
- Export a ruleset before making major changes.
- Export a profile when you want to move a setup to another machine.
- Keep a dated backup before trying bulk generation.

> Screenshot placeholder: `images/ch06-import-export-actions.png`
> Capture: export actions for rulesets and profiles.

## 7. Grow Your Vocabulary List

After the manual flow feels clear, LexiShift can help you build larger
replacement lists from installed language resources.

- Open `Settings -> App` and install language packs when they are available for your pair.
- Use Bulk Add to generate candidate replacements.
- Start with conservative settings and review samples.
- Save or export before applying large changes.

> Screenshot placeholder: `images/ch07-language-packs-bulk-add.png`
> Capture: installed language resources and the bulk suggestion flow.

## 8. Optional Chat Setup

If you use Discord with BetterDiscord, LexiShift can also apply replacements in
chat-style reading. This is optional and not part of the shortest first-day setup.

- Use the same exported rules or profile where possible.
- Keep browser and chat replacements aligned if you want a consistent experience.
- Adjust highlight settings for readability in message streams.

> Screenshot placeholder: `images/ch08-betterdiscord-plugin.png`
> Capture: plugin settings and a simple replacement in a message.

## 9. Optional Study Mode

Spaced review features are meant to help LexiShift adapt what you see over
time. You do not need this for the first install test.

- Feedback: rate learning words while reading so LexiShift can tell what felt easy or hard.
- Refresh: update the study list when you want LexiShift to change what it shows next.

Advanced checks:

- Make sure the extension is connected to the background helper.
- Choose the correct profile and language pair.
- Use diagnostics only when study behavior looks wrong.

> Screenshot placeholder: `images/ch09-srs-profile-pair-setup.png`
> Capture: study profile controls and feedback buttons.

## 10. Troubleshooting and FAQ

- The app will not open: on unsigned macOS beta builds, use Control-click > Open or check Privacy & Security settings.
- No replacements appear: make sure the right profile is selected, the ruleset is saved, and the extension is using that profile.
- Generated suggestions look weak: use fewer suggestions, raise confidence, and review examples before applying them.
- Browser connection fails: re-run helper installation from the app menu, then re-check extension options.

### Manual URL behavior

- Preferred guide URL: `https://lexishift.app/getting-started/`.
- Short tester notes URL: `https://lexishift.app/tester-notes/`.
- Fallback URL: repository `docs/getting-started/README.md`.

> Screenshot placeholder: `images/ch10-diagnostics-logs.png`
> Capture: useful diagnostics and helper connection checks.
