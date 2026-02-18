# GUI UX Decision Log

Last updated: 2026-02-14

## Purpose

This log tracks accepted UX and interaction decisions for the experimental GUI overhaul.  
When implementation changes quickly, this file is the source of truth for why a behavior exists.

## Decision Rules

- Only record decisions that affect user-visible behavior or workflow structure.
- Each decision must include rationale and current implementation status.
- If a decision is reversed, keep the old entry and add a superseding one.

## Decisions

### D-001 (Accepted): Stabilize state integrity before visual redesign

- Date: 2026-02-14
- Decision:
  - Fix profile/ruleset data-loss and crash paths before layout or theme polish.
- Rationale:
  - Visual changes are unsafe while core state transitions can corrupt user data.
- Status:
  - Implemented with regression tests.
- References:
  - `apps/gui/src/dialogs_profiles.py`
  - `apps/gui/src/main.py`
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/tests/test_profiles_dialog.py`

### D-002 (Accepted): Move pack management into a dedicated Settings view

- Date: 2026-02-14
- Decision:
  - Language/frequency/embedding management is no longer embedded in the App tab form.
  - It now lives in its own dedicated Settings tab.
- Rationale:
  - The pack flows are large and operationally distinct from simple app toggles.
  - Separating them lowers cognitive load and clarifies information architecture.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/dialogs.py`

### D-003 (Accepted): Simplify the main header action model

- Date: 2026-02-14
- Decision:
  - Remove redundant profile-save button from main header.
  - Keep a compact row with profile selection/manage and ruleset selection/open/save.
- Rationale:
  - The prior layout duplicated actions and blurred profile vs ruleset responsibility.
  - Header should focus on immediate context-switch actions.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/main.py`

### D-004 (Accepted): Keep advanced and less-frequent actions in menus

- Date: 2026-02-14
- Decision:
  - Preserve richer actions (import/export/debug/profile management variants) in menus.
  - Avoid adding equivalent top-row buttons unless they are core daily actions.
- Rationale:
  - Prevents header bloat while preserving power-user capability.
- Status:
  - Active policy.

### D-005 (Accepted): Every UX bugfix must land with a regression test

- Date: 2026-02-14
- Decision:
  - Add focused tests whenever fixing profile/ruleset/resource-state regressions.
- Rationale:
  - This area is rapidly changing and has repeated regressions in selection/commit flows.
- Status:
  - Active policy.

### D-006 (Accepted): Use semantic status color tokens in resource workflows

- Date: 2026-02-14
- Decision:
  - Resource status rendering must use semantic tone keys (`status_success`, `status_warning`, `status_error`, `status_info`, `status_neutral`, `status_muted`) instead of hardcoded hex colors.
  - User themes may override these keys; built-in themes define defaults.
- Rationale:
  - Hardcoded status colors break readability across light/dark themes and prevent custom theme consistency.
  - Semantic tokens let behavior-driven status tones stay stable while visuals adapt per theme.
- Status:
  - Implemented for language/frequency/embedding resource tables and status messages.
- References:
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/src/theme_loader.py`
  - `apps/gui/src/theme_manager.py`
  - `apps/gui/src/theme_registry.py`

### D-007 (Accepted): Main-window diagnostic colors follow active theme

- Date: 2026-02-14
- Decision:
  - Main-window log/error tinting and replacement highlight color are resolved from active theme tokens at runtime.
  - Theme re-apply updates delete-action tint and log color handlers.
- Rationale:
  - Diagnostic/readability cues must stay legible across light/dark themes and user themes.
  - Runtime updates prevent stale colors after theme switching.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/main.py`
  - `apps/gui/src/preview.py`

### D-008 (Accepted): Resources tab uses dedicated sub-views by pack type

- Date: 2026-02-14
- Decision:
  - Split Resources into internal sub-tabs: lexical packs, frequency packs, embeddings, and cross-embeddings.
  - Keep one shared status area while isolating heavy tables into distinct views.
- Rationale:
  - The previous single-scroll stack mixed four large operational tables and made flows harder to parse.
  - Dedicated sub-views reduce scanning load and make each workflow easier to discover.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/settings_language_packs.py`
  - `apps/gui/tests/test_settings_resources_tab.py`

### D-009 (Accepted): Surface unsaved ruleset state in main window title

- Date: 2026-02-14
- Decision:
  - Append `*` to the main window title when the active ruleset has unsaved changes.
  - Keep save actions enabled/disabled in sync with the same dirty state.
- Rationale:
  - Users need a persistent global signal before profile/ruleset switches.
  - A title-level signal is low-noise and always visible.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/main.py`
  - `apps/gui/tests/test_main_dirty_title.py`

### D-010 (Accepted): Normalize profile ruleset paths at state boundaries

- Date: 2026-02-14
- Decision:
  - On settings load/update/set-profiles, normalize profile ruleset paths (`expanduser`, absolute path resolution, dedupe).
  - Resolve `active_profile_id` to a valid profile, falling back to first available profile.
  - Keep `dataset_path` aligned with resolved `active_ruleset`.
- Rationale:
  - Imported/legacy settings can contain mixed relative, duplicate, and stale path fields that break active profile/ruleset loading.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/state.py`
  - `apps/gui/tests/test_state_profile_paths.py`

### D-011 (Accepted): Default runtime log text uses theme text color

- Date: 2026-02-14
- Decision:
  - Main log lines without explicit severity color are rendered using the active theme's `text` token.
- Rationale:
  - Prevents unreadable log text caused by implicit/default text formats after theme changes.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/main.py`
  - `apps/gui/tests/test_main_log_colors.py`

### D-012 (Accepted): Missing active ruleset path auto-recovers to an existing ruleset

- Date: 2026-02-14
- Decision:
  - When loading a profile, if `active_ruleset` is missing on disk but another listed ruleset exists, switch to the first existing ruleset and persist it as active.
- Rationale:
  - Prevents silent empty-dataset loads caused by stale active path pointers.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/main.py`
  - `apps/gui/tests/test_main_profile_loading.py`

### D-013 (Accepted): Imported profile IDs are sanitized and deduplicated

- Date: 2026-02-14
- Decision:
  - Profile IDs are normalized at state boundaries; empty IDs become `profile`, duplicates receive numeric suffixes.
  - Active profile selection is mapped onto the normalized ID set.
- Rationale:
  - Imports and legacy payloads can contain invalid profile IDs that break profile switching and persistence.
- Status:
  - Implemented.
- References:
  - `apps/gui/src/state.py`
  - `apps/gui/tests/test_state_profile_paths.py`

## Open Questions

- Should resources become a standalone window instead of a Settings tab?
- Should “Open Ruleset” become a split-button with recent paths?
- Should profile/ruleset switching gain explicit dirty-state banners before switching?
