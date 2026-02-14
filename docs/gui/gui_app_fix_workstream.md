# GUI App Fix Workstream

Last updated: 2026-02-14

## Context

The current desktop GUI has accumulated UX and state-management issues that now block usability:

- Header/button layout is confusing and partially redundant.
- Color and status signaling are inconsistent across themes, with contrast failures in dark modes.
- Language/frequency/embedding pack flows have outgrown a single settings tab and need dedicated views.
- Profile and ruleset state handling contains data-loss and active-selection bugs.

This workstream defines the fix plan and acceptance criteria.

## Progress Snapshot

- Phase 0 (Stabilization): in progress
  - Completed: profile data-loss fixes, profile remove-state fix, language-pack failure crash fix, regression tests.
- Phase 1 (State Consistency): in progress
  - Completed: stale `active_profile_id` fallback, ruleset-combo active selection consistency, unsaved-state title indicator in main window, profile path normalization at state boundaries, missing-active-ruleset recovery, and duplicate profile-id sanitization.
- Phase 2 (UX Architecture Refresh): in progress
  - Completed: dedicated resources tab in Settings, simplified main-window header action row, and resources sub-views split by pack type.
- Phase 3 (Visual/Accessibility Pass): in progress
  - Completed: semantic status color tokens in theme loading/registry, migration of resource status UI off hardcoded colors, and main-window log/preview/delete tinting tied to active theme.

## Scope

In scope:

- Main window information architecture (profile/ruleset controls, action placement).
- Language/frequency/embedding pack management UX and interaction model.
- Theme-consistent semantic color usage and minimum contrast requirements.
- Profile/ruleset correctness bugs (active profile, load behavior, persistence integrity).

Out of scope:

- New language-pair feature expansion.
- Chrome extension/plugin UX.

## Confirmed Problems

### P0 Data Integrity / Crash

1. Manage Profiles can silently corrupt profile data on open/save flow.
   - Symptoms: name/tags/description/rulesets/active ruleset can be wiped without intentional edits.
   - Key code paths:
     - `apps/gui/src/dialogs_profiles.py:179`
     - `apps/gui/src/dialogs_profiles.py:200`
     - `apps/gui/src/dialogs_profiles.py:138`
2. Removing a profile can overwrite surviving profile data with stale form state.
   - Key code path:
     - `apps/gui/src/dialogs_profiles.py:376`
3. Language pack failure handling can crash due to invalid row type access.
   - `LanguagePackRow` does not have `use_button`, but failure handler accesses it.
   - Key code paths:
     - `apps/gui/src/settings_language_packs.py:1423`
     - `apps/gui/src/settings_language_packs.py:1428`
     - `apps/gui/src/settings_language_packs.py:45`

### P1 State Correctness

4. Active profile fallback fails when configured `active_profile_id` is stale/invalid.
   - App can launch with profiles present but no profile loaded.
   - Mitigation landed: active profile id is normalized on settings load/update.
   - Key code path:
     - `apps/gui/src/main.py:664`
     - `apps/gui/src/state.py:20`
5. Ruleset “Set Active” behavior is unreliable in profile dialog.
   - Existing `active_ruleset` can override current UI selection when committing.
   - Key code paths:
     - `apps/gui/src/dialogs_profiles.py:306`
     - `apps/gui/src/dialogs_profiles.py:268`
6. Missing active ruleset files can silently load empty datasets.
   - Mitigation landed: profile load now prefers existing ruleset paths and persists corrected active ruleset.
   - Key code paths:
     - `apps/gui/src/main.py:1391`
     - `apps/gui/src/main.py:1402`

### P2 UX / IA / Accessibility

7. Header controls are redundant and unclear.
   - Top-level row duplicates menu actions and blends profile and ruleset actions without hierarchy.
   - Key code paths:
     - `apps/gui/src/main.py:485`
     - `apps/gui/src/main.py:399`
     - `apps/gui/src/main.py:1518`
8. Language pack management is overloaded in a single settings tab.
   - Four large, action-dense tables in one scroll path increase cognitive load.
   - Mitigation landed: resources now split into dedicated internal sub-views per pack type.
   - Key code paths:
     - `apps/gui/src/dialogs.py:345`
     - `apps/gui/src/settings_language_packs.py:253`
     - `apps/gui/src/settings_language_packs.py:283`
     - `apps/gui/src/settings_language_packs.py:298`
     - `apps/gui/src/settings_language_packs.py:318`
9. Status colors are not yet fully standardized across all GUI surfaces.
   - Core status surfaces now use semantic theme tokens, but a full contrast/accessibility audit is still pending.
   - Key code paths:
     - `apps/gui/src/main.py:607`
     - `apps/gui/src/preview.py:67`
     - `apps/gui/src/theme_loader.py:13`
     - `apps/gui/src/theme_registry.py:1`

## Workstream Plan

### Phase 0: Stabilization (Blockers)

- Fix profile dialog commit sequencing so no write occurs before form load.
- Fix profile removal flow to preserve selected profile data integrity.
- Fix language pack failure handlers to only access fields valid for each row type.
- Add safety tests for profile dialog open/save/remove transitions.

Exit criteria:

- No profile field loss in open-save-close smoke tests.
- No crash in language/frequency/embedding failure paths.

### Phase 1: State Consistency

- Harden active profile resolution: if configured profile is missing, fall back to first valid profile and persist.
- Fix ruleset activation logic to apply the explicitly selected ruleset.
- Add regression tests for:
  - invalid `active_profile_id`
  - ruleset activation in profile editor
  - startup load consistency

Exit criteria:

- Active profile and dataset always resolve deterministically on startup.
- Selected ruleset always loads and persists as active.

### Phase 2: UX Architecture Refresh

- Move pack management into a dedicated “Resources” view/window.
- Replace table-first UX with pack cards or list-detail panels:
  - clear state (Available, Downloaded, Linked, Active, Invalid)
  - primary action per pack
  - inline progress/cancel/error recovery
- Simplify main header:
  - reduce duplicate controls
  - separate selection controls from destructive/persistence actions
  - keep advanced actions in menus

Exit criteria:

- New-user path to select profile, select ruleset, and manage packs is straightforward in <= 3 steps each.
- No duplicate primary actions between header and menu without clear rationale.

### Phase 3: Visual/Accessibility Pass

- Replace hardcoded semantic colors with theme tokens.
- Define semantic roles in theme system (success/warning/error/info).
- Enforce contrast targets:
  - normal text >= 4.5:1
  - large text >= 3:1
- Add visual regression checks for light and dark built-in themes.

Exit criteria:

- No hardcoded status colors in GUI logic files.
- Contrast checks pass for all built-in themes.

## Test Strategy

- Unit tests for profile dialog state transitions.
- Unit tests for active profile/ruleset fallback resolution.
- Widget-level tests for language pack failure paths.
- Manual QA checklist:
  - profile create/edit/remove
  - ruleset switching with unsaved changes
  - download/fail/cancel/retry for all pack types
  - light/dark theme readability

## Deliverables

- Code fixes for all P0/P1 defects.
- Dedicated resources management UI.
- Updated theme semantics and color usage.
- New regression tests and a GUI QA checklist.
