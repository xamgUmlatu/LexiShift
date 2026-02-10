# Chrome Extension Structure

This extension is organized by runtime concern so content, shared runtime logic, and options UI stay isolated.

## Folders

- `_locales/`: i18n message catalogs.
- `content/`: content-script runtime modules.
  - `processing/`: tokenizer, matcher, replacement pipeline.
  - `runtime/`: content-script runtime controllers.
    - `dom_scan_runtime.js`: scan/observer lifecycle and page-budget tracking.
    - `rules/helper_rules_runtime.js`: helper rules fetch/cache/fallback resolution.
    - `rules/active_rules_runtime.js`: active-rule resolution (local + helper merge and SRS gate selection).
    - `diagnostics/apply_diagnostics_reporter.js`: structured settings-apply diagnostics/reporting.
    - `feedback/feedback_runtime_controller.js`: feedback persistence + helper sync bridge.
    - `settings_change_router.js`: routes `chrome.storage.onChanged` to targeted runtime updates.
  - `ui/`: popup and in-page UI behavior.
    - `popup_modules/`: attachable popup module renderers (e.g., Japanese scripts).
- `shared/`: cross-context runtime helpers loaded by content/options.
  - `language/`: language preferences and lemmatization helpers.
  - `settings/`: default settings and schema defaults used in runtime.
  - `helper/`: helper/native transport and helper cache sync.
  - `srs/`: SRS runtime modules (selector/store/feedback/gate/metrics).
  - `profile/`: profile-scoped media/background support.
- `options/`: options page controllers and submodules.
  - `core/`: options-page services/managers (settings, helper, rules, UI, localization).
    - `settings/`: `SettingsManager` domain installers (base/language/ui prefs/srs/signals).
  - `controllers/`: options feature domains.
    - `page/events/`: event binder composition (`general/`, `srs`, `profile_background`).
    - `profile/background/`: profile background render/prefs/runtime bridge helpers.
    - `srs/`: SRS actions and profile runtime wiring.
  - `vendor/`: options-page vendor codecs/helpers.
- `legacy/`: archived notes/prototypes not used in runtime.

## Runtime Entry Points

- `manifest.json`: content script loading order and web-accessible resources.
- `content_script.js`: content runtime orchestrator.
- `options.html` + `options.js`: options UI composition root.
