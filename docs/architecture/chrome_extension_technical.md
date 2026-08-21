# LexiShift Chrome Extension: Technical Notes

Status: active mixed reference
Role: Mixed
Last updated: 2026-04-21
Purpose: module-level technical reference for current extension behavior plus known gaps and ongoing areas
Source-of-truth: mixed as-is + known-gaps reference; verify live runtime behavior in `extension_system_map.md`, `apps/chrome-extension/manifest.json`, `apps/chrome-extension/options/core/bootstrap/controller_graph.js`, and the linked source modules.

This doc mixes current runtime notes with known gaps and forward-looking sections.
Use `extension_system_map.md` first when you need the shortest current-behavior path.

Recommended read order
- Start here for a single-page map: `docs/architecture/extension_system_map.md`.
- Then use this file for module-level detail.
- For options composition internals: `docs/architecture/options_controllers_architecture.md`.
- For popup module architecture: `docs/architecture/popup_modules_pattern.md`.

## How To Use This Doc

- Treat the overview, module layout, manifest ordering, settings flow, runtime/storage sections, and SRS/helper flow notes as the current extension reference.
- Treat Share Center rollout notes and the explicit known-issue section as mixed/gap-tracking content, not fully settled architecture.
- Verify implementation-facing claims in source when a change depends on exact runtime behavior.

## Current Runtime Reference

Overview
- The extension runs a content script on all frames and replaces visible text using a ruleset.
- The codebase is modularized into small, focused modules loaded in a strict order by the manifest.
- Settings are stored in `chrome.storage.local` and shared between the content script and options page.
- Profile media assets (background images) are stored in extension IndexedDB and referenced by id.

Top-level extension directories
- `apps/chrome-extension/shared`
  - Cross-runtime modules used by both content/runtime and options.
- `apps/chrome-extension/content`
  - Webpage runtime processing, scanning, replacement, and popup UI behavior.
- `apps/chrome-extension/options`
  - Options app controllers, settings installers, and bootstrap composition graph.
- `apps/chrome-extension/_locales`
  - Localization resource bundles.
- `apps/chrome-extension/icons`
  - Extension assets.

Module layout
- `apps/chrome-extension/shared/settings/settings_defaults.js`
  - Central default settings used by both the options UI and content script.
  - Avoids drift when new settings are added.
- `apps/chrome-extension/shared/srs/srs_selector.js`
  - Loads the fixed SRS test dataset and scores candidates.
  - Selects active SRS lemmas for gating.
- `apps/chrome-extension/shared/helper/helper_feedback_sync.js`
  - Persistent helper feedback sync queue with retry + backoff.
  - Uses a lightweight storage lock to reduce duplicate flush workers.
  - Supports optional dropped-entry archive when a retry cap is enabled.
- `apps/chrome-extension/shared/profile/profile_media_store.js`
  - IndexedDB-backed profile media store for blob assets.
  - Stores profile-scoped background images close to original binary size.
- `apps/chrome-extension/shared/srs/srs_feedback.js`
  - Persists SRS feedback events to `chrome.storage.local` (`srsFeedbackLog`).
  - Provides helper to build feedback entries from replacement spans.
- `apps/chrome-extension/shared/srs/srs_store.js`
  - Maintains a compact SRS item store in `chrome.storage.local` (`srsStore`).
  - Updates item history/scheduler fields from feedback events.
  - Exposure counts are telemetry and should not be treated as scheduling events.
- `apps/chrome-extension/shared/srs/srs_gate.js`
  - Filters rules using the active SRS lemma set (gating).
- `apps/chrome-extension/shared/language/lemmatizer.js`
  - Stub lemmatizer for early data collection (identity for JP, lowercase for EN/DE).
- `apps/chrome-extension/shared/srs/srs_metrics.js`
  - Records replacement exposures to `chrome.storage.local` (`srsExposureLog`).
  - Exposure logs are for diagnostics/analytics, not direct SRS scheduling.
- `apps/chrome-extension/content/processing/tokenizer.js`
  - Tokenization utilities (word/space/punct) and normalization helpers.
  - Exposes `tokenize`, `normalize`, `textHasToken`, `computeGapOk`.
- `apps/chrome-extension/content/processing/matcher.js`
  - Builds a phrase trie from rules and resolves longest-match tokens.
  - Applies case policy (`match`, `as-is`, `lower`, `upper`, `title`).
  - Normalizes rule objects to a consistent shape.
- `apps/chrome-extension/content/processing/replacements.js`
  - Builds a `DocumentFragment` with replacement spans for a text node.
  - Filters matches based on settings (max-one-per-block, allow-adjacent, page budgets).
  - Keeps optional replacement detail logs for debug mode.
  - Adds `data-origin`, `data-language-pair`, and `data-source` for downstream UI control.
- `apps/chrome-extension/content/processing/replacement_semantic_debug.js`
  - Serializes semantic admission decisions onto debug replacement metadata.
- `apps/chrome-extension/content/processing/replacement_semantic_override.js`
  - Builds stable per-match semantic-result overrides so budgeted scan preflight can reuse helper decisions during ordered DOM rendering.
- `apps/chrome-extension/content/runtime/dom_scan_runtime.js`
  - Owns DOM text-node scanning, mutation observer updates, and page budget enforcement orchestration.
  - Delegates node filtering, budget tracking, counter construction, and text-node replacement handling to `content/runtime/dom_scan/*`.
- `apps/chrome-extension/content/runtime/dom_scan/node_filters.js`
  - Central node guards for editable fields, excluded tags, non-rendered
    ancestor subtrees, and already-replaced LexiShift spans.
- `apps/chrome-extension/content/runtime/dom_scan/page_budget_tracker.js`
  - Builds and updates unified replacement budget state (page-total,
    per-sentence, and per-lemma caps) from existing and newly committed spans.
- `apps/chrome-extension/content/runtime/dom_scan/scan_order.js`
  - Prioritizes visible and near-viewport text nodes during full scans.
  - When page budgets are active, deterministically redistributes node order within viewport bands by page/profile seed.
- `apps/chrome-extension/content/runtime/dom_scan/semantic_context_support.js`
  - Clips helper semantic-admission input to the sentence containing the match.
  - Prefers locale-aware `Intl.Segmenter` sentence/word segmentation and keeps a
    deterministic fallback for unsupported runtimes.
  - The fallback preserves common non-terminal title abbreviations, decimal and
    embedded periods, closing sentence punctuation, Unicode terminators, and a
    hard 48-word / 1200-character context budget.
- `apps/chrome-extension/content/runtime/dom_scan/semantic_context.js`
  - Reconstructs semantic context across inline text nodes within bounded
    paragraph/list/table/heading-style containers.
  - Excludes hidden, editable, skipped, and already-replaced content.
  - Preserves explicit `<br>` and DOM/CSS block transitions as context
    boundaries while retaining match-offset mapping and scan-local block-cache
    reuse.
  - Assigns scan-stable, best-effort sentence identities from container identity
    plus sentence ordinal so split inline nodes share the same sentence budget.
- `apps/chrome-extension/content/runtime/dom_scan/semantic_node_scheduler.js`
  - Batches semantic text-node preflight work, including the two-phase path that preserves ordered page-budget rendering.
- `apps/chrome-extension/content/runtime/dom_scan/scan_counters.js`
  - Constructs scan diagnostics counters for full scans and mutation scans,
    including aggregate page/sentence/lemma budget rejection counts.
- `apps/chrome-extension/content/runtime/dom_scan/text_node_processor.js`
  - Executes per-node replacement, exposure logging, and focus-word diagnostics.
- `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`
  - Resolves helper rules with profile-scoped cache fallback (`memory -> persisted`).
  - Normalizes helper fetch failures into deterministic `helper` vs `helper-cache` source states.
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
  - Resolves active ruleset state for content runtime (`normalize -> enabled -> SRS gate`).
  - Returns source/origin counters and active lemma state used by diagnostics and logging.
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
  - Centralizes settings-apply diagnostics logs and runtime-state snapshots.
  - Keeps `content_script.js` focused on orchestration instead of report formatting.
- `apps/chrome-extension/content/runtime/apply_runtime_actions.js`
  - Runs apply-time runtime actions (styles/listeners/highlight + replacement scan execution).
  - Keeps `applySettings` orchestration in `content_script.js` concise.
- `apps/chrome-extension/content/runtime/apply_settings_pipeline.js`
  - Central pipeline for settings-apply flow (`normalize settings -> resolve active rules -> diagnostics -> runtime actions`).
  - Handles apply token staleness checks via injected runtime callback.
- `apps/chrome-extension/content/runtime/feedback/feedback_runtime_controller.js`
  - Owns feedback entry persistence and helper feedback-sync queue integration.
- `apps/chrome-extension/content/runtime/settings_change_router.js`
  - Routes `chrome.storage.onChanged` keys to targeted runtime actions (rebuild/highlight/debug/feedback updates).
- `apps/chrome-extension/content/ui/ui.js`
  - Composition layer for highlight styles, click-to-toggle behavior, and cleanup.
  - Delegates feedback popup behavior to `content/ui/feedback_popup_controller.js`.
  - Delegates Japanese script module rendering to `content/ui/popup_modules/japanese_script_module.js`.
  - Popup module architecture and extension plan: `docs/architecture/popup_modules_pattern.md`.
- `apps/chrome-extension/content/ui/feedback_popup_controller.js`
  - Owns feedback popup lifecycle, module attachment zone, keyboard shortcuts (Ctrl+1/2/3/4), and sound feedback.
  - Renders module blocks from the popup module registry before the feedback bar.
- `apps/chrome-extension/content/ui/popup_modules/module_registry.js`
  - Registry/composition layer for popup modules (`id + build(target)` descriptors).
  - Enables modular popup extension without changing popup controller internals.
- `apps/chrome-extension/content/ui/popup_modules/japanese_script_module.js`
  - Builds the Japanese scripts module payload for popup rendering using replacement metadata (`script_forms`).
- `apps/chrome-extension/content/ui/utils.js`
  - Logging helpers: element descriptors, codepoint snippets, node traversal.
- `apps/chrome-extension/options/core/settings_manager.js`
  - Thin `SettingsManager` class shell (storage IO + defaults) that applies domain installers.
- `apps/chrome-extension/options/core/settings/*.js`
  - Domain installers for `SettingsManager` methods:
    - `base_methods.js`
    - `language_methods.js`
    - `ui_prefs_methods.js`
    - `signals_methods.js`
    - `srs_profile_methods.js`
- `apps/chrome-extension/options/core/helper_manager.js`
  - Thin `HelperManager` class shell that applies helper-domain installers.
- `apps/chrome-extension/options/core/helper/*.js`
  - Domain installers for `HelperManager` methods:
    - `base_methods.js`
    - `diagnostics_methods.js`
    - `srs_set_methods.js`
- `apps/chrome-extension/options/core/bootstrap/*.js`
  - Options-root bootstrap helpers:
    - `controller_factory.js` (controller resolver)
    - `ui_bridge.js` (UI status/meta bridge adapters)
    - `language_prefs_adapter.js` (language/script preference adapter)
    - `translate_resolver.js` (shared translator resolver to avoid per-controller fallback duplication)
    - `dom_aliases.js` (stable UI DOM alias map used by bootstrap/controller composition)
    - `controller_adapters.js` (controller-to-callback adapters used by `options.js`)
    - `controller_graph.js` (options controller wiring/composition graph)
- `apps/chrome-extension/options/controllers/srs/actions_controller.js`
  - Thin SRS actions composition layer that wires dependencies and returns workflow handlers.
- `apps/chrome-extension/options/controllers/srs/actions/*.js`
  - SRS action support modules:
    - `formatters.js` (status/output formatting)
    - `shared.js` (shared action helpers, preflight, output sink)
    - `workflows.js` (initialize/refresh/diagnostics/sampled-preview/reset workflows)
- `apps/chrome-extension/content_script.js`
  - Orchestrator: loads settings, composes runtime controllers, builds trie, scans DOM, observes changes.
  - Provides debug logging and focus word diagnostics.
- `apps/chrome-extension/background.js`
  - Native helper bridge endpoint for helper requests.

Manifest ordering
- `apps/chrome-extension/manifest.json` loads modules before `content_script.js`.
- Load order is required to populate `globalThis.LexiShift` with module APIs.
- `content/runtime/dom_scan/node_filters.js`, `content/runtime/dom_scan/page_budget_tracker.js`, `content/runtime/dom_scan/scan_order.js`, `content/runtime/dom_scan/scan_counters.js`, and `content/runtime/dom_scan/text_node_processor.js` must load before `content/runtime/dom_scan_runtime.js`.
- `content/runtime/dom_scan_runtime.js`, `content/runtime/rules/helper_rules_runtime.js`, `content/runtime/rules/active_rules_runtime.js`, `content/runtime/diagnostics/apply_diagnostics_reporter.js`, `content/runtime/apply_runtime_actions.js`, `content/runtime/apply_settings_pipeline.js`, `content/runtime/feedback/feedback_runtime_controller.js`, and `content/runtime/settings_change_router.js` must load before `content_script.js`.
- `content/ui/popup_modules/module_registry.js` and `content/ui/popup_modules/japanese_script_module.js` must load before `content/ui/feedback_popup_controller.js`, which must load before `content/ui/ui.js`.
- The options page also loads `shared/settings/settings_defaults.js` before `options.js`.
- The options page loads `options/core/settings/*.js` installer scripts before `options/core/settings_manager.js`.
- The options page loads `options/core/helper/*.js` installer scripts before `options/core/helper_manager.js`.
- The options page loads `options/core/bootstrap/*.js` before `options.js`.
- `options.js` now requires registered controller factories and throws if required modules are missing.

Settings flow
- Defaults come from `globalThis.LexiShift.defaults` in `shared/settings/settings_defaults.js`.
- Options page writes values to `chrome.storage.local`.
- Options page writes background blobs to IndexedDB through `profile_media_store`.
- Content script reads settings on boot and reacts to `chrome.storage.onChanged`.
- Highlight/visual settings apply immediately; rules changes trigger a rescan.

Options UI tools (extension)
- SRS: “Initialize S for this pair” calls helper `srs_initialize` with profile-context scaffold.
- SRS: “Refresh S + publish rules” applies feedback-driven admissions and republishes runtime rules.
- SRS profile controls:
  - extension-local selected profile (global).
  - pair-specific SRS settings/signals loaded from the selected profile container.
  - “Refresh profiles” fetches helper profile catalog from `settings.json`.
  - Extension does not switch helper/GUI active profile.
- Profile background controls (per selected profile):
  - backdrop color + upload/remove/enable/opacity are saved into `srsProfiles.<profile_id>.uiPrefs`.
  - changes are staged until “Apply profile background” publishes options-page mirrors.
  - when no profile image is enabled, options page still applies the selected solid backdrop color.
- Advanced debug tools:
  - “SRS runtime diagnostics”
  - “Run sampled rulegen (5)…” (non-mutating helper preview)
  - helper connection test + open helper data folder
- Debug focus word: highlights whether a token was seen or replaced.
- Share Center (mixed rollout surface):
  - grouped/hierarchical share target UI above legacy share controls.
  - export action writes a JSON share payload file (download), not an in-modal share code string.
  - compact selection summary shows selection path, include groups, and output format.
  - compatibility targets map to existing share scopes:
    - `Profile settings` -> `srs`
    - `Full profile` -> `profile`
  - first new payload target:
    - `ruleset item` -> `ruleset` (single manual ruleset, path-free payload).
- Legacy Share Code card remains visible as fallback during rollout.
- Logging controls (Advanced):
  - Debug logs → console only (`debugEnabled`).
  - Exposure logging → stored in `chrome.storage.local` (`srsExposureLog`, telemetry).

Share envelope compatibility
- v1 envelope (`lexishift_share.version = 1`)
  - scopes: `rules`, `srs`, `profile`
  - payload in `data`
- v2 envelope (`lexishift_share.version = 2`)
  - scope: `ruleset`
  - payload at `data.ruleset`:
    - `name`
    - `rules`
    - `metadata`
- Importer is backward compatible:
  - accepts both v1 and v2 envelopes.
  - accepts legacy raw rules payloads without an envelope (treated as `rules` scope).

SRS settings (extension)
- `srsEnabled` (bool): enables SRS gating.
- `srsPair` (string): `en-en`, `de-de`, `ja-ja`, or `all`.
- `srsMaxActive` (int): max active lemmas to allow.
- `srsBootstrapTopN` (int): bootstrap inventory size for initial helper-side `S` admission.
- `srsInitialActiveCount` (int): initial active subset size declared for planner/policy.
- `srsHighlightColor` (hex): highlight color for SRS-origin spans.
- `srsFeedbackSrsEnabled` (bool): allow feedback popup on SRS-origin spans.
- `srsFeedbackRulesEnabled` (bool): reserved compatibility flag for ruleset-origin spans; normalized off/not exposed for MVP.
- `srsSoundEnabled` (bool): enable/disable feedback sound.
- `srsExposureLoggingEnabled` (bool): enable/disable logging of exposure events.
- `srsSelectedProfileId` (string): extension-local selected profile id for SRS runtime/options.
- `srsProfiles` (object): profile-first SRS container.
  - `srsProfiles.<profile_id>.languagePrefs` stores active LP for that profile (`sourceLanguage`, `targetLanguage`, `srsPairAuto`, `srsPair`, `targetScriptPrefs`).
    - `targetScriptPrefs.ja.primaryDisplayScript`: `kanji` | `kana` | `romaji`.
  - `srsProfiles.<profile_id>.srsByPair.<pair>` stores pair SRS settings.
  - `srsProfiles.<profile_id>.srsSignalsByPair.<pair>` stores planner/profile-context signals.
  - `srsProfiles.<profile_id>.uiPrefs` stores profile UI preferences (`backgroundAssetId`, `backgroundEnabled`, `backgroundOpacity`, `backgroundBackdropColor`).
- `srsProfileId` (string): runtime mirror key consumed by content script and feedback sync.
- `srsSemanticAdmissionFallbackPolicy` (string): derived fail-closed runtime mirror (`abstain_on_unavailable`); the lower-level gate still recognizes explicit legacy compatibility input, but normal defaults and profile publication do not select it.
- `targetDisplayScript` (string): runtime mirror for selected target display script (`kanji` | `kana` | `romaji` for Japanese target UI).
- `profileBackgroundEnabled` (bool): runtime background toggle for selected profile.
- `profileBackgroundAssetId` (string): selected profile background asset id (IndexedDB reference).
  - Background runtime mirrors are now used by the options page flow only (not injected into general web pages).
- `profileBackgroundOpacity` (float): selected profile background opacity (0..1).
- `profileBackgroundBackdropColor` (hex): selected profile backdrop color for options page (`#RRGGBB`).
- `maxReplacementsPerPage` (int): hard cap for total replacements in each frame document (standard default `0`; `0` = unlimited).
- `maxReplacementsPerSentence` (int): best-effort cap for replacements in one reconstructed sentence (standard default `0`; `0` = unlimited).
- `maxReplacementsPerLemmaPerPage` (int): cap for each replacement lemma on a page (standard default `0`; `0` = unlimited).

Replacement pipeline (content script)
1. Load and normalize settings from storage.
2. Normalize rules.
3. If SRS is enabled, load the fixed test dataset and select active lemmas.
4. Filter rules to those whose `replacement` is in the active lemma set.
5. Build a trie of word tokens from the filtered rules.
6. Collect all text nodes using a TreeWalker.
7. If page budgets are active, deterministically reorder the full-scan node list by page/profile seed before processing.
8. For each node:
   - Skip if empty, whitespace-only, in editable fields, excluded tags,
     non-rendered by `hidden`, `display:none`, `visibility:hidden/collapse`, or
     `content-visibility:hidden`, or already replaced.
   - Tokenize and find longest matches via the trie.
   - Run semantic admission, when active, against all lexical candidates.
   - Optionally filter matches:
     - `maxOnePerTextBlock`: keep only the first match in the text node.
     - `allowAdjacentReplacements=false`: skip back-to-back word matches.
     - `maxReplacementsPerPage`: stop replacing when page budget is exhausted.
     - `maxReplacementsPerSentence`: skip candidates after the reconstructed
       sentence reaches its cap.
     - `maxReplacementsPerLemmaPerPage`: skip lemmas that reached per-page cap.
     - When helper SRS metadata is present and replacement-load constraints
       apply, prefer new/learning/lower-stability due SRS items before mature
       or future-due SRS items.
   - Replace the node with a fragment containing spans and text nodes.
   - After the fragment is committed, increment the page-total, sentence, and
     lemma counters for exactly the spans that were rendered.
   - For Japanese targets, replacement display uses selected primary script when rule metadata includes script forms.
   - For morphology-tagged rules, display can use `metadata.morphology.target_surface` while canonical lemma remains `rule.replacement` for gating/feedback keys.
   - Each replacement span is tagged with `data-origin` (`srs` or `ruleset`).
9. Track processed nodes in a `WeakMap` to avoid repeated replacements.

SRS gating behavior (extension)
- The selector uses a fixed test dataset (`shared/srs/srs_selector_test_dataset.json`).
- The active lemma set gates rules by **replacement lemma**.
- If the dataset fails to load, the extension falls back to full rules and logs the error (debug only).

Helper set-planning flow (options)
- Options builds `profile_context` from:
  - pair-level SRS constraints (`srsMaxActive`)
  - scaffolded profile signals (`srsProfiles.<selected_profile>.srsSignalsByPair[pair]`)
  - sizing controls (`srsBootstrapTopN`, `srsInitialActiveCount`)
- Options publishes resolved pair-profile SRS settings into runtime storage keys (`srsEnabled`, `srsMaxActive`, etc.) plus `srsProfileId`, so content-script behavior tracks the selected profile.
- Options sends:
  - `strategy: "profile_bootstrap"`
  - `objective: "bootstrap"`
  - `bootstrap_top_n`
  - `initial_active_count`
  - `max_active_items_hint`
  - `trigger: "options_initialize_button"`
  - `profile_context`
- Helper returns plan metadata (`strategy_requested`, `strategy_effective`, `notes`) plus mutation result.

Profile switch behavior:
- When the selected profile changes, options first snapshots the current profile LP into that profile’s `languagePrefs`, then restores the target profile LP and loads that profile’s SRS settings for the restored pair.

Helper cache scoping:
- helper ruleset/snapshot cache keys are scoped by `profile_id + pair` to prevent cross-profile rule leakage.
- feedback sync payloads include `profile_id` so helper writes to the correct profile store.

Profile media scoping:
- Background assets are stored and cleaned per profile id in IndexedDB.
- Runtime mirrors store `profileBackgroundAssetId`/enabled/opacity/backdropColor in `chrome.storage.local`.
- Options page preview/apply flows read selected profile assets directly from `profile_media_store`.

SRS feedback UX (extension)
- Right click on a replacement shows a popup with 4 colored choices:
  - 1 (red) = Again / Failed
  - 2 (orange) = Hard
  - 3 (yellow) = Good
  - 4 (blue) = Easy
- Keyboard shortcuts: **Ctrl+1/2/3/4**.
- Feedback is stored in `chrome.storage.local` (`srsFeedbackLog`, max 500 entries).
- Feedback updates `srsStore` items (history + scheduling fields).
- Feedback is enqueued for helper sync (`record_feedback`) with persistent retry/backoff.
- Queue keys:
  - `helperFeedbackSyncQueue`
  - `helperFeedbackSyncLock`
  - `helperFeedbackSyncDropped`
- Feedback popup appears for SRS learning words in MVP. Ruleset-origin feedback
  remains an internal compatibility path gated by `srsFeedbackRulesEnabled`, but
  Options normalizes that flag off and does not expose a learner-facing toggle.

Exposure tracking (extension)
- Each replacement detail is logged with origin (`srs` or `ruleset`).
- Logged fields: lemma, replacement, original, language pair, source phrase, URL.
- Stored in `chrome.storage.local` as `srsExposureLog` (max 2000 entries).
- Logging is skipped when `srsExposureLoggingEnabled` is false (Advanced → Logging).
- Exposure records may update local telemetry fields (for debugging/analytics).
- Exposure logs are non-authoritative for SRS scheduling decisions.

Observer strategy
- A MutationObserver watches for added/edited nodes and rescans only the new content.
- `ensureObserver` rebinds if the document body changes.
- A lightweight rescan runs on window load and after a post-load timeout.

Debug tooling
- `debugEnabled` controls console logs across all modules.
- `debugFocusWord` highlights whether the word appears as:
  - substring in a node,
  - exact word token,
  - replaced or skipped.
- Detail logs are capped to avoid flooding the console.

Settings added for page replacement density
- `maxOnePerTextBlock` (default: false)
  - Legacy compatibility control that limits each text node to a single
    replacement. It remains runtime-supported for existing configurations but
    is de-emphasized under Advanced settings; use
    `maxReplacementsPerSentence = 1` for the learner-facing behavior.
- `allowAdjacentReplacements` (default: true)
  - When disabled, prevents replacements that occur on immediately adjacent words.
- `maxReplacementsPerPage` (default: 0)
  - Caps the total number of replacements per frame-document scan/session
    (`0` means unlimited). The top document and embedded frames have independent
    budgets because the content runtime executes in every frame.
- `maxReplacementsPerSentence` (default: 0)
  - Caps replacements within a best-effort reconstructed sentence (`0` means
    unlimited); a multi-word phrase counts as one replacement.
- `maxReplacementsPerLemmaPerPage` (default: 0)
  - Caps repeated replacements of the same lemma on a page (`0` means unlimited).
  - When replacement-load constraints are active, SRS candidates are selected
    with scheduler metadata-aware priority before deterministic tie-breaking.
- Density limits share one post-semantic selection pass. Semantic abstentions do
  not consume a slot, and counters advance only after the replacement fragment
  is attached to the page.
- Density settings are global extension settings. Debug runtime diagnostics
  expose the `frame_document` scope, configured limits, committed total usage,
  cap-exhaustion counts, and aggregate page/sentence/lemma rejection counts;
  lemma and sentence identifiers are not persisted.
- Visibility-related `class`, `hidden`, and `style` mutations trigger a targeted
  subtree rescan so content skipped while hidden can be processed when revealed.
- The defaults are declared as `replacementDensityDefaults.standard` in the
  extension settings defaults so the MVP density policy has one explicit tuning
  point.

## Known Gap To Preserve Explicitly

Known issue (not fixed yet)
- The act of replacing text nodes splits the original text into multiple nodes.
- This means `maxOnePerTextBlock` can no longer refer to the original text block,
  because the subsequent scan sees newly created nodes and treats them as separate.
- The control is therefore retained only as explicitly labeled legacy
  text-node compatibility. No automatic storage migration is performed.
- Sentence reconstruction is deliberately best effort. Malformed DOM,
  punctuation-free prose, shadow DOM boundaries, and unusually large/truncated
  containers can fall back to text-node-local identity; the cap remains safe
  but may be conservative or split one visible sentence.
