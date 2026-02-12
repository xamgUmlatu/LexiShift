# Chrome Extension Structure

This extension is organized by runtime concern so content, shared runtime logic, and options UI stay isolated.

## Folders

- `_locales/`: i18n message catalogs.
- `content/`: content-script runtime modules.
  - `processing/`: tokenizer, matcher, replacement pipeline.
  - `runtime/`: content-script runtime controllers.
    - `dom_scan/`: scan internals split by concern.
      - `node_filters.js`: editable/excluded/LexiShift node guards.
      - `page_budget_tracker.js`: page-level replacement budget state and updates.
      - `scan_counters.js`: full-scan/mutation diagnostic counter builders.
      - `text_node_processor.js`: text-node replacement processing pipeline.
    - `dom_scan_runtime.js`: scan/observer lifecycle orchestration.
    - `rules/helper_rules_runtime.js`: helper rules fetch/cache/fallback resolution.
    - `rules/active_rules_runtime.js`: active-rule resolution (local + helper merge and SRS gate selection).
    - `diagnostics/apply_diagnostics_reporter.js`: structured settings-apply diagnostics/reporting.
    - `apply_runtime_actions.js`: settings-apply action runner (styles/listeners/highlight + scan execution).
    - `apply_settings_pipeline.js`: settings-apply orchestration pipeline (normalize -> rules state -> diagnostics/actions).
    - `feedback/feedback_runtime_controller.js`: feedback persistence + helper sync bridge.
    - `settings_change_router.js`: routes `chrome.storage.onChanged` to targeted runtime updates.
  - `ui/`: popup and in-page UI behavior.
    - `popup_modules/`: attachable popup module registry/renderers (e.g., Japanese scripts).
- `shared/`: cross-context runtime helpers loaded by content/options.
  - `language/`: language preferences and lemmatization helpers.
  - `settings/`: default settings and schema defaults used in runtime.
  - `helper/`: helper/native transport and helper cache sync.
  - `srs/`: SRS runtime modules (selector/store/feedback/gate/metrics).
  - `profile/`: profile-scoped media/background support.
- `options/`: options page controllers and submodules.
  - `core/`: options-page services/managers (settings, helper, rules, UI, localization).
    - `settings/`: `SettingsManager` domain installers (base/language/ui prefs/srs/signals).
    - `helper/`: `HelperManager` domain installers (base, diagnostics, SRS set operations).
    - `bootstrap/`: options-root adapters/composition (`controller_factory`, `ui_bridge`, `language_prefs_adapter`, `dom_aliases`, `controller_graph`).
  - `controllers/`: options feature domains.
    - `page/events/`: event binder composition (`general/`, `srs`, `profile_background`).
    - `profile/background/`: profile background render/prefs/runtime bridge helpers.
    - `srs/`: SRS actions and profile runtime wiring.
      - `actions/`: formatter/shared/workflow modules used by `actions_controller.js`.
  - `vendor/`: options-page vendor codecs/helpers.

## Runtime Entry Points

- `manifest.json`: content script loading order and web-accessible resources.
- `content_script.js`: content runtime orchestrator.
- `options.html` + `options.js`: options UI composition root.
