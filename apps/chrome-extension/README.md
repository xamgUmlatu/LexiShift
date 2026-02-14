# Chrome Extension Structure

Purpose:
- Document the extension runtime architecture and current user-facing feature set.
- Provide a fast map for where to implement changes.

## Runtime Entry Points

- `manifest.json`
  - Declares permissions, background service worker, and ordered content script modules.
- `content_script.js`
  - Content runtime orchestrator (settings apply, active rules resolution, DOM scan, observer lifecycle).
- `background.js`
  - Native helper bridge endpoint for extension-helper communication.
- `options.html` + `options.js`
  - Options app shell + composition root.

## Folder Map

- `_locales/`
  - Extension message catalogs.
- `content/`
  - Webpage runtime modules.
  - `processing/`: tokenizer/matcher/replacements.
  - `runtime/`: scan/runtime/rules/feedback/diagnostics orchestration.
  - `ui/`: replacement UI behavior and popup modules.
- `shared/`
  - Cross-context runtime helpers.
  - `language/`: language preference helpers and lemmatizer.
  - `settings/`: default settings.
  - `helper/`: helper transport/client/cache/feedback-sync.
  - `srs/`: SRS runtime selector/store/feedback/gate/metrics.
  - `profile/`: profile media storage utilities.
- `options/`
  - Options app services and controllers.
  - `core/`: managers and bootstrap composition.
  - `controllers/`: domain behavior (page/srs/profile/helper/rules/ui).
  - `vendor/`: codecs and bundled helpers.

## Current Extension Features

- Replacement runtime
  - Longest-match phrase replacement with highlight and click-to-toggle behavior.
  - Supports morphology-aware display surfaces via rule metadata (`metadata.morphology.target_surface`) while keeping canonical replacement lemma identity for SRS keys.
  - Runtime replacement controls:
    - `maxOnePerTextBlock`
    - `allowAdjacentReplacements`
    - `maxReplacementsPerPage`
    - `maxReplacementsPerLemmaPerPage`
  - Works on all matching frames/pages and skips editable inputs/contenteditable areas.

- Rule source model
  - Uses local rules from extension storage.
  - Can merge in helper-generated rules.
  - Uses profile-scoped helper cache fallback on helper fetch failures.

- SRS features
  - SRS gate can filter active rules by replacement lemma.
  - Feedback popup on replacement spans with 4 ratings:
    - Again / Hard / Good / Easy
  - Feedback origin gating:
    - SRS words and ruleset words can be enabled independently.
  - Exposure logging and diagnostics are separate from scheduler feedback.

- Popup modules
  - Popup has module stack above a fixed feedback bar.
  - Built-in Japanese script module renders non-primary script forms when metadata is present.
  - Module rendering is registry-based (`content/ui/popup_modules/module_registry.js`).

- Profile-first options flow
  - Selected profile controls active settings view.
  - Per-profile language preferences and pair settings are stored under `srsProfiles`.
  - Per-profile UI preferences include background image settings.
  - Profile background media blobs are stored in IndexedDB (`shared/profile/profile_media_store.js`).

- Debug and diagnostics
  - Runtime diagnostics actions from options.
  - Focus-word debug tracing.
  - Helper connection/open-data-dir diagnostics.

- Localization
  - Options UI and extension strings are localized via `_locales`.

## Key Architecture References

- Extension system map:
  - `docs/architecture/extension_system_map.md`
- Extension technical details:
  - `docs/architecture/chrome_extension_technical.md`
- Options controller boundaries:
  - `docs/architecture/options_controllers_architecture.md`
- Popup module architecture:
  - `docs/architecture/popup_modules_pattern.md`

## Ownership Boundaries

- `content_script.js`
  - Orchestration and runtime lifecycle only.
- `content/runtime/*`
  - Apply pipeline, scan lifecycle, runtime actions, and settings change routing.
- `content/ui/*`
  - Rendering interactions and popup lifecycle.
- `options.js`
  - Startup/composition only; business logic belongs in controllers/services.
- `options/core/bootstrap/controller_graph.js`
  - Controller composition and cross-domain adapter wiring.
