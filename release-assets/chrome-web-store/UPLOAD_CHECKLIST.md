# Chrome Web Store 0.1.1 submission handoff

Current status: submitted for review on September 2, 2026 as an unlisted beta.
Dashboard package version `0.1.1` and production item ID were confirmed before
submission. Approval and the final Store install smoke remain pending.

This checklist begins after the repository preflight and release package build.
The Chrome Web Store dashboard remains a manual maintainer surface. Stop after
saving the completed draft if the release is not yet ready to enter review.

## Upload files

- Extension ZIP: `dist/cws/lexishift-chrome-extension-0.1.1-beta.zip`
- ZIP checksum: `dist/cws/lexishift-chrome-extension-0.1.1-beta.zip.sha256`
- Screenshot 1: `release-assets/chrome-web-store/screenshots/final/01-reading-sample-1280x800.png`
- Screenshot 2: `release-assets/chrome-web-store/screenshots/final/02-definition-popup-1280x800.png`
- Small promotional tile: `release-assets/chrome-web-store/promo/final/small-promo-440x280.png`

Production extension ID: `mgalgndncinhfceghjbpjonmgkfbfkgk`

## Manual dashboard pass

1. Upload the `0.1.1` ZIP to the existing item. Confirm the accepted version is
   `0.1.1` and the item ID remains unchanged.
2. Upload both 1280 x 800 screenshots under the all-languages screenshot area.
3. Upload the 440 x 280 image under Small promotional tile. The 1400 x 560
   marquee tile is optional for this beta.
4. Complete the listing description, category, and language fields.
5. Complete the privacy declarations and use
   `https://lexishift.app/privacy/` as the privacy-policy URL.
6. Explain the single purpose, `storage`, `nativeMessaging`, and all-sites page
   access. State that page processing and practice state are local-first and
   that extension code is packaged rather than remotely executed.
7. In reviewer instructions, provide a minimal visible-replacement test and
   explain that SRS/helper-backed features require the LexiShift desktop app,
   while cached/manual rules can operate in the degraded no-helper path.
8. Choose the beta visibility. `Unlisted` is the lowest-friction family/friends
   option; `Private` requires explicit trusted tester accounts.
9. Verify the publisher contact email.
10. Save and submit the completed draft when the coordinated beta release is
    ready. For this release, submission is complete and the matching desktop
    download is live; wait for the review result before sending tester invites.

Do not upload the old `0.1.0` draft ZIP: it predates the production native
messaging ID and the integrated beta fixes.
