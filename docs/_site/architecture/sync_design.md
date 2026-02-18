# LexiShift Sync Design (App ↔ Extension ↔ Plugin)

This document captures what should sync across the desktop app, Chrome extension, and BetterDiscord plugin, and how each client should consume the data. It is intended as a development blueprint and checklist.

## Goals
- Make rulesets portable across all clients.
- Keep UX consistent while allowing per‑client preferences.
- Avoid surprising behavior when a user switches profiles or rulesets.
- Support offline use with deterministic fallbacks.

## Clients & Capabilities
- **GUI App**: Source of truth for profiles, rulesets, language packs, and synonym generation.
- **Chrome Extension**: Applies replacements on web pages; options UI for rules, SRS controls, share code, and logging.
  - SRS profile selection is extension-local and global (picked from helper profile catalog).
  - SRS settings/signals are stored under that selected profile, with language-pair subkeys.
  - Extension does not mutate GUI/helper active profile.
- **BetterDiscord Plugin**: Applies replacements in Discord; options UI for basic settings + share code.

## Data Model to Sync
### Core entities
- **Profile**
  - `profile_id`, `name`, `description`, `tags`
  - `rulesets`: list of ruleset identifiers (path or stable ID)
  - `active_ruleset`: currently active ruleset
  - `srs_by_pair`: pair-scoped SRS settings/signals/state references
- **Ruleset**
  - `rules`: list of replacement rules (source_phrase, replacement, case_policy, enabled, priority, tags)
  - `metadata`: ruleset label/description/source
  - `updated_at`

### Shared settings (should sync)
- **Replacement behavior**
  - `max_one_per_text_block`
  - `allow_adjacent_replacements`
  - default `case_policy`
- **Highlighting**
  - `highlight_enabled`
  - `highlight_color`
  - `click_to_toggle_original`
- **Share code**
  - last exported code
  - last imported timestamp
- **Synonym settings**
  - `embedding_threshold`
  - `embedding_fallback_enabled`
  - `consensus_filter_enabled`
- **Language packs**
  - selected monolingual packs
  - selected cross‑lingual packs
  - per‑profile language choices (source/target)
- **Localization**
  - preferred UI language per client (default to client locale)
- **Diagnostics**
  - `debug_enabled`
  - `debug_focus_word`

## Per‑Client Local Settings (do not sync)
- **Chrome extension**
  - rules source mode (file vs editor)
  - file import path / last file name
  - debug tools (page scopes)
  - profile background UI prefs (`backgroundAssetId`, `backgroundEnabled`, `backgroundOpacity`, `backgroundBackdropColor`)
  - IndexedDB profile media blobs referenced by `backgroundAssetId`
- **BetterDiscord plugin**
  - per‑server toggles or UI presentation settings (if added)
- **GUI app**
  - local file system paths (rulesets, dictionaries, embeddings)
  - theme selection and background image paths

## Sync Direction
- **Primary source**: GUI app is the source of truth for profiles + rulesets.
- **Clients**: Extension and plugin consume exported snapshots:
  - ruleset JSON (active or chosen ruleset)
  - app settings subset (highlight, replacement behavior, etc.)
- **Extension profile bridge**:
  - extension reads helper profile snapshot via native messaging (`profiles_get`),
  - helper snapshot is sourced from GUI `settings.json`,
  - extension stores a local selected profile id (global) and never changes GUI/helper active profile.
  - helper runtime calls include `profile_id` and read/write profile-scoped SRS files.
- **Write‑back**: Optional future feature (clients can push updates back).

## Sync Mechanisms
### v1 (Manual)
- Export from app:
  - JSON ruleset file
  - Share code
- Import into clients:
  - Extension: JSON file or share code
  - Plugin: JSON file/path or share code

### v2 (Assisted)
- App exposes “Export to Extension/Plugin” in GUI.
- Generates:
  - Selected ruleset JSON
  - Settings JSON subset
  - QR/share code for fast import

### v3 (Auto‑sync)
- Local WebSocket or local HTTP endpoint (app runs a local sync service).
- Clients poll or subscribe to active profile changes.
- Optional per‑client ruleset selection from app.

## UX Integration Links
### In‑app (GUI)
- Settings → Integrations
  - Install Chrome Extension
  - Install BetterDiscord Plugin
  - Copy share code / export JSON

### Extension options
- “Get LexiShift Desktop App”
- “Get BetterDiscord Plugin”
- “Import from app” (share code / JSON)

### Plugin settings
- “Get LexiShift Desktop App”
- “Get Chrome Extension”

## Edge Cases & Conflicts
- Multiple rulesets in a profile vs. client supports only one.
- App uses absolute file paths not available on client.
- Language pack availability differs per device.
- If a ruleset is missing, fall back to last known ruleset with a warning.

## Roadmap Tasks
1) Define a stable ruleset export schema for clients.
2) Add an “Integrations” section to app settings with download links.
3) Add “Get the app/plugin” links in extension options and plugin settings.
4) Implement a settings subset export (highlight + behavior + debug).
5) Create a shared share‑code format for profiles + active ruleset.
6) Evaluate local auto‑sync service.
