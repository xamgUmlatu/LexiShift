# LexiShift Chrome Extension: Technical Notes

Overview
- The extension runs a content script on all frames and replaces visible text using a ruleset.
- The codebase is modularized into small, focused modules loaded in a strict order by the manifest.
- Settings are stored in `chrome.storage.local` and shared between the content script and options page.

Module layout
- `apps/chrome-extension/shared/settings_defaults.js`
  - Central default settings used by both the options UI and content script.
  - Avoids drift when new settings are added.
- `apps/chrome-extension/shared/srs_selector.js`
  - Loads the fixed SRS test dataset and scores candidates.
  - Selects active SRS lemmas for gating.
- `apps/chrome-extension/shared/helper_feedback_sync.js`
  - Persistent helper feedback sync queue with retry + backoff.
  - Uses a lightweight storage lock to reduce duplicate flush workers.
  - Supports optional dropped-entry archive when a retry cap is enabled.
- `apps/chrome-extension/shared/srs_feedback.js`
  - Persists SRS feedback events to `chrome.storage.local` (`srsFeedbackLog`).
  - Provides helper to build feedback entries from replacement spans.
- `apps/chrome-extension/shared/srs_store.js`
  - Maintains a compact SRS item store in `chrome.storage.local` (`srsStore`).
  - Updates item history/scheduler fields from feedback events.
  - Exposure counts are telemetry and should not be treated as scheduling events.
- `apps/chrome-extension/shared/srs_gate.js`
  - Filters rules using the active SRS lemma set (gating).
- `apps/chrome-extension/shared/lemmatizer.js`
  - Stub lemmatizer for early data collection (identity for JP, lowercase for EN/DE).
- `apps/chrome-extension/shared/srs_metrics.js`
  - Records replacement exposures to `chrome.storage.local` (`srsExposureLog`).
  - Exposure logs are for diagnostics/analytics, not direct SRS scheduling.
- `apps/chrome-extension/content/tokenizer.js`
  - Tokenization utilities (word/space/punct) and normalization helpers.
  - Exposes `tokenize`, `normalize`, `textHasToken`, `computeGapOk`.
- `apps/chrome-extension/content/matcher.js`
  - Builds a phrase trie from rules and resolves longest-match tokens.
  - Applies case policy (`match`, `as-is`, `lower`, `upper`, `title`).
  - Normalizes rule objects to a consistent shape.
- `apps/chrome-extension/content/replacements.js`
  - Builds a `DocumentFragment` with replacement spans for a text node.
  - Filters matches based on settings (max-one-per-block, allow-adjacent, page budgets).
  - Keeps optional replacement detail logs for debug mode.
  - Adds `data-origin`, `data-language-pair`, and `data-source` for downstream UI control.
- `apps/chrome-extension/content/ui.js`
  - Handles highlight styles, click-to-toggle behavior, and cleanup.
  - Provides SRS feedback popup and keyboard shortcuts (Ctrl+1/2/3/4).
  - Separates DOM mutation concerns from parsing and matching.
- `apps/chrome-extension/content/utils.js`
  - Logging helpers: element descriptors, codepoint snippets, node traversal.
- `apps/chrome-extension/content_script.js`
  - Orchestrator: loads settings, builds trie, scans DOM, observes changes.
  - Provides debug logging and focus word diagnostics.

Manifest ordering
- `apps/chrome-extension/manifest.json` loads modules before `content_script.js`.
- Load order is required to populate `globalThis.LexiShift` with module APIs.
- The options page also loads `shared/settings_defaults.js` before `options.js`.

Settings flow
- Defaults come from `globalThis.LexiShift.defaults` in `shared/settings_defaults.js`.
- Options page writes values to `chrome.storage.local`.
- Content script reads settings on boot and reacts to `chrome.storage.onChanged`.
- Highlight/visual settings apply immediately; rules changes trigger a rescan.

Options UI tools (extension)
- SRS: “Sample active words…” button uses the current selector + pair to show 5 candidates.
- SRS: “Initialize S for this pair” calls helper `srs_initialize` with profile-context scaffold.
- Debug focus word: highlights whether a token was seen or replaced.
- Share code: export/import compressed rules.
- Logging controls (Advanced):
  - Debug logs → console only (`debugEnabled`).
  - Exposure logging → stored in `chrome.storage.local` (`srsExposureLog`, telemetry).

SRS settings (extension)
- `srsEnabled` (bool): enables SRS gating.
- `srsPair` (string): `en-en`, `de-de`, `ja-ja`, or `all`.
- `srsMaxActive` (int): max active lemmas to allow.
- `srsBootstrapTopN` (int): bootstrap inventory size for initial helper-side `S` admission.
- `srsInitialActiveCount` (int): initial active subset size declared for planner/policy.
- `srsHighlightColor` (hex): highlight color for SRS-origin spans.
- `srsFeedbackSrsEnabled` (bool): allow feedback popup on SRS-origin spans.
- `srsFeedbackRulesEnabled` (bool): allow feedback popup on ruleset-origin spans.
- `srsSoundEnabled` (bool): enable/disable feedback sound.
- `srsExposureLoggingEnabled` (bool): enable/disable logging of exposure events.
- `srsProfileSignals` (object): scaffold storage for per-pair profile signals used by set planning.
  - Includes placeholders like interests/proficiency/objectives/empirical trends.
  - UI editing is pending; data may be written by future settings surfaces.
- `maxReplacementsPerPage` (int): hard cap for total replacements on a page (`0` = unlimited).
- `maxReplacementsPerLemmaPerPage` (int): cap for each replacement lemma on a page (`0` = unlimited).

Replacement pipeline (content script)
1. Load and normalize settings from storage.
2. Normalize rules.
3. If SRS is enabled, load the fixed test dataset and select active lemmas.
4. Filter rules to those whose `replacement` is in the active lemma set.
5. Build a trie of word tokens from the filtered rules.
6. Collect all text nodes using a TreeWalker.
7. For each node:
   - Skip if empty, whitespace-only, in editable fields, excluded tags, or already replaced.
   - Tokenize and find longest matches via the trie.
   - Optionally filter matches:
     - `maxOnePerTextBlock`: keep only the first match in the text node.
     - `allowAdjacentReplacements=false`: skip back-to-back word matches.
     - `maxReplacementsPerPage`: stop replacing when page budget is exhausted.
     - `maxReplacementsPerLemmaPerPage`: skip lemmas that reached per-page cap.
   - Replace the node with a fragment containing spans and text nodes.
   - Each replacement span is tagged with `data-origin` (`srs` or `ruleset`).
8. Track processed nodes in a `WeakMap` to avoid repeated replacements.

SRS gating behavior (extension)
- The selector uses a fixed test dataset (`shared/srs_selector_test_dataset.json`).
- The active lemma set gates rules by **replacement lemma**.
- If the dataset fails to load, the extension falls back to full rules and logs the error (debug only).

Helper set-planning flow (options)
- Options builds `profile_context` from:
  - pair-level SRS constraints (`srsMaxActive`)
  - scaffolded profile signals (`srsProfileSignals[pair]`)
  - sizing controls (`srsBootstrapTopN`, `srsInitialActiveCount`)
- Options sends:
  - `strategy: "profile_bootstrap"`
  - `objective: "bootstrap"`
  - `bootstrap_top_n`
  - `initial_active_count`
  - `max_active_items_hint`
  - `trigger: "options_initialize_button"`
  - `profile_context`
- Helper returns plan metadata (`strategy_requested`, `strategy_effective`, `notes`) plus mutation result.

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
- Feedback popup appears when the origin is enabled:
  - SRS words: `srsFeedbackSrsEnabled`
  - Ruleset words: `srsFeedbackRulesEnabled`

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

Settings added for replacement behavior
- `maxOnePerTextBlock` (default: false)
  - Limits each text node to a single replacement.
- `allowAdjacentReplacements` (default: true)
  - When disabled, prevents replacements that occur on immediately adjacent words.
- `maxReplacementsPerPage` (default: 0)
  - Caps the total number of replacements per page scan/session (`0` means unlimited).
- `maxReplacementsPerLemmaPerPage` (default: 0)
  - Caps repeated replacements of the same lemma on a page (`0` means unlimited).

Known issue (not fixed yet)
- The act of replacing text nodes splits the original text into multiple nodes.
- This means `maxOnePerTextBlock` can no longer refer to the original text block,
  because the subsequent scan sees newly created nodes and treats them as separate.
- This is a behavior-level bug; do not fix yet.
