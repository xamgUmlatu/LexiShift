# Popup Modules Settings: Implementation Plan

Status:
- Planning only.
- No runtime implementation in this document.
- Current runtime/settings behavior is documented in:
  - `docs/architecture/chrome_extension_technical.md`
  - `docs/architecture/popup_modules_pattern.md`

Goal:
- Replace target-language gear preferences with a generalized "Modules" settings flow.
- Make popup module preferences profile-scoped.
- Keep module rendering architecture extensible for future optional modules and plugin APIs.

## 1) Product Decisions Locked In

1. UI trigger:
- Replace the target-language gear button with a localized text button: `Modules`.

2. Modal content:
- Remove title/subtitle for language preferences.
- Show only module controls (toggle/select fields).

3. Language restriction behavior:
- Some modules are language-restricted (example: Japanese primary display script).
- Restricted modules appear only when target language supports them.

4. Storage policy:
- No legacy compatibility/migration code required.
- This is unreleased development; new schema can be canonical from first implementation.

5. Scope of preferences:
- Module preferences are per profile.

## 2) Current State (Relevant)

Primary files currently involved:
- `apps/chrome-extension/options.html`
- `apps/chrome-extension/options.css`
- `apps/chrome-extension/options.js`
- `apps/chrome-extension/options/core/ui_manager.js`
- `apps/chrome-extension/options/core/settings_manager.js`
- `apps/chrome-extension/content/ui/ui.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content_script.js`

Current behavior summary:
- Options currently uses language-pref modal and `ja-primary-display-script`.
- Script display preference is persisted under profile language prefs (`targetScriptPrefs`) and mirrored to `targetDisplayScript`.
- Popup UI module rendering exists but is hardcoded in content UI.

## 3) Target Architecture

### 3.1 Canonical profile schema

Add profile-scoped module preferences:
- `srsProfiles.<profileId>.modulePrefs`

Proposed canonical shape:
```json
{
  "srsProfiles": {
    "default": {
      "modulePrefs": {
        "byId": {
          "feedback-core": {
            "enabled": true
          },
          "ja-script-forms": {
            "enabled": true
          },
          "ja-primary-display-script": {
            "enabled": true,
            "config": {
              "primary": "kanji"
            }
          }
        }
      }
    }
  }
}
```

Notes:
- `feedback-core` remains effectively mandatory in runtime policy but can still be represented in prefs.
- `ja-primary-display-script` is modeled as a module config, not a language-pref special field.

### 3.2 Runtime mirror schema (selected profile)

Publish resolved module settings into root runtime keys for content scripts:
- `popupModulePrefs` (new)

Proposed shape:
```json
{
  "popupModulePrefs": {
    "byId": {
      "feedback-core": {
        "enabled": true
      },
      "ja-script-forms": {
        "enabled": true
      },
      "ja-primary-display-script": {
        "enabled": true,
        "config": {
          "primary": "kanji"
        }
      }
    }
  }
}
```

Derived compatibility mirror (optional but useful internally):
- `targetDisplayScript` can continue to be published from `ja-primary-display-script.config.primary` to avoid broader ripple in replacement display path.

Important:
- No fallback from old fields.
- Runtime values are resolved from `modulePrefs` only.

### 3.3 Module metadata registry (single source of truth)

Introduce a module definition registry used by both Options UI and runtime rendering policy.

Suggested location:
- `apps/chrome-extension/shared/srs/popup_modules_registry.js` (new)

Definition shape:
```js
{
  id: "ja-primary-display-script",
  type: "select", // toggle | select
  labelKey: "module_ja_primary_display_script",
  languageTargets: ["ja"], // null means all
  defaultEnabled: true,
  defaultConfig: { primary: "kanji" },
  options: [
    { value: "kanji", labelKey: "option_ja_script_kanji" },
    { value: "kana", labelKey: "option_ja_script_kana" },
    { value: "romaji", labelKey: "option_ja_script_romaji" }
  ]
}
```

Core module entries to seed:
- `feedback-core` (all languages)
- `ja-script-forms` (ja target only)
- `ja-primary-display-script` (ja target only, select)

Planned language-scoped module examples (future):
- `verb-conjugations` (language targets vary by available conjugation datasets/tools)
- `grammatical-gender` (primarily for languages with grammatical gender usage)

## 4) Data Flow Design

### 4.1 Load flow (options page)

1. Load selected profile and language prefs.
2. Read profile `modulePrefs` via settings manager.
3. Resolve visible module definitions based on current target language.
4. Render module controls in modal list.

### 4.2 Save flow (options page)

1. User toggles module or changes module config.
2. Options saves profile `modulePrefs` (single source of truth).
3. Settings manager publishes resolved runtime mirrors:
- `popupModulePrefs`
- `targetDisplayScript` derived from module config (if retained).

### 4.3 Runtime consumption (content script / popup UI)

1. Content script reads `popupModulePrefs`.
2. Popup renderer checks module enabled/config values.
3. Script module display behavior respects `ja-primary-display-script` config.

## 5) File-Level Implementation Plan

### 5.1 Options UI files

1. `apps/chrome-extension/options.html`
- Replace gear icon button with text button (`Modules` localized).
- Remove modal title/subtitle block.
- Keep modal container/backdrop structure and close behavior.
- Keep module controls container for dynamic rendering.

2. `apps/chrome-extension/options.css`
- Adjust button style for text label.
- Ensure modal list layout supports multiple module controls.

3. `apps/chrome-extension/options/core/ui_manager.js`
- Replace old modal element ids with new module list ids (if changed).

4. `apps/chrome-extension/options.js`
- Remove special-case "language-specific preferences" naming and copy.
- Replace direct script-setting control path with generic module control rendering and save handlers.
- Keep profile scoping through selected SRS profile id.

### 5.2 Settings and schema files

1. `apps/chrome-extension/options/core/settings_manager.js`
- Add normalization/get/update/publish methods for `modulePrefs`.
- Add profile entry support for `modulePrefs`.
- Publish `popupModulePrefs` runtime mirror.
- Derive/publish `targetDisplayScript` from `modulePrefs` (if we keep that mirror).
- Remove active path dependence on `targetScriptPrefs` for module settings.

2. `apps/chrome-extension/shared/settings/settings_defaults.js`
- Add defaults for new root runtime key:
  - `popupModulePrefs`

3. `apps/chrome-extension/shared/srs/popup_modules_registry.js` (new)
- Central module definitions, defaults, language restrictions.

### 5.3 Content/runtime files

1. `apps/chrome-extension/content_script.js`
- Ensure runtime settings include `popupModulePrefs`.
- Ensure settings updates trigger popup behavior refresh when module prefs change.

2. `apps/chrome-extension/content/ui/ui.js`
- Gate module rendering using `popupModulePrefs.byId`.
- Keep feedback bar attached at bottom.
- Keep script module conditional on module enabled + target data.

## 6) Localization Plan

Add i18n keys:
- Modules button label:
  - `button_modules`
- Module labels:
  - `module_feedback_core`
  - `module_ja_script_forms`
  - `module_ja_primary_display_script`

Existing keys reused:
- `option_ja_script_kanji`
- `option_ja_script_kana`
- `option_ja_script_romaji`
- `button_ok` (if retained in modal footer)

Remove usage (not necessarily remove key immediately):
- `title_language_specific_preferences`
- `hint_language_specific_preferences_ja`

## 7) Organization / Anti-Bloat Plan

Given current file sizes, avoid adding more domain logic into `options.js`.

Refactor boundary for this feature:
- `options.js`:
  - orchestration + event wiring only.
- `options/core/settings_manager.js`:
  - schema, normalization, profile-scoped persistence, runtime publish.
- `shared/srs/popup_modules_registry.js`:
  - module definitions and defaults.
- `content/ui/ui.js`:
  - rendering and interaction only.

Optional extraction for immediate hygiene:
- `apps/chrome-extension/options/modules_preferences.js` (new helper) for modal rendering logic.

## 8) Step Plan With Checkpoints

Step 1:
- Add module registry file + defaults + settings manager schema methods.
- Checkpoint:
  - `node --check` on touched JS files.

Step 2:
- Rework options modal markup/copy and dynamic module list rendering.
- Checkpoint:
  - `node --check` options JS/UI manager JS.
  - quick UI sanity pass (manual).

Step 3:
- Wire save/load per profile for module prefs.
- Publish runtime mirror keys.
- Checkpoint:
  - storage read/write smoke validation in options console.

Step 4:
- Wire runtime consumption in content script and popup UI module gating.
- Checkpoint:
  - popup opens with expected modules by target language.
  - feedback bar remains at bottom.

Step 5:
- Clean dead special-case references (gear language preference naming/path).
- Checkpoint:
  - grep confirms old path removal from active flow.

## 9) Acceptance Criteria

1. Options button reads `Modules` (localized), no gear icon.
2. Modal has no language-pref title/subtitle, only module controls.
3. Module toggles/settings persist per selected profile.
4. Japanese-specific module controls appear only when target language is Japanese.
5. Popup module rendering respects saved module preferences.
6. Feedback module remains functional and attached at bottom.
7. No fallback/migration code from old schema paths.

## 10) Risks And Guardrails

Risk:
- Breaking target display script behavior during schema transition.
Guardrail:
- Keep explicit runtime derivation path from `modulePrefs` to active display selection.

Risk:
- Further growth of `options.js`.
Guardrail:
- Route module-specific logic into dedicated helper/registry files.

Risk:
- Inconsistent language-target gating between options and runtime.
Guardrail:
- Use a shared registry and shared filtering logic.
