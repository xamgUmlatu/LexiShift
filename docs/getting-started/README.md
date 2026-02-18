# LexiShift Getting Started

This page is the canonical onboarding guide for the desktop GUI app.

## Product Context

The GUI app is the authoring and management surface.

- Manage profiles.
- Manage rulesets linked to profiles.
- Create manual rules.
- Generate rules in bulk from synonym sources.
- Export/import profile and ruleset data.

The extension and BetterDiscord plugin are the runtime surfaces where rules are actually applied.
SRS usage primarily happens in those runtime surfaces.

## Current In-App Instruction Flow

Instruction entry points currently implemented in the GUI:

1. Main menu:
   - `Help -> Open Setup Guide`
2. Rules table empty-state card:
   - Small circular `?` button in the card's top-right corner.
   - Opens this guide.

The intent is to keep guidance discoverable without crowding the main workspace.

## Recommended User Flow

1. Create or import a profile.
2. Create a new ruleset or link an existing ruleset.
3. Add rules manually and/or run Synonym Bulk Add.
4. Save the ruleset.
5. Configure extension/plugin for runtime usage and SRS workflows.

## GitHub Manual Plan

This guide should evolve into a structured manual hosted on GitHub Pages.

Planned top-level guide sections:

1. First launch and profile setup
2. Profile management
3. Ruleset management
4. Manual rule authoring
5. Synonym bulk generation
6. Import/export and backup
7. Extension setup and runtime behavior
8. BetterDiscord setup
9. SRS setup and expectations
10. Troubleshooting and FAQ

## Localization Plan

The manual should ship in multiple locales with locale-specific links from the app UI.

Target locales:

- English
- Deutsch
- 日本語
- 中文（简体）

## Project Note

This page is currently the source target used by the in-app guide links.
As the manual grows, keep this URL stable and expand content in-place or redirect to locale paths.
