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

This is also where SRS feedback is captured during real reading.

### Section 7.1: Runtime model

- Runtime applies local rules and helper rules together.
- SRS gating filters by replacement lemma when SRS is enabled.
- Feedback popup and exposure logging are runtime features on replaced spans.
- Module preferences are profile-scoped (enable/disable, order, per-module tuning).

### Section 7.2: Setup checklist in Options

1. Open the extension options page.
2. Select the extension profile used for this learning context.
3. Confirm language pair and runtime display settings.
4. Enable feedback behavior you want (`srsFeedbackSrsEnabled`, `srsFeedbackRulesEnabled`, `srsSoundEnabled`).
5. Turn on debug/exposure logging only when actively diagnosing behavior.

### Section 7.3: Verify runtime state

- Open a real webpage and confirm replacements render with expected highlighting.
- Right-click a replacement to confirm feedback popup availability.
- If needed, run `SRS runtime diagnostics` from options debug tools.

### Section 7.4: Mismatch triage

- Profile mismatch between GUI and extension is the most common failure mode.
- Unsaved rulesets in GUI produce stale runtime behavior.
- Helper offline/bridge issues can shift runtime to cached helper rules.

> Screenshot placeholder: `images/ch07-extension-options-overview.png`  
> Capture: profile picker, pair selection, and key runtime/SRS toggles.

> Screenshot placeholder: `images/ch07-extension-module-preferences.png`  
> Capture: per-profile module enable/disable, drag reorder, and color preview controls.

## Chapter 8: BetterDiscord Plugin Setup

BetterDiscord uses the same replacement core and is best for chat/message environments.

- Import the same JSON/share-code rules you use in other surfaces.
- Adjust highlight and click-to-toggle behavior for readability in chat streams.
- Treat plugin usage as another runtime profile target, not a separate authoring system.

Keep plugin and extension rulesets aligned when you want consistent vocabulary exposure across platforms.

> Screenshot placeholder: `images/ch08-betterdiscord-plugin.png`  
> Capture: plugin settings panel and a message with replacement highlighting.

## Chapter 9: SRS Setup and Expectations

This is the most important chapter. SRS behavior lives in the extension plus helper loop: initialize set `S`, collect feedback, refresh admissions, republish rules.

### Section 9.1: SRS model you should assume

- Scheduling is feedback-driven (ratings 1..4).
- Exposure logs are diagnostics/telemetry, not authoritative scheduling events.
- Helper profile store is the source of truth for mutable SRS schedule state.
- Local rules and helper SRS rules can run concurrently in runtime.

### Section 9.2: Extension preflight before initializing S

1. Install/verify helper connection in extension options.
2. Select the extension SRS profile (`srsSelectedProfileId`).
3. Select the language pair for this profile context.
4. Confirm pair resources are available (dictionaries/frequency inputs for that pair).

### Section 9.3: Core SRS controls in extension options

- `srsEnabled`: enables runtime SRS gating.
- `srsMaxActive`: cap on active lemmas allowed by gate.
- `srsBootstrapTopN`: initialization candidate pool size.
- `srsInitialActiveCount`: initial active subset size.
- `srsFeedbackSrsEnabled`/`srsFeedbackRulesEnabled`: popup eligibility by span origin.
- `srsSoundEnabled`: feedback sound toggle.
- `srsExposureLoggingEnabled`: diagnostics logging toggle.

### Section 9.4: Bootstrap and publish flow (first run)

1. Click `Initialize S for this pair` in extension options.
2. Wait for helper response with plan metadata and diagnostics notes.
3. Confirm runtime helper rules are published for the selected profile and pair.

Expected result: helper-managed `S` is initialized, ruleset/snapshot publish occurs, and runtime starts applying SRS-origin replacements.

### Section 9.5: Daily feedback loop in pages

1. Read normally on pages where replacements appear.
2. Right-click replacement spans and rate: 1=Again, 2=Hard, 3=Good, 4=Easy.
3. Use keyboard shortcut `Ctrl+1/2/3/4` for fast rating.
4. Allow helper feedback sync queue to flush ratings to helper store.

### Section 9.6: Refresh admissions and publish updates

1. Run `Refresh S + publish rules` from extension options.
2. Verify updated serving behavior on live pages.

Current model is explicit/manual refresh. Automatic adaptive refresh policy is still an in-progress track.

### Section 9.7: SRS diagnostics checklist

- Run `SRS runtime diagnostics` for helper/store/ruleset/cache counts.
- Run helper connection test and open helper data folder when troubleshooting.
- Use sampled rulegen preview for non-mutating inspection of current helper-managed `S`.
- If no SRS changes appear, check selected profile id + selected pair + feedback queue state first.

> Screenshot placeholder: `images/ch09-srs-profile-pair-setup.png`  
> Capture: selected profile, pair controls, and initialize/refresh buttons in extension options.

> Screenshot placeholder: `images/ch09-srs-feedback-popup.png`  
> Capture: in-page popup with rating actions (1..4) and any module stack above feedback controls.

> Screenshot placeholder: `images/ch09-srs-diagnostics.png`  
> Capture: runtime diagnostics output including helper/store/ruleset/cache count summary.

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
