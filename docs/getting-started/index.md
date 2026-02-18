---
layout: default
title: LexiShift Getting Started
---

<div class="guide-layout" data-guide-nav>
  <aside class="guide-rail" aria-label="Getting started chapters">
    <p class="guide-rail__title">Chapters</p>
    <a class="guide-rail__link is-active" href="#chapter-1">1. First Launch</a>
    <a class="guide-rail__link" href="#chapter-2">2. Profiles</a>
    <a class="guide-rail__link" href="#chapter-3">3. Rulesets</a>
    <a class="guide-rail__link" href="#chapter-4">4. Manual Rules</a>
    <a class="guide-rail__link" href="#chapter-5">5. Synonym Bulk Add</a>
    <a class="guide-rail__link" href="#chapter-6">6. Import and Backup</a>
    <a class="guide-rail__link" href="#chapter-7">7. Chrome Extension</a>
    <a class="guide-rail__link" href="#chapter-8">8. BetterDiscord</a>
    <a class="guide-rail__link" href="#chapter-9">9. SRS Setup</a>
    <a class="guide-rail__link" href="#chapter-10">10. Troubleshooting</a>
  </aside>

  <article class="guide-content">
    <header class="guide-hero">
      <p class="guide-eyebrow">LexiShift Manual</p>
      <h1>Getting Started</h1>
      <p>
        LexiShift has one authoring surface (desktop GUI) and runtime surfaces (Chrome extension and BetterDiscord plugin).
        Build rules in the GUI, then activate them in the runtime surfaces.
      </p>
    </header>

    <section id="chapter-1" class="guide-section" data-guide-section>
      <h2>Chapter 1: First Launch and Workspace Orientation</h2>
      <p>Goal: create a clean authoring baseline before you add any rules.</p>
      <ol>
        <li>Launch the desktop GUI app.</li>
        <li>Create a new profile or import an existing profile from JSON/share code.</li>
        <li>Create a ruleset for that profile (or link an existing one).</li>
        <li>Confirm the profile and ruleset selectors point to the pair you intend to edit.</li>
      </ol>
      <p>
        The GUI is the authoring tool. Runtime replacement happens in the extension/plugin,
        so this setup step is mainly about making sure your profile/ruleset structure is correct.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for first launch workspace">
        <p class="guide-screenshot__label">Screenshot Placeholder: First Launch Workspace</p>
        <p class="guide-screenshot__note">Capture the initial GUI view with profile/ruleset selectors visible.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch01-first-launch-workspace.png</code></p>
      </div>
    </section>

    <section id="chapter-2" class="guide-section" data-guide-section>
      <h2>Chapter 2: Profile Management</h2>
      <p>
        Profiles are top-level containers. They define the active working context and hold links to one or more rulesets.
      </p>
      <ul>
        <li>Use <code>Manage Profiles</code> to create, rename, or delete profiles.</li>
        <li>Use the profile selector to switch active context quickly.</li>
        <li>Keep separate profiles for separate goals (for example: reading practice vs domain vocabulary).</li>
      </ul>
      <p>
        Recommended structure: one profile per workflow, multiple rulesets per profile, and one active ruleset per session.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for profile management dialog">
        <p class="guide-screenshot__label">Screenshot Placeholder: Manage Profiles Dialog</p>
        <p class="guide-screenshot__note">Capture profile list, create/delete controls, and active-profile indicator.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch02-manage-profiles-dialog.png</code></p>
      </div>
    </section>

    <section id="chapter-3" class="guide-section" data-guide-section>
      <h2>Chapter 3: Ruleset Management</h2>
      <p>Rulesets are where actual replacements live.</p>
      <ul>
        <li>Create a new ruleset for new work.</li>
        <li>Link existing rulesets when reusing prior datasets.</li>
        <li>Use save frequently after edits or bulk generation.</li>
        <li>Use ruleset management tools to reveal file locations and keep dataset hygiene.</li>
      </ul>
      <p>
        Runtime surfaces use these rulesets directly (local rules + optional helper-generated rules).
        A wrong active ruleset is the most common source of "nothing replaced" behavior.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for ruleset management flow">
        <p class="guide-screenshot__label">Screenshot Placeholder: Ruleset Management</p>
        <p class="guide-screenshot__note">Capture create/link actions plus the active ruleset selected in the top controls.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch03-ruleset-management.png</code></p>
      </div>
    </section>

    <section id="chapter-4" class="guide-section" data-guide-section>
      <h2>Chapter 4: Manual Rule Authoring</h2>
      <p>
        LexiShift replacement is deterministic: left-to-right longest-match using a trie with whitespace-preserving output.
      </p>
      <ul>
        <li>Add rules manually for precise source phrase to replacement mappings.</li>
        <li>Use priority when you need conflict control between overlapping phrases.</li>
        <li>Use case policies (<code>match</code>, <code>as-is</code>, <code>lower</code>, <code>upper</code>, <code>title</code>) deliberately.</li>
        <li>Keep phrase variants explicit when punctuation/spacing behavior matters.</li>
      </ul>
      <p>
        Start with high-confidence manual rules before widening coverage with generated synonyms.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for manual rule editing">
        <p class="guide-screenshot__label">Screenshot Placeholder: Manual Rule Editing</p>
        <p class="guide-screenshot__note">Capture the rules table with source/replacement columns and one metadata edit example.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch04-manual-rule-editing.png</code></p>
      </div>
    </section>

    <section id="chapter-5" class="guide-section" data-guide-section>
      <h2>Chapter 5: Synonym Bulk Generation and Language Packs</h2>
      <p>
        Bulk Add lets you scale rules quickly from installed dictionaries and language-pair pipelines.
      </p>
      <ul>
        <li>Open <code>Settings -> App</code> and install language packs.</li>
        <li>Supported wired sources include WordNet, Moby, OpenThesaurus, JP WordNet, JMDict, and CC-CEDICT.</li>
        <li>Current language-pair pipelines include <code>ja_en</code>, <code>en_de</code>, <code>en_es</code>, and <code>es_en</code>.</li>
        <li>Optional embedding conversion can improve ranking workflows for large vector sets.</li>
      </ul>
      <p>
        Use conservative confidence thresholds first, then loosen only after reviewing generated samples.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for language packs and bulk add">
        <p class="guide-screenshot__label">Screenshot Placeholder: Language Packs and Bulk Add</p>
        <p class="guide-screenshot__note">Capture Settings -> App language-pack manager and the synonym bulk-add dialog.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch05-language-packs-bulk-add.png</code></p>
      </div>
    </section>

    <section id="chapter-6" class="guide-section" data-guide-section>
      <h2>Chapter 6: Import, Export, and Backup</h2>
      <p>LexiShift supports both ruleset-level and profile-level portability.</p>
      <ul>
        <li>Export rulesets as JSON or share code.</li>
        <li>Import rulesets from JSON or share code.</li>
        <li>Export/import profiles for full workflow transfer.</li>
        <li>Keep dated backups before major bulk operations.</li>
      </ul>
      <p>
        Practical backup pattern: daily JSON export + milestone export before dictionary refreshes or mass rule changes.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for import and export actions">
        <p class="guide-screenshot__label">Screenshot Placeholder: Import/Export Actions</p>
        <p class="guide-screenshot__note">Capture File menu import/export options for rulesets and profiles.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch06-import-export-actions.png</code></p>
      </div>
    </section>

    <section id="chapter-7" class="guide-section" data-guide-section>
      <h2>Chapter 7: Chrome Extension Runtime Setup</h2>
      <p>
        The extension is the primary runtime where replacements are applied on web pages and frames.
      </p>
      <ul>
        <li>Ensure extension profile/ruleset selection matches what you edited in the GUI.</li>
        <li>Use helper integration when you want SRS-gated helper rules and richer runtime diagnostics.</li>
        <li>Use highlight and feedback controls to validate rule quality in real content.</li>
        <li>Module preferences allow per-profile module enable/disable, ordering, and color tuning.</li>
      </ul>
      <p>
        If runtime behavior differs from GUI preview, verify active profile, active ruleset, and helper status first.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for extension runtime setup">
        <p class="guide-screenshot__label">Screenshot Placeholder: Chrome Extension Setup</p>
        <p class="guide-screenshot__note">Capture extension options page showing profile/ruleset selection and runtime controls.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch07-extension-runtime-setup.png</code></p>
      </div>
    </section>

    <section id="chapter-8" class="guide-section" data-guide-section>
      <h2>Chapter 8: BetterDiscord Plugin Setup</h2>
      <p>
        BetterDiscord uses the same replacement core and is best for chat/message environments.
      </p>
      <ul>
        <li>Import the same JSON/share-code rules you use in other surfaces.</li>
        <li>Adjust highlight and click-to-toggle behavior for readability in chat streams.</li>
        <li>Treat plugin usage as another runtime profile target, not a separate authoring system.</li>
      </ul>
      <p>
        Keep plugin and extension rulesets aligned when you want consistent vocabulary exposure across platforms.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for BetterDiscord plugin settings">
        <p class="guide-screenshot__label">Screenshot Placeholder: BetterDiscord Plugin</p>
        <p class="guide-screenshot__note">Capture plugin settings panel and a message example showing replacement highlights.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch08-betterdiscord-plugin.png</code></p>
      </div>
    </section>

    <section id="chapter-9" class="guide-section" data-guide-section>
      <h2>Chapter 9: SRS Setup and Expectations</h2>
      <p>
        SRS is primarily a runtime concern and is surfaced most deeply in extension/helper workflows.
      </p>
      <ul>
        <li>SRS store, scheduler, planning, bootstrap, and refresh are implemented in core/helper layers.</li>
        <li>Feedback/exposure signals flow back into SRS behavior and review scheduling.</li>
        <li>Profile-scoped SRS settings let you keep practice contexts isolated.</li>
      </ul>
      <p>
        Expected model: author rules in GUI, practice and gather signals in runtime, then iterate rules and thresholds.
      </p>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for SRS setup and feedback">
        <p class="guide-screenshot__label">Screenshot Placeholder: SRS Setup and Feedback</p>
        <p class="guide-screenshot__note">Capture SRS settings plus in-page feedback popup or exposure UI.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch09-srs-setup-feedback.png</code></p>
      </div>
    </section>

    <section id="chapter-10" class="guide-section" data-guide-section>
      <h2>Chapter 10: Troubleshooting and FAQ</h2>
      <h3>No replacements are happening</h3>
      <ul>
        <li>Confirm the active profile and active ruleset in GUI and runtime surface.</li>
        <li>Confirm rules are enabled and the ruleset is saved.</li>
        <li>Check for phrase mismatch, priority conflicts, or case-policy mismatch.</li>
      </ul>
      <h3>Bulk generation quality is weak</h3>
      <ul>
        <li>Raise confidence threshold and reduce source breadth.</li>
        <li>Verify language pack quality and pair alignment.</li>
        <li>Review samples before applying generated output broadly.</li>
      </ul>
      <h3>Downloads or helper flows fail</h3>
      <ul>
        <li>Use diagnostics and local log directory actions in the GUI.</li>
        <li>Re-run helper installation from the App menu if needed.</li>
      </ul>
      <h3>Manual URL behavior</h3>
      <ul>
        <li>Preferred guide URL: <code>https://xamgUmlatu.github.io/LexiShift/getting-started/</code>.</li>
        <li>Fallback URL: repository <code>docs/getting-started/README.md</code>.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for diagnostics and logs">
        <p class="guide-screenshot__label">Screenshot Placeholder: Diagnostics and Logs</p>
        <p class="guide-screenshot__note">Capture debug menu actions and startup diagnostics dialog for troubleshooting.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch10-diagnostics-logs.png</code></p>
      </div>
    </section>
  </article>
</div>

<script src="{{ '/assets/js/getting-started-nav.js' | relative_url }}" defer></script>
