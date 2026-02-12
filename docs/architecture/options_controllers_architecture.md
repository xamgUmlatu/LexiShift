# Options Controller Architecture

This document is the source-of-truth map for the options app structure and controller composition.

## Goals

- Keep `apps/chrome-extension/options.js` as startup/composition only.
- Keep behavior in small domain controllers with explicit dependencies.
- Keep state boundaries clear between:
  - settings persistence (`SettingsManager`)
  - helper actions (`HelperManager`)
  - UI wiring/controllers.

## Startup Flow

1. `apps/chrome-extension/options.html` loads scripts in strict order.
2. Core managers are constructed in `apps/chrome-extension/options.js`.
3. Bootstrap modules are resolved:
  - controller factory resolver
  - UI bridge
  - language prefs adapter factory
  - controller adapters factory.
4. `createControllerGraph(...)` composes all controllers.
5. App starts with:
  - `eventWiringController.bind()`
  - `pageInitController.load()`.

## Current Structure

```
apps/chrome-extension/options/
  core/
    bootstrap/
      controller_factory.js
      ui_bridge.js
      language_prefs_adapter.js
      translate_resolver.js
      dom_aliases.js
      controller_adapters.js
      controller_graph.js
    helper/
      base_methods.js
      diagnostics_methods.js
      srs_set_methods.js
    settings/
      base_methods.js
      language_methods.js
      ui_prefs_methods.js
      signals_methods.js
      srs_profile_methods.js
    helper_manager.js
    settings_manager.js
    localization_service.js
    rules_manager.js
    ui_manager.js
  controllers/
    helper/
      actions_controller.js
    page/
      init_controller.js
      event_wiring_controller.js
      events/
        general/
          display_bindings.js
          integrations_bindings.js
          language_bindings.js
          rules_bindings.js
        general_bindings.js
        profile_background_bindings.js
        srs_bindings.js
    profile/
      status_controller.js
      background_controller.js
      background/
        actions.js
        page_background_manager.js
        prefs_service.js
        preview_manager.js
        runtime_bridge.js
        utils.js
    rules/
      share_controller.js
    srs/
      profile_selector_controller.js
      profile_runtime_controller.js
      actions_controller.js
      actions/
        formatters.js
        shared.js
        workflows.js
    ui/
      display_replacement_settings_controller.js
      target_language_modal_controller.js
```

## Controller Graph (Ownership)

Composed in:
- `apps/chrome-extension/options/core/bootstrap/controller_graph.js`

Primary ownership:
- `pageInitController`
  - initial UI hydration and state load.
- `eventWiringController`
  - event binding only; no business logic.
- `srsProfileRuntimeController`
  - profile-scoped SRS settings load/save/publish path.
- `srsActionsController`
  - helper-backed SRS actions (initialize/refresh/diagnostics/sample/reset).
- `srsProfileSelectorController`
  - selected-profile selection and helper profile catalog refresh.
- `profileBackgroundController`
  - profile image prefs, preview/apply/remove, runtime bridge.
- `rulesShareController`
  - share-code generate/import/copy + rules text syncing.
- `helperActionsController`
  - helper diagnostics actions.
- `displayReplacementController`
  - replacement/highlight/debug setting controls.
- `targetLanguageModalController`
  - language-specific modal visibility and interaction lifecycle.
- `profileStatusController`
  - profile status output text/state only.

## Dependency Rules

- Controllers do not hard-import sibling controllers.
- Cross-domain interactions go through injected callbacks/adapters in `controller_graph.js`.
- Controllers receive concrete DOM elements via factory args; no broad global queries.
- `options.js` must fail fast when required bootstrap/controller modules are missing.
- Event binder modules delegate behavior to controllers; they do not own business logic.

## Growth Rules

- If a controller exceeds ~350-450 lines and has separable concerns, split by domain.
- New feature rule:
  - orchestration path in `controller_graph.js` and `options.js`
  - behavior path in a domain controller.
- Keep i18n strings in locale resources and use translation resolver from bootstrap.
- Keep runtime mirrors profile-scoped where profile semantics exist.

## Refactor Checklist

1. Identify one responsibility to extract.
2. Place new logic under the correct domain folder.
3. Register/wire controller via `controller_graph.js`.
4. Keep callsite behavior unchanged.
5. Remove dead wrappers only after full migration.
6. Run syntax checks:
   - `node --check <changed options js files>`
