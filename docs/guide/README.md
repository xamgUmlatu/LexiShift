# LexiShift Guide

<!--
Status: active fallback user guide
Role: Runbook / operational
Last updated: 2026-06-06
Last verified: 2026-06-06 user-facing journey pass; screenshot capture still pending
Purpose: provide the repository-view fallback guide when the rendered GitHub Pages guide is unavailable
Source-of-truth: user-facing fallback guide only; current behavior truth lives in source code, tests, and canonical developer/domain docs.
-->

This page is the fallback version of the user-facing guide. The rendered guide is
the preferred version when GitHub Pages is available.

Rendered guide: `https://lexishift.app/guide/`
Short invited-tester notes: `https://lexishift.app/tester-notes/`

LexiShift helps you practice vocabulary while browsing the web. Install the app,
create a profile, start Vocabulary Practice, and let the browser extension show
learning words in real pages.

## Sections

1. Install LexiShift
2. Create Your Profile
3. Start Vocabulary Practice
4. Connect the Browser Extension
5. Browse and Give Feedback
6. Optional: Add Your Own Words
7. Save, Export, and Share
8. Optional: Chat Setup
9. Troubleshooting and FAQ

## 1. Install LexiShift

Start from the download page or the private beta link you were given. The beta
build is still unsigned, so your operating system may ask for one extra
confirmation the first time you open it.

- macOS: download the app, open the file, move LexiShift into Applications if prompted, then open it from Applications.
- Windows: download the Windows build, unzip or run it, then allow the beta app if SmartScreen asks you to confirm.

macOS privacy note: if macOS says LexiShift cannot be verified, Control-click
the app and choose Open. If that option does not appear, open System Settings ->
Privacy & Security and use the allow/open option near the bottom of the page.

Windows beta note: if SmartScreen appears, choose More info, then Run anyway.
This is expected for an unsigned early beta and should go away once release
signing is in place.

> Screenshot placeholder: `images/ch01-install-flow.png`
> Capture: macOS and Windows first-open prompts.

## 2. Create Your Profile

The first thing LexiShift asks for is a profile. A profile is just your space
for one language goal, such as English -> Spanish practice or a separate
experiment for German.

1. Open LexiShift and choose Create New Profile.
2. Name the profile after the language or goal you want to try.
3. Keep the profile selected when you open the browser extension options.

You may still see words like ruleset in the app. For this first pass, think of
rulesets as optional custom word lists. The main learning path is Vocabulary
Practice.

> Screenshot placeholder: `images/ch02-profile-creation.png`
> Capture: first-time profile creation screen.

## 3. Start Vocabulary Practice

Vocabulary Practice is the main language-journey flow. LexiShift picks a focused
set of learning words for your profile and language pair, shows them while you
browse, and uses your feedback to decide what to show more or less often.

1. Open the Chrome extension Options page.
2. Go to `Vocabulary Practice`.
3. Choose the same profile you created in the desktop app.
4. Use `Start Vocabulary Practice`.
5. Choose your language pair, preferences, and starting pace.

The current beta is still catching up UX-wise. Some language-journey controls
may be more obvious in the extension Options page than in the desktop app. That
is normal for now.

> Screenshot placeholder: `images/ch03-vocabulary-practice.png`
> Capture: Vocabulary Practice setup flow in extension options.

## 4. Connect the Browser Extension

The desktop app manages local data. The browser extension is where LexiShift
actually changes words while you browse.

1. Install or enable the LexiShift Chrome extension from the beta link you were given.
2. Open the extension Options page.
3. Choose the profile you created in the desktop app.
4. Confirm Vocabulary Practice is enabled for the language pair you want to test.

- Same profile: if the desktop app and extension use different profiles, replacements may not appear.
- Helper connected: if the extension asks for the helper, open the desktop app and use the helper install/connect action.

> Screenshot placeholder: `images/ch04-browser-extension.png`
> Capture: extension options with the selected profile and Vocabulary Practice status.

## 5. Browse and Give Feedback

This is the payoff: open a normal webpage and read naturally. LexiShift should
replace selected words from your active learning set.

1. Open a real page you would normally read.
2. Look for highlighted or replaced learning words.
3. Use feedback controls when a word feels easy, hard, or unfamiliar.

You do not need to optimize this on day one. The useful beta signal is whether
the replacements appear, feel readable, and make you want to keep browsing.

> Screenshot placeholder: `images/ch05-browse-feedback.png`
> Capture: normal web page with a replacement and feedback controls.

## 6. Optional: Add Your Own Words

Custom words are useful when you want direct control: names, hobby vocabulary,
words from a class, or a few examples you want to test by hand.

- Add one common word or short phrase.
- Choose the replacement you want to see while browsing.
- Save before testing in the browser extension.
- Keep the first list small so it is easy to tell what changed.

Custom word lists are not the main language-journey flow. Treat them as a fun
power-user path after Vocabulary Practice is working.

> Screenshot placeholder: `images/ch06-custom-words.png`
> Capture: one simple custom replacement.

## 7. Save, Export, and Share

LexiShift is local-first. Your profiles, custom word lists, and study state live
on your machine unless you export or share them.

- Save often after changing custom words or profile settings.
- Export before big changes, imports, bulk changes, or beta experiments.
- Share carefully; only share exports with people you intend to give that profile or word list to.
- Keep beta notes separate for informal family testing.

> Screenshot placeholder: `images/ch07-export-share.png`
> Capture: export actions for profiles and word lists.

## 8. Optional: Chat Setup

If you use Discord with BetterDiscord, LexiShift can also apply replacements in
chat-style reading. This is optional and should come after the browser flow
works.

- Use the same profile or exported word lists where possible.
- Keep browser and chat behavior aligned if you want a consistent experience.
- Adjust highlights so messages stay readable.

> Screenshot placeholder: `images/ch08-betterdiscord-plugin.png`
> Capture: plugin settings and a simple replacement in a message.

## 9. Troubleshooting and FAQ

- The app will not open: on unsigned beta builds, use the macOS or Windows allow/open steps in the install section.
- No replacements appear: make sure the extension is enabled, the right profile is selected, and Vocabulary Practice is active.
- Practice setup is blocked: install the required language data when the setup flow asks for it, then try again.
- Custom words do not show up: save the custom list, then confirm the extension is using the profile that contains it.

### Guide URLs and Help Buttons

- Preferred guide URL: `https://lexishift.app/guide/`.
- Old getting-started URL: `https://lexishift.app/getting-started/` redirects to the guide.
- Useful section anchors: `#install`, `#profile`, `#vocabulary-practice`, `#browser-extension`, and `#troubleshooting`.
- Repository fallback: `docs/guide/README.md`.

> Screenshot placeholder: `images/ch09-troubleshooting.png`
> Capture: useful helper connection and practice setup checks.
