---
layout: default
title: LexiShift Guide
---

<!--
Status: active Pages user guide
Role: Runbook / operational
Last updated: 2026-09-02
Last verified: 2026-09-02 coordinated 0.1.1 beta onboarding pass; screenshot capture still pending
Purpose: present the rendered interactive guide for LexiShift users and beta testers
Source-of-truth: user-facing guide only; current GUI, extension, plugin, and SRS behavior truth lives in source code, tests, and canonical developer/domain docs.
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
  <aside class="guide-rail" aria-label="Guide sections">
    <p class="guide-rail__title">Sections</p>
    <a class="guide-rail__link is-active" href="#install">1. Install</a>
    <a class="guide-rail__link" href="#profile">2. Profile</a>
    <a class="guide-rail__link" href="#vocabulary-practice">3. Vocabulary Practice</a>
    <a class="guide-rail__link" href="#browser-extension">4. Browser Extension</a>
    <a class="guide-rail__link" href="#browse-feedback">5. Browse and Feedback</a>
    <a class="guide-rail__link" href="#custom-words">6. Custom Words</a>
    <a class="guide-rail__link" href="#save-share">7. Save and Share</a>
    <a class="guide-rail__link" href="#chat-setup">8. Chat Setup</a>
    <a class="guide-rail__link" href="#troubleshooting">9. Troubleshooting</a>
  </aside>

  <article class="guide-content">
    <header class="guide-hero">
      <p class="guide-eyebrow">LexiShift Guide</p>
      <h1>Guide</h1>
      <p>
        LexiShift helps you practice vocabulary while browsing the web. Install
        the app, create a profile, start Vocabulary Practice, and let the
        browser extension show learning words in real pages.
      </p>
      <p>
        This is a friendly handbook for the beta. It follows the path most
        testers should try first, then puts custom word lists and advanced
        options later.
      </p>
      <div class="guide-hero__actions">
        <a class="guide-button guide-button--primary" href="{{ '/download/' | relative_url }}">Download LexiShift</a>
        <a class="guide-button" href="{{ '/tester-notes/' | relative_url }}">Beta Tester Notes</a>
      </div>
    </header>

    <section id="install" class="guide-section" data-guide-section>
      <span id="chapter-1" class="guide-anchor-compat" aria-hidden="true"></span>
      <span id="chapter-2" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>1. Install LexiShift</h2>
      <p>
        Start from the download page or the private beta link you were given.
        Install the 0.1.1 desktop app first, then install the matching unlisted
        Chrome extension from your invitation after Store approval. The macOS
        beta is still unsigned, so the operating system may ask for one extra
        confirmation the first time you open it.
      </p>
      <div class="guide-card-grid">
        <div class="guide-card">
          <strong>macOS</strong>
          <span>Download LexiShift 0.1.1, open the DMG, move LexiShift into Applications if prompted, then open it from Applications.</span>
        </div>
        <div class="guide-card">
          <strong>Windows</strong>
          <span>A Windows installer is not published in this family-and-friends beta yet.</span>
        </div>
      </div>
      <div class="guide-callout">
        <p>
          <strong>macOS privacy note:</strong> if macOS says LexiShift cannot be
          verified, Control-click the app and choose Open. If that option does
          not appear, open System Settings -> Privacy &amp; Security and use the
          allow/open option near the bottom of the page.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for install flow">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Install Flow</p>
        <p class="guide-screenshot__note">This slot will show macOS and Windows first-open prompts.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch01-install-flow.png</code></p>
      </div>
    </section>

    <section id="profile" class="guide-section" data-guide-section>
      <span id="chapter-3" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>2. Create Your Profile</h2>
      <p>
        The first thing LexiShift asks for is a profile. A profile is just your
        space for one language goal, such as English -> Spanish practice or a
        separate experiment for German.
      </p>
      <div class="guide-step-grid">
        <div class="guide-step">
          <strong>1</strong>
          <span>Open LexiShift and choose Create New Profile.</span>
        </div>
        <div class="guide-step">
          <strong>2</strong>
          <span>Name the profile after the language or goal you want to try.</span>
        </div>
        <div class="guide-step">
          <strong>3</strong>
          <span>Keep the profile selected when you open the browser extension options.</span>
        </div>
      </div>
      <div class="guide-callout">
        <p>
          You may still see words like ruleset in the app. For this first pass,
          think of rulesets as optional custom word lists. The main learning
          path is Vocabulary Practice.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for profile creation">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Profile Creation</p>
        <p class="guide-screenshot__note">This slot will show the first-time profile creation screen.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch02-profile-creation.png</code></p>
      </div>
    </section>

    <section id="vocabulary-practice" class="guide-section" data-guide-section>
      <span id="chapter-7" class="guide-anchor-compat" aria-hidden="true"></span>
      <span id="chapter-9" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>3. Start Vocabulary Practice</h2>
      <p>
        Vocabulary Practice is the main language-journey flow. LexiShift picks
        a focused set of learning words for your profile and language pair,
        shows them while you browse, and uses your feedback to decide what to
        show more or less often.
      </p>
      <div class="guide-card-grid">
        <div class="guide-card">
          <strong>Choose language</strong>
          <span>Pick the source and target language pair for this profile.</span>
        </div>
        <div class="guide-card">
          <strong>Choose starting pace</strong>
          <span>Start with a small active set so the browser experience feels readable.</span>
        </div>
      </div>
      <ol>
        <li>Open the Chrome extension Options page.</li>
        <li>Go to <strong>Vocabulary Practice</strong>.</li>
        <li>Choose the same profile you created in the desktop app.</li>
        <li>Use <strong>Start Vocabulary Practice</strong>.</li>
        <li>Choose your language pair, preferences, and starting pace.</li>
      </ol>
      <div class="guide-callout">
        <p>
          The current beta is still catching up UX-wise. Some language-journey
          controls may be more obvious in the extension Options page than in the
          desktop app. That is normal for now.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for Vocabulary Practice setup">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Vocabulary Practice</p>
        <p class="guide-screenshot__note">This slot will show the Vocabulary Practice setup flow in extension options.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch03-vocabulary-practice.png</code></p>
      </div>
    </section>

    <section id="browser-extension" class="guide-section" data-guide-section>
      <span id="chapter-5" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>4. Connect the Browser Extension</h2>
      <p>
        The desktop app manages local data. The browser extension is where
        LexiShift actually changes words while you browse.
      </p>
      <ol>
        <li>Install the unlisted LexiShift Chrome extension from the Store link in your invitation after review is complete.</li>
        <li>Open the desktop app and use its Chrome browser-connection action if the helper is not connected yet.</li>
        <li>Open the extension Options page.</li>
        <li>Choose the profile you created in the desktop app.</li>
        <li>Confirm Vocabulary Practice is enabled for the language pair you want to test.</li>
      </ol>
      <div class="guide-check-grid">
        <div class="guide-check">
          <strong>Same profile</strong>
          <span>If the desktop app and extension use different profiles, replacements may not appear.</span>
        </div>
        <div class="guide-check">
          <strong>Helper connected</strong>
          <span>If the extension asks for the helper, open the desktop app and use the helper install/connect action.</span>
        </div>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for extension profile setup">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Browser Extension</p>
        <p class="guide-screenshot__note">This slot will show extension options with the selected profile and Vocabulary Practice status.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch04-browser-extension.png</code></p>
      </div>
    </section>

    <section id="browse-feedback" class="guide-section" data-guide-section>
      <h2>5. Browse and Give Feedback</h2>
      <p>
        This is the payoff: open a normal webpage and read naturally. LexiShift
        should replace selected words from your active learning set.
      </p>
      <div class="guide-step-grid">
        <div class="guide-step">
          <strong>1</strong>
          <span>Open a real page you would normally read.</span>
        </div>
        <div class="guide-step">
          <strong>2</strong>
          <span>Look for highlighted or replaced learning words.</span>
        </div>
        <div class="guide-step">
          <strong>3</strong>
          <span>Use feedback controls when a word feels easy, hard, or unfamiliar.</span>
        </div>
      </div>
      <p>
        You do not need to optimize this on day one. The useful beta signal is
        whether the replacements appear, feel readable, and make you want to
        keep browsing.
      </p>
      <div class="guide-callout">
        <p>
          If you need to separate extension setup from the full story flow, use
          the <a href="{{ '/test-sets/' | relative_url }}">five-word test-set tool</a>.
          It verifies manual replacement behavior without requiring the helper;
          LR stories and Vocabulary Practice remain the intended experience.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for browsing feedback">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Browsing Feedback</p>
        <p class="guide-screenshot__note">This slot will show a normal web page with a replacement and feedback controls.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch05-browse-feedback.png</code></p>
      </div>
    </section>

    <section id="custom-words" class="guide-section" data-guide-section>
      <span id="chapter-4" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>6. Optional: Add Your Own Words</h2>
      <p>
        Custom words are useful when you want direct control: names, hobby
        vocabulary, words from a class, or a few examples you want to test by
        hand.
      </p>
      <ul>
        <li>Add one common word or short phrase.</li>
        <li>Choose the replacement you want to see while browsing.</li>
        <li>Save before testing in the browser extension.</li>
        <li>Keep the first list small so it is easy to tell what changed.</li>
      </ul>
      <div class="guide-callout">
        <p>
          Custom word lists are not the main language-journey flow. Treat them
          as a fun power-user path after Vocabulary Practice is working.
        </p>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for custom words">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Custom Words</p>
        <p class="guide-screenshot__note">This slot will show one simple custom replacement.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch06-custom-words.png</code></p>
      </div>
    </section>

    <section id="save-share" class="guide-section" data-guide-section>
      <span id="chapter-6" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>7. Save, Export, and Share</h2>
      <p>
        LexiShift is local-first. Your profiles, custom word lists, and study
        state live on your machine unless you export or share them.
      </p>
      <div class="guide-check-grid">
        <div class="guide-check">
          <strong>Save often</strong>
          <span>Save after changing custom words or profile settings.</span>
        </div>
        <div class="guide-check">
          <strong>Export before big changes</strong>
          <span>Keep a dated backup before imports, bulk changes, or beta experiments.</span>
        </div>
        <div class="guide-check">
          <strong>Share carefully</strong>
          <span>Only share exports with people you intend to give that profile or word list to.</span>
        </div>
        <div class="guide-check">
          <strong>Keep beta notes separate</strong>
          <span>Use the short tester notes for informal family testing.</span>
        </div>
      </div>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for export and sharing">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Export and Share</p>
        <p class="guide-screenshot__note">This slot will show export actions for profiles and word lists.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch07-export-share.png</code></p>
      </div>
    </section>

    <section id="chat-setup" class="guide-section" data-guide-section>
      <span id="chapter-8" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>8. Optional: Chat Setup</h2>
      <p>
        If you use Discord with BetterDiscord, LexiShift can also apply
        replacements in chat-style reading. This is optional and should come
        after the browser flow works.
      </p>
      <ul>
        <li>Use the same profile or exported word lists where possible.</li>
        <li>Keep browser and chat behavior aligned if you want a consistent experience.</li>
        <li>Adjust highlights so messages stay readable.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for BetterDiscord plugin settings">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Chat Setup</p>
        <p class="guide-screenshot__note">This slot will show plugin settings and a simple replacement in a message.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch08-betterdiscord-plugin.png</code></p>
      </div>
    </section>

    <section id="troubleshooting" class="guide-section" data-guide-section>
      <span id="chapter-10" class="guide-anchor-compat" aria-hidden="true"></span>
      <h2>9. Troubleshooting and FAQ</h2>
      <div class="guide-check-grid">
        <div class="guide-check">
          <strong>The app will not open</strong>
          <span>On unsigned beta builds, use the macOS or Windows allow/open steps in the install section.</span>
        </div>
        <div class="guide-check">
          <strong>No replacements appear</strong>
          <span>Make sure the extension is enabled, the right profile is selected, and Vocabulary Practice is active.</span>
        </div>
        <div class="guide-check">
          <strong>The helper is disconnected</strong>
          <span>Open the desktop app, use its Chrome browser-connection action, then reopen or reload extension Options.</span>
        </div>
        <div class="guide-check">
          <strong>Practice setup is blocked</strong>
          <span>Install the required language data when the setup flow asks for it, then try again.</span>
        </div>
        <div class="guide-check">
          <strong>Custom words do not show up</strong>
          <span>Save the custom list, then confirm the extension is using the profile that contains it.</span>
        </div>
      </div>
      <h3>Guide URLs and Help Buttons</h3>
      <ul>
        <li>Preferred guide URL: <code>https://lexishift.app/guide/</code>.</li>
        <li>Old getting-started URL: <code>https://lexishift.app/getting-started/</code> redirects here.</li>
        <li>Useful section anchors: <code>#install</code>, <code>#profile</code>, <code>#vocabulary-practice</code>, <code>#browser-extension</code>, and <code>#troubleshooting</code>.</li>
        <li>Repository fallback: <code>docs/guide/README.md</code>.</li>
      </ul>
      <div class="guide-screenshot" role="img" aria-label="Screenshot placeholder for troubleshooting">
        <p class="guide-screenshot__label">Screenshot Coming Soon: Troubleshooting</p>
        <p class="guide-screenshot__note">This slot will show the most useful helper connection and practice setup checks.</p>
        <p class="guide-screenshot__filename">Suggested file: <code>images/ch09-troubleshooting.png</code></p>
      </div>
    </section>
  </article>
</div>

<script src="{{ '/assets/js/guide-nav.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/guide-theme.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/guide-locale.js' | relative_url }}" defer></script>
