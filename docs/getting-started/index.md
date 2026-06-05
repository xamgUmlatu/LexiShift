---
layout: default
title: LexiShift Getting Started
---

<!--
Status: active Pages onboarding guide
Role: Runbook / operational
Last updated: 2026-06-06
Last verified: 2026-06-06 user-facing structure pass; screenshot capture still pending
Purpose: present the rendered interactive getting-started guide for LexiShift users
Source-of-truth: user-facing onboarding guide only; current GUI, extension, plugin, and SRS behavior truth lives in source code, tests, and canonical developer/domain docs.
-->

<script>
(() => {
  const themeKey = "lexishift_guide_theme";
  const localeKey = "lexishift_guide_locale";
  const supportedLocales = new Set([
    "system",
    "en",
    "es",
    "fr",
    "eo",
    "de",
    "it",
    "ja",
    "zh-hant",
    "zh-hans",
  ]);
  let theme = "dark";
  let localePref = "system";

  const normalizeLocale = (value) =>
    String(value || "")
      .trim()
      .toLowerCase()
      .replace(/_/g, "-");

  const resolveLocalePreference = (value) => {
    const normalized = normalizeLocale(value);
    if (supportedLocales.has(normalized)) {
      return normalized;
    }
    if (
      normalized.startsWith("zh-hant")
      || normalized.startsWith("zh-tw")
      || normalized.startsWith("zh-hk")
      || normalized.startsWith("zh-mo")
    ) {
      return "zh-hant";
    }
    if (normalized.startsWith("zh")) {
      return "zh-hans";
    }
    const languageTag = normalized.split("-")[0];
    if (supportedLocales.has(languageTag)) {
      return languageTag;
    }
    return "system";
  };

  try {
    const saved = localStorage.getItem(themeKey);
    theme = saved === "light" ? "light" : "dark";
  } catch (_error) {
    theme = "dark";
  }

  try {
    localePref = resolveLocalePreference(localStorage.getItem(localeKey));
  } catch (_error) {
    localePref = "system";
  }

  const systemLocale = normalizeLocale(
    (typeof navigator !== "undefined" && navigator.language) || "en",
  ) || "en";
  const resolvedLocale = localePref === "system" ? systemLocale : localePref;

  document.documentElement.setAttribute("data-guide-theme", theme);
  document.documentElement.setAttribute("data-guide-locale-preference", localePref);
  document.documentElement.setAttribute("data-guide-locale", resolvedLocale);
})();
</script>

<div class="guide-layout" data-guide-nav>
  <div class="guide-floating-controls" aria-label="Guide display controls">
    <button
      class="guide-theme-toggle"
      type="button"
      aria-label="Switch to light mode"
      title="Switch to light mode"
      data-guide-theme-toggle
    >
      <span class="guide-theme-toggle__icon guide-theme-toggle__icon--sun" aria-hidden="true">
        <svg viewBox="0 0 24 24" role="img" focusable="false">
          <circle cx="12" cy="12" r="4"></circle>
          <path d="M12 2v3M12 19v3M4.93 4.93l2.12 2.12M16.95 16.95l2.12 2.12M2 12h3M19 12h3M4.93 19.07l2.12-2.12M16.95 7.05l2.12-2.12"></path>
        </svg>
      </span>
      <span class="guide-theme-toggle__icon guide-theme-toggle__icon--moon" aria-hidden="true">
        <svg viewBox="0 0 24 24" role="img" focusable="false">
          <path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a7 7 0 1 0 10.7 10.7z"></path>
        </svg>
      </span>
    </button>
    <div class="guide-locale-shell" data-guide-locale-shell>
      <button
        class="guide-locale-toggle"
        type="button"
        aria-label="Language: System default. Click to open language grid."
        title="Language: System default. Click to open language grid."
        aria-expanded="false"
        aria-controls="guide-locale-panel"
        data-guide-locale-toggle
      >
        <span class="guide-locale-toggle__icon" aria-hidden="true">🌐</span>
      </button>
      <div
        class="guide-locale-panel"
        id="guide-locale-panel"
        role="listbox"
        aria-label="Guide language options"
        aria-hidden="true"
        data-guide-locale-panel
      >
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="en">EN</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="es">ES</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="fr">FR</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="eo">EO</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="de">DE</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="it">IT</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="ja">日</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="zh-hant">繁</button>
        <button class="guide-locale-cell" type="button" role="option" data-guide-locale-option="zh-hans">简</button>
      </div>
    </div>
  </div>
  <aside class="guide-rail" aria-label="Getting started sections">
    <p class="guide-rail__title">Sections</p>
    <a class="guide-rail__link is-active" href="#chapter-1">1. Quick Start</a>
    <a class="guide-rail__link" href="#chapter-2">2. Install</a>
    <a class="guide-rail__link" href="#chapter-3">3. First Setup</a>
    <a class="guide-rail__link" href="#chapter-4">4. Replacements</a>
    <a class="guide-rail__link" href="#chapter-5">5. Try in Browser</a>
    <a class="guide-rail__link" href="#chapter-6">6. Save and Backup</a>
    <a class="guide-rail__link" href="#chapter-7">7. Grow Vocabulary</a>
    <a class="guide-rail__link" href="#chapter-8">8. Chat Setup</a>
    <a class="guide-rail__link" href="#chapter-9">9. Study Mode</a>
    <a class="guide-rail__link" href="#chapter-10">10. Troubleshooting</a>
  </aside>

  <article class="guide-content">
    <header class="guide-hero">
      <p class="guide-eyebrow">LexiShift Guide</p>
      <h1>Getting Started</h1>
      <p>
        LexiShift helps you practice vocabulary while reading normal text. Use
        the desktop app to choose what you want to learn, then use the browser
        or chat tools to see those words appear in context.
      </p>
      <p>
        This guide starts with the shortest useful path. Advanced features are
        still here, but they come after the basics.
      </p>
      <div class="guide-hero__actions">
        <a class="guide-button guide-button--primary" href="{{ '/download/' | relative_url }}">Download LexiShift</a>
        <a class="guide-button" href="{{ '/tester-notes/' | relative_url }}">Beta Tester Notes</a>
      </div>
    </header>

    <section id="chapter-1" class="guide-section" data-guide-section>
      <h2>1. Quick Start</h2>
      <p>
        If you only want to see whether LexiShift makes sense, follow this path
        first. You can come back to the advanced sections later.
      </p>
      <div class="guide-step-grid">
        <div class="guide-step">
          <strong>1</strong>
          <span>Install the desktop app and open it.</span>
        </div>
        <div class="guide-step">
          <strong>2</strong>
          <span>Create a profile for the language or reading goal you want to try.</span>
        </div>
        <div class="guide-step">
          <strong>3</strong>
          <span>Add a few replacements, save them, and try them in a real reading place.</span>
        </div>
      </div>
      <div class="guide-callout">
        <p>
          <strong>First beta note:</strong> the current macOS build is unsigned.
          If macOS blocks the first launch, Control-click LexiShift and choose
          Open.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for first launch workspace">
        <p class="guide-screenshot__label">Screenshot Coming Soon: First Launch</p>
        <p class="guide-screenshot__note">This slot will show the first app window and the main setup controls.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch01-first-launch-workspace.png</code></p>
      </div>
    </section>

    <section id="chapter-2" class="guide-section" data-guide-section>
      <h2>2. Install and Open LexiShift</h2>
      <p>
        Start from the download page or the private beta link you were given.
        The app should be installed like a normal desktop app.
      </p>
      <ol>
        <li>Download the current build from the <a href="{{ '/download/' | relative_url }}">download page</a> or private beta gate.</li>
        <li>Open the downloaded file.</li>
        <li>Move LexiShift into Applications if macOS asks.</li>
        <li>Open LexiShift from Applications.</li>
      </ol>
      <div class="guide-callout">
        <p>
          <strong>Unsigned beta:</strong> if macOS says the app cannot be
          verified, Control-click the app and choose Open. If needed, check
          System Settings -> Privacy &amp; Security for the allow/open option.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for install flow">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Install Flow</p>
        <p class="guide-screenshot__note">This slot will show the DMG/app install step and the first launch warning if present.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch02-install-open.png</code></p>
      </div>
    </section>

    <section id="chapter-3" class="guide-section" data-guide-section>
      <h2>3. Make Your First Setup</h2>
      <p>
        LexiShift keeps your work in profiles and rulesets. The names are a bit
        technical, but the idea is simple.
      </p>
      <div class="guide-card-grid">
        <div class="guide-card">
          <strong>Profile</strong>
          <span>A workspace for one goal, such as Spanish reading practice or a specific topic.</span>
        </div>
        <div class="guide-card">
          <strong>Ruleset</strong>
          <span>The list of words or phrases LexiShift should replace for that profile.</span>
        </div>
      </div>
      <ol>
        <li>Create a profile for the language or reading goal you want to test.</li>
        <li>Create a ruleset inside that profile.</li>
        <li>Choose the source and target languages if the app asks.</li>
        <li>Save before moving on.</li>
      </ol>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for first setup">
        <p class="guide-screenshot__label">Screenshot Coming Soon: First Profile and Ruleset</p>
        <p class="guide-screenshot__note">This slot will show the profile selector and first ruleset setup.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch03-first-setup.png</code></p>
      </div>
    </section>

    <section id="chapter-4" class="guide-section" data-guide-section>
      <h2>4. Add Your First Replacements</h2>
      <p>
        A replacement tells LexiShift what text to look for and what learning
        word to show instead. Start small so the result is easy to understand.
      </p>
      <ul>
        <li>Add one common word or short phrase.</li>
        <li>Choose the replacement you want to see while reading.</li>
        <li>Save the ruleset.</li>
        <li>Add only a few examples before testing them somewhere real.</li>
      </ul>
      <div class="guide-callout">
        <p>
          <strong>Good first test:</strong> use words you already recognize.
          The point is to confirm the replacement flow, not to build a huge
          vocabulary list on day one.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for manual rule editing">
        <p class="guide-screenshot__label">Screenshot Coming Soon: First Replacement</p>
        <p class="guide-screenshot__note">This slot will show the rules table with one simple source and replacement pair.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch04-manual-rule-editing.png</code></p>
      </div>
    </section>

    <section id="chapter-5" class="guide-section" data-guide-section>
      <h2>5. Try Replacements in a Browser</h2>
      <p>
        The desktop app is where you set up your words. The browser extension is
        where those words appear while you read web pages.
      </p>
      <ol>
        <li>Install or enable the LexiShift Chrome extension when it is available for your test.</li>
        <li>Open the extension options.</li>
        <li>Choose the same profile you created in the desktop app.</li>
        <li>Open a normal web page and check whether your replacements appear.</li>
      </ol>
      <div class="guide-callout">
        <p>
          If you are only testing the desktop app right now, you can stop after
          creating and saving a few replacements. The browser path can be tested
          separately.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for browser extension setup">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Browser Setup</p>
        <p class="guide-screenshot__note">This slot will show the extension options and a simple replacement on a page.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch05-browser-setup.png</code></p>
      </div>
    </section>

    <section id="chapter-6" class="guide-section" data-guide-section>
      <h2>6. Save, Export, and Back Up</h2>
      <p>
        LexiShift is local-first. Your profiles, rulesets, and study state live
        on your machine unless you export or share them.
      </p>
      <ul>
        <li>Save after editing replacements.</li>
        <li>Export a ruleset before making major changes.</li>
        <li>Export a profile when you want to move a setup to another machine.</li>
        <li>Keep a dated backup before trying bulk generation.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for import and export actions">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Export and Backup</p>
        <p class="guide-screenshot__note">This slot will show the export actions for rulesets and profiles.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch06-import-export-actions.png</code></p>
      </div>
    </section>

    <section id="chapter-7" class="guide-section" data-guide-section>
      <h2>7. Grow Your Vocabulary List</h2>
      <p>
        After the manual flow feels clear, LexiShift can help you build larger
        replacement lists from installed language resources.
      </p>
      <div class="guide-check-grid">
        <div class="guide-check">
          <strong>Use this later</strong>
          <span>Bulk tools are useful once you trust the basic setup.</span>
        </div>
        <div class="guide-check">
          <strong>Review before applying</strong>
          <span>Generated suggestions should be checked before they become part of your main list.</span>
        </div>
      </div>
      <ul>
        <li>Open <code>Settings -> App</code> and install language packs when they are available for your pair.</li>
        <li>Use Bulk Add to generate candidate replacements.</li>
        <li>Start with conservative settings and review samples.</li>
        <li>Save or export before applying large changes.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for language packs and bulk add">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Language Packs and Bulk Add</p>
        <p class="guide-screenshot__note">This slot will show installed language resources and the bulk suggestion flow.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch07-language-packs-bulk-add.png</code></p>
      </div>
    </section>

    <section id="chapter-8" class="guide-section" data-guide-section>
      <h2>8. Optional Chat Setup</h2>
      <p>
        If you use Discord with BetterDiscord, LexiShift can also apply
        replacements in chat-style reading. This is optional and not part of the
        shortest first-day setup.
      </p>
      <ul>
        <li>Use the same exported rules or profile where possible.</li>
        <li>Keep browser and chat replacements aligned if you want a consistent experience.</li>
        <li>Adjust highlight settings for readability in message streams.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for BetterDiscord plugin settings">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Chat Setup</p>
        <p class="guide-screenshot__note">This slot will show plugin settings and a simple replacement in a message.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch08-betterdiscord-plugin.png</code></p>
      </div>
    </section>

    <section id="chapter-9" class="guide-section" data-guide-section>
      <h2>9. Optional Study Mode</h2>
      <p>
        Spaced review features are meant to help LexiShift adapt what you see
        over time. You do not need this for the first install test.
      </p>
      <div class="guide-card-grid">
        <div class="guide-card">
          <strong>Feedback</strong>
          <span>Rate learning words while reading so LexiShift can tell what felt easy or hard.</span>
        </div>
        <div class="guide-card">
          <strong>Refresh</strong>
          <span>Update the study list when you want LexiShift to change what it shows next.</span>
        </div>
      </div>
      <h3>Advanced checks</h3>
      <ul>
        <li>Make sure the extension is connected to the background helper.</li>
        <li>Choose the correct profile and language pair.</li>
        <li>Use diagnostics only when study behavior looks wrong.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for SRS profile and pair setup">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Study Mode</p>
        <p class="guide-screenshot__note">This slot will show the study profile controls and feedback buttons.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch09-srs-profile-pair-setup.png</code></p>
      </div>
    </section>

    <section id="chapter-10" class="guide-section" data-guide-section>
      <h2>10. Troubleshooting and FAQ</h2>
      <div class="guide-check-grid">
        <div class="guide-check">
          <strong>The app will not open</strong>
          <span>On unsigned macOS beta builds, use Control-click > Open or check Privacy &amp; Security settings.</span>
        </div>
        <div class="guide-check">
          <strong>No replacements appear</strong>
          <span>Make sure the right profile is selected, the ruleset is saved, and the extension is using that profile.</span>
        </div>
        <div class="guide-check">
          <strong>Generated suggestions look weak</strong>
          <span>Use fewer suggestions, raise confidence, and review examples before applying them.</span>
        </div>
        <div class="guide-check">
          <strong>Browser connection fails</strong>
          <span>Re-run helper installation from the app menu, then re-check extension options.</span>
        </div>
      </div>
      <h3>Manual URL behavior</h3>
      <ul>
        <li>Preferred guide URL: <code>https://lexishift.app/getting-started/</code>.</li>
        <li>Short tester notes URL: <code>https://lexishift.app/tester-notes/</code>.</li>
        <li>Fallback URL: repository <code>docs/getting-started/README.md</code>.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for diagnostics and logs">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Troubleshooting</p>
        <p class="guide-screenshot__note">This slot will show the most useful diagnostics and helper connection checks.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch10-diagnostics-logs.png</code></p>
      </div>
    </section>
  </article>
</div>

<script src="{{ '/assets/js/getting-started-nav.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/getting-started-theme.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/getting-started-locale.js' | relative_url }}" defer></script>
