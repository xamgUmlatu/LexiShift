# LexiShift Extension System Map

Purpose:
- Provide a single-page map of how the Chrome extension works.
- Help new contributors find the right file quickly.
- Keep boundaries clear between runtime, options UI, shared modules, and helper integration.

## 1) Entry Points

Core extension entry files:
- `apps/chrome-extension/manifest.json`
- `apps/chrome-extension/content_script.js`
- `apps/chrome-extension/background.js`
- `apps/chrome-extension/options.html`
- `apps/chrome-extension/options.js`

How they connect:
- `manifest.json` loads ordered content modules, then `content_script.js`.
- `background.js` handles helper/native messaging bridge requests.
- `options.html` loads ordered options modules, then `options.js`.

## 2) Runtime Topology (Content Script)

Primary runtime folders:
- `apps/chrome-extension/content/processing`
- `apps/chrome-extension/content/runtime`
- `apps/chrome-extension/content/ui`
- `apps/chrome-extension/shared`

High-level flow:
1. Load and normalize settings from `chrome.storage.local`.
2. Resolve active ruleset (`ruleset` + optional helper rules + optional SRS gate).
3. Build matcher/trie and scan DOM text nodes.
4. Replace matched text with `.lexishift-replacement` spans.
5. Track exposure and enable feedback popup interactions.
6. Re-apply or rescan on settings/storage/mutation events.

Core runtime modules:
- `content/runtime/apply_settings_pipeline.js`
- `content/runtime/rules/active_rules_runtime.js`
- `content/runtime/dom_scan_runtime.js`
- `content/runtime/feedback/feedback_runtime_controller.js`
- `content/runtime/settings_change_router.js`

## 3) Popup Module Runtime

Popup ownership:
- `apps/chrome-extension/content/ui/feedback_popup_controller.js`
- `apps/chrome-extension/content/ui/popup_modules/module_registry.js`

Current built-in module:
- `apps/chrome-extension/content/ui/popup_modules/japanese_script_module.js`

Contract:
- Modules render in a stack above the fixed feedback bar.
- Feedback bar remains present and bottom-attached.
- Popup lifecycle (open/close/position/fade) is controlled by core popup controller.

Reference:
- `docs/architecture/popup_modules_pattern.md`

## 4) Options App Topology

Primary folders:
- `apps/chrome-extension/options/core`
- `apps/chrome-extension/options/controllers`

Composition root:
- `apps/chrome-extension/options.js`

Controller graph builder:
- `apps/chrome-extension/options/core/bootstrap/controller_graph.js`

Controller factory guard:
- `apps/chrome-extension/options/core/bootstrap/controller_factory.js`

Design rule:
- `options.js` does composition and startup.
- Domain behavior lives in controllers and core installers.

Detailed reference:
- `docs/architecture/options_controllers_architecture.md`

## 5) Storage Map

Persistent stores:
- `chrome.storage.local`
  - extension settings/rules/runtime mirrors
  - SRS logs/stores/feedback metadata
- IndexedDB (`profile_media_store`)
  - profile background image blobs

Defaults source:
- `apps/chrome-extension/shared/settings/settings_defaults.js`

Profile-scoped settings container:
- `srsProfiles.<profile_id>.*`

## 6) Helper Integration Map

Client/transport modules:
- `apps/chrome-extension/shared/helper/helper_transport_extension.js`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/shared/helper/helper_cache.js`
- `apps/chrome-extension/shared/helper/helper_feedback_sync.js`

Who calls helper flows:
- SRS options controllers (`initialize`, `refresh`, diagnostics, sampled preview)
- Feedback sync queue runtime path

## 7) Where To Edit (By Feature)

If you are changing:
- Replacement matching logic:
  - `content/processing/tokenizer.js`
  - `content/processing/matcher.js`
  - `content/processing/replacements.js`
- DOM scan/replacement scheduling:
  - `content/runtime/dom_scan_runtime.js`
  - `content/runtime/dom_scan/*`
- Popup UX/modules:
  - `content/ui/feedback_popup_controller.js`
  - `content/ui/popup_modules/*`
- Options setting behavior:
  - `options/controllers/*`
  - `options/core/settings/*`
- SRS setting persistence/profile behavior:
  - `options/core/settings/srs_profile_methods.js`
  - `options/controllers/srs/*`

## 8) Fast Debug Paths

A word is not replaced:
1. Check extension enabled + pair settings in options.
2. Check active rules resolution in content debug logs.
3. Check node-filter skips in DOM scan runtime logs.
4. Check page/lemma replacement budgets.

Popup module not visible:
1. Confirm replacement span has expected dataset payload (`data-script-forms`, `data-display-script`, `data-origin`).
2. Confirm origin gating allows popup on that span.
3. Confirm module registry build path runs and module returns content.

Profile switch appears inconsistent:
1. Check selected profile key (`srsSelectedProfileId` / runtime mirrors).
2. Check `srsProfiles.<id>` language prefs and pair settings.
3. Check profile background runtime bridge updates.

## 9) Architecture Invariants

- Manifest and options script ordering are hard dependencies.
- Content UI modules cannot break feedback core behavior.
- Profile scoping must be preserved in SRS settings, helper cache, and media assets.
- Controller boundaries in options must stay modular (no logic bloat in `options.js`).
