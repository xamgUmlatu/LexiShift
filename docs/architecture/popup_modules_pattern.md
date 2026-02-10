# Popup Modules Pattern (Architecture + Extension Plan)

Purpose:
- Define a stable popup-modules architecture for LexiShift replacement interactions.
- Keep UX consistent while allowing feature growth.
- Establish a clean path to a future public module API so users/developers can plug in their own popup modules.

Scope:
- Current Chrome extension popup behavior (`apps/chrome-extension/content/ui/feedback_popup_controller.js` + `apps/chrome-extension/content/ui/ui.js`).
- Core examples:
  - Japanese script module (shows non-primary scripts).
  - Word feedback module (Again/Hard/Good/Easy).
- Future extensibility contract for third-party modules.

## 1) Why This Pattern Exists

LexiShift replacements are compact inline UI elements in arbitrary webpages. The popup is where we can attach richer contextual information without cluttering the page.

Design goals:
- Fast, low-friction interaction.
- Progressive disclosure: deeper info only when requested.
- Language-aware UI (different modules by language and data availability).
- Stable interaction affordance users can learn once.

Current user action model:
- Click replacement: toggle replacement/original.
- Context menu on replacement: open popup for details + feedback.

## 2) Current Runtime Structure (Implemented Today)

Primary implementation:
- `apps/chrome-extension/content/ui/feedback_popup_controller.js`
- `apps/chrome-extension/content/ui/popup_modules/japanese_script_module.js`
- `apps/chrome-extension/content/ui/ui.js` (composition + bridge)

Data source for popup context:
- Replacement span dataset written by replacement pipeline in:
  - `apps/chrome-extension/content/processing/replacements.js`
  - `apps/chrome-extension/content_script.js` (origin tagging, SRS/ruleset flow)

Popup composition today:
- One popup container: `.lexishift-feedback-popup`
- One modules stack container: `.lexishift-feedback-modules`
- One fixed feedback bar container: `.lexishift-feedback-bar`

Layout contract today:
- Dynamic modules render in the modules stack.
- Feedback bar is always attached at the bottom.

Interaction flow today:
1. User opens context menu on `.lexishift-replacement`.
2. `attachFeedbackListener(...)` validates origin gating and opens popup.
3. `openFeedbackPopup(target)` calls `renderFeedbackModules(target)`.
4. `renderFeedbackModules` currently attempts Japanese script module.
5. Popup is positioned near the anchor span and animated open.
6. User clicks feedback rating or dismisses popup.

## 3) Module Concepts

Terminology:
- Popup: the full floating container (`modules stack + feedback bar`).
- Module: a self-contained visual/info block rendered inside the modules stack.
- Anchor target: the clicked replacement span.
- Context: parsed data derived from the anchor target and runtime settings.

Module requirements:
- Pure render from context (no global side effects during render).
- Graceful no-op when prerequisites are missing.
- Small footprint and predictable height.
- Safe fallback when malformed payload is encountered.

## 4) Core Example A: Japanese Script Module

Current behavior:
- Implemented in `build(target, debugLog)` in `apps/chrome-extension/content/ui/popup_modules/japanese_script_module.js`.
- Reads `target.dataset.scriptForms` JSON payload.
- Determines primary script from `target.dataset.displayScript`.
- Renders only non-primary script rows.
- Requires at least 2 available script forms to render.

Expected payload on replacement span:
- `data-script-forms` (serialized into `dataset.scriptForms`): object with optional keys:
  - `kanji`
  - `kana`
  - `romaji`
- `data-display-script` (serialized into `dataset.displayScript`): active primary display script.

Example value flow:
- If primary display script is `kanji`, module shows `kana` and `romaji` if available.
- If primary display script is `kana`, module shows `kanji` and `romaji` if available.

Why this is a good module:
- High-value contextual info.
- Language-specific and optional.
- Works cleanly with progressive disclosure.

## 5) Core Example B: Word Feedback Module

Current behavior:
- Implemented as feedback bar in `ensureFeedbackPopup()` in `apps/chrome-extension/content/ui/feedback_popup_controller.js`.
- Contains rating buttons:
  - `again` (1)
  - `hard` (2)
  - `good` (3)
  - `easy` (4)
- Selection triggers `handleFeedbackSelection(...)`.
- Feedback routes to SRS/telemetry path via content-script handler and shared feedback utilities.

Relevant files:
- `apps/chrome-extension/content/ui/feedback_popup_controller.js`
- `apps/chrome-extension/content/ui/popup_modules/japanese_script_module.js`
- `apps/chrome-extension/content/ui/ui.js`
- `apps/chrome-extension/content_script.js` (feedback handling, gating by origin)
- `apps/chrome-extension/shared/srs/srs_feedback.js`

Why this is a good core module:
- Universal and action-oriented.
- Lightweight but high impact.
- Anchors the popup as an SRS interaction primitive.

## 6) Data Contract For Popup Modules

Popup modules should rely on a stable context object, not ad hoc DOM reads throughout module code.

Recommended context shape:
```js
{
  target, // HTMLElement .lexishift-replacement
  origin, // "srs" | "ruleset"
  languagePair, // e.g. "en-ja"
  sourceLanguage, // optional resolved form
  targetLanguage, // optional resolved form
  replacement, // canonical replacement
  displayReplacement, // rendered text on page
  displayScript, // "kanji" | "kana" | "romaji" | ""
  scriptForms, // normalized object or null
  settings: {
    targetDisplayScript,
    srsFeedbackSrsEnabled,
    srsFeedbackRulesEnabled
  }
}
```

Span metadata conventions (current):
- `dataset.origin`
- `dataset.replacement`
- `dataset.displayReplacement`
- `dataset.displayScript`
- `dataset.scriptForms`
- `dataset.languagePair`
- `dataset.source`
- `dataset.original`

## 7) UX Contract For Popup Composition

Global UX invariants:
- Modules stack appears above the feedback bar.
- Feedback bar remains present and bottom-aligned.
- Popup opens near anchor and clamps to viewport bounds.
- Popup closes on outside click, scroll, resize, or `Escape`.

Future module UX rules:
- Modules should not hijack close behavior.
- Modules should avoid nested scroll containers unless content is large.
- Module visual density should match existing popup token sizes.

## 8) Future Public Module API (Target)

This section defines a practical path to external modules without destabilizing core UX.

### 8.1 Registry Contract

```js
registerPopupModule({
  id: "module-id",
  version: "1.0.0",
  priority: 100,
  supports(context) {
    return true; // or conditional
  },
  render(context, api) {
    // return HTMLElement or null
  },
  onOpen(context, api) {},
  onClose(context, api) {}
});
```

Registry behavior:
- Modules sorted by priority ascending.
- `supports` called before `render`.
- `render` exceptions are isolated so one module cannot break popup.
- Module output is appended in order to modules stack.

### 8.2 API Surface Exposed To Modules

Recommended minimal `api`:
- `api.createModuleContainer(className?)`
- `api.createRow(label, value)`
- `api.t(key, substitutions, fallback)` for localization
- `api.log(...)` (debug-gated)
- `api.emit(eventName, payload)` (optional event bus)

Non-goals for public API:
- Direct DOM access to popup root internals.
- Direct mutation of storage without permission checks.
- Arbitrary network calls without explicit permission model.

### 8.3 Module Isolation

Phase 1 (internal modules):
- Same runtime context as today.
- Internal registry only.

Phase 2 (signed or trusted local modules):
- Manifest-based load.
- Capability flags per module.

Phase 3 (public ecosystem):
- Stable versioned API.
- Compatibility checks.
- Module sandboxing policy (if needed by threat model).

## 9) Settings And User Selection Model (Target)

Target configuration model:
- Global enable/disable for popup modules.
- Per-language module toggles.
- Per-module priority overrides (optional advanced setting).
- Per-profile module settings (where useful).

Example settings shape:
```json
{
  "popupModules": {
    "enabled": true,
    "order": ["ja-script-forms", "feedback-core"],
    "byLanguage": {
      "ja": ["ja-script-forms", "feedback-core"],
      "default": ["feedback-core"]
    },
    "moduleConfig": {
      "ja-script-forms": { "enabled": true },
      "feedback-core": { "enabled": true }
    }
  }
}
```

## 10) Module Ideas Catalog (Learning-Word Focus)

The following are candidate popup modules for a clicked target learning word. These are intended to be optional modules that can be enabled/disabled in settings over time.

1. `quick-definition`
- Short gloss plus a plain explanation.

2. `example-sentence`
- One native example sentence with translation.

3. `collocations`
- Common word pairings and phrase partners.

4. `pos-grammar`
- Part of speech and key inflection/grammar notes.

5. `word-family`
- Related derivations and nearby forms.

6. `pronunciation`
- Audio playback and phonetic reading.

7. `jp-pitch-accent`
- Japanese pitch-accent pattern.

8. `jp-kanji-detail`
- Kanji readings, components, and stroke metadata.

9. `confusables`
- Similar-looking/similar-meaning words to disambiguate.

10. `frequency-usefulness`
- Frequency rank and practical usefulness signal.

11. `srs-state`
- Current stage, stability trend, and lapses.

12. `next-review`
- Next due time and queue context.

13. `personal-notes`
- User-authored mnemonics and notes.

14. `seen-history`
- Recent pages/contexts where this word appeared.

15. `synonyms-antonyms`
- Semantic neighborhood for meaning contrast.

16. `register-tone`
- Formality/register markers (casual, formal, slang, business).

17. `quick-actions`
- Suspend, prioritize, mark known, or pin to focus list.

18. `mini-recall-test`
- One-tap micro quiz (cloze or multiple choice).

Suggested first optional rollout:
- `quick-definition`
- `example-sentence`
- `srs-state`
- `next-review`
- `quick-actions`

## 11) Localization, Accessibility, And Performance

Localization:
- Module text should use extension i18n keys, not hardcoded strings.
- Dynamic runtime text should be re-rendered on locale change.

Accessibility:
- Popup root should preserve dialog semantics where appropriate.
- Module rows should maintain clear text contrast and readable labels.
- Keyboard interaction should remain consistent with popup close/feedback controls.

Performance:
- Module render should be O(1) to small O(n) over tiny payloads.
- Avoid blocking operations in `render`.
- Prefer pre-normalized context to repeated parsing.

## 12) Error Handling And Diagnostics

Rules:
- Parsing failures in a module should fail closed (module omitted).
- Log debug details only when debug mode is enabled.
- Popup core must still open even if optional modules fail.

Current diagnostics pattern:
- `debugLog(...)` in `apps/chrome-extension/content/ui/feedback_popup_controller.js`
- Focused logs for script-form parse failures and gating decisions.

## 13) Testing Strategy

Unit-level targets:
- `parseScriptForms` normalization.
- Primary-script resolution.
- Module gating behavior for incomplete payloads.

Integration-level targets:
- Contextmenu opens popup with expected module order.
- Feedback bar remains functional with and without optional modules.
- Origin gating (`srs` vs `ruleset`) remains correct.

Regression targets:
- SRS color and rule-based color remain independent.
- Popup module failures do not block feedback interactions.

## 14) Implementation Roadmap

Step 1:
- Extract current module render into internal registry abstraction.
- Keep existing visual output unchanged.

Step 2:
- Introduce normalized popup context builder.
- Route all modules through context object.

Step 3:
- Add internal module IDs and priorities.
- Migrate script module + feedback module to registry entries.

Step 4:
- Add options UI for enabling/disabling modules by language.

Step 5:
- Stabilize and version a public plugin API.

## 15) Non-Negotiable Invariants

- Feedback module stays core and cannot be removed by third-party modules unless explicitly allowed by product policy.
- Popup open/close lifecycle remains owned by core UI runtime.
- Module failures are isolated and non-fatal.
- Storage and network operations remain capability-gated.

---

This document is the contract for evolving popup modules from the current internal implementation to a robust extensible platform, while preserving fast interaction quality for core SRS usage.
