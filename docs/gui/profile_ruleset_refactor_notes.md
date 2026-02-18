# Profile/Ruleset Refactor Notes

Last updated: 2026-02-18

## Goal

Document the current behavior boundaries before larger UI architecture changes.

## Current Behavior Map

Profile/ruleset state is currently edited in three places:

1. Main window selectors (`/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/main.py`)
2. Manage Profiles dialog (`/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/dialogs_profiles.py`)
3. Ruleset Library dialog (`/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/dialogs_rulesets.py`)

Shared persistence is handled by `AppState`:

- `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/state.py`

## Key Operations In Scope

1. Create profile
2. Delete profile (unlink rulesets only)
3. Link existing ruleset to profile
4. Initialize/create new ruleset file and link it
5. Unlink ruleset from profile
6. Set active ruleset for a profile
7. Delete ruleset file globally (double-confirm + unlink from all linked profiles)

## Known Coupling Points

1. Path normalization and active-ruleset fallback are duplicated across main/dialogs.
2. UI widgets directly implement business rules (unlink safety, fallback behavior, missing-file handling).
3. Main window handles both workspace rendering and profile/ruleset orchestration.

## Staged Refactor Sequence

1. Low-risk UI extraction (done):
   - `RulesTableView` + `DeleteButtonDelegate` moved to `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/rules_table_view.py`
   - `UtilityDockPanel` + `UtilityDock` moved to `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/utility_dock.py`
2. Introduce pure profile/ruleset domain helpers (in progress):
   - Added `/Users/takeyayuki/Documents/projects/LexiShift/apps/gui/src/profile_ruleset_utils.py`
   - Shared `ruleset_display_name` + path normalization now used by main/profile/ruleset dialogs.
3. Expand domain helper coverage:
   - New module with deterministic operations (no Qt dependency).
   - Move active-ruleset fallback/unlink safety/deletion constraints out of UI classes.
4. Add focused tests for domain helpers:
   - Active-ruleset fallback, unlink safety, and deletion constraints.
5. Then iterate on UI information architecture:
   - Once shared behavior is centralized, reshape dialog layout/workflows with less regression risk.

## Architecture Direction

Keep dialogs and main window as view/controller layers. Move profile/ruleset policy into reusable pure functions so UI layout can evolve independently.
