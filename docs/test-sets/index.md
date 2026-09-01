---
layout: default
title: Language-pair test sets
permalink: /test-sets/
---

<!--
Status: active public test fixture
Role: Generate small import-ready rulesets and matching reading samples for supported language pairs
Last updated: 2026-09-02
Purpose: provide a deterministic extension-review path without presenting manual rules as the primary LexiShift workflow
-->

<div class="test-set-page">
  <header class="test-set-hero" data-lexishift-scan-skip="true">
    <a class="test-set-brand" href="{{ '/' | relative_url }}" aria-label="LexiShift home">
      <img src="{{ '/assets/images/lexishift-icon128.png' | relative_url }}" alt="">
      <span>LexiShift</span>
    </a>
    <div class="test-set-hero__copy">
      <p class="test-set-kicker">Tiny tools · real browser test</p>
      <h1>Pick a pair. Try a shift.</h1>
      <p>
        Make a five-word ruleset, import it into the extension, and use the
        matching sample below to see the result immediately.
      </p>
    </div>
    <p class="test-set-purpose-note">
      <strong>This is a test fixture.</strong>
      LexiShift’s normal beta experience centers on LR stories and vocabulary
      practice from the desktop app.
    </p>
  </header>

  <main class="test-set-workspace">
    <section class="test-set-builder" aria-labelledby="test-set-builder-title" data-lexishift-scan-skip="true">
      <div class="test-set-section-heading">
        <span class="test-set-step">01</span>
        <div>
          <p class="test-set-eyebrow">Language pair</p>
          <h2 id="test-set-builder-title">Choose what changes</h2>
        </div>
      </div>

      <div class="test-set-language-grid">
        <label class="test-set-language-card">
          <span>Source language</span>
          <select data-test-set-source aria-label="Source language"></select>
          <small>The language in the sample text</small>
        </label>

        <div class="test-set-pair-mark" aria-label="Selected language pair">
          <strong data-test-set-pair-source>EN</strong>
          <span aria-hidden="true">→</span>
          <strong data-test-set-pair-target>JA</strong>
        </div>

        <label class="test-set-language-card">
          <span>Target language</span>
          <select data-test-set-target aria-label="Target language"></select>
          <small>The words LexiShift introduces</small>
        </label>
      </div>

      <div class="test-set-rule-card">
        <div class="test-set-rule-card__heading">
          <div>
            <p class="test-set-eyebrow">Generated set</p>
            <h3 data-test-set-pair-label>English → 日本語</h3>
          </div>
          <span class="test-set-count">5 words</span>
        </div>
        <ul class="test-set-rules" data-test-set-rules aria-label="Generated replacement rules"></ul>
        <div class="test-set-actions">
          <button class="test-set-button test-set-button--primary" type="button" data-test-set-download>
            Download ruleset
          </button>
          <button class="test-set-button" type="button" data-test-set-copy-json>
            Copy JSON
          </button>
        </div>
        <p class="test-set-filename">File: <code data-test-set-filename></code></p>
      </div>
    </section>

    <section class="test-set-sample-card" aria-labelledby="test-set-sample-title">
      <div class="test-set-sample-card__heading" data-lexishift-scan-skip="true">
        <div class="test-set-section-heading">
          <span class="test-set-step">02</span>
          <div>
            <p class="test-set-eyebrow">Reading surface</p>
            <h2 id="test-set-sample-title">Reload, then read</h2>
          </div>
        </div>
        <div class="test-set-sample-actions">
          <span class="test-set-mode" data-test-set-mode>Native-script sample</span>
          <button class="test-set-text-button" type="button" data-test-set-copy-sample>Copy sample</button>
        </div>
      </div>
      <article class="test-set-reading-copy" lang="en">
        <p data-test-set-sample></p>
      </article>
      <p class="test-set-romanization-note" data-lexishift-scan-skip="true">
        Japanese and Chinese source samples use plain romanization so this compact
        fixture tests today’s browser matcher without pretending to validate
        native-script segmentation.
      </p>
    </section>

    <section class="test-set-instructions" aria-labelledby="test-set-instructions-title" data-lexishift-scan-skip="true">
      <div class="test-set-section-heading">
        <span class="test-set-step">03</span>
        <div>
          <p class="test-set-eyebrow">Extension check</p>
          <h2 id="test-set-instructions-title">Three quick moves</h2>
        </div>
      </div>
      <ol>
        <li><strong>Download</strong> the generated JSON file.</li>
        <li><strong>Open LexiShift Options</strong>, then import the file from Share Center.</li>
        <li><strong>Return here and reload.</strong> The five words above become clickable replacements.</li>
      </ol>
      <p>
        No account or desktop helper is required for this small manual test.
        Dictionary and story-powered experiences may use the local desktop app.
      </p>
    </section>

    <details class="test-set-json-card" data-lexishift-scan-skip="true">
      <summary>Inspect the generated JSON</summary>
      <textarea data-test-set-json readonly spellcheck="false" aria-label="Generated ruleset JSON"></textarea>
    </details>

    <p class="test-set-status" data-test-set-status data-tone="quiet" role="status" aria-live="polite" data-lexishift-scan-skip="true">
      Test set ready.
    </p>
  </main>
</div>

<script src="{{ '/assets/js/test-set-picker.js' | relative_url }}" defer></script>
