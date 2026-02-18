# LexiShift Getting Started

This page is the canonical onboarding guide for the desktop GUI app and the fallback public manual target when GitHub Pages is unavailable.

## Manual Chapters

1. [Chapter 1: First Launch and Workspace Orientation](#chapter-1-first-launch-and-workspace-orientation)
2. [Chapter 2: Profile Management](#chapter-2-profile-management)
3. [Chapter 3: Ruleset Management](#chapter-3-ruleset-management)
4. [Chapter 4: Manual Rule Authoring](#chapter-4-manual-rule-authoring)
5. [Chapter 5: Synonym Bulk Generation and Language Packs](#chapter-5-synonym-bulk-generation-and-language-packs)
6. [Chapter 6: Import, Export, and Backup](#chapter-6-import-export-and-backup)
7. [Chapter 7: Chrome Extension Runtime Setup](#chapter-7-chrome-extension-runtime-setup)
8. [Chapter 8: BetterDiscord Plugin Setup](#chapter-8-betterdiscord-plugin-setup)
9. [Chapter 9: SRS Setup and Expectations](#chapter-9-srs-setup-and-expectations)
10. [Chapter 10: Troubleshooting and FAQ](#chapter-10-troubleshooting-and-faq)

## Chapter 1: First Launch and Workspace Orientation

Goal: create a clean authoring baseline before you add any rules.

1. Launch the desktop GUI app.
2. Create a new profile or import an existing profile from JSON/share code.
3. Create a ruleset for that profile (or link an existing one).
4. Confirm the profile and ruleset selectors point to the pair you intend to edit.

The GUI is the authoring tool. Runtime replacement happens in the extension/plugin, so this setup step is mainly about making sure your profile/ruleset structure is correct.

> Screenshot placeholder: `images/ch01-first-launch-workspace.png`  
> Capture: initial GUI view with profile/ruleset selectors visible.

## Chapter 2: Profile Management

Profiles are top-level containers. They define the active working context and hold links to one or more rulesets.

- Use `Manage Profiles` to create, rename, or delete profiles.
- Use the profile selector to switch active context quickly.
- Keep separate profiles for separate goals (for example: reading practice vs domain vocabulary).

Recommended structure: one profile per workflow, multiple rulesets per profile, and one active ruleset per session.

> Screenshot placeholder: `images/ch02-manage-profiles-dialog.png`  
> Capture: profile list, create/delete controls, active-profile indicator.

## Chapter 3: Ruleset Management

Rulesets are where actual replacements live.

- Create a new ruleset for new work.
- Link existing rulesets when reusing prior datasets.
- Use save frequently after edits or bulk generation.
- Use ruleset management tools to reveal file locations and keep dataset hygiene.

Runtime surfaces use these rulesets directly (local rules + optional helper-generated rules). A wrong active ruleset is the most common source of "nothing replaced" behavior.

> Screenshot placeholder: `images/ch03-ruleset-management.png`  
> Capture: create/link actions and active ruleset selected in top controls.

## Chapter 4: Manual Rule Authoring

LexiShift replacement is deterministic: left-to-right longest-match using a trie with whitespace-preserving output.

- Add rules manually for precise source phrase to replacement mappings.
- Use priority when you need conflict control between overlapping phrases.
- Use case policies (`match`, `as-is`, `lower`, `upper`, `title`) deliberately.
- Keep phrase variants explicit when punctuation/spacing behavior matters.

Start with high-confidence manual rules before widening coverage with generated synonyms.

> Screenshot placeholder: `images/ch04-manual-rule-editing.png`  
> Capture: rules table with source/replacement columns and one metadata edit.

## Chapter 5: Synonym Bulk Generation and Language Packs

Bulk Add lets you scale rules quickly from installed dictionaries and language-pair pipelines.

- Open `Settings -> App` and install language packs.
- Supported wired sources include WordNet, Moby, OpenThesaurus, JP WordNet, JMDict, and CC-CEDICT.
- Current language-pair pipelines include `ja_en`, `en_de`, `en_es`, and `es_en`.
- Optional embedding conversion can improve ranking workflows for large vector sets.

Use conservative confidence thresholds first, then loosen only after reviewing generated samples.

> Screenshot placeholder: `images/ch05-language-packs-bulk-add.png`  
> Capture: Settings -> App language-pack manager plus synonym bulk-add dialog.

## Chapter 6: Import, Export, and Backup

LexiShift supports both ruleset-level and profile-level portability.

- Export rulesets as JSON or share code.
- Import rulesets from JSON or share code.
- Export/import profiles for full workflow transfer.
- Keep dated backups before major bulk operations.

Practical backup pattern: daily JSON export + milestone export before dictionary refreshes or mass rule changes.

> Screenshot placeholder: `images/ch06-import-export-actions.png`  
> Capture: File menu import/export options for rulesets and profiles.

## Chapter 7: Chrome Extension Runtime Setup

The extension is the primary runtime where replacements are applied on web pages and frames.

- Ensure extension profile/ruleset selection matches what you edited in the GUI.
- Use helper integration when you want SRS-gated helper rules and richer runtime diagnostics.
- Use highlight and feedback controls to validate rule quality in real content.
- Module preferences allow per-profile module enable/disable, ordering, and color tuning.

If runtime behavior differs from GUI preview, verify active profile, active ruleset, and helper status first.

> Screenshot placeholder: `images/ch07-extension-runtime-setup.png`  
> Capture: extension options page with profile/ruleset selection and runtime controls.

## Chapter 8: BetterDiscord Plugin Setup

BetterDiscord uses the same replacement core and is best for chat/message environments.

- Import the same JSON/share-code rules you use in other surfaces.
- Adjust highlight and click-to-toggle behavior for readability in chat streams.
- Treat plugin usage as another runtime profile target, not a separate authoring system.

Keep plugin and extension rulesets aligned when you want consistent vocabulary exposure across platforms.

> Screenshot placeholder: `images/ch08-betterdiscord-plugin.png`  
> Capture: plugin settings panel and a message with replacement highlighting.

## Chapter 9: SRS Setup and Expectations

SRS is primarily a runtime concern and is surfaced most deeply in extension/helper workflows.

- SRS store, scheduler, planning, bootstrap, and refresh are implemented in core/helper layers.
- Feedback/exposure signals flow back into SRS behavior and review scheduling.
- Profile-scoped SRS settings let you keep practice contexts isolated.

Expected model: author rules in GUI, practice and gather signals in runtime, then iterate rules and thresholds.

> Screenshot placeholder: `images/ch09-srs-setup-feedback.png`  
> Capture: SRS settings and in-page feedback/exposure UI.

## Chapter 10: Troubleshooting and FAQ

### No replacements are happening

- Confirm the active profile and active ruleset in GUI and runtime surface.
- Confirm rules are enabled and the ruleset is saved.
- Check for phrase mismatch, priority conflicts, or case-policy mismatch.

### Bulk generation quality is weak

- Raise confidence threshold and reduce source breadth.
- Verify language pack quality and pair alignment.
- Review samples before applying generated output broadly.

### Downloads or helper flows fail

- Use diagnostics and local log directory actions in the GUI.
- Re-run helper installation from the App menu if needed.

### Manual URL behavior

- Preferred guide URL: `https://xamgUmlatu.github.io/LexiShift/getting-started/`.
- Fallback URL: repository `docs/getting-started/README.md`.

> Screenshot placeholder: `images/ch10-diagnostics-logs.png`  
> Capture: debug menu actions and startup diagnostics dialog.
