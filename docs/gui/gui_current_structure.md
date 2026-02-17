# GUI Current Structure

Last updated: 2026-02-17

## Purpose

This document describes the current structure of the LexiShift desktop GUI after the Utility Dock overhaul.
It is a snapshot of how the app is organized today, not a long-term UX specification.

## Screen Topology

The app currently has two sibling management windows for profile/ruleset administration:

1. `Manage Profiles` dialog (`apps/gui/src/dialogs_profiles.py`)
2. `Ruleset Library` dialog (`apps/gui/src/dialogs_rulesets.py`)

Both are launched from the main window (`apps/gui/src/main.py`) and are also available in the `Profiles` menu.

## Main Window Layout

Main window construction lives in `MainWindow.__init__` in `apps/gui/src/main.py`.

Primary structure:

1. Horizontal splitter (`self._splitter`)
2. Left/editor side:
   - Profile + ruleset header cards (`_build_profile_header`)
   - Rules table (`RulesTableView`)
3. Right/utility side (`self._right_splitter`, vertical):
   - Replacements panel (always visible while editing)
   - Utility Dock (collapsible panel host)

### Header Cards

The top row has two cards:

1. Current Profile
   - Profile dropdown
   - `Manage...` button (opens `Manage Profiles`)
2. Current Ruleset
   - Ruleset dropdown
   - `Select...`, `Save Ruleset`, and `Rulesets...` buttons

These cards are the primary quick-switch controls.

### Rules Table

`RulesTableView` renders active rules from the currently loaded dataset.

- Supports sorting via proxy model (`QSortFilterProxyModel`).
- Uses a custom delete delegate for prominent delete actions.
- Shows a themed empty-state card when no rules exist.

### Replacements Panel

The replacements panel is always available on the right side and includes:

1. Replacement list
2. Similarity threshold slider
3. Embedding loading/status hints

This panel controls synonym-filter threshold behavior for selected replacement words.

## Utility Dock

Utility Dock lives in `apps/gui/src/main.py`:

1. `UtilityDockPanel`: one collapsible panel with header, content, and unread badge
2. `UtilityDock`: panel container with add/query/toggle helpers

Current panel set:

1. `logs` panel (contains runtime log text edit)

Behavior:

1. Logs are collapsed by default (`main_window/utility/logs_expanded`, default `False`)
2. When collapsed, new log lines increment unread badge count
3. Expanding clears unread count
4. Panel expanded state is persisted per panel id

Styling hooks are in `apps/gui/src/theme_manager.py`:

- `QWidget[utilityDockPanel="true"]`
- `QPushButton[dockHeader="true"]`
- `QLabel[utilityDockBadge="true"]`

## Manage Profiles Dialog

`ProfilesDialog` (`apps/gui/src/dialogs_profiles.py`) uses a left-right management layout:

1. Left: profile list + create/delete/set-startup actions
2. Right top: selected profile details (`Profile ID`, `Name`, active ruleset combo)
3. Right bottom left: linked rulesets list + link/create/unlink actions
4. Right bottom right: selected ruleset details + set-active/reveal actions

Important behavior:

1. Profile ID is currently read-only in v1.
2. Rulesets are shown by base name (stem), not full path.
3. Profile deletion unlinks rulesets but does not delete ruleset files.
4. Changes are staged and committed on explicit dialog acceptance (`OK`).

## Ruleset Library Dialog

`RulesetLibraryDialog` (`apps/gui/src/dialogs_rulesets.py`) is a dedicated ruleset administration window:

1. Left: all unique rulesets aggregated across profiles
2. Right: path/status/linked-profile details + simple rules preview
3. Actions: reveal selected ruleset, delete selected ruleset

Deletion flow is intentionally strict:

1. Block deletion if ruleset is the last ruleset for any linked profile
2. First confirmation: unlink impact across linked profiles
3. Second confirmation: final destructive confirmation

## State and Persistence Notes

Primary state engine: `AppState` in `apps/gui/src/state.py`.

Relevant persisted UI state:

1. Main window geometry/splitter sizes (`QSettings`)
2. Utility Dock panel expansion by panel id (`main_window/utility/<panel>_expanded`)
3. Theme/locale preferences (`appearance/theme`, `appearance/locale`)

## Localization Coverage

All user-facing strings in the current structure are wired through i18n keys in:

1. `apps/gui/resources/i18n/en.json`
2. `apps/gui/resources/i18n/de.json`
3. `apps/gui/resources/i18n/ja.json`
4. `apps/gui/resources/i18n/zh.json`

This includes:

1. Main-window startup diagnostics text
2. Utility Dock labels
3. Helper tray menu/status/notification text
4. Embedding conversion status text in language-pack management
