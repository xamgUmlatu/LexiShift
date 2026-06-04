---
layout: default
title: LexiShift
---

<!--
Status: active Pages entrypoint
Role: Public landing page
Last updated: 2026-06-05
Last verified: 2026-06-05 landing-page Jekyll build, repo checks, desktop/mobile previews, and generated visual mocks
Purpose: present LexiShift as the public beta front door and route visitors to downloads, extension status, setup, support, privacy, and release pages
Source-of-truth: Pages navigation entrypoint only; implementation truth remains in source code, canonical developer docs, architecture docs, and feature-state evidence.
-->

<div class="landing-page">
  <section class="landing-hero" aria-labelledby="landing-title">
    <div class="landing-hero__scene" aria-hidden="true" data-landing-mock-root>
      <div class="landing-scene__grid"></div>
      <div class="landing-scene__browser">
        <div class="landing-scene__bar">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="landing-scene__body">
          <p class="landing-scene__label" data-landing-mock-label>Spanish reading view</p>
          <div class="landing-scene__line landing-scene__line--long"></div>
          <div class="landing-scene__line"></div>
          <div class="landing-scene__translation">
            <span data-landing-mock-source>apple</span>
            <b aria-hidden="true">-&gt;</b>
            <strong data-landing-mock-target>manzana</strong>
          </div>
          <div class="landing-scene__sentence" data-landing-mock-sentence>
            Do we need <span>manzana</span> for the recipe?
          </div>
          <div class="landing-scene__line landing-scene__line--mid"></div>
          <div class="landing-scene__feedback" data-landing-mock-feedback>
            <strong>manzana</strong>
            <em>apple</em>
            <span>Again</span>
            <span>Hard</span>
            <span>Good</span>
            <span>Easy</span>
          </div>
        </div>
      </div>
      <div class="landing-scene__app">
        <p>Desktop authoring</p>
        <div>
          <span>Profile</span>
          <strong data-landing-mock-profile>Reading beta</strong>
        </div>
        <div>
          <span>Ruleset</span>
          <strong data-landing-mock-ruleset>en-es review</strong>
        </div>
        <div>
          <span>Runtime</span>
          <strong data-landing-mock-runtime>Local helper</strong>
        </div>
      </div>
    </div>

    <div class="landing-hero__inner">
      <div class="landing-brand-lockup">
        <img src="{{ '/assets/images/lexishift-icon128.png' | relative_url }}" alt="" class="landing-brand-lockup__icon">
        <span>LexiShift beta</span>
      </div>
      <h1 id="landing-title">LexiShift</h1>
      <p class="landing-hero__tagline">Language practice woven into the pages you already read.</p>
      <p class="landing-hero__lede">
        LexiShift pairs a local-first desktop app with browser and community runtime
        surfaces, so vocabulary replacement, review feedback, and setup stay under
        your control while the beta matures.
      </p>
      <div class="landing-actions" aria-label="Primary LexiShift actions">
        <a class="landing-button landing-button--primary" href="{{ '/download/' | relative_url }}">Download Beta App</a>
        <a class="landing-button" href="#runtime-links">Chrome Extension</a>
        <a class="landing-button landing-button--quiet" href="{{ '/getting-started/' | relative_url }}">Setup Guide</a>
      </div>
      <p class="landing-hero__note">
        First installer links are preparing. The download page will carry the
        versioned app files, checksums, signing status, and release notes.
      </p>
    </div>
  </section>

  <section class="landing-status-band" aria-label="Current beta status">
    <div class="landing-status-band__inner">
      <article>
        <span>Desktop app</span>
        <strong>macOS first beta lane</strong>
      </article>
      <article>
        <span>Downloads</span>
        <strong>Versioned installers planned</strong>
      </article>
      <article>
        <span>Runtime</span>
        <strong>Chrome extension plus local helper</strong>
      </article>
      <article>
        <span>Data posture</span>
        <strong>Local-first, distribution-aware</strong>
      </article>
    </div>
  </section>

  <section class="landing-section landing-section--workflow">
    <div class="landing-section__inner">
      <div class="landing-section__header">
        <p class="landing-kicker">How it works</p>
        <h2>Author once, practice wherever the runtime is allowed.</h2>
      </div>
      <div class="landing-feature-grid">
        <article class="landing-feature">
          <span class="landing-feature__index">01</span>
          <h3>Build a local profile</h3>
          <p>
            Create profiles, rulesets, and language-pair resources in the desktop
            app before sending anything into a runtime surface.
          </p>
        </article>
        <article class="landing-feature">
          <span class="landing-feature__index">02</span>
          <h3>Read with replacements</h3>
          <p>
            The extension applies active rules on web pages and keeps the helper
            bridge explicit, inspectable, and local to your machine.
          </p>
        </article>
        <article class="landing-feature">
          <span class="landing-feature__index">03</span>
          <h3>Review from real context</h3>
          <p>
            Feedback and SRS signals come from actual reading sessions, not a
            detached flashcard-only workflow.
          </p>
        </article>
      </div>
    </div>
  </section>

  <section class="landing-section landing-section--install" id="runtime-links">
    <div class="landing-section__inner">
      <div class="landing-section__header">
        <p class="landing-kicker">Beta access</p>
        <h2>Install paths stay separate on purpose.</h2>
        <p>
          The desktop app, Chrome extension, and optional community plugin have
          different distribution rules. This page routes each one without hiding
          the current beta status.
        </p>
      </div>
      <div class="landing-install-grid">
        <article class="landing-install-card landing-install-card--primary">
          <span class="landing-badge">Preparing</span>
          <h3>Desktop App</h3>
          <p>
            The app download page is the canonical place for beta installers,
            checksums, signing status, and release notes.
          </p>
          <a href="{{ '/download/' | relative_url }}">Open download page</a>
        </article>
        <article class="landing-install-card">
          <span class="landing-badge">Extension</span>
          <h3>Chrome Extension</h3>
          <p>
            The normal install path should become a Chrome Web Store beta or
            unlisted tester link. The repository path remains useful for status
            and implementation review.
          </p>
          <a href="https://github.com/xamgUmlatu/LexiShift/tree/main/apps/chrome-extension">View extension status</a>
        </article>
      </div>
    </div>
  </section>

  <section class="landing-section landing-section--details">
    <div class="landing-section__inner landing-detail-layout">
      <div>
        <p class="landing-kicker">Beta promise</p>
        <h2>Pretty, but still honest about what is ready.</h2>
        <p>
          This site should make LexiShift feel real without implying that every
          production concern is finished. The beta surface points testers to the
          exact install, privacy, support, and release pages they need.
        </p>
      </div>
      <div class="landing-link-stack">
        <a href="{{ '/beta/' | relative_url }}">
          <strong>Beta Overview</strong>
          <span>Tester expectations, setup boundary, and current limitations.</span>
        </a>
        <a href="{{ '/privacy/' | relative_url }}">
          <strong>Privacy Summary</strong>
          <span>Local-first behavior and what support reports may include.</span>
        </a>
        <a href="{{ '/support/' | relative_url }}">
          <strong>Support</strong>
          <span>Where to send feedback and what makes a report useful.</span>
        </a>
      </div>
    </div>
  </section>

  <section class="landing-section landing-section--integrations">
    <div class="landing-section__inner">
      <div class="landing-section__header">
        <p class="landing-kicker">Optional surfaces</p>
        <h2>Community-style integrations stay below the fold.</h2>
      </div>
      <div class="landing-integration-grid">
        <article>
          <span class="landing-badge">Primary runtime</span>
          <h3>Chrome Extension</h3>
          <p>
            Best fit for normal web reading once the beta distribution link is
            available.
          </p>
        </article>
        <article>
          <span class="landing-badge landing-badge--soft">Experimental</span>
          <h3>BetterDiscord Plugin</h3>
          <p>
            Optional for users who already run BetterDiscord and are comfortable
            with unofficial client plugins. It should not be treated as the core
            install path.
          </p>
          <a href="https://github.com/xamgUmlatu/LexiShift/tree/main/apps/betterdiscord-plugin">View plugin README</a>
        </article>
      </div>
    </div>
  </section>

  <section class="landing-footer-band">
    <div class="landing-footer-band__inner">
      <div>
        <strong>Need the repo docs?</strong>
        <span>Developer and handbook material stays available, but it is no longer the first impression.</span>
      </div>
      <nav aria-label="Repository documentation links">
        <a href="{{ '/handbook/' | relative_url }}">Handbook</a>
        <a href="{{ '/releases/' | relative_url }}">Releases</a>
        <a href="https://github.com/xamgUmlatu/LexiShift/blob/main/docs/README.md">Docs tree</a>
      </nav>
    </div>
  </section>
</div>

<script src="{{ '/assets/js/landing-visual-mocks.js' | relative_url }}" defer></script>
