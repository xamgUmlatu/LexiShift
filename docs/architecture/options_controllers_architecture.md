# Options Controller Architecture

This document defines how the options-page code is organized and how new logic should be added.

## Goals

- Keep `apps/chrome-extension/options.js` as composition/orchestration only.
- Keep feature logic in focused controllers grouped by domain.
- Preserve behavior while making future changes safer and faster.

## Current Structure

```
apps/chrome-extension/options/
  core/
    settings/
      base_methods.js
      language_methods.js
      ui_prefs_methods.js
      signals_methods.js
      srs_profile_methods.js
    settings_manager.js
  controllers/
    helper/
      actions_controller.js
    page/
      events/
        general/
          display_bindings.js
          integrations_bindings.js
          language_bindings.js
          rules_bindings.js
        general_bindings.js
        profile_background_bindings.js
        srs_bindings.js
      event_wiring_controller.js
      init_controller.js
    profile/
      background/
        actions.js
        page_background_manager.js
        prefs_service.js
        preview_manager.js
        runtime_bridge.js
        utils.js
      background_controller.js
      status_controller.js
    rules/
      share_controller.js
    srs/
      actions/
        formatters.js
      actions_controller.js
      profile_runtime_controller.js
      profile_selector_controller.js
    ui/
      display_replacement_settings_controller.js
      target_language_modal_controller.js
```

## Responsibility Boundaries

- `page/init_controller.js`
  - First-load hydration.
  - Initial UI sync and status bootstrapping.
- `page/event_wiring_controller.js`
  - DOM event binding only.
  - Delegates all behavior to domain controllers.
  - Delegates grouped event clusters to `page/events/*` binders.
- `page/events/general/*`
  - `rules_bindings.js`: rules save/import/export, rules-source toggles, share-code actions.
  - `display_bindings.js`: highlight/replacement/debug and global enable toggles.
  - `language_bindings.js`: UI language + source/target language + target-language modal behavior.
  - `integrations_bindings.js`: external integration link actions.
- `profile/*`
  - Profile selector/status and profile background behavior.
  - `profile/background/*` holds preview rendering, page background rendering, prefs persistence, runtime sync bridge, and utility helpers.
- `srs/*`
  - SRS runtime profile save/load and SRS helper actions.
  - `srs/actions/*` holds SRS action report/formatting helpers.
- `rules/*`
  - Rules save/import/export/share code flow.
- `helper/*`
  - Helper connection/status debug actions.
- `ui/*`
  - UI-only settings and modal behavior.
- `core/settings/*`
  - Domain installers for `SettingsManager` logic (base, language, ui prefs, signals, srs profile).
  - Keep `core/settings_manager.js` as constructor + storage IO + installer composition only.

## Dependency Rules

- Controllers communicate through injected callbacks and adapters, not hard imports between controllers.
- Controllers should not query arbitrary DOM globally; pass required elements in `createController(...)`.
- `options.js` composes controllers and provides cross-domain adapters.
- `options.js` resolves controller modules via required factory guards (fail fast on missing registrations).
- Avoid storing business logic in event handlers. Event handlers should delegate to controllers.

## Growth Rules

- If a controller grows past ~350-450 lines and has separable concerns, split it into subcontrollers.
- If a new feature touches more than one domain, keep orchestration in `options.js` and place logic in the owning domain controller.
- Keep user-visible messages centralized in existing i18n keys/fallbacks.
- Preserve behavior before refactoring; run syntax checks after each step.

## Refactor Checklist

1. Identify one coherent responsibility.
2. Extract behavior into a new controller under the correct domain folder.
3. Wire via `createController(...)` in `options.js`.
4. Keep old wrappers until callsites are migrated.
5. Remove dead code only after all callsites delegate cleanly.
6. Run `node --check` on changed files.
